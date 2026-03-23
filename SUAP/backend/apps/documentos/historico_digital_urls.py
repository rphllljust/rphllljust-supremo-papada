from django.urls import path

from .views import (
    consulta_publica_historico,
    exportar_historico_pdf,
    exportar_historico_xml,
    validar_historico_publico,
)

app_name = "historico_digital"

urlpatterns = [
    path("consulta/", consulta_publica_historico, name="consulta_publica_historico"),
    path("validar/<str:codigo>/", validar_historico_publico, name="validar_historico_publico"),
    path("historicos/<int:pk>/xml/", exportar_historico_xml, name="exportar_historico_xml"),
    path("historicos/<int:pk>/pdf/", exportar_historico_pdf, name="exportar_historico_pdf"),
]
