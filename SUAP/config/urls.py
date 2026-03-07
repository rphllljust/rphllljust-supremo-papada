from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

handler403 = "apps.core.views.acesso_negado"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ensino/", include(("apps.core.urls", "core"), namespace="core")),

    path("", include(("apps.dashboard.urls", "dashboard"), namespace="dashboard")),
    path("accounts/", include(("apps.accounts.urls", "accounts"), namespace="accounts")),

    path("usuarios/", include(("apps.usuarios.urls", "usuarios"), namespace="usuarios")),
    path("alunos/", include("apps.usuarios.alunos.urls")),
    path("cursos/", include(("apps.cursos.urls", "cursos"), namespace="cursos")),
    path("turmas/", include(("apps.turmas.urls", "turmas"), namespace="turmas")),
    path("matriculas/", include(("apps.matriculas.urls", "matriculas"), namespace="matriculas")),
    path("unidades/", include(("apps.unidades.urls", "unidades"), namespace="unidades")),
    path("notas/", include(("apps.notas.urls", "notas"), namespace="notas")),
    path("frequencia/", include(("apps.frequencia.urls", "frequencia"), namespace="frequencia")),
    path("agenda/", include(("apps.agenda.urls", "agenda"), namespace="agenda")),

    path("processos/", include(("apps.processos.urls", "processos"), namespace="processos")),
    path("arquivo/", include(("apps.arquivo.urls", "arquivo"), namespace="arquivo")),
    path("documentos/", include(("apps.documentos.urls", "documentos"), namespace="documentos")),
    path("auditoria/", include(("apps.auditoria.urls", "auditoria"), namespace="auditoria")),
    path("inscricoes/", include(("apps.inscricoes.urls", "inscricoes"), namespace="inscricoes")),
    path("estagio/", include(("apps.estagio.urls", "estagio"), namespace="estagio")),

    path("api/v1/", include("apps.api.v1.urls")),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
