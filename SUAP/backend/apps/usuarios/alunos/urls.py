from django.urls import path

from . import views

urlpatterns = [
    path("", views.alunos_list, name="alunos_list"),
    path("novo/", views.alunos_create, name="alunos_create"),
    path("<int:pk>/editar/", views.alunos_update, name="alunos_update"),
    path("<int:pk>/excluir/", views.alunos_delete, name="alunos_delete"),
]

