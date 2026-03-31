import re
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.frequencia.models import Frequencia
from apps.notas.models import Nota
from apps.turmas.models import DiarioAcademico, DiarioMaterialAula, DiarioOcorrencia, Turma
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


class SeedDevelopmentDataCommandTests(TestCase):
    def test_seed_creates_complete_academic_development_dataset(self):
        stdout = StringIO()

        call_command("seed_development_data", stdout=stdout)
        call_command("seed_development_data", stdout=stdout)

        self.assertTrue(
            Usuario.objects.filter(username="coordenacao.dev", tipo=PerfilUsuario.COORDENACAO).exists()
        )
        self.assertEqual(Turma.objects.filter(nome__startswith="DEV-").count(), 2)
        self.assertEqual(DiarioAcademico.objects.filter(turma__nome__startswith="DEV-").count(), 2)
        self.assertEqual(DiarioMaterialAula.objects.filter(diario__turma__nome__startswith="DEV-").count(), 3)
        self.assertEqual(DiarioOcorrencia.objects.filter(diario__turma__nome__startswith="DEV-").count(), 3)
        self.assertEqual(Nota.objects.filter(matricula__turma__nome__startswith="DEV-").count(), 8)
        self.assertEqual(Frequencia.objects.filter(matricula__turma__nome__startswith="DEV-").count(), 12)


class BootstrapInitialAdminCommandTests(TestCase):
    @override_settings(
        INITIAL_ADMIN_CPF="",
        INITIAL_ADMIN_PASSWORD="admin",
        INITIAL_ADMIN_FIRST_NAME="Administrador",
        INITIAL_ADMIN_LAST_NAME="Inicial",
    )
    def test_bootstrap_requires_explicit_cpf_when_env_is_missing(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesMessage(
                CommandError,
                "Informe o CPF do administrador inicial via --cpf ou pela variavel de ambiente INITIAL_ADMIN_CPF.",
            ):
                call_command("bootstrap_initial_admin")

    @override_settings(
        INITIAL_ADMIN_CPF="",
        INITIAL_ADMIN_PASSWORD="",
        INITIAL_ADMIN_FIRST_NAME="Administrador",
        INITIAL_ADMIN_LAST_NAME="Inicial",
    )
    def test_bootstrap_generates_random_credentials_when_flag_is_enabled(self):
        stdout = StringIO()

        call_command("bootstrap_initial_admin", "--generate-random-credentials", stdout=stdout)

        output = stdout.getvalue()
        match = re.search(r"cpf=(\d{11}) senha=([A-Za-z0-9]{16})", output)

        self.assertIsNotNone(match, msg=output)
        cpf, password = match.groups()

        usuario = Usuario.objects.get(cpf=cpf)
        self.assertEqual(usuario.tipo, PerfilUsuario.ADMIN)
        self.assertTrue(usuario.check_password(password))
        self.assertTrue(usuario.must_change_password)

    def test_bootstrap_random_credentials_reuses_existing_admin_cpf(self):
        admin_cpf = gerar_cpf(111222333)
        existing_admin = Usuario.objects.create_user(
            username=admin_cpf,
            cpf=admin_cpf,
            tipo=PerfilUsuario.ADMIN,
            password="senha_antiga",
            is_staff=True,
            is_superuser=True,
        )

        stdout = StringIO()
        call_command("bootstrap_initial_admin", "--generate-random-credentials", stdout=stdout)

        output = stdout.getvalue()
        match = re.search(r"cpf=(\d{11}) senha=([A-Za-z0-9]{16})", output)

        self.assertIsNotNone(match, msg=output)
        cpf, password = match.groups()
        self.assertEqual(cpf, admin_cpf)

        existing_admin.refresh_from_db()
        self.assertTrue(existing_admin.check_password(password))
