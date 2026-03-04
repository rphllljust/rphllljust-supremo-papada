from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),

    path("usuarios/", include(("apps.usuarios.urls", "usuarios"), namespace="usuarios")),
    path("cursos/", include(("apps.cursos.urls", "cursos"), namespace="cursos")),
    path("turmas/", include(("apps.turmas.urls", "turmas"), namespace="turmas")),
    path("matriculas/", include(("apps.matriculas.urls", "matriculas"), namespace="matriculas")),
    path("unidades/", include(("apps.unidades.urls", "unidades"), namespace="unidades")),
    path("notas/", include(("apps.notas.urls", "notas"), namespace="notas")),
    path("frequencia/", include(("apps.frequencia.urls", "frequencia"), namespace="frequencia")),
    path("agenda/", include(("apps.agenda.urls", "agenda"), namespace="agenda")),

    path("api/v1/", include("apps.api.v1.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)