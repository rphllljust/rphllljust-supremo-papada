from django.test import TestCase

from apps.unidades.models import Unidade


class SmokeRoutesTests(TestCase):
    def test_main_pages_are_available(self):
        for path in ["/", "/usuarios/", "/turmas/", "/matriculas/", "/unidades/"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, msg=f"Falha em {path}")

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
