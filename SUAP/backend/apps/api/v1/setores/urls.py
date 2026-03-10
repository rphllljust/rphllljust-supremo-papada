from django.urls import path

from .views import SetorViewSet

app_name = "api_v1_setores"

urlpatterns = [
    path("", SetorViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", SetorViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]