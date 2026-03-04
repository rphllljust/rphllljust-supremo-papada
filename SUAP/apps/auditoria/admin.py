from django.contrib import admin

from .models import LogAuditoria


@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("data", "acao", "modelo", "objeto_id", "usuario", "ip_address")
    list_filter = ("acao", "modelo")
    search_fields = ("usuario__username", "modelo", "descricao")
    readonly_fields = ("data", "usuario", "acao", "modelo", "objeto_id", "descricao", "dados", "ip_address")
    date_hierarchy = "data"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
