from django.urls import path

from .views import MatriculaDetailApiView, MatriculaListApiView

app_name = "api_v1_matriculas"

urlpatterns = [
    path("", MatriculaListApiView.as_view(), name="list"),
    path("<int:pk>/", MatriculaDetailApiView.as_view(), name="detail"),
]
