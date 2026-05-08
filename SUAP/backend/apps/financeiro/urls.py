from django.urls import path

from .views import ContratoFinanceiroViewSet, MensalidadeViewSet, PlanoPagamentoViewSet

urlpatterns = [
    path(
        "planos/",
        PlanoPagamentoViewSet.as_view({"get": "list", "post": "create"}),
        name="plano-list",
    ),
    path(
        "planos/<int:pk>/",
        PlanoPagamentoViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="plano-detail",
    ),
    path(
        "contratos/",
        ContratoFinanceiroViewSet.as_view({"get": "list", "post": "create"}),
        name="contrato-list",
    ),
    path(
        "contratos/<int:pk>/",
        ContratoFinanceiroViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="contrato-detail",
    ),
    path(
        "contratos/<int:pk>/gerar-parcelas/",
        ContratoFinanceiroViewSet.as_view({"post": "gerar_parcelas"}),
        name="contrato-gerar-parcelas",
    ),
    path(
        "mensalidades/",
        MensalidadeViewSet.as_view({"get": "list", "post": "create"}),
        name="mensalidade-list",
    ),
    path(
        "mensalidades/<int:pk>/",
        MensalidadeViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="mensalidade-detail",
    ),
    path(
        "mensalidades/<int:pk>/registrar-pagamento/",
        MensalidadeViewSet.as_view({"post": "registrar_pagamento"}),
        name="mensalidade-registrar-pagamento",
    ),
    path(
        "mensalidades/<int:pk>/reemitir-boleto/",
        MensalidadeViewSet.as_view({"post": "reemitir_boleto"}),
        name="mensalidade-reemitir-boleto",
    ),
]
