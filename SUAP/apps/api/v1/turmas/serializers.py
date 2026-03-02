from rest_framework import serializers
from apps.turmas.models import Turma

class TurmaSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Turma
        fields = [
            "id",
            "nome",
            "ano_letivo",
            "curso",
            "curso_nome",
            "professor_responsavel",
            "professor_nome",
        ]

    def get_professor_nome(self, obj):
        if obj.professor_responsavel:
            return f"{obj.professor_responsavel.first_name} {obj.professor_responsavel.last_name}".strip()
        return None