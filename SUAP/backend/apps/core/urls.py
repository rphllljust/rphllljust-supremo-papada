# File: `apps/core/urls.py`
from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("indisponivel/<slug:item_slug>/", views.ensino_item_indisponivel, name="ensino_item_indisponivel"),
]