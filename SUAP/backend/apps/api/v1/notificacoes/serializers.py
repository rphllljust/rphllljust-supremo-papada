from rest_framework import serializers

from apps.notificacoes.models import Notificacao, PreferenciaNotificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    categoria_slug = serializers.CharField(source="categoria.slug", read_only=True)
    categoria_titulo = serializers.CharField(source="categoria.titulo", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    is_unread = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Notificacao
        fields = [
            "id",
            "titulo",
            "resumo",
            "mensagem",
            "tipo",
            "tipo_display",
            "categoria_slug",
            "categoria_titulo",
            "link",
            "link_label",
            "via_suap",
            "via_email",
            "data_evento",
            "lida_em",
            "is_unread",
            "metadados",
        ]

    def get_is_unread(self, obj):
        return obj.is_unread


class PreferenciaNotificacaoSerializer(serializers.ModelSerializer):
    categoria_slug = serializers.CharField(source="categoria.slug", read_only=True)
    categoria_titulo = serializers.CharField(source="categoria.titulo", read_only=True)
    categoria_descricao = serializers.CharField(source="categoria.descricao", read_only=True)

    class Meta:
        model = PreferenciaNotificacao
        fields = [
            "id",
            "categoria",
            "categoria_slug",
            "categoria_titulo",
            "categoria_descricao",
            "via_suap",
            "via_email",
            "atualizado_em",
        ]
        read_only_fields = ["categoria", "categoria_slug", "categoria_titulo", "categoria_descricao", "atualizado_em"]
