"""
Estágio (se aplicável)
Fluxo: Convenio → Estagio → TermoCompromisso → Acompanhamento → Encerramento
"""

from django.conf import settings
from django.db import models

from apps.matriculas.models import Matricula


class Convenio(models.Model):
    """Convênio firmado com empresa/instituição para oferta de vagas de estágio."""

    STATUS_CHOICES = (
        ('VIGENTE',    'Vigente'),
        ('VENCIDO',    'Vencido'),
        ('CANCELADO',  'Cancelado'),
    )

    empresa            = models.CharField(max_length=255, verbose_name='Empresa / Instituição')
    cnpj               = models.CharField(max_length=18, blank=True, verbose_name='CNPJ')
    responsavel_empresa = models.CharField(max_length=200, blank=True, verbose_name='Responsável na Empresa')
    email_empresa      = models.EmailField(blank=True, verbose_name='E-mail da Empresa')
    telefone_empresa   = models.CharField(max_length=20, blank=True, verbose_name='Telefone da Empresa')
    numero_convenio    = models.CharField(max_length=30, unique=True, editable=False, verbose_name='Nº do Convênio')
    data_assinatura    = models.DateField(verbose_name='Data de Assinatura')
    data_vencimento    = models.DateField(null=True, blank=True, verbose_name='Data de Vencimento')
    status             = models.CharField(max_length=15, choices=STATUS_CHOICES, default='VIGENTE', verbose_name='Status')
    objeto             = models.TextField(blank=True, verbose_name='Objeto do Convênio')
    responsavel_idep   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='convenios_estagio',
        verbose_name='Responsável IDEP',
    )

    class Meta:
        verbose_name = 'Convênio de Estágio'
        verbose_name_plural = 'Convênios de Estágio'
        ordering = ['-data_assinatura']

    def save(self, *args, **kwargs):
        if not self.numero_convenio:
            from django.utils import timezone
            ano = timezone.now().year
            ultimo = Convenio.objects.filter(numero_convenio__startswith=f'CON-{ano}-').order_by('-numero_convenio').first()
            seq = 1
            if ultimo:
                try:
                    seq = int(ultimo.numero_convenio.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = Convenio.objects.filter(numero_convenio__startswith=f'CON-{ano}-').count() + 1
            self.numero_convenio = f'CON-{ano}-{seq:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.numero_convenio} – {self.empresa} [{self.get_status_display()}]'


class Estagio(models.Model):
    """Registro de estágio de um aluno."""

    MODALIDADE_CHOICES = (
        ('OBRIGATORIO',     'Obrigatório'),
        ('NAO_OBRIGATORIO', 'Não Obrigatório'),
    )
    STATUS_CHOICES = (
        ('PREVISTO',    'Previsto'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO',   'Concluído'),
        ('CANCELADO',   'Cancelado'),
        ('INTERROMPIDO', 'Interrompido'),
    )

    matricula          = models.ForeignKey(
        Matricula, on_delete=models.CASCADE,
        related_name='estagios',
        verbose_name='Matrícula',
    )
    convenio           = models.ForeignKey(
        Convenio, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='estagios',
        verbose_name='Convênio',
    )
    modalidade         = models.CharField(max_length=20, choices=MODALIDADE_CHOICES, default='OBRIGATORIO', verbose_name='Modalidade')
    empresa            = models.CharField(max_length=255, verbose_name='Empresa / Local de Estágio')
    supervisor_empresa = models.CharField(max_length=200, blank=True, verbose_name='Supervisor na Empresa')
    orientador_idep    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='estagios_orientados',
        limit_choices_to={'tipo': 'PROFESSOR'},
        verbose_name='Orientador IDEP',
    )
    carga_horaria_total = models.PositiveIntegerField(default=0, verbose_name='Carga Horária Total (h)')
    carga_horaria_semanal = models.PositiveIntegerField(default=0, verbose_name='Carga Horária Semanal (h)')
    data_inicio        = models.DateField(verbose_name='Data de Início')
    data_fim_prevista  = models.DateField(null=True, blank=True, verbose_name='Data Fim Prevista')
    data_fim_real      = models.DateField(null=True, blank=True, verbose_name='Data Fim Real')
    status             = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PREVISTO', verbose_name='Status')
    bolsa_mensal       = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Bolsa Mensal (R$)')
    seguro_numero      = models.CharField(max_length=50, blank=True, verbose_name='Nº Apólice do Seguro')
    observacao         = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Estágio'
        verbose_name_plural = 'Estágios'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'Estágio – {self.matricula.aluno} em {self.empresa} [{self.get_status_display()}]'


class TermoCompromisso(models.Model):
    """Termo de Compromisso de Estágio assinado pelas partes."""

    STATUS_CHOICES = (
        ('PENDENTE',   'Pendente de Assinatura'),
        ('ASSINADO',   'Assinado'),
        ('ADITADO',    'Aditado'),
        ('ENCERRADO',  'Encerrado'),
    )

    estagio            = models.ForeignKey(
        Estagio, on_delete=models.CASCADE,
        related_name='termos',
        verbose_name='Estágio',
    )
    numero_termo       = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº do Termo')
    data_assinatura    = models.DateField(null=True, blank=True, verbose_name='Data de Assinatura')
    status             = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    assinado_aluno     = models.BooleanField(default=False, verbose_name='Assinado pelo Aluno')
    assinado_empresa   = models.BooleanField(default=False, verbose_name='Assinado pela Empresa')
    assinado_idep      = models.BooleanField(default=False, verbose_name='Assinado pelo IDEP')
    observacao         = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Termo de Compromisso'
        verbose_name_plural = 'Termos de Compromisso'
        ordering = ['-data_assinatura']

    def save(self, *args, **kwargs):
        if not self.numero_termo:
            from django.utils import timezone
            ano = timezone.now().year
            ultimo = TermoCompromisso.objects.filter(numero_termo__startswith=f'TCE-{ano}-').order_by('-numero_termo').first()
            seq = 1
            if ultimo:
                try:
                    seq = int(ultimo.numero_termo.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = TermoCompromisso.objects.filter(numero_termo__startswith=f'TCE-{ano}-').count() + 1
            self.numero_termo = f'TCE-{ano}-{seq:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.numero_termo} – {self.estagio} [{self.get_status_display()}]'


class AcompanhamentoEstagio(models.Model):
    """Registro periódico de acompanhamento do estágio."""

    TIPO_CHOICES = (
        ('VISITA',        'Visita ao Local'),
        ('RELATORIO',     'Relatório do Estagiário'),
        ('AVALIACAO',     'Avaliação pelo Supervisor'),
        ('ORIENTACAO',    'Orientação pelo IDEP'),
    )

    estagio       = models.ForeignKey(
        Estagio, on_delete=models.CASCADE,
        related_name='acompanhamentos',
        verbose_name='Estágio',
    )
    tipo          = models.CharField(max_length=15, choices=TIPO_CHOICES, verbose_name='Tipo de Acompanhamento')
    data          = models.DateField(verbose_name='Data')
    descricao     = models.TextField(verbose_name='Descrição / Observações')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='acompanhamentos_estagio',
        verbose_name='Registrado por',
    )

    class Meta:
        verbose_name = 'Acompanhamento de Estágio'
        verbose_name_plural = 'Acompanhamentos de Estágio'
        ordering = ['-data']

    def __str__(self):
        return f'{self.get_tipo_display()} – {self.estagio} ({self.data:%d/%m/%Y})'
