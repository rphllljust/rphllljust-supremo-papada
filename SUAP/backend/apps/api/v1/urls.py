# python
# file: `apps/api/v1/urls.py`
from django.urls import include, path

urlpatterns = [
    path("access/", include(("apps.access.api.urls", "access_api"), namespace="access_api")),
    path("auth/", include(("apps.api.v1.auth.urls", "api_v1_auth"), namespace="api_v1_auth")),
    path("atas-professores/", include("apps.api.v1.atas_professores.urls")),
    path("cursos/", include("apps.api.v1.cursos.urls")),
    path("declaracoes/", include("apps.api.v1.declaracoes.urls")),
    path("frequencias/", include("apps.api.v1.frequencias.urls")),
    path("guias-transferencia/", include("apps.api.v1.guias_transferencia.urls")),
    path("historicos/", include("apps.api.v1.historicos.urls")),
    path("processos/", include("apps.api.v1.processos.urls")),
    path("servidores/", include("apps.api.v1.servidores.urls")),
    path("setores/", include("apps.api.v1.setores.urls")),
    path("transferencias/", include("apps.api.v1.transferencias.urls")),
    path("usuarios/", include("apps.api.v1.usuarios.urls")),
    path("unidades/", include("apps.api.v1.unidades.urls")),
    path("turmas/", include("apps.api.v1.turmas.urls")),
    path("matriculas/", include("apps.api.v1.matriculas.urls")),
    path("notas/", include("apps.api.v1.notas.urls")),
]