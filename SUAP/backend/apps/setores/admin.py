from django.contrib import admin

from .models import Setor


@admin.register(Setor)
class SetorAdmin(admin.ModelAdmin):
    list_display = ("codigo", "sigla", "nome", "setor_superior", "ativo")
    list_filter = ("ativo",)
    search_fields = ("codigo", "sigla", "nome")
