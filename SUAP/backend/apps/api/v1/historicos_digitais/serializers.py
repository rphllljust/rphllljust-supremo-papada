from rest_framework import serializers

from apps.documentos.models import HistoricoEscolarDigital
from apps.documentos.services.issuance import EmissaoHistoricoDigitalInput


class HistoricoEscolarDigitalSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source="get_tipo_documento_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    historico_protocolo = serializers.CharField(source="historico.numero_protocolo", read_only=True)
    matricula_numero = serializers.CharField(source="historico.matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    emitido_por_nome = serializers.SerializerMethodField(read_only=True)
    pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HistoricoEscolarDigital
        fields = [
            "id",
            "historico",
            "historico_protocolo",
            "tipo_documento",
            "tipo_documento_display",
            "status",
            "status_display",
            "versao",
            "numero_unico",
            "hash_documento",
            "chave_autenticacao",
            "matricula_numero",
            "aluno_nome",
            "validacao_xsd_ok",
            "validacao_xsd_erros",
            "assinado_digitalmente",
            "assinatura_metadados",
            "qr_payload_url",
            "qr_code_data_uri",
            "pdf_url",
            "revogado",
            "motivo_revogacao",
            "referencia_original",
            "emitido_por",
            "emitido_por_nome",
            "emitido_em",
            "atualizado_em",
        ]
        read_only_fields = fields

    def get_aluno_nome(self, obj):
        matricula = getattr(obj.historico, "matricula", None)
        aluno = getattr(matricula, "aluno", None) if matricula else None
        if not aluno:
            return ""
        pessoa = getattr(aluno, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return aluno.get_full_name().strip() or aluno.username

    def get_emitido_por_nome(self, obj):
        emitido_por = obj.emitido_por
        if not emitido_por:
            return ""
        pessoa = getattr(emitido_por, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return emitido_por.get_full_name().strip() or emitido_por.username

    def get_pdf_url(self, obj):
        if not obj.pdf_arquivo:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.pdf_arquivo.url)
        return obj.pdf_arquivo.url


class EmitirHistoricoDigitalSerializer(serializers.Serializer):
    tipo_documento = serializers.ChoiceField(choices=HistoricoEscolarDigital.TIPO_DOCUMENTO_CHOICES)
    assinar_xml = serializers.BooleanField(default=False)
    forcar_reemissao = serializers.BooleanField(default=False)
    referencia_original_id = serializers.IntegerField(required=False, allow_null=True)

    def to_input(self) -> EmissaoHistoricoDigitalInput:
        data = self.validated_data
        return EmissaoHistoricoDigitalInput(
            tipo_documento=data["tipo_documento"],
            assinar_xml=data.get("assinar_xml", False),
            forcar_reemissao=data.get("forcar_reemissao", False),
            referencia_original_id=data.get("referencia_original_id"),
        )


class RevogarHistoricoDigitalSerializer(serializers.Serializer):
    motivo_revogacao = serializers.CharField(min_length=5, max_length=500)
