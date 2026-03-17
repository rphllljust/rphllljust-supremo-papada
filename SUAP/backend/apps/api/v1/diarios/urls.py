from django.urls import path

from .views import (
    DiarioDetailApiView,
    DiarioDocumentoApiView,
    DiarioFecharApiView,
    DiarioListApiView,
    DiarioMaterialCreateApiView,
    DiarioOcorrenciaCreateApiView,
    DiarioReabrirApiView,
)

app_name = 'api_v1_diarios'

urlpatterns = [
    path('', DiarioListApiView.as_view(), name='list'),
    path('<int:pk>/', DiarioDetailApiView.as_view(), name='detail'),
    path('<int:pk>/fechar/', DiarioFecharApiView.as_view(), name='fechar'),
    path('<int:pk>/reabrir/', DiarioReabrirApiView.as_view(), name='reabrir'),
    path('<int:pk>/documento/', DiarioDocumentoApiView.as_view(), name='documento'),
    path('<int:pk>/materiais/', DiarioMaterialCreateApiView.as_view(), name='materiais'),
    path('<int:pk>/ocorrencias/', DiarioOcorrenciaCreateApiView.as_view(), name='ocorrencias'),
]