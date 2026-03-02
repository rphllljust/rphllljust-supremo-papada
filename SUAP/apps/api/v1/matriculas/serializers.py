from rest_framework import serializers
from apps.matriculas.models import Matricula

class MatriculaSerializer(serializers.ModelSerializer):
    aluno_username = serializers.CharField(source="aluno.username", read_only=True)
    turma_nome = serializers.CharField(source="turma.nome", read_only=True)

    class Meta:
        model = Matricula
        fields = [
            "id",
            "aluno",
            "aluno_username",
            "turma",
            "turma_nome",
            "data_matricula",
            "status",
        ]
        read_only_fields = ["data_matricula"]