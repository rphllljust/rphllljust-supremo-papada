from django import forms

from apps.frequencia.models import Frequencia


class FrequenciaForm(forms.ModelForm):
    class Meta:
        model = Frequencia
        fields = ["matricula", "data", "presente", "observacao"]

