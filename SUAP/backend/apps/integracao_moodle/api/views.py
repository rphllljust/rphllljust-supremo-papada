from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanExportToAva
from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.services import (
    create_moodle_courses,
    delete_moodle_courses,
    get_moodle_categories,
    get_moodle_courses,
    get_moodle_courses_by_field,
    get_moodle_recent_courses,
    import_moodle_courses_to_formacao_inicial,
    save_moodle_assignment_grade,
    save_moodle_assignment_grades,
    search_moodle_courses,
    store_moodle_grade_tree,
    store_moodle_gradeitems,
    store_moodle_user_grade_items,
    store_moodle_user_grades_table,
    sync_moodle_categories_data,
    create_moodle_categories,
    update_moodle_categories,
    delete_moodle_categories,
    sync_moodle_catalog_data,
    update_moodle_grades,
    update_moodle_courses,
    view_moodle_course,
    sync_and_create_moodle_structured_categories,
)
from django.conf import settings

# Allow ad-hoc test of Moodle connection using core_webservice_get_site_info.
from ..client import MoodleApiClient, MoodleApiSettings
from ..models import MoodleIntegrationConfig


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
        # Support both: sync local mirror (no action) and write actions via `action` param
        action = (request.data.get("action") or "").strip().lower()

        if action:
            params = request.data.get("params") or {}
            try:
                if action == "core_course_create_categories":
                    payload = create_moodle_categories(params)
                    return Response({"detail": "Categorias criadas no Moodle.", "moodle_response": payload})

                if action == "core_course_update_categories":
                    payload = update_moodle_categories(params)
                    return Response({"detail": "Categorias atualizadas no Moodle.", "moodle_response": payload})

                if action == "core_course_delete_categories":
                    payload = delete_moodle_categories(params)
                    return Response({"detail": "Categorias excluidas no Moodle.", "moodle_response": payload})

                return Response({"detail": "Acao de categorias do Moodle nao suportada."}, status=400)
            except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
                return self.handle_moodle_error(exc)

        # Default: sync and persist categories locally
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

    def delete(self, request):
        """Support HTTP DELETE to remove categories using `categoryids`.

        Accepts either JSON body like `{ "categoryids": [1,2] }` or
        query string `?categoryids=1,2` for convenience.
        """
        # prefer JSON body when provided
        params = {}
        if isinstance(request.data, dict) and request.data:
            params = dict(request.data)
        else:
            # Try to read list-based query params (categoryids or categoryids[])
            query = request.query_params
            ids = []
            # QueryDict provides getlist
            try:
                ids = query.getlist('categoryids') or query.getlist('categoryids[]')
            except Exception:
                # fallback to parsing comma-separated single param
                raw = query.get('categoryids')
                if raw:
                    ids = [x.strip() for x in raw.split(',') if x.strip()]

            if ids:
                try:
                    params['categoryids'] = [int(x) for x in ids]
                except Exception:
                    return Response({"detail": "Param categoryids invalido."}, status=400)

        try:
            payload = delete_moodle_categories(params)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        return Response({"detail": "Categorias excluidas no Moodle.", "moodle_response": payload})


class MoodleCoursesIntegrationAPIView(MoodleBaseIntegrationAPIView):
    READ_ACTIONS = {
        "core_course_get_courses_by_field",
        "core_course_get_recent_courses",
        "core_course_search_courses",
    }
    WRITE_ACTIONS = {
        "core_course_create_courses",
        "core_course_update_courses",
        "core_course_delete_courses",
        "core_course_view_course",
    }

    def get(self, request):
        action = (request.query_params.get("action") or "").strip().lower()
        if action:
            return self._handle_read_action(request, action)

        try:
            courses = get_moodle_courses()
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response({"count": len(courses), "results": courses})

    def post(self, request):
        action = (request.data.get("action") or "").strip().lower()
        if action:
            return self._handle_write_action(request, action)

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

    def _handle_read_action(self, request, action: str):
        if action not in self.READ_ACTIONS:
            return Response({"detail": "Acao de consulta de cursos do Moodle nao suportada."}, status=400)

        params = request.query_params.dict()
        params.pop("action", None)

        try:
            if action == "core_course_get_courses_by_field":
                courses = get_moodle_courses_by_field(params.get("field", ""), params.get("value"))
                return Response({"action": action, "count": len(courses), "results": courses})

            if action == "core_course_get_recent_courses":
                courses = get_moodle_recent_courses(params)
                # Return plain list of courses to match Moodle's `core_course_get_recent_courses` response
                return Response(courses)

            result = search_moodle_courses(params)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                "action": action,
                "count": len(result.get("courses", [])),
                "total": result.get("total"),
                "warnings": result.get("warnings", []),
                "courses": result.get("courses", []),
            }
        )

    def _handle_write_action(self, request, action: str):
        if action not in self.WRITE_ACTIONS:
            return Response({"detail": "Acao de gestao de cursos do Moodle nao suportada."}, status=400)

        params = request.data.get("params") or {}
        unidade_codigo = (request.data.get("unidade_codigo") or request.query_params.get("unidade_codigo") or "sede").strip().lower()
        persistir_espelho_local = _as_bool(
            request.data.get("persistir_espelho_local")
            if "persistir_espelho_local" in request.data
            else request.query_params.get("persistir_espelho_local"),
            default=True,
        )
        integrar_catalogo_interno = _as_bool(
            request.data.get("integrar_catalogo_interno")
            if "integrar_catalogo_interno" in request.data
            else request.query_params.get("integrar_catalogo_interno"),
            default=False,
        )
        desvincular_catalogo_interno = _as_bool(
            request.data.get("desvincular_catalogo_interno")
            if "desvincular_catalogo_interno" in request.data
            else request.query_params.get("desvincular_catalogo_interno"),
            default=True,
        )

        try:
            if action == "core_course_create_courses":
                result = create_moodle_courses(
                    params,
                    unidade_codigo=unidade_codigo,
                    persistir_espelho_local=persistir_espelho_local,
                    integrar_catalogo_interno=integrar_catalogo_interno,
                )
                return Response(
                    {
                        "detail": "Cursos criados no Moodle e processados pelo SUAP.",
                        "action": action,
                        "log_id": result["log"].id,
                        "course_ids": result["course_ids"],
                        "moodle_response": result["response_payload"],
                        "catalog_storage": self._serialize_catalog_storage(result["catalog_storage"]),
                        "summary": self._serialize_import_summary(result["import_summary"]),
                        "results": result["synced_courses"],
                    }
                )

            if action == "core_course_update_courses":
                result = update_moodle_courses(
                    params,
                    unidade_codigo=unidade_codigo,
                    persistir_espelho_local=persistir_espelho_local,
                    integrar_catalogo_interno=integrar_catalogo_interno,
                )
                return Response(
                    {
                        "detail": "Cursos atualizados no Moodle e processados pelo SUAP.",
                        "action": action,
                        "log_id": result["log"].id,
                        "course_ids": result["course_ids"],
                        "moodle_response": result["response_payload"],
                        "catalog_storage": self._serialize_catalog_storage(result["catalog_storage"]),
                        "summary": self._serialize_import_summary(result["import_summary"]),
                        "results": result["synced_courses"],
                    }
                )

            if action == "core_course_delete_courses":
                result = delete_moodle_courses(
                    params,
                    persistir_espelho_local=persistir_espelho_local,
                    desvincular_catalogo_interno=desvincular_catalogo_interno,
                )
                deletion_summary = result["deletion_summary"]
                return Response(
                    {
                        "detail": "Cursos excluidos no Moodle e refletidos localmente no SUAP.",
                        "action": action,
                        "log_id": result["log"].id,
                        "moodle_response": result["response_payload"],
                        "deletion_summary": {
                            "requested_ids": deletion_summary.requested_ids if deletion_summary else [],
                            "removed_local_records": deletion_summary.removed_local_records if deletion_summary else 0,
                            "unlinked_internal_courses": deletion_summary.unlinked_internal_courses if deletion_summary else 0,
                        },
                    }
                )

            result = view_moodle_course(params)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                "detail": "Visualizacao de curso registrada no Moodle.",
                "action": action,
                "log_id": result["log"].id,
                "moodle_response": result["response_payload"],
            }
        )

    def _serialize_catalog_storage(self, catalog_storage):
        if catalog_storage is None:
            return None

        return {
            "categories_received": catalog_storage.categories_received,
            "categories_created": catalog_storage.categories_created,
            "categories_updated": catalog_storage.categories_updated,
            "courses_received": catalog_storage.courses_received,
            "courses_created": catalog_storage.courses_created,
            "courses_updated": catalog_storage.courses_updated,
            "courses_linked_internal": catalog_storage.courses_linked_internal,
        }

    def _serialize_import_summary(self, summary):
        if summary is None:
            return None

        return {
            "unidade_codigo": summary.unidade_codigo,
            "total_received": summary.total_received,
            "created": summary.created,
            "updated": summary.updated,
            "linked_existing": summary.linked_existing,
            "skipped": summary.skipped,
        }


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


class MoodleCategoriesResetAndSyncAPIView(APIView):
    permission_classes = [IsAuthenticated, CanExportToAva]

    def post(self, request):
        # Apagar todas as categorias do Moodle
        categories = get_moodle_categories()
        ids = [cat["id"] for cat in categories]
        deletion_results = None
        if ids:
            deletion_results = delete_moodle_categories({"categoryids": ids})
        # Sincronizar nova estrutura
        created_ids = sync_and_create_moodle_structured_categories()
        return Response(
            {
                "detail": "Categorias do Moodle resetadas e sincronizadas com nova estrutura.",
                "created_ids": created_ids,
                "deletion_results": deletion_results,
            }
        )


class MoodleTestConnectionAPIView(MoodleBaseIntegrationAPIView):
    """Protected endpoint to test Moodle connectivity using core_webservice_get_site_info.

    Accepts optional `wstoken` and `moodlewsrestformat` in request data to override
    configured settings for ad-hoc testing.
    """

    def post(self, request):
        wstoken = (request.data.get("wstoken") or request.query_params.get("wstoken"))
        rest_format = (request.data.get("moodlewsrestformat") or request.query_params.get("moodlewsrestformat"))

        # Build a client using provided overrides or Django settings
        config = MoodleApiSettings(
            base_url=settings.MOODLE_BASE_URL,
            token=wstoken or settings.MOODLE_WS_TOKEN,
            rest_format=rest_format or settings.MOODLE_REST_FORMAT,
            timeout=getattr(settings, "MOODLE_TIMEOUT", None),
            rest_path=getattr(settings, "MOODLE_REST_PATH", "/webservice/rest/server.php"),
            verify_ssl=getattr(settings, "MOODLE_VERIFY_SSL", True),
        )

        client = MoodleApiClient(config=config)

        try:
            payload = client.call("core_webservice_get_site_info")
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response({"detail": "Conexao OK.", "site_info": payload})


class MoodleIntegrationConfigAPIView(MoodleBaseIntegrationAPIView):
    """GET/POST to read/update persisted Moodle integration settings."""

    def get(self, request):
        try:
            cfg = MoodleIntegrationConfig.objects.first()
        except Exception:
            cfg = None

        if not cfg:
            return Response(
                {
                    "base_url": settings.MOODLE_BASE_URL,
                    "wstoken": settings.MOODLE_WS_TOKEN,
                    "moodlewsrestformat": settings.MOODLE_REST_FORMAT,
                    "rest_path": settings.MOODLE_REST_PATH,
                    "timeout": getattr(settings, "MOODLE_TIMEOUT", None),
                    "verify_ssl": getattr(settings, "MOODLE_VERIFY_SSL", True),
                }
            )

        return Response(
            {
                "base_url": cfg.base_url,
                "wstoken": cfg.token,
                "moodlewsrestformat": cfg.rest_format,
                "rest_path": cfg.rest_path,
                "timeout": cfg.timeout,
                "verify_ssl": cfg.verify_ssl,
            }
        )

    def post(self, request):
        data = request.data or {}
        try:
            cfg, created = MoodleIntegrationConfig.objects.get_or_create(pk=1)
            cfg.base_url = data.get("base_url") or cfg.base_url
            cfg.token = data.get("wstoken") or cfg.token
            cfg.rest_format = data.get("moodlewsrestformat") or cfg.rest_format
            cfg.rest_path = data.get("rest_path") or cfg.rest_path
            cfg.timeout = data.get("timeout") if data.get("timeout") is not None else cfg.timeout
            cfg.verify_ssl = data.get("verify_ssl") if data.get("verify_ssl") is not None else cfg.verify_ssl
            cfg.save()
        except Exception as exc:
            logger.exception("Failed saving Moodle integration config: %s", exc)
            return Response({"detail": "Falha ao salvar configuracao."}, status=500)

        return Response({"detail": "Configuracao salva com sucesso."})