from rest_framework import serializers

from apps.agenda.models import EventoAgenda


class EventoAgendaSerializer(serializers.ModelSerializer):
    turma_nome = serializers.CharField(source="turma.nome", read_only=True)
    curso_nome = serializers.CharField(source="turma.curso.nome", read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EventoAgenda
        fields = [
            "id",
            "titulo",
            "descricao",
            "turma",
            "turma_nome",
            "curso_nome",
            "professor_nome",
            "inicio",
            "fim",
        ]

    def get_professor_nome(self, obj):
        professor = obj.turma.professor_responsavel
        if not professor:
            return None

        full_name = professor.get_full_name().strip()
        return full_name or professor.username