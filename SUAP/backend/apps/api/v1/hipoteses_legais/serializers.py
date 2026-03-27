from rest_framework import serializers

from apps.processos.models import HipoteseLegal


class HipoteseLegalSerializer(serializers.ModelSerializer):
    nivel_acesso_display = serializers.CharField(source="get_nivel_acesso_display", read_only=True)

    class Meta:
        model = HipoteseLegal
        fields = [
            "id",
            "descricao",
            "base_legal",
            "nivel_acesso",
            "nivel_acesso_display",
            "ativo",
            "data_criacao",
            "data_atualizacao",
        ]
        read_only_fields = ["data_criacao", "data_atualizacao"]
