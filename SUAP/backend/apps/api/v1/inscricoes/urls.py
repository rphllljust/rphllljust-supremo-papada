from django.urls import path

from .views import InscricaoDetailApiView, InscricaoListApiView

app_name = "api_v1_inscricoes"

urlpatterns = [
    path("", InscricaoListApiView.as_view(), name="list"),
    path("<int:pk>/", InscricaoDetailApiView.as_view(), name="detail"),
]