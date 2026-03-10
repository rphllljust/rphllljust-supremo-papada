from django.contrib import admin

from .models import EmprestimoDocumento, EtapaFluxoArquivo, FluxoArquivo, GuardaDocumental, PlanoClassificacao, TermoEliminacao


class EmprestimoInline(admin.TabularInline):
    model = EmprestimoDocumento
    extra = 0
    readonly_fields = ("data_emprestimo",)


@admin.register(GuardaDocumental)
class GuardaDocumentalAdmin(admin.ModelAdmin):
    list_display = ("numero_registro", "tipo_documento", "descricao", "status", "numero_caixa", "data_arquivamento")
    list_filter = ("tipo_documento", "status")
    search_fields = ("numero_registro", "descricao", "numero_caixa")
    readonly_fields = ("numero_registro", "data_arquivamento")
    inlines = [EmprestimoInline]


@admin.register(EmprestimoDocumento)
class EmprestimoDocumentoAdmin(admin.ModelAdmin):
    list_display = ("guarda", "solicitante", "data_emprestimo", "data_devolucao", "devolvido")
    list_filter = ("devolvido",)
    readonly_fields = ("data_emprestimo",)


class EtapaFluxoArquivoInline(admin.TabularInline):
    model = EtapaFluxoArquivo
    extra = 0
    readonly_fields = ("data",)


class TermoEliminacaoInline(admin.StackedInline):
    model = TermoEliminacao
    extra = 0
    readonly_fields = ("numero", "data_termo")


@admin.register(FluxoArquivo)
class FluxoArquivoAdmin(admin.ModelAdmin):
    list_display = ("guarda", "etapa_atual", "concluido", "data_inicio")
    list_filter = ("etapa_atual", "concluido")
    search_fields = ("guarda__numero_registro", "guarda__descricao")
    readonly_fields = ("data_inicio",)
    inlines = [EtapaFluxoArquivoInline, TermoEliminacaoInline]


@admin.register(TermoEliminacao)
class TermoEliminacaoAdmin(admin.ModelAdmin):
    list_display = ("numero", "fluxo", "data_termo", "autorizado_por", "data_autorizacao")
    search_fields = ("numero", "fluxo__guarda__numero_registro")
    readonly_fields = ("numero", "data_termo")


@admin.register(PlanoClassificacao)
class PlanoClassificacaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao", "prazo_guarda_anos", "destinacao")
    list_filter = ("destinacao",)
    search_fields = ("codigo", "descricao")
