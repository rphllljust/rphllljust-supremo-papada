from django.contrib import admin

from .models import ContratoFinanceiro, HistoricoFinanceiro, Mensalidade, PlanoPagamento


@admin.register(PlanoPagamento)
class PlanoPagamentoAdmin(admin.ModelAdmin):
    list_display = ['curso', 'valor_total', 'quantidade_parcelas', 'periodicidade', 'permite_bolsa', 'ativo']
    list_filter = ['periodicidade', 'permite_bolsa', 'ativo']
    search_fields = ['curso__nome']


@admin.register(ContratoFinanceiro)
class ContratoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['matricula', 'status', 'valor_total', 'tipo_bolsa', 'percentual_bolsa', 'parcelas_pagas', 'parcelas_vencidas']
    list_filter = ['status', 'tipo_bolsa']
    search_fields = ['matricula__numero_matricula', 'matricula__aluno__cpf']
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(Mensalidade)
class MensalidadeAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'numero_parcela', 'data_vencimento', 'valor_original', 'status', 'data_pagamento']
    list_filter = ['status']
    search_fields = ['contrato__matricula__numero_matricula']
    readonly_fields = ['criado_em', 'atualizado_em']


@admin.register(HistoricoFinanceiro)
class HistoricoFinanceiroAdmin(admin.ModelAdmin):
    list_display = ['contrato', 'tipo_evento', 'valor', 'criado_em']
    list_filter = ['tipo_evento']
    readonly_fields = ['criado_em']
