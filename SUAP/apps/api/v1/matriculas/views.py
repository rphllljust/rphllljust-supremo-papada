from rest_framework.viewsets import ModelViewSet
from apps.matriculas.models import Matricula
from .serializers import MatriculaSerializer

class MatriculaViewSet(ModelViewSet):
    queryset = Matricula.objects.select_related("aluno", "turma").all().order_by("id")
    serializer_class = MatriculaSerializer