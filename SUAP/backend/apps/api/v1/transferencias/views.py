from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.matriculas.models import Transferencia

from .serializers import TransferenciaSerializer


class TransferenciaListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TransferenciaSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = Transferencia.objects.select_related(
            "matricula",
            "matricula__aluno__pessoa",
            "matricula__curso",
            "matricula__turma",
        ).order_by("-data_solicitacao", "-id")

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()
        matricula_id = self.request.query_params.get("matricula", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if matricula_id:
            queryset = queryset.filter(matricula_id=matricula_id)

        if search:
            queryset = queryset.filter(
                Q(numero_guia__icontains=search)
                | Q(escola_origem__icontains=search)
                | Q(escola_destino__icontains=search)
                | Q(observacao__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()


class TransferenciaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"
    serializer_class = TransferenciaSerializer
    queryset = Transferencia.objects.select_related(
        "matricula",
        "matricula__aluno__pessoa",
        "matricula__curso",
        "matricula__turma",
    )

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
