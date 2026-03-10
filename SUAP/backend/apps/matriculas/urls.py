# file: apps/matriculas/urls.py
from django.urls import include, path

from . import views

app_name = "matriculas"

urlpatterns = [
    path("", include("apps.matriculas.matriculas.urls")),
    path("inicio/", views.index, name="index"),
]