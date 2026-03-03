# file: apps/turmas/urls.py
from django.urls import path
from . import views

app_name = "turmas"

urlpatterns = [
    path("", views.index, name="index"),
]