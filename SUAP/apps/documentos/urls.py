from django.urls import path

from . import views

urlpatterns = [
    # Declaração
    path("declaracoes/", views.declaracao_list, name="declaracao_list"),
    path("declaracoes/novo/", views.declaracao_create, name="declaracao_create"),
    path("declaracoes/<int:pk>/", views.declaracao_detalhe, name="declaracao_detalhe"),

    # Histórico Escolar
    path("historicos/", views.historico_list, name="historico_list"),
    path("historicos/novo/", views.historico_create, name="historico_create"),
    path("historicos/<int:pk>/", views.historico_detalhe, name="historico_detalhe"),

    # Guia de Transferência
    path("guias/", views.guia_list, name="guia_list"),
    path("guias/novo/", views.guia_create, name="guia_create"),
    path("guias/<int:pk>/", views.guia_detalhe, name="guia_detalhe"),

    # Ata / Ofício / Memorando
    path("atas/", views.ata_list, name="ata_list"),
    path("atas/novo/", views.ata_create, name="ata_create"),
    path("atas/<int:pk>/editar/", views.ata_update, name="ata_update"),
    path("atas/<int:pk>/", views.ata_detalhe, name="ata_detalhe"),
]
