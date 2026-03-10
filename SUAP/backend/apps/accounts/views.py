from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import (
    LoginView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from apps.usuarios.models import PerfilUsuario

from .forms import CadastroPublicoForm, PerfilAuthenticationForm, RecuperarSenhaForm
from .services import create_public_user, redirect_by_profile
from .tokens import token_generator


class AccountsLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = PerfilAuthenticationForm
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.method == "GET" and request.GET.get("next") and not request.user.is_authenticated:
            messages.warning(request, "Sua sessao expirou. Faca login novamente para continuar.")
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        return redirect_by_profile(self.request.user)


def logout_view(request):
    if request.method != "POST":
        messages.warning(request, "Use o botao Sair para encerrar a sessao.")
        return redirect("dashboard:index")
    logout(request)
    messages.success(request, "Sessao encerrada com sucesso.")
    return redirect("accounts:logout_confirmado")


def logout_confirmado(request):
    return render(request, "accounts/logout_confirmado.html")


def cadastro(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = CadastroPublicoForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        perfil = form.cleaned_data["perfil"]
        if perfil == PerfilUsuario.ALUNO:
            messages.error(request, "Perfil Aluno nao possui acesso ao sistema SUAP.")
            return render(request, "accounts/cadastro.html", {"form": form}, status=403)

        usuario = create_public_user(
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data.get("last_name", ""),
            email=form.cleaned_data.get("email", ""),
            cpf=form.cleaned_data["cpf"],
            perfil=perfil,
            password=form.cleaned_data["password1"],
        )
        messages.success(
            request,
            f"Conta criada com sucesso para o CPF {usuario.cpf}. Agora faca login.",
        )
        return redirect("accounts:login")

    return render(request, "accounts/cadastro.html", {"form": form})


class AccountsPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")
    form_class = RecuperarSenhaForm


class AccountsPasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class AccountsPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")
    token_generator = token_generator


class AccountsPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"

