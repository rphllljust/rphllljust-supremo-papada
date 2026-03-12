from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.usuarios.models import PerfilUsuario

from .serializers import AlunoSerializer


Usuario = get_user_model()


class AlunoViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "usuarios"
    access_surface = "api"
    serializer_class = AlunoSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Usuario.objects.select_related("pessoa", "pessoa__aluno").filter(tipo=PerfilUsuario.ALUNO).order_by(
        "pessoa__nome_completo", "first_name", "last_name", "username"
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        situacao = self.request.query_params.get("situacao", "").strip()

        if situacao:
            queryset = queryset.filter(pessoa__aluno__situacao=situacao)

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
        if pessoa:
            pessoa.delete()