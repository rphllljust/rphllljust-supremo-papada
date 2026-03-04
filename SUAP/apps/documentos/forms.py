from django import forms

from .models import AtaOficioMemorando, Declaracao, GuiaTransferencia, HistoricoEscolar


class DeclaracaoForm(forms.ModelForm):
    class Meta:
        model = Declaracao
        fields = ["tipo", "assunto", "matricula", "observacao"]
        labels = {
            "tipo": "Tipo de Declaração",
            "assunto": "Assunto",
            "matricula": "Matrícula",
            "observacao": "Observação",
        }
        widgets = {"observacao": forms.Textarea(attrs={"rows": 3})}


class HistoricoEscolarForm(forms.ModelForm):
    class Meta:
        model = HistoricoEscolar
        fields = ["tipo", "assunto", "matricula", "periodo_ref", "observacao"]
        labels = {
            "tipo": "Tipo",
            "assunto": "Assunto",
            "matricula": "Matrícula",
            "periodo_ref": "Período de Referência",
            "observacao": "Observação",
        }
        widgets = {"observacao": forms.Textarea(attrs={"rows": 3})}


class GuiaTransferenciaForm(forms.ModelForm):
    class Meta:
        model = GuiaTransferencia
        fields = ["assunto", "matricula", "escola_origem", "escola_destino", "transferencia", "observacao"]
        labels = {
            "assunto": "Assunto",
            "matricula": "Matrícula",
            "escola_origem": "Escola de Origem",
            "escola_destino": "Escola de Destino",
            "transferencia": "Transferência Vinculada",
            "observacao": "Observação",
        }
        widgets = {"observacao": forms.Textarea(attrs={"rows": 3})}


class AtaOficioMemorandoForm(forms.ModelForm):
    class Meta:
        model = AtaOficioMemorando
        fields = ["tipo", "assunto", "destinatario", "referencia", "processo", "observacao"]
        labels = {
            "tipo": "Tipo",
            "assunto": "Assunto",
            "destinatario": "Destinatário",
            "referencia": "Referência",
            "processo": "Processo Vinculado",
            "observacao": "Observação",
        }
        widgets = {"observacao": forms.Textarea(attrs={"rows": 3})}
