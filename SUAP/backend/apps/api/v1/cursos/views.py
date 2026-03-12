from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.cursos.models import AreaCurso, ComponenteCurricular, Curso

from .serializers import AreaCursoSerializer, ComponenteCurricularSerializer, CursoSerializer, EixoTecnologicoSerializer


class EixoTecnologicoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = EixoTecnologicoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        search = self.request.query_params.get("search", "").strip()
        queryset = Curso.objects.exclude(eixo_tecnologico="")

        if search:
            queryset = queryset.filter(eixo_tecnologico__icontains=search)

        return queryset.values("eixo_tecnologico").distinct().order_by("eixo_tecnologico")


class ComponenteCurricularListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = ComponenteCurricularSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_base_queryset(self):
        return ComponenteCurricular.objects.select_related("curso").order_by("nome", "id")

    def apply_filters(self, queryset, include_tab=True):
        params = self.request.query_params
        search = (params.get("search") or params.get("q") or "").strip()
        sigla = params.get("sigla", "").strip()
        ativo = params.get("ativo", "").strip()
        tipo_componente = (params.get("tipo_componente") or params.get("tipo_id") or "").strip()
        nivel_ensino = (params.get("nivel_ensino") or params.get("nivel_id") or "").strip()
        matriz_curricular = (params.get("matriz_curricular") or params.get("matriz_id") or "").strip()
        grupo_atuacao = (params.get("grupo_atuacao") or params.get("grupo_id") or "").strip()

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(sigla__icontains=search)
                | Q(sigla_qacademico__icontains=search)
                | Q(observacao__icontains=search)
            )

        if sigla:
            queryset = queryset.filter(sigla__icontains=sigla)

        if ativo == "SIM":
            queryset = queryset.filter(ativo=True)
        elif ativo == "NAO":
            queryset = queryset.filter(ativo=False)

        if tipo_componente:
            queryset = queryset.filter(tipo_componente=tipo_componente)
        if nivel_ensino:
            queryset = queryset.filter(nivel_ensino=nivel_ensino)
        if matriz_curricular:
            queryset = queryset.filter(curso_id=matriz_curricular)
        if grupo_atuacao:
            queryset = queryset.filter(grupo_atuacao=grupo_atuacao)

        if include_tab:
            aba = params.get("aba", "TODOS").strip() or "TODOS"
            if aba == "NAO_UTILIZADOS":
                queryset = queryset.none()

        return queryset

    def get_queryset(self):
        return self.apply_filters(self.get_base_queryset(), include_tab=True)

    def build_summary(self, queryset):
        cursos = queryset.values("curso_id", "curso__nome").distinct().order_by("curso__nome")
        tipos = queryset.exclude(tipo_componente="").values_list("tipo_componente", flat=True).distinct().order_by("tipo_componente")
        niveis = queryset.exclude(nivel_ensino="").values_list("nivel_ensino", flat=True).distinct().order_by("nivel_ensino")
        grupos = queryset.exclude(grupo_atuacao="").values_list("grupo_atuacao", flat=True).distinct().order_by("grupo_atuacao")

        return {
            "tab_counts": {
                "TODOS": queryset.count(),
                "UTILIZADOS": queryset.count(),
                "NAO_UTILIZADOS": 0,
            },
            "filter_options": {
                "tipos_componente": [{"value": value, "label": value} for value in tipos],
                "niveis_ensino": [{"value": value, "label": value} for value in niveis],
                "matrizes_curriculares": [
                    {"value": item["curso_id"], "label": item["curso__nome"]}
                    for item in cursos
                    if item["curso_id"]
                ],
                "grupos_atuacao": [{"value": value, "label": value} for value in grupos],
            },
        }

    def list(self, request, *args, **kwargs):
        filtered_queryset = self.apply_filters(self.get_base_queryset(), include_tab=False)
        response = super().list(request, *args, **kwargs)
        response.data["summary"] = self.build_summary(filtered_queryset)
        return response


class ComponenteCurricularDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    serializer_class = ComponenteCurricularSerializer
    queryset = ComponenteCurricular.objects.select_related("curso")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class AreaCursoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = AreaCursoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = AreaCurso.objects.order_by("descricao")
        search = self.request.query_params.get("search", "").strip()

        if search:
            queryset = queryset.filter(
                Q(descricao__icontains=search)
                | Q(codigo_cine__icontains=search)
                | Q(codigo_area_detalhada__icontains=search)
                | Q(codigo_area_especifica__icontains=search)
                | Q(codigo_area_geral__icontains=search)
                | Q(cine__icontains=search)
                | Q(area_detalhada__icontains=search)
                | Q(area_especifica__icontains=search)
                | Q(area_geral__icontains=search)
            )

        return queryset


class AreaCursoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    serializer_class = AreaCursoSerializer
    queryset = AreaCurso.objects.order_by("descricao")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class CursoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = CursoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Curso.objects.select_related("unidade", "area_curso").order_by("nome")
        search = self.request.query_params.get("search", "").strip()
        apenas_tecnicos = self.request.query_params.get("apenas_tecnicos", "").strip().lower()
        apenas_superiores = self.request.query_params.get("apenas_superiores", "").strip().lower()
        area_curso = self.request.query_params.get("area_curso", "").strip()

        if apenas_tecnicos in {"1", "true", "sim", "yes"}:
            queryset = queryset.exclude(eixo_tecnologico="")
        if apenas_superiores in {"1", "true", "sim", "yes"}:
            queryset = queryset.filter(eixo_tecnologico="")
        if area_curso:
            queryset = queryset.filter(area_curso_id=area_curso)

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(sigla__icontains=search)
                | Q(unidade__nome__icontains=search)
                | Q(area_curso__descricao__icontains=search)
                | Q(eixo_tecnologico__icontains=search)
            )

        return queryset.distinct()


class CursoDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = CursoSerializer
    queryset = Curso.objects.select_related("unidade", "area_curso")