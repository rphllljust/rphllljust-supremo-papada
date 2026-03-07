from django.urls import path

from .views import TurmaDetailApiView, TurmaListApiView

app_name = "api_v1_turmas"

urlpatterns = [
    path("", TurmaListApiView.as_view(), name="list"),
    path("<int:pk>/", TurmaDetailApiView.as_view(), name="detail"),
]
