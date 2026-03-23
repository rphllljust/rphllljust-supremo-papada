from django.urls import path

from .views import (
    EmitirHistoricoDigitalApiView,
    HistoricoEscolarDigitalDetailApiView,
    HistoricoEscolarDigitalListApiView,
    RevogarHistoricoDigitalApiView,
    ValidarHistoricoDigitalPublicoApiView,
)

app_name = "api_v1_historicos_digitais"

urlpatterns = [
    path("", HistoricoEscolarDigitalListApiView.as_view(), name="list"),
    path("<int:pk>/", HistoricoEscolarDigitalDetailApiView.as_view(), name="detail"),
    path("<int:pk>/revogar/", RevogarHistoricoDigitalApiView.as_view(), name="revogar"),
    path("validar-publico/", ValidarHistoricoDigitalPublicoApiView.as_view(), name="validar_publico"),
    path("emitir/<int:historico_id>/", EmitirHistoricoDigitalApiView.as_view(), name="emitir"),
]
