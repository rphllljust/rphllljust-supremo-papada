from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.accounts.utils import normalize_cpf
from apps.usuarios.models import PerfilUsuario, Pessoa, Usuario


def authenticate_user_by_cpf_profile(*, cpf: str, password: str, perfil: str):
    normalized_cpf = normalize_cpf(cpf)
    usuario = Usuario.objects.filter(cpf=normalized_cpf).first()
    if not usuario:
        raise ValidationError("Conta nao encontrada para o CPF informado.")

    if not usuario.is_active:
        raise ValidationError("Sua conta esta inativa. Procure a secretaria.")

    if usuario.tipo == PerfilUsuario.ALUNO:
        raise ValidationError("Perfil Aluno nao possui acesso ao sistema SUAP.")

    if usuario.tipo != perfil:
        raise ValidationError("O perfil selecionado nao corresponde ao perfil da sua conta.")

    if not usuario.check_password(password):
        raise ValidationError("Senha incorreta para o CPF informado.")

    return usuario


def redirect_by_profile(user) -> str:
    tipo = getattr(user, "tipo", None)
    if tipo == PerfilUsuario.SECRETARIA:
        return reverse("matriculas:matriculas_list")
    if tipo == PerfilUsuario.COORDENACAO:
        return reverse("dashboard:index")
    if tipo == PerfilUsuario.PROFESSOR:
        return reverse("turmas:turmas_list")
    if tipo == PerfilUsuario.ALUNO:
        return reverse("access:acesso_negado")
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
