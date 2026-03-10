from django.urls import path

from . import views

urlpatterns = [
    path("", views.cursos_list, name="cursos_list"),
    path("novo/", views.cursos_create, name="cursos_create"),
    path("<int:pk>/editar/", views.cursos_update, name="cursos_update"),
    path("<int:pk>/excluir/", views.cursos_delete, name="cursos_delete"),
]

