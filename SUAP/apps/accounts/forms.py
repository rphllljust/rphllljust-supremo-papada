from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.exceptions import ValidationError

from apps.usuarios.models import Pessoa, Usuario

from .utils import normalize_cpf


class PerfilAuthenticationForm(AuthenticationForm):
    perfil = forms.ChoiceField(choices=Usuario.TIPO_CHOICES, label="Perfil de acesso")

    def clean(self):
        cleaned_data = super().clean()
        user = self.get_user()
        perfil = cleaned_data.get("perfil")
        if user and perfil and getattr(user, "tipo", None) != perfil:
            raise forms.ValidationError("Perfil selecionado nao corresponde ao perfil do usuario.")
        return cleaned_data


class CadastroPublicoForm(forms.Form):
    PERFIL_CADASTRO_CHOICES = (
        ("ALUNO", "Aluno"),
        ("PROFESSOR", "Professor"),
    )

    username = forms.CharField(label="Usuario", max_length=150)
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    cpf = forms.CharField(label="CPF", max_length=14)
    perfil = forms.ChoiceField(label="Perfil", choices=PERFIL_CADASTRO_CHOICES)
    password1 = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar senha", widget=forms.PasswordInput)

    def clean_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["cpf"])
        if Usuario.objects.filter(cpf=cpf).exists() or Pessoa.objects.filter(cpf=cpf).exists():
            raise ValidationError("Ja existe cadastro com este CPF.")
        return cpf

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError("Este usuario ja esta em uso.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") and cleaned_data.get("password2") and cleaned_data["password1"] != cleaned_data["password2"]:
            raise ValidationError("As senhas nao conferem.")
        return cleaned_data


class RecuperarSenhaForm(PasswordResetForm):
    email = forms.EmailField(label="E-mail cadastrado")

