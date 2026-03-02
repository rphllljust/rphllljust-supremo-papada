from rest_framework.viewsets import ModelViewSet
from apps.turmas.models import Turma
from .serializers import TurmaSerializer

class TurmaViewSet(ModelViewSet):
    queryset = Turma.objects.select_related("curso", "professor_responsavel").all().order_by("id")
    serializer_class = TurmaSerializer