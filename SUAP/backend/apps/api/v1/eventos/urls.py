from django.urls import path

from .views import EventoAgendaDetailApiView, EventoAgendaListApiView

app_name = "api_v1_eventos"

urlpatterns = [
    path("", EventoAgendaListApiView.as_view(), name="list"),
    path("<int:pk>/", EventoAgendaDetailApiView.as_view(), name="detail"),
]