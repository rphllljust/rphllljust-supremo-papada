from django.urls import include, path

from . import views

app_name = "frequencia"

urlpatterns = [
    path("", include("apps.frequencia.frequencia.urls")),
    path("inicio/", views.index, name="index"),
]

