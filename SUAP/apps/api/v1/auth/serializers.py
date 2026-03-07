from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.services import authenticate_user_by_cpf_profile
from apps.accounts.utils import normalize_cpf
from apps.usuarios.models import PerfilUsuario


class PerfilTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = "cpf"

    cpf = serializers.CharField(max_length=14)
    perfil = serializers.ChoiceField(choices=PerfilUsuario.autenticaveis_choices())
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "invalid_credentials": "Nao foi possivel autenticar com as credenciais informadas.",
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["cpf"] = user.cpf
        token["perfil"] = user.tipo
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        return token

    def validate(self, attrs):
        try:
            cpf = normalize_cpf(attrs.get("cpf", ""))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"cpf": list(exc.messages)}) from exc

        perfil = attrs.get("perfil")
        password = attrs.get("password")

        try:
            self.user = authenticate_user_by_cpf_profile(cpf=cpf, password=password, perfil=perfil)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"detail": list(exc.messages)}) from exc

        refresh = self.get_token(self.user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": self.user.id,
                "cpf": self.user.cpf,
                "perfil": self.user.tipo,
                "username": self.user.username,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
            },
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {
        "invalid_token": "Refresh token invalido ou expirado.",
    }

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except TokenError as exc:
            self.fail("invalid_token")
