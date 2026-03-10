from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.usuarios.models import PerfilUsuario
from apps.usuarios.profile_compat import has_servidor_profile_table

from .serializers import ServidorSerializer


Usuario = get_user_model()


class ServidorViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "servidores"
    access_surface = "api"
    serializer_class = ServidorSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Usuario.objects.select_related("pessoa", "setor").exclude(tipo=PerfilUsuario.ALUNO).order_by(
        "pessoa__nome_completo", "first_name", "last_name", "username"
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()
        setor_id = self.request.query_params.get("setor", "").strip()

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if setor_id:
            queryset = queryset.filter(setor_id=setor_id)

        if search:
            filters = (
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(cpf__icontains=search)
                | Q(pessoa__nome_completo__icontains=search)
                | Q(setor__nome__icontains=search)
                | Q(setor__codigo__icontains=search)
            )
            if has_servidor_profile_table():
                filters |= Q(perfil_servidor__matricula_servidor__icontains=search)
            queryset = queryset.filter(filters)

        return queryset.distinct()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    @transaction.atomic
    def perform_destroy(self, instance):
        pessoa = instance.pessoa
        instance.delete()

        if pessoa and not hasattr(pessoa, "aluno"):
            pessoa.delete()