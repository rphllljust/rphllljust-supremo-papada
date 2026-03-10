from django.urls import path

from . import views

urlpatterns = [
    path("", views.processos_list, name="processos_list"),
    path("novo/", views.processo_create, name="processo_create"),
    path("<int:pk>/", views.processo_detalhe, name="processo_detalhe"),
    path("<int:pk>/editar/", views.processo_update, name="processo_update"),
    path("<int:pk>/excluir/", views.processo_delete, name="processo_delete"),
]
