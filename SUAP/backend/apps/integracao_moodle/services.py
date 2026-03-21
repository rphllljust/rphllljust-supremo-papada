def create_moodle_categories(params: dict) -> dict | list:
    client = get_moodle_api_client()

    # Accept convenience shapes from frontend: a plain list of category objects
    # (params = [ {...} ]) or a wrapper { 'params': [ ... ] } and normalize to
    # the Moodle-expected { 'categories': [ {...} ] } with sensible defaults.
    normalized_params = None

    if isinstance(params, (list, tuple)):
        normalized_params = {"categories": list(params)}
    elif isinstance(params, dict) and isinstance(params.get("params"), (list, tuple)):
        normalized_params = {"categories": list(params.get("params"))}
    elif isinstance(params, dict) and isinstance(params.get("categories"), (list, tuple)):
        normalized_params = {"categories": list(params.get("categories"))}
    else:
        normalized_params = dict(params or {})

    # Ensure defaults for each category object
    cats = []
    for item in normalized_params.get("categories") or []:
        obj = dict(item) if isinstance(item, dict) else {"name": str(item)}
        # skip categories without a name to avoid creating anonymous/default ones
        name_val = (obj.get("name") or "").strip()
        if not name_val:
            logger.warning("Skipping category creation for item without name: %s", obj)
            continue
        obj["name"] = name_val
        if "parent" not in obj:
            obj["parent"] = 0
        if "descriptionformat" not in obj:
            obj["descriptionformat"] = 1
        if "idnumber" not in obj:
            obj["idnumber"] = ""
        if "description" not in obj:
            obj["description"] = ""
        if "theme" not in obj:
            obj["theme"] = ""
        cats.append(obj)
    if not cats:
        raise ValueError("Nenhuma categoria valida fornecida para criacao.")

    payload = {"categories": cats}
    logger.debug("Creating Moodle categories with payload=%s", payload)
    response_payload = client.create_categories(payload)
    logger.debug("Moodle create categories response: %s", response_payload)
    # TODO: armazenar localmente se necessário
    return response_payload

def update_moodle_categories(params: dict) -> dict | list:
    response_payload = get_moodle_api_client().update_categories(params)
    # TODO: atualizar localmente se necessário
    return response_payload

def delete_moodle_categories(params: dict) -> dict | list:
    # The Moodle API may reject bulk deletion for system or protected categories.
    # Handle deletion per-category id to be resilient: try deleting each id and
    # collect successes/failures.
    client = get_moodle_api_client()
    category_ids = []
    # Accept either `categoryids` (convenience) or a properly formatted
    # `categories` list of objects as expected by Moodle.
    if isinstance(params, dict):
        if isinstance(params.get("categories"), (list, tuple)) and params.get("categories"):
            # normalize categories list: ensure each item has `recursive` (default to 1)
            normalized = []
            for item in params.get("categories"):
                obj = dict(item) if isinstance(item, dict) else {"id": item}
                if "recursive" not in obj:
                    obj["recursive"] = 1
                normalized.append(obj)
            try:
                return client.delete_categories({"categories": normalized})
            except Exception:
                # fallback to per-item deletion below
                category_ids = [c.get("id") for c in normalized if c.get("id")]

        if isinstance(params.get("categoryids"), (list, tuple)):
            category_ids = list(params.get("categoryids"))

    if not category_ids:
        # fallback to direct call when no explicit ids provided
        response_payload = client.delete_categories(params)
        return response_payload

    results = {"deleted": [], "failed": []}
    for cid in category_ids:
        try:
            params_to_send = {"categories": [{"id": cid, "recursive": 1}]}
            logger.debug("Deleting Moodle category with params=%s", params_to_send)
            payload = client.delete_categories(params_to_send)
            logger.debug("Moodle delete response for category %s: %s", cid, payload)
            results["deleted"].append({"id": cid, "response": payload})
        except Exception as exc:  # keep going on individual failures
            logger.exception("Failed deleting Moodle category %s: %s", cid, exc)
            results["failed"].append({"id": cid, "error": str(exc)})

    return results
import logging
from dataclasses import dataclass

from django.conf import settings
from django.db import transaction

from apps.cursos.models import Curso
from apps.unidades.models import Unidade

from .client import MoodleApiClient
from .models import MoodleCategory, MoodleCourse, MoodleGradeSnapshot, MoodleWritebackLog
from .schemas import MoodleApiSettings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MoodleCatalogStorageSummary:
    categories_received: int = 0
    categories_created: int = 0
    categories_updated: int = 0
    courses_received: int = 0
    courses_created: int = 0
    courses_updated: int = 0
    courses_linked_internal: int = 0


@dataclass(slots=True)
class MoodleCourseImportSummary:
    unidade_codigo: str
    total_received: int = 0
    created: int = 0
    updated: int = 0
    linked_existing: int = 0
    skipped: int = 0
    catalog_storage: MoodleCatalogStorageSummary | None = None


@dataclass(slots=True)
class MoodleCourseDeletionSummary:
    requested_ids: list[int]
    removed_local_records: int = 0
    unlinked_internal_courses: int = 0


MOODLE_COURSE_ROOT_CATEGORY_IDS = {
    "formacao_inicial": [399],
    "tecnico": [387],
    "itinerante": [415],
}


def get_moodle_api_client() -> MoodleApiClient:
    # Prefer persisted integration config in DB when available, falling back
    # to Django settings/env variables.
    try:
        from .models import MoodleIntegrationConfig

        config_obj = MoodleIntegrationConfig.objects.first()
    except Exception:
        config_obj = None

    if config_obj:
        return MoodleApiClient(
            config=MoodleApiSettings(
                base_url=config_obj.base_url or settings.MOODLE_BASE_URL,
                token=config_obj.token or settings.MOODLE_WS_TOKEN,
                rest_format=config_obj.rest_format or settings.MOODLE_REST_FORMAT,
                timeout=config_obj.timeout or settings.MOODLE_TIMEOUT,
                rest_path=config_obj.rest_path or settings.MOODLE_REST_PATH,
                verify_ssl=config_obj.verify_ssl if config_obj.verify_ssl is not None else settings.MOODLE_VERIFY_SSL,
            )
        )

    return MoodleApiClient.from_django_settings()


def get_moodle_courses() -> list[dict]:
    return get_moodle_api_client().get_courses()


def get_moodle_categories(criteria: dict | None = None) -> list[dict]:
    return get_moodle_api_client().get_categories(criteria=criteria)


def get_moodle_courses_by_field(field: str, value) -> list[dict]:
    return get_moodle_api_client().get_courses_by_field({"field": field, "value": value})


def get_moodle_recent_courses(params: dict) -> list[dict]:
    return get_moodle_api_client().get_recent_courses(params)


def search_moodle_courses(params: dict) -> dict:
    return get_moodle_api_client().search_courses(params)


def import_moodle_courses_to_formacao_inicial(unidade_codigo: str = "sede") -> MoodleCourseImportSummary:
    return import_moodle_courses_by_type(
        unidade_codigo=unidade_codigo,
        tipo_curso="formacao_inicial",
    )


def import_moodle_courses_by_type(
    unidade_codigo: str = "sede",
    *,
    tipo_curso: str = "formacao_inicial",
    root_category_ids: list[int] | tuple[int, ...] | None = None,
) -> MoodleCourseImportSummary:
    unidade = _get_unidade(unidade_codigo)
    normalized_tipo_curso = _normalize_course_type(tipo_curso)
    resolved_root_category_ids = _resolve_root_category_ids(normalized_tipo_curso, root_category_ids)

    categories = get_moodle_categories()
    courses = get_moodle_courses()
    storage_summary = _persist_moodle_catalog_payloads(categories, courses)
    filtered_courses = _filter_courses_by_root_categories(
        courses,
        categories,
        resolved_root_category_ids,
    )

    return _import_moodle_course_payloads(
        filtered_courses,
        unidade=unidade,
        catalog_storage=storage_summary,
        tipo_curso=normalized_tipo_curso,
    )


def sync_moodle_catalog_data(category_criteria: dict | None = None) -> tuple[MoodleCatalogStorageSummary, list[dict]]:
    categories = get_moodle_categories(criteria=category_criteria)
    courses = get_moodle_courses()
    summary = _persist_moodle_catalog_payloads(categories, courses)
    return summary, courses


def sync_moodle_categories_data(category_criteria: dict | None = None) -> MoodleCatalogStorageSummary:
    categories = get_moodle_categories(criteria=category_criteria)
    summary = MoodleCatalogStorageSummary(categories_received=len(categories))

    with transaction.atomic():
        _store_moodle_categories(categories, summary)

    return summary


def create_moodle_courses(
    params: dict,
    *,
    unidade_codigo: str = "sede",
    persistir_espelho_local: bool = True,
    integrar_catalogo_interno: bool = False,
) -> dict:
    return _execute_course_write_operation(
        wsfunction="core_course_create_courses",
        params=params,
        executor=get_moodle_api_client().create_courses,
        unidade_codigo=unidade_codigo,
        persistir_espelho_local=persistir_espelho_local,
        integrar_catalogo_interno=integrar_catalogo_interno,
    )


def update_moodle_courses(
    params: dict,
    *,
    unidade_codigo: str = "sede",
    persistir_espelho_local: bool = True,
    integrar_catalogo_interno: bool = False,
) -> dict:
    return _execute_course_write_operation(
        wsfunction="core_course_update_courses",
        params=params,
        executor=get_moodle_api_client().update_courses,
        unidade_codigo=unidade_codigo,
        persistir_espelho_local=persistir_espelho_local,
        integrar_catalogo_interno=integrar_catalogo_interno,
    )


def delete_moodle_courses(
    params: dict,
    *,
    persistir_espelho_local: bool = True,
    desvincular_catalogo_interno: bool = True,
) -> dict:
    response_payload = get_moodle_api_client().delete_courses(params)
    course_ids = _extract_course_ids(response_payload) or _extract_course_ids(params)
    log = _store_writeback_log(
        wsfunction="core_course_delete_courses",
        request_payload=params,
        response_payload=response_payload,
        moodle_course_id=course_ids[0] if len(course_ids) == 1 else None,
    )
    deletion_summary = None

    if persistir_espelho_local and course_ids:
        deletion_summary = _remove_deleted_courses_from_local_catalog(
            course_ids,
            desvincular_catalogo_interno=desvincular_catalogo_interno,
        )

    return {
        "response_payload": response_payload,
        "log": log,
        "deletion_summary": deletion_summary,
    }


def view_moodle_course(params: dict) -> dict:
    response_payload = get_moodle_api_client().view_course(params)
    course_ids = _extract_course_ids(response_payload) or _extract_course_ids(params)
    log = _store_writeback_log(
        wsfunction="core_course_view_course",
        request_payload=params,
        response_payload=response_payload,
        moodle_course_id=course_ids[0] if len(course_ids) == 1 else None,
    )
    return {
        "response_payload": response_payload,
        "log": log,
    }


def store_moodle_grade_tree(params: dict):
    return _store_grade_snapshot(
        snapshot_type="grade_tree",
        wsfunction="core_grades_get_grade_tree",
        request_params=params,
        response_payload=get_moodle_api_client().get_grade_tree(params),
    )


def store_moodle_gradeitems(params: dict):
    return _store_grade_snapshot(
        snapshot_type="gradeitems",
        wsfunction="core_grades_get_gradeitems",
        request_params=params,
        response_payload=get_moodle_api_client().get_gradeitems(params),
    )


def store_moodle_user_grade_items(params: dict):
    return _store_grade_snapshot(
        snapshot_type="user_grade_items",
        wsfunction="gradereport_user_get_grade_items",
        request_params=params,
        response_payload=get_moodle_api_client().get_user_grade_items(params),
    )


def store_moodle_user_grades_table(params: dict):
    return _store_grade_snapshot(
        snapshot_type="user_grades_table",
        wsfunction="gradereport_user_get_grades_table",
        request_params=params,
        response_payload=get_moodle_api_client().get_user_grades_table(params),
    )


def update_moodle_grades(params: dict):
    response_payload = get_moodle_api_client().update_grades(params)
    return _store_writeback_log(
        wsfunction="core_grades_update_grades",
        request_payload=params,
        response_payload=response_payload,
    )


def save_moodle_assignment_grade(params: dict):
    response_payload = get_moodle_api_client().save_assignment_grade(params)
    return _store_writeback_log(
        wsfunction="mod_assign_save_grade",
        request_payload=params,
        response_payload=response_payload,
    )


def save_moodle_assignment_grades(params: dict):
    response_payload = get_moodle_api_client().save_assignment_grades(params)
    return _store_writeback_log(
        wsfunction="mod_assign_save_grades",
        request_payload=params,
        response_payload=response_payload,
    )


def _should_skip_course(course_payload: dict) -> bool:
    if course_payload.get("format") == "site":
        return True
    return not (course_payload.get("fullname") or "").strip()


def _get_unidade(unidade_codigo: str) -> Unidade:
    normalized_unidade_codigo = (unidade_codigo or "sede").strip().lower()

    try:
        return Unidade.objects.get(codigo=normalized_unidade_codigo)
    except Unidade.DoesNotExist as exc:
        raise ValueError(f"Unidade '{normalized_unidade_codigo}' nao encontrada.") from exc


def _import_moodle_course_payloads(
    courses: list[dict],
    *,
    unidade: Unidade,
    catalog_storage: MoodleCatalogStorageSummary | None = None,
    tipo_curso: str = "formacao_inicial",
) -> MoodleCourseImportSummary:
    normalized_tipo_curso = _normalize_course_type(tipo_curso)
    summary = MoodleCourseImportSummary(
        unidade_codigo=unidade.codigo,
        total_received=len(courses),
        catalog_storage=catalog_storage,
    )

    with transaction.atomic():
        for course_payload in courses:
            if _should_skip_course(course_payload):
                summary.skipped += 1
                continue

            moodle_course_id = course_payload["id"]
            target_course = Curso.objects.filter(moodle_course_id=moodle_course_id).first()
            linked_existing = False

            if target_course is None:
                target_course = Curso.objects.filter(
                    unidade=unidade,
                    nome__iexact=(course_payload.get("fullname") or "").strip(),
                    moodle_course_id__isnull=True,
                    tipo_curso=normalized_tipo_curso,
                ).first()
                linked_existing = target_course is not None

            if target_course is None:
                target_course = Curso.objects.create(
                    **_build_new_course_data(
                        course_payload,
                        unidade,
                        tipo_curso=normalized_tipo_curso,
                    )
                )
                summary.created += 1
            else:
                _update_existing_course_from_moodle(
                    target_course,
                    course_payload,
                    unidade=unidade,
                    linked_existing=linked_existing,
                    tipo_curso=normalized_tipo_curso,
                )

                if linked_existing:
                    summary.linked_existing += 1
                else:
                    summary.updated += 1

            MoodleCourse.objects.filter(moodle_course_id=moodle_course_id).update(curso=target_course)

    logger.info(
        "Imported Moodle courses into Curso catalog unidade=%s created=%s updated=%s linked_existing=%s skipped=%s",
        summary.unidade_codigo,
        summary.created,
        summary.updated,
        summary.linked_existing,
        summary.skipped,
    )
    return summary


def _resolve_sigla(course_payload: dict) -> str:
    raw_sigla = (course_payload.get("shortname") or course_payload.get("displayname") or course_payload.get("fullname") or "").strip()
    return raw_sigla[:16]


def _build_new_course_data(course_payload: dict, unidade: Unidade, *, tipo_curso: str) -> dict:
    return {
        "tipo_curso": tipo_curso,
        "unidade": unidade,
        "area_curso": None,
        "nome": (course_payload.get("fullname") or "").strip(),
        "sigla": _resolve_sigla(course_payload),
        "moodle_course_id": course_payload["id"],
        "moodle_shortname": (course_payload.get("shortname") or "").strip(),
        "eixo_tecnologico": "",
        "carga_horaria": 0,
    }


def _update_existing_course_from_moodle(
    target_course: Curso,
    course_payload: dict,
    *,
    unidade: Unidade,
    linked_existing: bool,
    tipo_curso: str,
):
    target_course.tipo_curso = tipo_curso
    target_course.moodle_course_id = course_payload["id"]
    target_course.moodle_shortname = (course_payload.get("shortname") or "").strip()
    target_course.nome = (course_payload.get("fullname") or target_course.nome or "").strip()

    if not target_course.sigla:
        target_course.sigla = _resolve_sigla(course_payload)

    if not linked_existing:
        target_course.unidade = unidade

    target_course.save()


def _store_moodle_categories(categories: list[dict], summary: MoodleCatalogStorageSummary) -> dict[int, MoodleCategory]:
    category_map: dict[int, MoodleCategory] = {}

    for category_payload in categories:
        defaults = {
            "nome": (category_payload.get("name") or "").strip(),
            "idnumber": (category_payload.get("idnumber") or "").strip(),
            "descricao": category_payload.get("description") or "",
            "descricao_formato": category_payload.get("descriptionformat") or 0,
            "sortorder": category_payload.get("sortorder") or 0,
            "coursecount": category_payload.get("coursecount") or 0,
            "visible": bool(category_payload.get("visible", False)),
            "depth": category_payload.get("depth") or 0,
            "path": category_payload.get("path") or "",
            "timemodified": category_payload.get("timemodified"),
            "raw_payload": category_payload,
        }
        category, created = MoodleCategory.objects.update_or_create(
            moodle_category_id=category_payload["id"],
            defaults=defaults,
        )
        category_map[category.moodle_category_id] = category
        if created:
            summary.categories_created += 1
        else:
            summary.categories_updated += 1

    for category_payload in categories:
        parent_id = category_payload.get("parent") or 0
        if not parent_id:
            continue

        category = category_map.get(category_payload["id"]) or MoodleCategory.objects.filter(
            moodle_category_id=category_payload["id"]
        ).first()

        # Prefer the freshly-created/updated parent from the in-memory map; if absent,
        # try to resolve an existing local MoodleCategory by moodle_category_id so that
        # creating a subcategory (where the parent already exists locally) correctly
        # links the new child to its parent.
        parent = category_map.get(parent_id) or MoodleCategory.objects.filter(moodle_category_id=parent_id).first()

        if category is None or parent is None or category.parent_id == parent.id:
            continue

        category.parent = parent
        category.save(update_fields=["parent", "updated_at"])

    return category_map


def _store_moodle_courses(courses: list[dict], category_map: dict[int, MoodleCategory], summary: MoodleCatalogStorageSummary):
    for course_payload in courses:
        moodle_course_id = course_payload["id"]
        category = category_map.get(course_payload.get("categoryid"))
        linked_course = Curso.objects.filter(moodle_course_id=moodle_course_id).first()

        defaults = {
            "curso": linked_course,
            "categoria": category,
            "shortname": (course_payload.get("shortname") or "").strip(),
            "fullname": (course_payload.get("fullname") or "").strip(),
            "displayname": (course_payload.get("displayname") or "").strip(),
            "idnumber": (course_payload.get("idnumber") or "").strip(),
            "summary": course_payload.get("summary") or "",
            "summaryformat": course_payload.get("summaryformat") or 0,
            "format": (course_payload.get("format") or "").strip(),
            "visible": bool(course_payload.get("visible", False)),
            "startdate": course_payload.get("startdate"),
            "enddate": course_payload.get("enddate"),
            "timecreated": course_payload.get("timecreated"),
            "timemodified": course_payload.get("timemodified"),
            "enablecompletion": bool(course_payload.get("enablecompletion", False)),
            "showactivitydates": bool(course_payload.get("showactivitydates", False)),
            "showcompletionconditions": bool(course_payload.get("showcompletionconditions", False)),
            "courseformatoptions": course_payload.get("courseformatoptions") or [],
            "raw_payload": course_payload,
        }
        _, created = MoodleCourse.objects.update_or_create(
            moodle_course_id=moodle_course_id,
            defaults=defaults,
        )
        if created:
            summary.courses_created += 1
        else:
            summary.courses_updated += 1
        if linked_course is not None:
            summary.courses_linked_internal += 1


def _persist_moodle_catalog_payloads(
    categories: list[dict],
    courses: list[dict],
) -> MoodleCatalogStorageSummary:
    summary = MoodleCatalogStorageSummary(
        categories_received=len(categories),
        courses_received=len(courses),
    )

    with transaction.atomic():
        category_map = _store_moodle_categories(categories, summary)
        _store_moodle_courses(courses, category_map, summary)

    return summary


def _normalize_course_type(tipo_curso: str | None) -> str:
    normalized_tipo_curso = (tipo_curso or "formacao_inicial").strip().lower()
    if normalized_tipo_curso not in MOODLE_COURSE_ROOT_CATEGORY_IDS:
        raise ValueError(f"Tipo de curso '{normalized_tipo_curso}' nao suportado para sincronizacao Moodle.")
    return normalized_tipo_curso


def _resolve_root_category_ids(
    tipo_curso: str,
    root_category_ids: list[int] | tuple[int, ...] | None,
) -> list[int]:
    if root_category_ids:
        normalized_ids = sorted({int(category_id) for category_id in root_category_ids if category_id is not None})
        if normalized_ids:
            return normalized_ids

    return list(MOODLE_COURSE_ROOT_CATEGORY_IDS[_normalize_course_type(tipo_curso)])


def _collect_branch_category_ids(categories: list[dict], root_category_ids: list[int]) -> set[int]:
    normalized_roots = {int(category_id) for category_id in root_category_ids if category_id is not None}
    branch_ids: set[int] = set(normalized_roots)

    for category_payload in categories:
        category_id = _parse_int(category_payload.get("id"))
        if category_id is None:
            continue

        path_ids = {
            parsed_id
            for parsed_id in (_parse_int(chunk) for chunk in str(category_payload.get("path") or "").split("/"))
            if parsed_id is not None
        }

        if category_id in normalized_roots or normalized_roots.intersection(path_ids):
            branch_ids.add(category_id)

    return branch_ids


def _filter_courses_by_root_categories(
    courses: list[dict],
    categories: list[dict],
    root_category_ids: list[int],
) -> list[dict]:
    if not root_category_ids:
        return list(courses)

    branch_category_ids = _collect_branch_category_ids(categories, root_category_ids)
    if not branch_category_ids:
        return []

    filtered_courses = []
    for course_payload in courses:
        category_id = _parse_int(course_payload.get("categoryid"))
        if category_id in branch_category_ids:
            filtered_courses.append(course_payload)

    return filtered_courses


def _execute_course_write_operation(
    *,
    wsfunction: str,
    params: dict,
    executor,
    unidade_codigo: str,
    persistir_espelho_local: bool,
    integrar_catalogo_interno: bool,
) -> dict:
    response_payload = executor(params)
    course_ids = _extract_course_ids(response_payload) or _extract_course_ids(params)
    log = _store_writeback_log(
        wsfunction=wsfunction,
        request_payload=params,
        response_payload=response_payload,
        moodle_course_id=course_ids[0] if len(course_ids) == 1 else None,
    )

    catalog_storage = None
    import_summary = None
    synced_courses: list[dict] = []

    if persistir_espelho_local and course_ids:
        catalog_storage, import_summary, synced_courses = _sync_moodle_courses_by_ids(
            course_ids,
            unidade_codigo=unidade_codigo,
            integrar_catalogo_interno=integrar_catalogo_interno,
        )

    return {
        "response_payload": response_payload,
        "log": log,
        "course_ids": course_ids,
        "catalog_storage": catalog_storage,
        "import_summary": import_summary,
        "synced_courses": synced_courses,
    }


def _sync_moodle_courses_by_ids(
    course_ids: list[int],
    *,
    unidade_codigo: str,
    integrar_catalogo_interno: bool,
) -> tuple[MoodleCatalogStorageSummary | None, MoodleCourseImportSummary | None, list[dict]]:
    normalized_course_ids = sorted(set(course_ids))
    if not normalized_course_ids:
        return None, None, []

    courses = [course for course in get_moodle_courses() if course.get("id") in normalized_course_ids]
    if not courses:
        return None, None, []

    categories = get_moodle_categories()
    summary = _persist_moodle_catalog_payloads(categories, courses)

    import_summary = None
    if integrar_catalogo_interno:
        unidade = _get_unidade(unidade_codigo)
        import_summary = _import_moodle_course_payloads(
            courses,
            unidade=unidade,
            catalog_storage=summary,
        )

    return summary, import_summary, courses


def _remove_deleted_courses_from_local_catalog(
    course_ids: list[int],
    *,
    desvincular_catalogo_interno: bool,
) -> MoodleCourseDeletionSummary:
    summary = MoodleCourseDeletionSummary(requested_ids=sorted(set(course_ids)))
    if not summary.requested_ids:
        return summary

    with transaction.atomic():
        if desvincular_catalogo_interno:
            summary.unlinked_internal_courses = Curso.objects.filter(
                moodle_course_id__in=summary.requested_ids
            ).update(moodle_course_id=None, moodle_shortname="")

        summary.removed_local_records = MoodleCourse.objects.filter(
            moodle_course_id__in=summary.requested_ids
        ).delete()[0]

    return summary


def _store_grade_snapshot(*, snapshot_type: str, wsfunction: str, request_params: dict, response_payload):
    course_id = _extract_int(request_params, "courseid")
    user_id = _extract_int(request_params, "userid")
    course_record = MoodleCourse.objects.filter(moodle_course_id=course_id).first() if course_id else None

    return MoodleGradeSnapshot.objects.create(
        snapshot_type=snapshot_type,
        wsfunction=wsfunction,
        curso=course_record,
        moodle_course_id=course_id,
        moodle_user_id=user_id,
        request_payload=request_params,
        response_payload=response_payload,
    )


def _store_writeback_log(
    *,
    wsfunction: str,
    request_payload: dict,
    response_payload,
    status: str = "success",
    error_message: str = "",
    moodle_course_id: int | None = None,
):
    return MoodleWritebackLog.objects.create(
        wsfunction=wsfunction,
        status=status,
        moodle_course_id=moodle_course_id if moodle_course_id is not None else _extract_int(request_payload, "courseid"),
        moodle_assignment_id=_extract_int(request_payload, "assignmentid"),
        moodle_user_id=_extract_int(request_payload, "userid"),
        request_payload=request_payload,
        response_payload=response_payload,
        error_message=error_message,
    )


def _extract_course_ids(payload) -> list[int]:
    course_ids: list[int] = []

    def collect(value):
        if isinstance(value, list):
            for item in value:
                collect(item)
            return

        if isinstance(value, dict):
            if value.get("id") not in (None, ""):
                parsed = _parse_int(value.get("id"))
                if parsed is not None:
                    course_ids.append(parsed)
            if value.get("courseid") not in (None, ""):
                parsed = _parse_int(value.get("courseid"))
                if parsed is not None:
                    course_ids.append(parsed)
            if isinstance(value.get("courseids"), list):
                for course_id in value["courseids"]:
                    parsed = _parse_int(course_id)
                    if parsed is not None:
                        course_ids.append(parsed)
            if isinstance(value.get("courses"), list):
                collect(value["courses"])

    collect(payload)
    return sorted(set(course_ids))


def _extract_category_ids(payload) -> list[int]:
    ids: list[int] = []

    def collect(value):
        if isinstance(value, list):
            for item in value:
                collect(item)
            return

        if isinstance(value, dict):
            if value.get("id") not in (None, ""):
                parsed = _parse_int(value.get("id"))
                if parsed is not None:
                    ids.append(parsed)
            if isinstance(value.get("categories"), list):
                collect(value.get("categories"))

    collect(payload)
    return sorted(set(ids))


def persist_moodle_categories(categories: list[dict]) -> MoodleCatalogStorageSummary:
    """Persist a list of Moodle category payloads into local mirror and
    return a summary object describing counts created/updated.
    """
    summary = MoodleCatalogStorageSummary(categories_received=len(categories))
    with transaction.atomic():
        _store_moodle_categories(categories, summary)
    return summary


def remove_local_categories_by_ids(category_ids: list[int]) -> int:
    """Remove local `MoodleCategory` records for the given Moodle category ids.

    Returns the number of deleted records.
    """
    if not category_ids:
        return 0
    return MoodleCategory.objects.filter(moodle_category_id__in=category_ids).delete()[0]


def _extract_int(payload: dict, key: str) -> int | None:
    value = payload.get(key)
    if value in (None, ""):
        return None

    return _parse_int(value)


def _parse_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def sync_moodle_structured_categories():
    """
    Monta e sincroniza a estrutura de categorias do Moodle conforme o tipo de curso.
    Hierarquia:
    - Técnico: componentes curriculares
    - Formação Inicial: cursos simples
    - Itinerante: estrutura própria
    """
    from apps.cursos.models import Curso, ComponenteCurricular, EixoTecnologico
    from apps.unidades.models import Unidade

    # Categorias raiz
    root_categories = {
        "tecnico": {
            "name": "EDUCAÇÃO PROFISSIONAL TÉCNICA",
            "children": []
        },
        "formacao_inicial": {
            "name": "FORMAÇÃO INICIAL E CONTINUADA",
            "children": []
        },
        "itinerante": {
            "name": "QUALIFICAÇÃO PROFISSIONAL ITINERANTE",
            "children": []
        }
    }

    cursos = Curso.objects.all()
    for curso in cursos:
        if curso.tipo_curso == "tecnico":
            # Estrutura: Ano > Eixo Tecnológico > Polo > Curso > Módulos > Componentes
            eixo = curso.eixo_tecnologico or "Eixo"
            unidade = curso.unidade.nome
            ano = "2026"  # Pode ser dinâmico
            curso_cat = {
                "name": curso.nome,
                "children": []
            }
            # Componentes curriculares
            componentes = ComponenteCurricular.objects.filter(curso=curso)
            for comp in componentes:
                curso_cat["children"].append({"name": comp.nome})
            root_categories["tecnico"]["children"].append({
                "name": ano,
                "children": [{
                    "name": eixo,
                    "children": [{
                        "name": unidade,
                        "children": [curso_cat]
                    }]
                }]
            })
        elif curso.tipo_curso == "formacao_inicial":
            # Estrutura: Ano > Modalidade > Eixo Temático > Polo > Curso
            ano = "2026"
            modalidade = "Presencial"  # Pode ser dinâmico
            eixo = curso.eixo_tecnologico or "Eixo Temático"
            unidade = curso.unidade.nome
            root_categories["formacao_inicial"]["children"].append({
                "name": ano,
                "children": [{
                    "name": modalidade,
                    "children": [{
                        "name": eixo,
                        "children": [{
                            "name": unidade,
                            "children": [{"name": curso.nome}]
                        }]
                    }]
                }]
            })
        elif curso.tipo_curso == "itinerante":
            # Estrutura: Ano > Unidade Móvel > Local de Oferta > Eixo Temático > Curso
            ano = "2026"
            unidade_movel = curso.unidade.nome
            local = "Local de Oferta"  # Pode ser dinâmico
            eixo = curso.eixo_tecnologico or "Eixo Temático"
            root_categories["itinerante"]["children"].append({
                "name": ano,
                "children": [{
                    "name": unidade_movel,
                    "children": [{
                        "name": local,
                        "children": [{
                            "name": eixo,
                            "children": [{"name": curso.nome}]
                        }]
                    }]
                }]
            })

    # Aqui você pode converter root_categories para chamadas de criação de categorias no Moodle
    # Exemplo: percorrer a árvore e chamar create_moodle_categories para cada nível
    # TODO: Implementar integração real com Moodle
    return root_categories


def sync_and_create_moodle_structured_categories():
    """
    Monta e sincroniza a estrutura de categorias do Moodle conforme o tipo de curso,
    criando as categorias no Moodle.
    """
    from apps.cursos.models import Curso, ComponenteCurricular, EixoTecnologico
    from apps.unidades.models import Unidade

    def create_category_recursive(category, parent_id=None):
        payload = {
            "name": category["name"],
            "parent": parent_id or 0,
            "description": "",
            "descriptionformat": 1,
        }
        # Cria categoria no Moodle
        result = create_moodle_categories({"categories": [payload]})
        moodle_id = result[0]["id"] if isinstance(result, list) and result else None
        # Cria filhos
        children = category.get("children", [])
        for child in children:
            create_category_recursive(child, moodle_id)
        return moodle_id

    # Monta estrutura
    root_categories = sync_moodle_structured_categories()
    created_ids = {}
    for tipo, root in root_categories.items():
        created_ids[tipo] = create_category_recursive(root)
    return created_ids