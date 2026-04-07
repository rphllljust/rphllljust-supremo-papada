from django.urls import path

from .views import HistoricoEscolarTecnicoViewSet

app_name = "api_v1_historicos"

urlpatterns = [
    path("", HistoricoEscolarTecnicoViewSet.as_view({"get": "list"}), name="list"),
    path("emitir/", HistoricoEscolarTecnicoViewSet.as_view({"post": "emitir"}), name="emitir"),
    path("preview/", HistoricoEscolarTecnicoViewSet.as_view({"get": "preview_emissao"}), name="preview-emissao"),
    path("<int:pk>/", HistoricoEscolarTecnicoViewSet.as_view({"get": "retrieve"}), name="detail"),
    path("<int:pk>/pdf/", HistoricoEscolarTecnicoViewSet.as_view({"get": "pdf"}), name="pdf"),
    path("<int:pk>/preview/", HistoricoEscolarTecnicoViewSet.as_view({"get": "preview"}), name="preview"),
    path("<int:pk>/reemitir/", HistoricoEscolarTecnicoViewSet.as_view({"post": "reemitir"}), name="reemitir"),
    path("<int:pk>/cancelar/", HistoricoEscolarTecnicoViewSet.as_view({"post": "cancelar"}), name="cancelar"),
]
