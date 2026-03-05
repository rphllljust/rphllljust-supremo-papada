from django import forms

from apps.unidades.models import Unidade


class UnidadeForm(forms.ModelForm):
    class Meta:
        model = Unidade
        fields = ["nome", "codigo"]
        labels = {
            "nome": "Nome",
            "codigo": "Codigo",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["codigo"].choices = Unidade.FIXED_UNITS
        for field in self.fields.values():
            field.disabled = True
