from django.urls import path

from .views import GuiaTransferenciaViewSet

app_name = "api_v1_guias_transferencia"

urlpatterns = [
    path("", GuiaTransferenciaViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", GuiaTransferenciaViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]