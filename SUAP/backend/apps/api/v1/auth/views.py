from django.conf import settings
from django.contrib.auth import logout
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.access.policies import build_access_context

from .serializers import LogoutSerializer, PerfilTokenObtainPairSerializer


class PerfilTokenObtainPairView(TokenObtainPairView):
    serializer_class = PerfilTokenObtainPairSerializer


class PerfilTokenRefreshView(TokenRefreshView):
    pass


class AuthLogoutApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logout(request)
        return Response({"detail": "Refresh token invalidado com sucesso."})


class AuthMeApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        access_context = build_access_context(user)
        return Response(
            {
                "id": user.id,
                "cpf": user.cpf,
                "perfil": user.tipo,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "access_context": access_context,
            }
        )
