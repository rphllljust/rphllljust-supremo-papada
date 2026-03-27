from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.inscricoes.models import PublicacaoInscricao

from .serializers import PublicacaoInscricaoSerializer


class PublicacaoInscricaoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "inscricoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = PublicacaoInscricaoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = PublicacaoInscricao.objects.select_related("curso", "publicado_por").order_by(
            "-data_inicio", "-id"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        curso_id = self.request.query_params.get("curso", "").strip()
        modalidade = self.request.query_params.get("modalidade_ingresso", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        if modalidade:
            queryset = queryset.filter(modalidade_ingresso=modalidade)

        if search:
            queryset = queryset.filter(
                Q(codigo_edital__icontains=search)
                | Q(titulo__icontains=search)
                | Q(descricao__icontains=search)
                | Q(curso__nome__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(publicado_por=self.request.user if self.request.user.is_authenticated else None)


class PublicacaoInscricaoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "inscricoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = PublicacaoInscricaoSerializer
    queryset = PublicacaoInscricao.objects.select_related("curso", "publicado_por")

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
