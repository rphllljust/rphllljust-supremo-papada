from rest_framework import serializers

from apps.processos.models import Processo


class ProcessoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    requerente_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Processo
        fields = [
            "id",
            "numero",
            "tipo",
            "tipo_display",
            "assunto",
            "descricao",
            "status",
            "status_display",
            "data_abertura",
            "data_conclusao",
            "requerente",
            "requerente_nome",
        ]

    def get_requerente_nome(self, obj):
        if not obj.requerente:
            return ""

        if getattr(obj.requerente, "pessoa", None) and obj.requerente.pessoa.nome_completo:
            return obj.requerente.pessoa.nome_completo

        full_name = obj.requerente.get_full_name().strip()
        return full_name or obj.requerente.username