from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Nota


class NotaCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Informatica", carga_horaria=1200)
        self.professor = Usuario.objects.create_user(
            username="prof_notas",
            cpf="42345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_notas",
            cpf="42345678902",
            tipo="ALUNO",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="INFO-1",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
        )

    def test_create_nota(self):
        response = self.client.post(
            reverse("notas:notas_create"),
            {
                "matricula": self.matricula.pk,
                "descricao": "Prova 1",
                "valor": "8.50",
                "peso": "1.00",
                "data_lancamento": "2026-03-01",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Nota.objects.filter(matricula=self.matricula, descricao="Prova 1").exists())

    def test_list_notas(self):
        Nota.objects.create(
            matricula=self.matricula,
            descricao="Trabalho",
            valor=Decimal("9.00"),
            peso=Decimal("1.00"),
            data_lancamento=date(2026, 3, 2),
        )

        response = self.client.get(reverse("notas:notas_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Trabalho")

    def test_delete_nota(self):
        nota = Nota.objects.create(
            matricula=self.matricula,
            descricao="Seminario",
            valor=Decimal("7.50"),
            peso=Decimal("1.00"),
            data_lancamento=date(2026, 3, 3),
        )

        response = self.client.post(reverse("notas:notas_delete", args=[nota.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Nota.objects.filter(pk=nota.pk).exists())
