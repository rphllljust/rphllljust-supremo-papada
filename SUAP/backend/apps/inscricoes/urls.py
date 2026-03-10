from django.urls import path

from . import views

app_name = "inscricoes"

urlpatterns = [
    # Publicações de Inscrição (Captação)
    path("", views.publicacoes_list, name="publicacoes_list"),
    path("novo/", views.publicacao_create, name="publicacao_create"),
    path("<int:pk>/editar/", views.publicacao_update, name="publicacao_update"),
    path("<int:pk>/excluir/", views.publicacao_delete, name="publicacao_delete"),

    # Inscrições
    path("inscricoes/", views.inscricoes_list, name="inscricoes_list"),
    path("inscricoes/novo/", views.inscricao_create, name="inscricao_create"),
    path("inscricoes/<int:pk>/validar/", views.inscricao_validar, name="inscricao_validar"),
    path("inscricoes/<int:pk>/excluir/", views.inscricao_delete, name="inscricao_delete"),
    path("inscricoes/<int:pk>/documentos/", views.inscricao_documentos, name="inscricao_documentos"),

    # Processo Seletivo
    path("seletivos/", views.seletivos_list, name="seletivos_list"),
    path("seletivos/novo/", views.seletivo_create, name="seletivo_create"),
    path("seletivos/<int:pk>/editar/", views.seletivo_update, name="seletivo_update"),
    path("seletivos/<int:pk>/excluir/", views.seletivo_delete, name="seletivo_delete"),

    # Candidatos / Convocação
    path("candidatos/", views.candidatos_list, name="candidatos_list"),
    path("candidatos/novo/", views.candidato_create, name="candidato_create"),
    path("candidatos/<int:pk>/editar/", views.candidato_update, name="candidato_update"),
    path("candidatos/<int:pk>/excluir/", views.candidato_delete, name="candidato_delete"),

    # Recursos
    path("recursos/", views.recursos_list, name="recursos_list"),
    path("recursos/novo/", views.recurso_create, name="recurso_create"),
    path("recursos/<int:pk>/decisao/", views.recurso_decisao, name="recurso_decisao"),
    path("recursos/<int:pk>/excluir/", views.recurso_delete, name="recurso_delete"),
]
