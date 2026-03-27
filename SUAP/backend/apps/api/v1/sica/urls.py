from django.urls import path

from .views import (
    SicaComponenteDetailApiView,
    SicaComponenteListApiView,
    SicaMatrizDetailApiView,
    SicaMatrizListApiView,
)

app_name = "api_v1_sica"

urlpatterns = [
    path("matrizes/", SicaMatrizListApiView.as_view(), name="matrizes-list"),
    path("matrizes/<int:pk>/", SicaMatrizDetailApiView.as_view(), name="matrizes-detail"),
    path("componentes/", SicaComponenteListApiView.as_view(), name="componentes-list"),
    path("componentes/<int:pk>/", SicaComponenteDetailApiView.as_view(), name="componentes-detail"),
]
