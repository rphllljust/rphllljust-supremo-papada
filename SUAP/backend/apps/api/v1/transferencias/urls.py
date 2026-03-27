from django.urls import path

from .views import TransferenciaDetailApiView, TransferenciaListApiView

app_name = "api_v1_transferencias"

urlpatterns = [
    path("", TransferenciaListApiView.as_view(), name="list"),
    path("<int:pk>/", TransferenciaDetailApiView.as_view(), name="detail"),
]
