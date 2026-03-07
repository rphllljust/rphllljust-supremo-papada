# python
# file: `apps/api/v1/urls.py`
from django.urls import include, path

urlpatterns = [
    path("access/", include(("apps.access.api.urls", "access_api"), namespace="access_api")),
    path("auth/", include(("apps.api.v1.auth.urls", "api_v1_auth"), namespace="api_v1_auth")),
    path("usuarios/", include("apps.api.v1.usuarios.urls")),
    path("unidades/", include("apps.api.v1.unidades.urls")),
    path("turmas/", include("apps.api.v1.turmas.urls")),
    path("matriculas/", include("apps.api.v1.matriculas.urls")),
]