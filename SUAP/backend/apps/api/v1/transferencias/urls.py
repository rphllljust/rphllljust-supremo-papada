from django.urls import path

from .views import TransferenciaListApiView

app_name = "api_v1_transferencias"

urlpatterns = [
    path("", TransferenciaListApiView.as_view(), name="list"),
]