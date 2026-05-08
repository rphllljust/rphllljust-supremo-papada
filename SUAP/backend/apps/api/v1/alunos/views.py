from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework import viewsets

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.documentos.services.historico_escolar_tecnico import (
    HistoricoTecnicoError,
    consolidar_dados_historico,
    serializar_itens_consolidacao,
)
from apps.usuarios.models import PerfilUsuario

from .serializers import AlunoSerializer


Usuario = get_user_model()


class AlunoViewSet(viewsets.ModelViewSet):
    permission_classes = [CanAccessModule]
    module_name = "usuarios"
    access_surface = "api"
    serializer_class = AlunoSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Usuario.objects.select_related("pessoa", "pessoa__aluno").filter(tipo=PerfilUsuario.ALUNO).order_by(
        "pessoa__nome_completo", "first_name", "last_name", "username"
    )

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        search = self.request.query_params.get("search", "").strip()
        situacao = self.request.query_params.get("situacao", "").strip()
        turma_id = self.request.query_params.get("turma", "").strip()

        # T010: por padrão exclui inativos, a menos que seja solicitado explicitamente
        if not situacao:
            queryset = queryset.filter(pessoa__aluno__situacao="ATIVO")
        else:
            queryset = queryset.filter(pessoa__aluno__situacao=situacao)

        # T092/T093: professor vê SEMPRE apenas alunos das suas turmas,
        # independente dos parâmetros de busca ou turma informada
        if getattr(user, "tipo", None) == PerfilUsuario.PROFESSOR:
            queryset = queryset.filter(
                matriculas__turma__professor_responsavel=user,
                matriculas__status="ATIVA",
            )
            if turma_id:
                # Mesmo com turma_id, professor só vê alunos de SUAS turmas
                queryset = queryset.filter(
                    matriculas__turma_id=turma_id,
                    matriculas__turma__professor_responsavel=user,
                    matriculas__status="ATIVA",
                )
        elif turma_id:
            queryset = queryset.filter(
                matriculas__turma_id=turma_id,
                matriculas__status="ATIVA",
            )

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(cpf__icontains=search)
                | Q(pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()

    def perform_destroy(self, instance):
        # T096: exclusão restrita ao perfil ADMIN
        user = self.request.user
        if getattr(user, "tipo", None) != PerfilUsuario.ADMIN:
            raise PermissionDenied("Apenas administradores podem excluir cadastros de alunos.")
        self._destroy_with_cleanup(instance)

    @transaction.atomic
    def _destroy_with_cleanup(self, instance):
        pessoa = instance.pessoa
        instance.delete()
        if pessoa:
            pessoa.delete()

    @action(detail=True, methods=["get"], url_path="dados-para-historico")
    def dados_para_historico(self, request, pk=None):
        aluno = self.get_object()
        try:
            consolidacao = consolidar_dados_historico(aluno_id=aluno.id)
        except HistoricoTecnicoError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "aluno_id": aluno.id,
                "aluno_nome": consolidacao.aluno_nome,
                "aluno_cpf": consolidacao.aluno_cpf,
                "curso_nome": consolidacao.curso_nome,
                "eixo_tecnologico": consolidacao.eixo_tecnologico,
                "carga_horaria_total": consolidacao.carga_horaria_total,
                "situacao_final": consolidacao.situacao_final,
                "data_conclusao": consolidacao.data_conclusao,
                "matricula_id": consolidacao.matricula.id,
                "matricula_numero": consolidacao.matricula.numero_matricula,
                "itens": serializar_itens_consolidacao(consolidacao.itens),
                "estagios": consolidacao.estagios,
                "tcc_pratica": serializar_itens_consolidacao(consolidacao.tcc_pratica),
                "forma_ingresso": consolidacao.forma_ingresso,
                "municipio_unidade": consolidacao.municipio_unidade,
                "observacoes": consolidacao.observacoes,
            }
        )
