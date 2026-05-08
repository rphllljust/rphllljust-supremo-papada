from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.usuarios.models import PerfilUsuario


class PlanoPagamento(models.Model):
    """Plano de pagamento/politica financeira por curso."""

    PERIODICIDADE_CHOICES = (
        ('MENSAL', 'Mensal'),
        ('TRIMESTRAL', 'Trimestral'),
        ('SEMESTRAL', 'Semestral'),
        ('ANUAL', 'Anual'),
        ('UNICA', 'Parcela Unica'),
    )

    curso = models.OneToOneField(Curso, on_delete=models.CASCADE, related_name='plano_pagamento')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Total')
    valor_parcela = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor da Parcela')
    quantidade_parcelas = models.PositiveIntegerField(default=12, verbose_name='Quantidade de Parcelas')
    periodicidade = models.CharField(max_length=15, choices=PERIODICIDADE_CHOICES, default='MENSAL', verbose_name='Periodicidade')
    permite_bolsa = models.BooleanField(default=True, verbose_name='Permite Bolsa')
    percentual_bolsa_maximo = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, verbose_name='Percentual Maximo de Bolsa (%)')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plano de Pagamento'
        verbose_name_plural = 'Planos de Pagamento'
        ordering = ['curso__nome']

    def clean(self):
        errors = {}
        if self.valor_total is not None and self.valor_total <= 0:
            errors['valor_total'] = 'O valor total deve ser maior que zero.'
        if self.valor_parcela is not None and self.valor_parcela <= 0:
            errors['valor_parcela'] = 'O valor da parcela deve ser maior que zero.'
        if self.quantidade_parcelas <= 0:
            errors['quantidade_parcelas'] = 'A quantidade de parcelas deve ser maior que zero.'
        if self.percentual_bolsa_maximo is not None and (self.percentual_bolsa_maximo < 0 or self.percentual_bolsa_maximo > 100):
            errors['percentual_bolsa_maximo'] = 'O percentual de bolsa deve estar entre 0 e 100%.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Plano - {self.curso.nome} ({self.quantidade_parcelas}x R$ {self.valor_parcela})'


class ContratoFinanceiro(models.Model):
    """Contrato financeiro do aluno vinculado a uma matrícula."""

    STATUS_CHOICES = (
        ('ATIVO', 'Ativo'),
        ('QUITADO', 'Quitado'),
        ('INADIMPLENTE', 'Inadimplente'),
        ('CANCELADO', 'Cancelado'),
    )

    TIPO_BOLSA_CHOICES = (
        ('SEM_BOLSA', 'Sem Bolsa'),
        ('SOCIAL', 'Bolsa Social'),
        ('MERITO', 'Bolsa Merito'),
        ('FUNCIONARIO', 'Bolsa Funcionario'),
        ('CONVENIO', 'Bolsa Convenio'),
        ('OUTRA', 'Outra'),
    )

    matricula = models.OneToOneField(Matricula, on_delete=models.CASCADE, related_name='contrato_financeiro')
    plano = models.ForeignKey(PlanoPagamento, on_delete=models.PROTECT, related_name='contratos')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVO', verbose_name='Status')
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Total')
    valor_original = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Original (sem descontos)')
    quantidade_parcelas = models.PositiveIntegerField(verbose_name='Quantidade de Parcelas')
    tipo_bolsa = models.CharField(max_length=15, choices=TIPO_BOLSA_CHOICES, default='SEM_BOLSA', verbose_name='Tipo de Bolsa')
    percentual_bolsa = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Percentual de Bolsa (%)')
    observacao = models.TextField(blank=True, verbose_name='Observacao')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contrato Financeiro'
        verbose_name_plural = 'Contratos Financeiros'
        ordering = ['-criado_em']

    def clean(self):
        errors = {}
        if self.percentual_bolsa > 0 and self.tipo_bolsa == 'SEM_BOLSA':
            errors['tipo_bolsa'] = 'Informe o tipo de bolsa quando houver percentual de desconto.'
        if self.percentual_bolsa > (self.plano.percentual_bolsa_maximo if self.plano_id else 100):
            errors['percentual_bolsa'] = f'Percentual de bolsa excede o maximo permitido ({self.plano.percentual_bolsa_maximo}%).'
        if self.valor_total is not None and self.valor_total <= 0:
            errors['valor_total'] = 'O valor total deve ser maior que zero.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def valor_desconto(self):
        return round(self.valor_original * (self.percentual_bolsa / Decimal('100')), 2)

    @property
    def valor_parcela(self):
        if self.quantidade_parcelas > 0:
            return round(self.valor_total / self.quantidade_parcelas, 2)
        return Decimal('0')

    @property
    def parcelas_vencidas(self):
        return self.parcelas.filter(data_vencimento__lt=timezone.now().date(), status='PENDENTE').count()

    @property
    def parcelas_pagas(self):
        return self.parcelas.filter(status='PAGA').count()

    @property
    def esta_inadimplente(self):
        return self.parcelas_vencidas > 0

    def atualizar_status(self):
        if self.parcelas.filter(status='PENDENTE').count() == 0:
            self.status = 'QUITADO'
        elif self.parcelas_vencidas > 0:
            self.status = 'INADIMPLENTE'
        else:
            self.status = 'ATIVO'
        self.save(update_fields=['status'])

    def __str__(self):
        return f'Contrato {self.matricula.numero_matricula} - R$ {self.valor_total}'


class Mensalidade(models.Model):
    """Parcela/mensalidade gerada a partir do contrato financeiro."""

    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente'),
        ('PAGA', 'Paga'),
        ('ATRASADA', 'Atrasada'),
        ('CANCELADA', 'Cancelada'),
        ('ISENTA', 'Isenta'),
    )

    contrato = models.ForeignKey(ContratoFinanceiro, on_delete=models.CASCADE, related_name='parcelas')
    numero_parcela = models.PositiveIntegerField(verbose_name='Numero da Parcela')
    data_vencimento = models.DateField(verbose_name='Data de Vencimento')
    valor_original = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Valor Original')
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Valor Pago')
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Desconto')
    multa = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Multa')
    juros = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Juros')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    data_pagamento = models.DateField(null=True, blank=True, verbose_name='Data de Pagamento')
    forma_pagamento = models.CharField(max_length=50, blank=True, verbose_name='Forma de Pagamento')
    numero_boleto = models.CharField(max_length=50, blank=True, verbose_name='Numero do Boleto')
    linha_digitavel = models.CharField(max_length=60, blank=True, verbose_name='Linha Digitavel')
    observacao = models.TextField(blank=True, verbose_name='Observacao')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mensalidade'
        verbose_name_plural = 'Mensalidades'
        ordering = ['contrato', 'numero_parcela']
        unique_together = ('contrato', 'numero_parcela')

    def clean(self):
        errors = {}
        if self.valor_original is not None and self.valor_original <= 0:
            errors['valor_original'] = 'O valor original deve ser maior que zero.'
        if self.valor_pago is not None and self.valor_pago < 0:
            errors['valor_pago'] = 'O valor pago nao pode ser negativo.'
        if self.status == 'PAGA' and not self.data_pagamento:
            errors['data_pagamento'] = 'Informe a data de pagamento.'
        if self.status == 'PAGA' and not self.valor_pago:
            errors['valor_pago'] = 'Informe o valor pago.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Atualiza status para ATRASADA se vencida
        if self.status == 'PENDENTE' and self.data_vencimento < timezone.now().date():
            self.status = 'ATRASADA'
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def valor_total(self):
        return self.valor_original - self.desconto + self.multa + self.juros

    def registrar_pagamento(self, valor_pago, data_pagamento, forma_pagamento='', numero_boleto=''):
        self.valor_pago = valor_pago
        self.data_pagamento = data_pagamento
        self.forma_pagamento = forma_pagamento
        self.numero_boleto = numero_boleto
        self.status = 'PAGA'
        self.save()
        self.contrato.atualizar_status()

    def cancelar(self):
        self.status = 'CANCELADA'
        self.save()

    def __str__(self):
        return f'Parcela {self.numero_parcela}/{self.contrato.quantidade_parcelas} - {self.contrato.matricula.numero_matricula}'


class HistoricoFinanceiro(models.Model):
    """Historico de eventos financeiros do contrato."""

    TIPO_EVENTO_CHOICES = (
        ('CRIACAO', 'Criacao do Contrato'),
        ('PAGAMENTO', 'Pagamento'),
        ('CANCELAMENTO', 'Cancelamento'),
        ('REEMISSAO_BOLETO', 'Reemissao de Boleto'),
        ('ALTERACAO_BOLSA', 'Alteracao de Bolsa'),
        ('NEGATIVACAO', 'Negativacao'),
        ('ACORDO', 'Acordo'),
    )

    contrato = models.ForeignKey(ContratoFinanceiro, on_delete=models.CASCADE, related_name='historicos')
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES, verbose_name='Tipo de Evento')
    descricao = models.TextField(verbose_name='Descricao')
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='Valor')
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='eventos_financeiros',
        verbose_name='Usuario',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historico Financeiro'
        verbose_name_plural = 'Historicos Financeiros'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_tipo_evento_display()} - {self.contrato}'
