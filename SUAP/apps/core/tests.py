from django.test import TestCase
from django.urls import reverse

from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario


class SmokeRoutesTests(TestCase):
    def test_main_pages_redirect_to_login_when_anonymous(self):
        for path in ["/", "/turmas/", "/matriculas/"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 302, msg=f"Falha em {path}")
            self.assertIn(reverse("accounts:login"), response.url)

    def test_forbidden_role_sees_friendly_access_denied_page(self):
        aluno = Usuario.objects.create_user(
            username="aluno_sem_permissao",
            cpf="92345678911",
            tipo="ALUNO",
            password="x",
        )
        self.client.force_login(aluno)

        response = self.client.get(reverse("cursos:cursos_create"))

        self.assertEqual(response.status_code, 403)
        self.assertContains(response, "Acesso negado", status_code=403)
        self.assertContains(response, "Voltar ao painel", status_code=403)

    def test_api_v1_list_routes_are_available(self):
        for path in [
            "/api/v1/usuarios/",
            "/api/v1/turmas/",
            "/api/v1/matriculas/",
            "/api/v1/unidades/",
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, msg=f"Falha em {path}")

    def test_api_v1_detail_routes_are_available(self):
        unidade = Unidade.objects.create(nome="Unidade Teste", codigo="UT001")

        for path in [
            "/api/v1/usuarios/1/",
            "/api/v1/turmas/1/",
            "/api/v1/matriculas/1/",
            f"/api/v1/unidades/{unidade.pk}/",
        ]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, msg=f"Falha em {path}")
