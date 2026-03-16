from django.urls import path

from .views import AreaCursoDetailApiView, AreaCursoListApiView, ComponenteCurricularDetailApiView, ComponenteCurricularListApiView, CursoDetailApiView, CursoListApiView, EixoTecnologicoDetailApiView, EixoTecnologicoListApiView

app_name = "api_v1_cursos"

urlpatterns = [
    path("componentes/", ComponenteCurricularListApiView.as_view(), name="componentes-list"),
    path("componentes/<int:pk>/", ComponenteCurricularDetailApiView.as_view(), name="componentes-detail"),
    path("eixos-tecnologicos/", EixoTecnologicoListApiView.as_view(), name="eixos-list"),
    path("eixos-tecnologicos/<int:pk>/", EixoTecnologicoDetailApiView.as_view(), name="eixos-detail"),
    path("areas/", AreaCursoListApiView.as_view(), name="areas-list"),
    path("areas/<int:pk>/", AreaCursoDetailApiView.as_view(), name="areas-detail"),
    path("", CursoListApiView.as_view(), name="list"),
    path("<int:pk>/", CursoDetailApiView.as_view(), name="detail"),
]