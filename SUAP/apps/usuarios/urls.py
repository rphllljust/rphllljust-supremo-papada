from django.urls import include, path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.redirect_login_legacy, name="login"),
    path("logout/", views.redirect_logout_legacy, name="logout"),
    path("alunos/", include("apps.usuarios.alunos.urls")),
    path("professores/", include("apps.usuarios.professores.urls")),
]