"""
Domínio de Documentos – Class Diagram
Hierarquia com DocumentoBase (abstrato) → Declaracao, HistoricoEscolar,
GuiaTransferencia, AtaOficioMemorando
"""

import uuid

from apps.cursos.models import Curso as CursoTecnico
from apps.unidades.models import Unidade as InstituicaoEmissora
from apps.usuarios.models import Aluno
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string


def _ano_atual():
    return timezone.now().year


class DocumentoBase(models.Model):
    """
    Classe abstrata base para todos os documentos emitidos pela secretaria.
    Cada subclasse recebe sua própria tabela + numeração de protocolo.
    """

    numero_protocolo = models.CharField(
        max_length=20, unique=True, editable=False, verbose_name='Nº de Protocolo'
    )
    data_emissao = models.DateField(auto_now_add=True, verbose_name='Data de Emissão')
    assunto      = models.CharField(max_length=255, verbose_name='Assunto')
    emitido_por  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name='Emitido por',
    )
    matricula    = models.ForeignKey(
        'matriculas.Matricula',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='+',
        verbose_name='Matrícula',
    )
    observacao   = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        abstract = True
        ordering = ['-data_emissao']

    @classmethod
    def _prefixo(cls):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        if not self.numero_protocolo:
            self.numero_protocolo = self._gerar_protocolo()
        super().save(*args, **kwargs)

    def _gerar_protocolo(self):
        from django.utils import timezone
        ano = timezone.now().year
        prefixo = self._prefixo()
        ultimo = (
            self.__class__.objects
            .filter(numero_protocolo__startswith=f'{prefixo}-{ano}-')
            .order_by('-numero_protocolo')
            .first()
        )
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero_protocolo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = self.__class__.objects.filter(
                    numero_protocolo__startswith=f'{prefixo}-{ano}-'
                ).count() + 1
        return f'{prefixo}-{ano}-{seq:04d}'

    def __str__(self):
        return f'{self.numero_protocolo} – {self.assunto}'


# ── Declaração ────────────────────────────────────────────────────────────────

class Declaracao(DocumentoBase):
    """Declaração de Matrícula, Frequência ou Conclusão."""

    TIPO_CHOICES = (
        ('MATRICULA',  'Declaração de Matrícula'),
        ('FREQUENCIA', 'Declaração de Frequência'),
        ('CONCLUSAO',  'Declaração de Conclusão de Curso'),
    )

    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, verbose_name='Tipo de Declaração')

    class Meta(DocumentoBase.Meta):
        verbose_name = 'Declaração'
        verbose_name_plural = 'Declarações'

    @classmethod
    def _prefixo(cls):
        return 'DEC'


# ── Histórico Escolar ─────────────────────────────────────────────────────────

class HistoricoEscolar(DocumentoBase):
    """Histórico Escolar completo ou parcial."""

    TIPO_CHOICES = (
        ('COMPLETO', 'Histórico Completo'),
        ('PARCIAL',  'Histórico Parcial'),
    )

    tipo         = models.CharField(max_length=10, choices=TIPO_CHOICES, default='COMPLETO', verbose_name='Tipo')
    periodo_ref  = models.CharField(max_length=50, blank=True, verbose_name='Período de Referência')

    class Meta(DocumentoBase.Meta):
        verbose_name = 'Histórico Escolar'
        verbose_name_plural = 'Históricos Escolares'

    @classmethod
    def _prefixo(cls):
        return 'HIS'


# ── Guia de Transferência ─────────────────────────────────────────────────────

class GuiaTransferencia(DocumentoBase):
    """Guia emitida para transferência de aluno."""

    escola_origem  = models.CharField(max_length=200, blank=True, verbose_name='Escola de Origem')
    escola_destino = models.CharField(max_length=200, blank=True, verbose_name='Escola de Destino')
    transferencia  = models.ForeignKey(
        'matriculas.Transferencia',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='guias',
        verbose_name='Transferência',
    )

    class Meta(DocumentoBase.Meta):
        verbose_name = 'Guia de Transferência'
        verbose_name_plural = 'Guias de Transferência'

    @classmethod
    def _prefixo(cls):
        return 'GTR'


# ── Ata / Ofício / Memorando ──────────────────────────────────────────────────

class AtaOficioMemorando(DocumentoBase):
    """Ata de reunião, Ofício ou Memorando interno/externo."""

    TIPO_CHOICES = (
        ('ATA',       'Ata'),
        ('OFICIO',    'Ofício'),
        ('MEMORANDO', 'Memorando'),
    )

    TIPO_REUNIAO_CHOICES = (
        ('CONSELHO_ESCOLAR', 'Conselho Escolar'),
        ('CONSELHO_CLASSE', 'Conselho de Classe'),
        ('REUNIAO_PEDAGOGICA', 'Reunião Pedagógica'),
        ('REUNIAO_ADMINISTRATIVA', 'Reunião Administrativa'),
        ('OUTRO', 'Outro'),
    )

    MODALIDADE_CHOICES = (
        ('PRESENCIAL', 'Presencial'),
        ('ONLINE', 'Online'),
        ('HIBRIDA', 'Híbrida'),
    )

    SITUACAO_CHOICES = (
        ('RASCUNHO', 'Rascunho'),
        ('EMITIDO', 'Emitido'),
    )

    tipo         = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    destinatario = models.CharField(max_length=255, blank=True, verbose_name='Destinatário')
    referencia   = models.CharField(max_length=100, blank=True, verbose_name='Referência')
    processo     = models.ForeignKey(
        'processos.Processo',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='atas_oficios',
        verbose_name='Processo Vinculado',
    )
    numero_ata = models.CharField(max_length=20, blank=True, verbose_name='Número da Ata')
    ano = models.PositiveIntegerField(default=_ano_atual, verbose_name='Ano')
    tipo_reuniao_registro = models.CharField(
        max_length=30,
        choices=TIPO_REUNIAO_CHOICES,
        blank=True,
        verbose_name='Tipo de Reunião/Registro',
    )
    tipo_reuniao_outro = models.CharField(max_length=255, blank=True, verbose_name='Outro Tipo de Reunião')
    livro = models.CharField(max_length=50, blank=True, verbose_name='Livro')
    folha_pagina = models.CharField(max_length=50, blank=True, verbose_name='Folha/Página')

    data_reuniao = models.DateField(null=True, blank=True, verbose_name='Data da Reunião')
    horario_inicio = models.TimeField(null=True, blank=True, verbose_name='Horário de Início')
    horario_termino = models.TimeField(null=True, blank=True, verbose_name='Horário de Término')
    local_reuniao = models.CharField(max_length=255, blank=True, verbose_name='Local')
    modalidade = models.CharField(max_length=20, choices=MODALIDADE_CHOICES, blank=True, verbose_name='Modalidade')
    plataforma = models.CharField(max_length=100, blank=True, verbose_name='Plataforma')
    link_reuniao = models.URLField(blank=True, verbose_name='Link da Reunião')
    cidade_uf = models.CharField(max_length=120, blank=True, verbose_name='Cidade/UF')

    presidente_reuniao = models.CharField(max_length=255, blank=True, verbose_name='Presidente/Coordenação')
    responsavel_lavratura = models.CharField(max_length=255, blank=True, verbose_name='Responsável pela Lavratura')
    participantes = models.JSONField(default=list, blank=True, verbose_name='Participantes')
    pauta = models.JSONField(default=list, blank=True, verbose_name='Pauta')
    deliberacoes = models.JSONField(default=list, blank=True, verbose_name='Relato e Deliberações')
    encaminhamentos = models.JSONField(default=list, blank=True, verbose_name='Encaminhamentos')
    assinaturas = models.JSONField(default=list, blank=True, verbose_name='Assinaturas')

    horario_encerramento = models.TimeField(null=True, blank=True, verbose_name='Horário de Encerramento')
    texto_abertura = models.TextField(blank=True, verbose_name='Texto de Abertura')
    texto_final = models.TextField(blank=True, verbose_name='Texto Final')
    forma_assinatura = models.CharField(max_length=120, blank=True, verbose_name='Forma de Assinatura')
    chave_autenticidade = models.CharField(max_length=32, blank=True, verbose_name='Chave de Autenticidade')
    situacao = models.CharField(max_length=12, choices=SITUACAO_CHOICES, default='RASCUNHO', verbose_name='Situação')
    data_emissao_final = models.DateTimeField(null=True, blank=True, verbose_name='Data/Hora de Emissão Final')

    class Meta(DocumentoBase.Meta):
        verbose_name = 'Ata / Ofício / Memorando'
        verbose_name_plural = 'Atas / Ofícios / Memorandos'

    @classmethod
    def _prefixo(cls):
        return 'ATA'

    def gerar_numero_ata(self):
        if self.numero_ata:
            return self.numero_ata
        ano_ref = self.ano or _ano_atual()
        ultimo = (
            AtaOficioMemorando.objects
            .filter(tipo='ATA', ano=ano_ref, numero_ata__regex=r'^\d{3}/\d{4}$')
            .order_by('-numero_ata')
            .first()
        )
        seq = 1
        if ultimo and ultimo.numero_ata:
            try:
                seq = int(ultimo.numero_ata.split('/')[0]) + 1
            except (ValueError, IndexError):
                seq = (
                    AtaOficioMemorando.objects
                    .filter(tipo='ATA', ano=ano_ref)
                    .exclude(numero_ata='')
                    .count() + 1
                )
        return f'{seq:03d}/{ano_ref}'

    def emitir(self):
        self.tipo = 'ATA'
        self.numero_ata = self.gerar_numero_ata()
        self.situacao = 'EMITIDO'
        self.data_emissao_final = timezone.now()
        if not self.chave_autenticidade:
            self.chave_autenticidade = timezone.now().strftime('%Y%m%d%H%M%S%f')[-16:]


class AtaAnexo(models.Model):
    """Anexos opcionais vinculados à ata digital."""

    TIPO_CHOICES = (
        ('LISTA_PRESENCA', 'Lista de presença'),
        ('RELATORIO', 'Relatório'),
        ('FOTOS', 'Fotos'),
        ('PRINTS', 'Prints'),
        ('OUTROS', 'Outros'),
    )

    ata = models.ForeignKey(
        AtaOficioMemorando,
        on_delete=models.CASCADE,
        related_name='anexos_upload',
    )
    tipo_anexo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OUTROS', verbose_name='Tipo do Anexo')
    descricao = models.CharField(max_length=255, blank=True, verbose_name='Descrição')
    arquivo = models.FileField(upload_to='documentos/atas/anexos/', null=True, blank=True, verbose_name='Arquivo')

    class Meta:
        verbose_name = 'Anexo da Ata'
        verbose_name_plural = 'Anexos da Ata'

    def __str__(self):
        return f'{self.get_tipo_anexo_display()} - {self.descricao or self.pk}'


class HistoricoEscolarDigital(models.Model):
    """
    Camada digital complementar do HistoricoEscolar para emissao oficial
    (XML MEC, validacao XSD, assinatura XMLDSig, PDF e chave de autenticacao).
    """

    TIPO_DOCUMENTO_CHOICES = (
        ('PARCIAL', 'DocumentoHistoricoEscolarParcial'),
        ('FINAL', 'DocumentoHistoricoEscolarFinal'),
        ('SEGUNDA_VIA_NATO_FISICO', 'DocumentoHistoricoEscolarSegundaViaNatoFisico'),
    )

    STATUS_CHOICES = (
        ('GERADO', 'Gerado'),
        ('VALIDADO', 'Validado'),
        ('ASSINADO', 'Assinado'),
        ('REVOGADO', 'Revogado'),
        ('ERRO', 'Erro'),
    )

    historico = models.ForeignKey(
        HistoricoEscolar,
        on_delete=models.CASCADE,
        related_name='versoes_digitais',
        verbose_name='Historico Base',
    )
    referencia_original = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='segundas_vias_emitidas',
        verbose_name='Documento Digital Original',
    )
    tipo_documento = models.CharField(max_length=32, choices=TIPO_DOCUMENTO_CHOICES, verbose_name='Tipo do Documento MEC')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='GERADO', verbose_name='Status')
    versao = models.PositiveIntegerField(default=1, verbose_name='Versao')
    numero_unico = models.CharField(max_length=40, unique=True, editable=False, verbose_name='Numero Unico')
    hash_documento = models.CharField(max_length=64, blank=True, verbose_name='Hash SHA-256')
    chave_autenticacao = models.CharField(max_length=32, unique=True, editable=False, verbose_name='Chave de Autenticacao')
    xml_conteudo = models.TextField(verbose_name='XML Gerado')
    xml_assinado_conteudo = models.TextField(blank=True, verbose_name='XML Assinado')
    validacao_xsd_ok = models.BooleanField(default=False, verbose_name='Validacao XSD OK')
    validacao_xsd_erros = models.JSONField(default=list, blank=True, verbose_name='Erros da Validacao XSD')
    assinado_digitalmente = models.BooleanField(default=False, verbose_name='Assinado Digitalmente')
    assinatura_metadados = models.JSONField(default=dict, blank=True, verbose_name='Metadados de Assinatura')
    qr_payload_url = models.CharField(max_length=600, blank=True, verbose_name='URL de Validacao por QR Code')
    qr_code_data_uri = models.TextField(blank=True, verbose_name='QR Code Data URI')
    pdf_arquivo = models.FileField(upload_to='documentos/historicos_digitais/pdf/', null=True, blank=True, verbose_name='PDF Institucional')
    revogado = models.BooleanField(default=False, verbose_name='Revogado')
    motivo_revogacao = models.TextField(blank=True, verbose_name='Motivo da Revogacao')
    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historicos_digitais_emitidos',
        verbose_name='Emitido por',
    )
    emitido_em = models.DateTimeField(auto_now_add=True, verbose_name='Emitido em')
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Historico Escolar Digital'
        verbose_name_plural = 'Historicos Escolares Digitais'
        ordering = ['-emitido_em', '-id']
        indexes = [
            models.Index(fields=['numero_unico']),
            models.Index(fields=['chave_autenticacao']),
            models.Index(fields=['tipo_documento', 'status']),
            models.Index(fields=['historico', 'versao']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['historico', 'versao'],
                name='uniq_historico_digital_versao_por_historico',
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.numero_unico:
            self.numero_unico = self._gerar_numero_unico()
        if not self.chave_autenticacao:
            self.chave_autenticacao = self._gerar_chave_autenticacao()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_chave_autenticacao():
        return get_random_string(24, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ23456789')

    def _gerar_numero_unico(self):
        ano = timezone.now().year
        prefixo = f'HED-{ano}-'
        ultimo = (
            HistoricoEscolarDigital.objects
            .filter(numero_unico__startswith=prefixo)
            .order_by('-numero_unico')
            .first()
        )
        seq = 1
        if ultimo and ultimo.numero_unico:
            try:
                seq = int(ultimo.numero_unico.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = (
                    HistoricoEscolarDigital.objects
                    .filter(numero_unico__startswith=prefixo)
                    .count()
                    + 1
                )
        return f'{prefixo}{seq:06d}'

    def __str__(self):
        return f'{self.numero_unico} - {self.get_tipo_documento_display()}'


class HistoricoEscolarTecnico(models.Model):
    """
    Modelo complementar para historico escolar de cursos tecnicos do IDEP.
    Mantido em paralelo ao HistoricoEscolar legado para nao afetar componentes existentes.
    """

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='historicos_tecnicos')
    curso = models.ForeignKey(CursoTecnico, on_delete=models.PROTECT, related_name='historicos_tecnicos')
    instituicao = models.ForeignKey(
        InstituicaoEmissora,
        on_delete=models.PROTECT,
        related_name='historicos_tecnicos',
    )

    versao = models.CharField(max_length=10, default='1.05')
    ambiente = models.CharField(max_length=20, default='Produção')

    data_ingresso = models.DateField()
    forma_acesso = models.CharField(max_length=100, default='Processo Seletivo')

    data_emissao_historico = models.DateField()
    hora_emissao_historico = models.TimeField()

    carga_horaria_integralizada = models.PositiveIntegerField(default=0)
    carga_horaria_curso = models.PositiveIntegerField(default=1200)

    codigo_validacao = models.CharField(max_length=60, unique=True, blank=True)

    informacoes_adicionais = models.TextField(blank=True)

    data_conclusao_curso = models.DateField(null=True, blank=True)
    data_colacao_grau = models.DateField(null=True, blank=True)
    data_expedicao_diploma = models.DateField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historico Escolar Tecnico'
        verbose_name_plural = 'Historicos Escolares Tecnicos'
        ordering = ['-data_emissao_historico', '-id']
        indexes = [
            models.Index(fields=['codigo_validacao']),
            models.Index(fields=['aluno', 'curso']),
            models.Index(fields=['instituicao', 'data_emissao_historico']),
        ]

    def clean(self):
        # Restringe emissao ao contexto de educacao profissional tecnica.
        if self.curso_id and self.curso.tipo_curso != 'tecnico':
            raise ValidationError(
                {'curso': 'Este historico e exclusivo para cursos tecnicos.'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.codigo_validacao:
            ano = self.data_emissao_historico.year if self.data_emissao_historico else '2026'
            token = uuid.uuid4().hex[:8].upper()
            self.codigo_validacao = f'HE-IDEPRO-{ano}-{token}'
        super().save(*args, **kwargs)

    def __str__(self):
        aluno_nome = getattr(getattr(self.aluno, 'pessoa', None), 'nome_completo', None) or str(self.aluno)
        return f'{aluno_nome} - {self.curso.nome}'


class HistoricoEscolarTecnicoDocumento(models.Model):
    class StatusDocumento(models.TextChoices):
        RASCUNHO = "RASCUNHO", "Rascunho"
        EMITIDO = "EMITIDO", "Emitido"
        CANCELADO = "CANCELADO", "Cancelado"
        SUBSTITUIDO = "SUBSTITUIDO", "Substituido"

    class SituacaoFinal(models.TextChoices):
        APROVADO = "APROVADO", "Aprovado"
        REPROVADO = "REPROVADO", "Reprovado"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        TRANSFERIDO = "TRANSFERIDO", "Transferido"
        INDEFINIDA = "INDEFINIDA", "Indefinida"

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="UUID")
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="historicos_tecnicos_documentos",
        verbose_name="Aluno",
    )
    matricula = models.ForeignKey(
        "matriculas.Matricula",
        on_delete=models.PROTECT,
        related_name="historicos_tecnicos_documentos",
        verbose_name="Matricula",
    )
    curso = models.ForeignKey(
        "cursos.Curso",
        on_delete=models.PROTECT,
        related_name="historicos_tecnicos_documentos",
        verbose_name="Curso",
    )
    numero_registro = models.CharField(max_length=40, unique=True, verbose_name="Numero de Registro")
    livro = models.CharField(max_length=30, blank=True, default="", verbose_name="Livro")
    folha = models.CharField(max_length=30, blank=True, default="", verbose_name="Folha")
    pagina = models.CharField(max_length=30, blank=True, default="", verbose_name="Pagina")
    versao = models.PositiveIntegerField(default=1, verbose_name="Versao")
    status = models.CharField(
        max_length=20,
        choices=StatusDocumento.choices,
        default=StatusDocumento.RASCUNHO,
        verbose_name="Status",
    )
    hash_documento = models.CharField(max_length=64, verbose_name="Hash do Documento")
    codigo_validacao = models.CharField(max_length=32, unique=True, verbose_name="Codigo de Validacao")
    data_emissao = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora de Emissao")
    data_cancelamento = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora de Cancelamento")
    motivo_cancelamento = models.TextField(blank=True, default="", verbose_name="Motivo de Cancelamento")
    historico_substituido = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_substitutos",
        verbose_name="Historico Substituido",
    )
    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_tecnicos_emitidos",
        verbose_name="Emitido por",
    )
    observacoes = models.TextField(blank=True, default="", verbose_name="Observacoes Academicas")
    pdf_arquivo = models.FileField(
        upload_to="documentos/historicos_tecnicos/pdf/",
        null=True,
        blank=True,
        verbose_name="PDF",
    )
    qrcode_imagem = models.ImageField(
        upload_to="documentos/historicos_tecnicos/qrcode/",
        null=True,
        blank=True,
        verbose_name="Imagem QR Code",
    )
    carga_horaria_total = models.PositiveIntegerField(default=0, verbose_name="Carga Horaria Total")
    situacao_final = models.CharField(
        max_length=20,
        choices=SituacaoFinal.choices,
        default=SituacaoFinal.INDEFINIDA,
        verbose_name="Situacao Final",
    )
    data_conclusao = models.DateField(null=True, blank=True, verbose_name="Data de Conclusao")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        verbose_name = "Historico Escolar Tecnico (Documento)"
        verbose_name_plural = "Historicos Escolares Tecnicos (Documentos)"
        ordering = ["-criado_em", "-id"]
        indexes = [
            models.Index(fields=["uuid"]),
            models.Index(fields=["codigo_validacao"]),
            models.Index(fields=["aluno", "curso"]),
            models.Index(fields=["matricula", "status"]),
        ]

    def __str__(self):
        return f"{self.numero_registro} - {self.aluno}"


class HistoricoEscolarItem(models.Model):
    class ResultadoItem(models.TextChoices):
        APROVADO = "APROVADO", "Aprovado"
        REPROVADO = "REPROVADO", "Reprovado"
        CURSANDO = "CURSANDO", "Cursando"
        APROVEITADO = "APROVEITADO", "Aproveitado"
        DISPENSADO = "DISPENSADO", "Dispensado"

    historico = models.ForeignKey(
        HistoricoEscolarTecnicoDocumento,
        on_delete=models.CASCADE,
        related_name="itens",
        verbose_name="Historico",
    )
    componente_curricular = models.ForeignKey(
        "cursos.ComponenteCurricular",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historico_itens",
        verbose_name="Componente Curricular",
    )
    componente_nome = models.CharField(max_length=220, verbose_name="Nome do Componente")
    modulo_periodo = models.CharField(max_length=80, blank=True, default="", verbose_name="Modulo/Periodo/Serie")
    carga_horaria = models.PositiveIntegerField(default=0, verbose_name="Carga Horaria")
    nota = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Nota")
    frequencia = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Frequencia")
    resultado = models.CharField(
        max_length=20,
        choices=ResultadoItem.choices,
        default=ResultadoItem.CURSANDO,
        verbose_name="Resultado",
    )
    ordem_exibicao = models.PositiveIntegerField(default=1, verbose_name="Ordem de Exibicao")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Historico Escolar Item"
        verbose_name_plural = "Historico Escolar Itens"
        ordering = ["ordem_exibicao", "id"]
        indexes = [
            models.Index(fields=["historico", "ordem_exibicao"]),
            models.Index(fields=["resultado"]),
        ]

    def __str__(self):
        return f"{self.componente_nome} ({self.historico.numero_registro})"


class HistoricoEscolarEvento(models.Model):
    class TipoEvento(models.TextChoices):
        EMISSAO = "EMISSAO", "Emissao"
        REEMISSAO = "REEMISSAO", "Reemissao"
        CANCELAMENTO = "CANCELAMENTO", "Cancelamento"
        VISUALIZACAO = "VISUALIZACAO", "Visualizacao"
        VALIDACAO_PUBLICA = "VALIDACAO_PUBLICA", "Validacao Publica"

    historico = models.ForeignKey(
        HistoricoEscolarTecnicoDocumento,
        on_delete=models.CASCADE,
        related_name="eventos",
        verbose_name="Historico",
    )
    tipo_evento = models.CharField(max_length=20, choices=TipoEvento.choices, verbose_name="Tipo de Evento")
    descricao = models.TextField(blank=True, default="", verbose_name="Descricao")
    motivo = models.TextField(blank=True, default="", verbose_name="Motivo")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="eventos_historico_tecnico",
        verbose_name="Usuario",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")

    class Meta:
        verbose_name = "Historico Escolar Evento"
        verbose_name_plural = "Historico Escolar Eventos"
        ordering = ["-criado_em", "-id"]
        indexes = [models.Index(fields=["historico", "tipo_evento"]), models.Index(fields=["criado_em"])]

    def __str__(self):
        return f"{self.get_tipo_evento_display()} - {self.historico.numero_registro}"


class DocumentoValidacao(models.Model):
    historico = models.OneToOneField(
        HistoricoEscolarTecnicoDocumento,
        on_delete=models.CASCADE,
        related_name="validacao",
        verbose_name="Historico",
    )
    hash_documento = models.CharField(max_length=64, verbose_name="Hash")
    hash_resumido = models.CharField(max_length=16, verbose_name="Hash Resumido")
    url_validacao = models.CharField(max_length=500, verbose_name="URL de Validacao")
    valido = models.BooleanField(default=True, verbose_name="Valido")
    observacoes = models.TextField(blank=True, default="", verbose_name="Observacoes")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Documento Validacao"
        verbose_name_plural = "Documentos Validacao"
        indexes = [models.Index(fields=["hash_documento"]), models.Index(fields=["hash_resumido"])]

    def __str__(self):
        return f"Validacao - {self.historico.numero_registro}"


class AssinaturaDocumento(models.Model):
    historico = models.ForeignKey(
        HistoricoEscolarTecnicoDocumento,
        on_delete=models.CASCADE,
        related_name="assinaturas",
        verbose_name="Historico",
    )
    nome = models.CharField(max_length=150, verbose_name="Nome")
    cargo = models.CharField(max_length=150, verbose_name="Cargo")
    identificador = models.CharField(max_length=60, blank=True, default="", verbose_name="Identificador")
    assinatura_hash = models.CharField(max_length=64, blank=True, default="", verbose_name="Hash da Assinatura")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Assinatura de Documento"
        verbose_name_plural = "Assinaturas de Documento"
        ordering = ["id"]

    def __str__(self):
        return f"{self.nome} - {self.cargo}"


class ConfiguracaoHistorico(models.Model):
    nome_instituicao = models.CharField(max_length=200, default="IDEP-ETEC/RO", verbose_name="Nome da Instituicao")
    subtitulo = models.CharField(max_length=200, blank=True, default="", verbose_name="Subtitulo")
    livro_padrao = models.CharField(max_length=30, blank=True, default="1", verbose_name="Livro padrao")
    folha_padrao = models.CharField(max_length=30, blank=True, default="1", verbose_name="Folha padrao")
    pagina_padrao = models.CharField(max_length=30, blank=True, default="1", verbose_name="Pagina padrao")
    carga_horaria_minima_aprovacao = models.PositiveIntegerField(default=0, verbose_name="CH minima")
    nota_minima_aprovacao = models.DecimalField(max_digits=4, decimal_places=2, default=6.0, verbose_name="Nota minima")
    frequencia_minima_aprovacao = models.DecimalField(max_digits=5, decimal_places=2, default=75.0, verbose_name="Frequencia minima")
    assinatura_1_nome = models.CharField(max_length=150, blank=True, default="", verbose_name="Assinatura 1 Nome")
    assinatura_1_cargo = models.CharField(max_length=150, blank=True, default="", verbose_name="Assinatura 1 Cargo")
    assinatura_2_nome = models.CharField(max_length=150, blank=True, default="", verbose_name="Assinatura 2 Nome")
    assinatura_2_cargo = models.CharField(max_length=150, blank=True, default="", verbose_name="Assinatura 2 Cargo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracao de Historico"
        verbose_name_plural = "Configuracoes de Historico"
        ordering = ["-ativo", "-atualizado_em", "-id"]

    def __str__(self):
        return self.nome_instituicao
