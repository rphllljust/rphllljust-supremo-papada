from django.urls import path

from .views import FrequenciaDetailApiView, FrequenciaListApiView

app_name = "api_v1_frequencias"

urlpatterns = [
    path("", FrequenciaListApiView.as_view(), name="list"),
    path("<int:pk>/", FrequenciaDetailApiView.as_view(), name="detail"),
]