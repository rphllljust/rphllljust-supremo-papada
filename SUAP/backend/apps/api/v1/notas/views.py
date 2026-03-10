from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.notas.models import Nota

from .serializers import NotaSerializer


class NotaListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "notas"
    access_surface = "api"
    access_action = "view"
    serializer_class = NotaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Nota.objects.select_related(
            "matricula__aluno__pessoa",
            "matricula__curso",
            "matricula__turma",
        ).order_by("-data_lancamento", "descricao", "-id")

        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(descricao__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
                | Q(matricula__curso__nome__icontains=search)
                | Q(matricula__turma__nome__icontains=search)
            )

        return queryset.distinct()


class NotaDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "notas"
    access_surface = "api"
    access_action = "view"
    serializer_class = NotaSerializer
    queryset = Nota.objects.select_related(
        "matricula__aluno__pessoa",
        "matricula__curso",
        "matricula__turma",
    )