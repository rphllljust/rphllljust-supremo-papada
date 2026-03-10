from django import forms

from .models import AcompanhamentoEstagio, Convenio, Estagio, TermoCompromisso


class ConvenioForm(forms.ModelForm):
    class Meta:
        model = Convenio
        fields = [
            "empresa", "cnpj", "responsavel_empresa", "email_empresa",
            "telefone_empresa", "data_assinatura", "data_vencimento",
            "status", "objeto", "responsavel_idep",
        ]
        labels = {
            "empresa": "Empresa / Instituição",
            "cnpj": "CNPJ",
            "responsavel_empresa": "Responsável na Empresa",
            "email_empresa": "E-mail da Empresa",
            "telefone_empresa": "Telefone",
            "data_assinatura": "Data de Assinatura",
            "data_vencimento": "Data de Vencimento",
            "status": "Status",
            "objeto": "Objeto do Convênio",
            "responsavel_idep": "Responsável IDEP",
        }
        widgets = {
            "data_assinatura": forms.DateInput(attrs={"type": "date"}),
            "data_vencimento": forms.DateInput(attrs={"type": "date"}),
            "objeto": forms.Textarea(attrs={"rows": 4}),
        }


class EstagioForm(forms.ModelForm):
    class Meta:
        model = Estagio
        fields = [
            "matricula", "convenio", "modalidade", "empresa", "supervisor_empresa",
            "orientador_idep", "carga_horaria_total", "carga_horaria_semanal",
            "data_inicio", "data_fim_prevista", "bolsa_mensal", "seguro_numero",
            "status", "observacao",
        ]
        labels = {
            "matricula": "Matrícula",
            "convenio": "Convênio",
            "modalidade": "Modalidade",
            "empresa": "Empresa / Local",
            "supervisor_empresa": "Supervisor na Empresa",
            "orientador_idep": "Orientador IDEP",
            "carga_horaria_total": "Carga Horária Total (h)",
            "carga_horaria_semanal": "Carga Horária Semanal (h)",
            "data_inicio": "Data de Início",
            "data_fim_prevista": "Data Fim Prevista",
            "bolsa_mensal": "Bolsa Mensal (R$)",
            "seguro_numero": "Nº Apólice do Seguro",
            "status": "Status",
            "observacao": "Observação",
        }
        widgets = {
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim_prevista": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class EncerrarEstagioForm(forms.ModelForm):
    class Meta:
        model = Estagio
        fields = ["status", "data_fim_real", "observacao"]
        labels = {
            "status": "Status Final",
            "data_fim_real": "Data de Encerramento",
            "observacao": "Observação",
        }
        widgets = {
            "data_fim_real": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class TermoCompromissoForm(forms.ModelForm):
    class Meta:
        model = TermoCompromisso
        fields = [
            "estagio", "data_assinatura", "status",
            "assinado_aluno", "assinado_empresa", "assinado_idep", "observacao",
        ]
        labels = {
            "estagio": "Estágio",
            "data_assinatura": "Data de Assinatura",
            "status": "Status",
            "assinado_aluno": "Assinado pelo Aluno",
            "assinado_empresa": "Assinado pela Empresa",
            "assinado_idep": "Assinado pelo IDEP",
            "observacao": "Observação",
        }
        widgets = {
            "data_assinatura": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class AcompanhamentoEstagioForm(forms.ModelForm):
    class Meta:
        model = AcompanhamentoEstagio
        fields = ["estagio", "tipo", "data", "descricao"]
        labels = {
            "estagio": "Estágio",
            "tipo": "Tipo de Acompanhamento",
            "data": "Data",
            "descricao": "Descrição / Observações",
        }
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.Textarea(attrs={"rows": 4}),
        }
