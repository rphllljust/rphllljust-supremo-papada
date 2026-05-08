from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.access.api.permissions import CanAccessModule

from .models import ContratoFinanceiro, Mensalidade, PlanoPagamento
from .serializers import (
    ContratoFinanceiroSerializer,
    MensalidadeSerializer,
    PlanoPagamentoSerializer,
    RegistrarPagamentoSerializer,
)

Usuario = get_user_model()


class PlanoPagamentoViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "financeiro"
    access_surface = "api"
    queryset = PlanoPagamento.objects.select_related('curso').all()
    serializer_class = PlanoPagamentoSerializer


class ContratoFinanceiroViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "financeiro"
    access_surface = "api"
    queryset = ContratoFinanceiro.objects.select_related(
        'matricula', 'matricula__aluno', 'matricula__curso', 'plano'
    ).all()
    serializer_class = ContratoFinanceiroSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        matricula_id = self.request.query_params.get('matricula')
        status = self.request.query_params.get('status')
        inadimplente = self.request.query_params.get('inadimplente')

        if matricula_id:
            qs = qs.filter(matricula_id=matricula_id)
        if status:
            qs = qs.filter(status=status)
        if inadimplente:
            qs = qs.filter(status='INADIMPLENTE')

        return qs

    @action(detail=True, methods=['post'])
    def gerar_parcelas(self, request, pk=None):
        """Gera todas as parcelas do contrato automaticamente."""
        contrato = self.get_object()
        if contrato.parcelas.exists():
            return Response(
                {'detail': 'Este contrato ja possui parcelas geradas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from datetime import date, timedelta
        from decimal import Decimal

        parcela = contrato.valor_parcela
        vencimento_base = date.today().replace(day=10)
        if vencimento_base < date.today():
            vencimento_base = vencimento_base.replace(month=vencimento_base.month + 1)

        parcelas = []
        for i in range(contrato.quantidade_parcelas):
            mes = (vencimento_base.month + i - 1) % 12 + 1
            ano = vencimento_base.year + (vencimento_base.month + i - 1) // 12
            try:
                venc = date(ano, mes, min(vencimento_base.day, 28))
            except ValueError:
                venc = date(ano, mes, 28)

            parcelas.append(Mensalidade(
                contrato=contrato,
                numero_parcela=i + 1,
                data_vencimento=venc,
                valor_original=parcela,
                status='PENDENTE',
            ))

        Mensalidade.objects.bulk_create(parcelas)
        return Response({'detail': f'{len(parcelas)} parcelas geradas com sucesso.'})


class MensalidadeViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "financeiro"
    access_surface = "api"
    queryset = Mensalidade.objects.select_related(
        'contrato', 'contrato__matricula', 'contrato__matricula__aluno'
    ).all()
    serializer_class = MensalidadeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        contrato_id = self.request.query_params.get('contrato')
        status = self.request.query_params.get('status')

        if contrato_id:
            qs = qs.filter(contrato_id=contrato_id)
        if status:
            qs = qs.filter(status=status)

        return qs

    @action(detail=True, methods=['post'])
    def registrar_pagamento(self, request, pk=None):
        serializer = RegistrarPagamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mensalidade = self.get_object()
        with transaction.atomic():
            mensalidade.registrar_pagamento(
                valor_pago=serializer.validated_data['valor_pago'],
                data_pagamento=serializer.validated_data['data_pagamento'],
                forma_pagamento=serializer.validated_data.get('forma_pagamento', ''),
                numero_boleto=serializer.validated_data.get('numero_boleto', ''),
            )

        return Response(MensalidadeSerializer(mensalidade).data)

    @action(detail=True, methods=['post'])
    def reemitir_boleto(self, request, pk=None):
        mensalidade = self.get_object()
        # Simula reemissao de boleto (geraria novo numero)
        import uuid
        mensalidade.numero_boleto = f'BOL-{uuid.uuid4().hex[:12].upper()}'
        mensalidade.linha_digitavel = ''.join([str(uuid.uuid4().int)[:47], str(uuid.uuid4().int)[:47], str(uuid.uuid4().int)[:4]])
        mensalidade.save(update_fields=['numero_boleto', 'linha_digitavel'])
        return Response(MensalidadeSerializer(mensalidade).data)
