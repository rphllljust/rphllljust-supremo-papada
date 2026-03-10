from django.urls import path

from .views import (
    NotificacaoDetailApiView,
    NotificacaoListApiView,
    NotificacaoMarcarLidaApiView,
    NotificacaoMarcarTodasLidasApiView,
    NotificacaoOcultarApiView,
    PreferenciaNotificacaoBulkUpdateApiView,
    PreferenciaNotificacaoListApiView,
    PreferenciaNotificacaoUpdateApiView,
)

app_name = "api_v1_notificacoes"

urlpatterns = [
    path("", NotificacaoListApiView.as_view(), name="list"),
    path("marcar-todas-lidas/", NotificacaoMarcarTodasLidasApiView.as_view(), name="mark-all-read"),
    path("preferencias/", PreferenciaNotificacaoListApiView.as_view(), name="preferences-list"),
    path("preferencias/atualizar-em-lote/", PreferenciaNotificacaoBulkUpdateApiView.as_view(), name="preferences-bulk-update"),
    path("preferencias/<int:pk>/", PreferenciaNotificacaoUpdateApiView.as_view(), name="preferences-update"),
    path("<int:pk>/", NotificacaoDetailApiView.as_view(), name="detail"),
    path("<int:pk>/marcar-lida/", NotificacaoMarcarLidaApiView.as_view(), name="mark-read"),
    path("<int:pk>/ocultar/", NotificacaoOcultarApiView.as_view(), name="hide"),
]