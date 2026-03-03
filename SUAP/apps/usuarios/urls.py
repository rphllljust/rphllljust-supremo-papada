from django.urls import include, path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.index, name="index"),
    path("alunos/", include("apps.usuarios.alunos.urls")),
    path("professores/", include("apps.usuarios.professores.urls")),
]