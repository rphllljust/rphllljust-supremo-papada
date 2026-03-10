from django.urls import path

from . import views

app_name = "access"

urlpatterns = [
    path("acesso-negado/", views.acesso_negado, name="acesso_negado"),
]
