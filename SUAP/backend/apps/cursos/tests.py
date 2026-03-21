from django.test import TestCase
from django.urls import reverse

from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import ComponenteCurricular, Curso, MatrizCurricular
from .services import create_initial_matrix_for_course, rollback_initial_matrices


class CursoCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.secretaria = Usuario.objects.create_user(
            username="sec_cursos",
            cpf="92345678901",
            tipo="SECRETARIA",
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_curso(self):
        response = self.client.post(
            reverse("cursos:cursos_create"),
            {
                "unidade": self.unidade.pk,
                "nome": "Informatica",
                "carga_horaria": 1200,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Curso.objects.filter(nome="Informatica").exists())

    def test_list_cursos(self):
        Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)

        response = self.client.get(reverse("cursos:cursos_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administracao")

    def test_delete_curso(self):
        curso = Curso.objects.create(unidade=self.unidade, nome="Quimica", carga_horaria=1400)

        response = self.client.post(reverse("cursos:cursos_delete", args=[curso.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Curso.objects.filter(pk=curso.pk).exists())


class MatrizCurricularTransitionTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo='sede', defaults={'nome': 'Sede'})
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome='Técnico em Administração',
            sigla='ADMTEC',
            tipo_curso='tecnico',
            carga_horaria=1200,
        )
        self.componente_1 = ComponenteCurricular.objects.create(
            curso=self.curso,
            nome='Fundamentos da Administração',
            sigla='FADM',
            carga_horaria=60,
            hora_aula=80,
            qtd_creditos=4,
        )
        self.componente_2 = ComponenteCurricular.objects.create(
            curso=self.curso,
            nome='Empreendedorismo',
            sigla='EMPRE',
            carga_horaria=40,
            hora_aula=60,
            qtd_creditos=2,
        )

    def test_create_initial_matrix_for_course_links_existing_components_and_course(self):
        matriz, created, componentes_ligados = create_initial_matrix_for_course(self.curso, ano_referencia=2026)

        self.assertTrue(created)
        self.assertEqual(componentes_ligados, 2)
        self.assertEqual(matriz.curso_base, self.curso)

        self.componente_1.refresh_from_db()
        self.componente_2.refresh_from_db()
        self.curso.refresh_from_db()

        self.assertEqual(self.componente_1.matriz_curricular, matriz)
        self.assertEqual(self.componente_2.matriz_curricular, matriz)
        self.assertEqual(self.curso.matriz_curricular, matriz)

    def test_rollback_initial_matrices_unlinks_components_and_course(self):
        matriz, _, _ = create_initial_matrix_for_course(self.curso, ano_referencia=2026)

        result = rollback_initial_matrices(ano_referencia=2026, course_ids=[self.curso.id])

        self.assertGreaterEqual(result['matrizes_removidas'], 1)
        self.assertEqual(result['componentes_desvinculados'], 2)
        self.assertEqual(result['cursos_limpos'], 1)
        self.assertFalse(MatrizCurricular.objects.filter(pk=matriz.pk).exists())

        self.componente_1.refresh_from_db()
        self.componente_2.refresh_from_db()
        self.curso.refresh_from_db()

        self.assertIsNone(self.componente_1.matriz_curricular)
        self.assertIsNone(self.componente_2.matriz_curricular)
        self.assertIsNone(self.curso.matriz_curricular)
