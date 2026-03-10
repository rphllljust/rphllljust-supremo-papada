from django import forms

from .models import (
    Candidato,
    DocumentoInscricao,
    Inscricao,
    ProcessoSeletivo,
    PublicacaoInscricao,
    RecursoInscricao,
)


class PublicacaoInscricaoForm(forms.ModelForm):
    class Meta:
        model = PublicacaoInscricao
        fields = ["curso", "titulo", "descricao", "vagas", "data_inicio", "data_fim", "status"]
        labels = {
            "curso": "Curso",
            "titulo": "Título do Edital",
            "descricao": "Descrição / Requisitos",
            "vagas": "Nº de Vagas",
            "data_inicio": "Início das Inscrições",
            "data_fim": "Fim das Inscrições",
            "status": "Status",
        }
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 4}),
            "data_inicio": forms.DateInput(attrs={"type": "date"}),
            "data_fim": forms.DateInput(attrs={"type": "date"}),
        }


class InscricaoForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        fields = [
            "publicacao", "nome_candidato", "cpf", "email",
            "telefone", "data_nascimento", "usuario", "observacao",
        ]
        labels = {
            "publicacao": "Edital",
            "nome_candidato": "Nome Completo",
            "cpf": "CPF (apenas números)",
            "email": "E-mail",
            "telefone": "Telefone",
            "data_nascimento": "Data de Nascimento",
            "usuario": "Usuário do Sistema (opcional)",
            "observacao": "Observação",
        }
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class InscricaoValidarForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        fields = ["status", "observacao"]
        labels = {"status": "Status", "observacao": "Observação"}
        widgets = {"observacao": forms.Textarea(attrs={"rows": 3})}


class DocumentoInscricaoForm(forms.ModelForm):
    class Meta:
        model = DocumentoInscricao
        fields = ["tipo", "entregue", "data_entrega", "observacao"]
        labels = {
            "tipo": "Tipo de Documento",
            "entregue": "Entregue",
            "data_entrega": "Data de Entrega",
            "observacao": "Observação",
        }
        widgets = {"data_entrega": forms.DateInput(attrs={"type": "date"})}


class ProcessoSeletivoForm(forms.ModelForm):
    class Meta:
        model = ProcessoSeletivo
        fields = [
            "publicacao", "modalidade", "data_realizacao",
            "data_resultado", "status", "criterios", "resultado", "responsavel",
        ]
        labels = {
            "publicacao": "Publicação",
            "modalidade": "Modalidade",
            "data_realizacao": "Data de Realização",
            "data_resultado": "Data do Resultado",
            "status": "Status",
            "criterios": "Critérios",
            "resultado": "Resultado Publicado",
            "responsavel": "Responsável",
        }
        widgets = {
            "data_realizacao": forms.DateInput(attrs={"type": "date"}),
            "data_resultado": forms.DateInput(attrs={"type": "date"}),
            "criterios": forms.Textarea(attrs={"rows": 4}),
            "resultado": forms.Textarea(attrs={"rows": 4}),
        }


class CandidatoForm(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = [
            "processo", "inscricao", "classificacao",
            "pontuacao", "situacao", "data_convocacao", "observacao",
        ]
        labels = {
            "processo": "Processo Seletivo",
            "inscricao": "Inscrição",
            "classificacao": "Classificação",
            "pontuacao": "Pontuação",
            "situacao": "Situação",
            "data_convocacao": "Data da Convocação",
            "observacao": "Observação",
        }
        widgets = {
            "data_convocacao": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class RecursoInscricaoForm(forms.ModelForm):
    class Meta:
        model = RecursoInscricao
        fields = ["candidato", "motivo"]
        labels = {"candidato": "Candidato", "motivo": "Motivo do Recurso"}
        widgets = {"motivo": forms.Textarea(attrs={"rows": 4})}


class RecursoDecisaoForm(forms.ModelForm):
    class Meta:
        model = RecursoInscricao
        fields = ["status", "resposta", "data_decisao"]
        labels = {
            "status": "Decisão",
            "resposta": "Resposta / Justificativa",
            "data_decisao": "Data da Decisão",
        }
        widgets = {
            "resposta": forms.Textarea(attrs={"rows": 4}),
            "data_decisao": forms.DateInput(attrs={"type": "date"}),
        }
