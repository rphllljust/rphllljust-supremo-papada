from django.db.models import Q
from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.setores.models import Setor

from .serializers import SetorSerializer


class SetorViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "setores"
    access_surface = "api"
    serializer_class = SetorSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Setor.objects.select_related("setor_superior").order_by("nome", "codigo")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        ativo = self.request.query_params.get("ativo", "").strip().lower()

        if ativo in {"true", "false"}:
            queryset = queryset.filter(ativo=(ativo == "true"))

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(sigla__icontains=search)
                | Q(codigo__icontains=search)
                | Q(setor_superior__nome__icontains=search)
            )

        return queryset.distinct()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()