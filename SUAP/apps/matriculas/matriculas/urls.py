from django.urls import path

from . import views

urlpatterns = [
    path("", views.matriculas_list, name="matriculas_list"),
    path("novo/", views.matriculas_create, name="matriculas_create"),
    path("<int:pk>/editar/", views.matriculas_update, name="matriculas_update"),
    path("<int:pk>/excluir/", views.matriculas_delete, name="matriculas_delete"),
]

