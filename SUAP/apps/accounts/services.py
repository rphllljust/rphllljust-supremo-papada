from django.urls import reverse

from apps.usuarios.models import Pessoa, Usuario


def redirect_by_profile(user) -> str:
    tipo = getattr(user, "tipo", None)
    if tipo == "SECRETARIA":
        return reverse("matriculas:matriculas_list")
    if tipo == "COORDENACAO":
        return reverse("dashboard:index")
    if tipo == "PROFESSOR":
        return reverse("turmas:turmas_list")
    if tipo == "ALUNO":
        return reverse("matriculas:matriculas_list")
    return reverse("dashboard:index")


def create_public_user(*, username, first_name, last_name, email, cpf, perfil, password):
    nome_completo = " ".join(part for part in [first_name, last_name] if part).strip() or username
    pessoa = Pessoa.objects.create(
        nome_completo=nome_completo,
        cpf=cpf,
        email=email or "",
        telefone="",
    )
    return Usuario.objects.create_user(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email or "",
        cpf=cpf,
        tipo=perfil,
        password=password,
        pessoa=pessoa,
    )

