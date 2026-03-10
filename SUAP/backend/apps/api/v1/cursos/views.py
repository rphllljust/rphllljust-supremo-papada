from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.cursos.models import Curso

from .serializers import CursoSerializer


class CursoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = CursoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Curso.objects.select_related("unidade").order_by("nome")
        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(sigla__icontains=search)
                | Q(unidade__nome__icontains=search)
                | Q(eixo_tecnologico__icontains=search)
            )

        return queryset.distinct()


class CursoDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = CursoSerializer
    queryset = Curso.objects.select_related("unidade")