from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.cursos.models import Curso
from apps.matriculas.models import FluxoTransferencia, Matricula
from django.core.exceptions import ValidationError
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario


class TransferenciaFluxoAutoCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.curso = Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)
        self.turma = Turma.objects.create(curso=self.curso, nome="ADM-T1", ano_letivo=2026, status="ATIVA")
        self.secretaria = Usuario.objects.create_user(
            username="sec_transf",
            cpf="90000010059",
            tipo="SECRETARIA",
            password="senha123",
        )
        self.aluno = Usuario.objects.create_user(
            username="aluno_transf",
            cpf="90000010060",
            tipo="ALUNO",
            password="x",
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="ATIVA",
            tipo_matricula="NOVA",
        )

        self.client.force_authenticate(user=self.secretaria)

    def test_create_transferencia_auto_creates_fluxo_transferencia(self):
        response = self.client.post(
            reverse("api_v1_transferencias:list"),
            {
                "matricula": self.matricula.id,
                "tipo": "SAIDA",
                "escola_destino": "Escola Estadual Exemplo",
                "status": "SOLICITADA",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        transferencia_id = response.data["id"]
        self.assertTrue(FluxoTransferencia.objects.filter(transferencia_id=transferencia_id).exists())

    def test_blocks_invalid_status_transition(self):
        response = self.client.post(
            reverse("api_v1_transferencias:list"),
            {
                "matricula": self.matricula.id,
                "tipo": "SAIDA",
                "escola_destino": "Escola Estadual Exemplo",
                "status": "SOLICITADA",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

        from apps.matriculas.models import Transferencia
        transferencia = Transferencia.objects.get(pk=response.data["id"])
        transferencia.status = "CONCLUIDA"
        with self.assertRaises(ValidationError):
            transferencia.full_clean()
