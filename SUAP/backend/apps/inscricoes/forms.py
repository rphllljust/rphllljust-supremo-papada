from django import forms

from .models import (
    Candidato,
    ChamadaProcessoSeletivo,
    ConvocacaoCandidato,
    CotaProcessoSeletivo,
    DocumentoInscricao,
    Inscricao,
    ProcessoSeletivo,
    PublicacaoInscricao,
    RecursoInscricao,
)


class PublicacaoInscricaoForm(forms.ModelForm):
    class Meta:
        model = PublicacaoInscricao
        fields = [
            "curso",
            "codigo_edital",
            "titulo",
            "descricao",
            "vagas",
            "modalidade_ingresso",
            "nota_corte",
            "usa_cotas_lei_12711",
            "data_inicio",
            "data_fim",
            "status",
        ]
        labels = {
            "curso": "Curso",
            "codigo_edital": "Codigo do Edital",
            "titulo": "Titulo do Edital",
            "descricao": "Descricao / Requisitos",
            "vagas": "Numero de Vagas",
            "modalidade_ingresso": "Modalidade de Ingresso",
            "nota_corte": "Nota de Corte",
            "usa_cotas_lei_12711": "Aplica Lei de Cotas",
            "data_inicio": "Inicio das Inscricoes",
            "data_fim": "Fim das Inscricoes",
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
            "publicacao",
            "nome_candidato",
            "cpf",
            "email",
            "telefone",
            "data_nascimento",
            "modalidade_concorrencia",
            "cota_codigo_opcao",
            "status_candidato",
            "usuario",
            "observacao",
        ]
        labels = {
            "publicacao": "Edital",
            "nome_candidato": "Nome Completo",
            "cpf": "CPF (apenas numeros)",
            "email": "E-mail",
            "telefone": "Telefone",
            "data_nascimento": "Data de Nascimento",
            "modalidade_concorrencia": "Modalidade de Concorrencia",
            "cota_codigo_opcao": "Codigo da Cota",
            "status_candidato": "Status do Candidato",
            "usuario": "Usuario do Sistema (opcional)",
            "observacao": "Observacao",
        }
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class InscricaoValidarForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        fields = ["status", "status_candidato", "observacao"]
        labels = {
            "status": "Status",
            "status_candidato": "Status do Candidato",
            "observacao": "Observacao",
        }
        widgets = {"observacao": forms.Textarea(attrs={"rows": 3})}


class DocumentoInscricaoForm(forms.ModelForm):
    class Meta:
        model = DocumentoInscricao
        fields = [
            "tipo",
            "arquivo",
            "entregue",
            "status_validacao",
            "data_entrega",
            "observacao",
            "justificativa_validacao",
        ]
        labels = {
            "tipo": "Tipo de Documento",
            "arquivo": "Arquivo Digital",
            "entregue": "Entregue",
            "status_validacao": "Status de Validacao",
            "data_entrega": "Data de Entrega",
            "observacao": "Observacao",
            "justificativa_validacao": "Justificativa da Validacao",
        }
        widgets = {
            "data_entrega": forms.DateInput(attrs={"type": "date"}),
            "justificativa_validacao": forms.Textarea(attrs={"rows": 3}),
        }


class ProcessoSeletivoForm(forms.ModelForm):
    class Meta:
        model = ProcessoSeletivo
        fields = [
            "publicacao",
            "modalidade",
            "data_realizacao",
            "data_resultado",
            "status",
            "nota_corte",
            "usa_cotas_lei_12711",
            "criterios",
            "resultado",
            "responsavel",
        ]
        labels = {
            "publicacao": "Publicacao",
            "modalidade": "Modalidade",
            "data_realizacao": "Data de Realizacao",
            "data_resultado": "Data do Resultado",
            "status": "Status",
            "nota_corte": "Nota de Corte",
            "usa_cotas_lei_12711": "Aplica Lei de Cotas",
            "criterios": "Criterios",
            "resultado": "Resultado Publicado",
            "responsavel": "Responsavel",
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
            "processo",
            "inscricao",
            "classificacao",
            "pontuacao",
            "modalidade_vaga",
            "cota_codigo",
            "situacao",
            "chamada_atual",
            "data_convocacao",
            "observacao",
        ]
        labels = {
            "processo": "Processo Seletivo",
            "inscricao": "Inscricao",
            "classificacao": "Classificacao",
            "pontuacao": "Pontuacao",
            "modalidade_vaga": "Modalidade de Vaga",
            "cota_codigo": "Codigo da Cota",
            "situacao": "Situacao",
            "chamada_atual": "Chamada Atual",
            "data_convocacao": "Data da Convocacao",
            "observacao": "Observacao",
        }
        widgets = {
            "data_convocacao": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class CotaProcessoSeletivoForm(forms.ModelForm):
    class Meta:
        model = CotaProcessoSeletivo
        fields = ["processo", "codigo", "nome", "percentual_vagas", "vagas_reservadas", "ordem_remanejamento", "ativa"]


class ChamadaProcessoSeletivoForm(forms.ModelForm):
    class Meta:
        model = ChamadaProcessoSeletivo
        fields = [
            "processo",
            "numero",
            "tipo",
            "data_publicacao",
            "prazo_matricula_inicio",
            "prazo_matricula_fim",
            "status",
            "observacao",
        ]
        widgets = {
            "data_publicacao": forms.DateInput(attrs={"type": "date"}),
            "prazo_matricula_inicio": forms.DateInput(attrs={"type": "date"}),
            "prazo_matricula_fim": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class ConvocacaoCandidatoForm(forms.ModelForm):
    class Meta:
        model = ConvocacaoCandidato
        fields = [
            "chamada",
            "candidato",
            "modalidade_vaga",
            "cota_codigo",
            "classificacao_na_chamada",
            "status",
            "data_status",
            "observacao",
        ]
        widgets = {
            "data_status": forms.DateInput(attrs={"type": "date"}),
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
            "status": "Decisao",
            "resposta": "Resposta / Justificativa",
            "data_decisao": "Data da Decisao",
        }
        widgets = {
            "resposta": forms.Textarea(attrs={"rows": 4}),
            "data_decisao": forms.DateInput(attrs={"type": "date"}),
        }
