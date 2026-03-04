from django.urls import path

from . import views

urlpatterns = [
    path("", views.notas_list, name="notas_list"),
    path("novo/", views.notas_create, name="notas_create"),
    path("<int:pk>/editar/", views.notas_update, name="notas_update"),
    path("<int:pk>/excluir/", views.notas_delete, name="notas_delete"),
]

