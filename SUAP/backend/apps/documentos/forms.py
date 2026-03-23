import json
from datetime import datetime

from django import forms
from django.core.exceptions import ValidationError

from .models import AtaOficioMemorando, AtaAnexo, Declaracao, GuiaTransferencia, HistoricoEscolar


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

    participantes_json = forms.CharField(required=False, widget=forms.HiddenInput())
    pauta_json = forms.CharField(required=False, widget=forms.HiddenInput())
    deliberacoes_json = forms.CharField(required=False, widget=forms.HiddenInput())
    encaminhamentos_json = forms.CharField(required=False, widget=forms.HiddenInput())
    anexos_json = forms.CharField(required=False, widget=forms.HiddenInput())
    assinaturas_json = forms.CharField(required=False, widget=forms.HiddenInput())
    acao = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = AtaOficioMemorando
        fields = [
            "tipo",
            "numero_ata",
            "ano",
            "tipo_reuniao_registro",
            "tipo_reuniao_outro",
            "livro",
            "folha_pagina",
            "processo",
            "data_reuniao",
            "horario_inicio",
            "horario_termino",
            "local_reuniao",
            "modalidade",
            "plataforma",
            "link_reuniao",
            "cidade_uf",
            "presidente_reuniao",
            "responsavel_lavratura",
            "horario_encerramento",
            "texto_final",
            "forma_assinatura",
            "assunto",
            "observacao",
        ]
        labels = {
            "tipo": "Tipo do Documento",
            "numero_ata": "Número da Ata",
            "ano": "Ano",
            "tipo_reuniao_registro": "Tipo de Reunião/Registro",
            "tipo_reuniao_outro": "Outro Tipo de Reunião",
            "livro": "Livro",
            "folha_pagina": "Folha/Página",
            "processo": "Processo Vinculado",
            "data_reuniao": "Data",
            "horario_inicio": "Horário de Início",
            "horario_termino": "Horário de Término",
            "local_reuniao": "Local",
            "modalidade": "Modalidade",
            "plataforma": "Plataforma",
            "link_reuniao": "Link da Reunião",
            "cidade_uf": "Cidade/UF",
            "presidente_reuniao": "Presidente/Coordenador(a)",
            "responsavel_lavratura": "Responsável pela Lavratura",
            "horario_encerramento": "Horário de Encerramento",
            "texto_final": "Texto final padrão da ata",
            "forma_assinatura": "Forma de assinatura",
            "assunto": "Assunto/Título",
            "observacao": "Observações internas",
        }
        widgets = {
            "tipo": forms.Select(attrs={"readonly": "readonly"}),
            "numero_ata": forms.TextInput(attrs={"placeholder": "000/ANO"}),
            "data_reuniao": forms.DateInput(attrs={"type": "date"}),
            "horario_inicio": forms.TimeInput(attrs={"type": "time"}),
            "horario_termino": forms.TimeInput(attrs={"type": "time"}),
            "horario_encerramento": forms.TimeInput(attrs={"type": "time"}),
            "link_reuniao": forms.URLInput(attrs={"placeholder": "https://"}),
            "texto_final": forms.Textarea(attrs={"rows": 4}),
            "observacao": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].initial = "ATA"
        self.fields["tipo"].disabled = True
        self.fields["ano"].initial = self.instance.ano or datetime.now().year

        if not self.instance.pk:
            self.fields["numero_ata"].initial = self.instance.gerar_numero_ata()

        if not self.instance.texto_final:
            self.fields["texto_final"].initial = self._texto_final_padrao()

        for name, field in self.fields.items():
            current_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (current_class + " ata-input").strip()

    def _parse_json_list(self, field_name):
        raw = self.cleaned_data.get(field_name) or "[]"
        try:
            value = json.loads(raw)
            return value if isinstance(value, list) else []
        except json.JSONDecodeError:
            raise ValidationError(f"Dados inválidos em {field_name}.")

    def _texto_final_padrao(self):
        return (
            "Nada mais havendo a tratar, deu-se por encerrada a reunião. "
            "Eu, [responsável], lavrei a presente ata, que após lida e aprovada, "
            "segue assinada eletronicamente pelos participantes."
        )

    def _validar_dinamicos_obrigatorios(self, participantes, pauta, deliberacoes, assinaturas):
        if not participantes:
            self.add_error(None, "Adicione ao menos um participante.")
        if not pauta:
            self.add_error(None, "Adicione ao menos um item de pauta.")
        if not deliberacoes:
            self.add_error(None, "Informe pelo menos uma deliberação.")
        if not assinaturas:
            self.add_error(None, "Inclua ao menos uma assinatura.")

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data["tipo"] = "ATA"

        modalidade = cleaned_data.get("modalidade")
        plataforma = (cleaned_data.get("plataforma") or "").strip()
        tipo_reuniao = cleaned_data.get("tipo_reuniao_registro")
        tipo_outro = (cleaned_data.get("tipo_reuniao_outro") or "").strip()

        horario_inicio = cleaned_data.get("horario_inicio")
        horario_termino = cleaned_data.get("horario_termino")
        horario_encerramento = cleaned_data.get("horario_encerramento")

        if horario_inicio and horario_termino and horario_termino < horario_inicio:
            self.add_error("horario_termino", "O horário de término não pode ser menor que o horário de início.")

        if horario_inicio and horario_encerramento and horario_encerramento < horario_inicio:
            self.add_error("horario_encerramento", "O horário de encerramento não pode ser menor que o horário de início.")

        if modalidade in {"ONLINE", "HIBRIDA"} and not plataforma:
            self.add_error("plataforma", "Informe a plataforma para reuniões online ou híbridas.")

        if tipo_reuniao == "OUTRO" and not tipo_outro:
            self.add_error("tipo_reuniao_outro", "Informe o tipo de reunião quando selecionar 'Outro'.")

        participantes = self._parse_json_list("participantes_json")
        pauta = self._parse_json_list("pauta_json")
        deliberacoes = self._parse_json_list("deliberacoes_json")
        encaminhamentos = self._parse_json_list("encaminhamentos_json")
        anexos = self._parse_json_list("anexos_json")
        assinaturas = self._parse_json_list("assinaturas_json")

        cleaned_data["participantes"] = participantes
        cleaned_data["pauta"] = pauta
        cleaned_data["deliberacoes"] = deliberacoes
        cleaned_data["encaminhamentos"] = encaminhamentos
        cleaned_data["anexos"] = anexos
        cleaned_data["assinaturas"] = assinaturas

        acao = cleaned_data.get("acao")
        if acao == "emitir":
            campos_obrigatorios = [
                "numero_ata",
                "ano",
                "tipo_reuniao_registro",
                "data_reuniao",
                "horario_inicio",
                "local_reuniao",
                "modalidade",
                "cidade_uf",
                "presidente_reuniao",
                "responsavel_lavratura",
            ]
            for campo in campos_obrigatorios:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Campo obrigatório para emissão da ata.")
            self._validar_dinamicos_obrigatorios(participantes, pauta, deliberacoes, assinaturas)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.tipo = "ATA"
        instance.participantes = self.cleaned_data.get("participantes", [])
        instance.pauta = self.cleaned_data.get("pauta", [])
        instance.deliberacoes = self.cleaned_data.get("deliberacoes", [])
        instance.encaminhamentos = self.cleaned_data.get("encaminhamentos", [])
        instance.assinaturas = self.cleaned_data.get("assinaturas", [])
        if not instance.texto_final:
            instance.texto_final = self._texto_final_padrao()
        if commit:
            instance.save()
        return instance


class AtaAnexoUploadForm(forms.ModelForm):
    class Meta:
        model = AtaAnexo
        fields = ["tipo_anexo", "descricao", "arquivo"]


class ConsultaCodigoValidacaoForm(forms.Form):
    codigo_validacao = forms.CharField(
        label="C\u00f3digo de valida\u00e7\u00e3o",
        max_length=60,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex.: HE-IDEPRO-2023-00001",
                "autocomplete": "off",
            }
        ),
    )

    def clean_codigo_validacao(self):
        return self.cleaned_data["codigo_validacao"].strip().upper()
