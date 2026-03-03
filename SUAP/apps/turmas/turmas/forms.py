from django import forms

from apps.turmas.models import Turma


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ["curso", "nome", "ano_letivo", "professor_responsavel"]
        labels = {
            "curso": "Curso",
            "nome": "Nome",
            "ano_letivo": "Ano letivo",
            "professor_responsavel": "Professor responsavel",
        }

