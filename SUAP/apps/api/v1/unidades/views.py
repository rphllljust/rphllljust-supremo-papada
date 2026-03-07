from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
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