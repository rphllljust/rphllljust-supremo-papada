# file: apps/turmas/urls.py
from django.urls import include, path

from . import views

app_name = "turmas"

urlpatterns = [
    path("", include("apps.turmas.turmas.urls")),
    path("inicio/", views.index, name="index"),
]