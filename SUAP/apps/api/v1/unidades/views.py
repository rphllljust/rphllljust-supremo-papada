# python
# File: apps/api/v1/unidades/views.py
from rest_framework import viewsets

from apps.unidades.models import Unidade
from .serializers import UnidadeSerializer


class UnidadeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet padrão para o modelo Unidade.
    Garante atributos `queryset` e `serializer_class` necessários ao DefaultRouter.
    """
    queryset = Unidade.objects.all().order_by("nome")
    serializer_class = UnidadeSerializer