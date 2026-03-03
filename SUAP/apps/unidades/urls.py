# file: apps/unidades/urls.py
from django.urls import include, path

from . import views

app_name = "unidades"

urlpatterns = [
    path("", include("apps.unidades.unidades.urls")),
    path("inicio/", views.index, name="index"),
]