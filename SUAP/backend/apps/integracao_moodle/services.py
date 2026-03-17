import logging
from dataclasses import dataclass

from django.db import transaction

from apps.cursos.models import Curso
from apps.unidades.models import Unidade

from .client import MoodleApiClient
from .models import MoodleCategory, MoodleCourse, MoodleGradeSnapshot, MoodleWritebackLog

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


def get_moodle_api_client() -> MoodleApiClient:
    return MoodleApiClient.from_django_settings()


def get_moodle_courses() -> list[dict]:
    return get_moodle_api_client().get_courses()


def get_moodle_categories(criteria: dict | None = None) -> list[dict]:
    return get_moodle_api_client().get_categories(criteria=criteria)


def import_moodle_courses_to_formacao_inicial(unidade_codigo: str = "sede") -> MoodleCourseImportSummary:
    normalized_unidade_codigo = (unidade_codigo or "sede").strip().lower()

    try:
        unidade = Unidade.objects.get(codigo=normalized_unidade_codigo)
    except Unidade.DoesNotExist as exc:
        raise ValueError(f"Unidade '{normalized_unidade_codigo}' nao encontrada.") from exc

    storage_summary, courses = sync_moodle_catalog_data()
    summary = MoodleCourseImportSummary(
        unidade_codigo=unidade.codigo,
        total_received=len(courses),
        catalog_storage=storage_summary,
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
                ).first()
                linked_existing = target_course is not None

            if target_course is None:
                target_course = Curso.objects.create(**_build_new_course_data(course_payload, unidade))
                summary.created += 1
            else:
                _update_existing_course_from_moodle(target_course, course_payload, unidade=unidade, linked_existing=linked_existing)

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


def sync_moodle_catalog_data(category_criteria: dict | None = None) -> tuple[MoodleCatalogStorageSummary, list[dict]]:
    categories = get_moodle_categories(criteria=category_criteria)
    courses = get_moodle_courses()
    summary = MoodleCatalogStorageSummary(
        categories_received=len(categories),
        courses_received=len(courses),
    )

    with transaction.atomic():
        category_map = _store_moodle_categories(categories, summary)
        _store_moodle_courses(courses, category_map, summary)

    return summary, courses


def sync_moodle_categories_data(category_criteria: dict | None = None) -> MoodleCatalogStorageSummary:
    categories = get_moodle_categories(criteria=category_criteria)
    summary = MoodleCatalogStorageSummary(categories_received=len(categories))

    with transaction.atomic():
        _store_moodle_categories(categories, summary)

    return summary


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


def _resolve_sigla(course_payload: dict) -> str:
    raw_sigla = (course_payload.get("shortname") or course_payload.get("displayname") or course_payload.get("fullname") or "").strip()
    return raw_sigla[:16]


def _build_new_course_data(course_payload: dict, unidade: Unidade) -> dict:
    return {
        "unidade": unidade,
        "area_curso": None,
        "nome": (course_payload.get("fullname") or "").strip(),
        "sigla": _resolve_sigla(course_payload),
        "moodle_course_id": course_payload["id"],
        "moodle_shortname": (course_payload.get("shortname") or "").strip(),
        "eixo_tecnologico": "",
        "carga_horaria": 0,
    }


def _update_existing_course_from_moodle(target_course: Curso, course_payload: dict, *, unidade: Unidade, linked_existing: bool):
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

        category = category_map.get(category_payload["id"])
        parent = category_map.get(parent_id)
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


def _store_writeback_log(*, wsfunction: str, request_payload: dict, response_payload, status: str = "success", error_message: str = ""):
    return MoodleWritebackLog.objects.create(
        wsfunction=wsfunction,
        status=status,
        moodle_course_id=_extract_int(request_payload, "courseid"),
        moodle_assignment_id=_extract_int(request_payload, "assignmentid"),
        moodle_user_id=_extract_int(request_payload, "userid"),
        request_payload=request_payload,
        response_payload=response_payload,
        error_message=error_message,
    )


def _extract_int(payload: dict, key: str) -> int | None:
    value = payload.get(key)
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None