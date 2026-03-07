
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule


class UsuarioListApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "usuarios"
    access_surface = "api"
    access_action = "view"

    def get(self, request):
        return Response({"message": "Lista de usuarios (exemplo)"})


class UsuarioDetailApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "usuarios"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk):
        return Response({"message": f"Detalhe do usuario {pk} (exemplo)"})