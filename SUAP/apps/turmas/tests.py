from django.test import TestCase
from django.urls import reverse

from apps.cursos.models import Curso
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Turma


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
