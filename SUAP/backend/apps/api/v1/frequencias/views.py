from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.frequencia.models import Frequencia

from .serializers import FrequenciaSerializer


class FrequenciaListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "frequencia"
    access_surface = "api"
    access_action = "view"
    serializer_class = FrequenciaSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = Frequencia.objects.select_related(
            "matricula__aluno__pessoa",
            "matricula__curso",
            "matricula__turma",
        ).order_by("-data", "-id")

        search = self.request.query_params.get("search", "").strip()
        presente = self.request.query_params.get("presente", "").strip().lower()

        if presente in {"true", "false"}:
            queryset = queryset.filter(presente=(presente == "true"))

        if search:
            queryset = queryset.filter(
                Q(observacao__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
                | Q(matricula__curso__nome__icontains=search)
                | Q(matricula__turma__nome__icontains=search)
            )

        return queryset.distinct()


class FrequenciaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "frequencia"
    access_surface = "api"
    serializer_class = FrequenciaSerializer
    queryset = Frequencia.objects.select_related(
        "matricula__aluno__pessoa",
        "matricula__curso",
        "matricula__turma",
    )

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()