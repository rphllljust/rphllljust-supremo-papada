from django import forms

from .models import EmprestimoDocumento, EtapaFluxoArquivo, GuardaDocumental, TermoEliminacao


class GuardaDocumentalForm(forms.ModelForm):
    class Meta:
        model = GuardaDocumental
        fields = [
            "tipo_documento", "descricao", "numero_caixa", "localizacao",
            "data_eliminacao_prevista", "status", "matricula", "processo",
        ]
        labels = {
            "tipo_documento": "Tipo de Documento",
            "descricao": "Descrição",
            "numero_caixa": "Nº da Caixa",
            "localizacao": "Localização",
            "data_eliminacao_prevista": "Data de Eliminação Prevista",
            "status": "Status",
            "matricula": "Matrícula Vinculada",
            "processo": "Processo Vinculado",
        }
        widgets = {
            "data_eliminacao_prevista": forms.DateInput(attrs={"type": "date"}),
        }


class EmprestimoDocumentoForm(forms.ModelForm):
    class Meta:
        model = EmprestimoDocumento
        fields = ["solicitante", "data_devolucao", "devolvido", "observacao"]
        labels = {
            "solicitante": "Solicitante",
            "data_devolucao": "Data de Devolução",
            "devolvido": "Devolvido",
            "observacao": "Observação",
        }
        widgets = {
            "data_devolucao": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("devolvido") and not cleaned_data.get("data_devolucao"):
            self.add_error("data_devolucao", "Informe a data de devolução.")
        return cleaned_data


# ── P04 – Fluxo de Arquivo Escolar e Prazos ──────────────────────────────────

class FluxoArquivoIniciarForm(forms.ModelForm):
    """Etapa 1 – Inicia o fluxo vinculando uma GuardaDocumental existente."""

    class Meta:
        model = GuardaDocumental
        fields = []  # Seleção da guarda é feita pelo view via pk

    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class ClassificacaoForm(forms.ModelForm):
    """Etapa 1 – Classificar: tipo e descrição do documento."""

    class Meta:
        model = GuardaDocumental
        fields = ["tipo_documento", "descricao"]
        labels = {
            "tipo_documento": "Tipo de Documento",
            "descricao": "Descrição / Assunto",
        }


class IndexacaoForm(forms.ModelForm):
    """Etapa 2 – Indexar: localização física."""

    class Meta:
        model = GuardaDocumental
        fields = ["numero_caixa", "localizacao"]
        labels = {
            "numero_caixa": "Nº da Caixa",
            "localizacao": "Localização (Prateleira/Sala)",
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("numero_caixa") and not cleaned_data.get("localizacao"):
            raise forms.ValidationError("Informe ao menos o número da caixa ou a localização.")
        return cleaned_data


class PrazoGuardaForm(forms.ModelForm):
    """Etapa 3 – Prazo de guarda: data de eliminação prevista."""

    class Meta:
        model = GuardaDocumental
        fields = ["data_eliminacao_prevista"]
        labels = {"data_eliminacao_prevista": "Data de Eliminação Prevista"}
        widgets = {"data_eliminacao_prevista": forms.DateInput(attrs={"type": "date"})}

    def clean_data_eliminacao_prevista(self):
        data = self.cleaned_data.get("data_eliminacao_prevista")
        if not data:
            raise forms.ValidationError("A data de eliminação prevista é obrigatória.")
        return data


class TermoEliminacaoForm(forms.ModelForm):
    """Etapa 4 – Termo de Eliminação."""

    class Meta:
        model = TermoEliminacao
        fields = ["justificativa", "autorizado_por", "data_autorizacao", "observacao"]
        labels = {
            "justificativa": "Justificativa de Eliminação",
            "autorizado_por": "Autorizado por",
            "data_autorizacao": "Data de Autorização",
            "observacao": "Observação",
        }
        widgets = {
            "justificativa": forms.Textarea(attrs={"rows": 4}),
            "data_autorizacao": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("justificativa"):
            self.add_error("justificativa", "A justificativa é obrigatória para eliminar o documento.")
        if cleaned_data.get("autorizado_por") and not cleaned_data.get("data_autorizacao"):
            self.add_error("data_autorizacao", "Informe a data de autorização.")
        return cleaned_data


class EtapaArquivoObservacaoForm(forms.ModelForm):
    """Formulário genérico de observação para avançar etapas do P04."""

    class Meta:
        model = EtapaFluxoArquivo
        fields = ["observacao"]
        labels = {"observacao": "Observação"}
        widgets = {"observacao": forms.Textarea(attrs={"rows": 2})}
