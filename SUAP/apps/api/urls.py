from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UnidadeViewSet

router = DefaultRouter()
router.register(r"unidades", UnidadeViewSet, basename="unidade")

urlpatterns = [
    path("v1/", include(router.urls)),
]