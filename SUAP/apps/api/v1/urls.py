from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.api.v1.unidades.views import UnidadeViewSet
from apps.api.v1.turmas.views import TurmaViewSet
from apps.api.v1.matriculas.views import MatriculaViewSet
from apps.api.v1.usuarios.views import UsuarioViewSet

router = DefaultRouter()
router.register(r"unidades", UnidadeViewSet, basename="unidade")
router.register(r"turmas", TurmaViewSet, basename="turma")
router.register(r"matriculas", MatriculaViewSet, basename="matricula")
router.register(r"usuarios", UsuarioViewSet, basename="usuario")

urlpatterns = [
    path("", include(router.urls)),
]