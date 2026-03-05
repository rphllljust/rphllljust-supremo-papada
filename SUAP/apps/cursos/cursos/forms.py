from django import forms

from apps.cursos.models import Curso
from apps.unidades.models import Unidade


class CursoForm(forms.ModelForm):
    class Meta:
        model = Curso
        fields = ["unidade", "nome", "sigla", "carga_horaria"]
        labels = {
            "unidade": "Unidade",
            "nome": "Nome",
            "sigla": "Sigla",
            "carga_horaria": "Carga horaria",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidade"].queryset = Unidade.objects.filter(
            codigo__in=[code for code, _ in Unidade.FIXED_UNITS]
        ).order_by("nome")
