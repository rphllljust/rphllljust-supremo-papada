from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.unidades.models import Unidade
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


class SmokeRoutesTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.secretaria = Usuario.objects.create_user(
            username="secretaria_api",
            cpf=gerar_cpf(923456783),
            tipo=PerfilUsuario.SECRETARIA,
            password="x",
        )
        self.professor = Usuario.objects.create_user(
            username="professor_api",
            cpf=gerar_cpf(923456784),
            tipo=PerfilUsuario.PROFESSOR,
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

    def test_main_pages_redirect_to_login_when_anonymous(self):
        for path in ["/", "/turmas/", "/matriculas/"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302, msg=f"Falha em {path}")
            self.assertIn(reverse("accounts:login"), response.url)

    def test_forbidden_role_sees_friendly_access_denied_page(self):
        aluno = Usuario.objects.create_user(
            username="aluno_sem_permissao",
            cpf=gerar_cpf(923456785),
            tipo="ALUNO",
            password="x",
        )
        self.client.force_login(aluno)

        response = self.client.get(reverse("cursos:cursos_create"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Acesso negado", status_code=403)
        self.assertContains(response, "Voltar ao painel", status_code=403)

    def test_api_v1_list_routes_require_authenticated_authorized_user(self):
        for path in [
            "/api/v1/usuarios/",
            "/api/v1/turmas/",
            "/api/v1/matriculas/",
            "/api/v1/unidades/",
        ]:
            self.api_client.credentials()
            anonymous_response = self.api_client.get(path)
            self.assertEqual(anonymous_response.status_code, 401, msg=f"Falha anonima em {path}")

            self._authenticate_api_client(self.professor)
            forbidden_response = self.api_client.get(path)
            self.assertEqual(forbidden_response.status_code, 403, msg=f"Falha de perfil em {path}")

            self._authenticate_api_client(self.secretaria)
            authorized_response = self.api_client.get(path)
            self.assertEqual(authorized_response.status_code, 200, msg=f"Falha autorizada em {path}")

    def test_api_v1_detail_routes_require_authenticated_authorized_user(self):
        unidade = Unidade.objects.get(codigo="sede")

        for path in [
            "/api/v1/usuarios/1/",
            "/api/v1/turmas/1/",
            "/api/v1/matriculas/1/",
            f"/api/v1/unidades/{unidade.pk}/",
        ]:
            self.api_client.credentials()
            anonymous_response = self.api_client.get(path)
            self.assertEqual(anonymous_response.status_code, 401, msg=f"Falha anonima em {path}")

            self._authenticate_api_client(self.professor)
            forbidden_response = self.api_client.get(path)
            self.assertEqual(forbidden_response.status_code, 403, msg=f"Falha de perfil em {path}")

            self._authenticate_api_client(self.secretaria)
            authorized_response = self.api_client.get(path)
            self.assertEqual(authorized_response.status_code, 200, msg=f"Falha autorizada em {path}")


class HelloWorldTestCase(TestCase):
    def test_hello_world(self):
        self.assertEqual("hello", "hello")
