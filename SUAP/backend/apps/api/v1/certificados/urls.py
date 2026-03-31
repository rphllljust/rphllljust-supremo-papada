from django.urls import path

from .views import (
    AssinaturaCertificadoDetailApiView,
    AssinaturaCertificadoListCreateApiView,
    CertificadoCancelarApiView,
    CertificadoEmitidoDetailApiView,
    CertificadoEmitidoListApiView,
    CertificadoPdfApiView,
    CertificadoPreviewApiView,
    CertificadoQrCodeApiView,
    CertificadoReemitirApiView,
    CertificadoReimprimirApiView,
    CertificadoStatusValidacaoApiView,
    CertificadoValidarPublicoApiView,
    ConfiguracaoVisualCertificadoDetailApiView,
    ConfiguracaoVisualCertificadoListCreateApiView,
    EmitirCertificadoApiView,
    EmitirCertificadoLoteApiView,
    HistoricoEmissaoCertificadoListApiView,
    ModeloCertificadoDetailApiView,
    ModeloCertificadoListCreateApiView,
    PreviewRascunhoCertificadoApiView,
)

app_name = "api_v1_certificados"

urlpatterns = [
    path("modelos/", ModeloCertificadoListCreateApiView.as_view(), name="modelos-list"),
    path("modelos/<int:pk>/", ModeloCertificadoDetailApiView.as_view(), name="modelos-detail"),

    path("assinaturas/", AssinaturaCertificadoListCreateApiView.as_view(), name="assinaturas-list"),
    path("assinaturas/<int:pk>/", AssinaturaCertificadoDetailApiView.as_view(), name="assinaturas-detail"),

    path("configuracoes-visuais/", ConfiguracaoVisualCertificadoListCreateApiView.as_view(), name="configuracoes-list"),
    path("configuracoes-visuais/<int:pk>/", ConfiguracaoVisualCertificadoDetailApiView.as_view(), name="configuracoes-detail"),

    path("emitidos/", CertificadoEmitidoListApiView.as_view(), name="emitidos-list"),
    path("emitidos/<int:pk>/", CertificadoEmitidoDetailApiView.as_view(), name="emitidos-detail"),
    path("emitidos/<int:pk>/preview/", CertificadoPreviewApiView.as_view(), name="emitidos-preview"),
    path("emitidos/<int:pk>/pdf/", CertificadoPdfApiView.as_view(), name="emitidos-pdf"),
    path("emitidos/<int:pk>/reimprimir/", CertificadoReimprimirApiView.as_view(), name="emitidos-reimprimir"),
    path("emitidos/<int:pk>/reemitir/", CertificadoReemitirApiView.as_view(), name="emitidos-reemitir"),
    path("emitidos/<int:pk>/cancelar/", CertificadoCancelarApiView.as_view(), name="emitidos-cancelar"),
    path("emitidos/<int:pk>/qrcode/", CertificadoQrCodeApiView.as_view(), name="emitidos-qrcode"),
    path("emitidos/<int:pk>/status-validacao/", CertificadoStatusValidacaoApiView.as_view(), name="emitidos-status-validacao"),

    path("emitir/", EmitirCertificadoApiView.as_view(), name="emitir"),
    path("emitir-lote/", EmitirCertificadoLoteApiView.as_view(), name="emitir-lote"),
    path("preview/", PreviewRascunhoCertificadoApiView.as_view(), name="preview-rascunho"),

    path("validar/<str:codigo_validacao>/", CertificadoValidarPublicoApiView.as_view(), name="validar-publico"),
    path("historico/", HistoricoEmissaoCertificadoListApiView.as_view(), name="historico"),
]
