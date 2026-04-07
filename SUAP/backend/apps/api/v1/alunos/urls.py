from django.urls import path

from .views import AlunoViewSet

app_name = "api_v1_alunos"

urlpatterns = [
    path("", AlunoViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/", AlunoViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
    path("<int:pk>/dados-para-historico/", AlunoViewSet.as_view({"get": "dados_para_historico"}), name="dados-para-historico"),
]
