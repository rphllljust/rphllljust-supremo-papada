from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Aluno, DocumentoPessoal, Endereco, Pessoa, Responsavel, Usuario


@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'cpf', 'tipo', 'is_staff')
    list_filter = ('tipo', 'is_staff', 'is_superuser', 'is_active')

    fieldsets = UserAdmin.fieldsets + (
        ('Dados Institucionais', {'fields': ('cpf', 'tipo', 'pessoa')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Dados Institucionais', {'fields': ('cpf', 'tipo')}),
    )


@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ("nome_completo", "cpf", "email", "telefone", "ativo")
    search_fields = ("nome_completo", "cpf", "email")
    list_filter = ("ativo",)


@admin.register(Endereco)
class EnderecoAdmin(admin.ModelAdmin):
    list_display = ("pessoa", "municipio", "uf", "principal")
    list_filter = ("uf", "principal")
    search_fields = ("pessoa__nome_completo", "municipio", "cep")


@admin.register(DocumentoPessoal)
class DocumentoPessoalAdmin(admin.ModelAdmin):
    list_display = ("pessoa", "tipo", "numero", "orgao_emissor", "uf_emissor")
    list_filter = ("tipo", "uf_emissor")
    search_fields = ("pessoa__nome_completo", "numero")


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ("pessoa", "usuario", "situacao", "data_ingresso")
    list_filter = ("situacao",)
    search_fields = ("pessoa__nome_completo", "pessoa__cpf", "usuario__username")


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("pessoa", "aluno", "parentesco", "responsavel_principal")
    list_filter = ("responsavel_principal", "parentesco")
    search_fields = ("pessoa__nome_completo", "aluno__pessoa__nome_completo")
