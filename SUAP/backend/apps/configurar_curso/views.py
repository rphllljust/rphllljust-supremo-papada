from django.db.models import Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    CoRequisito,
    ComponenteCurricular,
    ConfiguracaoCursoWizard,
    Coordenador,
    Curso,
    CursoCoordenador,
    EstruturaCurso,
    MatrizComponente,
    MatrizCurricular,
    PreRequisito,
)
from .pagination import ConfigurarCursoPagination
from .permissions import CanAccessConfigurarCurso
from .serializers import (
    CoRequisitoSerializer,
    ComponenteCurricularSerializer,
    ConfiguracaoCursoWizardSerializer,
    CoordenadorSerializer,
    CursoCoordenadorSerializer,
    CursoSerializer,
    EstruturaCursoSerializer,
    MatrizComponenteSerializer,
    MatrizCurricularSerializer,
    PreRequisitoSerializer,
    WizardSalvarEtapaSerializer,
)
from .services import AuditoriaService, WizardService, serialize_instance


def _parse_bool(value):
    if value is None or value == "":
        return None

    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "sim", "yes", "on"}:
        return True
    if normalized in {"0", "false", "nao", "não", "no", "off"}:
        return False

    return None


class ConfigurarCursoAccessMixin:
    permission_classes = [CanAccessConfigurarCurso]
    module_name = "configurar_curso"
    access_surface = "api"
    pagination_class = ConfigurarCursoPagination

    def get_permissions(self):
        if self.action in {
            "create",
            "update",
            "partial_update",
            "destroy",
            "componentes",
            "coordenadores",
            "salvar_etapa",
            "avancar",
            "voltar",
            "concluir",
        }:
            self.access_action = "manage"
        else:
            self.access_action = "view"

        return super().get_permissions()


class AuditModelMixin:
    def perform_create(self, serializer):
        instance = serializer.save()
        AuditoriaService.registrar_criacao(self.request.user, instance, dados_novos=serializer.data)

    def perform_update(self, serializer):
        old_data = serialize_instance(self.get_object())
        instance = serializer.save()
        AuditoriaService.registrar_edicao(
            self.request.user,
            instance,
            dados_anteriores=old_data,
            dados_novos=serializer.data,
        )

    def perform_destroy(self, instance):
        old_data = serialize_instance(instance)

        if hasattr(instance, "ativo"):
            instance.ativo = False
            instance.save(update_fields=["ativo", "atualizado_em"])
            AuditoriaService.registrar_exclusao_logica(self.request.user, instance, dados_anteriores=old_data)
            return

        instance.delete()
        AuditoriaService.registrar(
            self.request.user,
            acao="excluido",
            entidade=instance._meta.label,
            entidade_id=instance.pk,
            dados_anteriores=old_data,
            dados_novos={},
        )


class EstruturaCursoViewSet(ConfigurarCursoAccessMixin, AuditModelMixin, viewsets.ModelViewSet):
    serializer_class = EstruturaCursoSerializer
    queryset = EstruturaCurso.objects.order_by("nome", "id")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        incluir_inativos = _parse_bool(self.request.query_params.get("incluir_inativos"))

        if incluir_inativos is not True:
            queryset = queryset.filter(ativo=True)

        if search:
            queryset = queryset.filter(Q(nome__icontains=search) | Q(descricao__icontains=search))

        return queryset


class MatrizCurricularViewSet(ConfigurarCursoAccessMixin, AuditModelMixin, viewsets.ModelViewSet):
    serializer_class = MatrizCurricularSerializer
    queryset = MatrizCurricular.objects.select_related("estrutura_curso").order_by("nome", "versao", "id")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        estrutura_curso = self.request.query_params.get("estrutura_curso", "").strip()
        ativo = _parse_bool(self.request.query_params.get("ativo"))

        if estrutura_curso:
            queryset = queryset.filter(estrutura_curso_id=estrutura_curso)

        if ativo is not None:
            queryset = queryset.filter(ativo=ativo)

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(codigo__icontains=search)
                | Q(versao__icontains=search)
                | Q(estrutura_curso__nome__icontains=search)
            )

        return queryset

    @action(detail=True, methods=["get", "post"], url_path="componentes")
    def componentes(self, request, pk=None):
        matriz = self.get_object()

        if request.method == "GET":
            queryset = MatrizComponente.objects.filter(matriz_curricular=matriz).select_related(
                "matriz_curricular",
                "componente_curricular",
            ).order_by("periodo", "ordem", "id")

            search = request.query_params.get("search", "").strip()
            periodo = request.query_params.get("periodo", "").strip()

            if periodo:
                queryset = queryset.filter(periodo=periodo)

            if search:
                queryset = queryset.filter(
                    Q(componente_curricular__nome__icontains=search)
                    | Q(componente_curricular__codigo__icontains=search)
                )

            page = self.paginate_queryset(queryset)
            serializer = MatrizComponenteSerializer(page if page is not None else queryset, many=True)

            if page is not None:
                return self.get_paginated_response(serializer.data)

            return Response(serializer.data)

        serializer = MatrizComponenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vinculo = serializer.save(matriz_curricular=matriz)

        AuditoriaService.registrar_criacao(
            request.user,
            vinculo,
            dados_novos=MatrizComponenteSerializer(vinculo).data,
        )

        return Response(MatrizComponenteSerializer(vinculo).data, status=status.HTTP_201_CREATED)


class ComponenteCurricularViewSet(ConfigurarCursoAccessMixin, AuditModelMixin, viewsets.ModelViewSet):
    serializer_class = ComponenteCurricularSerializer
    queryset = ComponenteCurricular.objects.order_by("nome", "id")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()
        ativo = _parse_bool(self.request.query_params.get("ativo"))

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if ativo is not None:
            queryset = queryset.filter(ativo=ativo)

        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search)
                | Q(nome__icontains=search)
                | Q(ementa__icontains=search)
            )

        return queryset


class MatrizComponenteViewSet(
    ConfigurarCursoAccessMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MatrizComponenteSerializer
    queryset = MatrizComponente.objects.select_related("matriz_curricular", "componente_curricular")

    def perform_update(self, serializer):
        old_data = serialize_instance(self.get_object())
        instance = serializer.save()
        AuditoriaService.registrar_edicao(
            self.request.user,
            instance,
            dados_anteriores=old_data,
            dados_novos=serializer.data,
        )

    def perform_destroy(self, instance):
        old_data = serialize_instance(instance)
        pk = instance.pk
        instance.delete()
        AuditoriaService.registrar(
            self.request.user,
            acao="excluido",
            entidade="configurar_curso.MatrizComponente",
            entidade_id=pk,
            dados_anteriores=old_data,
            dados_novos={},
        )


class PreRequisitoViewSet(
    ConfigurarCursoAccessMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PreRequisitoSerializer
    queryset = PreRequisito.objects.select_related("componente", "requisito")

    def get_queryset(self):
        queryset = super().get_queryset()
        matriz = self.request.query_params.get("matriz", "").strip()
        componente = self.request.query_params.get("componente", "").strip()

        if matriz:
            queryset = queryset.filter(
                componente__matrizes_vinculadas__matriz_curricular_id=matriz
            ).distinct()

        if componente:
            queryset = queryset.filter(componente_id=componente)

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditoriaService.registrar_criacao(self.request.user, instance, dados_novos=serializer.data)

    def perform_destroy(self, instance):
        old_data = serialize_instance(instance)
        pk = instance.pk
        instance.delete()
        AuditoriaService.registrar(
            self.request.user,
            acao="excluido",
            entidade="configurar_curso.PreRequisito",
            entidade_id=pk,
            dados_anteriores=old_data,
            dados_novos={},
        )


class CoRequisitoViewSet(
    ConfigurarCursoAccessMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CoRequisitoSerializer
    queryset = CoRequisito.objects.select_related("componente", "requisito")

    def get_queryset(self):
        queryset = super().get_queryset()
        matriz = self.request.query_params.get("matriz", "").strip()
        componente = self.request.query_params.get("componente", "").strip()

        if matriz:
            queryset = queryset.filter(
                componente__matrizes_vinculadas__matriz_curricular_id=matriz
            ).distinct()

        if componente:
            queryset = queryset.filter(componente_id=componente)

        return queryset

    def perform_create(self, serializer):
        instance = serializer.save()
        AuditoriaService.registrar_criacao(self.request.user, instance, dados_novos=serializer.data)

    def perform_destroy(self, instance):
        old_data = serialize_instance(instance)
        pk = instance.pk
        instance.delete()
        AuditoriaService.registrar(
            self.request.user,
            acao="excluido",
            entidade="configurar_curso.CoRequisito",
            entidade_id=pk,
            dados_anteriores=old_data,
            dados_novos={},
        )


class CursoViewSet(ConfigurarCursoAccessMixin, AuditModelMixin, viewsets.ModelViewSet):
    serializer_class = CursoSerializer
    queryset = Curso.objects.select_related("matriz_curricular", "estrutura_curso").order_by("nome", "id")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        modalidade = self.request.query_params.get("modalidade", "").strip()
        situacao = self.request.query_params.get("situacao", "").strip()
        ativo = _parse_bool(self.request.query_params.get("ativo"))

        if modalidade:
            queryset = queryset.filter(modalidade=modalidade)

        if situacao:
            queryset = queryset.filter(situacao=situacao)

        if ativo is not None:
            queryset = queryset.filter(ativo=ativo)

        if search:
            queryset = queryset.filter(
                Q(codigo__icontains=search)
                | Q(nome__icontains=search)
                | Q(nome_curto__icontains=search)
            )

        return queryset

    @action(detail=True, methods=["get", "post"], url_path="coordenadores")
    def coordenadores(self, request, pk=None):
        curso = self.get_object()

        if request.method == "GET":
            queryset = curso.vinculos_coordenadores.select_related("coordenador").order_by("-principal", "-inicio_vigencia", "id")
            serializer = CursoCoordenadorSerializer(queryset, many=True)
            return Response(serializer.data)

        serializer = CursoCoordenadorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vinculo = serializer.save(curso=curso)

        AuditoriaService.registrar_criacao(
            request.user,
            vinculo,
            dados_novos=CursoCoordenadorSerializer(vinculo).data,
        )

        return Response(CursoCoordenadorSerializer(vinculo).data, status=status.HTTP_201_CREATED)


class CoordenadorViewSet(ConfigurarCursoAccessMixin, AuditModelMixin, viewsets.ModelViewSet):
    serializer_class = CoordenadorSerializer
    queryset = Coordenador.objects.order_by("nome", "id")

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "").strip()
        ativo = _parse_bool(self.request.query_params.get("ativo"))

        if ativo is not None:
            queryset = queryset.filter(ativo=ativo)

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(email__icontains=search)
                | Q(matricula__icontains=search)
            )

        return queryset


class CursoCoordenadorViewSet(
    ConfigurarCursoAccessMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CursoCoordenadorSerializer
    queryset = CursoCoordenador.objects.select_related("curso", "coordenador")

    def perform_destroy(self, instance):
        old_data = serialize_instance(instance)
        pk = instance.pk
        instance.delete()
        AuditoriaService.registrar(
            self.request.user,
            acao="excluido",
            entidade="configurar_curso.CursoCoordenador",
            entidade_id=pk,
            dados_anteriores=old_data,
            dados_novos={},
        )


class ConfiguracaoCursoWizardViewSet(
    ConfigurarCursoAccessMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ConfiguracaoCursoWizardSerializer
    queryset = ConfiguracaoCursoWizard.objects.select_related(
        "usuario",
        "estrutura_curso",
        "matriz_curricular",
        "curso",
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        user_tipo = getattr(user, "tipo", "")

        if getattr(user, "is_superuser", False) or user_tipo == "ADMIN":
            return queryset

        return queryset.filter(usuario=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        wizard = WizardService.criar_wizard(user=request.user, payload=serializer.validated_data)
        response_serializer = self.get_serializer(wizard)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["patch"], url_path="salvar-etapa")
    def salvar_etapa(self, request, pk=None):
        wizard = self.get_object()
        serializer = WizardSalvarEtapaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dados = serializer.validated_data
        etapa = dados.pop("etapa", None)
        payload = dados.pop("payload", None)

        merged_payload = {**dados, **(payload or {})}
        wizard = WizardService.salvar_etapa(
            wizard=wizard,
            user=request.user,
            etapa=etapa,
            payload=merged_payload,
        )

        return Response(self.get_serializer(wizard).data)

    @action(detail=True, methods=["post"], url_path="avancar")
    def avancar(self, request, pk=None):
        wizard = self.get_object()
        wizard = WizardService.avancar(wizard=wizard, user=request.user)
        return Response(self.get_serializer(wizard).data)

    @action(detail=True, methods=["post"], url_path="voltar")
    def voltar(self, request, pk=None):
        wizard = self.get_object()
        wizard = WizardService.voltar(wizard=wizard, user=request.user)
        return Response(self.get_serializer(wizard).data)

    @action(detail=True, methods=["post"], url_path="resumo")
    def resumo(self, request, pk=None):
        wizard = self.get_object()
        resumo = WizardService.resumo(wizard=wizard)
        return Response({"wizard": self.get_serializer(wizard).data, "resumo": resumo})

    @action(detail=True, methods=["post"], url_path="concluir")
    def concluir(self, request, pk=None):
        wizard = self.get_object()
        wizard = WizardService.concluir(wizard=wizard, user=request.user)
        return Response({"wizard": self.get_serializer(wizard).data, "resumo": WizardService.resumo(wizard=wizard)})
