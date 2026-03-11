from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.cursos.models import Curso
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import PerfilUsuario, Usuario

from .models import EventoAgenda


class AgendaCrudTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
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

    def _authenticate_api_client(self, user, password="x"):
        self.api_client.force_authenticate(user=user)

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

    def test_api_list_eventos_returns_paginated_results_for_professor(self):
        EventoAgenda.objects.create(
            titulo="Aula inaugural",
            descricao="Boas-vindas da turma.",
            turma=self.turma,
            inicio=timezone.make_aware(datetime(2026, 3, 10, 19, 0)),
            fim=timezone.make_aware(datetime(2026, 3, 10, 21, 0)),
        )

        self.api_client.credentials()
        anonymous_response = self.api_client.get("/api/v1/eventos/?search=&page=1")
        self.assertEqual(anonymous_response.status_code, 401)

        self._authenticate_api_client(self.professor)
        response = self.api_client.get("/api/v1/eventos/?search=&page=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["titulo"], "Aula inaugural")
        self.assertEqual(response.data["results"][0]["turma_nome"], self.turma.nome)

    def test_api_manage_eventos_requires_staff_role(self):
        secretaria = Usuario.objects.create_user(
            username="secretaria_agenda",
            cpf="62345678902",
            tipo=PerfilUsuario.SECRETARIA,
            password="x",
        )

        self._authenticate_api_client(self.professor)
        forbidden_response = self.api_client.post(
            "/api/v1/eventos/",
            {
                "titulo": "Reuniao extra",
                "descricao": "Planejamento.",
                "turma": self.turma.pk,
                "inicio": "2026-03-11T08:00:00-03:00",
                "fim": "2026-03-11T09:00:00-03:00",
            },
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, 403)

        self._authenticate_api_client(secretaria)
        authorized_response = self.api_client.post(
            "/api/v1/eventos/",
            {
                "titulo": "Reuniao extra",
                "descricao": "Planejamento.",
                "turma": self.turma.pk,
                "inicio": "2026-03-11T08:00:00-03:00",
                "fim": "2026-03-11T09:00:00-03:00",
            },
            format="json",
        )
        self.assertEqual(authorized_response.status_code, 201)
        self.assertTrue(EventoAgenda.objects.filter(titulo="Reuniao extra").exists())
