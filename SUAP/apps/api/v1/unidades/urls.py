# File: unidades/urls.py
from django.urls import path
from .views import UnidadeViewSet

app_name = "api_v1_unidades"

urlpatterns = [
    path("", UnidadeViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", UnidadeViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]