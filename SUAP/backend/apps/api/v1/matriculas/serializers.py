from rest_framework import serializers
from apps.matriculas.models import Matricula


class MatriculaSerializer(serializers.ModelSerializer):
    aluno_username = serializers.CharField(source="aluno.username", read_only=True)
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    turma_nome = serializers.CharField(source="turma.nome", read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)
    periodo = serializers.SerializerMethodField(read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tipo_matricula_display = serializers.CharField(source="get_tipo_matricula_display", read_only=True)
    turno_display = serializers.CharField(source="get_turno_display", read_only=True)
    situacao_academica = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Matricula
        fields = [
            "id",
            "numero_matricula",
            "aluno",
            "aluno_nome",
            "aluno_username",
            "curso",
            "curso_nome",
            "turma",
            "turma_nome",
            "professor_nome",
            "periodo",
            "data_matricula",
            "status",
            "status_display",
            "tipo_matricula",
            "tipo_matricula_display",
            "turno",
            "turno_display",
            "situacao_academica",
        ]
        read_only_fields = ["data_matricula"]

    def get_aluno_nome(self, obj):
        if getattr(obj.aluno, "pessoa", None) and obj.aluno.pessoa.nome_completo:
            return obj.aluno.pessoa.nome_completo

        full_name = obj.aluno.get_full_name().strip()
        return full_name or obj.aluno.username

    def get_professor_nome(self, obj):
        professor = getattr(obj.turma, "professor_responsavel", None)
        if not professor:
            return None
        full_name = professor.get_full_name().strip()
        return full_name or professor.username

    def get_periodo(self, obj):
        diario = obj.turma.diarios.order_by("-id").first()
        if diario and diario.periodo:
            return diario.periodo
        return str(obj.turma.ano_letivo)

    def get_situacao_academica(self, obj):
        consolidacao = getattr(obj, "consolidacao", None)
        if consolidacao:
            return consolidacao.get_situacao_display()
        return obj.get_status_display()
