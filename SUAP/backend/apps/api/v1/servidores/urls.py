from django.urls import path

from .profile_views import ServidorProfileByIdApiView, ServidorProfileByMatriculaApiView
from .views import ServidorViewSet

app_name = "api_v1_servidores"

urlpatterns = [
    path("", ServidorViewSet.as_view({"get": "list", "post": "create"}), name="list"),
    path("<int:pk>/perfil/", ServidorProfileByIdApiView.as_view(), name="profile-by-id"),
    path("matricula/<str:matricula_servidor>/perfil/", ServidorProfileByMatriculaApiView.as_view(), name="profile-by-matricula"),
    path("<int:pk>/", ServidorViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="detail"),
]