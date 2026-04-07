from django.urls import path

from apps.api.v1.historicos.views import ValidacaoHistoricoPublicoViewSet

app_name = "api_v1_validacao_historicos"

urlpatterns = [
    path("", ValidacaoHistoricoPublicoViewSet.as_view({"get": "list"}), name="validar-por-codigo"),
    path("<uuid:pk>/", ValidacaoHistoricoPublicoViewSet.as_view({"get": "retrieve"}), name="validar"),
]
