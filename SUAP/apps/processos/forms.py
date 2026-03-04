from django import forms

from .models import Processo, Tramitacao


class ProcessoForm(forms.ModelForm):
    class Meta:
        model = Processo
        fields = ["tipo", "requerente", "assunto", "descricao", "status", "data_conclusao"]
        labels = {
            "tipo": "Tipo",
            "requerente": "Requerente",
            "assunto": "Assunto",
            "descricao": "Descrição",
            "status": "Status",
            "data_conclusao": "Data de Conclusão",
        }
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "data_conclusao": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("status") in ("CONCLUIDO", "ARQUIVADO") and not cleaned_data.get("data_conclusao"):
            self.add_error("data_conclusao", "Informe a data de conclusão para este status.")
        return cleaned_data


class TramitacaoForm(forms.ModelForm):
    class Meta:
        model = Tramitacao
        fields = ["acao", "setor_destino", "observacao"]
        labels = {
            "acao": "Ação",
            "setor_destino": "Setor de Destino",
            "observacao": "Observação",
        }
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }
