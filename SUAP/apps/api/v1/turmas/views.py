from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule


class TurmaListApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "turmas"
    access_surface = "api"
    access_action = "view"

    def get(self, request):
        return Response({"message": "Lista de turmas (exemplo)"})


class TurmaDetailApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "turmas"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk):
        return Response({"message": f"Detalhe da turma {pk} (exemplo)"})
