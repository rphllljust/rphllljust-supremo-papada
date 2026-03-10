from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.documentos.models import AtaOficioMemorando

from .serializers import AtaProfessoresSerializer


class AtaProfessoresViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    serializer_class = AtaProfessoresSerializer
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = AtaOficioMemorando.objects.select_related(
            "emitido_por__pessoa",
            "processo",
        ).prefetch_related("anexos_upload").filter(tipo="ATA").order_by("-data_reuniao", "-data_emissao", "-id")

        search = self.request.query_params.get("search", "").strip()
        situacao = self.request.query_params.get("situacao", "").strip()

        if situacao:
            queryset = queryset.filter(situacao=situacao)

        if search:
            queryset = queryset.filter(
                Q(numero_ata__icontains=search)
                | Q(numero_protocolo__icontains=search)
                | Q(assunto__icontains=search)
                | Q(local_reuniao__icontains=search)
                | Q(presidente_reuniao__icontains=search)
                | Q(responsavel_lavratura__icontains=search)
                | Q(tipo_reuniao_outro__icontains=search)
                | Q(processo__numero__icontains=search)
            )

        return queryset.distinct()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.situacao == "EMITIDO":
            raise ValidationError({"detail": "Atas emitidas nao podem ser excluidas."})
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)