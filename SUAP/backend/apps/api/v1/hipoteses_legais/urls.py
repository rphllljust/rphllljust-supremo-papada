from django.urls import path

from .views import HipoteseLegalDetailApiView, HipoteseLegalListApiView

app_name = "api_v1_hipoteses_legais"

urlpatterns = [
    path("", HipoteseLegalListApiView.as_view(), name="list"),
    path("<int:pk>/", HipoteseLegalDetailApiView.as_view(), name="detail"),
]
