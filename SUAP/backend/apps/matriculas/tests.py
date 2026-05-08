from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from apps.cursos.models import Curso
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import DependenciaAcademica, Matricula


class MatriculaCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000, tipo_curso="tecnico")
        self.secretaria = Usuario.objects.create_user(
            username="sec_matricula",
            cpf="92345678903",
            tipo="SECRETARIA",
            password="x",
        )
        self.professor = Usuario.objects.create_user(
            username="prof_matricula",
            cpf="32345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_matricula",
            cpf="32345678902",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="ADM-1",
            ano_letivo=2026,
            professor_responsavel=self.professor,
            status="ATIVA",
        )
        self.client.force_login(self.secretaria)

    def test_create_matricula(self):
        response = self.client.post(
            reverse("matriculas:matriculas_create"),
            {
                "aluno": self.aluno.pk,
                "curso": self.curso.pk,
                "turma": self.turma.pk,
                "tipo_matricula": "NOVA",
                "status": "ATIVA",
                "turno": "MANHA",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Matricula.objects.filter(aluno=self.aluno, turma=self.turma, curso=self.curso).exists())

    def test_list_matriculas(self):
        Matricula.objects.create(aluno=self.aluno, curso=self.curso, turma=self.turma, status="ATIVA", turno="MANHA")

        response = self.client.get(reverse("matriculas:matriculas_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "aluno_matricula")

    def test_delete_matricula(self):
        matricula = Matricula.objects.create(aluno=self.aluno, curso=self.curso, turma=self.turma, status="ATIVA", turno="MANHA")

        response = self.client.post(reverse("matriculas:matriculas_delete", args=[matricula.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Matricula.objects.filter(pk=matricula.pk).exists())

    def test_block_new_active_enrollment_when_student_has_active_in_other_course(self):
        outro_curso = Curso.objects.create(unidade=self.unidade, nome="Logistica", carga_horaria=900, tipo_curso="tecnico")
        outra_turma = Turma.objects.create(
            curso=outro_curso,
            nome="LOG-1",
            ano_letivo=2026,
            professor_responsavel=self.professor,
            status="ATIVA",
        )

        Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
            tipo_matricula="NOVA",
            turno="MANHA",
        )

        nova = Matricula(
            aluno=self.aluno,
            curso=outro_curso,
            turma=outra_turma,
            status="ATIVA",
            tipo_matricula="NOVA",
            turno="TARDE",
        )

        with self.assertRaises(ValidationError) as exc:
            nova.full_clean()

        self.assertIn("aluno", exc.exception.message_dict)

    def test_blocks_tecnico_enrollment_when_course_workload_invalid(self):
        curso_tecnico = Curso.objects.create(
            unidade=self.unidade,
            nome="Tecnico Sem Carga",
            carga_horaria=0,
            tipo_curso="tecnico",
        )
        turma_tecnica = Turma.objects.create(
            curso=curso_tecnico,
            nome="TEC-0",
            ano_letivo=2026,
            professor_responsavel=self.professor,
            status="ATIVA",
        )

        matricula = Matricula(
            aluno=self.aluno,
            curso=curso_tecnico,
            turma=turma_tecnica,
            status="TRANCADA",
            tipo_matricula="NOVA",
        )

        with self.assertRaises(ValidationError) as exc:
            matricula.full_clean()

        self.assertIn("curso", exc.exception.message_dict)

    def test_blocks_status_concluida_when_has_active_dependency(self):
        matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
            tipo_matricula="NOVA",
            turno="MANHA",
        )
        DependenciaAcademica.objects.create(
            matricula=matricula,
            componente="Matematica Basica",
            status="ATIVA",
            motivo="NOTA",
        )

        matricula.status = "CONCLUIDA"
        with self.assertRaises(ValidationError) as exc:
            matricula.full_clean()

        self.assertIn("status", exc.exception.message_dict)
