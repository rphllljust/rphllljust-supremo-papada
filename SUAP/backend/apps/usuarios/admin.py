from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Aluno,
    DocumentoPessoal,
    Endereco,
    Pessoa,
    Responsavel,
    ServidorFerias,
    ServidorHistoricoFuncional,
    ServidorOcorrenciaAfastamento,
    ServidorPerfil,
    ServidorSetorHistorico,
    Usuario,
)


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
    list_display = ("pessoa", "situacao", "data_ingresso")
    list_filter = ("situacao",)
    search_fields = ("pessoa__nome_completo", "pessoa__cpf")


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ("pessoa", "aluno", "parentesco", "responsavel_principal")
    list_filter = ("responsavel_principal", "parentesco")
    search_fields = ("pessoa__nome_completo", "aluno__pessoa__nome_completo")


@admin.register(ServidorPerfil)
class ServidorPerfilAdmin(admin.ModelAdmin):
    list_display = ("matricula_servidor", "usuario", "nome_usual", "email_institucional", "em_pgd")
    search_fields = ("matricula_servidor", "usuario__username", "usuario__pessoa__nome_completo", "nome_usual")
    list_filter = ("em_pgd", "nao_tem_impressao_digital")


@admin.register(ServidorOcorrenciaAfastamento)
class ServidorOcorrenciaAfastamentoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "perfil", "tipo", "situacao", "data_inicio", "data_fim")
    list_filter = ("tipo", "situacao")
    search_fields = ("titulo", "perfil__usuario__username", "perfil__usuario__pessoa__nome_completo")


@admin.register(ServidorSetorHistorico)
class ServidorSetorHistoricoAdmin(admin.ModelAdmin):
    list_display = ("perfil", "setor", "tipo_vinculo", "principal", "data_inicio", "data_fim")
    list_filter = ("principal", "setor")
    search_fields = ("perfil__usuario__username", "perfil__usuario__pessoa__nome_completo", "setor__nome")


@admin.register(ServidorHistoricoFuncional)
class ServidorHistoricoFuncionalAdmin(admin.ModelAdmin):
    list_display = ("titulo", "perfil", "tipo_evento", "data_evento")
    list_filter = ("tipo_evento",)
    search_fields = ("titulo", "perfil__usuario__username", "perfil__usuario__pessoa__nome_completo")


@admin.register(ServidorFerias)
class ServidorFeriasAdmin(admin.ModelAdmin):
    list_display = ("perfil", "exercicio", "periodo_inicio", "periodo_fim", "situacao")
    list_filter = ("situacao",)
    search_fields = ("perfil__usuario__username", "perfil__usuario__pessoa__nome_completo", "exercicio")
