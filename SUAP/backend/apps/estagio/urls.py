from django.urls import path

from . import views

app_name = "estagio"

urlpatterns = [
    # Convênios
    path("convenios/", views.convenios_list, name="convenios_list"),
    path("convenios/novo/", views.convenio_create, name="convenio_create"),
    path("convenios/<int:pk>/editar/", views.convenio_update, name="convenio_update"),
    path("convenios/<int:pk>/excluir/", views.convenio_delete, name="convenio_delete"),

    # Estágios
    path("", views.estagios_list, name="estagios_list"),
    path("novo/", views.estagio_create, name="estagio_create"),
    path("<int:pk>/editar/", views.estagio_update, name="estagio_update"),
    path("<int:pk>/encerrar/", views.estagio_encerrar, name="estagio_encerrar"),
    path("<int:pk>/excluir/", views.estagio_delete, name="estagio_delete"),

    # Termos de Compromisso
    path("termos/", views.termos_list, name="termos_list"),
    path("termos/novo/", views.termo_create, name="termo_create"),
    path("termos/<int:pk>/editar/", views.termo_update, name="termo_update"),
    path("termos/<int:pk>/excluir/", views.termo_delete, name="termo_delete"),

    # Acompanhamentos
    path("acompanhamentos/", views.acompanhamentos_list, name="acompanhamentos_list"),
    path("acompanhamentos/novo/", views.acompanhamento_create, name="acompanhamento_create"),
    path("acompanhamentos/<int:pk>/excluir/", views.acompanhamento_delete, name="acompanhamento_delete"),
]
