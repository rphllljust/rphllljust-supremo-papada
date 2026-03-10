from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import CanExportToAva


class AvaExportPreviewView(APIView):
    permission_classes = [CanExportToAva]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "detail": "Permissao de exportacao para o AVA validada.",
                "usuario": request.user.username,
            }
        )
