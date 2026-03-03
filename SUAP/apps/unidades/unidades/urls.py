from django.urls import path

from . import views

urlpatterns = [
    path("", views.unidades_list, name="unidades_list"),
    path("novo/", views.unidades_create, name="unidades_create"),
    path("<int:pk>/editar/", views.unidades_update, name="unidades_update"),
    path("<int:pk>/excluir/", views.unidades_delete, name="unidades_delete"),
]

