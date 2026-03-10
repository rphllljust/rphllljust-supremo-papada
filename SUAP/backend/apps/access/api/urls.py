from django.urls import path

from .views import AvaExportPreviewView

app_name = "access_api"

urlpatterns = [
    path("ava-export/preview/", AvaExportPreviewView.as_view(), name="ava_export_preview"),
]
