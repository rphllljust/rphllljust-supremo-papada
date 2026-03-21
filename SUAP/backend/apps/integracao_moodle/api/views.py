from django.db.models import Q
from django.db import transaction
import logging

logger = logging.getLogger(__name__)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanExportToAva
from apps.integracao_moodle.api.serializers import MoodleCategoryMirrorSerializer, MoodleCourseMirrorSerializer
from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.models import MoodleCategory, MoodleCourse
from apps.integracao_moodle.services import (
    MOODLE_COURSE_ROOT_CATEGORY_IDS,
    create_moodle_courses,
    delete_moodle_courses,
    get_moodle_categories,
    get_moodle_courses,
    get_moodle_courses_by_field,
    get_moodle_recent_courses,
    import_moodle_courses_by_type,
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
    LOCAL_COURSE_FIELD_MAP = {
        "id": "moodle_course_id",
        "shortname": "shortname",
        "idnumber": "idnumber",
        "fullname": "fullname",
        "displayname": "displayname",
        "categoryid": "categoria__moodle_category_id",
    }

    def handle_moodle_error(self, exc: Exception):
        if isinstance(exc, MoodleConfigurationError):
            return Response({"detail": str(exc)}, status=503)
        if isinstance(exc, MoodleAuthenticationError):
            return Response({"detail": "Falha de autenticacao na integracao com o Moodle."}, status=502)
        if isinstance(exc, ValueError):
            return Response({"detail": str(exc)}, status=400)
        return Response({"detail": str(exc)}, status=502)

    def get_local_categories_queryset(self):
        return MoodleCategory.objects.select_related("parent").order_by("depth", "sortorder", "nome")

    def get_local_courses_queryset(self):
        return MoodleCourse.objects.select_related("categoria", "curso", "curso__unidade", "curso__area_curso").order_by("fullname")

    def parse_root_category_ids(self, value) -> list[int]:
        if value in (None, ""):
            return []

        if isinstance(value, (list, tuple)):
            raw_values = value
        else:
            raw_values = [chunk.strip() for chunk in str(value).split(",") if chunk.strip()]

        parsed_ids = []
        for raw_value in raw_values:
            try:
                parsed_ids.append(int(raw_value))
            except (TypeError, ValueError) as exc:
                raise ValueError("Informe IDs de categorias Moodle validos.") from exc

        return sorted(set(parsed_ids))

    def resolve_root_category_ids(self, tipo_curso: str | None, root_category_ids=None) -> list[int]:
        parsed_root_category_ids = self.parse_root_category_ids(root_category_ids)
        if parsed_root_category_ids:
            return parsed_root_category_ids

        normalized_tipo_curso = (tipo_curso or "").strip().lower()
        if not normalized_tipo_curso:
            return []
        if normalized_tipo_curso not in MOODLE_COURSE_ROOT_CATEGORY_IDS:
            raise ValueError(f"Tipo de curso '{normalized_tipo_curso}' nao suportado para sincronizacao Moodle.")
        return list(MOODLE_COURSE_ROOT_CATEGORY_IDS[normalized_tipo_curso])

    def filter_local_courses_by_root_categories(self, queryset, root_category_ids: list[int]):
        if not root_category_ids:
            return queryset

        filters = Q()
        for root_category_id in root_category_ids:
            filters |= Q(categoria__moodle_category_id=root_category_id)
            filters |= Q(categoria__path__icontains=f"/{root_category_id}/")
            filters |= Q(categoria__path__endswith=f"/{root_category_id}")

        return queryset.filter(filters).distinct()

    def serialize_local_categories(self, queryset=None):
        queryset = queryset or self.get_local_categories_queryset()
        return MoodleCategoryMirrorSerializer(queryset, many=True).data

    def serialize_local_courses(self, queryset=None):
        queryset = queryset or self.get_local_courses_queryset()
        return MoodleCourseMirrorSerializer(queryset, many=True).data

    def sync_categories_to_local(self, *, criteria=None):
        return sync_moodle_categories_data(category_criteria=criteria or {})

    def sync_courses_to_local(self):
        return sync_moodle_catalog_data(category_criteria={})

    def build_local_course_search_queryset(self, search_term: str):
        normalized = (search_term or "").strip()
        queryset = self.get_local_courses_queryset()
        if not normalized:
            return queryset
        return queryset.filter(
            Q(fullname__icontains=normalized)
            | Q(displayname__icontains=normalized)
            | Q(shortname__icontains=normalized)
            | Q(idnumber__icontains=normalized)
            | Q(categoria__nome__icontains=normalized)
            | Q(curso__nome__icontains=normalized)
            | Q(curso__sigla__icontains=normalized)
        )

    def build_local_course_field_queryset(self, field: str, value):
        field_name = self.LOCAL_COURSE_FIELD_MAP.get((field or "").strip().lower())
        if not field_name:
            raise ValueError(f"Campo '{field}' nao suportado para consulta local do espelho Moodle.")

        queryset = self.get_local_courses_queryset()
        if value is None or value == "":
            return queryset.none()

        if field_name in {"moodle_course_id", "categoria__moodle_category_id"}:
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Valor invalido para o campo '{field}'.") from exc
            return queryset.filter(**{field_name: value})

        return queryset.filter(**{f"{field_name}__iexact": str(value).strip()})


class MoodleCategoriesMirrorAPIView(MoodleBaseIntegrationAPIView):
    def get(self, request):
        serialized = self.serialize_local_categories()
        return Response({"count": len(serialized), "results": serialized})


class MoodleCoursesMirrorAPIView(MoodleBaseIntegrationAPIView):
    def get(self, request):
        search = request.query_params.get("search") or request.query_params.get("q") or ""
        queryset = self.build_local_course_search_queryset(search)
        root_category_ids = self.resolve_root_category_ids(
            request.query_params.get("tipo_curso"),
            request.query_params.get("root_category_ids") or request.query_params.get("root_category_id"),
        )
        queryset = self.filter_local_courses_by_root_categories(queryset, root_category_ids)
        serialized = self.serialize_local_courses(queryset)
        return Response({"count": len(serialized), "results": serialized})


class MoodleCategoriesSyncAPIView(MoodleBaseIntegrationAPIView):
    def post(self, request):
        criteria = request.data.get("criteria") or {}

        try:
            summary = self.sync_categories_to_local(criteria=criteria)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                "detail": "Categorias do Moodle sincronizadas para o espelho local do SUAP.",
                "summary": {
                    "categories_received": summary.categories_received,
                    "categories_created": summary.categories_created,
                    "categories_updated": summary.categories_updated,
                },
            }
        )


class MoodleCoursesSyncAPIView(MoodleBaseIntegrationAPIView):
    def post(self, request):
        unidade_codigo = (request.data.get("unidade_codigo") or request.query_params.get("unidade_codigo") or "sede").strip().lower()
        tipo_curso = (request.data.get("tipo_curso") or request.query_params.get("tipo_curso") or "formacao_inicial").strip().lower()
        root_category_ids = self.resolve_root_category_ids(
            tipo_curso,
            request.data.get("root_category_ids")
            or request.data.get("root_category_id")
            or request.query_params.get("root_category_ids")
            or request.query_params.get("root_category_id"),
        )
        integrar_catalogo_interno = _as_bool(
            request.data.get("integrar_catalogo_interno")
            if "integrar_catalogo_interno" in request.data
            else request.query_params.get("integrar_catalogo_interno"),
            default=True,
        )

        try:
            if integrar_catalogo_interno:
                summary = import_moodle_courses_by_type(
                    unidade_codigo=unidade_codigo,
                    tipo_curso=tipo_curso,
                    root_category_ids=root_category_ids,
                )
            else:
                storage_summary, courses = self.sync_courses_to_local()
                summary = {
                    "unidade_codigo": unidade_codigo,
                    "tipo_curso": tipo_curso,
                    "total_received": len(courses),
                    "created": 0,
                    "updated": 0,
                    "linked_existing": 0,
                    "skipped": 0,
                    "catalog_storage": self._serialize_catalog_storage(storage_summary),
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
                "tipo_curso": tipo_curso,
                "root_category_ids": root_category_ids,
                "total_received": summary.total_received,
                "created": summary.created,
                "updated": summary.updated,
                "linked_existing": summary.linked_existing,
                "skipped": summary.skipped,
            }

        return Response(
            {
                "detail": (
                    "Cursos do Moodle sincronizados e integrados ao catalogo interno do SUAP."
                    if integrar_catalogo_interno
                    else "Cursos do Moodle sincronizados para o espelho local do SUAP."
                ),
                "tipo_curso": tipo_curso,
                "root_category_ids": root_category_ids,
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


class MoodleCategoriesIntegrationAPIView(MoodleBaseIntegrationAPIView):
    def get(self, request):
        criteria = request.query_params.dict()
        source = (criteria.pop("source", "local") or "local").strip().lower()
        sync = _as_bool(criteria.pop("sync", None), default=False)

        if source == "live" or sync:
            try:
                self.sync_categories_to_local(criteria=criteria)
            except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
                return self.handle_moodle_error(exc)

        serialized = self.serialize_local_categories()
        return Response({"count": len(serialized), "results": serialized})

    def post(self, request):
        # Support both: sync local mirror (no action) and write actions via `action` param
        action = (request.data.get("action") or "").strip().lower()

        if action:
            params = request.data.get("params") or {}
            try:
                if action == "core_course_create_categories":
                    payload = create_moodle_categories(params)
                    # Persist created categories locally if Moodle returned them
                    try:
                        from apps.integracao_moodle.services import persist_moodle_categories, _extract_category_ids

                        def _normalize_created_categories_response(response_payload, request_params):
                            # Moodle may return only ids (or a partial payload). When that happens,
                            # fall back to the original request payload so we preserve the parent.
                            if isinstance(response_payload, dict) and isinstance(response_payload.get("categories"), list):
                                response_items = list(response_payload["categories"])
                            elif isinstance(response_payload, list):
                                response_items = list(response_payload)
                            elif isinstance(response_payload, dict):
                                response_items = [response_payload]
                            else:
                                response_items = []

                            request_items = []
                            if isinstance(request_params, dict) and isinstance(request_params.get("categories"), list):
                                request_items = list(request_params["categories"])
                            elif isinstance(request_params, list):
                                request_items = list(request_params)
                            elif isinstance(request_params, dict) and isinstance(request_params.get("params"), list):
                                request_items = list(request_params["params"])

                            normalized = []
                            for index, response_item in enumerate(response_items):
                                request_item = request_items[index] if index < len(request_items) and isinstance(request_items[index], dict) else {}
                                if not isinstance(response_item, dict):
                                    response_item = {}

                                merged = dict(request_item)
                                merged.update(response_item)

                                # ensure essential fields exist so the local mirror can rebuild the tree
                                if "parent" not in merged:
                                    merged["parent"] = request_item.get("parent", 0)
                                if "name" not in merged:
                                    merged["name"] = request_item.get("name") or request_item.get("nome") or ""

                                normalized.append(merged)

                            return normalized

                        created_ids = _extract_category_ids(payload) or []
                        normalized_payload = _normalize_created_categories_response(payload, params)

                        if normalized_payload:
                            persist_moodle_categories(normalized_payload)
                        elif created_ids:
                            # fetch those specific categories and persist
                            cats = get_moodle_categories(criteria={"ids": created_ids})
                            persist_moodle_categories(cats)
                    except Exception:
                        logger.exception("Failed to persist created Moodle categories locally")

                    return Response({"detail": "Categorias criadas no Moodle.", "moodle_response": payload})

                if action == "core_course_update_categories":
                    payload = update_moodle_categories(params)
                    try:
                        from apps.integracao_moodle.services import persist_moodle_categories, _extract_category_ids

                        updated_ids = _extract_category_ids(payload) or []
                        if isinstance(payload, list) and payload:
                            persist_moodle_categories(payload)
                        elif updated_ids:
                            cats = get_moodle_categories(criteria={"ids": updated_ids})
                            persist_moodle_categories(cats)
                    except Exception:
                        logger.exception("Failed to persist updated Moodle categories locally")

                    return Response({"detail": "Categorias atualizadas no Moodle.", "moodle_response": payload})

                if action == "core_course_delete_categories":
                    payload = delete_moodle_categories(params)
                    try:
                        from apps.integracao_moodle.services import _extract_category_ids, remove_local_categories_by_ids

                        deleted_ids = _extract_category_ids(payload) or []
                        # fallback: try to extract from params (support `categoryids` convenience param)
                        if not deleted_ids:
                            deleted_ids = _extract_category_ids(params) or []

                        if not deleted_ids and isinstance(params, dict):
                            raw_ids = params.get('categoryids') or params.get('categoryids[]')
                            if raw_ids:
                                try:
                                    if isinstance(raw_ids, (list, tuple)):
                                        deleted_ids = [int(x) for x in raw_ids]
                                    else:
                                        # comma-separated string
                                        deleted_ids = [int(x.strip()) for x in str(raw_ids).split(',') if x.strip()]
                                except Exception:
                                    deleted_ids = []

                        if deleted_ids:
                            removed_count = remove_local_categories_by_ids(deleted_ids)
                            logger.info("Removed %s local MoodleCategory records for deleted ids: %s", removed_count, deleted_ids)
                    except Exception:
                        logger.exception("Failed to remove local Moodle categories after delete action")

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

        params = request.query_params.dict()
        source = (params.pop("source", "local") or "local").strip().lower()
        sync = _as_bool(params.pop("sync", None), default=False)

        if source == "live" or sync:
            try:
                self.sync_courses_to_local()
            except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
                return self.handle_moodle_error(exc)

        serialized = self.serialize_local_courses()
        return Response({"count": len(serialized), "results": serialized})

    def post(self, request):
        action = (request.data.get("action") or "").strip().lower()
        if action:
            return self._handle_write_action(request, action)

        unidade_codigo = (request.data.get("unidade_codigo") or request.query_params.get("unidade_codigo") or "sede").strip().lower()
        tipo_curso = (request.data.get("tipo_curso") or request.query_params.get("tipo_curso") or "formacao_inicial").strip().lower()
        root_category_ids = self.resolve_root_category_ids(
            tipo_curso,
            request.data.get("root_category_ids")
            or request.data.get("root_category_id")
            or request.query_params.get("root_category_ids")
            or request.query_params.get("root_category_id"),
        )
        integrar_catalogo_interno = _as_bool(
            request.data.get("integrar_catalogo_interno")
            if "integrar_catalogo_interno" in request.data
            else request.query_params.get("integrar_catalogo_interno"),
            default=True,
        )

        try:
            if integrar_catalogo_interno:
                summary = import_moodle_courses_by_type(
                    unidade_codigo=unidade_codigo,
                    tipo_curso=tipo_curso,
                    root_category_ids=root_category_ids,
                )
            else:
                storage_summary, courses = sync_moodle_catalog_data()
                summary = {
                    "unidade_codigo": unidade_codigo,
                    "tipo_curso": tipo_curso,
                    "total_received": len(courses),
                    "created": 0,
                    "updated": 0,
                    "linked_existing": 0,
                    "skipped": 0,
                    "catalog_storage": self._serialize_catalog_storage(storage_summary),
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
                "tipo_curso": tipo_curso,
                "root_category_ids": root_category_ids,
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
                "tipo_curso": tipo_curso,
                "root_category_ids": root_category_ids,
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
        source = (params.pop("source", "local") or "local").strip().lower()
        sync = _as_bool(params.pop("sync", None), default=False)

        if source == "live" or sync:
            try:
                self.sync_courses_to_local()
            except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
                return self.handle_moodle_error(exc)

        try:
            if action == "core_course_get_courses_by_field":
                queryset = self.build_local_course_field_queryset(params.get("field", ""), params.get("value"))
                serialized = self.serialize_local_courses(queryset)
                return Response({"action": action, "count": len(serialized), "results": serialized})

            if action == "core_course_get_recent_courses":
                if not (source == "live" or sync):
                    return Response(
                        {
                            "action": action,
                            "count": 0,
                            "results": [],
                            "detail": "Consulta de cursos recentes exige sincronizacao live enquanto o SUAP nao persiste historico de acesso por usuario.",
                        }
                    )

                live_courses = get_moodle_recent_courses(params)
                course_ids = [course.get("id") for course in live_courses if course.get("id") is not None]
                queryset = self.get_local_courses_queryset().filter(moodle_course_id__in=course_ids)
                serialized = self.serialize_local_courses(queryset)
                return Response({"action": action, "count": len(serialized), "results": serialized})

            queryset = self.build_local_course_search_queryset(params.get("criteriavalue") or params.get("search") or "")
            serialized = self.serialize_local_courses(queryset)
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError, ValueError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                "action": action,
                "count": len(serialized),
                "total": len(serialized),
                "warnings": [],
                "courses": serialized,
                "results": serialized,
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


class MoodleCategoriesDiffAndSyncAPIView(APIView):
    """GET: retorna um resumo das diferenças entre categorias do Moodle (live)
    e o espelho local (`MoodleCategory`).

    POST: executa a mesma operação de reset+sync — apaga categorias no Moodle
    e cria a estrutura gerada por `sync_and_create_moodle_structured_categories()`.
    """
    permission_classes = [IsAuthenticated, CanExportToAva]

    def get(self, request):
        try:
            live = get_moodle_categories()
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        from apps.integracao_moodle.models import MoodleCategory

        local = list(MoodleCategory.objects.all().values_list('moodle_category_id', flat=True))

        live_ids = {c.get('id') for c in live if c.get('id') is not None}
        local_ids = set(int(x) for x in local if x is not None)

        only_in_live = sorted(list(live_ids - local_ids))
        only_in_local = sorted(list(local_ids - live_ids))

        return Response(
            {
                'count_live': len(live_ids),
                'count_local': len(local_ids),
                'only_in_live_count': len(only_in_live),
                'only_in_local_count': len(only_in_local),
                'only_in_live_preview': only_in_live[:100],
                'only_in_local_preview': only_in_local[:100],
            }
        )

    def post(self, request):
        # Perform reset & sync (same behaviour as MoodleCategoriesResetAndSyncAPIView)
        try:
            categories = get_moodle_categories()
            ids = [cat['id'] for cat in categories if 'id' in cat]
            deletion_results = None
            if ids:
                deletion_results = delete_moodle_categories({'categoryids': ids})
            created_ids = sync_and_create_moodle_structured_categories()
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)

        return Response(
            {
                'detail': 'Sincronizacao executada: Moodle resetado e sincronizado com SUAP.',
                'created_ids': created_ids,
                'deletion_results': deletion_results,
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


class MoodleLocalResetAndSyncAPIView(MoodleBaseIntegrationAPIView):
    permission_classes = [IsAuthenticated, CanExportToAva]

    def post(self, request):
        """Wipe local mirror tables and repopulate from live Moodle.

        Deletes local mirror records (`MoodleCourse`, `MoodleCategory`,
        `MoodleGradeSnapshot`, `MoodleWritebackLog`) and then calls
        `sync_moodle_catalog_data()` to fetch and persist fresh data from
        the Moodle instance.
        """
        try:
            from apps.integracao_moodle.models import (
                MoodleCategory,
                MoodleCourse,
                MoodleGradeSnapshot,
                MoodleWritebackLog,
            )

            with transaction.atomic():
                deleted = {}
                deleted["moodle_courses"] = MoodleCourse.objects.all().delete()[0]
                deleted["moodle_categories"] = MoodleCategory.objects.all().delete()[0]
                deleted["grade_snapshots"] = MoodleGradeSnapshot.objects.all().delete()[0]
                deleted["writeback_logs"] = MoodleWritebackLog.objects.all().delete()[0]

            summary, courses = sync_moodle_catalog_data()
        except (MoodleConfigurationError, MoodleAuthenticationError, MoodleAPIError) as exc:
            return self.handle_moodle_error(exc)
        except Exception as exc:
            logger.exception("Failed resetting local Moodle mirror: %s", exc)
            return Response({"detail": str(exc)}, status=500)

        return Response(
            {
                "detail": "Espelho local reinicializado e sincronizado a partir do Moodle.",
                "deleted_counts": deleted,
                "summary": {
                    "categories_received": summary.categories_received,
                    "categories_created": summary.categories_created,
                    "categories_updated": summary.categories_updated,
                    "courses_received": summary.courses_received,
                    "courses_created": summary.courses_created,
                    "courses_updated": summary.courses_updated,
                    "courses_linked_internal": summary.courses_linked_internal,
                },
                "courses_synced": len(courses),
            }
        )