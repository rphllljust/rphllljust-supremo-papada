from django.urls import reverse

from apps.usuarios.models import PerfilUsuario, Pessoa, Usuario


def redirect_by_profile(user) -> str:
    tipo = getattr(user, "tipo", None)
    if tipo == PerfilUsuario.SECRETARIA:
        return reverse("matriculas:matriculas_list")
    if tipo == PerfilUsuario.COORDENACAO:
        return reverse("dashboard:index")
    if tipo == PerfilUsuario.PROFESSOR:
        return reverse("turmas:turmas_list")
    if tipo == PerfilUsuario.ALUNO:
        return reverse("accounts:acesso_negado")
    return reverse("dashboard:index")


def create_public_user(*, first_name, last_name, email, cpf, perfil, password):
    nome_completo = " ".join(part for part in [first_name, last_name] if part).strip() or cpf
    pessoa = Pessoa.objects.create(
        nome_completo=nome_completo,
        cpf=cpf,
        email=email or "",
        telefone="",
    )
    return Usuario.objects.create_user(
        username=cpf,
        first_name=first_name,
        last_name=last_name,
        email=email or "",
        cpf=cpf,
        tipo=perfil,
        password=password,
        pessoa=pessoa,
    )
