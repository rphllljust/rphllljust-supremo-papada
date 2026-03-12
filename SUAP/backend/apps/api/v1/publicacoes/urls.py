from django.urls import path

from .views import PublicacaoInscricaoDetailApiView, PublicacaoInscricaoListApiView

app_name = "api_v1_publicacoes"

urlpatterns = [
    path("", PublicacaoInscricaoListApiView.as_view(), name="list"),
    path("<int:pk>/", PublicacaoInscricaoDetailApiView.as_view(), name="detail"),
]