from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.matriculas.models import Transferencia

from .serializers import TransferenciaSerializer


class TransferenciaListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TransferenciaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Transferencia.objects.select_related("matricula__aluno__pessoa").order_by("-data_solicitacao", "-id")
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(numero_guia__icontains=search)
                | Q(escola_origem__icontains=search)
                | Q(escola_destino__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
            )
        return queryset.distinct()