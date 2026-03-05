from django import forms

from apps.matriculas.models import (
    ConsolidacaoAcademica,
    DocumentoEmitido,
    DocumentoMatricula,
    EtapaFluxo,
    EtapaFluxoEmissao,
    EtapaFluxoTransferencia,
    FluxoEmissaoDocumento,
    FluxoMatricula,
    FluxoTransferencia,
    Matricula,
    PendenciaDocumental,
    RegraAcademica,
    Transferencia,
)
from apps.turmas.models import Turma


class MatriculaForm(forms.ModelForm):
    class Meta:
        model = Matricula
        fields = ["aluno", "curso", "turma", "tipo_matricula", "status"]
        labels = {
            "aluno": "Aluno",
            "curso": "Curso",
            "turma": "Turma",
            "tipo_matricula": "Tipo de Matrícula",
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
        """UC01 – include: Validar Requisitos"""
        cleaned_data = super().clean()
        curso = cleaned_data.get("curso")
        turma = cleaned_data.get("turma")
        aluno = cleaned_data.get("aluno")
        tipo = cleaned_data.get("tipo_matricula")

        if curso and turma and turma.curso_id != curso.id:
            self.add_error("turma", "A turma selecionada nao pertence ao curso informado.")

        # Validar rematrícula: aluno deve ter matrícula anterior no mesmo curso
        if tipo == 'REMATRICULA' and aluno and curso:
            pk = self.instance.pk if self.instance else None
            ja_teve = Matricula.objects.filter(aluno=aluno, curso=curso).exclude(pk=pk).exists()
            if not ja_teve:
                self.add_error(
                    "tipo_matricula",
                    "Para rematrícula o aluno deve ter uma matrícula anterior neste curso."
                )

        # Validar duplicidade de matrícula ativa na mesma turma
        if aluno and turma:
            pk = self.instance.pk if self.instance else None
            duplicada = Matricula.objects.filter(
                aluno=aluno, turma=turma, status='ATIVA'
            ).exclude(pk=pk).exists()
            if duplicada:
                self.add_error("turma", "Este aluno já possui matrícula ativa nesta turma.")

        return cleaned_data


class DocumentoMatriculaForm(forms.ModelForm):
    """UC01 – include: Conferir Documentação"""

    class Meta:
        model = DocumentoMatricula
        fields = [
            "tipo_documento",
            "status",
            "data_recebimento",
            "data_validacao",
            "motivo_recusa",
            "arquivo",
            "observacao",
        ]
        labels = {
            "tipo_documento": "Tipo de Documento",
            "status": "Status",
            "data_recebimento": "Data de Recebimento",
            "data_validacao": "Data de Validação",
            "motivo_recusa": "Motivo da Recusa",
            "arquivo": "Arquivo",
            "observacao": "Observação",
        }
        widgets = {
            "data_recebimento": forms.DateInput(attrs={"type": "date"}),
            "data_validacao": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        data_recebimento = cleaned_data.get("data_recebimento")
        data_validacao = cleaned_data.get("data_validacao")
        motivo_recusa = cleaned_data.get("motivo_recusa")

        if status in {"RECEBIDO", "VALIDADO", "RECUSADO"} and not data_recebimento:
            self.add_error("data_recebimento", "Informe a data de recebimento.")

        if status == "VALIDADO" and not data_validacao:
            self.add_error("data_validacao", "Informe a data de validação.")

        if status == "RECUSADO" and not motivo_recusa:
            self.add_error("motivo_recusa", "Informe o motivo da recusa.")

        return cleaned_data


class PendenciaDocumentalForm(forms.ModelForm):
    """UC01 – extend: Abrir Pendência Documental"""

    class Meta:
        model = PendenciaDocumental
        fields = ["descricao", "status", "data_resolucao", "observacao"]
        labels = {
            "descricao": "Descrição da Pendência",
            "status": "Status",
            "data_resolucao": "Data de Resolução",
            "observacao": "Observação",
        }
        widgets = {
            "data_resolucao": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        data_resolucao = cleaned_data.get("data_resolucao")
        if status == 'RESOLVIDA' and not data_resolucao:
            self.add_error("data_resolucao", "Informe a data de resolução da pendência.")
        return cleaned_data


class DocumentoEmitidoForm(forms.ModelForm):
    """UC02 – Emitir Documentos"""

    class Meta:
        model = DocumentoEmitido
        fields = ["tipo", "observacao"]
        labels = {
            "tipo": "Tipo de Documento",
            "observacao": "Observação",
        }
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        # Guia de transferência só pode ser emitida para matrículas ativas ou trancadas
        if tipo == 'GUIA_TRANSFERENCIA':
            matricula = getattr(self, '_matricula', None)
            if matricula and matricula.status == 'CANCELADA':
                self.add_error("tipo", "Guia de Transferência não pode ser emitida para matrícula cancelada.")
        return cleaned_data


class ValidarDocumentoForm(forms.ModelForm):
    """UC02 – include: Assinar/Validar"""

    class Meta:
        model = DocumentoEmitido
        fields = ["validado", "data_validacao"]
        labels = {
            "validado": "Validado / Assinado",
            "data_validacao": "Data de Validação",
        }
        widgets = {
            "data_validacao": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("validado") and not cleaned_data.get("data_validacao"):
            self.add_error("data_validacao", "Informe a data de validação.")
        return cleaned_data


class EntregaDocumentoForm(forms.ModelForm):
    """UC02 – include: Registrar Entrega (Protocolo)"""

    class Meta:
        model = DocumentoEmitido
        fields = ["entregue", "data_entrega", "recebido_por"]
        labels = {
            "entregue": "Entregue",
            "data_entrega": "Data de Entrega",
            "recebido_por": "Recebido por",
        }
        widgets = {
            "data_entrega": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("entregue"):
            if not cleaned_data.get("data_entrega"):
                self.add_error("data_entrega", "Informe a data de entrega.")
            if not cleaned_data.get("recebido_por"):
                self.add_error("recebido_por", "Informe quem recebeu o documento.")
        return cleaned_data


class TransferenciaForm(forms.ModelForm):
    """UC03 – Transferência (Entrada/Saída)"""

    class Meta:
        model = Transferencia
        fields = ["tipo", "escola_origem", "escola_destino", "data_transferencia", "status", "numero_guia", "observacao"]
        labels = {
            "tipo": "Tipo",
            "escola_origem": "Escola de Origem",
            "escola_destino": "Escola de Destino",
            "data_transferencia": "Data da Transferência",
            "status": "Status",
            "numero_guia": "Nº da Guia",
            "observacao": "Observação",
        }
        widgets = {
            "data_transferencia": forms.DateInput(attrs={"type": "date"}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


class RegraAcademicaForm(forms.ModelForm):
    """UC04 – Configurar regra acadêmica local por curso"""

    class Meta:
        model = RegraAcademica
        fields = ["curso", "media_minima", "frequencia_minima"]
        labels = {
            "curso": "Curso",
            "media_minima": "Média Mínima",
            "frequencia_minima": "Frequência Mínima (%)",
        }


class ConsolidacaoObservacaoForm(forms.ModelForm):
    """UC04 – Editar situação/observação manualmente (ex.: Em Recuperação)"""

    class Meta:
        model = ConsolidacaoAcademica
        fields = ["situacao", "observacao"]
        labels = {
            "situacao": "Situação",
            "observacao": "Observação",
        }
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }


# ── P01 – Fluxo de Matrícula ─────────────────────────────────────────────────

class FluxoMatriculaIniciarForm(forms.ModelForm):
    """Etapa 1 – Receber Requerimento (Aluno → Secretaria)"""

    class Meta:
        model = FluxoMatricula
        fields = ["aluno", "tipo_matricula", "observacoes"]
        labels = {
            "aluno": "Aluno",
            "tipo_matricula": "Tipo de Matrícula",
            "observacoes": "Observações do Requerimento",
        }
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class FluxoEnturmarForm(forms.ModelForm):
    """Etapa 6 – Enturmar / Alocar Turno"""

    class Meta:
        model = Matricula
        fields = ["turma", "turno"]
        labels = {"turma": "Turma", "turno": "Turno"}


class PendenciaFluxoForm(forms.ModelForm):
    """Etapa 3 – Abrir Pendência com Prazo e Orientação ao Aluno"""

    class Meta:
        model = PendenciaDocumental
        fields = ["descricao", "prazo", "orientacao_aluno", "observacao"]
        labels = {
            "descricao": "Descrição da Pendência",
            "prazo": "Prazo para Regularização",
            "orientacao_aluno": "Orientação ao Aluno",
            "observacao": "Observação Interna",
        }
        widgets = {
            "prazo": forms.DateInput(attrs={"type": "date"}),
            "orientacao_aluno": forms.Textarea(attrs={"rows": 3}),
            "observacao": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("prazo"):
            self.add_error("prazo", "Informe o prazo para que o aluno regularize a documentação.")
        return cleaned_data


class EtapaObservacaoForm(forms.ModelForm):
    """Formulário genérico de observação para avançar etapas."""

    class Meta:
        model = EtapaFluxo
        fields = ["observacao"]
        labels = {"observacao": "Observação"}
        widgets = {"observacao": forms.Textarea(attrs={"rows": 2})}


# ── P02 – Fluxo de Emissão de Histórico/Declaração ───────────────────────────

class FluxoEmissaoIniciarForm(forms.ModelForm):
    """Etapa 1 – Abrir Protocolo (P02)"""

    class Meta:
        model = FluxoEmissaoDocumento
        fields = ["solicitante", "matricula", "tipo_documento", "observacoes"]
        labels = {
            "solicitante": "Solicitante",
            "matricula": "Matrícula",
            "tipo_documento": "Tipo de Documento",
            "observacoes": "Observações da Solicitação",
        }
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}

    def clean(self):
        cleaned_data = super().clean()
        solicitante = cleaned_data.get("solicitante")
        matricula = cleaned_data.get("matricula")
        if solicitante and matricula and matricula.aluno != solicitante:
            self.add_error("matricula", "A matrícula selecionada não pertence ao solicitante informado.")
        return cleaned_data


class ValidarEntregaP02Form(forms.ModelForm):
    """Etapa 5 – Registrar Entrega no P02 (reutiliza EntregaDocumentoForm via instância)"""

    class Meta:
        model = DocumentoEmitido
        fields = ["entregue", "data_entrega", "recebido_por"]
        labels = {
            "entregue": "Entregue",
            "data_entrega": "Data de Entrega",
            "recebido_por": "Recebido por",
        }
        widgets = {"data_entrega": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("entregue"):
            if not cleaned_data.get("data_entrega"):
                self.add_error("data_entrega", "Informe a data de entrega.")
            if not cleaned_data.get("recebido_por"):
                self.add_error("recebido_por", "Informe quem recebeu o documento.")
        return cleaned_data


class EtapaEmissaoObservacaoForm(forms.ModelForm):
    """Formulário genérico de observação para avançar etapas do P02."""

    class Meta:
        model = EtapaFluxoEmissao
        fields = ["observacao"]
        labels = {"observacao": "Observação"}
        widgets = {"observacao": forms.Textarea(attrs={"rows": 2})}


# ── P03 – Fluxo de Transferência ─────────────────────────────────────────────

class FluxoTransferenciaIniciarForm(forms.ModelForm):
    """Etapa 1 – Solicitação: seleciona a matrícula e dados iniciais."""

    class Meta:
        model = FluxoTransferencia
        fields = ["matricula", "observacoes"]
        labels = {
            "matricula": "Matrícula",
            "observacoes": "Observações da Solicitação",
        }
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}


class TransferenciaFluxoForm(forms.ModelForm):
    """Etapa 1 – Dados da transferência (tipo, escola origem/destino)."""

    class Meta:
        model = Transferencia
        fields = ["tipo", "escola_origem", "escola_destino", "observacao"]
        labels = {
            "tipo": "Tipo de Transferência",
            "escola_origem": "Escola de Origem",
            "escola_destino": "Escola de Destino",
            "observacao": "Observação",
        }
        widgets = {"observacao": forms.Textarea(attrs={"rows": 2})}


class EtapaTransferenciaObservacaoForm(forms.ModelForm):
    """Formulário genérico de observação para avançar etapas do P03."""

    class Meta:
        model = EtapaFluxoTransferencia
        fields = ["observacao"]
        labels = {"observacao": "Observação"}
        widgets = {"observacao": forms.Textarea(attrs={"rows": 2})}
