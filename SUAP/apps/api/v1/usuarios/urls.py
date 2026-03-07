from django.urls import path

from .views import UsuarioDetailApiView, UsuarioListApiView

app_name = "api_v1_usuarios"

urlpatterns = [
    path("", UsuarioListApiView.as_view(), name="list"),
    path("<int:pk>/", UsuarioDetailApiView.as_view(), name="detail"),
]