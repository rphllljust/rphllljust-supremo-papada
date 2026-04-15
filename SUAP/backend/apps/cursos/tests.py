from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import CalendarioLetivo, ComponenteCurricular, Curso, MatrizCurricular, NivelEnsino, OfertaCurso, TipoComponente
from .services import clone_matriz_curricular, close_matriz_curricular, create_initial_matrix_for_course, create_oferta_curso, publish_matriz_curricular, rollback_initial_matrices, set_matriz_as_current, sync_oferta_curso_to_moodle


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


class ComponenteCatalogoCompatibilityTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo='sede', defaults={'nome': 'Sede'})
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome='Técnico em Logística',
            sigla='LOGTEC',
            tipo_curso='tecnico',
            carga_horaria=1000,
        )

    def test_legacy_text_fields_create_catalog_links(self):
        componente = ComponenteCurricular.objects.create(
            curso=self.curso,
            nome='Fundamentos de Logística',
            sigla='FLOG',
            tipo_componente='Disciplina',
            nivel_ensino='Técnico',
            carga_horaria=60,
            hora_aula=80,
            qtd_creditos=4,
        )

        self.assertEqual(componente.tipo_componente_catalogo.descricao, 'Disciplina')
        self.assertEqual(componente.nivel_ensino_catalogo.descricao, 'Técnico')
        self.assertTrue(TipoComponente.objects.filter(descricao='Disciplina').exists())
        self.assertTrue(NivelEnsino.objects.filter(descricao='Técnico').exists())

    def test_catalog_links_refresh_legacy_text_fields(self):
        tipo = TipoComponente.objects.create(descricao='Projeto Integrador')
        nivel = NivelEnsino.objects.create(descricao='Educação Profissional Técnica')

        componente = ComponenteCurricular.objects.create(
            curso=self.curso,
            nome='Projeto Aplicado',
            sigla='PAPL',
            tipo_componente_catalogo=tipo,
            nivel_ensino_catalogo=nivel,
            carga_horaria=40,
            hora_aula=60,
            qtd_creditos=2,
        )

        self.assertEqual(componente.tipo_componente, 'Projeto Integrador')
        self.assertEqual(componente.nivel_ensino, 'Educação Profissional Técnica')


class MatrizCurricularGovernanceTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo='sede', defaults={'nome': 'Sede'})
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome='Técnico em Redes',
            sigla='REDTEC',
            tipo_curso='tecnico',
            carga_horaria=1200,
        )
        self.matriz = MatrizCurricular.objects.create(
            curso_base=self.curso,
            nome='Matriz Redes 2026',
            ano_referencia=2026,
            versao='1.0',
            status='RASCUNHO',
            ativa=True,
        )
        ComponenteCurricular.objects.create(
            curso=self.curso,
            matriz_curricular=self.matriz,
            nome='Infraestrutura de Redes',
            sigla='INFR',
            carga_horaria=80,
            hora_aula=100,
            qtd_creditos=4,
            modulo_numero=1,
            modulo_nome='Base técnica',
            ordem_no_modulo=1,
        )

    def test_clone_matriz_curricular_creates_new_version_with_components(self):
        clone = clone_matriz_curricular(self.matriz)

        self.assertNotEqual(clone.id, self.matriz.id)
        self.assertEqual(clone.status, 'RASCUNHO')
        self.assertEqual(clone.componentes.count(), 1)
        self.assertNotEqual(clone.versao, self.matriz.versao)

    def test_publish_matriz_curricular_sets_course_reference(self):
        publish_matriz_curricular(self.matriz)
        self.matriz.refresh_from_db()
        self.curso.refresh_from_db()

        self.assertEqual(self.matriz.status, 'VIGENTE')
        self.assertEqual(self.curso.matriz_curricular, self.matriz)

    def test_publish_matriz_curricular_with_existing_vigente_returns_current(self):
        vigente = clone_matriz_curricular(self.matriz, versao='1.1')
        publish_matriz_curricular(vigente)

        resultado = publish_matriz_curricular(self.matriz)

        self.matriz.refresh_from_db()
        vigente.refresh_from_db()
        self.curso.refresh_from_db()

        self.assertEqual(resultado.id, vigente.id)
        self.assertEqual(vigente.status, 'VIGENTE')
        self.assertEqual(self.matriz.status, 'RASCUNHO')
        self.assertEqual(self.curso.matriz_curricular, vigente)

    def test_set_matriz_as_current_closes_previous_vigente(self):
        publish_matriz_curricular(self.matriz)
        clone = clone_matriz_curricular(self.matriz, versao='1.1')

        set_matriz_as_current(clone)

        self.matriz.refresh_from_db()
        clone.refresh_from_db()
        self.curso.refresh_from_db()

        self.assertEqual(self.matriz.status, 'ENCERRADA')
        self.assertEqual(clone.status, 'VIGENTE')
        self.assertEqual(self.curso.matriz_curricular, clone)

    def test_close_matriz_curricular_removes_course_reference_when_no_other_vigente_exists(self):
        publish_matriz_curricular(self.matriz)

        close_matriz_curricular(self.matriz)

        self.matriz.refresh_from_db()
        self.curso.refresh_from_db()
        self.assertEqual(self.matriz.status, 'ENCERRADA')
        self.assertIsNone(self.curso.matriz_curricular)


class OfertaCursoServiceTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo='sede', defaults={'nome': 'Sede'})
        self.polo, _ = Unidade.objects.get_or_create(codigo='rio_branco', defaults={'nome': 'Rio Branco'})
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome='Técnico em Informática',
            sigla='INFTEC',
            tipo_curso='tecnico',
            carga_horaria=1200,
        )
        self.matriz = MatrizCurricular.objects.create(
            curso_base=self.curso,
            nome='Matriz Informática 2026',
            ano_referencia=2026,
            versao='1.0',
            status='VIGENTE',
            ativa=True,
        )
        self.curso.matriz_curricular = self.matriz
        self.curso.save(update_fields=['matriz_curricular'])
        ComponenteCurricular.objects.create(
            curso=self.curso,
            matriz_curricular=self.matriz,
            nome='Lógica de Programação',
            sigla='LOGP',
            carga_horaria=80,
            hora_aula=100,
            qtd_creditos=4,
            modulo_numero=1,
            modulo_nome='Fundamentos',
            ordem_no_modulo=1,
        )
        ComponenteCurricular.objects.create(
            curso=self.curso,
            matriz_curricular=self.matriz,
            nome='Banco de Dados',
            sigla='BDAD',
            carga_horaria=80,
            hora_aula=100,
            qtd_creditos=4,
            modulo_numero=2,
            modulo_nome='Dados',
            ordem_no_modulo=1,
        )
        self.calendario = CalendarioLetivo.objects.create(
            ano_letivo='2026',
            curso=self.curso,
            data_inicio='2026-02-01',
            data_fim='2026-12-20',
            status='VIGENTE',
        )

    def test_create_oferta_curso_uses_course_current_matrix_by_default(self):
        oferta = create_oferta_curso(
            curso_base=self.curso,
            calendario_letivo=self.calendario,
            polo=self.polo,
            codigo_turma='A',
            periodo_letivo='1',
            turno='NOITE',
            vagas_totais=30,
        )

        self.assertEqual(oferta.matriz_curricular, self.matriz)
        self.assertEqual(oferta.ano_oferta, 2026)
        self.assertEqual(oferta.vagas_disponiveis, 30)
        self.assertTrue(oferta.logs.filter(evento='criacao_oferta').exists())

    @patch('apps.cursos.services.update_moodle_inplace_editable')
    @patch('apps.cursos.services.get_moodle_course_contents')
    @patch('apps.cursos.services.duplicate_moodle_course')
    @patch('apps.cursos.services.create_moodle_categories')
    @patch('apps.cursos.services.get_moodle_categories')
    def test_sync_oferta_curso_to_moodle_creates_course_and_updates_sync_fields(self, mock_get_categories, mock_create_categories, mock_duplicate_course, mock_get_contents, mock_update_inplace):
        self.matriz.moodle_template_course_id = 555
        self.matriz.moodle_template_shortname = 'TPL-INF-2026'
        self.matriz.save(update_fields=['moodle_template_course_id', 'moodle_template_shortname'])
        oferta = create_oferta_curso(
            curso_base=self.curso,
            calendario_letivo=self.calendario,
            polo=self.polo,
            codigo_turma='B',
            periodo_letivo='2',
            turno='MANHA',
            vagas_totais=25,
        )
        mock_get_categories.side_effect = [
            [],
            [{'id': 900, 'name': 'OFERTAS SUAP', 'idnumber': 'suap-ofertas-tecnico', 'parent': 387}],
            [
                {'id': 900, 'name': 'OFERTAS SUAP', 'idnumber': 'suap-ofertas-tecnico', 'parent': 387},
                {'id': 901, 'name': 'Rio Branco', 'idnumber': 'suap-ofertas-polo-rio_branco', 'parent': 900},
            ],
        ]
        mock_create_categories.side_effect = [
            [{'id': 900}],
            [{'id': 901}],
            [{'id': 902}],
        ]
        mock_duplicate_course.return_value = {'course_ids': [777], 'response_payload': {'id': 777}}
        mock_get_contents.return_value = [
            {'id': 1001, 'section': 1, 'name': 'Topic 1', 'modules': []},
            {'id': 1002, 'section': 2, 'name': 'Topic 2', 'modules': []},
        ]

        result = sync_oferta_curso_to_moodle(oferta)

        oferta.refresh_from_db()
        self.assertEqual(result['oferta'].id, oferta.id)
        self.assertEqual(oferta.moodle_course_id, 777)
        self.assertEqual(oferta.moodle_category_id, 902)
        self.assertEqual(oferta.last_sync_status, 'success')
        self.assertEqual(oferta.moodle_sync_mode, 'duplicate_template')
        self.assertTrue(oferta.moodle_template_applied)
        self.assertEqual(oferta.moodle_template_source_course_id, 555)
        self.assertTrue(oferta.logs.filter(evento='sincronizacao_moodle').exists())
        self.assertTrue(oferta.logs.filter(evento='importacao_conteudo').exists())
        self.assertEqual(mock_update_inplace.call_count, 2)

    @patch('apps.cursos.services.update_moodle_inplace_editable')
    @patch('apps.cursos.services.get_moodle_course_contents')
    @patch('apps.cursos.services.import_moodle_course')
    @patch('apps.cursos.services.update_moodle_courses')
    @patch('apps.cursos.services.create_moodle_categories')
    @patch('apps.cursos.services.get_moodle_categories')
    def test_sync_oferta_curso_to_moodle_imports_template_into_existing_empty_course(self, mock_get_categories, mock_create_categories, mock_update_moodle_courses, mock_import_moodle_course, mock_get_contents, mock_update_inplace):
        self.matriz.moodle_template_course_id = 555
        self.matriz.moodle_template_shortname = 'TPL-INF-2026'
        self.matriz.save(update_fields=['moodle_template_course_id', 'moodle_template_shortname'])
        oferta = create_oferta_curso(
            curso_base=self.curso,
            calendario_letivo=self.calendario,
            polo=self.polo,
            codigo_turma='C',
            periodo_letivo='2',
            turno='NOITE',
            vagas_totais=20,
        )
        oferta.moodle_course_id = 888
        oferta.moodle_shortname = 'OF-EXISTENTE'
        oferta.save(update_fields=['moodle_course_id', 'moodle_shortname'])

        mock_get_categories.side_effect = [
            [],
            [{'id': 900, 'name': 'OFERTAS SUAP', 'idnumber': 'suap-ofertas-tecnico', 'parent': 387}],
            [
                {'id': 900, 'name': 'OFERTAS SUAP', 'idnumber': 'suap-ofertas-tecnico', 'parent': 387},
                {'id': 901, 'name': 'Rio Branco', 'idnumber': 'suap-ofertas-polo-rio_branco', 'parent': 900},
            ],
        ]
        mock_create_categories.side_effect = [
            [{'id': 900}],
            [{'id': 901}],
            [{'id': 902}],
        ]
        mock_update_moodle_courses.return_value = {'response_payload': {'warnings': []}, 'course_ids': [888]}
        mock_import_moodle_course.return_value = {'response_payload': None}
        mock_get_contents.side_effect = [
            [
                {'id': 2001, 'section': 1, 'name': 'Topic 1', 'modules': []},
                {'id': 2002, 'section': 2, 'name': 'Topic 2', 'modules': []},
            ],
            [
                {'id': 2001, 'section': 1, 'name': 'Fundamentos', 'modules': []},
                {'id': 2002, 'section': 2, 'name': 'Dados', 'modules': []},
            ],
        ]

        sync_oferta_curso_to_moodle(oferta)

        oferta.refresh_from_db()
        self.assertEqual(oferta.moodle_sync_mode, 'import_template')
        self.assertTrue(oferta.moodle_template_applied)
        self.assertEqual(oferta.moodle_template_source_course_id, 555)
        self.assertEqual(oferta.moodle_template_source_shortname, 'TPL-INF-2026')
        self.assertEqual(oferta.moodle_sync_fallback_reason, '')
        self.assertTrue(oferta.logs.filter(evento='sincronizacao_template').exists())
        mock_import_moodle_course.assert_called_once()

    @patch('apps.cursos.services.update_moodle_inplace_editable')
    @patch('apps.cursos.services.get_moodle_course_contents')
    @patch('apps.cursos.services.create_moodle_courses')
    @patch('apps.cursos.services.create_moodle_categories')
    @patch('apps.cursos.services.get_moodle_categories')
    def test_sync_oferta_curso_to_moodle_uses_fallback_without_template(self, mock_get_categories, mock_create_categories, mock_create_moodle_courses, mock_get_contents, mock_update_inplace):
        oferta = create_oferta_curso(
            curso_base=self.curso,
            calendario_letivo=self.calendario,
            polo=self.polo,
            codigo_turma='D',
            periodo_letivo='1',
            turno='MANHA',
            vagas_totais=20,
        )

        mock_get_categories.side_effect = [
            [],
            [{'id': 900, 'name': 'OFERTAS SUAP', 'idnumber': 'suap-ofertas-tecnico', 'parent': 387}],
            [
                {'id': 900, 'name': 'OFERTAS SUAP', 'idnumber': 'suap-ofertas-tecnico', 'parent': 387},
                {'id': 901, 'name': 'Rio Branco', 'idnumber': 'suap-ofertas-polo-rio_branco', 'parent': 900},
            ],
        ]
        mock_create_categories.side_effect = [
            [{'id': 900}],
            [{'id': 901}],
            [{'id': 902}],
        ]
        mock_create_moodle_courses.return_value = {'course_ids': [999], 'response_payload': {'id': 999}}
        mock_get_contents.return_value = [
            {'id': 3001, 'section': 1, 'name': 'Topic 1', 'modules': []},
            {'id': 3002, 'section': 2, 'name': 'Topic 2', 'modules': []},
        ]

        sync_oferta_curso_to_moodle(oferta)

        oferta.refresh_from_db()
        self.assertEqual(oferta.moodle_sync_mode, 'create_fallback')
        self.assertFalse(oferta.moodle_template_applied)
        self.assertIn('sem curso modelo Moodle', oferta.moodle_sync_fallback_reason)
