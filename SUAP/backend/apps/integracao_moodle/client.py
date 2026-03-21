import logging
from urllib.parse import urljoin

import requests
from django.conf import settings

from .exceptions import (
    MoodleAPIError,
    MoodleAuthenticationError,
    MoodleConfigurationError,
    MoodleConnectionError,
    MoodleUnsupportedFunctionError,
    MoodleUnexpectedResponseError,
)
from .normalizers import extract_courses_payload, normalize_categories_payload, normalize_course_search_payload, normalize_courses_payload
from .schemas import MoodleApiSettings

logger = logging.getLogger(__name__)


SUPPORTED_MOODLE_WS_FUNCTIONS = (
    "core_course_create_categories",
    "core_course_update_categories",
    "core_course_delete_categories",
    "core_course_create_courses",
    "core_course_delete_courses",
    "core_course_duplicate_course",
    "core_course_get_contents",
    "core_course_get_categories",
    "core_course_get_courses",
    "core_course_get_courses_by_field",
    "core_course_import_course",
    "core_course_get_recent_courses",
    "core_course_search_courses",
    "core_course_update_courses",
    "core_course_view_course",
    "core_grades_get_grade_tree",
    "core_grades_get_gradeitems",
    "core_grades_update_grades",
    "gradereport_user_get_grade_items",
    "gradereport_user_get_grades_table",
    "mod_assign_save_grade",
    "mod_assign_save_grades",
    "core_update_inplace_editable",
    "core_webservice_get_site_info",
)


class MoodleApiClient:
    def __init__(self, config: MoodleApiSettings, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()

    @classmethod
    def from_django_settings(cls) -> "MoodleApiClient":
        return cls(
            config=MoodleApiSettings(
                base_url=settings.MOODLE_BASE_URL,
                token=settings.MOODLE_WS_TOKEN,
                rest_format=settings.MOODLE_REST_FORMAT,
                timeout=settings.MOODLE_TIMEOUT,
                rest_path=settings.MOODLE_REST_PATH,
                verify_ssl=settings.MOODLE_VERIFY_SSL,
            )
        )

    @property
    def is_configured(self) -> bool:
        return self.config.is_configured

    def build_url(self) -> str:
        return urljoin(self.config.base_url.rstrip("/") + "/", self.config.rest_path.lstrip("/"))

    def build_params(self, wsfunction: str, params: dict | None = None, **extra_params) -> dict:
        if not self.is_configured:
            raise MoodleConfigurationError(
                "A integracao com o Moodle nao esta configurada. Defina MOODLE_BASE_URL e MOODLE_WS_TOKEN."
            )

        self._validate_wsfunction(wsfunction)

        request_params = {
            "wstoken": self.config.token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": self.config.rest_format,
        }

        flattened_params = self._flatten_params(params or {})
        flattened_extra_params = self._flatten_params(extra_params or {})

        if flattened_params:
            request_params.update(flattened_params)
        if flattened_extra_params:
            request_params.update(flattened_extra_params)

        return request_params

    def call(self, wsfunction: str, params: dict | None = None, method: str = "get", **extra_params):
        request_params = self.build_params(wsfunction, params=params, **extra_params)
        url = self.build_url()

        logger.debug(
            "Calling Moodle REST API with wsfunction=%s url=%s params=%s",
            wsfunction,
            url,
            self._sanitize_params(request_params),
        )

        try:
            response = self._perform_request(method=method, url=url, request_params=request_params)
        except requests.Timeout as exc:
            logger.warning("Timeout while calling Moodle wsfunction=%s", wsfunction)
            raise MoodleConnectionError("Tempo limite excedido ao chamar a API do Moodle.") from exc
        except requests.ConnectionError as exc:
            logger.warning("Connection error while calling Moodle wsfunction=%s", wsfunction)
            raise MoodleConnectionError("Falha de conexao ao chamar a API do Moodle.") from exc
        except requests.RequestException as exc:
            logger.exception("Unexpected request error while calling Moodle wsfunction=%s", wsfunction)
            raise MoodleConnectionError("Falha de rede ao chamar a API do Moodle.") from exc

        if response.status_code in {401, 403}:
            logger.warning("Authentication failure from Moodle wsfunction=%s status=%s", wsfunction, response.status_code)
            raise MoodleAuthenticationError("Falha de autenticacao na API do Moodle.")

        if not response.ok:
            logger.error("Unexpected HTTP status from Moodle wsfunction=%s status=%s", wsfunction, response.status_code)
            raise MoodleAPIError(f"A API do Moodle retornou HTTP {response.status_code}.")

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("Invalid JSON response from Moodle wsfunction=%s", wsfunction)
            raise MoodleUnexpectedResponseError("A API do Moodle retornou uma resposta JSON invalida.") from exc

        self._raise_for_moodle_error(payload)

        logger.info("Moodle REST call completed successfully for wsfunction=%s", wsfunction)
        return payload

    def get_courses(self) -> list[dict]:
        payload = self.call("core_course_get_courses")
        return normalize_courses_payload(payload)

    def get_categories(self, criteria: dict | None = None) -> list[dict]:
        payload = self.call("core_course_get_categories", params=criteria or {})
        return normalize_categories_payload(payload)

    def create_categories(self, params: dict) -> dict | list:
        return self.call("core_course_create_categories", params=params, method="post")

    def update_categories(self, params: dict) -> dict | list:
        return self.call("core_course_update_categories", params=params, method="post")

    def delete_categories(self, params: dict) -> dict | list:
        return self.call("core_course_delete_categories", params=params, method="post")

    def get_courses_by_field(self, params: dict) -> list[dict]:
        payload = self.call("core_course_get_courses_by_field", params=params)
        return extract_courses_payload(payload, "core_course_get_courses_by_field")

    def get_recent_courses(self, params: dict) -> list[dict]:
        payload = self.call("core_course_get_recent_courses", params=params)
        return extract_courses_payload(payload, "core_course_get_recent_courses")

    def search_courses(self, params: dict) -> dict:
        payload = self.call("core_course_search_courses", params=params)
        return normalize_course_search_payload(payload)

    def create_courses(self, params: dict) -> dict | list:
        return self.call("core_course_create_courses", params=params, method="post")

    def update_courses(self, params: dict) -> dict | list:
        return self.call("core_course_update_courses", params=params, method="post")

    def delete_courses(self, params: dict) -> dict | list:
        return self.call("core_course_delete_courses", params=params, method="post")

    def duplicate_course(self, params: dict) -> dict | list:
        return self.call("core_course_duplicate_course", params=params, method="post")

    def import_course(self, params: dict) -> dict | list:
        return self.call("core_course_import_course", params=params, method="post")

    def get_course_contents(self, params: dict) -> dict | list:
        return self.call("core_course_get_contents", params=params)

    def update_inplace_editable(self, params: dict) -> dict | list:
        return self.call("core_update_inplace_editable", params=params, method="post")

    def view_course(self, params: dict) -> dict | list:
        return self.call("core_course_view_course", params=params, method="post")

    def get_grade_tree(self, params: dict) -> dict | list:
        return self.call("core_grades_get_grade_tree", params=params)

    def get_gradeitems(self, params: dict) -> dict | list:
        return self.call("core_grades_get_gradeitems", params=params)

    def get_user_grade_items(self, params: dict) -> dict | list:
        return self.call("gradereport_user_get_grade_items", params=params)

    def get_user_grades_table(self, params: dict) -> dict | list:
        return self.call("gradereport_user_get_grades_table", params=params)

    def update_grades(self, params: dict) -> dict | list:
        return self.call("core_grades_update_grades", params=params, method="post")

    def save_assignment_grade(self, params: dict) -> dict | list:
        return self.call("mod_assign_save_grade", params=params, method="post")

    def save_assignment_grades(self, params: dict) -> dict | list:
        return self.call("mod_assign_save_grades", params=params, method="post")

    def _validate_wsfunction(self, wsfunction: str):
        if wsfunction in SUPPORTED_MOODLE_WS_FUNCTIONS:
            return

        logger.warning("Blocked unsupported Moodle wsfunction=%s", wsfunction)
        raise MoodleUnsupportedFunctionError(
            "A funcao do Moodle solicitada nao esta aprovada para uso nesta fase da integracao."
        )

    def _perform_request(self, *, method: str, url: str, request_params: dict):
        normalized_method = (method or "get").strip().lower()

        if normalized_method == "get":
            return self.session.get(
                url,
                params=request_params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )

        if normalized_method == "post":
            return self.session.post(
                url,
                data=request_params,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )

        raise ValueError(f"Metodo HTTP nao suportado para a API do Moodle: {method}")

    def _flatten_params(self, params: dict) -> dict:
        flattened: dict[str, object] = {}

        def flatten_value(prefix: str, value):
            if isinstance(value, dict):
                for key, nested_value in value.items():
                    nested_prefix = f"{prefix}[{key}]" if prefix else str(key)
                    flatten_value(nested_prefix, nested_value)
                return

            if isinstance(value, list):
                for index, nested_value in enumerate(value):
                    nested_prefix = f"{prefix}[{index}]"
                    flatten_value(nested_prefix, nested_value)
                return

            flattened[prefix] = value

        for key, value in params.items():
            flatten_value(str(key), value)

        return flattened

    def _raise_for_moodle_error(self, payload):
        if not isinstance(payload, dict):
            return

        if not payload.get("exception") and not payload.get("errorcode"):
            return

        error_code = str(payload.get("errorcode") or "").strip().lower()
        exception_name = str(payload.get("exception") or "").strip().lower()
        message = (
            payload.get("message")
            or payload.get("debuginfo")
            or payload.get("errorcode")
            or "Erro retornado pela API do Moodle."
        )
        message_text = str(message)
        auth_indicators = {"invalidtoken", "accessexception", "requireloginerror"}
        text_to_check = f"{error_code} {exception_name} {message_text}".lower()

        if error_code in auth_indicators or "token" in text_to_check or "login" in text_to_check:
            logger.warning("Moodle authentication error detected: %s", exception_name or error_code or "unknown")
            raise MoodleAuthenticationError("Falha de autenticacao na API do Moodle.")

        logger.error("Moodle returned an application error: %s", message_text)
        raise MoodleAPIError(message_text)

    def _sanitize_params(self, params: dict) -> dict:
        sanitized = dict(params)
        if "wstoken" in sanitized:
            sanitized["wstoken"] = "***"
        return sanitized