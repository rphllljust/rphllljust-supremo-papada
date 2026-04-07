from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AssinaturaDocumento,
    AtaOficioMemorando,
    ConfiguracaoHistorico,
    Declaracao,
    DocumentoValidacao,
    GuiaTransferencia,
    HistoricoEscolar,
    HistoricoEscolarEvento,
    HistoricoEscolarItem,
    HistoricoEscolarTecnico,
    HistoricoEscolarTecnicoDocumento,
    HistoricoEscolarDigital,
)


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


@admin.register(HistoricoEscolarDigital)
class HistoricoEscolarDigitalAdmin(admin.ModelAdmin):
    list_display = (
        "numero_unico",
        "historico",
        "tipo_documento",
        "versao",
        "status",
        "validacao_xsd_ok",
        "assinado_digitalmente",
        "revogado",
        "emitido_em",
    )
    list_filter = ("tipo_documento", "status", "validacao_xsd_ok", "assinado_digitalmente", "revogado")
    search_fields = ("numero_unico", "chave_autenticacao", "historico__numero_protocolo")
    readonly_fields = (
        "numero_unico",
        "chave_autenticacao",
        "hash_documento",
        "emitido_em",
        "atualizado_em",
    )


@admin.register(HistoricoEscolarTecnico)
class HistoricoEscolarTecnicoAdmin(admin.ModelAdmin):
    list_display = (
        "aluno",
        "curso",
        "codigo_validacao",
        "data_emissao_historico",
        "acoes_documentos",
        "instituicao",
        "versao",
        "ambiente",
    )
    list_filter = ("ambiente", "curso__tipo_curso", "instituicao")
    search_fields = ("codigo_validacao", "aluno__pessoa__nome_completo", "curso__nome")
    readonly_fields = ("codigo_validacao", "links_publicos", "criado_em", "atualizado_em")

    def acoes_documentos(self, obj):
        url_xml = reverse("historico_digital:exportar_historico_xml", args=[obj.pk])
        url_pdf = reverse("historico_digital:exportar_historico_pdf", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank">XML</a>&nbsp;'
            '<a class="button" href="{}" target="_blank">PDF</a>',
            url_xml,
            url_pdf,
        )

    acoes_documentos.short_description = "Documentos"

    def links_publicos(self, obj):
        if not obj.pk:
            return "Salve o registro primeiro."
        url_validacao = reverse("historico_digital:validar_historico_publico", args=[obj.codigo_validacao])
        url_consulta = reverse("historico_digital:consulta_publica_historico")
        return format_html(
            'Consulta publica: <a href="{}" target="_blank">{}</a><br>'
            'Validacao direta: <a href="{}" target="_blank">{}</a>',
            url_consulta,
            url_consulta,
            url_validacao,
            url_validacao,
        )

    links_publicos.short_description = "Links publicos"


@admin.register(HistoricoEscolarTecnicoDocumento)
class HistoricoEscolarTecnicoDocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_registro",
        "uuid",
        "aluno",
        "matricula",
        "curso",
        "versao",
        "status",
        "codigo_validacao",
        "data_emissao",
    )
    list_filter = ("status", "curso", "versao")
    search_fields = ("numero_registro", "codigo_validacao", "aluno__username", "aluno__cpf", "aluno__pessoa__nome_completo")
    readonly_fields = ("uuid", "hash_documento", "codigo_validacao", "data_emissao", "criado_em", "atualizado_em")


@admin.register(HistoricoEscolarItem)
class HistoricoEscolarItemAdmin(admin.ModelAdmin):
    list_display = ("historico", "ordem_exibicao", "componente_nome", "carga_horaria", "nota", "frequencia", "resultado")
    list_filter = ("resultado",)
    search_fields = ("historico__numero_registro", "componente_nome")


@admin.register(HistoricoEscolarEvento)
class HistoricoEscolarEventoAdmin(admin.ModelAdmin):
    list_display = ("historico", "tipo_evento", "usuario", "criado_em")
    list_filter = ("tipo_evento",)
    search_fields = ("historico__numero_registro", "descricao", "motivo")


@admin.register(DocumentoValidacao)
class DocumentoValidacaoAdmin(admin.ModelAdmin):
    list_display = ("historico", "hash_resumido", "valido", "atualizado_em")
    list_filter = ("valido",)
    search_fields = ("historico__numero_registro", "hash_documento", "hash_resumido")


@admin.register(AssinaturaDocumento)
class AssinaturaDocumentoAdmin(admin.ModelAdmin):
    list_display = ("historico", "nome", "cargo", "identificador", "criado_em")
    search_fields = ("historico__numero_registro", "nome", "cargo")


@admin.register(ConfiguracaoHistorico)
class ConfiguracaoHistoricoAdmin(admin.ModelAdmin):
    list_display = ("nome_instituicao", "livro_padrao", "folha_padrao", "pagina_padrao", "ativo", "atualizado_em")
    list_filter = ("ativo",)
