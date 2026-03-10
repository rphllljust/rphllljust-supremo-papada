from django.urls import path

from . import views

urlpatterns = [
    path("", views.agenda_list, name="agenda_list"),
    path("novo/", views.agenda_create, name="agenda_create"),
    path("<int:pk>/editar/", views.agenda_update, name="agenda_update"),
    path("<int:pk>/excluir/", views.agenda_delete, name="agenda_delete"),
]

