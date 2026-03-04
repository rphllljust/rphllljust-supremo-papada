from django.contrib import admin
from .models import CalendarioLetivo, Curso

admin.site.register(Curso)

@admin.register(CalendarioLetivo)
class CalendarioLetivoAdmin(admin.ModelAdmin):
    list_display = ("ano_letivo", "curso", "data_inicio", "data_fim", "dias_letivos", "status")
    list_filter = ("status", "curso")
    search_fields = ("ano_letivo", "curso__nome")
