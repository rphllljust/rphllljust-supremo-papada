from django.urls import path

from .views import HistoricoEscolarViewSet

app_name = "api_v1_historicos"

urlpatterns = [
    path("", HistoricoEscolarViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", HistoricoEscolarViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]