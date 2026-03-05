# python
# file: apps/usuarios/views.py
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


def index(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    return redirect("usuarios:alunos_list")


def redirect_login_legacy(request):
    return redirect("accounts:login")


def redirect_logout_legacy(request):
    return redirect("accounts:logout")


class PerfilLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        return redirect("accounts:login")


def perfil_logout(request):
    return redirect("accounts:logout")


def logout_confirmado(request):
    return redirect("accounts:logout_confirmado")


def cadastro_publico(request):
    return redirect("accounts:register")
