from rest_framework import serializers
from apps.turmas.models import Turma


class TurmaSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    curso_sigla = serializers.CharField(source="curso.sigla", read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    total_alunos = serializers.IntegerField(read_only=True)
    total_diarios = serializers.IntegerField(read_only=True)

    class Meta:
        model = Turma
        fields = [
            "id",
            "nome",
            "ano_letivo",
            "status",
            "status_display",
            "curso",
            "curso_nome",
            "curso_sigla",
            "professor_responsavel",
            "professor_nome",
            "total_alunos",
            "total_diarios",
        ]

    def get_professor_nome(self, obj):
        if obj.professor_responsavel:
            return f"{obj.professor_responsavel.first_name} {obj.professor_responsavel.last_name}".strip()
        return None