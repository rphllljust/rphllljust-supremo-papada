from django import forms

from apps.turmas.models import Turma


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ["curso", "nome", "ano_letivo", "status", "professor_responsavel"]
        labels = {
            "curso": "Curso",
            "nome": "Nome",
            "ano_letivo": "Ano letivo",
            "status": "Status",
            "professor_responsavel": "Professor responsavel",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].required = False
        self.fields["status"].initial = self.instance.status if self.instance and self.instance.pk else "PLANEJADA"

    def clean_status(self):
        return self.cleaned_data.get("status") or "PLANEJADA"
