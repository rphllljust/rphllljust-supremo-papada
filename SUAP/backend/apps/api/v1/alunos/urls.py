from django.urls import path

from .views import AlunoViewSet

app_name = "api_v1_alunos"

urlpatterns = [
    path("", AlunoViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", AlunoViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]