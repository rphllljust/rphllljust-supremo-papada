from django.urls import path

from . import views

urlpatterns = [
    path("", views.turmas_list, name="turmas_list"),
    path("novo/", views.turmas_create, name="turmas_create"),
    path("<int:pk>/editar/", views.turmas_update, name="turmas_update"),
    path("<int:pk>/excluir/", views.turmas_delete, name="turmas_delete"),

    # Diário Acadêmico
    path("diarios/", views.diarios_list, name="diarios_list"),
    path("<int:turma_pk>/diarios/novo/", views.diario_create, name="diario_create"),
    path("diarios/<int:pk>/fechar/", views.diario_fechar, name="diario_fechar"),
    path("diarios/<int:pk>/excluir/", views.diario_delete, name="diario_delete"),
]

