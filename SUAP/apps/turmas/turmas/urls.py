from django.urls import path

from . import views

urlpatterns = [
    path("", views.turmas_list, name="turmas_list"),
    path("novo/", views.turmas_create, name="turmas_create"),
    path("<int:pk>/editar/", views.turmas_update, name="turmas_update"),
    path("<int:pk>/excluir/", views.turmas_delete, name="turmas_delete"),
]

