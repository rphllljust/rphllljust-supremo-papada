from django.urls import path

from .views import EstagioDetailApiView, EstagioListApiView

app_name = "api_v1_estagios"

urlpatterns = [
    path("", EstagioListApiView.as_view(), name="list"),
    path("<int:pk>/", EstagioDetailApiView.as_view(), name="detail"),
]