from django.db.models import Q
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.documentos.models import HistoricoEscolar, HistoricoEscolarDigital
from apps.documentos.services.exceptions import (
    HistoricoDigitalBusinessError,
    HistoricoDigitalValidationError,
)
from apps.documentos.services.issuance import emitir_historico_digital, revogar_historico_digital
from apps.usuarios.models import PerfilUsuario

from .serializers import (
    EmitirHistoricoDigitalSerializer,
    HistoricoEscolarDigitalSerializer,
    RevogarHistoricoDigitalSerializer,
)


def _filter_queryset_by_profile(queryset, user):
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()

    if getattr(user, "is_superuser", False):
        return queryset

    user_profile = getattr(user, "tipo", "")
    if user_profile == PerfilUsuario.ALUNO:
        return queryset.filter(historico__matricula__aluno=user)
    if user_profile == PerfilUsuario.PROFESSOR:
        return queryset.filter(historico__matricula__turma__professor_responsavel=user)
    return queryset


class HistoricoEscolarDigitalListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    access_action = "view"
    serializer_class = HistoricoEscolarDigitalSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            HistoricoEscolarDigital.objects
            .select_related(
                "historico__matricula__aluno__pessoa",
                "historico__matricula__turma",
                "emitido_por__pessoa",
                "referencia_original",
            )
            .order_by("-emitido_em", "-id")
        )
        queryset = _filter_queryset_by_profile(queryset, self.request.user)
        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(numero_unico__icontains=search)
                | Q(chave_autenticacao__icontains=search)
                | Q(historico__numero_protocolo__icontains=search)
                | Q(historico__matricula__numero_matricula__icontains=search)
                | Q(historico__matricula__aluno__username__icontains=search)
                | Q(historico__matricula__aluno__first_name__icontains=search)
                | Q(historico__matricula__aluno__last_name__icontains=search)
                | Q(historico__matricula__aluno__pessoa__nome_completo__icontains=search)
            )

        tipo_documento = self.request.query_params.get("tipo_documento", "").strip()
        if tipo_documento:
            queryset = queryset.filter(tipo_documento=tipo_documento)

        revogado = self.request.query_params.get("revogado", "").strip().lower()
        if revogado in {"true", "false"}:
            queryset = queryset.filter(revogado=(revogado == "true"))

        return queryset.distinct()


class HistoricoEscolarDigitalDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    access_action = "view"
    serializer_class = HistoricoEscolarDigitalSerializer

    def get_queryset(self):
        queryset = (
            HistoricoEscolarDigital.objects
            .select_related(
                "historico__matricula__aluno__pessoa",
                "historico__matricula__turma",
                "emitido_por__pessoa",
                "referencia_original",
            )
        )
        return _filter_queryset_by_profile(queryset, self.request.user)


class EmitirHistoricoDigitalApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, historico_id: int):
        historico = generics.get_object_or_404(
            HistoricoEscolar.objects.select_related(
                "matricula__aluno__pessoa",
                "matricula__curso__unidade",
                "matricula__turma",
            ),
            pk=historico_id,
        )

        serializer = EmitirHistoricoDigitalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            documento, criado = emitir_historico_digital(
                historico=historico,
                emissor=request.user,
                payload=serializer.to_input(),
                request=request,
            )
        except HistoricoDigitalBusinessError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except HistoricoDigitalValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        response_serializer = HistoricoEscolarDigitalSerializer(documento, context={"request": request})
        response_status = status.HTTP_201_CREATED if criado else status.HTTP_200_OK
        return Response(
            {
                "created": criado,
                "documento": response_serializer.data,
            },
            status=response_status,
        )


class RevogarHistoricoDigitalApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "documentos"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk: int):
        documento = generics.get_object_or_404(
            HistoricoEscolarDigital.objects.select_related("historico", "emitido_por"),
            pk=pk,
        )
        serializer = RevogarHistoricoDigitalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            revogar_historico_digital(
                documento=documento,
                motivo=serializer.validated_data["motivo_revogacao"],
                emissor=request.user,
                request=request,
            )
        except HistoricoDigitalBusinessError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        response_serializer = HistoricoEscolarDigitalSerializer(documento, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)


class ValidarHistoricoDigitalPublicoApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        chave = (request.query_params.get("chave", "") or "").strip()
        if not chave:
            return Response({"detail": "Informe a chave de autenticacao."}, status=status.HTTP_400_BAD_REQUEST)

        documento = (
            HistoricoEscolarDigital.objects
            .select_related("historico", "historico__matricula", "historico__matricula__aluno__pessoa")
            .filter(chave_autenticacao=chave)
            .first()
        )
        if not documento:
            return Response({"detail": "Documento nao encontrado para a chave informada."}, status=status.HTTP_404_NOT_FOUND)

        aluno_nome = ""
        matricula = getattr(documento.historico, "matricula", None)
        if matricula and matricula.aluno:
            aluno = matricula.aluno
            pessoa = getattr(aluno, "pessoa", None)
            aluno_nome = pessoa.nome_completo if pessoa and pessoa.nome_completo else aluno.get_full_name().strip() or aluno.username

        return Response(
            {
                "documento_encontrado": True,
                "numero_unico": documento.numero_unico,
                "tipo_documento": documento.tipo_documento,
                "status": documento.status,
                "revogado": documento.revogado,
                "motivo_revogacao": documento.motivo_revogacao,
                "historico_protocolo": documento.historico.numero_protocolo,
                "matricula_numero": matricula.numero_matricula if matricula else "",
                "aluno_nome": aluno_nome,
                "hash_documento": documento.hash_documento,
                "emitido_em": documento.emitido_em,
                "validacao_xsd_ok": documento.validacao_xsd_ok,
                "assinado_digitalmente": documento.assinado_digitalmente,
            }
        )
