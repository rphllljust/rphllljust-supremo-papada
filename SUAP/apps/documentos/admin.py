from django.contrib import admin

from .models import AtaOficioMemorando, Declaracao, GuiaTransferencia, HistoricoEscolar


@admin.register(Declaracao)
class DeclaracaoAdmin(admin.ModelAdmin):
    list_display = ("numero_protocolo", "tipo", "assunto", "matricula", "emitido_por", "data_emissao")
    list_filter = ("tipo",)
    search_fields = ("numero_protocolo", "assunto")
    readonly_fields = ("numero_protocolo", "data_emissao")


@admin.register(HistoricoEscolar)
class HistoricoEscolarAdmin(admin.ModelAdmin):
    list_display = ("numero_protocolo", "tipo", "assunto", "matricula", "emitido_por", "data_emissao")
    list_filter = ("tipo",)
    search_fields = ("numero_protocolo", "assunto")
    readonly_fields = ("numero_protocolo", "data_emissao")


@admin.register(GuiaTransferencia)
class GuiaTransferenciaAdmin(admin.ModelAdmin):
    list_display = ("numero_protocolo", "assunto", "escola_destino", "matricula", "emitido_por", "data_emissao")
    search_fields = ("numero_protocolo", "assunto", "escola_destino")
    readonly_fields = ("numero_protocolo", "data_emissao")


@admin.register(AtaOficioMemorando)
class AtaOficioMemorandoAdmin(admin.ModelAdmin):
    list_display = ("numero_protocolo", "tipo", "assunto", "destinatario", "emitido_por", "data_emissao")
    list_filter = ("tipo",)
    search_fields = ("numero_protocolo", "assunto", "destinatario")
    readonly_fields = ("numero_protocolo", "data_emissao")
