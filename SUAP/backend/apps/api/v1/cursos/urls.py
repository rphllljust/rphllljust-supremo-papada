from django.urls import path

from .views import CursoDetailApiView, CursoListApiView

app_name = "api_v1_cursos"

urlpatterns = [
    path("", CursoListApiView.as_view(), name="list"),
    path("<int:pk>/", CursoDetailApiView.as_view(), name="detail"),
]