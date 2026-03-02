from rest_framework import serializers
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        # ajuste os campos conforme seu model (cpf, tipo, etc.)
        fields = ["id", "username", "first_name", "last_name", "email", "cpf", "tipo"]