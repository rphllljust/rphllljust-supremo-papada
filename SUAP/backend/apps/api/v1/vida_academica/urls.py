from django.urls import path

from .views import (
    AgendaAcademicaListApiView,
    AproveitamentoEstudosDetailApiView,
    AproveitamentoEstudosListApiView,
    CertificadoDiplomaDetailApiView,
    CertificadoDiplomaListApiView,
    DependenciaAcademicaDetailApiView,
    DependenciaAcademicaListApiView,
    VidaAcademicaDetailApiView,
    VidaAcademicaListApiView,
    VidaAcademicaStatusActionApiView,
)

app_name = "api_v1_vida_academica"

urlpatterns = [
    path("", VidaAcademicaListApiView.as_view(), name="list"),
    path("agenda/", AgendaAcademicaListApiView.as_view(), name="agenda"),
    path("aproveitamentos/", AproveitamentoEstudosListApiView.as_view(), name="aproveitamentos-list"),
    path("aproveitamentos/<int:pk>/", AproveitamentoEstudosDetailApiView.as_view(), name="aproveitamentos-detail"),
    path("certificados-diplomas/", CertificadoDiplomaListApiView.as_view(), name="certificados-diplomas-list"),
    path("certificados-diplomas/<int:pk>/", CertificadoDiplomaDetailApiView.as_view(), name="certificados-diplomas-detail"),
    path("dependencias/", DependenciaAcademicaListApiView.as_view(), name="dependencias-list"),
    path("dependencias/<int:pk>/", DependenciaAcademicaDetailApiView.as_view(), name="dependencias-detail"),
    path("<int:pk>/", VidaAcademicaDetailApiView.as_view(), name="detail"),
    path("<int:pk>/acao-status/", VidaAcademicaStatusActionApiView.as_view(), name="acao-status"),
]
