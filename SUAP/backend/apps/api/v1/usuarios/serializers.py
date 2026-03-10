from rest_framework import serializers
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "nome_completo",
            "email",
            "cpf",
            "tipo",
            "tipo_display",
            "is_active",
        ]

    def get_nome_completo(self, obj):
        if getattr(obj, "pessoa", None) and obj.pessoa.nome_completo:
            return obj.pessoa.nome_completo

        full_name = obj.get_full_name().strip()
        return full_name or obj.username