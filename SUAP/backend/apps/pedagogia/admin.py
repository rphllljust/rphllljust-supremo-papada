from django.contrib import admin

from .models import AtendimentoPedagogico


@admin.register(AtendimentoPedagogico)
class AtendimentoPedagogicoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "aluno",
        "pedagogia_responsavel",
        "data_atendimento",
        "status",
    )
    list_filter = ("status", "data_atendimento")
    search_fields = (
        "aluno__username",
        "aluno__first_name",
        "aluno__last_name",
        "aluno__pessoa__nome_completo",
        "pedagogia_responsavel__username",
        "pedagogia_responsavel__first_name",
        "pedagogia_responsavel__last_name",
        "pedagogia_responsavel__pessoa__nome_completo",
        "diagnostico",
        "plano_acao",
    )
