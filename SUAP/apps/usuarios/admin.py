from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'cpf', 'tipo', 'is_staff')
    list_filter = ('tipo', 'is_staff', 'is_superuser', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Dados Institucionais', {'fields': ('cpf', 'tipo')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados Institucionais', {'fields': ('cpf', 'tipo')}),
    )