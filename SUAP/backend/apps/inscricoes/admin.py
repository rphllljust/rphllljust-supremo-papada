from django.contrib import admin

from .models import (
    Candidato,
    ChamadaProcessoSeletivo,
    ConvocacaoCandidato,
    CotaProcessoSeletivo,
    DocumentoInscricao,
    Inscricao,
    ProcessoSeletivo,
    PublicacaoInscricao,
    RecursoInscricao,
)


@admin.register(PublicacaoInscricao)
class PublicacaoInscricaoAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo_edital", "titulo", "curso", "modalidade_ingresso", "vagas", "status")
    search_fields = ("codigo_edital", "titulo", "curso__nome")
    list_filter = ("status", "modalidade_ingresso", "usa_cotas_lei_12711")


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ("id", "numero_inscricao", "nome_candidato", "cpf", "publicacao", "status", "status_candidato")
    search_fields = ("numero_inscricao", "nome_candidato", "cpf", "publicacao__titulo")
    list_filter = ("status", "status_candidato", "modalidade_concorrencia")


@admin.register(DocumentoInscricao)
class DocumentoInscricaoAdmin(admin.ModelAdmin):
    list_display = ("id", "inscricao", "tipo", "entregue", "status_validacao", "data_entrega")
    search_fields = ("inscricao__numero_inscricao", "inscricao__nome_candidato")
    list_filter = ("tipo", "entregue", "status_validacao")


@admin.register(ProcessoSeletivo)
class ProcessoSeletivoAdmin(admin.ModelAdmin):
    list_display = ("id", "publicacao", "modalidade", "status", "nota_corte", "usa_cotas_lei_12711")
    list_filter = ("modalidade", "status", "usa_cotas_lei_12711")


@admin.register(CotaProcessoSeletivo)
class CotaProcessoSeletivoAdmin(admin.ModelAdmin):
    list_display = ("id", "processo", "codigo", "nome", "percentual_vagas", "vagas_reservadas", "ativa")
    search_fields = ("codigo", "nome", "processo__publicacao__titulo")
    list_filter = ("ativa",)


@admin.register(ChamadaProcessoSeletivo)
class ChamadaProcessoSeletivoAdmin(admin.ModelAdmin):
    list_display = ("id", "processo", "numero", "tipo", "status", "data_publicacao")
    list_filter = ("tipo", "status")


@admin.register(Candidato)
class CandidatoAdmin(admin.ModelAdmin):
    list_display = ("id", "processo", "inscricao", "classificacao", "modalidade_vaga", "situacao")
    search_fields = ("inscricao__nome_candidato", "inscricao__cpf", "processo__publicacao__titulo")
    list_filter = ("situacao", "modalidade_vaga")


@admin.register(ConvocacaoCandidato)
class ConvocacaoCandidatoAdmin(admin.ModelAdmin):
    list_display = ("id", "chamada", "candidato", "modalidade_vaga", "status", "data_status")
    list_filter = ("status", "modalidade_vaga")


@admin.register(RecursoInscricao)
class RecursoInscricaoAdmin(admin.ModelAdmin):
    list_display = ("id", "candidato", "status", "data_recurso", "data_decisao")
    list_filter = ("status",)
