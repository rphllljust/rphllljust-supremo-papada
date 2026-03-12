from rest_framework import serializers

from apps.arquivo.models import GuardaDocumental


class GuardaDocumentalSerializer(serializers.ModelSerializer):
    tipo_documento_display = serializers.CharField(source="get_tipo_documento_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    responsavel_nome = serializers.SerializerMethodField(read_only=True)
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    processo_numero = serializers.CharField(source="processo.numero", read_only=True)

    class Meta:
        model = GuardaDocumental
        fields = [
            "id",
            "numero_registro",
            "tipo_documento",
            "tipo_documento_display",
            "descricao",
            "numero_caixa",
            "localizacao",
            "data_arquivamento",
            "data_eliminacao_prevista",
            "status",
            "status_display",
            "plano_classificacao",
            "responsavel",
            "responsavel_nome",
            "matricula",
            "matricula_numero",
            "processo",
            "processo_numero",
        ]
        read_only_fields = ["numero_registro", "data_arquivamento", "responsavel"]

    def get_responsavel_nome(self, obj):
        if not obj.responsavel:
            return None

        full_name = obj.responsavel.get_full_name().strip()
        return full_name or obj.responsavel.username
