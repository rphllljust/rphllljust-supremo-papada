from django.db.models import Q
from rest_framework import generics, serializers as drf_serializers

from apps.access.api.permissions import CanAccessModule
from apps.access.policies import filter_aluno_scoped_queryset
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.matriculas.models import Matricula, PendenciaDocumental

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
            "aluno__pessoa__aluno",
            "curso",
            "turma",
            "turma__professor_responsavel",
            "consolidacao",
        ).prefetch_related("turma__diarios").order_by(
            "-data_matricula", "-id"
        )

        params = self.request.query_params
        search = params.get("search", "").strip()

        # T075: filtros combinados — todos aplicados em AND
        status_value = params.get("status", "").strip()
        curso_id = params.get("curso", "").strip()
        turma_id = params.get("turma", "").strip()
        tipo_matricula = params.get("tipo_matricula", "").strip()
        data_inicio = params.get("data_inicio", "").strip()
        data_fim = params.get("data_fim", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)
        if turma_id:
            queryset = queryset.filter(turma_id=turma_id)
        if tipo_matricula:
            queryset = queryset.filter(tipo_matricula=tipo_matricula)
        # T101: filtro de data corrigido — aplica data_inicio como limite inferior
        if data_inicio:
            queryset = queryset.filter(data_matricula__gte=data_inicio)
        if data_fim:
            queryset = queryset.filter(data_matricula__lte=data_fim)

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

        queryset = filter_aluno_scoped_queryset(
            self.request.user,
            queryset,
            aluno_lookup="aluno_id",
        )

        return queryset.distinct()

    def perform_create(self, serializer):
        # T027: bloqueia rematrícula de aluno inadimplente
        aluno = serializer.validated_data.get("aluno")
        tipo = serializer.validated_data.get("tipo_matricula", "NOVA")
        if tipo == "REMATRICULA" and aluno:
            from apps.matriculas.models import Matricula as M
            tem_inadimplencia = M.objects.filter(
                aluno=aluno,
                status="ATIVA",
            ).filter(
                # Verifica se há consolidação pendente ou nota negativa
                consolidacao__situacao__in=["REPROVADO_NOTA", "REPROVADO_FREQUENCIA", "REPROVADO_AMBOS"]
            ).exists()
            if tem_inadimplencia:
                raise drf_serializers.ValidationError(
                    {"tipo_matricula": "Rematricula nao permitida: aluno com pendencias academicas em aberto."}
                )
            tem_inadimplencia_financeira = PendenciaDocumental.objects.filter(
                matricula__aluno=aluno,
                status="ABERTA",
            ).filter(
                Q(descricao__icontains="financeir")
                | Q(descricao__icontains="mensalidade")
                | Q(descricao__icontains="debito")
                | Q(descricao__icontains="inadimpl")
            ).exists()
            if tem_inadimplencia_financeira:
                raise drf_serializers.ValidationError(
                    {"tipo_matricula": "Rematricula nao permitida: aluno com inadimplencia financeira em aberto."}
                )
        serializer.save()


class MatriculaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    serializer_class = MatriculaSerializer

    def get_queryset(self):
        queryset = Matricula.objects.select_related(
            "aluno__pessoa",
            "curso",
            "turma",
            "turma__professor_responsavel",
            "consolidacao",
        ).prefetch_related("turma__diarios")
        return filter_aluno_scoped_queryset(
            self.request.user,
            queryset,
            aluno_lookup="aluno_id",
        )

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
