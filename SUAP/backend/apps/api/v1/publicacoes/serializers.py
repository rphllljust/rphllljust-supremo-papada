from rest_framework import serializers

from apps.inscricoes.models import PublicacaoInscricao


class PublicacaoInscricaoSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modalidade_ingresso_display = serializers.CharField(source="get_modalidade_ingresso_display", read_only=True)
    publicado_por_nome = serializers.SerializerMethodField(read_only=True)
    inscricoes_count = serializers.IntegerField(source="inscricoes.count", read_only=True)

    class Meta:
        model = PublicacaoInscricao
        fields = [
            "id",
            "curso",
            "curso_nome",
            "codigo_edital",
            "titulo",
            "descricao",
            "vagas",
            "modalidade_ingresso",
            "modalidade_ingresso_display",
            "nota_corte",
            "usa_cotas_lei_12711",
            "data_inicio",
            "data_fim",
            "status",
            "status_display",
            "publicado_por",
            "publicado_por_nome",
            "inscricoes_count",
        ]
        read_only_fields = ["publicado_por"]

    def get_publicado_por_nome(self, obj):
        if not obj.publicado_por:
            return None

        full_name = obj.publicado_por.get_full_name().strip()
        return full_name or obj.publicado_por.username
