from django.urls import path

from .views import ProcessoDetailApiView, ProcessoListApiView

app_name = "api_v1_processos"

urlpatterns = [
    path("", ProcessoListApiView.as_view(), name="list"),
    path("<int:pk>/", ProcessoDetailApiView.as_view(), name="detail"),
]