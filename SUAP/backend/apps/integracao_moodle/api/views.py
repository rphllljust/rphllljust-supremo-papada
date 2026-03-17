from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanExportToAva
from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.services import (
    get_moodle_categories,
    get_moodle_courses,
    import_moodle_courses_to_formacao_inicial,
    save_moodle_assignment_grade,
    save_moodle_assignment_grades,
    store_moodle_grade_tree,
    store_moodle_gradeitems,
    store_moodle_user_grade_items,
    store_moodle_user_grades_table,
    sync_moodle_categories_data,
    sync_moodle_catalog_data,
    update_moodle_grades,
)


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "sim", "yes", "y", "on"}


class MoodleBaseIntegrationAPIView(APIView):
    permission_classes = [IsAuthenticated, CanExportToAva]
    module_name = "integracao_moodle"

    def handle_moodle_error(self, exc: Exception):
        if isinstance(exc, MoodleConfigurationError):
            return Response({"detail": str(exc)}, status=503)
        if isinstance(exc, MoodleAuthenticationError):
            return Response({"detail": "Falha de autenticacao na integracao com o Moodle."}, status=502)
        if isinstance(exc, ValueError):
            return Response({"detail": str(exc)}, status=400)
        return Response({"detail": str(exc)}, status=502)


class MoodleCategoriesIntegrationAPIView(MoodleBaseIntegrationAPIView):
    def get(self, request):
        criteria = request.query_params.dict()

        try:
            categories = get_moodle_categories(criteria=criteria)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response({"count": len(categories), "results": categories})

    def post(self, request):
        criteria = request.data.get("criteria") or {}

        try:
            summary = sync_moodle_categories_data(category_criteria=criteria)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                "detail": "Categorias do Moodle armazenadas localmente com sucesso.",
                "summary": {
                    "categories_received": summary.categories_received,
                    "categories_created": summary.categories_created,
                    "categories_updated": summary.categories_updated,
                    "courses_received": summary.courses_received,
                    "courses_created": summary.courses_created,
                    "courses_updated": summary.courses_updated,
                    "courses_linked_internal": summary.courses_linked_internal,
                },
            }
        )


class MoodleCoursesIntegrationAPIView(MoodleBaseIntegrationAPIView):
    def get(self, request):
        try:
            courses = get_moodle_courses()
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response({"count": len(courses), "results": courses})

    def post(self, request):
        unidade_codigo = (request.data.get("unidade_codigo") or request.query_params.get("unidade_codigo") or "sede").strip().lower()
        integrar_catalogo_interno = _as_bool(
            request.data.get("integrar_catalogo_interno")
            if "integrar_catalogo_interno" in request.data
            else request.query_params.get("integrar_catalogo_interno"),
            default=True,
        )

        try:
            if integrar_catalogo_interno:
                summary = import_moodle_courses_to_formacao_inicial(unidade_codigo=unidade_codigo)
            else:
                storage_summary, courses = sync_moodle_catalog_data()
                summary = {
                    "unidade_codigo": unidade_codigo,
                    "total_received": len(courses),
                    "created": 0,
                    "updated": 0,
                    "linked_existing": 0,
                    "skipped": 0,
                    "catalog_storage": storage_summary,
                }
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        if isinstance(summary, dict):
            catalog_storage = summary["catalog_storage"]
            summary_payload = summary
        else:
            catalog_storage = summary.catalog_storage
            summary_payload = {
                "unidade_codigo": summary.unidade_codigo,
                "total_received": summary.total_received,
                "created": summary.created,
                "updated": summary.updated,
                "linked_existing": summary.linked_existing,
                "skipped": summary.skipped,
            }

        return Response(
            {
                "detail": (
                    "Cursos do Moodle armazenados localmente e integrados ao catalogo interno com sucesso."
                    if integrar_catalogo_interno
                    else "Cursos e categorias do Moodle armazenados localmente com sucesso."
                ),
                "summary": summary_payload,
                "catalog_storage": {
                    "categories_received": catalog_storage.categories_received if catalog_storage else 0,
                    "categories_created": catalog_storage.categories_created if catalog_storage else 0,
                    "categories_updated": catalog_storage.categories_updated if catalog_storage else 0,
                    "courses_received": catalog_storage.courses_received if catalog_storage else 0,
                    "courses_created": catalog_storage.courses_created if catalog_storage else 0,
                    "courses_updated": catalog_storage.courses_updated if catalog_storage else 0,
                    "courses_linked_internal": catalog_storage.courses_linked_internal if catalog_storage else 0,
                },
            }
        )


class MoodleGradesIntegrationAPIView(MoodleBaseIntegrationAPIView):
    ACTION_MAP = {
        "grade_tree": store_moodle_grade_tree,
        "gradeitems": store_moodle_gradeitems,
        "user_grade_items": store_moodle_user_grade_items,
        "user_grades_table": store_moodle_user_grades_table,
        "update_grades": update_moodle_grades,
    }

    def post(self, request):
        action = (request.data.get("action") or "").strip().lower()
        params = request.data.get("params") or {}
        handler = self.ACTION_MAP.get(action)

        if handler is None:
            return Response({"detail": "Acao de notas do Moodle nao suportada."}, status=400)

        try:
            stored_record = handler(params)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        if action == "update_grades":
            return Response(
                {
                    "detail": "Operacao de atualizacao de notas enviada ao Moodle e registrada localmente.",
                    "log_id": stored_record.id,
                    "status": stored_record.status,
                    "wsfunction": stored_record.wsfunction,
                }
            )

        return Response(
            {
                "detail": "Dados de notas do Moodle consultados e armazenados localmente.",
                "snapshot_id": stored_record.id,
                "snapshot_type": stored_record.snapshot_type,
                "wsfunction": stored_record.wsfunction,
                "moodle_course_id": stored_record.moodle_course_id,
                "moodle_user_id": stored_record.moodle_user_id,
            }
        )


class MoodleAssignmentsIntegrationAPIView(MoodleBaseIntegrationAPIView):
    ACTION_MAP = {
        "save_grade": save_moodle_assignment_grade,
        "save_grades": save_moodle_assignment_grades,
    }

    def post(self, request):
        action = (request.data.get("action") or "").strip().lower()
        params = request.data.get("params") or {}
        handler = self.ACTION_MAP.get(action)

        if handler is None:
            return Response({"detail": "Acao de assignment do Moodle nao suportada."}, status=400)

        try:
            log = handler(params)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                "detail": "Operacao de assignment enviada ao Moodle e registrada localmente.",
                "log_id": log.id,
                "status": log.status,
                "wsfunction": log.wsfunction,
            }
        )