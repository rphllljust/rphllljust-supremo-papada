from django.urls import path

from .views import DeclaracaoViewSet

app_name = "api_v1_declaracoes"

urlpatterns = [
    path("", DeclaracaoViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", DeclaracaoViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]