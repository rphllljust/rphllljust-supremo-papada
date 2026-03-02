from rest_framework.viewsets import ModelViewSet
from apps.unidades.models import Unidade
from .serializers import UnidadeSerializer

class UnidadeViewSet(ModelViewSet):
    queryset = Unidade.objects.all().order_by("id")
    serializer_class = UnidadeSerializer