from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.sica.models import SicaComponenteCurricular, SicaMatrizCurricular

from .serializers import SicaComponenteCurricularSerializer, SicaMatrizCurricularSerializer


class SicaMatrizListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "sica"
    access_surface = "api"
    access_action = "view"
    serializer_class = SicaMatrizCurricularSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        self.access_action = "manage" if self.request.method == "POST" else "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = SicaMatrizCurricular.objects.select_related("curso").order_by("curso__nome", "-id")
        search = self.request.query_params.get("search", "").strip()
        curso = self.request.query_params.get("curso", "").strip()
        status_value = self.request.query_params.get("status", "").strip()

        if curso:
            queryset = queryset.filter(curso_id=curso)

        if status_value:
            queryset = queryset.filter(status=status_value)

        if search:
            queryset = queryset.filter(
                Q(curso__nome__icontains=search)
                | Q(versao__icontains=search)
                | Q(descricao__icontains=search)
            )

        return queryset


class SicaMatrizDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "sica"
    access_surface = "api"
    access_action = "view"
    serializer_class = SicaMatrizCurricularSerializer
    queryset = SicaMatrizCurricular.objects.select_related("curso")

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class SicaComponenteListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "sica"
    access_surface = "api"
    access_action = "view"
    serializer_class = SicaComponenteCurricularSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        self.access_action = "manage" if self.request.method == "POST" else "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = SicaComponenteCurricular.objects.select_related(
            "matriz",
            "matriz__curso",
        ).prefetch_related(
            "prerequisitos",
            "equivalencias",
        ).order_by("periodo", "componente", "id")

        search = self.request.query_params.get("search", "").strip()
        matriz = self.request.query_params.get("matriz", "").strip()
        curso = self.request.query_params.get("curso", "").strip()
        periodo = self.request.query_params.get("periodo", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()

        if matriz:
            queryset = queryset.filter(matriz_id=matriz)

        if curso:
            queryset = queryset.filter(matriz__curso_id=curso)

        if periodo:
            queryset = queryset.filter(periodo=periodo)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if search:
            queryset = queryset.filter(
                Q(componente__icontains=search)
                | Q(ementa__icontains=search)
                | Q(matriz__curso__nome__icontains=search)
                | Q(matriz__versao__icontains=search)
            )

        return queryset


class SicaComponenteDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "sica"
    access_surface = "api"
    access_action = "view"
    serializer_class = SicaComponenteCurricularSerializer
    queryset = SicaComponenteCurricular.objects.select_related("matriz", "matriz__curso").prefetch_related(
        "prerequisitos",
        "equivalencias",
    )

    def get_permissions(self):
        if self.request.method in {"PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()
