"""
Domínio de Documentos – Class Diagram
Hierarquia com DocumentoBase (abstrato) → Declaracao, HistoricoEscolar,
GuiaTransferencia, AtaOficioMemorando
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


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
