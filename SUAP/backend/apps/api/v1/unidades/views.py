from django.db.models import Q
from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.unidades.models import Unidade
from .serializers import UnidadeSerializer


class UnidadeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet padrão para o modelo Unidade.
    Garante atributos `queryset` e `serializer_class` necessários ao DefaultRouter.
    """
    permission_classes = [CanAccessModule]
    module_name = "unidades"
    access_surface = "api"
    access_action = "view"
    queryset = Unidade.objects.all().order_by("nome")
    serializer_class = UnidadeSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | Q(codigo__icontains=search)
            )

        return queryset