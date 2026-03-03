# python
# file: `apps/api/v1/turmas/urls.py`
from django.urls import path
from . import views

app_name = "api_v1_turmas"

urlpatterns = [
    path("", views.turmas_list, name="list"),
    path("<int:pk>/", views.turmas_detail, name="detail"),
]
