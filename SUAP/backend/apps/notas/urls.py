from django.urls import include, path

from . import views

app_name = "notas"

urlpatterns = [
    path("", include("apps.notas.notas.urls")),
    path("inicio/", views.index, name="index"),
]

