from django.urls import include, path

from . import views

app_name = "cursos"

urlpatterns = [
    path("", include("apps.cursos.cursos.urls")),
    path("inicio/", views.index, name="index"),
]

