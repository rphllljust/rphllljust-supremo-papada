from rest_framework import serializers

from apps.documentos.models import GuiaTransferencia


class GuiaTransferenciaSerializer(serializers.ModelSerializer):
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    emitido_por_nome = serializers.SerializerMethodField(read_only=True)
    transferencia_label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = GuiaTransferencia
        fields = [
            "id",
            "numero_protocolo",
            "data_emissao",
            "assunto",
            "matricula",
            "matricula_numero",
            "aluno_nome",
            "escola_origem",
            "escola_destino",
            "transferencia",
            "transferencia_label",
            "observacao",
            "emitido_por",
            "emitido_por_nome",
        ]
        read_only_fields = ["numero_protocolo", "data_emissao", "emitido_por", "emitido_por_nome"]

    def get_aluno_nome(self, obj):
        if not obj.matricula_id:
            return ""
        aluno = obj.matricula.aluno
        if getattr(aluno, "pessoa", None) and aluno.pessoa.nome_completo:
            return aluno.pessoa.nome_completo
        full_name = aluno.get_full_name().strip()
        return full_name or aluno.username

    def get_emitido_por_nome(self, obj):
        if not obj.emitido_por:
            return ""
        if getattr(obj.emitido_por, "pessoa", None) and obj.emitido_por.pessoa.nome_completo:
            return obj.emitido_por.pessoa.nome_completo
        full_name = obj.emitido_por.get_full_name().strip()
        return full_name or obj.emitido_por.username

    def get_transferencia_label(self, obj):
        return str(obj.transferencia) if obj.transferencia else ""

    def create(self, validated_data):
        validated_data["emitido_por"] = self.context["request"].user
        return super().create(validated_data)