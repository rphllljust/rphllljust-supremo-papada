from django.urls import path

from .views import ServidorViewSet

app_name = "api_v1_servidores"

urlpatterns = [
    path("", ServidorViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", ServidorViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]