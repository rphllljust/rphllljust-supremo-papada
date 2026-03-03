from django.test import TestCase
from django.urls import reverse

from apps.cursos.models import Curso
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Matricula


class MatriculaCrudTests(TestCase):
    def setUp(self):
        self.unidade = Unidade.objects.create(nome="Campus Zona Sul", codigo="ZSU")
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
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
        )

    def test_create_matricula(self):
        response = self.client.post(
            reverse("matriculas:matriculas_create"),
            {
                "aluno": self.aluno.pk,
                "turma": self.turma.pk,
                "status": "ATIVA",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Matricula.objects.filter(aluno=self.aluno, turma=self.turma).exists())

    def test_list_matriculas(self):
        Matricula.objects.create(aluno=self.aluno, turma=self.turma, status="ATIVA")

        response = self.client.get(reverse("matriculas:matriculas_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "aluno_matricula")

    def test_delete_matricula(self):
        matricula = Matricula.objects.create(aluno=self.aluno, turma=self.turma, status="ATIVA")

        response = self.client.post(reverse("matriculas:matriculas_delete", args=[matricula.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Matricula.objects.filter(pk=matricula.pk).exists())
