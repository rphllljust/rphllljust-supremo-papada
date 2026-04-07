from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.auditoria.models import LogAuditoria
from apps.cursos.models import ComponenteCurricular, Curso
from apps.documentos.models import HistoricoEscolarTecnicoDocumento
from apps.documentos.services.historico_escolar_tecnico import (
    gerar_hash_documento,
    gerar_qrcode_validacao,
)
from apps.frequencia.models import Frequencia
from apps.matriculas.models import ConsolidacaoAcademica, Matricula
from apps.notas.models import Nota
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import PerfilUsuario


Usuario = get_user_model()


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


class HistoricoTecnicoApiTests(APITestCase):
    def setUp(self):
        self.admin = Usuario.objects.create_user(
            username=gerar_cpf(210000001),
            cpf=gerar_cpf(210000001),
            tipo=PerfilUsuario.ADMIN,
            password="senha123",
            is_superuser=True,
            is_staff=True,
        )
        self.secretaria = Usuario.objects.create_user(
            username=gerar_cpf(210000002),
            cpf=gerar_cpf(210000002),
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
        )
        self.professor = Usuario.objects.create_user(
            username=gerar_cpf(210000003),
            cpf=gerar_cpf(210000003),
            tipo=PerfilUsuario.PROFESSOR,
            password="senha123",
        )
        self.aluno = Usuario.objects.create_user(
            username=gerar_cpf(210000004),
            cpf=gerar_cpf(210000004),
            tipo=PerfilUsuario.ALUNO,
            password="senha123",
        )

        self.unidade, _ = Unidade.objects.get_or_create(nome="Sede", codigo="sede", defaults={"cidade": "Porto Velho", "uf": "RO"})
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome="Tecnico em Informatica",
            sigla="TIN",
            tipo_curso="tecnico",
            carga_horaria=1200,
            eixo_tecnologico="Informacao e Comunicacao",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="TIN-2026-1",
            ano_letivo=2026,
            status="ATIVA",
            professor_responsavel=self.professor,
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="CONCLUIDA",
            tipo_matricula="NOVA",
            turno="NOITE",
        )

        ComponenteCurricular.objects.create(curso=self.curso, nome="Programacao I", sigla="PRG1", carga_horaria=80, ordem=1)
        ComponenteCurricular.objects.create(curso=self.curso, nome="Banco de Dados", sigla="BD", carga_horaria=80, ordem=2)

        Nota.objects.create(matricula=self.matricula, descricao="Programacao I", valor=Decimal("8.5"), peso=Decimal("1"), data_lancamento=timezone.now().date())
        Nota.objects.create(matricula=self.matricula, descricao="Banco de Dados", valor=Decimal("7.8"), peso=Decimal("1"), data_lancamento=timezone.now().date())

        Frequencia.objects.create(matricula=self.matricula, data=timezone.now().date(), presente=True)
        Frequencia.objects.create(matricula=self.matricula, data=timezone.now().date() + timedelta(days=1), presente=True)

        ConsolidacaoAcademica.objects.create(
            matricula=self.matricula,
            media_final=Decimal("8.15"),
            percentual_frequencia=Decimal("100.00"),
            situacao="APROVADO",
            data_consolidacao=timezone.now().date(),
        )

    def test_emissao_com_sucesso(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["numero_registro"])
        self.assertEqual(HistoricoEscolarTecnicoDocumento.objects.count(), 1)

    def test_bloqueio_dados_incompletos(self):
        Nota.objects.filter(matricula=self.matricula).delete()
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("notas", response.data["detail"].lower())

    def test_geracao_hash(self):
        payload = {"aluno": "Teste", "curso": "Tecnico", "versao": 1}
        hash_1 = gerar_hash_documento(payload)
        hash_2 = gerar_hash_documento(payload)
        self.assertEqual(hash_1, hash_2)
        self.assertEqual(len(hash_1), 64)

    def test_geracao_qrcode(self):
        qr = gerar_qrcode_validacao("http://localhost/validacao/historico/123")
        self.assertTrue(qr)
        self.assertGreater(len(qr), 100)

    def test_geracao_pdf(self):
        self.client.force_authenticate(self.admin)
        emit_response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        historico_id = emit_response.data["id"]

        pdf_response = self.client.get(f"/api/v1/historicos/{historico_id}/pdf/")
        self.assertEqual(pdf_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")

    def test_preview_emissao_serializavel(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/v1/historicos/preview/", {"matricula_id": self.matricula.id}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["itens"])
        self.assertIn("componente_curricular_id", response.data["itens"][0])

    def test_validacao_publica(self):
        self.client.force_authenticate(self.admin)
        emit_response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        uuid = emit_response.data["uuid"]

        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/v1/validacao/historicos/{uuid}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["documento_encontrado"])
        self.assertEqual(response.data["autenticidade"], "VALIDO")

    def test_reemissao_incrementa_versao(self):
        self.client.force_authenticate(self.admin)
        emit_response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        original_id = emit_response.data["id"]

        reemitir_response = self.client.post(
            f"/api/v1/historicos/{original_id}/reemitir/",
            {"motivo": "Ajuste de dados institucionais"},
            format="json",
        )
        self.assertEqual(reemitir_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(reemitir_response.data["versao"], 2)

        original = HistoricoEscolarTecnicoDocumento.objects.get(pk=original_id)
        self.assertEqual(original.status, HistoricoEscolarTecnicoDocumento.StatusDocumento.SUBSTITUIDO)

    def test_cancelamento(self):
        self.client.force_authenticate(self.admin)
        emit_response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        historico_id = emit_response.data["id"]

        cancel_response = self.client.post(
            f"/api/v1/historicos/{historico_id}/cancelar/",
            {"motivo": "Cancelamento administrativo"},
            format="json",
        )
        self.assertEqual(cancel_response.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_response.data["status"], "CANCELADO")

    def test_permissoes(self):
        self.client.force_authenticate(self.professor)
        response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        self.assertIn(response.status_code, {status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN})

    def test_auditoria(self):
        self.client.force_authenticate(self.admin)
        emit_response = self.client.post("/api/v1/historicos/emitir/", {"matricula_id": self.matricula.id}, format="json")
        historico_id = emit_response.data["id"]

        historico = HistoricoEscolarTecnicoDocumento.objects.get(pk=historico_id)
        self.client.force_authenticate(user=None)
        self.client.get(f"/api/v1/validacao/historicos/{historico.uuid}/")

        self.assertTrue(
            LogAuditoria.objects.filter(modelo="HistoricoEscolarTecnicoDocumento", objeto_id=historico_id).exists()
        )
