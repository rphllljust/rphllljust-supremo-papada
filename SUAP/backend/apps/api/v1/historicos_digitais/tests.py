from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from apps.cursos.models import Curso
from apps.documentos.models import HistoricoEscolar, HistoricoEscolarDigital
from apps.matriculas.models import ConsolidacaoAcademica, Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import PerfilUsuario, Usuario


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


class HistoricoDigitalApiTests(APITestCase):
    def setUp(self):
        self.secretaria = Usuario.objects.create_user(
            username=gerar_cpf(100000001),
            cpf=gerar_cpf(100000001),
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
        )
        self.professor = Usuario.objects.create_user(
            username=gerar_cpf(100000002),
            cpf=gerar_cpf(100000002),
            tipo=PerfilUsuario.PROFESSOR,
            password="senha123",
        )
        self.aluno = Usuario.objects.create_user(
            username=gerar_cpf(100000003),
            cpf=gerar_cpf(100000003),
            tipo=PerfilUsuario.ALUNO,
            password="senha123",
        )

        self.unidade, _ = Unidade.objects.get_or_create(nome="Sede", codigo="sede")
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome="Tecnico em Desenvolvimento de Sistemas",
            sigla="TDS",
            carga_horaria=1200,
            tipo_curso="tecnico",
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome="TDS-2026-1",
            ano_letivo=2026,
            professor_responsavel=self.professor,
            status="ATIVA",
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno,
            curso=self.curso,
            turma=self.turma,
            status="CONCLUIDA",
            tipo_matricula="NOVA",
            turno="NOITE",
        )
        ConsolidacaoAcademica.objects.create(
            matricula=self.matricula,
            media_final=Decimal("8.50"),
            percentual_frequencia=Decimal("92.00"),
            situacao="APROVADO",
        )
        self.historico = HistoricoEscolar.objects.create(
            tipo="COMPLETO",
            assunto="Historico escolar completo",
            matricula=self.matricula,
            emitido_por=self.secretaria,
            periodo_ref="2026",
        )

    def test_secretaria_emite_historico_digital_parcial(self):
        self.client.force_authenticate(user=self.secretaria)
        response = self.client.post(
            f"/api/v1/historicos-digitais/emitir/{self.historico.id}/",
            {"tipo_documento": "PARCIAL", "assinar_xml": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["created"])
        documento = response.data["documento"]
        self.assertTrue(documento["numero_unico"])
        self.assertTrue(documento["chave_autenticacao"])
        self.assertIn("validacao_xsd_ok", documento)
        self.assertEqual(HistoricoEscolarDigital.objects.count(), 1)

    def test_professor_nao_pode_emitir_historico_digital(self):
        self.client.force_authenticate(user=self.professor)
        response = self.client.post(
            f"/api/v1/historicos-digitais/emitir/{self.historico.id}/",
            {"tipo_documento": "PARCIAL", "assinar_xml": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_validacao_publica_por_chave(self):
        self.client.force_authenticate(user=self.secretaria)
        response = self.client.post(
            f"/api/v1/historicos-digitais/emitir/{self.historico.id}/",
            {"tipo_documento": "PARCIAL", "assinar_xml": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chave = response.data["documento"]["chave_autenticacao"]

        self.client.force_authenticate(user=None)
        validacao = self.client.get(f"/api/v1/historicos-digitais/validar-publico/?chave={chave}")
        self.assertEqual(validacao.status_code, status.HTTP_200_OK)
        self.assertTrue(validacao.data["documento_encontrado"])
        self.assertEqual(validacao.data["historico_protocolo"], self.historico.numero_protocolo)

    def test_historico_final_exige_consolidacao_e_status_concluida(self):
        consolidacao = self.matricula.consolidacao
        consolidacao.situacao = "PENDENTE"
        consolidacao.save(update_fields=["situacao"])

        self.client.force_authenticate(user=self.secretaria)
        response = self.client.post(
            f"/api/v1/historicos-digitais/emitir/{self.historico.id}/",
            {"tipo_documento": "FINAL", "assinar_xml": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("aprovada", response.data["detail"].lower())
