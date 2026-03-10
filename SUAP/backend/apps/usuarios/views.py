from django.shortcuts import redirect


def index(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    return redirect("usuarios:alunos_list")


def logout_confirmado(request):
    return redirect("accounts:logout_confirmado")


def cadastro_publico(request):
    return redirect("accounts:register")
