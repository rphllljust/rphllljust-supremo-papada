from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.arquivo.models import GuardaDocumental

from .serializers import GuardaDocumentalSerializer


class GuardaDocumentalListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "arquivo"
    access_surface = "api"
    access_action = "view"
    serializer_class = GuardaDocumentalSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = GuardaDocumental.objects.select_related("responsavel", "matricula", "processo").order_by(
            "-data_arquivamento", "-id"
        )

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        tipo_documento = self.request.query_params.get("tipo_documento", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)

        if search:
            queryset = queryset.filter(
                Q(numero_registro__icontains=search)
                | Q(descricao__icontains=search)
                | Q(localizacao__icontains=search)
                | Q(numero_caixa__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(processo__numero__icontains=search)
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(responsavel=self.request.user if self.request.user.is_authenticated else None)


class GuardaDocumentalDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "arquivo"
    access_surface = "api"
    access_action = "view"
    serializer_class = GuardaDocumentalSerializer
    queryset = GuardaDocumental.objects.select_related("responsavel", "matricula", "processo")

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
