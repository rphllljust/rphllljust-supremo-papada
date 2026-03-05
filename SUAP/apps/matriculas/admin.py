from django.contrib import admin

from .models import (
    ConsolidacaoAcademica,
    DocumentoEmitido,
    DocumentoMatricula,
    EtapaFluxo,
    EtapaFluxoEmissao,
    EtapaFluxoTransferencia,
    FluxoEmissaoDocumento,
    FluxoMatricula,
    FluxoTransferencia,
    Matricula,
    PendenciaDocumental,
    RegraAcademica,
    Transferencia,
)


class DocumentoMatriculaInline(admin.TabularInline):
    model = DocumentoMatricula
    extra = 0
    readonly_fields = ("validado_por",)


class PendenciaDocumentalInline(admin.TabularInline):
    model = PendenciaDocumental
    extra = 0


class DocumentoEmitidoInline(admin.TabularInline):
    model = DocumentoEmitido
    extra = 0
    readonly_fields = ("numero_protocolo", "data_emissao")


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("numero_matricula", "aluno", "curso", "turma", "tipo_matricula", "status", "data_matricula")
    list_filter = ("tipo_matricula", "status", "curso")
    search_fields = ("numero_matricula", "aluno__username", "aluno__first_name", "aluno__last_name")
    inlines = [DocumentoMatriculaInline, PendenciaDocumentalInline, DocumentoEmitidoInline]


@admin.register(DocumentoMatricula)
class DocumentoMatriculaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "tipo_documento", "status", "data_recebimento", "data_validacao", "validado_por")
    list_filter = ("tipo_documento", "status")


@admin.register(PendenciaDocumental)
class PendenciaDocumentalAdmin(admin.ModelAdmin):
    list_display = ("matricula", "descricao", "status", "data_abertura", "data_resolucao")
    list_filter = ("status",)


@admin.register(DocumentoEmitido)
class DocumentoEmitidoAdmin(admin.ModelAdmin):
    list_display = ("numero_protocolo", "matricula", "tipo", "data_emissao", "validado", "entregue")
    list_filter = ("tipo", "validado", "entregue")
    search_fields = ("numero_protocolo", "matricula__aluno__username", "recebido_por")
    readonly_fields = ("numero_protocolo", "data_emissao")


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "tipo", "status", "data_solicitacao", "numero_guia")
    list_filter = ("tipo", "status")


@admin.register(RegraAcademica)
class RegraAcademicaAdmin(admin.ModelAdmin):
    list_display = ("curso", "media_minima", "frequencia_minima")


@admin.register(ConsolidacaoAcademica)
class ConsolidacaoAcademicaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "situacao", "media_final", "percentual_frequencia", "data_consolidacao")
    list_filter = ("situacao",)
    readonly_fields = ("data_consolidacao",)


class EtapaFluxoInline(admin.TabularInline):
    model = EtapaFluxo
    extra = 0
    readonly_fields = ("data",)


@admin.register(FluxoMatricula)
class FluxoMatriculaAdmin(admin.ModelAdmin):
    list_display = ("aluno", "tipo_matricula", "etapa_atual", "concluido", "data_inicio")
    list_filter = ("etapa_atual", "concluido", "tipo_matricula")
    search_fields = ("aluno__username", "aluno__first_name", "aluno__last_name")
    readonly_fields = ("data_inicio",)
    inlines = [EtapaFluxoInline]


class EtapaFluxoEmissaoInline(admin.TabularInline):
    model = EtapaFluxoEmissao
    extra = 0
    readonly_fields = ("data",)


@admin.register(FluxoEmissaoDocumento)
class FluxoEmissaoDocumentoAdmin(admin.ModelAdmin):
    list_display = ("solicitante", "tipo_documento", "etapa_atual", "elegivel", "concluido", "data_inicio")
    list_filter = ("etapa_atual", "tipo_documento", "concluido", "elegivel")
    search_fields = ("solicitante__username", "solicitante__first_name", "solicitante__last_name")
    readonly_fields = ("data_inicio", "elegivel", "motivo_inelegivel")
    inlines = [EtapaFluxoEmissaoInline]


class EtapaFluxoTransferenciaInline(admin.TabularInline):
    model = EtapaFluxoTransferencia
    extra = 0
    readonly_fields = ("data",)


@admin.register(FluxoTransferencia)
class FluxoTransferenciaAdmin(admin.ModelAdmin):
    list_display = ("matricula", "etapa_atual", "concluido", "data_inicio")
    list_filter = ("etapa_atual", "concluido")
    search_fields = (
        "matricula__aluno__username",
        "matricula__aluno__first_name",
        "matricula__aluno__last_name",
    )
    readonly_fields = ("data_inicio",)
    inlines = [EtapaFluxoTransferenciaInline]
