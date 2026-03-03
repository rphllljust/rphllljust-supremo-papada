# python
# File: apps/api/v1/unidades/views.py
from rest_framework import viewsets
from apps.unidades.models import Unidade  # ajuste este import se o modelo estiver em outro lugar
from .serializers import UnidadeSerializer

class UnidadeViewSet(viewsets.ModelViewSet):
    """
    ViewSet padrão para o modelo Unidade.
    Garante atributos `queryset` e `serializer_class` necessários ao DefaultRouter.
    """
    queryset = Unidade.objects.all()
    serializer_class = UnidadeSerializer