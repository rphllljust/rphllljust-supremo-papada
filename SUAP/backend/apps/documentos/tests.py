from django.test import TestCase
from django.urls import reverse

from apps.documentos.models import AtaOficioMemorando
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


class AtaAssistenteTests(TestCase):
    def setUp(self):
        cpf = gerar_cpf(423456780)
        self.usuario = Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
        )
        self.client.force_login(self.usuario)

    def test_salva_rascunho_ata(self):
        response = self.client.post(
            reverse("documentos:ata_create"),
            {
                "acao": "rascunho",
                "assunto": "Ata de reunião administrativa",
                "ano": "2026",
                "participantes_json": "[]",
                "pauta_json": "[]",
                "deliberacoes_json": "[]",
                "encaminhamentos_json": "[]",
                "anexos_json": "[]",
                "assinaturas_json": "[]",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        doc = AtaOficioMemorando.objects.latest("id")
        self.assertEqual(doc.situacao, "RASCUNHO")
        self.assertEqual(doc.tipo, "ATA")

    def test_emite_ata_com_campos_essenciais(self):
        response = self.client.post(
            reverse("documentos:ata_create"),
            {
                "acao": "emitir",
                "assunto": "Ata do Conselho Escolar",
                "ano": "2026",
                "numero_ata": "001/2026",
                "tipo_reuniao_registro": "CONSELHO_ESCOLAR",
                "data_reuniao": "2026-03-05",
                "horario_inicio": "09:00",
                "horario_termino": "11:00",
                "local_reuniao": "Sala de reuniões",
                "modalidade": "PRESENCIAL",
                "cidade_uf": "Porto Velho-RO",
                "presidente_reuniao": "Maria Silva - Diretora",
                "responsavel_lavratura": "Joao Souza - Secretario",
                "participantes_json": '[{"nome":"Maria Silva","cargo":"Diretora","presente":true}]',
                "pauta_json": '[{"titulo":"Resultados do bimestre","descricao":"Analise geral"}]',
                "deliberacoes_json": '[{"titulo":"Resultados do bimestre","relato":"Apresentacao de dados","decisao":"Aprovado plano","responsavel":"Coordenacao","prazo":"2026-03-20","observacoes":"Sem ressalvas"}]',
                "encaminhamentos_json": '[{"descricao":"Atualizar plano","responsavel":"Coordenacao","prazo":"2026-03-20"}]',
                "anexos_json": "[]",
                "assinaturas_json": '[{"nome":"Maria Silva","cargo":"Diretora","tipo_assinatura":"eletronica"}]',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        doc = AtaOficioMemorando.objects.latest("id")
        self.assertEqual(doc.situacao, "EMITIDO")
        self.assertTrue(doc.numero_ata)
        self.assertTrue(doc.chave_autenticidade)
        self.assertIsNotNone(doc.data_emissao_final)

    def test_bloqueia_edicao_quando_emitida(self):
        doc = AtaOficioMemorando.objects.create(
            tipo="ATA",
            assunto="Ata emitida",
            emitido_por=self.usuario,
            situacao="RASCUNHO",
        )
        doc.emitir()
        doc.save()

        response = self.client.get(reverse("documentos:ata_update", args=[doc.pk]), follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("documentos:ata_detalhe", args=[doc.pk]))
