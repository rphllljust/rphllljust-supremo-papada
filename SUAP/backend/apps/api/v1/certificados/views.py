from types import SimpleNamespace

from django.db.models import Q
from django.http import HttpResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.certificados.models import (
    AssinaturaCertificado,
    CertificadoEmitido,
    ConfiguracaoVisualCertificado,
    HistoricoEmissaoCertificado,
    ModeloCertificado,
)
from apps.certificados.services import (
    emitir_certificado,
    emitir_certificados_em_lote,
    gerar_pdf_certificado,
    montar_dados_certificado,
    montar_url_validacao,
    registrar_historico,
    registrar_reimpressao,
    renderizar_html_certificado,
)
from apps.certificados.services.qrcode_service import gerar_qr_code_data_uri
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.usuarios.models import PerfilUsuario

from .serializers import (
    AssinaturaCertificadoSerializer,
    CertificadoEmitidoSerializer,
    ConfiguracaoVisualCertificadoSerializer,
    EmitirCertificadoSerializer,
    HistoricoEmissaoCertificadoSerializer,
    ModeloCertificadoSerializer,
    PreviewRascunhoCertificadoSerializer,
)


def _filtrar_por_perfil(queryset, user):
    if not user or not getattr(user, "is_authenticated", False):
        return queryset.none()
    if getattr(user, "is_superuser", False):
        return queryset

    perfil = getattr(user, "tipo", "")
    if perfil == PerfilUsuario.ALUNO:
        return queryset.filter(matricula__aluno=user)
    if perfil == PerfilUsuario.PROFESSOR:
        return queryset.filter(turma__professor_responsavel=user)
    return queryset


class ModeloCertificadoListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"
    serializer_class = ModeloCertificadoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = (
            ModeloCertificado.objects
            .select_related("curso", "unidade", "criado_por", "atualizado_por", "configuracao_visual")
            .prefetch_related("assinaturas")
            .order_by("-atualizado_em", "nome")
        )
        params = self.request.query_params
        search = params.get("search", "").strip()
        tipo = params.get("tipo", "").strip()
        ativo = params.get("ativo", "").strip().lower()
        curso_id = params.get("curso", "").strip()
        unidade_id = params.get("unidade", "").strip()

        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(descricao__icontains=search)
                | Q(slug__icontains=search)
            )
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if ativo in {"true", "1", "sim"}:
            queryset = queryset.filter(ativo=True)
        elif ativo in {"false", "0", "nao", "não"}:
            queryset = queryset.filter(ativo=False)
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)
        if unidade_id:
            queryset = queryset.filter(unidade_id=unidade_id)
        return queryset

    def perform_create(self, serializer):
        modelo = serializer.save()
        registrar_historico(
            acao="ALTERACAO_MODELO",
            descricao=f"Modelo criado: {modelo.nome}",
            dados={"modelo_id": modelo.id},
            usuario=self.request.user,
            modelo=modelo,
            request=self.request,
        )


class ModeloCertificadoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    serializer_class = ModeloCertificadoSerializer
    queryset = (
        ModeloCertificado.objects
        .select_related("curso", "unidade", "criado_por", "atualizado_por", "configuracao_visual")
        .prefetch_related("assinaturas")
    )

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def perform_update(self, serializer):
        modelo = serializer.save()
        registrar_historico(
            acao="ALTERACAO_MODELO",
            descricao=f"Modelo atualizado: {modelo.nome}",
            dados={"modelo_id": modelo.id},
            usuario=self.request.user,
            modelo=modelo,
            request=self.request,
        )

    def perform_destroy(self, instance):
        registrar_historico(
            acao="ALTERACAO_MODELO",
            descricao=f"Modelo removido: {instance.nome}",
            dados={"modelo_id": instance.id},
            usuario=self.request.user,
            modelo=instance,
            request=self.request,
        )
        instance.delete()


class AssinaturaCertificadoListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"
    serializer_class = AssinaturaCertificadoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = AssinaturaCertificado.objects.select_related("modelo").order_by("ordem", "nome")
        modelo_id = self.request.query_params.get("modelo", "").strip()
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)
        return queryset


class AssinaturaCertificadoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    serializer_class = AssinaturaCertificadoSerializer
    queryset = AssinaturaCertificado.objects.select_related("modelo")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class ConfiguracaoVisualCertificadoListCreateApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"
    serializer_class = ConfiguracaoVisualCertificadoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == "POST":
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        queryset = ConfiguracaoVisualCertificado.objects.select_related("modelo").order_by("modelo__nome")
        modelo_id = self.request.query_params.get("modelo", "").strip()
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)
        return queryset


class ConfiguracaoVisualCertificadoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    serializer_class = ConfiguracaoVisualCertificadoSerializer
    queryset = ConfiguracaoVisualCertificado.objects.select_related("modelo")

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class CertificadoEmitidoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"
    serializer_class = CertificadoEmitidoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            CertificadoEmitido.objects
            .select_related(
                "modelo",
                "aluno__pessoa",
                "matricula__aluno__pessoa",
                "curso",
                "unidade",
                "turma",
                "usuario_emissor__pessoa",
            )
            .order_by("-criado_em", "-id")
        )
        queryset = _filtrar_por_perfil(queryset, self.request.user)

        params = self.request.query_params
        search = params.get("search", "").strip()
        status_val = params.get("status", "").strip()
        curso_id = params.get("curso", "").strip()
        turma_id = params.get("turma", "").strip()
        periodo = params.get("periodo", "").strip()
        unidade_id = params.get("unidade", "").strip()

        if status_val:
            queryset = queryset.filter(status=status_val)
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)
        if turma_id:
            queryset = queryset.filter(turma_id=turma_id)
        if unidade_id:
            queryset = queryset.filter(unidade_id=unidade_id)
        if periodo:
            queryset = queryset.filter(
                Q(data_inicio__year=periodo)
                | Q(data_emissao__year=periodo)
                | Q(data_conclusao__year=periodo)
            )
        if search:
            queryset = queryset.filter(
                Q(numero_certificado__icontains=search)
                | Q(codigo_validacao__icontains=search)
                | Q(nome_aluno_snapshot__icontains=search)
                | Q(cpf_aluno_snapshot__icontains=search)
                | Q(curso_nome_snapshot__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
            )
        return queryset.distinct()


class CertificadoEmitidoDetailApiView(generics.RetrieveUpdateAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    serializer_class = CertificadoEmitidoSerializer
    queryset = (
        CertificadoEmitido.objects
        .select_related(
            "modelo",
            "aluno__pessoa",
            "matricula__aluno__pessoa",
            "curso",
            "unidade",
            "turma",
            "usuario_emissor__pessoa",
        )
    )

    def get_permissions(self):
        if self.request.method in {"PUT", "PATCH"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def get_queryset(self):
        return _filtrar_por_perfil(super().get_queryset(), self.request.user)

    def perform_update(self, serializer):
        instancia_anterior = self.get_object()
        status_anterior = instancia_anterior.status
        certificado = serializer.save()
        if status_anterior != certificado.status:
            registrar_historico(
                acao="ALTERACAO_STATUS",
                descricao=f"Status alterado de {status_anterior} para {certificado.status}",
                dados={
                    "status_anterior": status_anterior,
                    "status_novo": certificado.status,
                },
                usuario=self.request.user,
                certificado=certificado,
                modelo=certificado.modelo,
                request=self.request,
            )


class EmitirCertificadoApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "manage"

    def post(self, request):
        serializer = EmitirCertificadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        modelo = generics.get_object_or_404(ModeloCertificado, id=payload["modelo_id"], ativo=True)
        sobrescritas = payload.get("sobrescritas") or {}
        gerar_pdf = payload.get("gerar_pdf", True)

        if payload.get("matricula_id"):
            matricula = generics.get_object_or_404(
                Matricula.objects.select_related("curso__unidade", "turma", "aluno__pessoa"),
                id=payload["matricula_id"],
            )
            certificado = emitir_certificado(
                modelo=modelo,
                matricula=matricula,
                emissor=request.user,
                sobrescritas=sobrescritas,
                request=request,
                gerar_pdf=gerar_pdf,
            )
            return Response(
                CertificadoEmitidoSerializer(certificado, context={"request": request}).data,
                status=status.HTTP_201_CREATED,
            )

        turma = generics.get_object_or_404(Turma, id=payload["turma_id"])
        matriculas = (
            Matricula.objects
            .select_related("curso__unidade", "turma", "aluno__pessoa")
            .filter(turma=turma)
            .order_by("numero_matricula")
        )
        if sobrescritas.get("somente_concluintes", True):
            matriculas = matriculas.filter(status="CONCLUIDA")

        certificados, erros = emitir_certificados_em_lote(
            modelo=modelo,
            matriculas=matriculas,
            emissor=request.user,
            sobrescritas=sobrescritas,
            request=request,
            gerar_pdf=gerar_pdf,
        )
        return Response(
            {
                "total_emitidos": len(certificados),
                "total_erros": len(erros),
                "certificados": CertificadoEmitidoSerializer(
                    certificados, many=True, context={"request": request}
                ).data,
                "erros": erros,
            },
            status=status.HTTP_201_CREATED,
        )


class EmitirCertificadoLoteApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "manage"

    def post(self, request):
        serializer = EmitirCertificadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        if not payload.get("turma_id"):
            return Response(
                {"detail": "Para emissão em lote informe turma_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        modelo = generics.get_object_or_404(ModeloCertificado, id=payload["modelo_id"], ativo=True)
        turma = generics.get_object_or_404(Turma, id=payload["turma_id"])
        sobrescritas = payload.get("sobrescritas") or {}
        gerar_pdf = payload.get("gerar_pdf", True)
        matriculas = (
            Matricula.objects
            .select_related("curso__unidade", "turma", "aluno__pessoa")
            .filter(turma=turma)
            .order_by("numero_matricula")
        )
        if sobrescritas.get("somente_concluintes", True):
            matriculas = matriculas.filter(status="CONCLUIDA")

        certificados, erros = emitir_certificados_em_lote(
            modelo=modelo,
            matriculas=matriculas,
            emissor=request.user,
            sobrescritas=sobrescritas,
            request=request,
            gerar_pdf=gerar_pdf,
        )
        return Response(
            {
                "total_emitidos": len(certificados),
                "total_erros": len(erros),
                "certificados": CertificadoEmitidoSerializer(
                    certificados, many=True, context={"request": request}
                ).data,
                "erros": erros,
            },
            status=status.HTTP_201_CREATED,
        )


class PreviewRascunhoCertificadoApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "manage"

    def post(self, request):
        serializer = PreviewRascunhoCertificadoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        modelo = generics.get_object_or_404(ModeloCertificado, id=payload["modelo_id"], ativo=True)
        matricula = None
        if payload.get("matricula_id"):
            matricula = generics.get_object_or_404(
                Matricula.objects.select_related("curso__unidade", "turma", "aluno__pessoa"),
                id=payload["matricula_id"],
            )
        sobrescritas = payload.get("sobrescritas") or {}

        rascunho = SimpleNamespace(
            numero_certificado=CertificadoEmitido.gerar_numero_certificado(),
            codigo_validacao=CertificadoEmitido.gerar_codigo_validacao(),
            data_emissao=sobrescritas.get("data_emissao"),
            data_inicio=sobrescritas.get("data_inicio"),
            data_fim=sobrescritas.get("data_fim"),
            data_conclusao=sobrescritas.get("data_conclusao"),
            livro=sobrescritas.get("livro", ""),
            folha=sobrescritas.get("folha", ""),
            curso=getattr(matricula, "curso", None) or modelo.curso,
            unidade=getattr(getattr(matricula, "curso", None), "unidade", None) or modelo.unidade,
            turma=getattr(matricula, "turma", None),
            aluno=None,
            qr_code_data_uri="",
        )
        url_validacao = montar_url_validacao(rascunho.codigo_validacao, request=request)
        qr_code_data_uri, _ = gerar_qr_code_data_uri(url_validacao)
        rascunho.qr_code_data_uri = qr_code_data_uri
        dados = montar_dados_certificado(
            modelo=modelo,
            matricula=matricula,
            certificado=rascunho,
            sobrescritas=sobrescritas,
            url_validacao=url_validacao,
        )
        dados["qr_code_data_uri"] = qr_code_data_uri
        html, css = renderizar_html_certificado(dados_certificado=dados, modelo=modelo)

        registrar_historico(
            acao="PREVIEW",
            descricao="Pré-visualização de certificado (rascunho)",
            dados={
                "modelo_id": modelo.id,
                "matricula_id": matricula.id if matricula else None,
            },
            usuario=request.user,
            modelo=modelo,
            request=request,
        )
        return Response({"html": html, "css": css, "dados": dados})


class CertificadoPreviewApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk: int):
        certificado = generics.get_object_or_404(
            _filtrar_por_perfil(
                CertificadoEmitido.objects.select_related(
                    "modelo",
                    "matricula__curso__unidade",
                    "matricula__turma",
                    "matricula__aluno__pessoa",
                    "aluno__pessoa",
                ),
                request.user,
            ),
            id=pk,
        )
        dados = certificado.dados_dinamicos or montar_dados_certificado(
            modelo=certificado.modelo,
            matricula=certificado.matricula,
            certificado=certificado,
            url_validacao=certificado.qr_code_validacao,
        )
        html, css = renderizar_html_certificado(dados_certificado=dados, modelo=certificado.modelo)

        registrar_historico(
            acao="PREVIEW",
            descricao=f"Pré-visualização do certificado {certificado.numero_certificado}",
            dados={"certificado_id": certificado.id},
            usuario=request.user,
            certificado=certificado,
            modelo=certificado.modelo,
            request=request,
        )
        return Response({"html": html, "css": css, "dados": dados})


class CertificadoPdfApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"

    def get(self, request, pk: int):
        certificado = generics.get_object_or_404(
            _filtrar_por_perfil(
                CertificadoEmitido.objects.select_related(
                    "modelo",
                    "matricula__curso__unidade",
                    "matricula__turma",
                    "matricula__aluno__pessoa",
                    "aluno__pessoa",
                ),
                request.user,
            ),
            id=pk,
        )
        dados = certificado.dados_dinamicos or montar_dados_certificado(
            modelo=certificado.modelo,
            matricula=certificado.matricula,
            certificado=certificado,
            url_validacao=certificado.qr_code_validacao,
        )
        pdf = gerar_pdf_certificado(dados_certificado=dados, modelo=certificado.modelo)

        registrar_historico(
            acao="GERACAO_PDF",
            descricao=f"Geração de PDF para {certificado.numero_certificado}",
            dados={"certificado_id": certificado.id},
            usuario=request.user,
            certificado=certificado,
            modelo=certificado.modelo,
            request=request,
        )

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{certificado.numero_certificado}.pdf"'
        return response


class CertificadoReimprimirApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "manage"

    def post(self, request, pk: int):
        certificado = generics.get_object_or_404(
            _filtrar_por_perfil(
                CertificadoEmitido.objects.select_related("modelo"),
                request.user,
            ),
            id=pk,
        )
        registrar_reimpressao(certificado, usuario=request.user, request=request)
        return Response(
            {
                "detail": "Reimpressão registrada com sucesso.",
                "certificado": CertificadoEmitidoSerializer(
                    certificado, context={"request": request}
                ).data,
            }
        )


class CertificadoValidarPublicoApiView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, codigo_validacao: str):
        certificado = (
            CertificadoEmitido.objects
            .select_related("unidade", "curso")
            .filter(codigo_validacao=codigo_validacao)
            .first()
        )
        if not certificado:
            return Response(
                {"detail": "Certificado não encontrado para o código informado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        status_valido = certificado.status != "CERTIFICADO_CANCELADO"
        registrar_historico(
            acao="VALIDACAO_PUBLICA",
            descricao=f"Validação pública do certificado {certificado.numero_certificado}",
            dados={"codigo_validacao": codigo_validacao, "status_valido": status_valido},
            certificado=certificado,
            modelo=certificado.modelo,
            request=request,
        )
        return Response(
            {
                "valido": status_valido,
                "status_validade": "válido" if status_valido else "inválido",
                "nome_aluno": certificado.nome_aluno_snapshot,
                "curso": certificado.curso_nome_snapshot,
                "data_conclusao": certificado.data_conclusao,
                "numero_certificado": certificado.numero_certificado,
                "codigo_validacao": certificado.codigo_validacao,
                "instituicao_emissora": certificado.dados_dinamicos.get("nome_da_instituicao", ""),
                "data_emissao": certificado.data_emissao,
            }
        )


class HistoricoEmissaoCertificadoListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "certificados"
    access_surface = "api"
    access_action = "view"
    serializer_class = HistoricoEmissaoCertificadoSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = (
            HistoricoEmissaoCertificado.objects
            .select_related("certificado", "modelo", "usuario__pessoa")
            .order_by("-criado_em")
        )
        search = self.request.query_params.get("search", "").strip()
        acao = self.request.query_params.get("acao", "").strip()
        certificado_id = self.request.query_params.get("certificado", "").strip()
        modelo_id = self.request.query_params.get("modelo", "").strip()
        if acao:
            queryset = queryset.filter(acao=acao)
        if certificado_id:
            queryset = queryset.filter(certificado_id=certificado_id)
        if modelo_id:
            queryset = queryset.filter(modelo_id=modelo_id)
        if search:
            queryset = queryset.filter(
                Q(descricao__icontains=search)
                | Q(certificado__numero_certificado__icontains=search)
                | Q(modelo__nome__icontains=search)
                | Q(usuario__username__icontains=search)
                | Q(usuario__pessoa__nome_completo__icontains=search)
            )
        return queryset
