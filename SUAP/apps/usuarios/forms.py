from django import forms

from .models import Pessoa, Usuario


class TipoUsuarioForm(forms.ModelForm):
    tipo_valor = None

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "cpf", "is_active"]
        labels = {
            "username": "Usuario de acesso",
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "email": "E-mail",
            "cpf": "CPF",
            "is_active": "Ativo",
        }

    def clean_cpf(self):
        cpf = "".join(ch for ch in self.cleaned_data["cpf"] if ch.isdigit())
        if len(cpf) != 11:
            raise forms.ValidationError("Informe um CPF com 11 digitos.")
        qs = Usuario.objects.filter(cpf=cpf)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ja existe um usuario com este CPF.")
        return cpf

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if not self.tipo_valor:
            raise ValueError("tipo_valor deve ser definido no formulario filho.")
        usuario.tipo = self.tipo_valor
        if not usuario.username:
            usuario.username = usuario.cpf
        if not usuario.password:
            usuario.set_unusable_password()

        nome_completo = " ".join(
            part for part in [usuario.first_name, usuario.last_name] if part
        ).strip() or usuario.username

        pessoa = usuario.pessoa
        if pessoa is None:
            pessoa = Pessoa(
                nome_completo=nome_completo,
                cpf=usuario.cpf,
                email=usuario.email or "",
                telefone="",
            )
        else:
            pessoa.nome_completo = nome_completo
            pessoa.cpf = usuario.cpf
            pessoa.email = usuario.email or ""

        if commit:
            pessoa.save()
            usuario.pessoa = pessoa
            usuario.save()
        else:
            usuario.pessoa = pessoa
        return usuario
