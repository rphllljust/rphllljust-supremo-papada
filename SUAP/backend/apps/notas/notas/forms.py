from django import forms

from apps.notas.models import Nota


class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ["matricula", "descricao", "valor", "peso", "data_lancamento"]

