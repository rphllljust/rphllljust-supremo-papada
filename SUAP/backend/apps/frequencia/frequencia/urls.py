from django.urls import path

from . import views

urlpatterns = [
    path("", views.frequencia_list, name="frequencia_list"),
    path("novo/", views.frequencia_create, name="frequencia_create"),
    path("<int:pk>/editar/", views.frequencia_update, name="frequencia_update"),
    path("<int:pk>/excluir/", views.frequencia_delete, name="frequencia_delete"),
]

