from django import forms

from apps.matriculas.models import Matricula
from apps.turmas.models import Turma


class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ["aluno", "curso", "turma", "status"]
        labels = {
            "aluno": "Aluno",
            "curso": "Curso",
            "turma": "Turma",
            "status": "Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["curso"].queryset = self.fields["curso"].queryset.order_by("nome")
        self.fields["turma"].queryset = Turma.objects.select_related("curso").all().order_by("ano_letivo", "nome")

        curso_id = None
        if self.data.get("curso"):
            curso_id = self.data.get("curso")
        elif self.instance.pk and self.instance.curso_id:
            curso_id = self.instance.curso_id

        if curso_id:
            self.fields["turma"].queryset = Turma.objects.filter(curso_id=curso_id).order_by("ano_letivo", "nome")

    def clean(self):
        cleaned_data = super().clean()
        curso = cleaned_data.get("curso")
        turma = cleaned_data.get("turma")

        if curso and turma and turma.curso_id != curso.id:
            self.add_error("turma", "A turma selecionada nao pertence ao curso informado.")

        return cleaned_data
