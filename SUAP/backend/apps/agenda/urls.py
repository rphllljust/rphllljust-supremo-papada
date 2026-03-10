from django.urls import include, path

from . import views

app_name = "agenda"

urlpatterns = [
    path("", include("apps.agenda.agenda.urls")),
    path("inicio/", views.index, name="index"),
]

