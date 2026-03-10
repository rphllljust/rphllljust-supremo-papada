from rest_framework import serializers

from apps.cursos.models import Curso


class CursoSerializer(serializers.ModelSerializer):
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)

    class Meta:
        model = Curso
        fields = [
            "id",
            "nome",
            "sigla",
            "unidade",
            "unidade_nome",
            "eixo_tecnologico",
            "carga_horaria",
        ]