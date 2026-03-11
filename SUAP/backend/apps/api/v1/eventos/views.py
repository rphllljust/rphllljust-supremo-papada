from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.agenda.models import EventoAgenda
from apps.api.v1.pagination import StandardResultsSetPagination

from .serializers import EventoAgendaSerializer


class EventoAgendaListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "agenda"
    access_surface = "api"
    access_action = "view"
    serializer_class = EventoAgendaSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = EventoAgenda.objects.select_related(
            "turma",
            "turma__curso",
            "turma__professor_responsavel",
        ).order_by("inicio", "id")

        search = self.request.query_params.get("search", "").strip()
        turma_id = self.request.query_params.get("turma", "").strip()

        if turma_id:
            queryset = queryset.filter(turma_id=turma_id)

        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search)
                | Q(descricao__icontains=search)
                | Q(turma__nome__icontains=search)
                | Q(turma__curso__nome__icontains=search)
                | Q(turma__professor_responsavel__first_name__icontains=search)
                | Q(turma__professor_responsavel__last_name__icontains=search)
                | Q(turma__professor_responsavel__username__icontains=search)
            )

        return queryset.distinct()


class EventoAgendaDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "agenda"
    access_surface = "api"
    serializer_class = EventoAgendaSerializer
    queryset = EventoAgenda.objects.select_related(
        "turma",
        "turma__curso",
        "turma__professor_responsavel",
    )

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()