from django.urls import path

from . import views

urlpatterns = [
    path("", views.arquivo_list, name="arquivo_list"),
    path("novo/", views.arquivo_create, name="arquivo_create"),
    path("<int:pk>/editar/", views.arquivo_update, name="arquivo_update"),
    path("<int:pk>/excluir/", views.arquivo_delete, name="arquivo_delete"),
    path("<int:guarda_pk>/emprestimo/", views.emprestimo_create, name="emprestimo_create"),
    path("emprestimo/<int:pk>/editar/", views.emprestimo_update, name="emprestimo_update"),

    # P04 – Fluxo de Arquivo Escolar e Prazos
    path("fluxo/", views.fluxo_arquivo_list, name="fluxo_arquivo_list"),
    path("<int:guarda_pk>/fluxo/novo/", views.fluxo_arquivo_create, name="fluxo_arquivo_create"),
    path("fluxo/<int:pk>/", views.fluxo_arquivo_detalhe, name="fluxo_arquivo_detalhe"),
    path("fluxo/<int:pk>/avancar/", views.fluxo_arquivo_avancar, name="fluxo_arquivo_avancar"),
    path("termo/<int:pk>/", views.termo_eliminacao_detalhe, name="termo_eliminacao_detalhe"),
]
