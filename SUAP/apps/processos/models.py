"""UC05 â Abrir e Tramitar Processo/Protocolo"""

from django.conf import settings
from django.db import models


class Processo(models.Model):
    TIPO_CHOICES = (
        ('REQUERIMENTO',   'Requerimento'),
        ('RECURSO',        'Recurso'),
        ('TRANSFERENCIA',  'TransferÃªncia'),
        ('SOLICITACAO',    'SolicitaÃ§Ã£o Geral'),
        ('OUTROS',         'Outros'),
    )
    STATUS_CHOICES = (
        ('ABERTO',          'Aberto'),
        ('EM_TRAMITACAO',   'Em TramitaÃ§Ã£o'),
        ('CONCLUIDO',       'ConcluÃ­do'),
        ('ARQUIVADO',       'Arquivado'),
    )

    numero          = models.CharField(max_length=20, unique=True, editable=False, verbose_name='NÂº do Processo')
    tipo            = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    requerente      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processos_requeridos',
        verbose_name='Requerente',
    )
    assunto         = models.CharField(max_length=255, verbose_name='Assunto')
    descricao       = models.TextField(blank=True, verbose_name='DescriÃ§Ã£o')
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO', verbose_name='Status')
    data_abertura   = models.DateField(auto_now_add=True, verbose_name='Data de Abertura')
    data_conclusao  = models.DateField(null=True, blank=True, verbose_name='Data de ConclusÃ£o')

    class Meta:
        verbose_name = 'Processo'
        verbose_name_plural = 'Processos'
        ordering = ['-data_abertura']

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._gerar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_numero():
        from django.utils import timezone
        ano = timezone.now().year
        ultimo = (
            Processo.objects
            .filter(numero__startswith=f'PRO-{ano}-')
            .order_by('-numero')
            .first()
        )
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = Processo.objects.filter(numero__startswith=f'PRO-{ano}-').count() + 1
        return f'PRO-{ano}-{seq:04d}'

    def __str__(self):
        return f'{self.numero} â {self.assunto}'


class Tramitacao(models.Model):
    ACAO_CHOICES = (
        ('RECEBIDO',     'Recebido'),
        ('ENCAMINHADO',  'Encaminhado'),
        ('RESPONDIDO',   'Respondido'),
        ('ARQUIVADO',    'Arquivado'),
        ('DEVOLVIDO',    'Devolvido'),
    )

    processo        = models.ForeignKey(Processo, on_delete=models.CASCADE, related_name='tramitacoes')
    responsavel     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tramitacoes_realizadas',
        verbose_name='ResponsÃ¡vel',
    )
    setor_destino   = models.CharField(max_length=100, blank=True, verbose_name='Setor de Destino')
    acao            = models.CharField(max_length=15, choices=ACAO_CHOICES, verbose_name='AÃ§Ã£o')
    observacao      = models.TextField(blank=True, verbose_name='ObservaÃ§Ã£o')
    data            = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')

    class Meta:
        verbose_name = 'TramitaÃ§Ã£o'
        verbose_name_plural = 'TramitaÃ§Ãµes'
        ordering = ['-data']

    def __str__(self):
        return f'{self.processo.numero} â {self.get_acao_display()} ({self.data:%d/%m/%Y})'


class Solicitacao(models.Model):
    """Pré-protocolo: solicitação formal antes de abrir um Processo."""

    TIPO_CHOICES = (
        ('MATRICULA',     'Matrícula / Rematrícula'),
        ('TRANSFERENCIA', 'Transferência'),
        ('DOCUMENTO',     'Emissão de Documento'),
        ('RECURSO',       'Recurso'),
        ('OUTROS',        'Outros'),
    )
    STATUS_CHOICES = (
        ('ABERTA',      'Aberta'),
        ('EM_ANALISE',  'Em Análise'),
        ('ATENDIDA',    'Atendida'),
        ('CANCELADA',   'Cancelada'),
    )

    solicitante      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='solicitacoes',
        verbose_name='Solicitante',
    )
    tipo             = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo')
    descricao        = models.TextField(verbose_name='Descrição')
    status           = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ABERTA', verbose_name='Status')
    data_abertura    = models.DateField(auto_now_add=True, verbose_name='Data de Abertura')
    data_resolucao   = models.DateField(null=True, blank=True, verbose_name='Data de Resolução')
    processo         = models.ForeignKey(
        Processo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='solicitacoes',
        verbose_name='Processo Vinculado',
    )
    observacao       = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Solicitação'
        verbose_name_plural = 'Solicitações'
        ordering = ['-data_abertura']

    def __str__(self):
        return f'Solicitação [{self.get_tipo_display()}]  {self.solicitante} [{self.get_status_display()}]'
