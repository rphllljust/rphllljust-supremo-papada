# python
# file: `apps/api/v1/urls.py`
from django.urls import include, path

urlpatterns = [
    path("usuarios/", include("apps.api.v1.usuarios.urls")),
    path("unidades/", include("apps.api.v1.unidades.urls")),
    path("turmas/", include("apps.api.v1.turmas.urls")),
    path("matriculas/", include("apps.api.v1.matriculas.urls")),
]