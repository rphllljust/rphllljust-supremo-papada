from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination

from .serializers import UsuarioSerializer


Usuario = get_user_model()


class UsuarioListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "usuarios"
    access_surface = "api"
    access_action = "view"
    serializer_class = UsuarioSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Usuario.objects.select_related("pessoa").order_by(
            "pessoa__nome_completo", "first_name", "last_name", "username"
        )

        search = self.request.query_params.get("search", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(cpf__icontains=search)
                | Q(pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()


class UsuarioDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "usuarios"
    access_surface = "api"
    access_action = "view"
    serializer_class = UsuarioSerializer
    queryset = Usuario.objects.select_related("pessoa")