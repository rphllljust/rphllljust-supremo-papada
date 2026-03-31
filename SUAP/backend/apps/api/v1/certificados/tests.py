from rest_framework import status
from rest_framework.test import APITestCase
from django.test import override_settings

from apps.certificados.models import CertificadoEmitido, ConfiguracaoVisualCertificado, ModeloCertificado
from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.unidades.models import Unidade
from apps.usuarios.models import Aluno, PerfilUsuario, Pessoa, Usuario


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


class CertificadosQrCodeApiTests(APITestCase):
    def _criar_usuario(self, seed: int, tipo: str, nome: str):
        cpf = gerar_cpf(seed)
        pessoa = Pessoa.objects.create(nome_completo=nome, cpf=cpf)
        return Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=tipo,
            password='senha123',
            pessoa=pessoa,
        )

    def setUp(self):
        self.admin = self._criar_usuario(300000001, PerfilUsuario.ADMIN, 'Admin Certificados')
        self.professor = self._criar_usuario(300000002, PerfilUsuario.PROFESSOR, 'Professor Teste')
        self.aluno_user = self._criar_usuario(300000003, PerfilUsuario.ALUNO, 'Aluno Teste')
        self.aluno = Aluno.objects.create(pessoa=self.aluno_user.pessoa)

        self.unidade, _ = Unidade.objects.get_or_create(nome='Sede', codigo='sede')
        self.curso = Curso.objects.create(
            unidade=self.unidade,
            nome='Tecnico em Desenvolvimento de Sistemas',
            sigla='TDS',
            carga_horaria=1200,
            tipo_curso='tecnico',
        )
        self.turma = Turma.objects.create(
            curso=self.curso,
            nome='TDS-2026-1',
            ano_letivo=2026,
            professor_responsavel=self.professor,
            status='ATIVA',
        )
        self.matricula = Matricula.objects.create(
            aluno=self.aluno_user,
            curso=self.curso,
            turma=self.turma,
            status='CONCLUIDA',
            tipo_matricula='NOVA',
            turno='NOITE',
        )

        self.modelo = ModeloCertificado.objects.create(
            nome='Modelo Oficial Diploma e Historico',
            tipo='DIPLOMA',
            curso=self.curso,
            unidade=self.unidade,
            ativo=True,
        )
        ConfiguracaoVisualCertificado.objects.create(modelo=self.modelo)

        self.client.force_authenticate(user=self.admin)

    def _emitir(self, tipo_documento='DIPLOMA', sobrescritas=None):
        payload = {
            'modelo_id': self.modelo.id,
            'matricula_id': self.matricula.id,
            'tipo_documento': tipo_documento,
            'gerar_pdf': True,
            'sobrescritas': {
                'livro': 'L-01',
                'folha': 'F-10',
                'pagina': 'P-100',
                **(sobrescritas or {}),
            },
        }
        return self.client.post('/api/v1/certificados/emitir/', payload, format='json')

    def test_emissao_diploma_com_qrcode_e_pdf(self):
        response = self._emitir(tipo_documento='DIPLOMA')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tipo_documento'], 'DIPLOMA')
        self.assertTrue(response.data['numero_registro'])
        self.assertTrue(response.data['codigo_validacao'])
        self.assertTrue(response.data['hash_integridade'])
        self.assertTrue(response.data['url_validacao'])
        self.assertEqual(CertificadoEmitido.objects.count(), 1)

    def test_emissao_historico_com_qrcode_e_pdf(self):
        response = self._emitir(tipo_documento='HISTORICO', sobrescritas={'livro': 'H-01'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['tipo_documento'], 'HISTORICO')
        self.assertIn('numero_registro', response.data)
        self.assertIn('dados_dinamicos', response.data)
        self.assertIn('disciplinas', response.data['dados_dinamicos'])
        self.assertIn('media_final', response.data['dados_dinamicos'])
        self.assertIn('frequencia_final', response.data['dados_dinamicos'])

    def test_validacao_publica_por_codigo(self):
        emissao = self._emitir(tipo_documento='DIPLOMA')
        codigo = emissao.data['codigo_validacao']

        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/publico/validar-documento/{codigo}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['autenticidade'], 'valido')
        self.assertEqual(response.data['tipo_documento'], 'DIPLOMA')
        self.assertEqual(response.data['numero_registro'], emissao.data['numero_registro'])

    def test_bloqueio_de_duplicidade(self):
        primeira = self._emitir(tipo_documento='DIPLOMA')
        self.assertEqual(primeira.status_code, status.HTTP_201_CREATED)

        duplicada = self._emitir(tipo_documento='DIPLOMA')
        self.assertEqual(duplicada.status_code, status.HTTP_409_CONFLICT)
        self.assertIn('Ja existe documento ativo', duplicada.data['detail'])

    def test_rascunho_existente_nao_bloqueia_emissao(self):
        CertificadoEmitido.objects.create(
            modelo=self.modelo,
            aluno=self.aluno,
            matricula=self.matricula,
            curso=self.curso,
            unidade=self.unidade,
            turma=self.turma,
            usuario_emissor=self.admin,
            tipo_documento='DIPLOMA',
            status_documento='RASCUNHO',
            status='DIPLOMA_EM_PREPARACAO',
            livro='TMP',
            folha='TMP',
            pagina='TMP',
        )

        response = self._emitir(tipo_documento='DIPLOMA')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status_documento'], 'EMITIDO')

    @override_settings(CERTIFICADOS_VALIDATION_FRONTEND_BASE_URL='https://portal.idep.edu.br')
    def test_url_validacao_usa_base_publica_configurada(self):
        response = self._emitir(tipo_documento='HISTORICO')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['url_validacao'].startswith('https://portal.idep.edu.br/validar-documento/'))

    def test_reemissao_com_rastreabilidade(self):
        primeira = self._emitir(tipo_documento='DIPLOMA')
        documento_id = primeira.data['id']

        response = self.client.post(f'/api/v1/certificados/emitidos/{documento_id}/reemitir/', {'gerar_pdf': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        antigo = CertificadoEmitido.objects.get(id=documento_id)
        novo = CertificadoEmitido.objects.get(id=response.data['documento']['id'])

        self.assertEqual(antigo.status_documento, 'REEMITIDO')
        self.assertEqual(novo.reemitido_de_id, antigo.id)
        self.assertEqual(novo.tipo_documento, antigo.tipo_documento)

    def test_cancelamento_documento(self):
        emissao = self._emitir(tipo_documento='HISTORICO')
        documento_id = emissao.data['id']

        response = self.client.post(
            f'/api/v1/certificados/emitidos/{documento_id}/cancelar/',
            {'motivo': 'Erro de grafia no nome'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certificado']['status_documento'], 'CANCELADO')

    def test_qrcode_pdf_e_status_validacao(self):
        emissao = self._emitir(tipo_documento='DIPLOMA')
        documento_id = emissao.data['id']

        qrcode_response = self.client.get(f'/api/v1/certificados/emitidos/{documento_id}/qrcode/')
        self.assertEqual(qrcode_response.status_code, status.HTTP_200_OK)
        self.assertEqual(qrcode_response['Content-Type'], 'image/png')

        pdf_response = self.client.get(f'/api/v1/certificados/emitidos/{documento_id}/pdf/')
        self.assertEqual(pdf_response.status_code, status.HTTP_200_OK)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')

        status_response = self.client.get(f'/api/v1/certificados/emitidos/{documento_id}/status-validacao/')
        self.assertEqual(status_response.status_code, status.HTTP_200_OK)
        self.assertEqual(status_response.data['autenticidade'], 'valido')

    def test_listagem_e_busca_por_campos_documentais(self):
        primeira = self._emitir(tipo_documento='DIPLOMA', sobrescritas={'livro': 'LIV-A', 'folha': '001', 'pagina': '010'})
        segunda = self._emitir(tipo_documento='HISTORICO', sobrescritas={'livro': 'LIV-B', 'folha': '002', 'pagina': '011'})

        filtro_tipo = self.client.get('/api/v1/certificados/emitidos/', {'tipo_documento': 'HISTORICO'})
        self.assertEqual(filtro_tipo.status_code, status.HTTP_200_OK)
        self.assertEqual(filtro_tipo.data['count'], 1)

        filtro_registro = self.client.get('/api/v1/certificados/emitidos/', {'numero_registro': segunda.data['numero_registro']})
        self.assertEqual(filtro_registro.status_code, status.HTTP_200_OK)
        self.assertEqual(filtro_registro.data['count'], 1)

        filtro_livro_folha_pagina = self.client.get(
            '/api/v1/certificados/emitidos/',
            {'livro': 'LIV-A', 'folha': '001', 'pagina': '010'},
        )
        self.assertEqual(filtro_livro_folha_pagina.status_code, status.HTTP_200_OK)
        self.assertEqual(filtro_livro_folha_pagina.data['count'], 1)
        self.assertEqual(filtro_livro_folha_pagina.data['results'][0]['id'], primeira.data['id'])

    def test_historico_de_emissao_disponivel(self):
        self._emitir(tipo_documento='DIPLOMA')

        response = self.client.get('/api/v1/certificados/historico/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
