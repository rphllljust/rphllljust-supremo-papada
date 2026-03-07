from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch, reverse
from django.views import View
from rest_framework.test import APIClient, APIRequestFactory

from apps.access.api.permissions import CanAccessModule, CanExportToAva
from apps.access.decorators import module_access_required
from apps.access.mixins import ModuleAccessRequiredMixin
from apps.access.permissions import ACCESS_MATRIX
from apps.access.policies import (
    can_access_module,
    can_export_to_ava,
    can_view_object,
    filter_queryset_for_user,
    get_allowed_profiles,
)
from apps.accounts.services import redirect_by_profile
from apps.usuarios.models import PerfilUsuario, Usuario


def gerar_cpf(seed: int) -> str:
    base = f"{seed:09d}"[-9:]

    def dv(parcial: str) -> str:
        peso_inicial = len(parcial) + 1
        total = sum(int(digito) * (peso_inicial - indice) for indice, digito in enumerate(parcial))
        resto = 11 - (total % 11)
        return "0" if resto >= 10 else str(resto)

    d1 = dv(base)
    d2 = dv(base + d1)
    return f"{base}{d1}{d2}"


class ProtectedModuleView(ModuleAccessRequiredMixin, View):
    module_name = "matriculas"

    def get(self, request):
        return HttpResponse("ok")


class DummyOwnedObject:
    def __init__(self, user_id, app_label="matriculas"):
        self.user_id = user_id
        self._meta = type("Meta", (), {"app_label": app_label})()


class AccessRoutesTests(TestCase):
    def test_acesso_negado_route_exists(self):
        response = self.client.get(reverse("access:acesso_negado"))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Acesso negado", status_code=403)

    def test_old_accounts_acesso_negado_route_does_not_exist(self):
        with self.assertRaises(NoReverseMatch):
            reverse("accounts:acesso_negado")

    def test_redirect_by_profile_uses_access_route_for_aluno(self):
        aluno = Usuario.objects.create_user(
            username="aluno_access",
            cpf=gerar_cpf(923456789),
            tipo=PerfilUsuario.ALUNO,
            password="x",
        )
        self.assertEqual(redirect_by_profile(aluno), reverse("access:acesso_negado"))


class AccessPoliciesTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.api_factory = APIRequestFactory()
        self.api_client = APIClient()
        self.secretaria = Usuario.objects.create_user(
            username="secretaria_access",
            cpf=gerar_cpf(923456780),
            tipo=PerfilUsuario.SECRETARIA,
            password="x",
        )
        self.professor = Usuario.objects.create_user(
            username="professor_access",
            cpf=gerar_cpf(923456781),
            tipo=PerfilUsuario.PROFESSOR,
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_access2",
            cpf=gerar_cpf(923456782),
            tipo=PerfilUsuario.ALUNO,
            password="x",
        )

    def _authenticate_api_client(self, user, password="x"):
        response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": user.cpf,
                "password": password,
                "perfil": user.tipo,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")

    def test_can_access_module_allows_expected_profile(self):
        self.assertTrue(can_access_module(self.secretaria, "matriculas"))
        self.assertTrue(can_access_module(self.professor, "turmas"))

    def test_can_access_module_blocks_disallowed_profile(self):
        self.assertFalse(can_access_module(self.professor, "matriculas"))
        self.assertFalse(can_access_module(self.aluno, "dashboard"))
        self.assertFalse(can_access_module(self.secretaria, "modulo_inexistente"))

    def test_matrix_exposes_surface_and_action_specific_profiles(self):
        self.assertEqual(
            get_allowed_profiles("matriculas", surface="web", action="manage"),
            ACCESS_MATRIX["matriculas"]["web"]["manage"],
        )
        self.assertEqual(
            get_allowed_profiles("turmas", surface="api_ava", action="export"),
            ACCESS_MATRIX["turmas"]["api_ava"]["export"],
        )

    def test_can_export_to_ava_follows_shared_policy(self):
        self.assertTrue(can_export_to_ava(self.secretaria))
        self.assertTrue(can_export_to_ava(self.secretaria, module_name="turmas"))
        self.assertFalse(can_export_to_ava(self.professor))

    def test_can_view_object_allows_owner_and_blocks_unrelated_user(self):
        obj = DummyOwnedObject(self.professor.id)
        self.assertTrue(can_view_object(self.professor, obj))
        self.assertFalse(can_view_object(self.aluno, obj))

    def test_filter_queryset_for_user_returns_empty_when_module_is_denied(self):
        queryset = Usuario.objects.order_by("id")
        filtered = filter_queryset_for_user(self.professor, queryset)
        self.assertEqual(filtered.count(), 0)

    def test_module_access_required_decorator_allows_and_denies_consistently(self):
        @module_access_required("matriculas")
        def sample_view(request):
            return HttpResponse("ok")

        allowed_request = self.factory.get("/fake/")
        allowed_request.user = self.secretaria
        allowed_response = sample_view(allowed_request)
        self.assertEqual(allowed_response.status_code, 200)

        denied_request = self.factory.get("/fake/")
        denied_request.user = self.professor
        denied_response = sample_view(denied_request)
        self.assertEqual(denied_response.status_code, 403)
        self.assertContains(denied_response, "modulo matriculas", status_code=403)

    def test_module_access_required_mixin_denies_disallowed_profile(self):
        request = self.factory.get("/fake/")
        request.user = self.professor
        response = ProtectedModuleView.as_view()(request)
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "modulo matriculas", status_code=403)

    def test_drf_permissions_reuse_policies(self):
        request = self.api_factory.get("/api/v1/unidades/")
        request.user = self.secretaria

        class DummyModuleView:
            module_name = "unidades"

        self.assertEqual(
            CanAccessModule().has_permission(request, DummyModuleView()),
            can_access_module(self.secretaria, "unidades"),
        )
        self.assertEqual(CanExportToAva().has_permission(request, object()), can_export_to_ava(self.secretaria))

    def test_ava_export_preview_endpoint_requires_authorization(self):
        url = reverse("access_api:ava_export_preview")

        anonymous_response = self.api_client.get(url)
        self.assertEqual(anonymous_response.status_code, 401)

        self._authenticate_api_client(self.secretaria)
        authorized_response = self.api_client.get(url)
        self.assertEqual(authorized_response.status_code, 200)
        self.assertEqual(authorized_response.json()["status"], "ok")