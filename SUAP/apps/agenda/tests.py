from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.cursos.models import Curso
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import EventoAgenda


class AgendaCrudTests(TestCase):
    def setUp(self):
        self.unidade = Unidade.objects.create(nome="Campus Agenda", codigo="AGD")
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Logistica", carga_horaria=900)
        self.professor = Usuario.objects.create_user(
            username="prof_agenda",
            cpf="62345678901",
            tipo="PROFESSOR",
            password="x",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="LOG-1",
            ano_letivo=2026,
            professor_responsavel=self.professor,
        )

    def test_create_evento(self):
        response = self.client.post(
            reverse("agenda:agenda_create"),
            {
                "titulo": "Reuniao pedagogica",
                "descricao": "Alinhamento do bimestre.",
                "turma": self.turma.pk,
                "inicio": "2026-03-10 08:00",
                "fim": "2026-03-10 10:00",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(EventoAgenda.objects.filter(titulo="Reuniao pedagogica").exists())

    def test_list_agenda(self):
        EventoAgenda.objects.create(
            titulo="Simulado",
            descricao="Aplicacao de simulados.",
            turma=self.turma,
            inicio=timezone.make_aware(datetime(2026, 3, 12, 9, 0)),
            fim=timezone.make_aware(datetime(2026, 3, 12, 11, 0)),
        )

        response = self.client.get(reverse("agenda:agenda_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Simulado")

    def test_delete_evento(self):
        evento = EventoAgenda.objects.create(
            titulo="Plantao",
            descricao="Plantao para duvidas.",
            turma=self.turma,
            inicio=timezone.make_aware(datetime(2026, 3, 15, 14, 0)),
            fim=timezone.make_aware(datetime(2026, 3, 15, 16, 0)),
        )

        response = self.client.post(reverse("agenda:agenda_delete", args=[evento.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(EventoAgenda.objects.filter(pk=evento.pk).exists())
