from django.urls import path

from .views import GuardaDocumentalDetailApiView, GuardaDocumentalListApiView

app_name = "api_v1_guarda_documental"

urlpatterns = [
    path("", GuardaDocumentalListApiView.as_view(), name="list"),
    path("<int:pk>/", GuardaDocumentalDetailApiView.as_view(), name="detail"),
]