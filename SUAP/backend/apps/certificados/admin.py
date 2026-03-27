from django.contrib import admin

from .models import (
    AssinaturaCertificado,
    CertificadoEmitido,
    ConfiguracaoVisualCertificado,
    HistoricoEmissaoCertificado,
    ModeloCertificado,
)


@admin.register(ModeloCertificado)
class ModeloCertificadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "tipo", "curso", "unidade", "ativo", "atualizado_em")
    list_filter = ("tipo", "ativo", "unidade")
    search_fields = ("nome", "descricao", "slug")
    readonly_fields = ("slug", "criado_em", "atualizado_em")


@admin.register(ConfiguracaoVisualCertificado)
class ConfiguracaoVisualCertificadoAdmin(admin.ModelAdmin):
    list_display = ("modelo", "sigla_instituicao", "cidade_padrao", "estado_padrao", "atualizado_em")
    search_fields = ("modelo__nome", "nome_da_instituicao", "sigla_instituicao")


@admin.register(AssinaturaCertificado)
class AssinaturaCertificadoAdmin(admin.ModelAdmin):
    list_display = ("nome", "cargo", "modelo", "ordem", "ativo")
    list_filter = ("ativo", "modelo")
    search_fields = ("nome", "cargo", "modelo__nome")


@admin.register(CertificadoEmitido)
class CertificadoEmitidoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_certificado",
        "nome_aluno_snapshot",
        "curso_nome_snapshot",
        "status",
        "codigo_validacao",
        "data_emissao",
    )
    list_filter = ("status", "modelo", "unidade")
    search_fields = (
        "numero_certificado",
        "codigo_validacao",
        "nome_aluno_snapshot",
        "cpf_aluno_snapshot",
        "curso_nome_snapshot",
    )
    readonly_fields = ("numero_certificado", "codigo_validacao", "qr_code_data_uri", "criado_em", "atualizado_em")


@admin.register(HistoricoEmissaoCertificado)
class HistoricoEmissaoCertificadoAdmin(admin.ModelAdmin):
    list_display = ("acao", "certificado", "modelo", "usuario", "ip_origem", "criado_em")
    list_filter = ("acao",)
    search_fields = ("descricao", "usuario__username", "certificado__numero_certificado")
    readonly_fields = ("criado_em",)

