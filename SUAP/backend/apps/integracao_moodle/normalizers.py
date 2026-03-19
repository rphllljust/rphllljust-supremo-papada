from .exceptions import MoodleUnexpectedResponseError


def normalize_category_payload(category: dict) -> dict:
    if not isinstance(category, dict):
        raise MoodleUnexpectedResponseError("A API do Moodle retornou uma categoria em formato inesperado.")

    return {
        "id": category.get("id"),
        "name": category.get("name") or "",
        "idnumber": category.get("idnumber") or "",
        "description": category.get("description") or "",
        "descriptionformat": category.get("descriptionformat") or 0,
        "parent": category.get("parent") or 0,
        "sortorder": category.get("sortorder") or 0,
        "coursecount": category.get("coursecount") or 0,
        "visible": bool(category.get("visible", False)),
        "depth": category.get("depth") or 0,
        "path": category.get("path") or "",
        "timemodified": category.get("timemodified"),
    }


def normalize_course_payload(course: dict) -> dict:
    if not isinstance(course, dict):
        raise MoodleUnexpectedResponseError("A API do Moodle retornou um curso em formato inesperado.")

    return {
        "id": course.get("id"),
        "shortname": course.get("shortname") or "",
        "categoryid": course.get("categoryid"),
        "fullname": course.get("fullname") or "",
        "displayname": course.get("displayname") or course.get("fullname") or "",
        "idnumber": course.get("idnumber") or "",
        "summary": course.get("summary") or "",
        "summaryformat": course.get("summaryformat") or 0,
        "format": course.get("format") or "",
        "visible": bool(course.get("visible", False)),
        "startdate": course.get("startdate"),
        "enddate": course.get("enddate"),
        "timecreated": course.get("timecreated"),
        "timemodified": course.get("timemodified"),
        "enablecompletion": bool(course.get("enablecompletion", False)),
        "showactivitydates": bool(course.get("showactivitydates", False)),
        "showcompletionconditions": bool(course.get("showcompletionconditions", False)),
        "courseformatoptions": course.get("courseformatoptions") or [],
        # Additional fields commonly returned by core_course_search_courses
        "courseimage": course.get("courseimage") or course.get("courseimageurl"),
        "categoryname": course.get("categoryname") or course.get("categoryname"),
        "sortorder": course.get("sortorder"),
        "summaryfiles": course.get("summaryfiles") or [],
        "overviewfiles": course.get("overviewfiles") or [],
        "contacts": course.get("contacts") or [],
        "enrollmentmethods": course.get("enrollmentmethods") or [],
        "customfields": course.get("customfields") or [],
        "showshortname": bool(course.get("showshortname", False)),
    }


def normalize_courses_payload(payload) -> list[dict]:
    if not isinstance(payload, list):
        raise MoodleUnexpectedResponseError("A funcao core_course_get_courses deveria retornar uma lista de cursos.")

    return [normalize_course_payload(course) for course in payload]


def extract_courses_payload(payload, wsfunction: str) -> list[dict]:
    if isinstance(payload, list):
        return [normalize_course_payload(course) for course in payload]

    if isinstance(payload, dict) and isinstance(payload.get("courses"), list):
        return [normalize_course_payload(course) for course in payload["courses"]]

    raise MoodleUnexpectedResponseError(
        f"A funcao {wsfunction} deveria retornar uma lista de cursos ou um objeto com a chave 'courses'."
    )


def normalize_course_search_payload(payload) -> dict:
    if not isinstance(payload, dict):
        raise MoodleUnexpectedResponseError("A funcao core_course_search_courses deveria retornar um objeto.")

    results = extract_courses_payload(payload, "core_course_search_courses")
    total = payload.get("total")
    if total is None:
        total = payload.get("totalcount")
    if total is None:
        total = len(results)

    return {
        "total": total,
        "warnings": payload.get("warnings") or [],
        "courses": results,
    }


def normalize_categories_payload(payload) -> list[dict]:
    if not isinstance(payload, list):
        raise MoodleUnexpectedResponseError("A funcao core_course_get_categories deveria retornar uma lista de categorias.")

    return [normalize_category_payload(category) for category in payload]