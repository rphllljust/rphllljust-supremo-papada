from django import forms

from .models import Usuario


class TipoUsuarioForm(forms.ModelForm):
    tipo_valor = None

    class Meta:
        model = Usuario
        fields = ["username", "first_name", "last_name", "email", "cpf", "is_active"]
        labels = {
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
        if not usuario.password:
            usuario.set_unusable_password()
        if commit:
            usuario.save()
        return usuario

