from django.contrib import admin

from .models import SicaComponenteCurricular, SicaEquivalencia, SicaMatrizCurricular, SicaPreRequisito


class SicaComponenteInline(admin.TabularInline):
    model = SicaComponenteCurricular
    extra = 0


@admin.register(SicaMatrizCurricular)
class SicaMatrizCurricularAdmin(admin.ModelAdmin):
    list_display = ("id", "curso", "versao", "status", "criado_em")
    list_filter = ("status", "curso")
    search_fields = ("curso__nome", "versao", "descricao")
    inlines = [SicaComponenteInline]


@admin.register(SicaComponenteCurricular)
class SicaComponenteCurricularAdmin(admin.ModelAdmin):
    list_display = ("id", "componente", "matriz", "periodo", "tipo", "carga_horaria")
    list_filter = ("tipo", "periodo", "matriz__curso")
    search_fields = ("componente", "ementa", "matriz__curso__nome", "matriz__versao")


@admin.register(SicaPreRequisito)
class SicaPreRequisitoAdmin(admin.ModelAdmin):
    list_display = ("id", "componente", "prerequisito")
    search_fields = ("componente__componente", "prerequisito__componente")


@admin.register(SicaEquivalencia)
class SicaEquivalenciaAdmin(admin.ModelAdmin):
    list_display = ("id", "componente", "equivalente")
    search_fields = ("componente__componente", "equivalente__componente")
