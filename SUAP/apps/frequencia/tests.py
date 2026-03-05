from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Frequencia


class FrequenciaCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
        self.professor = Usuario.objects.create_user(
            username="prof_freq",
            cpf="52345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_freq",
            cpf="52345678902",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="ADM-2",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
        )

    def test_create_frequencia(self):
        response = self.client.post(
            reverse("frequencia:frequencia_create"),
            {
                "matricula": self.matricula.pk,
                "data": "2026-03-01",
                "presente": "on",
                "observacao": "Chegou no horario.",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Frequencia.objects.filter(matricula=self.matricula, data=date(2026, 3, 1)).exists())

    def test_list_frequencia(self):
        Frequencia.objects.create(matricula=self.matricula, data=date(2026, 3, 2), presente=True)

        response = self.client.get(reverse("frequencia:frequencia_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "02/03/2026")

    def test_delete_frequencia(self):
        registro = Frequencia.objects.create(
            matricula=self.matricula,
            data=date(2026, 3, 3),
            presente=False,
            observacao="Falta justificada.",
        )

        response = self.client.post(reverse("frequencia:frequencia_delete", args=[registro.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Frequencia.objects.filter(pk=registro.pk).exists())
