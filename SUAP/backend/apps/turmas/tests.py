from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cursos.models import Curso
from apps.frequencia.models import Frequencia
from apps.matriculas.models import Matricula
from apps.notas.models import Nota
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import DiarioAcademico, DiarioMaterialAula, DiarioOcorrencia, Turma


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


class TurmaCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Informatica", carga_horaria=1200)
        self.secretaria = Usuario.objects.create_user(
            username="sec_turma",
            cpf="92345678902",
            tipo="SECRETARIA",
            password="x",
        )
        self.professor = Usuario.objects.create_user(
            username="prof_turma",
            cpf="22345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_turma(self):
        response = self.client.post(
            reverse("turmas:turmas_create"),
            {
                "curso": self.curso.pk,
                "nome": "1A",
                "ano_letivo": 2026,
                "professor_responsavel": self.professor.pk,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Turma.objects.filter(nome="1A", ano_letivo=2026).exists())

    def test_list_turmas(self):
        Turma.objects.create(
            curso=self.curso,
            nome="2B",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )

        response = self.client.get(reverse("turmas:turmas_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2B")

    def test_delete_turma(self):
        turma = Turma.objects.create(
            curso=self.curso,
            nome="3C",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )

        response = self.client.post(reverse("turmas:turmas_delete", args=[turma.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Turma.objects.filter(pk=turma.pk).exists())


class TurmaApiListTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.professor = Usuario.objects.create_user(
            username="prof_turma_api",
            cpf=gerar_cpf(523456780),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Marta",
            last_name="Silva",
        )
        self.outro_professor = Usuario.objects.create_user(
            username="prof_turma_api_2",
            cpf=gerar_cpf(523456781),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Jonas",
            last_name="Souza",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_turma_api",
            cpf=gerar_cpf(523456782),
            tipo="ALUNO",
            password="x",
        )
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Informática", sigla="INFO", carga_horaria=1200)
        self.outro_curso = Curso.objects.create(unidade=self.unidade, nome="Logística", sigla="LOG", carga_horaria=900)
        self.turma = Turma.objects.create(curso=self.curso, nome="INFO-2026-A", ano_letivo=2026, status="ATIVA", professor_responsavel=self.professor)
        self.turma_sem_diario = Turma.objects.create(curso=self.outro_curso, nome="LOG-2026-B", ano_letivo=2026, status="PLANEJADA", professor_responsavel=self.professor)
        self.turma_outro_professor = Turma.objects.create(curso=self.curso, nome="INFO-2025-C", ano_letivo=2025, status="ENCERRADA", professor_responsavel=self.outro_professor)
        Matricula.objects.create(aluno=self.aluno, curso=self.curso, turma=self.turma, status="ATIVA")
        DiarioAcademico.objects.create(turma=self.turma, periodo="2026/1", componente_curricular="Projeto Integrador", aberto_por=self.professor)

        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.professor.cpf,
                "password": "senha123",
                "perfil": "PROFESSOR",
            },
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

    def test_list_returns_summary_filters_and_annotated_counts(self):
        response = self.api_client.get(
            reverse("api_v1_turmas:list"),
            {
                "aba": "TODOS",
                "ano_letivo": 2026,
                "professor": self.professor.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(response.data["summary"]["TODOS"], 2)
        self.assertEqual(response.data["summary"]["ATIVAS"], 1)
        self.assertEqual(response.data["summary"]["PLANEJADAS"], 1)
        self.assertEqual(response.data["summary"]["SEM_DIARIOS"], 1)

        turma_info = next(item for item in response.data["results"] if item["id"] == self.turma.id)
        self.assertEqual(turma_info["curso_sigla"], "INFO")
        self.assertEqual(turma_info["total_alunos"], 1)
        self.assertEqual(turma_info["total_diarios"], 1)

    def test_sem_diarios_tab_returns_only_classes_without_diary(self):
        response = self.api_client.get(reverse("api_v1_turmas:list"), {"aba": "SEM_DIARIOS"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.turma_sem_diario.id)


class DiarioApiTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.professor = Usuario.objects.create_user(
            username="prof_diario_api",
            cpf=gerar_cpf(823456780),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Helena",
            last_name="Diario",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_diario_api",
            cpf=gerar_cpf(823456781),
            tipo="ALUNO",
            password="x",
            first_name="Aline",
            last_name="Silva",
        )
        self.outro_aluno = Usuario.objects.create_user(
            username="aluno_diario_api_2",
            cpf=gerar_cpf(823456782),
            tipo="ALUNO",
            password="x",
            first_name="Bruno",
            last_name="Souza",
        )
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Informatica", carga_horaria=1200)
        self.turma = Turma.objects.create(curso=self.curso, nome="INFO-DIARIO", ano_letivo=2026, professor_responsavel=self.professor)
        self.diario = DiarioAcademico.objects.create(
            turma=self.turma,
            periodo="2026/1",
            componente_curricular="Projeto Integrador",
            observacoes="Acompanhamento regular da turma.",
            aberto_por=self.professor,
        )
        self.matricula = Matricula.objects.create(aluno=self.aluno, curso=self.curso, turma=self.turma, status="ATIVA")
        self.outra_matricula = Matricula.objects.create(aluno=self.outro_aluno, curso=self.curso, turma=self.turma, status="ATIVA")
        Nota.objects.create(matricula=self.matricula, descricao="Avaliação 1", valor="8.50", peso="1.00", data_lancamento="2026-03-10")
        Frequencia.objects.create(matricula=self.matricula, data="2026-03-11", presente=True)
        DiarioMaterialAula.objects.create(
            diario=self.diario,
            titulo="Plano de aula da semana 1",
            descricao="Conteúdo inicial e checklist da turma.",
            criado_por=self.professor,
        )
        DiarioOcorrencia.objects.create(
            diario=self.diario,
            tipo="OCORRENCIA",
            titulo="Reposição de conteúdo",
            descricao="Aula remanejada por feriado.",
            data_ocorrencia="2026-03-12",
            registrado_por=self.professor,
        )
        DiarioOcorrencia.objects.create(
            diario=self.diario,
            tipo="SUSPENSAO",
            titulo="Suspensão temporária",
            descricao="Registro disciplinar para análise.",
            data_ocorrencia="2026-03-13",
            registrado_por=self.professor,
        )

        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.professor.cpf,
                "password": "senha123",
                "perfil": "PROFESSOR",
            },
            format="json",
        )
        self.assertEqual(token_response.status_code, 200)
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

    def test_list_returns_summary_and_pending_counts(self):
        response = self.api_client.get(reverse("api_v1_diarios:list"), {"aba": "TODOS", "ano_letivo": 2026})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["summary"]["TODOS"], 1)
        self.assertEqual(response.data["results"][0]["notas_pendentes"], 1)
        self.assertEqual(response.data["results"][0]["frequencias_pendentes"], 1)
        self.assertEqual(response.data["results"][0]["professor_nome"], "Helena Diario")

    def test_detail_returns_students_materials_occurrences_and_stats(self):
        response = self.api_client.get(reverse("api_v1_diarios:detail", args=[self.diario.id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["estudantes"]), 2)
        self.assertEqual(len(response.data["materiais_aula"]), 1)
        self.assertEqual(len(response.data["ocorrencias"]), 1)
        self.assertEqual(len(response.data["suspensoes"]), 1)
        self.assertEqual(response.data["estatisticas"]["alunos_sem_notas"], 1)
        self.assertEqual(response.data["estatisticas"]["alunos_sem_frequencia"], 1)

    def test_close_and_reopen_diary(self):
        fechar = self.api_client.post(reverse("api_v1_diarios:fechar", args=[self.diario.id]))
        self.assertEqual(fechar.status_code, 200)
        self.diario.refresh_from_db()
        self.assertEqual(self.diario.status, "FECHADO")
        self.assertIsNotNone(self.diario.data_fechamento)

        reabrir = self.api_client.post(reverse("api_v1_diarios:reabrir", args=[self.diario.id]))
        self.assertEqual(reabrir.status_code, 200)
        self.diario.refresh_from_db()
        self.assertEqual(self.diario.status, "ABERTO")
        self.assertIsNone(self.diario.data_fechamento)

    def test_can_register_material_and_occurrence(self):
        material_response = self.api_client.post(
            reverse("api_v1_diarios:materiais", args=[self.diario.id]),
            {
                "titulo": "Lista de exercícios",
                "descricao": "Material complementar da unidade 2.",
                "data_referencia": "2026-03-20",
            },
            format="json",
        )
        self.assertEqual(material_response.status_code, 201)

        ocorrencia_response = self.api_client.post(
            reverse("api_v1_diarios:ocorrencias", args=[self.diario.id]),
            {
                "tipo": "OCORRENCIA",
                "titulo": "Aula de reforço",
                "descricao": "Aula extra para recuperação de conteúdo.",
                "data_ocorrencia": "2026-03-21",
            },
            format="json",
        )
        self.assertEqual(ocorrencia_response.status_code, 201)
        self.assertTrue(DiarioMaterialAula.objects.filter(diario=self.diario, titulo="Lista de exercícios").exists())
        self.assertTrue(DiarioOcorrencia.objects.filter(diario=self.diario, titulo="Aula de reforço").exists())

    def test_professor_scope_hides_other_turmas_and_diarios(self):
        outro_professor = Usuario.objects.create_user(
            username="prof_diario_api_2",
            cpf=gerar_cpf(823456783),
            tipo="PROFESSOR",
            password="senha123",
            first_name="Carlos",
            last_name="Outro",
        )
        outra_turma = Turma.objects.create(curso=self.curso, nome="INFO-OUTRA", ano_letivo=2026, professor_responsavel=outro_professor)
        DiarioAcademico.objects.create(turma=outra_turma, periodo="2026/1", componente_curricular="Banco de Dados", aberto_por=outro_professor)

        turmas_response = self.api_client.get(reverse("api_v1_turmas:list"))
        diarios_response = self.api_client.get(reverse("api_v1_diarios:list"))

        self.assertEqual(turmas_response.status_code, 200)
        self.assertEqual(diarios_response.status_code, 200)
        self.assertEqual(turmas_response.data["count"], 1)
        self.assertEqual(diarios_response.data["count"], 1)
        self.assertEqual(turmas_response.data["results"][0]["nome"], "INFO-DIARIO")
        self.assertEqual(diarios_response.data["results"][0]["turma_nome"], "INFO-DIARIO")
