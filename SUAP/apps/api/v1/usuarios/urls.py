# python
# file: `apps/api/v1/usuarios/urls.py`
from django.urls import path
from . import views

app_name = "api_v1_usuarios"

urlpatterns = [
    path("", views.usuario_list, name="list"),
    path("<int:pk>/", views.usuario_detail, name="detail"),
]