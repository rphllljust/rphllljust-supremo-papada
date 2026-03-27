from django.contrib import admin

from .models import (
    Auditoria,
    CoRequisito,
    ComponenteCurricular,
    ConfiguracaoCursoWizard,
    Coordenador,
    Curso,
    CursoCoordenador,
    EstruturaCurso,
    MatrizComponente,
    MatrizCurricular,
    PreRequisito,
)


@admin.register(EstruturaCurso)
class EstruturaCursoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "ativo", "criado_em", "atualizado_em")
    list_filter = ("ativo",)
    search_fields = ("nome", "descricao")


@admin.register(MatrizCurricular)
class MatrizCurricularAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "nome", "versao", "estrutura_curso", "carga_horaria_total", "ativo")
    list_filter = ("ativo", "estrutura_curso")
    search_fields = ("codigo", "nome", "versao", "estrutura_curso__nome")


@admin.register(ComponenteCurricular)
class ComponenteCurricularAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "nome", "tipo", "carga_horaria", "ativo")
    list_filter = ("ativo", "tipo")
    search_fields = ("codigo", "nome", "ementa")


@admin.register(MatrizComponente)
class MatrizComponenteAdmin(admin.ModelAdmin):
    list_display = ("id", "matriz_curricular", "componente_curricular", "periodo", "carga_horaria", "obrigatorio", "ordem")
    list_filter = ("obrigatorio", "periodo", "matriz_curricular")
    search_fields = ("matriz_curricular__nome", "matriz_curricular__codigo", "componente_curricular__nome", "componente_curricular__codigo")


@admin.register(PreRequisito)
class PreRequisitoAdmin(admin.ModelAdmin):
    list_display = ("id", "componente", "requisito", "criado_em")
    search_fields = ("componente__nome", "componente__codigo", "requisito__nome", "requisito__codigo")


@admin.register(CoRequisito)
class CoRequisitoAdmin(admin.ModelAdmin):
    list_display = ("id", "componente", "requisito", "criado_em")
    search_fields = ("componente__nome", "componente__codigo", "requisito__nome", "requisito__codigo")


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("id", "codigo", "nome", "modalidade", "situacao", "matriz_curricular", "ativo")
    list_filter = ("ativo", "modalidade", "situacao")
    search_fields = ("codigo", "nome", "nome_curto")


@admin.register(Coordenador)
class CoordenadorAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "email", "matricula", "ativo")
    list_filter = ("ativo",)
    search_fields = ("nome", "email", "matricula")


@admin.register(CursoCoordenador)
class CursoCoordenadorAdmin(admin.ModelAdmin):
    list_display = ("id", "curso", "coordenador", "principal", "inicio_vigencia", "fim_vigencia")
    list_filter = ("principal", "curso")
    search_fields = ("curso__nome", "curso__codigo", "coordenador__nome", "coordenador__matricula")


@admin.register(ConfiguracaoCursoWizard)
class ConfiguracaoCursoWizardAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "etapa_atual", "status", "curso", "matriz_curricular", "atualizado_em")
    list_filter = ("status", "etapa_atual")
    search_fields = ("usuario__username", "usuario__cpf", "curso__nome", "matriz_curricular__nome")


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "acao", "entidade", "entidade_id", "criado_em")
    list_filter = ("acao", "entidade")
    search_fields = ("usuario__username", "entidade", "entidade_id")
