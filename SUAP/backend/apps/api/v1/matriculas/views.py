from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.matriculas.models import Matricula

from .serializers import MatriculaSerializer


class MatriculaListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"
    serializer_class = MatriculaSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = Matricula.objects.select_related(
            "aluno__pessoa",
            "curso",
            "turma",
            "turma__professor_responsavel",
            "consolidacao",
        ).prefetch_related("turma__diarios").order_by(
            "-data_matricula", "-id"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if search:
            queryset = queryset.filter(
                Q(numero_matricula__icontains=search)
                | Q(aluno__username__icontains=search)
                | Q(aluno__cpf__icontains=search)
                | Q(aluno__first_name__icontains=search)
                | Q(aluno__last_name__icontains=search)
                | Q(aluno__pessoa__nome_completo__icontains=search)
                | Q(curso__nome__icontains=search)
                | Q(turma__nome__icontains=search)
            )

        return queryset.distinct()


class MatriculaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    serializer_class = MatriculaSerializer
    queryset = Matricula.objects.select_related(
        "aluno__pessoa",
        "curso",
        "turma",
        "turma__professor_responsavel",
        "consolidacao",
    ).prefetch_related("turma__diarios")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
