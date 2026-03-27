from django.urls import path

from .views import (
    CandidatoDetailApiView,
    CandidatoListApiView,
    ChamadaProcessoSeletivoDetailApiView,
    ChamadaProcessoSeletivoListApiView,
    ConvocacaoCandidatoDetailApiView,
    ConvocacaoCandidatoListApiView,
    CotaProcessoSeletivoDetailApiView,
    CotaProcessoSeletivoListApiView,
    InscricaoDetailApiView,
    InscricaoListApiView,
    ProcessoSeletivoDetailApiView,
    ProcessoSeletivoListApiView,
)

app_name = "api_v1_inscricoes"

urlpatterns = [
    path("", InscricaoListApiView.as_view(), name="list"),
    path("<int:pk>/", InscricaoDetailApiView.as_view(), name="detail"),
    path("processos/", ProcessoSeletivoListApiView.as_view(), name="processos-list"),
    path("processos/<int:pk>/", ProcessoSeletivoDetailApiView.as_view(), name="processos-detail"),
    path("candidatos/", CandidatoListApiView.as_view(), name="candidatos-list"),
    path("candidatos/<int:pk>/", CandidatoDetailApiView.as_view(), name="candidatos-detail"),
    path("cotas/", CotaProcessoSeletivoListApiView.as_view(), name="cotas-list"),
    path("cotas/<int:pk>/", CotaProcessoSeletivoDetailApiView.as_view(), name="cotas-detail"),
    path("chamadas/", ChamadaProcessoSeletivoListApiView.as_view(), name="chamadas-list"),
    path("chamadas/<int:pk>/", ChamadaProcessoSeletivoDetailApiView.as_view(), name="chamadas-detail"),
    path("convocacoes/", ConvocacaoCandidatoListApiView.as_view(), name="convocacoes-list"),
    path("convocacoes/<int:pk>/", ConvocacaoCandidatoDetailApiView.as_view(), name="convocacoes-detail"),
]
