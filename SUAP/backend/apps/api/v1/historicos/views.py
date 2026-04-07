from django.db.models import Q
from django.http import FileResponse, Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.documentos.models import HistoricoEscolarTecnicoDocumento
from apps.documentos.services.historico_escolar_tecnico import (
    HistoricoTecnicoError,
    cancelar_historico,
    consolidar_dados_historico,
    emitir_historico,
    reemitir_historico,
    serializar_itens_consolidacao,
    validar_historico_publicamente,
)
from apps.usuarios.models import PerfilUsuario

from .serializers import (
    CancelarHistoricoSerializer,
    EmitirHistoricoSerializer,
    HistoricoEscolarTecnicoDocumentoSerializer,
    HistoricoPreviewSerializer,
    ReemitirHistoricoSerializer,
)


class HistoricoEscolarTecnicoViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    serializer_class = HistoricoEscolarTecnicoDocumentoSerializer
    pagination_class = StandardResultsSetPagination
    queryset = (
        HistoricoEscolarTecnicoDocumento.objects.select_related(
            "aluno__pessoa",
            "matricula__turma",
            "matricula__curso",
            "curso",
            "emitido_por__pessoa",
            "historico_substituido",
        )
        .prefetch_related("itens", "eventos")
        .order_by("-data_emissao", "-id")
    )

    def get_permissions(self):
        if self.action in {"emitir", "reemitir", "cancelar"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if user and getattr(user, "is_authenticated", False) and not getattr(user, "is_superuser", False):
            if user.tipo == PerfilUsuario.ALUNO:
                queryset = queryset.filter(aluno=user)
            elif user.tipo == PerfilUsuario.PROFESSOR:
                queryset = queryset.filter(matricula__turma__professor_responsavel=user)

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(numero_registro__icontains=search)
                | Q(codigo_validacao__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(aluno__username__icontains=search)
                | Q(aluno__cpf__icontains=search)
                | Q(aluno__first_name__icontains=search)
                | Q(aluno__last_name__icontains=search)
                | Q(aluno__pessoa__nome_completo__icontains=search)
                | Q(curso__nome__icontains=search)
            )

        status_param = self.request.query_params.get("status", "").strip().upper()
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.distinct()

    @action(detail=False, methods=["post"], url_path="emitir")
    def emitir(self, request):
        serializer = EmitirHistoricoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            documento = emitir_historico(
                matricula_id=serializer.validated_data.get("matricula_id"),
                aluno_id=serializer.validated_data.get("aluno_id"),
                emitido_por=request.user,
                request=request,
                observacoes=serializer.validated_data.get("observacoes", ""),
                livro=serializer.validated_data.get("livro", ""),
                folha=serializer.validated_data.get("folha", ""),
                pagina=serializer.validated_data.get("pagina", ""),
            )
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        payload = self.get_serializer(documento).data
        return Response(payload, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="reemitir")
    def reemitir(self, request, pk=None):
        serializer = ReemitirHistoricoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            documento = reemitir_historico(
                historico_id=int(pk),
                motivo=serializer.validated_data["motivo"],
                usuario=request.user,
                request=request,
            )
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(documento).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancelar")
    def cancelar(self, request, pk=None):
        serializer = CancelarHistoricoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            documento = cancelar_historico(
                historico_id=int(pk),
                motivo=serializer.validated_data["motivo"],
                usuario=request.user,
                request=request,
            )
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(self.get_serializer(documento).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="pdf")
    def pdf(self, request, pk=None):
        documento = self.get_object()
        if not documento.pdf_arquivo:
            raise Http404("PDF nao encontrado para este historico.")
        return FileResponse(documento.pdf_arquivo.open("rb"), content_type="application/pdf")

    @action(detail=True, methods=["get"], url_path="preview")
    def preview(self, request, pk=None):
        documento = self.get_object()
        data = self.get_serializer(documento).data
        data["itens_resumo"] = [
            {
                "componente": item["componente_nome"],
                "ch": item["carga_horaria"],
                "nota": item["nota"],
                "frequencia": item["frequencia"],
                "resultado": item["resultado_display"],
            }
            for item in data.get("itens", [])
        ]
        return Response(data)

    @action(detail=False, methods=["get"], url_path="preview")
    def preview_emissao(self, request):
        serializer = HistoricoPreviewSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            consolidacao = consolidar_dados_historico(
                matricula_id=serializer.validated_data.get("matricula_id"),
                aluno_id=serializer.validated_data.get("aluno_id"),
            )
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "aluno_nome": consolidacao.aluno_nome,
                "aluno_cpf": consolidacao.aluno_cpf,
                "curso_nome": consolidacao.curso_nome,
                "eixo_tecnologico": consolidacao.eixo_tecnologico,
                "situacao_final": consolidacao.situacao_final,
                "carga_horaria_total": consolidacao.carga_horaria_total,
                "data_conclusao": consolidacao.data_conclusao,
                "itens": serializar_itens_consolidacao(consolidacao.itens),
                "estagios": consolidacao.estagios,
                "forma_ingresso": consolidacao.forma_ingresso,
                "municipio_unidade": consolidacao.municipio_unidade,
                "observacoes": consolidacao.observacoes,
            }
        )


class ValidacaoHistoricoPublicoViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        codigo = (request.query_params.get("codigo") or "").strip()
        try:
            payload = validar_historico_publicamente(codigo_validacao=codigo, request=request)
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        status_code = status.HTTP_200_OK if payload.get("documento_encontrado") else status.HTTP_404_NOT_FOUND
        return Response(payload, status=status_code)

    @action(detail=True, methods=["get"], url_path="")
    def retrieve(self, request, pk=None):
        try:
            payload = validar_historico_publicamente(historico_uuid=pk, request=request)
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        status_code = status.HTTP_200_OK if payload.get("documento_encontrado") else status.HTTP_404_NOT_FOUND
        return Response(payload, status=status_code)
