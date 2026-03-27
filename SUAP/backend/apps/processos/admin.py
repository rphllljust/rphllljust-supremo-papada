from django.contrib import admin

from .models import HipoteseLegal, Processo, Solicitacao, Tramitacao


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

@admin.register(Solicitacao)
class SolicitacaoAdmin(admin.ModelAdmin):
    list_display = ("solicitante", "tipo", "status", "data_abertura", "data_resolucao", "processo")
    list_filter = ("tipo", "status")
    search_fields = ("solicitante__username", "descricao")


@admin.register(HipoteseLegal)
class HipoteseLegalAdmin(admin.ModelAdmin):
    list_display = ("descricao", "base_legal", "nivel_acesso", "ativo", "data_atualizacao")
    list_filter = ("nivel_acesso", "ativo")
    search_fields = ("descricao", "base_legal")
