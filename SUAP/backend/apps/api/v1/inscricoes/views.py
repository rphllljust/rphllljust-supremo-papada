from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.inscricoes.models import (
    Candidato,
    ChamadaProcessoSeletivo,
    ConvocacaoCandidato,
    CotaProcessoSeletivo,
    Inscricao,
    ProcessoSeletivo,
)

from .serializers import (
    CandidatoSerializer,
    ChamadaProcessoSeletivoSerializer,
    ConvocacaoCandidatoSerializer,
    CotaProcessoSeletivoSerializer,
    InscricaoSerializer,
    ProcessoSeletivoSerializer,
)


class _InscricoesApiPermissionMixin:
    permission_classes = [CanAccessModule]
    module_name = "inscricoes"
    access_surface = "api"
    access_action = "view"

    def get_permissions(self):
        if self.request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class InscricaoListApiView(_InscricoesApiPermissionMixin, generics.ListCreateAPIView):
    serializer_class = InscricaoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Inscricao.objects.select_related("publicacao", "publicacao__curso", "usuario").order_by(
            "-data_inscricao", "-id"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        status_candidato = self.request.query_params.get("status_candidato", "").strip()
        publicacao_id = self.request.query_params.get("publicacao", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if status_candidato:
            queryset = queryset.filter(status_candidato=status_candidato)

        if publicacao_id:
            queryset = queryset.filter(publicacao_id=publicacao_id)

        if search:
            queryset = queryset.filter(
                Q(numero_inscricao__icontains=search)
                | Q(nome_candidato__icontains=search)
                | Q(cpf__icontains=search)
                | Q(email__icontains=search)
                | Q(publicacao__titulo__icontains=search)
                | Q(publicacao__curso__nome__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user if self.request.user.is_authenticated else None)


class InscricaoDetailApiView(_InscricoesApiPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InscricaoSerializer
    queryset = Inscricao.objects.select_related("publicacao", "publicacao__curso", "usuario")


class ProcessoSeletivoListApiView(_InscricoesApiPermissionMixin, generics.ListCreateAPIView):
    serializer_class = ProcessoSeletivoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = ProcessoSeletivo.objects.select_related("publicacao", "publicacao__curso", "responsavel").order_by(
            "-data_realizacao", "-id"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        modalidade = self.request.query_params.get("modalidade", "").strip()
        publicacao_id = self.request.query_params.get("publicacao", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if modalidade:
            queryset = queryset.filter(modalidade=modalidade)

        if publicacao_id:
            queryset = queryset.filter(publicacao_id=publicacao_id)

        if search:
            queryset = queryset.filter(
                Q(publicacao__titulo__icontains=search)
                | Q(criterios__icontains=search)
                | Q(resultado__icontains=search)
            )

        return queryset


class ProcessoSeletivoDetailApiView(_InscricoesApiPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProcessoSeletivoSerializer
    queryset = ProcessoSeletivo.objects.select_related("publicacao", "publicacao__curso", "responsavel")


class CandidatoListApiView(_InscricoesApiPermissionMixin, generics.ListCreateAPIView):
    serializer_class = CandidatoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Candidato.objects.select_related(
            "processo",
            "processo__publicacao",
            "inscricao",
            "chamada_atual",
        ).order_by("processo_id", "classificacao", "id")

        search = self.request.query_params.get("search", "").strip()
        processo_id = self.request.query_params.get("processo", "").strip()
        situacao = self.request.query_params.get("situacao", "").strip()

        if processo_id:
            queryset = queryset.filter(processo_id=processo_id)

        if situacao:
            queryset = queryset.filter(situacao=situacao)

        if search:
            queryset = queryset.filter(
                Q(inscricao__nome_candidato__icontains=search)
                | Q(inscricao__cpf__icontains=search)
                | Q(inscricao__numero_inscricao__icontains=search)
                | Q(processo__publicacao__titulo__icontains=search)
            )

        return queryset


class CandidatoDetailApiView(_InscricoesApiPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CandidatoSerializer
    queryset = Candidato.objects.select_related("processo", "inscricao", "chamada_atual")


class CotaProcessoSeletivoListApiView(_InscricoesApiPermissionMixin, generics.ListCreateAPIView):
    serializer_class = CotaProcessoSeletivoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = CotaProcessoSeletivo.objects.select_related("processo", "processo__publicacao").order_by(
            "processo_id", "ordem_remanejamento", "id"
        )

        processo_id = self.request.query_params.get("processo", "").strip()
        ativa = self.request.query_params.get("ativa", "").strip().lower()

        if processo_id:
            queryset = queryset.filter(processo_id=processo_id)

        if ativa in {"true", "false"}:
            queryset = queryset.filter(ativa=(ativa == "true"))

        return queryset


class CotaProcessoSeletivoDetailApiView(_InscricoesApiPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CotaProcessoSeletivoSerializer
    queryset = CotaProcessoSeletivo.objects.select_related("processo", "processo__publicacao")


class ChamadaProcessoSeletivoListApiView(_InscricoesApiPermissionMixin, generics.ListCreateAPIView):
    serializer_class = ChamadaProcessoSeletivoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = ChamadaProcessoSeletivo.objects.select_related("processo", "processo__publicacao").order_by(
            "processo_id", "numero", "id"
        )

        processo_id = self.request.query_params.get("processo", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()

        if processo_id:
            queryset = queryset.filter(processo_id=processo_id)

        if status_value:
            queryset = queryset.filter(status=status_value)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset


class ChamadaProcessoSeletivoDetailApiView(_InscricoesApiPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChamadaProcessoSeletivoSerializer
    queryset = ChamadaProcessoSeletivo.objects.select_related("processo", "processo__publicacao")


class ConvocacaoCandidatoListApiView(_InscricoesApiPermissionMixin, generics.ListCreateAPIView):
    serializer_class = ConvocacaoCandidatoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = ConvocacaoCandidato.objects.select_related(
            "chamada",
            "candidato",
            "candidato__inscricao",
        ).order_by("chamada_id", "classificacao_na_chamada", "id")

        chamada_id = self.request.query_params.get("chamada", "").strip()
        candidato_id = self.request.query_params.get("candidato", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        search = self.request.query_params.get("search", "").strip()

        if chamada_id:
            queryset = queryset.filter(chamada_id=chamada_id)

        if candidato_id:
            queryset = queryset.filter(candidato_id=candidato_id)

        if status_value:
            queryset = queryset.filter(status=status_value)

        if search:
            queryset = queryset.filter(
                Q(candidato__inscricao__nome_candidato__icontains=search)
                | Q(candidato__inscricao__cpf__icontains=search)
            )

        return queryset


class ConvocacaoCandidatoDetailApiView(_InscricoesApiPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ConvocacaoCandidatoSerializer
    queryset = ConvocacaoCandidato.objects.select_related("chamada", "candidato", "candidato__inscricao")
