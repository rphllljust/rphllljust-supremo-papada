from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.usuarios.models import PerfilUsuario, Usuario


class DashboardSheetsIntegrationTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username="90000010057",
            cpf="90000010057",
            tipo=PerfilUsuario.ADMIN,
            password="admin",
        )
        self.professor = Usuario.objects.create_user(
            username="90000010058",
            cpf="90000010058",
            tipo=PerfilUsuario.PROFESSOR,
            password="admin",
        )

    def test_overview_requer_autenticacao(self):
        response = self.client.get("/api/v1/dashboard/overview/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_overview_autenticado_retorna_dados(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/dashboard/overview/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("summary", response.data)

    @override_settings(GOOGLE_SHEETS_EXPORT_TOKEN="")
    def test_export_csv_sem_token_configurado(self):
        response = self.client.get("/api/v1/dashboard/overview-sheets.csv")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @override_settings(GOOGLE_SHEETS_EXPORT_TOKEN="abc123")
    def test_export_csv_token_invalido(self):
        response = self.client.get("/api/v1/dashboard/overview-sheets.csv", {"token": "errado"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @override_settings(GOOGLE_SHEETS_EXPORT_TOKEN="abc123")
    def test_export_csv_com_token_valido(self):
        response = self.client.get("/api/v1/dashboard/overview-sheets.csv", {"token": "abc123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertNotIn("Content-Disposition", response)
        self.assertIn("secao,id,titulo,descricao,valor,data,status,href", response.content.decode("utf-8"))

    def test_sheets_module_requer_autenticacao(self):
        response = self.client.get("/api/v1/dashboard/sheets/module/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        GOOGLE_SHEETS_EXPORT_TOKEN="abc123",
        GOOGLE_SHEETS_PUBLIC_BASE_URL="https://idep-dashboard-ro-2026.loca.lt",
    )
    def test_sheets_module_admin_retorna_formula_e_url_com_token(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/dashboard/sheets/module/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["integrated"])
        self.assertTrue(response.data["user_is_admin"])
        self.assertIn("token=abc123", response.data["export_url_with_token"])
        self.assertIn("IMPORTDATA", response.data["sheets_formula"])
        self.assertTrue(response.data["preview_rows"] is not None)

    @override_settings(
        GOOGLE_SHEETS_EXPORT_TOKEN="abc123",
        GOOGLE_SHEETS_PUBLIC_BASE_URL="https://idep-dashboard-ro-2026.loca.lt",
    )
    def test_sheets_module_nao_admin_oculta_segredo(self):
        self.client.force_authenticate(user=self.professor)
        response = self.client.get("/api/v1/dashboard/sheets/module/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["integrated"])
        self.assertFalse(response.data["user_is_admin"])
        self.assertEqual(response.data["export_url_with_token"], "")
        self.assertEqual(response.data["sheets_formula"], "")
