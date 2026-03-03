# file: apps/matriculas/urls.py
from django.urls import path
from . import views

app_name = "matriculas"

urlpatterns = [
    path("", views.index, name="index"),
]