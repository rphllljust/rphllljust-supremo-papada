from django.contrib import admin

from .models import Processo, Tramitacao


class TramitacaoInline(admin.TabularInline):
    model = Tramitacao
    extra = 0
    readonly_fields = ("data",)


@admin.register(Processo)
class ProcessoAdmin(admin.ModelAdmin):
    list_display = ("numero", "tipo", "assunto", "status", "requerente", "data_abertura")
    list_filter = ("tipo", "status")
    search_fields = ("numero", "assunto", "requerente__username")
    readonly_fields = ("numero", "data_abertura")
    inlines = [TramitacaoInline]


@admin.register(Tramitacao)
class TramitacaoAdmin(admin.ModelAdmin):
    list_display = ("processo", "acao", "setor_destino", "responsavel", "data")
    list_filter = ("acao",)
    readonly_fields = ("data",)


from .models import Solicitacao

@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ("solicitante", "tipo", "status", "data_abertura", "data_resolucao", "processo")
    list_filter = ("tipo", "status")
    search_fields = ("solicitante__username", "descricao")
