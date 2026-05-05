from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula, PendenciaDocumental
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario


class RematriculaFinanceiraTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
        self.turma = Turma.objects.create(curso=self.curso, nome="ADM-2026", ano_letivo=2026, status="ATIVA")

        self.secretaria = Usuario.objects.create_user(
            username="sec_fin",
            cpf="90000010057",
            tipo="SECRETARIA",
            password="senha123",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_fin",
            cpf="90000010058",
            tipo="ALUNO",
            password="x",
        )

        self.matricula_ativa = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
            tipo_matricula="NOVA",
        )
        PendenciaDocumental.objects.create(
            matricula=self.matricula_ativa,
            descricao="Inadimplencia financeira - mensalidade em atraso",
            status="ABERTA",
        )

        token_response = self.client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {"cpf": self.secretaria.cpf, "password": "senha123", "perfil": "SECRETARIA"},
            format="json",
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}")

    def test_blocks_rematricula_with_financial_delinquency(self):
        response = self.client.post(
            reverse("api_v1_matriculas:list"),
            {
                "aluno": self.aluno.id,
                "curso": self.curso.id,
                "turma": self.turma.id,
                "tipo_matricula": "REMATRICULA",
                "status": "ATIVA",
                "turno": "NOITE",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tipo_matricula", response.data)
