from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.inscricoes.models import Inscricao

from .serializers import InscricaoSerializer


class InscricaoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "inscricoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = InscricaoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = Inscricao.objects.select_related("publicacao", "publicacao__curso", "usuario").order_by(
            "-data_inscricao", "-id"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        publicacao_id = self.request.query_params.get("publicacao", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

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


class InscricaoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "inscricoes"
    access_surface = "api"
    access_action = "view"
    serializer_class = InscricaoSerializer
    queryset = Inscricao.objects.select_related("publicacao", "publicacao__curso", "usuario")

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
