# python
# file: `apps/api/v1/matriculas/urls.py`
from django.urls import path
from . import views

app_name = "api_v1_matriculas"

urlpatterns = [
    path("", views.matriculas_list, name="list"),
    path("<int:pk>/", views.matriculas_detail, name="detail"),
]
