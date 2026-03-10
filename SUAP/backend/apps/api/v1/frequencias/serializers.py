from rest_framework import serializers

from apps.frequencia.models import Frequencia


class FrequenciaSerializer(serializers.ModelSerializer):
    numero_matricula = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    curso_nome = serializers.CharField(source="matricula.curso.nome", read_only=True)
    turma_nome = serializers.CharField(source="matricula.turma.nome", read_only=True)
    presente_label = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Frequencia
        fields = [
            "id",
            "matricula",
            "numero_matricula",
            "aluno_nome",
            "curso_nome",
            "turma_nome",
            "data",
            "presente",
            "presente_label",
            "observacao",
        ]

    def get_aluno_nome(self, obj):
        aluno = obj.matricula.aluno
        if getattr(aluno, "pessoa", None) and aluno.pessoa.nome_completo:
            return aluno.pessoa.nome_completo

        full_name = aluno.get_full_name().strip()
        return full_name or aluno.username

    def get_presente_label(self, obj):
        return "Presente" if obj.presente else "Falta"