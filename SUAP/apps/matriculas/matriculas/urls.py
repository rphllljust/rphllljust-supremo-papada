from django.urls import path

from . import views

urlpatterns = [
    # UC01 – Realizar Matrícula/Rematrícula
    path("", views.matriculas_list, name="matriculas_list"),
    path("novo/", views.matriculas_create, name="matriculas_create"),
    path("<int:pk>/editar/", views.matriculas_update, name="matriculas_update"),
    path("<int:pk>/excluir/", views.matriculas_delete, name="matriculas_delete"),

    # UC01 – include: Conferir Documentação / Registrar no Sistema
    path("<int:pk>/documentos/", views.matricula_documentos, name="matricula_documentos"),
    path("<int:matricula_pk>/documentos/novo/", views.documento_create, name="documento_create"),
    path("documentos/<int:pk>/editar/", views.documento_update, name="documento_update"),
    path("documentos/<int:pk>/excluir/", views.documento_delete, name="documento_delete"),

    # UC01 – extend: Abrir Pendência Documental
    path("<int:pk>/pendencias/", views.matricula_pendencias, name="matricula_pendencias"),
    path("<int:matricula_pk>/pendencias/novo/", views.pendencia_create, name="pendencia_create"),
    path("pendencias/<int:pk>/editar/", views.pendencia_update, name="pendencia_update"),
    path("pendencias/<int:pk>/excluir/", views.pendencia_delete, name="pendencia_delete"),

    # UC03 – Transferência
    path("transferencias/", views.transferencias_list, name="transferencias_list"),
    path("<int:matricula_pk>/transferencia/novo/", views.transferencia_create, name="transferencia_create"),
    path("transferencias/<int:pk>/editar/", views.transferencia_update, name="transferencia_update"),
    path("transferencias/<int:pk>/excluir/", views.transferencia_delete, name="transferencia_delete"),

    # UC04 – Consolidação Acadêmica
    path("regras/", views.regras_list, name="regras_list"),
    path("regras/novo/", views.regra_create, name="regra_create"),
    path("regras/<int:pk>/editar/", views.regra_update, name="regra_update"),
    path("<int:matricula_pk>/consolidacao/", views.consolidacao_view, name="consolidacao_view"),

    # UC02 – Emitir Documentos
    path("emitidos/", views.documentos_emitidos_list, name="documentos_emitidos_list"),
    path("<int:pk>/emitidos/", views.matricula_documentos_emitidos, name="matricula_documentos_emitidos"),
    path("<int:matricula_pk>/emitidos/novo/", views.documento_emitido_create, name="documento_emitido_create"),
    path("emitidos/<int:pk>/", views.documento_emitido_detalhe, name="documento_emitido_detalhe"),
    path("emitidos/<int:pk>/validar/", views.documento_emitido_validar, name="documento_emitido_validar"),
    path("emitidos/<int:pk>/entrega/", views.documento_emitido_entrega, name="documento_emitido_entrega"),
    path("emitidos/<int:pk>/excluir/", views.documento_emitido_delete, name="documento_emitido_delete"),

    # P01 – Fluxo de Matrícula
    path("fluxo/", views.fluxo_list, name="fluxo_list"),
    path("fluxo/novo/", views.fluxo_create, name="fluxo_create"),
    path("fluxo/<int:pk>/", views.fluxo_detalhe, name="fluxo_detalhe"),
    path("fluxo/<int:pk>/avancar/", views.fluxo_avancar, name="fluxo_avancar"),
    path("fluxo/<int:pk>/matricula/", views.fluxo_vincular_matricula, name="fluxo_vincular_matricula"),

    # P02 – Fluxo de Emissão de Histórico/Declaração
    path("emissao/", views.emissao_list, name="emissao_list"),
    path("emissao/novo/", views.emissao_create, name="emissao_create"),
    path("emissao/<int:pk>/", views.emissao_detalhe, name="emissao_detalhe"),
    path("emissao/<int:pk>/avancar/", views.emissao_avancar, name="emissao_avancar"),

    # P03 – Fluxo de Transferência
    path("transferencias/fluxo/", views.transferencia_fluxo_list, name="transferencia_fluxo_list"),
    path("transferencias/fluxo/novo/", views.transferencia_fluxo_create, name="transferencia_fluxo_create"),
    path("transferencias/fluxo/<int:pk>/", views.transferencia_fluxo_detalhe, name="transferencia_fluxo_detalhe"),
    path("transferencias/fluxo/<int:pk>/avancar/", views.transferencia_fluxo_avancar, name="transferencia_fluxo_avancar"),
]
