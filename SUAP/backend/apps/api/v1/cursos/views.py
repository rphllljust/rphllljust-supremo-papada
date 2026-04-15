from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.cursos.models import AreaCurso, CalendarioLetivo, ComponenteCurricular, Curso, EixoTecnologico, MatrizCurricular, NivelEnsino, TipoComponente
from apps.cursos.services import clone_matriz_curricular, close_matriz_curricular, create_course_offer_from_matriz, publish_matriz_curricular, set_matriz_as_current, sync_matriz_curricular_template_to_moodle

from .serializers import AreaCursoSerializer, CalendarioLetivoSerializer, ComponenteCurricularSerializer, CursoSerializer, EixoTecnologicoManageSerializer, EixoTecnologicoSerializer, MatrizCurricularLogSerializer, MatrizCurricularSerializer, NivelEnsinoSerializer, TipoComponenteSerializer


class EixoTecnologicoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EixoTecnologicoManageSerializer
        return EixoTecnologicoSerializer

    def get_queryset(self):
        search = self.request.query_params.get("search", "").strip()
        queryset = EixoTecnologico.objects.order_by("descricao")

        if search:
            queryset = queryset.filter(descricao__icontains=search)

        return queryset


class EixoTecnologicoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    serializer_class = EixoTecnologicoManageSerializer
    queryset = EixoTecnologico.objects.order_by("descricao")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def perform_destroy(self, instance):
        Curso.objects.filter(eixo_tecnologico=instance.descricao).update(eixo_tecnologico="")
        instance.delete()


class TipoComponenteListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_serializer_class(self):
        return TipoComponenteSerializer

    def get_queryset(self):
        queryset = TipoComponente.objects.order_by("descricao")
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(descricao__icontains=search)
        return queryset


class TipoComponenteDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    serializer_class = TipoComponenteSerializer
    queryset = TipoComponente.objects.order_by("descricao")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class NivelEnsinoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_serializer_class(self):
        return NivelEnsinoSerializer

    def get_queryset(self):
        queryset = NivelEnsino.objects.order_by("descricao")
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(descricao__icontains=search)
        return queryset


class NivelEnsinoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    serializer_class = NivelEnsinoSerializer
    queryset = NivelEnsino.objects.order_by("descricao")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


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
        return ComponenteCurricular.objects.select_related(
            "curso",
            "matriz_curricular",
            "matriz_curricular__curso_base",
            "tipo_componente_catalogo",
            "nivel_ensino_catalogo",
        ).order_by("nome", "id")

    def apply_filters(self, queryset, include_tab=True):
        params = self.request.query_params
        search = (params.get("search") or params.get("q") or "").strip()
        sigla = params.get("sigla", "").strip()
        ativo = params.get("ativo", "").strip()
        tipo_componente = (params.get("tipo_componente") or "").strip()
        tipo_id = (params.get("tipo_id") or "").strip()
        nivel_ensino = (params.get("nivel_ensino") or "").strip()
        nivel_id = (params.get("nivel_id") or "").strip()
        matriz_curricular = (params.get("matriz_curricular") or params.get("matriz_id") or "").strip()
        grupo_atuacao = (params.get("grupo_atuacao") or params.get("grupo_id") or "").strip()
        eixo_tecnologico = (params.get("eixo_tecnologico") or params.get("eixo_id") or "").strip()

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

        if tipo_id:
            queryset = queryset.filter(tipo_componente_catalogo_id=tipo_id)
        elif tipo_componente:
            queryset = queryset.filter(Q(tipo_componente_catalogo__descricao=tipo_componente) | Q(tipo_componente=tipo_componente))

        if nivel_id:
            queryset = queryset.filter(nivel_ensino_catalogo_id=nivel_id)
        elif nivel_ensino:
            queryset = queryset.filter(Q(nivel_ensino_catalogo__descricao=nivel_ensino) | Q(nivel_ensino=nivel_ensino))
        if matriz_curricular:
            queryset = queryset.filter(Q(matriz_curricular_id=matriz_curricular) | Q(curso_id=matriz_curricular))
        if grupo_atuacao:
            queryset = queryset.filter(grupo_atuacao=grupo_atuacao)
        if eixo_tecnologico:
            queryset = queryset.filter(curso__eixo_tecnologico=eixo_tecnologico)

        if include_tab:
            aba = params.get("aba", "TODOS").strip() or "TODOS"
            if aba == "NAO_UTILIZADOS":
                queryset = queryset.none()

        return queryset

    def get_queryset(self):
        return self.apply_filters(self.get_base_queryset(), include_tab=True)

    def build_summary(self, queryset):
        cursos = queryset.values(
            "curso_id",
            "curso__nome",
            "matriz_curricular_id",
            "matriz_curricular__nome",
        ).distinct().order_by("matriz_curricular__nome", "curso__nome")
        tipos = TipoComponente.objects.order_by("descricao")
        niveis = NivelEnsino.objects.order_by("descricao")
        grupos = queryset.exclude(grupo_atuacao="").values_list("grupo_atuacao", flat=True).distinct().order_by("grupo_atuacao")
        eixos = queryset.exclude(curso__eixo_tecnologico="").values_list("curso__eixo_tecnologico", flat=True).distinct().order_by("curso__eixo_tecnologico")

        matrizes = []
        vistos = set()
        for item in cursos:
            key = item["matriz_curricular_id"] or item["curso_id"]
            label = item["matriz_curricular__nome"] or item["curso__nome"]
            if not key or not label or key in vistos:
                continue
            vistos.add(key)
            matrizes.append({"value": key, "label": label})

        return {
            "tab_counts": {
                "TODOS": queryset.count(),
                "UTILIZADOS": queryset.count(),
                "NAO_UTILIZADOS": 0,
            },
            "filter_options": {
                "tipos_componente": [{"value": item.id, "label": item.descricao, "legacy_value": item.descricao} for item in tipos],
                "niveis_ensino": [{"value": item.id, "label": item.descricao, "legacy_value": item.descricao} for item in niveis],
                "matrizes_curriculares": matrizes,
                "grupos_atuacao": [{"value": value, "label": value} for value in grupos],
                "eixos_tecnologicos": [{"value": value, "label": value} for value in eixos],
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
    queryset = ComponenteCurricular.objects.select_related(
        "curso",
        "matriz_curricular",
        "matriz_curricular__curso_base",
        "tipo_componente_catalogo",
        "nivel_ensino_catalogo",
    )

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


class CursoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = CursoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = Curso.objects.select_related("unidade", "area_curso").order_by("nome")
        search = self.request.query_params.get("search", "").strip()
        tipo_curso = self.request.query_params.get("tipo_curso", "").strip().lower()
        apenas_tecnicos = self.request.query_params.get("apenas_tecnicos", "").strip().lower()
        apenas_superiores = self.request.query_params.get("apenas_superiores", "").strip().lower()
        area_curso = self.request.query_params.get("area_curso", "").strip()

        if tipo_curso:
            queryset = queryset.filter(tipo_curso=tipo_curso)
        if apenas_tecnicos in {"1", "true", "sim", "yes"}:
            queryset = queryset.filter(tipo_curso="tecnico")
        if apenas_superiores in {"1", "true", "sim", "yes"}:
            queryset = queryset.filter(tipo_curso="itinerante")
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


class CursoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = CursoSerializer
    queryset = Curso.objects.select_related("unidade", "area_curso", "matriz_curricular")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class CursoCalendariosApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = 'cursos'
    access_surface = 'api'
    access_action = 'view'
    serializer_class = CalendarioLetivoSerializer

    def get_queryset(self):
        return CalendarioLetivo.objects.filter(curso_id=self.kwargs['pk']).select_related('curso').order_by('-ano_letivo', '-data_inicio', 'id')


class MatrizCurricularListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"
    serializer_class = MatrizCurricularSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = MatrizCurricular.objects.select_related("curso_base", "curso_base__unidade", "curso_base__area_curso").prefetch_related("componentes", "logs")
        params = self.request.query_params
        search = params.get("search", "").strip()
        curso_base = params.get("curso_base", "").strip()
        ano_referencia = params.get("ano_referencia", "").strip()
        status = params.get("status", "").strip().upper()
        ativa = params.get("ativa", "").strip().lower()

        if curso_base:
            queryset = queryset.filter(curso_base_id=curso_base)
        if ano_referencia:
            queryset = queryset.filter(ano_referencia=ano_referencia)
        if status:
            queryset = queryset.filter(status=status)
        if ativa in {"1", "true", "sim", "yes"}:
            queryset = queryset.filter(ativa=True)
        elif ativa in {"0", "false", "nao", "não", "no"}:
            queryset = queryset.filter(ativa=False)
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(curso_base__nome__icontains=search)
                | Q(curso_base__sigla__icontains=search)
                | Q(descricao__icontains=search)
            )

        return queryset.order_by("-ano_referencia", "nome", "versao")


class MatrizCurricularDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    serializer_class = MatrizCurricularSerializer
    queryset = MatrizCurricular.objects.select_related("curso_base", "curso_base__unidade", "curso_base__area_curso").prefetch_related("componentes", "logs")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def perform_destroy(self, instance):
        if instance.status == 'VIGENTE':
            raise ValidationError('Matrizes vigentes não podem ser removidas. Encerre ou substitua a vigência antes de excluir.')
        if instance.cursos_ofertados.exists():
            raise ValidationError('Não é possível remover uma matriz que já possui ofertas vinculadas.')
        instance.delete()


class MatrizCurricularComponentesApiView(generics.ListCreateAPIView):
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

    def get_matriz(self):
        return MatrizCurricular.objects.select_related("curso_base").get(pk=self.kwargs["pk"])

    def get_queryset(self):
        matriz = self.get_matriz()
        return ComponenteCurricular.objects.select_related("curso", "matriz_curricular", "matriz_curricular__curso_base").filter(matriz_curricular=matriz).order_by("modulo_numero", "ordem_no_modulo", "ordem", "nome")

    def perform_create(self, serializer):
        matriz = self.get_matriz()
        serializer.save(matriz_curricular=matriz, curso=matriz.curso_base)


class MatrizCurricularLogsApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk):
        matriz = MatrizCurricular.objects.prefetch_related("logs").get(pk=pk)
        serializer = MatrizCurricularLogSerializer(matriz.logs.all(), many=True)
        return Response(serializer.data)


class MatrizCurricularTemplateStatusApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base").get(pk=pk)
        serializer = MatrizCurricularSerializer(matriz, context={"request": request})
        return Response(serializer.data.get("template_status", {}))


class MatrizCurricularSyncTemplateApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base").get(pk=pk)
        unidade_codigo = (request.data.get("unidade_codigo") or request.query_params.get("unidade_codigo") or "sede").strip().lower()
        result = sync_matriz_curricular_template_to_moodle(matriz, unidade_codigo=unidade_codigo)
        serializer = MatrizCurricularSerializer(result["matriz"], context={"request": request})
        return Response(
            {
                "detail": "Curso modelo da matriz sincronizado com o Moodle.",
                "matriz": serializer.data,
                "moodle": result["moodle"],
            }
        )


class MatrizCurricularCloneApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base").prefetch_related("componentes").get(pk=pk)
        payload = request.data or {}
        clone = clone_matriz_curricular(
            matriz,
            versao=payload.get('versao'),
            nome=payload.get('nome'),
            ano_referencia=payload.get('ano_referencia'),
            descricao=payload.get('descricao'),
        )
        serializer = MatrizCurricularSerializer(clone, context={"request": request})
        return Response({"detail": "Matriz curricular clonada com sucesso.", "matriz": serializer.data})


class MatrizCurricularPublishApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base").get(pk=pk)
        try:
            matriz = publish_matriz_curricular(matriz)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        serializer = MatrizCurricularSerializer(matriz, context={"request": request})
        return Response({"detail": "Matriz curricular publicada com sucesso.", "matriz": serializer.data})


class MatrizCurricularCloseApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base").get(pk=pk)
        matriz = close_matriz_curricular(matriz)
        serializer = MatrizCurricularSerializer(matriz, context={"request": request})
        return Response({"detail": "Matriz curricular encerrada com sucesso.", "matriz": serializer.data})


class MatrizCurricularSetCurrentApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base").get(pk=pk)
        try:
            matriz = set_matriz_as_current(matriz)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        serializer = MatrizCurricularSerializer(matriz, context={"request": request})
        return Response({"detail": "Matriz curricular definida como vigente.", "matriz": serializer.data})


class MatrizCurricularGerarOfertaApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "cursos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk):
        matriz = MatrizCurricular.objects.select_related("curso_base", "curso_base__unidade").get(pk=pk)
        payload = request.data or {}
        result = create_course_offer_from_matriz(
            matriz,
            nome=payload.get("nome"),
            sigla=payload.get("sigla"),
            unidade_id=payload.get("unidade") or matriz.curso_base.unidade_id,
            unidade_codigo=(payload.get("unidade_codigo") or request.query_params.get("unidade_codigo") or "sede").strip().lower(),
            copiar_para_moodle=payload.get("copiar_para_moodle", True),
        )
        serializer = CursoSerializer(result["curso"], context={"request": request})
        return Response(
            {
                "detail": "Oferta real criada a partir da matriz curricular.",
                "curso": serializer.data,
                "moodle": result.get("moodle"),
            }
        )
