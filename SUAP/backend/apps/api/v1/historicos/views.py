from django.db.models import Q
from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.documentos.models import HistoricoEscolar

from .serializers import HistoricoEscolarSerializer


class HistoricoEscolarViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    serializer_class = HistoricoEscolarSerializer
    pagination_class = StandardResultsSetPagination
    queryset = HistoricoEscolar.objects.select_related("matricula__aluno__pessoa", "emitido_por__pessoa").order_by("-data_emissao", "-id")

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(numero_protocolo__icontains=search)
                | Q(assunto__icontains=search)
                | Q(periodo_ref__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
            )
        return queryset.distinct()