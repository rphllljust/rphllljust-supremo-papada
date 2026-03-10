from django.urls import path

from .views import AtaProfessoresViewSet

app_name = "api_v1_atas_professores"

urlpatterns = [
    path("", AtaProfessoresViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", AtaProfessoresViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]