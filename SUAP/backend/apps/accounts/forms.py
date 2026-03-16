from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from apps.usuarios.models import PerfilUsuario, Pessoa, Usuario

from .services import authenticate_user_by_cpf_profile
from .utils import normalize_cpf


class PerfilAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={
                "data-cpf-mask": "true",
                "inputmode": "numeric",
                "maxlength": "14",
                "placeholder": "000.000.000-00",
                "autocomplete": "username",
            }
        ),
    )
    perfil = forms.ChoiceField(choices=PerfilUsuario.autenticaveis_choices(), label="Perfil de acesso")

    def clean_username(self):
        return normalize_cpf(self.cleaned_data["username"])

    def clean(self):
        cleaned_data = self.cleaned_data
        cpf = cleaned_data.get("username")
        senha = cleaned_data.get("password")
        perfil = cleaned_data.get("perfil")

        if not cpf or not senha or not perfil:
            return cleaned_data

        try:
            usuario = authenticate_user_by_cpf_profile(cpf=cpf, password=senha, perfil=perfil)
        except ValidationError as exc:
            raise forms.ValidationError(exc.messages) from exc

        self.confirm_login_allowed(usuario)
        self.user_cache = usuario
        return cleaned_data


class CadastroPublicoForm(forms.Form):
    perfil = forms.ChoiceField(label="Perfil", choices=PerfilUsuario.autenticaveis_choices())
    first_name = forms.CharField(label="Nome", max_length=150)
    last_name = forms.CharField(label="Sobrenome", max_length=150)
    email = forms.EmailField(label="E-mail")
    cpf = forms.CharField(
        label="CPF",
        max_length=14,
        widget=forms.TextInput(
            attrs={
                "data-cpf-mask": "true",
                "inputmode": "numeric",
                "maxlength": "14",
                "placeholder": "000.000.000-00",
                "autocomplete": "off",
            }
        ),
    )
    password1 = forms.CharField(label="Senha", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar senha", widget=forms.PasswordInput)

    def clean_cpf(self):
        cpf = normalize_cpf(self.cleaned_data["cpf"])
        if Usuario.objects.filter(cpf=cpf).exists() or Pessoa.objects.filter(cpf=cpf).exists():
            raise ValidationError("Ja existe cadastro com este CPF.")
        return cpf

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        validate_email(email)
        if Usuario.objects.filter(email__iexact=email).exists() or Pessoa.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ja existe cadastro com este e-mail.")
        return email

    def clean(self):
        cleaned_data = super().clean()

        faltando = []
        for campo in ("first_name", "last_name", "email", "cpf", "perfil", "password1", "password2"):
            if not cleaned_data.get(campo):
                faltando.append(campo)
        if faltando:
            raise ValidationError("Revise os campos obrigatorios destacados no formulario.")

        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise ValidationError("As senhas nao conferem.")

        validate_password(cleaned_data["password1"])
        return cleaned_data


class RecuperarSenhaForm(PasswordResetForm):
    email = forms.EmailField(label="E-mail cadastrado")
