from django.urls import path

from .views import OfertaCursoDetailApiView, OfertaCursoListApiView, OfertaCursoLogsApiView, OfertaCursoSyncMoodleApiView

app_name = 'api_v1_ofertas'

urlpatterns = [
    path('', OfertaCursoListApiView.as_view(), name='list'),
    path('<int:pk>/', OfertaCursoDetailApiView.as_view(), name='detail'),
    path('<int:pk>/logs/', OfertaCursoLogsApiView.as_view(), name='logs'),
    path('<int:pk>/sincronizar-moodle/', OfertaCursoSyncMoodleApiView.as_view(), name='sync-moodle'),
]