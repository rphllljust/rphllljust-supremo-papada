from rest_framework import serializers

from apps.matriculas.models import Transferencia


class TransferenciaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transferencia
        fields = [
            "id",
            "matricula",
            "matricula_numero",
            "aluno_nome",
            "tipo",
            "tipo_display",
            "status",
            "status_display",
            "numero_guia",
            "escola_origem",
            "escola_destino",
        ]

    def get_aluno_nome(self, obj):
        aluno = obj.matricula.aluno
        if getattr(aluno, "pessoa", None) and aluno.pessoa.nome_completo:
            return aluno.pessoa.nome_completo
        full_name = aluno.get_full_name().strip()
        return full_name or aluno.username