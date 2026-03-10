from django.contrib import admin

from .models import Notificacao, NotificacaoCategoria, PreferenciaNotificacao


@admin.register(NotificacaoCategoria)
class NotificacaoCategoriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "slug", "ordem", "ativa")
    list_editable = ("ordem", "ativa")
    search_fields = ("titulo", "slug", "descricao")


@admin.register(PreferenciaNotificacao)
class PreferenciaNotificacaoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "categoria", "via_suap", "via_email", "atualizado_em")
    list_filter = ("via_suap", "via_email", "categoria")
    search_fields = ("usuario__username", "usuario__pessoa__nome_completo", "categoria__titulo")


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "usuario", "categoria", "tipo", "via_suap", "via_email", "data_evento", "lida_em")
    list_filter = ("tipo", "categoria", "via_suap", "via_email")
    search_fields = ("titulo", "resumo", "mensagem", "usuario__username", "usuario__pessoa__nome_completo")
    autocomplete_fields = ("usuario", "categoria")
