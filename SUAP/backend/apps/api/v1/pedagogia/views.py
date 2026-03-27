from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.pedagogia.models import AtendimentoPedagogico

from .serializers import AtendimentoPedagogicoSerializer


class AtendimentoPedagogicoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "pedagogia"
    access_surface = "api"
    access_action = "view"
    serializer_class = AtendimentoPedagogicoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = AtendimentoPedagogico.objects.select_related(
            "aluno__pessoa",
            "pedagogia_responsavel__pessoa",
        ).order_by("-data_atendimento", "-id")

        status_value = self.request.query_params.get("status", "").strip()
        search = self.request.query_params.get("search", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if search:
            queryset = queryset.filter(
                Q(aluno__username__icontains=search)
                | Q(aluno__first_name__icontains=search)
                | Q(aluno__last_name__icontains=search)
                | Q(aluno__pessoa__nome_completo__icontains=search)
                | Q(pedagogia_responsavel__username__icontains=search)
                | Q(pedagogia_responsavel__first_name__icontains=search)
                | Q(pedagogia_responsavel__last_name__icontains=search)
                | Q(pedagogia_responsavel__pessoa__nome_completo__icontains=search)
                | Q(diagnostico__icontains=search)
                | Q(plano_acao__icontains=search)
            )

        return queryset.distinct()


class AtendimentoPedagogicoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "pedagogia"
    access_surface = "api"
    access_action = "view"
    serializer_class = AtendimentoPedagogicoSerializer
    queryset = AtendimentoPedagogico.objects.select_related(
        "aluno__pessoa",
        "pedagogia_responsavel__pessoa",
    )

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
