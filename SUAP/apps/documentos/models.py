"""
Domínio de Documentos – Class Diagram
Hierarquia com DocumentoBase (abstrato) → Declaracao, HistoricoEscolar,
GuiaTransferencia, AtaOficioMemorando
"""

from django.conf import settings
from django.db import models


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

    class Meta(DocumentoBase.Meta):
        verbose_name = 'Ata / Ofício / Memorando'
        verbose_name_plural = 'Atas / Ofícios / Memorandos'

    @classmethod
    def _prefixo(cls):
        return 'ATA'
