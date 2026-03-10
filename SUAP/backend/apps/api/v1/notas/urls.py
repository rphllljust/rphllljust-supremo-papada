from django.urls import path

from .views import NotaDetailApiView, NotaListApiView

app_name = "api_v1_notas"

urlpatterns = [
    path("", NotaListApiView.as_view(), name="list"),
    path("<int:pk>/", NotaDetailApiView.as_view(), name="detail"),
]