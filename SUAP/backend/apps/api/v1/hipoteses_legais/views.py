from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from apps.api.v1.pagination import StandardResultsSetPagination
from apps.processos.models import HipoteseLegal

from .serializers import HipoteseLegalSerializer


class HipoteseLegalListApiView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HipoteseLegalSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = HipoteseLegal.objects.order_by("descricao", "id")
        texto = self.request.query_params.get("texto", "").strip()
        nivel_acesso = self.request.query_params.get("nivel_acesso", "").strip()
        ativo = self.request.query_params.get("ativo", "").strip().lower()

        if nivel_acesso:
            queryset = queryset.filter(nivel_acesso=nivel_acesso)

        if ativo in {"true", "1", "sim"}:
            queryset = queryset.filter(ativo=True)
        elif ativo in {"false", "0", "nao"}:
            queryset = queryset.filter(ativo=False)

        if texto:
            queryset = queryset.filter(
                Q(descricao__icontains=texto)
                | Q(base_legal__icontains=texto)
            )

        return queryset


class HipoteseLegalDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = HipoteseLegalSerializer
    queryset = HipoteseLegal.objects.all()
