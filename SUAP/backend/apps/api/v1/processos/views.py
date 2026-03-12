from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.processos.models import Processo

from .serializers import ProcessoSerializer, TramitarProcessoSerializer, TramitacaoSerializer


class ProcessoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "processos"
    access_surface = "api"
    access_action = "view"
    serializer_class = ProcessoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = Processo.objects.select_related("requerente__pessoa").prefetch_related("tramitacoes__responsavel__pessoa").order_by("-data_abertura", "-id")
        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if search:
            queryset = queryset.filter(
                Q(numero__icontains=search)
                | Q(assunto__icontains=search)
                | Q(descricao__icontains=search)
                | Q(requerente__username__icontains=search)
                | Q(requerente__first_name__icontains=search)
                | Q(requerente__last_name__icontains=search)
                | Q(requerente__pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()


class ProcessoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "processos"
    access_surface = "api"
    access_action = "view"
    serializer_class = ProcessoSerializer
    queryset = Processo.objects.select_related("requerente__pessoa").prefetch_related("tramitacoes__responsavel__pessoa")

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class ProcessoTramitarApiView(generics.GenericAPIView):
    permission_classes = [CanAccessModule]
    module_name = "processos"
    access_surface = "api"
    access_action = "manage"
    serializer_class = TramitarProcessoSerializer
    queryset = Processo.objects.select_related("requerente__pessoa")

    def post(self, request, *args, **kwargs):
        processo = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"processo": processo, "responsavel": request.user})
        serializer.is_valid(raise_exception=True)
        tramitacao = serializer.save()
        return Response(TramitacaoSerializer(tramitacao).data, status=status.HTTP_201_CREATED)