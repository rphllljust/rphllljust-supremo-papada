from rest_framework import serializers

from apps.inscricoes.models import Inscricao


class InscricaoSerializer(serializers.ModelSerializer):
    publicacao_titulo = serializers.CharField(source="publicacao.titulo", read_only=True)
    curso_nome = serializers.CharField(source="publicacao.curso.nome", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    usuario_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Inscricao
        fields = [
            "id",
            "publicacao",
            "publicacao_titulo",
            "curso_nome",
            "nome_candidato",
            "cpf",
            "email",
            "telefone",
            "data_nascimento",
            "status",
            "status_display",
            "data_inscricao",
            "numero_inscricao",
            "observacao",
            "usuario",
            "usuario_nome",
        ]
        read_only_fields = ["data_inscricao", "numero_inscricao", "usuario"]

    def get_usuario_nome(self, obj):
        if not obj.usuario:
            return None

        full_name = obj.usuario.get_full_name().strip()
        return full_name or obj.usuario.username
