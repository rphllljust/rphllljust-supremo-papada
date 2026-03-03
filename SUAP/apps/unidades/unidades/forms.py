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

