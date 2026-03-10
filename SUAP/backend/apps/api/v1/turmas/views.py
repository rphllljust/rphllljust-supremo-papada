from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.turmas.models import Turma

from .serializers import TurmaSerializer


class TurmaListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "turmas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TurmaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Turma.objects.select_related("curso", "professor_responsavel").order_by(
            "-ano_letivo", "nome"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        curso_id = self.request.query_params.get("curso", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(curso__nome__icontains=search)
                | Q(professor_responsavel__first_name__icontains=search)
                | Q(professor_responsavel__last_name__icontains=search)
            )

        return queryset.distinct()


class TurmaDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "turmas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TurmaSerializer
    queryset = Turma.objects.select_related("curso", "professor_responsavel")
