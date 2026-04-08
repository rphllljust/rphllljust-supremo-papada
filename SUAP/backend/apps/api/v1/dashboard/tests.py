from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from urllib.error import HTTPError
import tempfile
from pathlib import Path

from apps.api.v1.dashboard import views as dashboard_views

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

    def test_sheets_module_rejeita_fonte_que_nao_e_google_sheets(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            "/api/v1/dashboard/sheets/module/",
            {"source_url": "https://example.com/planilha.csv"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["source_is_external"])
        self.assertEqual(response.data["source_total_requested"], 1)
        self.assertEqual(response.data["source_total_loaded"], 0)
        self.assertTrue(response.data["source_errors"])
        self.assertIn("Google Sheets", response.data["source_errors"][0]["detail"])

    @override_settings(
        GOOGLE_SHEETS_EXPORT_TOKEN="abc123",
        GOOGLE_SHEETS_PUBLIC_BASE_URL="https://idep-dashboard-ro-2026.loca.lt",
    )
    @patch("apps.api.v1.dashboard.views._fetch_external_csv_content")
    def test_sheets_module_ler_planilha_google_externa(self, fetch_csv_mock):
        fetch_csv_mock.return_value = "nome,cpf,status\nAna,123,Ativa\nBruno,456,Inativa\n"
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            "/api/v1/dashboard/sheets/module/",
            {"source_url": "https://docs.google.com/spreadsheets/d/abc123/edit#gid=999"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["source_is_external"])
        self.assertEqual(response.data["source_mode"], "external_google_sheets")
        self.assertIn("/export?format=csv&gid=999", response.data["source_csv_url"])
        self.assertEqual(response.data["preview_columns"], ["planilha", "nome", "cpf", "status"])
        self.assertEqual(response.data["preview_rows"][0]["nome"], "Ana")

    @override_settings(
        GOOGLE_SHEETS_EXPORT_TOKEN="abc123",
        GOOGLE_SHEETS_PUBLIC_BASE_URL="https://idep-dashboard-ro-2026.loca.lt",
    )
    @patch("apps.api.v1.dashboard.views._fetch_external_csv_content")
    def test_sheets_module_ler_multiplas_planilhas_google(self, fetch_csv_mock):
        def mocked_csv(url, timeout=20, source_info=None):
            if "gid=10" in url:
                return "secao,id,titulo,descricao,valor,data,status,href\nsummary,recent_enrollments,recent_enrollments,,4,,,\n"
            if "gid=20" in url:
                return "secao,id,titulo,descricao,valor,data,status,href\nsummary,document_pending,document_pending,,6,,,\n"
            return "secao,id,titulo,descricao,valor,data,status,href\n"

        fetch_csv_mock.side_effect = mocked_csv
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            "/api/v1/dashboard/sheets/module/",
            {
                "source_urls_text": "\n".join(
                    [
                        "https://docs.google.com/spreadsheets/d/planilhaA/edit#gid=10",
                        "https://docs.google.com/spreadsheets/d/planilhaB/edit#gid=20",
                    ]
                )
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["source_is_external"])
        self.assertEqual(response.data["source_mode"], "external_google_sheets_batch")
        self.assertEqual(response.data["source_total_requested"], 2)
        self.assertEqual(response.data["source_total_loaded"], 2)
        self.assertEqual(len(response.data["source_csv_urls"]), 2)
        self.assertEqual(response.data["summary"]["recent_enrollments"], 4)
        self.assertEqual(response.data["summary"]["document_pending"], 6)

    @override_settings(
        GOOGLE_SHEETS_EXPORT_TOKEN="abc123",
        GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON='{"type":"service_account","client_email":"suap-bot@project.iam.gserviceaccount.com","private_key":"-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----\\n"}',
    )
    def test_sheets_module_expoe_email_conta_servico(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get("/api/v1/dashboard/sheets/module/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["service_account_email"], "suap-bot@project.iam.gserviceaccount.com")

    @patch("apps.api.v1.dashboard.views._fetch_external_csv_content_via_service_account")
    @patch("apps.api.v1.dashboard.views.urlopen")
    def test_fetch_external_csv_fallback_em_401(self, urlopen_mock, fallback_mock):
        urlopen_mock.side_effect = HTTPError(
            url="https://docs.google.com/spreadsheets/d/abc/export?format=csv&gid=0",
            code=401,
            msg="Unauthorized",
            hdrs=None,
            fp=None,
        )
        fallback_mock.return_value = "nome,cpf\nAna,123\n"

        content = dashboard_views._fetch_external_csv_content(
            "https://docs.google.com/spreadsheets/d/abc/export?format=csv&gid=0",
            source_info={"sheet_id": "abc", "gid": "0"},
        )

        self.assertEqual(content, "nome,cpf\nAna,123\n")
        fallback_mock.assert_called_once()

    @patch("apps.api.v1.dashboard.views.urlopen")
    def test_fetch_external_csv_tenta_candidata_alternativa(self, urlopen_mock):
        class _CsvResponse:
            def __init__(self, payload):
                self.payload = payload

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return self.payload

        urlopen_mock.side_effect = [
            HTTPError(
                url="https://docs.google.com/spreadsheets/d/abc/export?format=csv&gid=0",
                code=403,
                msg="Forbidden",
                hdrs=None,
                fp=None,
            ),
            _CsvResponse(b"nome,cpf\nAna,123\n"),
        ]

        content = dashboard_views._fetch_external_csv_content(
            "https://docs.google.com/spreadsheets/d/abc/export?format=csv&gid=0",
            source_info={
                "sheet_id": "abc",
                "gid": "0",
                "csv_candidates": ["https://docs.google.com/spreadsheets/d/abc/gviz/tq?tqx=out:csv&gid=0"],
            },
        )

        self.assertEqual(content, "nome,cpf\nAna,123\n")
        self.assertEqual(urlopen_mock.call_count, 2)

    def test_extract_google_source_info_rejeita_url_lista(self):
        with self.assertRaisesMessage(ValueError, "lista de planilhas"):
            dashboard_views._extract_google_sheet_source_info("https://docs.google.com/spreadsheets/u/0/")

    def test_extract_google_source_info_aceita_planilha_publicada(self):
        info = dashboard_views._extract_google_sheet_source_info(
            "https://docs.google.com/spreadsheets/d/e/2PACX-abc123/pubhtml?gid=0&single=true"
        )
        self.assertEqual(info["sheet_id"], "")
        self.assertIn("/pub?output=csv", info["csv_url"])
        self.assertTrue(info["csv_candidates"])

    def test_sheets_module_post_salvar_credencial_requer_admin(self):
        self.client.force_authenticate(user=self.professor)
        response = self.client.post(
            "/api/v1/dashboard/sheets/module/",
            data={
                "service_account_json": '{"type":"service_account","client_email":"x@y","private_key":"pk"}'
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sheets_module_post_salvar_e_remover_credencial(self):
        self.client.force_authenticate(user=self.admin)

        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = Path(temp_dir) / "sa.json"
            with override_settings(GOOGLE_SHEETS_SERVICE_ACCOUNT_LOCAL_FILE=str(local_path)):
                save_response = self.client.post(
                    "/api/v1/dashboard/sheets/module/",
                    data={
                        "service_account_json": {
                            "type": "service_account",
                            "client_email": "suap-local@project.iam.gserviceaccount.com",
                            "private_key": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n",
                        }
                    },
                    format="json",
                )
                self.assertEqual(save_response.status_code, status.HTTP_200_OK)
                self.assertTrue(local_path.exists())
                self.assertEqual(
                    save_response.data["service_account_email"],
                    "suap-local@project.iam.gserviceaccount.com",
                )

                get_response = self.client.get("/api/v1/dashboard/sheets/module/")
                self.assertEqual(get_response.status_code, status.HTTP_200_OK)
                self.assertTrue(get_response.data["service_account_configured"])
                self.assertEqual(
                    get_response.data["service_account_email"],
                    "suap-local@project.iam.gserviceaccount.com",
                )

                clear_response = self.client.post(
                    "/api/v1/dashboard/sheets/module/",
                    data={"clear_service_account": True},
                    format="json",
                )
                self.assertEqual(clear_response.status_code, status.HTTP_200_OK)
                self.assertFalse(local_path.exists())
