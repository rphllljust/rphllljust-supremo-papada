from django.urls import path

from .views import (
    CoRequisitoViewSet,
    ComponenteCurricularViewSet,
    ConfiguracaoCursoWizardViewSet,
    CoordenadorViewSet,
    CursoCoordenadorViewSet,
    CursoViewSet,
    EstruturaCursoViewSet,
    MatrizComponenteViewSet,
    MatrizCurricularViewSet,
    PreRequisitoViewSet,
)

app_name = "api_v1_configurar_curso"

urlpatterns = [
    path("estruturas/", EstruturaCursoViewSet.as_view({"get": "list", "post": "create"}), name="estruturas-list"),
    path("estruturas/<int:pk>/", EstruturaCursoViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="estruturas-detail"),

    path("matrizes/", MatrizCurricularViewSet.as_view({"get": "list", "post": "create"}), name="matrizes-list"),
    path("matrizes/<int:pk>/", MatrizCurricularViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="matrizes-detail"),
    path("matrizes/<int:pk>/componentes/", MatrizCurricularViewSet.as_view({"get": "componentes", "post": "componentes"}), name="matrizes-componentes"),

    path("componentes/", ComponenteCurricularViewSet.as_view({"get": "list", "post": "create"}), name="componentes-list"),
    path("componentes/<int:pk>/", ComponenteCurricularViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="componentes-detail"),

    path("matriz-componentes/<int:pk>/", MatrizComponenteViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="matriz-componentes-detail"),

    path("pre-requisitos/", PreRequisitoViewSet.as_view({"get": "list", "post": "create"}), name="pre-requisitos-list-create"),
    path("pre-requisitos/<int:pk>/", PreRequisitoViewSet.as_view({"delete": "destroy"}), name="pre-requisitos-delete"),

    path("co-requisitos/", CoRequisitoViewSet.as_view({"get": "list", "post": "create"}), name="co-requisitos-list-create"),
    path("co-requisitos/<int:pk>/", CoRequisitoViewSet.as_view({"delete": "destroy"}), name="co-requisitos-delete"),

    path("cursos/", CursoViewSet.as_view({"get": "list", "post": "create"}), name="cursos-list"),
    path("cursos/<int:pk>/", CursoViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="cursos-detail"),
    path("cursos/<int:pk>/coordenadores/", CursoViewSet.as_view({"get": "coordenadores", "post": "coordenadores"}), name="cursos-coordenadores"),

    path("coordenadores/", CoordenadorViewSet.as_view({"get": "list", "post": "create"}), name="coordenadores-list"),
    path("coordenadores/<int:pk>/", CoordenadorViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}), name="coordenadores-detail"),

    path("curso-coordenadores/<int:pk>/", CursoCoordenadorViewSet.as_view({"get": "retrieve", "delete": "destroy"}), name="curso-coordenadores-detail"),

    path("wizard/", ConfiguracaoCursoWizardViewSet.as_view({"post": "create"}), name="wizard-create"),
    path("wizard/<int:pk>/", ConfiguracaoCursoWizardViewSet.as_view({"get": "retrieve"}), name="wizard-detail"),
    path("wizard/<int:pk>/salvar-etapa/", ConfiguracaoCursoWizardViewSet.as_view({"patch": "salvar_etapa"}), name="wizard-salvar-etapa"),
    path("wizard/<int:pk>/avancar/", ConfiguracaoCursoWizardViewSet.as_view({"post": "avancar"}), name="wizard-avancar"),
    path("wizard/<int:pk>/voltar/", ConfiguracaoCursoWizardViewSet.as_view({"post": "voltar"}), name="wizard-voltar"),
    path("wizard/<int:pk>/resumo/", ConfiguracaoCursoWizardViewSet.as_view({"post": "resumo"}), name="wizard-resumo"),
    path("wizard/<int:pk>/concluir/", ConfiguracaoCursoWizardViewSet.as_view({"post": "concluir"}), name="wizard-concluir"),
]
