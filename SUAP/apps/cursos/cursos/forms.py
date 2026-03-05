from django import forms

from apps.cursos.models import Curso


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
