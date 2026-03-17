from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.access.api.permissions import CanAccessModule
from apps.access.policies import filter_professor_scoped_queryset, professor_owns_related_resource
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.turmas.models import Turma

from .serializers import TurmaSerializer


TAB_FILTERS = {
    "TODOS": lambda queryset: queryset,
    "ATIVAS": lambda queryset: queryset.filter(status="ATIVA"),
    "PLANEJADAS": lambda queryset: queryset.filter(status="PLANEJADA"),
    "ENCERRADAS": lambda queryset: queryset.filter(status="ENCERRADA"),
    "CANCELADAS": lambda queryset: queryset.filter(status="CANCELADA"),
    "SEM_DIARIOS": lambda queryset: queryset.filter(total_diarios=0),
}


def annotate_turma_queryset(queryset):
    return queryset.annotate(
        total_alunos=Count("matriculas", filter=Q(matriculas__status="ATIVA"), distinct=True),
        total_diarios=Count("diarios", distinct=True),
    )


class TurmaListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "turmas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TurmaSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = annotate_turma_queryset(
            Turma.objects.select_related("curso", "professor_responsavel")
        ).order_by(
            "-ano_letivo", "nome"
        )
        queryset = filter_professor_scoped_queryset(
            self.request.user,
            queryset,
            professor_lookup="professor_responsavel_id",
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        curso_id = self.request.query_params.get("curso", "").strip()
        professor_id = self.request.query_params.get("professor", "").strip()
        ano_letivo = self.request.query_params.get("ano_letivo", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        if professor_id:
            queryset = queryset.filter(professor_responsavel_id=professor_id)

        if ano_letivo:
            queryset = queryset.filter(ano_letivo=ano_letivo)

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(curso__nome__icontains=search)
                | Q(curso__sigla__icontains=search)
                | Q(professor_responsavel__first_name__icontains=search)
                | Q(professor_responsavel__last_name__icontains=search)
            )

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        aba = (request.query_params.get("aba") or "TODOS").strip().upper()
        summary = {key: TAB_FILTERS[key](queryset).count() for key in TAB_FILTERS}
        filtered = TAB_FILTERS.get(aba, TAB_FILTERS["TODOS"])(queryset)

        page = self.paginate_queryset(filtered)
        serializer = self.get_serializer(page if page is not None else filtered, many=True)

        if page is not None:
            response = self.get_paginated_response(serializer.data)
            response.data["summary"] = summary
            response.data["active_tab"] = aba
            return response

        return Response({"results": serializer.data, "summary": summary, "active_tab": aba})

    def perform_create(self, serializer):
        professor = serializer.validated_data.get("professor_responsavel")
        professor_id = getattr(professor, "id", None)
        if not professor_owns_related_resource(self.request.user, professor_id=professor_id):
            raise PermissionDenied("Professor so pode operar turmas sob sua responsabilidade.")
        serializer.save()


class TurmaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "turmas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TurmaSerializer
    queryset = annotate_turma_queryset(Turma.objects.select_related("curso", "professor_responsavel"))

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            self.queryset,
            professor_lookup="professor_responsavel_id",
        )

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
