from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.processos.models import Processo

from .serializers import ProcessoSerializer


class ProcessoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "processos"
    access_surface = "api"
    access_action = "view"
    serializer_class = ProcessoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Processo.objects.select_related("requerente__pessoa").order_by("-data_abertura", "-id")
        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search)
                | Q(assunto__icontains=search)
                | Q(descricao__icontains=search)
                | Q(requerente__username__icontains=search)
                | Q(requerente__first_name__icontains=search)
                | Q(requerente__last_name__icontains=search)
                | Q(requerente__pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()


class ProcessoDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "processos"
    access_surface = "api"
    access_action = "view"
    serializer_class = ProcessoSerializer
    queryset = Processo.objects.select_related("requerente__pessoa")