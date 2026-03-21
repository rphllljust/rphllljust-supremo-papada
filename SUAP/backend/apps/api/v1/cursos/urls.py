from django.urls import path

from .views import AreaCursoDetailApiView, AreaCursoListApiView, ComponenteCurricularDetailApiView, ComponenteCurricularListApiView, CursoCalendariosApiView, CursoDetailApiView, CursoListApiView, EixoTecnologicoDetailApiView, EixoTecnologicoListApiView, MatrizCurricularCloneApiView, MatrizCurricularCloseApiView, MatrizCurricularComponentesApiView, MatrizCurricularDetailApiView, MatrizCurricularGerarOfertaApiView, MatrizCurricularListApiView, MatrizCurricularLogsApiView, MatrizCurricularPublishApiView, MatrizCurricularSetCurrentApiView, MatrizCurricularSyncTemplateApiView, MatrizCurricularTemplateStatusApiView, NivelEnsinoDetailApiView, NivelEnsinoListApiView, TipoComponenteDetailApiView, TipoComponenteListApiView

app_name = "api_v1_cursos"

urlpatterns = [
    path("componentes/", ComponenteCurricularListApiView.as_view(), name="componentes-list"),
    path("componentes/<int:pk>/", ComponenteCurricularDetailApiView.as_view(), name="componentes-detail"),
    path("matrizes-curriculares/", MatrizCurricularListApiView.as_view(), name="matrizes-list"),
    path("matrizes-curriculares/<int:pk>/", MatrizCurricularDetailApiView.as_view(), name="matrizes-detail"),
    path("matrizes-curriculares/<int:pk>/componentes/", MatrizCurricularComponentesApiView.as_view(), name="matrizes-componentes"),
    path("matrizes-curriculares/<int:pk>/logs/", MatrizCurricularLogsApiView.as_view(), name="matrizes-logs"),
    path("matrizes-curriculares/<int:pk>/template-status/", MatrizCurricularTemplateStatusApiView.as_view(), name="matrizes-template-status"),
    path("matrizes-curriculares/<int:pk>/clonar/", MatrizCurricularCloneApiView.as_view(), name="matrizes-clonar"),
    path("matrizes-curriculares/<int:pk>/publicar/", MatrizCurricularPublishApiView.as_view(), name="matrizes-publicar"),
    path("matrizes-curriculares/<int:pk>/encerrar/", MatrizCurricularCloseApiView.as_view(), name="matrizes-encerrar"),
    path("matrizes-curriculares/<int:pk>/definir-vigente/", MatrizCurricularSetCurrentApiView.as_view(), name="matrizes-definir-vigente"),
    path("matrizes-curriculares/<int:pk>/sincronizar-template-moodle/", MatrizCurricularSyncTemplateApiView.as_view(), name="matrizes-sync-template"),
    path("matrizes-curriculares/<int:pk>/gerar-oferta/", MatrizCurricularGerarOfertaApiView.as_view(), name="matrizes-gerar-oferta"),
    path("eixos-tecnologicos/", EixoTecnologicoListApiView.as_view(), name="eixos-list"),
    path("eixos-tecnologicos/<int:pk>/", EixoTecnologicoDetailApiView.as_view(), name="eixos-detail"),
    path("tipos-componentes/", TipoComponenteListApiView.as_view(), name="tipos-componentes-list"),
    path("tipos-componentes/<int:pk>/", TipoComponenteDetailApiView.as_view(), name="tipos-componentes-detail"),
    path("niveis-ensino/", NivelEnsinoListApiView.as_view(), name="niveis-ensino-list"),
    path("niveis-ensino/<int:pk>/", NivelEnsinoDetailApiView.as_view(), name="niveis-ensino-detail"),
    path("areas/", AreaCursoListApiView.as_view(), name="areas-list"),
    path("areas/<int:pk>/", AreaCursoDetailApiView.as_view(), name="areas-detail"),
    path("<int:pk>/calendarios/", CursoCalendariosApiView.as_view(), name="calendarios"),
    path("", CursoListApiView.as_view(), name="list"),
    path("<int:pk>/", CursoDetailApiView.as_view(), name="detail"),
]