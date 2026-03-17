from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied

from apps.access.api.permissions import CanAccessModule
from apps.access.policies import filter_professor_scoped_queryset, professor_owns_related_resource
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
            "matricula__turma__professor_responsavel",
        ).order_by("-data", "-id")
        queryset = filter_professor_scoped_queryset(
            self.request.user,
            queryset,
            professor_lookup="matricula__turma__professor_responsavel_id",
        )

        search = self.request.query_params.get("search", "").strip()
        presente = self.request.query_params.get("presente", "").strip().lower()
        curso_id = self.request.query_params.get("curso", "").strip()
        turma_id = self.request.query_params.get("turma", "").strip()
        professor_id = self.request.query_params.get("professor", "").strip()

        if curso_id:
            queryset = queryset.filter(matricula__curso_id=curso_id)

        if turma_id:
            queryset = queryset.filter(matricula__turma_id=turma_id)

        if professor_id:
            queryset = queryset.filter(matricula__turma__professor_responsavel_id=professor_id)

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
                | Q(matricula__turma__professor_responsavel__first_name__icontains=search)
                | Q(matricula__turma__professor_responsavel__last_name__icontains=search)
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        matricula = serializer.validated_data.get("matricula")
        professor_id = getattr(getattr(matricula, "turma", None), "professor_responsavel_id", None)
        if not professor_owns_related_resource(self.request.user, professor_id=professor_id):
            raise PermissionDenied("Professor so pode lancar frequencia nas turmas sob sua responsabilidade.")
        serializer.save()


class FrequenciaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "frequencia"
    access_surface = "api"
    serializer_class = FrequenciaSerializer
    queryset = Frequencia.objects.select_related(
        "matricula__aluno__pessoa",
        "matricula__curso",
        "matricula__turma",
        "matricula__turma__professor_responsavel",
    )

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            self.queryset,
            professor_lookup="matricula__turma__professor_responsavel_id",
        )

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()