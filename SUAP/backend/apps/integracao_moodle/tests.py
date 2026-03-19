from io import StringIO
from unittest.mock import Mock, patch

import requests
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.cursos.models import Curso
from apps.integracao_moodle.api.views import (
	MoodleAssignmentsIntegrationAPIView,
	MoodleCategoriesIntegrationAPIView,
	MoodleCoursesIntegrationAPIView,
	MoodleGradesIntegrationAPIView,
)
from apps.integracao_moodle.client import MoodleApiClient
from apps.integracao_moodle.exceptions import (
	MoodleAPIError,
	MoodleAuthenticationError,
	MoodleConfigurationError,
	MoodleConnectionError,
	MoodleUnsupportedFunctionError,
	MoodleUnexpectedResponseError,
)
from apps.integracao_moodle.models import MoodleCategory, MoodleCourse, MoodleGradeSnapshot, MoodleWritebackLog
from apps.integracao_moodle.schemas import MoodleApiSettings
from apps.integracao_moodle.services import (
	MoodleCatalogStorageSummary,
	MoodleCourseImportSummary,
	_build_new_course_data,
	_should_skip_course,
	delete_moodle_courses,
	save_moodle_assignment_grade,
	store_moodle_grade_tree,
	sync_moodle_catalog_data,
	update_moodle_grades,
)
from apps.unidades.models import Unidade


def gerar_cpf(seed: int) -> str:
	base = f"{seed:09d}"[-9:]

	def dv(parcial: str) -> str:
		peso_inicial = len(parcial) + 1
		total = sum(int(digito) * (peso_inicial - indice) for indice, digito in enumerate(parcial))
		resto = 11 - (total % 11)
		return "0" if resto >= 10 else str(resto)

	d1 = dv(base)
	d2 = dv(base + d1)
	return f"{base}{d1}{d2}"


class MoodleApiSettingsTests(SimpleTestCase):
	def test_is_configured_depends_on_base_url_and_token(self):
		self.assertFalse(MoodleApiSettings(base_url="", token="").is_configured)
		self.assertTrue(MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro").is_configured)


class MoodleApiClientTests(SimpleTestCase):
	@override_settings(
		MOODLE_BASE_URL="https://moodle.exemplo.local",
		MOODLE_WS_TOKEN="token-seguro",
		MOODLE_REST_FORMAT="json",
		MOODLE_TIMEOUT=45,
		MOODLE_VERIFY_SSL=True,
		MOODLE_REST_PATH="webservice/rest/server.php",
	)
	def test_client_is_built_from_django_settings(self):
		client = MoodleApiClient.from_django_settings()

		self.assertEqual(client.build_url(), "https://moodle.exemplo.local/webservice/rest/server.php")
		self.assertTrue(client.is_configured)
		self.assertEqual(client.config.timeout, 45)
		self.assertEqual(client.config.rest_format, "json")

	def test_build_params_requires_configuration(self):
		client = MoodleApiClient(config=MoodleApiSettings(base_url="", token=""))

		with self.assertRaises(MoodleConfigurationError):
			client.build_params("core_webservice_get_site_info")

	def test_build_params_includes_required_moodle_fields(self):
		client = MoodleApiClient(
			config=MoodleApiSettings(
				base_url="https://moodle.exemplo.local",
				token="token-seguro",
				rest_format="json",
			)
		)

		params = client.build_params("core_course_get_courses", moodlewssettingfilter=True)

		self.assertEqual(params["wstoken"], "token-seguro")
		self.assertEqual(params["wsfunction"], "core_course_get_courses")
		self.assertEqual(params["moodlewsrestformat"], "json")
		self.assertTrue(params["moodlewssettingfilter"])

	def test_build_params_rejects_wsfunction_outside_approved_scope(self):
		client = MoodleApiClient(
			config=MoodleApiSettings(
				base_url="https://moodle.exemplo.local",
				token="token-seguro",
				rest_format="json",
			)
		)

		with self.assertRaises(MoodleUnsupportedFunctionError):
			client.build_params("core_user_get_users")

	def test_call_uses_get_with_standard_query_params(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = [{"id": 1, "shortname": "CURSO", "fullname": "Curso Teste"}]
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		payload = client.call("core_course_get_courses", params={"classification": "visible"})

		self.assertEqual(payload[0]["id"], 1)
		session.get.assert_called_once_with(
			"https://moodle.exemplo.local/webservice/rest/server.php",
			params={
				"wstoken": "token-seguro",
				"wsfunction": "core_course_get_courses",
				"moodlewsrestformat": "json",
				"classification": "visible",
			},
			timeout=30,
			verify=True,
		)

	def test_call_uses_post_with_flattened_nested_payload(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = {"status": "ok"}
		session.post.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		payload = client.call(
			"mod_assign_save_grades",
			params={
				"assignmentid": 55,
				"grades": [
					{"userid": 10, "grade": 9.5},
					{"userid": 11, "grade": 8.0},
				],
			},
			method="post",
		)

		self.assertEqual(payload["status"], "ok")
		session.post.assert_called_once_with(
			"https://moodle.exemplo.local/webservice/rest/server.php",
			data={
				"wstoken": "token-seguro",
				"wsfunction": "mod_assign_save_grades",
				"moodlewsrestformat": "json",
				"assignmentid": 55,
				"grades[0][userid]": 10,
				"grades[0][grade]": 9.5,
				"grades[1][userid]": 11,
				"grades[1][grade]": 8.0,
			},
			timeout=30,
			verify=True,
		)

	def test_call_raises_connection_error_on_timeout(self):
		session = Mock(spec=requests.Session)
		session.get.side_effect = requests.Timeout()
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		with self.assertRaises(MoodleConnectionError):
			client.call("core_course_get_courses")

	def test_call_raises_api_error_on_http_failure(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 500
		response.ok = False
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		with self.assertRaises(MoodleAPIError):
			client.call("core_course_get_courses")

	def test_call_raises_unexpected_response_error_on_invalid_json(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.side_effect = ValueError("invalid json")
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		with self.assertRaises(MoodleUnexpectedResponseError):
			client.call("core_course_get_courses")

	def test_call_raises_api_error_when_moodle_returns_application_error(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = {
			"exception": "invalid_parameter_exception",
			"errorcode": "invalidparameter",
			"message": "Parametro invalido.",
		}
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		with self.assertRaises(MoodleAPIError):
			client.call("core_course_get_courses")

	def test_call_raises_authentication_error_when_moodle_rejects_token(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = {
			"exception": "required_capability_exception",
			"errorcode": "invalidtoken",
			"message": "Invalid token.",
		}
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		with self.assertRaises(MoodleAuthenticationError):
			client.call("core_course_get_courses")

	def test_get_courses_returns_normalized_payload(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = [
			{
				"id": 7,
				"shortname": "TEC-INFO",
				"fullname": "Tecnico em Informatica",
				"summary": "<p>Curso</p>",
				"visible": 1,
				"format": "topics",
				"courseformatoptions": [{"name": "numsections", "value": 10}],
			}
		]
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		courses = client.get_courses()

		self.assertEqual(courses, [
			{
				"id": 7,
				"shortname": "TEC-INFO",
				"categoryid": None,
				"fullname": "Tecnico em Informatica",
				"displayname": "Tecnico em Informatica",
				"idnumber": "",
				"summary": "<p>Curso</p>",
				"summaryformat": 0,
				"format": "topics",
				"visible": True,
				"startdate": None,
				"enddate": None,
				"timecreated": None,
				"timemodified": None,
				"enablecompletion": False,
				"showactivitydates": False,
				"showcompletionconditions": False,
				"courseformatoptions": [{"name": "numsections", "value": 10}],
			}
		])

	def test_get_categories_returns_normalized_payload(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = [
			{
				"id": 3,
				"name": "Formacao Inicial",
				"parent": 0,
				"visible": 1,
			}
		]
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		categories = client.get_categories()

		self.assertEqual(categories, [
			{
				"id": 3,
				"name": "Formacao Inicial",
				"idnumber": "",
				"description": "",
				"descriptionformat": 0,
				"parent": 0,
				"sortorder": 0,
				"coursecount": 0,
				"visible": True,
				"depth": 0,
				"path": "",
				"timemodified": None,
			}
		])

	def test_get_courses_by_field_returns_normalized_courses_from_courses_key(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = {
			"courses": [
				{
					"id": 9,
					"shortname": "CURSO-9",
					"fullname": "Curso 9",
					"visible": 1,
				}
			]
		}
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		courses = client.get_courses_by_field({"field": "id", "value": 9})

		self.assertEqual(courses[0]["id"], 9)
		self.assertEqual(courses[0]["fullname"], "Curso 9")

	def test_search_courses_returns_metadata_and_normalized_results(self):
		session = Mock(spec=requests.Session)
		response = Mock()
		response.status_code = 200
		response.ok = True
		response.json.return_value = {
			"total": 1,
			"courses": [
				{
					"id": 12,
					"shortname": "BUSCA-12",
					"fullname": "Curso Encontrado",
					"visible": 1,
				}
			],
			"warnings": [],
		}
		session.get.return_value = response
		client = MoodleApiClient(
			config=MoodleApiSettings(base_url="https://moodle.exemplo.local", token="token-seguro"),
			session=session,
		)

		result = client.search_courses({"criterianame": "search", "criteriavalue": "Curso"})

		self.assertEqual(result["total"], 1)
		self.assertEqual(result["results"][0]["id"], 12)


class MoodleIntegrationApiTests(SimpleTestCase):
	def setUp(self):
		self.factory = APIRequestFactory()
		self.courses_view = MoodleCoursesIntegrationAPIView.as_view()
		self.categories_view = MoodleCategoriesIntegrationAPIView.as_view()
		self.grades_view = MoodleGradesIntegrationAPIView.as_view()
		self.assignments_view = MoodleAssignmentsIntegrationAPIView.as_view()
		self.user = Mock()
		self.user.is_authenticated = True
		self.user.is_superuser = True

	@patch("apps.integracao_moodle.api.views.get_moodle_courses")
	def test_courses_endpoint_returns_courses_for_authorized_user(self, get_moodle_courses_mock):
		get_moodle_courses_mock.return_value = [{"id": 1, "shortname": "CURSO", "fullname": "Curso"}]
		request = self.factory.get("/api/v1/integracoes/moodle/cursos/")
		force_authenticate(request, user=self.user)

		response = self.courses_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(response.data["results"][0]["shortname"], "CURSO")

	@patch("apps.integracao_moodle.api.views.get_moodle_courses")
	def test_courses_endpoint_maps_configuration_error_to_503(self, get_moodle_courses_mock):
		get_moodle_courses_mock.side_effect = MoodleConfigurationError("Configuracao ausente")
		request = self.factory.get("/api/v1/integracoes/moodle/cursos/")
		force_authenticate(request, user=self.user)

		response = self.courses_view(request)

		self.assertEqual(response.status_code, 503)
		self.assertEqual(response.data["detail"], "Configuracao ausente")

	@patch("apps.integracao_moodle.api.views.import_moodle_courses_to_formacao_inicial")
	def test_courses_endpoint_imports_courses_into_internal_catalog(self, import_moodle_courses_mock):
		import_moodle_courses_mock.return_value = MoodleCourseImportSummary(
			unidade_codigo="sede",
			total_received=5,
			created=3,
			updated=1,
			linked_existing=1,
			skipped=0,
			catalog_storage=MoodleCatalogStorageSummary(categories_received=2, courses_received=5),
		)
		request = self.factory.post("/api/v1/integracoes/moodle/cursos/", {"unidade_codigo": "sede"}, format="json")
		force_authenticate(request, user=self.user)

		response = self.courses_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["summary"]["created"], 3)
		self.assertEqual(response.data["summary"]["linked_existing"], 1)
		self.assertEqual(response.data["catalog_storage"]["categories_received"], 2)

	@patch("apps.integracao_moodle.api.views.search_moodle_courses")
	def test_courses_endpoint_supports_search_action(self, search_moodle_courses_mock):
		search_moodle_courses_mock.return_value = {
			"total": 1,
			"warnings": [],
			"results": [{"id": 5, "shortname": "CUR-5", "fullname": "Curso 5"}],
		}
		request = self.factory.get(
			"/api/v1/integracoes/moodle/cursos/",
			{"action": "core_course_search_courses", "criterianame": "search", "criteriavalue": "Curso"},
		)
		force_authenticate(request, user=self.user)

		response = self.courses_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["action"], "core_course_search_courses")
		self.assertEqual(response.data["total"], 1)
		self.assertEqual(response.data["results"][0]["id"], 5)

	@patch("apps.integracao_moodle.api.views.create_moodle_courses")
	def test_courses_endpoint_supports_create_action(self, create_moodle_courses_mock):
		create_moodle_courses_mock.return_value = {
			"response_payload": [{"id": 71}],
			"log": Mock(id=18),
			"course_ids": [71],
			"catalog_storage": MoodleCatalogStorageSummary(categories_received=1, courses_received=1, courses_created=1),
			"import_summary": MoodleCourseImportSummary(unidade_codigo="sede", total_received=1, created=1),
			"synced_courses": [{"id": 71, "shortname": "CUR-71", "fullname": "Curso 71"}],
		}
		request = self.factory.post(
			"/api/v1/integracoes/moodle/cursos/",
			{
				"action": "core_course_create_courses",
				"params": {"courses": [{"fullname": "Curso 71", "shortname": "CUR-71", "categoryid": 3}]},
				"integrar_catalogo_interno": True,
			},
			format="json",
		)
		force_authenticate(request, user=self.user)

		response = self.courses_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["action"], "core_course_create_courses")
		self.assertEqual(response.data["log_id"], 18)
		self.assertEqual(response.data["course_ids"], [71])

	@patch("apps.integracao_moodle.api.views.get_moodle_categories")
	def test_categories_endpoint_returns_categories(self, get_moodle_categories_mock):
		get_moodle_categories_mock.return_value = [{"id": 1, "name": "Raiz"}]
		request = self.factory.get("/api/v1/integracoes/moodle/categorias/")
		force_authenticate(request, user=self.user)

		response = self.categories_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["count"], 1)
		self.assertEqual(response.data["results"][0]["name"], "Raiz")

	def test_grades_endpoint_stores_grade_tree_snapshot(self):
		grade_tree_handler = Mock(return_value=Mock(
			id=9,
			snapshot_type="grade_tree",
			wsfunction="core_grades_get_grade_tree",
			moodle_course_id=88,
			moodle_user_id=None,
		))
		request = self.factory.post(
			"/api/v1/integracoes/moodle/notas/",
			{"action": "grade_tree", "params": {"courseid": 88}},
			format="json",
		)
		force_authenticate(request, user=self.user)

		with patch.dict(MoodleGradesIntegrationAPIView.ACTION_MAP, {"grade_tree": grade_tree_handler}):
			response = self.grades_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["snapshot_id"], 9)
		self.assertEqual(response.data["wsfunction"], "core_grades_get_grade_tree")

	def test_assignments_endpoint_logs_save_grade(self):
		save_grade_handler = Mock(return_value=Mock(id=4, status="success", wsfunction="mod_assign_save_grade"))
		request = self.factory.post(
			"/api/v1/integracoes/moodle/assignments/",
			{"action": "save_grade", "params": {"assignmentid": 10, "userid": 20, "grade": 8.5}},
			format="json",
		)
		force_authenticate(request, user=self.user)

		with patch.dict(MoodleAssignmentsIntegrationAPIView.ACTION_MAP, {"save_grade": save_grade_handler}):
			response = self.assignments_view(request)

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data["log_id"], 4)
		self.assertEqual(response.data["wsfunction"], "mod_assign_save_grade")


class MoodleCourseImportServiceTests(SimpleTestCase):
	def test_should_skip_site_course(self):
		self.assertTrue(_should_skip_course({"format": "site", "fullname": "Portal"}))
		self.assertTrue(_should_skip_course({"format": "topics", "fullname": ""}))
		self.assertFalse(_should_skip_course({"format": "topics", "fullname": "Curso valido"}))

	def test_build_new_course_data_maps_moodle_payload_to_formacao_inicial(self):
		unidade = Mock(codigo="sede")
		course_data = _build_new_course_data(
			{
				"id": 44,
				"shortname": "CURSO-EXTERNO-MOODLE",
				"fullname": "Curso Externo Moodle",
			},
			unidade,
		)

		self.assertEqual(course_data["unidade"], unidade)
		self.assertEqual(course_data["moodle_course_id"], 44)
		self.assertEqual(course_data["moodle_shortname"], "CURSO-EXTERNO-MOODLE")
		self.assertEqual(course_data["sigla"], "CURSO-EXTERNO-MO")
		self.assertEqual(course_data["eixo_tecnologico"], "")
		self.assertEqual(course_data["carga_horaria"], 0)


class MoodlePersistenceServiceTests(TestCase):
	def setUp(self):
		self.unidade = Unidade.objects.get(codigo="sede")

	@patch("apps.integracao_moodle.services.get_moodle_courses")
	@patch("apps.integracao_moodle.services.get_moodle_categories")
	def test_sync_moodle_catalog_data_persists_categories_and_courses(self, get_moodle_categories_mock, get_moodle_courses_mock):
		linked_course = Curso.objects.create(
			unidade=self.unidade,
			area_curso=None,
			nome="Curso Integrado",
			sigla="CURSOINT",
			moodle_course_id=44,
			moodle_shortname="CUR-44",
			eixo_tecnologico="",
			carga_horaria=40,
		)
		get_moodle_categories_mock.return_value = [
			{"id": 7, "name": "Formacao Inicial", "parent": 0, "visible": 1},
		]
		get_moodle_courses_mock.return_value = [
			{
				"id": 44,
				"categoryid": 7,
				"shortname": "CUR-44",
				"fullname": "Curso Integrado",
				"displayname": "Curso Integrado",
				"idnumber": "",
				"summary": "",
				"summaryformat": 0,
				"format": "topics",
				"visible": True,
				"startdate": None,
				"enddate": None,
				"timecreated": None,
				"timemodified": None,
				"enablecompletion": False,
				"showactivitydates": False,
				"showcompletionconditions": False,
				"courseformatoptions": [],
			},
		]

		summary, courses = sync_moodle_catalog_data()

		self.assertEqual(summary.categories_created, 1)
		self.assertEqual(summary.courses_created, 1)
		self.assertEqual(summary.courses_linked_internal, 1)
		self.assertEqual(len(courses), 1)
		category = MoodleCategory.objects.get(moodle_category_id=7)
		course = MoodleCourse.objects.get(moodle_course_id=44)
		self.assertEqual(course.categoria, category)
		self.assertEqual(course.curso, linked_course)

	@patch("apps.integracao_moodle.services.get_moodle_api_client")
	def test_store_moodle_grade_tree_persists_snapshot(self, get_moodle_api_client_mock):
		MoodleCourse.objects.create(moodle_course_id=88, fullname="Curso 88")
		client = Mock()
		client.get_grade_tree.return_value = {"items": []}
		get_moodle_api_client_mock.return_value = client

		snapshot = store_moodle_grade_tree({"courseid": 88})

		self.assertIsInstance(snapshot, MoodleGradeSnapshot)
		self.assertEqual(snapshot.wsfunction, "core_grades_get_grade_tree")
		self.assertEqual(snapshot.moodle_course_id, 88)
		self.assertEqual(MoodleGradeSnapshot.objects.count(), 1)

	@patch("apps.integracao_moodle.services.get_moodle_api_client")
	def test_update_moodle_grades_persists_writeback_log(self, get_moodle_api_client_mock):
		client = Mock()
		client.update_grades.return_value = {"status": "ok"}
		get_moodle_api_client_mock.return_value = client

		log = update_moodle_grades({"courseid": 33, "grades": [{"userid": 9, "grade": 7.5}]})

		self.assertIsInstance(log, MoodleWritebackLog)
		self.assertEqual(log.wsfunction, "core_grades_update_grades")
		self.assertEqual(log.moodle_course_id, 33)

	@patch("apps.integracao_moodle.services.get_moodle_api_client")
	def test_save_assignment_grade_persists_writeback_log(self, get_moodle_api_client_mock):
		client = Mock()
		client.save_assignment_grade.return_value = []
		get_moodle_api_client_mock.return_value = client

		log = save_moodle_assignment_grade({"assignmentid": 9, "userid": 7, "grade": 6.0})

		self.assertEqual(log.wsfunction, "mod_assign_save_grade")
		self.assertEqual(log.moodle_assignment_id, 9)
		self.assertEqual(log.moodle_user_id, 7)

	@patch("apps.integracao_moodle.services.get_moodle_api_client")
	def test_delete_moodle_courses_unlinks_internal_course_and_removes_local_record(self, get_moodle_api_client_mock):
		linked_course = Curso.objects.create(
			unidade=self.unidade,
			area_curso=None,
			nome="Curso Moodle",
			sigla="CURMOODLE",
			moodle_course_id=44,
			moodle_shortname="CUR-44",
			eixo_tecnologico="",
			carga_horaria=40,
		)
		MoodleCourse.objects.create(moodle_course_id=44, shortname="CUR-44", fullname="Curso Moodle", curso=linked_course)
		client = Mock()
		client.delete_courses.return_value = []
		get_moodle_api_client_mock.return_value = client

		result = delete_moodle_courses({"courseids": [44]})

		linked_course.refresh_from_db()
		self.assertEqual(result["deletion_summary"].requested_ids, [44])
		self.assertEqual(result["deletion_summary"].removed_local_records, 1)
		self.assertEqual(result["deletion_summary"].unlinked_internal_courses, 1)
		self.assertIsNone(linked_course.moodle_course_id)
		self.assertEqual(linked_course.moodle_shortname, "")
		self.assertFalse(MoodleCourse.objects.filter(moodle_course_id=44).exists())


class MoodleIntegrationManagementCommandTests(SimpleTestCase):
	@patch("apps.integracao_moodle.management.commands.testar_integracao_moodle.get_moodle_courses")
	def test_management_command_lists_returned_courses(self, get_moodle_courses_mock):
		get_moodle_courses_mock.return_value = [
			{"id": 1, "shortname": "CURSO-1", "fullname": "Curso 1"},
			{"id": 2, "shortname": "CURSO-2", "fullname": "Curso 2"},
		]
		stdout = StringIO()

		call_command("testar_integracao_moodle", stdout=stdout)

		output = stdout.getvalue()
		self.assertIn("2 cursos retornados pelo Moodle.", output)
		self.assertIn("[1] CURSO-1 :: Curso 1", output)

	@patch("apps.integracao_moodle.management.commands.importar_cursos_moodle.import_moodle_courses_to_formacao_inicial")
	def test_import_command_reports_summary(self, import_moodle_courses_mock):
		import_moodle_courses_mock.return_value = MoodleCourseImportSummary(
			unidade_codigo="sede",
			total_received=8,
			created=5,
			updated=2,
			linked_existing=1,
			skipped=0,
			catalog_storage=MoodleCatalogStorageSummary(categories_received=2, courses_received=8),
		)
		stdout = StringIO()

		call_command("importar_cursos_moodle", stdout=stdout)

		output = stdout.getvalue()
		self.assertIn("Importacao de cursos do Moodle concluida.", output)
		self.assertIn("Cursos criados: 5", output)
		self.assertIn("Cursos vinculados a registros existentes: 1", output)

	@patch("apps.integracao_moodle.management.commands.sincronizar_categorias_moodle.sync_moodle_categories_data")
	def test_sync_categories_command_reports_summary(self, sync_categories_mock):
		sync_categories_mock.return_value = MoodleCatalogStorageSummary(
			categories_received=6,
			categories_created=4,
			categories_updated=2,
		)
		stdout = StringIO()

		call_command("sincronizar_categorias_moodle", stdout=stdout)

		output = stdout.getvalue()
		self.assertIn("Sincronizacao de categorias do Moodle concluida.", output)
		self.assertIn("Categorias recebidas do Moodle: 6", output)
		self.assertIn("Categorias criadas localmente: 4", output)

	@patch("apps.integracao_moodle.management.commands.sincronizar_catalogo_moodle.sync_moodle_catalog_data")
	def test_sync_catalog_command_reports_summary(self, sync_catalog_mock):
		sync_catalog_mock.return_value = (
			MoodleCatalogStorageSummary(
				categories_received=3,
				categories_created=1,
				categories_updated=2,
				courses_received=10,
				courses_created=7,
				courses_updated=3,
				courses_linked_internal=2,
			),
			[],
		)
		stdout = StringIO()

		call_command("sincronizar_catalogo_moodle", stdout=stdout)

		output = stdout.getvalue()
		self.assertIn("Sincronizacao do catalogo do Moodle concluida.", output)
		self.assertIn("Cursos recebidos do Moodle: 10", output)
		self.assertIn("Cursos vinculados ao catalogo interno: 2", output)
