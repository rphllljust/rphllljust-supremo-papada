from rest_framework import serializers

from apps.pedagogia.models import AtendimentoPedagogico
from apps.usuarios.models import PerfilUsuario


class AtendimentoPedagogicoSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    pedagogia_responsavel_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AtendimentoPedagogico
        fields = [
            "id",
            "aluno",
            "aluno_nome",
            "pedagogia_responsavel",
            "pedagogia_responsavel_nome",
            "data_atendimento",
            "diagnostico",
            "plano_acao",
            "status",
            "status_display",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]

    def validate_aluno(self, value):
        if value.tipo != PerfilUsuario.ALUNO:
            raise serializers.ValidationError("Selecione um usuario com perfil de aluno.")
        return value

    def validate(self, attrs):
        responsavel = attrs.get("pedagogia_responsavel", getattr(self.instance, "pedagogia_responsavel", None))
        if responsavel is None:
            raise serializers.ValidationError({"pedagogia_responsavel": "Informe a pedagogia responsavel."})
        return attrs

    def validate_pedagogia_responsavel(self, value):
        if value.tipo == PerfilUsuario.ALUNO:
            raise serializers.ValidationError("O responsavel pedagogico nao pode possuir perfil de aluno.")
        return value

    def get_aluno_nome(self, obj):
        if getattr(obj.aluno, "pessoa", None) and obj.aluno.pessoa.nome_completo:
            return obj.aluno.pessoa.nome_completo

        full_name = obj.aluno.get_full_name().strip()
        return full_name or obj.aluno.username

    def get_pedagogia_responsavel_nome(self, obj):
        if not obj.pedagogia_responsavel:
            return ""

        if getattr(obj.pedagogia_responsavel, "pessoa", None) and obj.pedagogia_responsavel.pessoa.nome_completo:
            return obj.pedagogia_responsavel.pessoa.nome_completo

        full_name = obj.pedagogia_responsavel.get_full_name().strip()
        return full_name or obj.pedagogia_responsavel.username
