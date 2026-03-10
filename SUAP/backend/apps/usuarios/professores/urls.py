from django.urls import path

from . import views

urlpatterns = [
    path("", views.professores_list, name="professores_list"),
    path("novo/", views.professores_create, name="professores_create"),
    path("<int:pk>/editar/", views.professores_update, name="professores_update"),
    path("<int:pk>/excluir/", views.professores_delete, name="professores_delete"),
]

