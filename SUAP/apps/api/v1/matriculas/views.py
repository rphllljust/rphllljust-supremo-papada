from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule


class MatriculaListApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"

    def get(self, request):
        return Response({"message": "Lista de matriculas (exemplo)"})


class MatriculaDetailApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk):
        return Response({"message": f"Detalhe da matricula {pk} (exemplo)"})
