"""UC06 – Arquivar e Gerir Guarda Documental"""

from django.conf import settings
from django.db import models




class PlanoClassificacao(models.Model):
    """
    Plano de Classificacao Documental - define codigo, prazo de guarda
    e destinacao final de cada tipo de documento.
    """

    DESTINACAO_CHOICES = (
        ('ELIMINACAO',        'Eliminacao'),
        ('GUARDA_PERMANENTE', 'Guarda Permanente'),
        ('TRANSFERENCIA',     'Transferencia para Arquivo Central'),
    )

    codigo            = models.CharField(max_length=20, unique=True, verbose_name='Codigo')
    descricao         = models.CharField(max_length=255, verbose_name='Descricao')
    prazo_guarda_anos = models.PositiveIntegerField(verbose_name='Prazo de Guarda (anos)')
    destinacao        = models.CharField(max_length=20, choices=DESTINACAO_CHOICES, verbose_name='Destinacao Final')
    observacao        = models.TextField(blank=True, verbose_name='Observacao')

    class Meta:
        verbose_name = 'Plano de Classificacao'
        verbose_name_plural = 'Planos de Classificacao'
        ordering = ['codigo']

    def __str__(self):
        return f'{self.codigo} - {self.descricao} ({self.prazo_guarda_anos} anos)'

class GuardaDocumental(models.Model):
    TIPO_CHOICES = (
        ('PASTA_ALUNO',  'Pasta do Aluno'),
        ('PROCESSO',     'Processo Administrativo'),
        ('CONTRATO',     'Contrato'),
        ('ATA',          'Ata'),
        ('DECLARACAO',   'Declaração'),
        ('HISTORICO',    'Histórico Escolar'),
        ('OUTROS',       'Outros'),
    )
    STATUS_CHOICES = (
        ('ATIVO',       'Ativo'),
        ('EMPRESTADO',  'Emprestado'),
        ('ELIMINADO',   'Eliminado'),
    )

    numero_registro          = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº de Registro')
    tipo_documento           = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name='Tipo de Documento')
    descricao                = models.CharField(max_length=255, verbose_name='Descrição')
    numero_caixa             = models.CharField(max_length=50, blank=True, verbose_name='Nº da Caixa')
    localizacao              = models.CharField(max_length=100, blank=True, verbose_name='Localização (Prateleira/Sala)')
    data_arquivamento        = models.DateField(auto_now_add=True, verbose_name='Data de Arquivamento')
    data_eliminacao_prevista = models.DateField(null=True, blank=True, verbose_name='Data de Eliminação Prevista')
    status                   = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVO', verbose_name='Status')
    plano_classificacao      = models.ForeignKey(
        PlanoClassificacao,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='guardas',
        verbose_name='Plano de Classificacao',
    )
    responsavel              = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='guardas_documentais',
        verbose_name='Responsável pelo Arquivamento',
    )

    # Vínculos opcionais
    matricula = models.ForeignKey(
        'matriculas.Matricula',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='guardas_documentais',
        verbose_name='Matrícula Vinculada',
    )
    processo = models.ForeignKey(
        'processos.Processo',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='guardas_documentais',
        verbose_name='Processo Vinculado',
    )

    class Meta:
        verbose_name = 'Guarda Documental'
        verbose_name_plural = 'Guarda Documental'
        ordering = ['-data_arquivamento']

    def save(self, *args, **kwargs):
        if not self.numero_registro:
            self.numero_registro = self._gerar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_numero():
        from django.utils import timezone
        ano = timezone.now().year
        ultimo = (
            GuardaDocumental.objects
            .filter(numero_registro__startswith=f'ARQ-{ano}-')
            .order_by('-numero_registro')
            .first()
        )
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero_registro.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = GuardaDocumental.objects.filter(
                    numero_registro__startswith=f'ARQ-{ano}-'
                ).count() + 1
        return f'ARQ-{ano}-{seq:04d}'

    def __str__(self):
        return f'{self.numero_registro} – {self.get_tipo_documento_display()} – {self.descricao}'


class EmprestimoDocumento(models.Model):
    """Controle de empréstimo de documentos arquivados."""

    guarda          = models.ForeignKey(GuardaDocumental, on_delete=models.CASCADE, related_name='emprestimos')
    solicitante     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='emprestimos_documentos',
        verbose_name='Solicitante',
    )
    data_emprestimo = models.DateField(auto_now_add=True, verbose_name='Data do Empréstimo')
    data_devolucao  = models.DateField(null=True, blank=True, verbose_name='Data de Devolução')
    devolvido       = models.BooleanField(default=False, verbose_name='Devolvido')
    observacao      = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Empréstimo de Documento'
        verbose_name_plural = 'Empréstimos de Documentos'
        ordering = ['-data_emprestimo']

    def __str__(self):
        return f'Empréstimo – {self.guarda} ({self.data_emprestimo:%d/%m/%Y})'


# ── P04 – Fluxo de Arquivo Escolar e Prazos ──────────────────────────────────

class FluxoArquivo(models.Model):
    """
    P04 – Ciclo de vida documental: Classificar → Indexar → Prazo → Eliminar.
    Swimlanes: Secretaria | Sistema
    """

    ETAPA_CHOICES = (
        ('CLASSIFICADO',   'Classificar Documento'),
        ('INDEXADO',       'Indexar / Localizar'),
        ('PRAZO_APLICADO', 'Aplicar Prazo de Guarda'),
        ('ELIMINADO',      'Eliminar + Termo'),
    )

    ATOR_ETAPA = {
        'CLASSIFICADO':   'secretaria',
        'INDEXADO':       'secretaria',
        'PRAZO_APLICADO': 'sistema',
        'ELIMINADO':      'secretaria',
    }

    ORDEM_ETAPAS = [e[0] for e in ETAPA_CHOICES]

    guarda      = models.ForeignKey(
        GuardaDocumental,
        on_delete=models.CASCADE,
        related_name='fluxos_arquivo',
        verbose_name='Guarda Documental',
    )
    etapa_atual = models.CharField(
        max_length=20,
        choices=ETAPA_CHOICES,
        default='CLASSIFICADO',
        verbose_name='Etapa Atual',
    )
    data_inicio = models.DateField(auto_now_add=True, verbose_name='Data de Início')
    concluido   = models.BooleanField(default=False, verbose_name='Concluído')
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Fluxo de Arquivo'
        verbose_name_plural = 'Fluxos de Arquivo'
        ordering = ['-data_inicio']

    def get_indice_etapa(self):
        try:
            return self.ORDEM_ETAPAS.index(self.etapa_atual)
        except ValueError:
            return 0

    def get_proxima_etapa(self):
        idx = self.get_indice_etapa()
        if idx < len(self.ORDEM_ETAPAS) - 1:
            return self.ORDEM_ETAPAS[idx + 1]
        return None

    def avancar(self, proxima_etapa=None):
        if proxima_etapa:
            self.etapa_atual = proxima_etapa
        else:
            prox = self.get_proxima_etapa()
            if prox:
                self.etapa_atual = prox
        if self.etapa_atual == 'ELIMINADO':
            self.concluido = True
        self.save()

    def etapas_info(self):
        idx_atual = self.get_indice_etapa()
        resultado = []
        for i, (codigo, label) in enumerate(self.ETAPA_CHOICES):
            resultado.append({
                'codigo': codigo,
                'label': label,
                'ator': self.ATOR_ETAPA.get(codigo, 'secretaria'),
                'concluida': i < idx_atual,
                'atual': i == idx_atual,
                'futura': i > idx_atual,
            })
        return resultado

    def __str__(self):
        return f'P04 – {self.guarda.numero_registro} [{self.get_etapa_atual_display()}]'


class EtapaFluxoArquivo(models.Model):
    """Log de auditoria das transições do P04."""

    fluxo       = models.ForeignKey(FluxoArquivo, on_delete=models.CASCADE, related_name='log_etapas')
    etapa       = models.CharField(max_length=20, choices=FluxoArquivo.ETAPA_CHOICES, verbose_name='Etapa')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etapas_fluxo_arquivo',
        verbose_name='Responsável',
    )
    data        = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    observacao  = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Etapa do Fluxo de Arquivo'
        verbose_name_plural = 'Etapas do Fluxo de Arquivo'
        ordering = ['data']

    def __str__(self):
        return f'{self.fluxo} → {self.etapa} ({self.data:%d/%m/%Y %H:%M})'


class TermoEliminacao(models.Model):
    """P04 – Termo formal gerado na etapa de Eliminação de documento."""

    fluxo            = models.OneToOneField(
        FluxoArquivo,
        on_delete=models.CASCADE,
        related_name='termo_eliminacao',
        verbose_name='Fluxo de Arquivo',
    )
    numero           = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº do Termo')
    data_termo       = models.DateField(auto_now_add=True, verbose_name='Data do Termo')
    justificativa    = models.TextField(verbose_name='Justificativa de Eliminação')
    autorizado_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='termos_eliminacao',
        verbose_name='Autorizado por',
    )
    data_autorizacao = models.DateField(null=True, blank=True, verbose_name='Data de Autorização')
    observacao       = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Termo de Eliminação'
        verbose_name_plural = 'Termos de Eliminação'
        ordering = ['-data_termo']

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = self._gerar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_numero():
        from django.utils import timezone
        ano = timezone.now().year
        ultimo = (
            TermoEliminacao.objects
            .filter(numero__startswith=f'TER-{ano}-')
            .order_by('-numero')
            .first()
        )
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = TermoEliminacao.objects.filter(
                    numero__startswith=f'TER-{ano}-'
                ).count() + 1
        return f'TER-{ano}-{seq:04d}'

    def __str__(self):
        return f'{self.numero} – {self.fluxo.guarda.numero_registro} ({self.data_termo:%d/%m/%Y})'
