from django import forms

from apps.matriculas.models import Matricula


class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ["aluno", "turma", "status"]
        labels = {
            "aluno": "Aluno",
            "turma": "Turma",
            "status": "Status",
        }

