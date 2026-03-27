from datetime import datetime, time
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.matriculas.serializers import MatriculaSerializer
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.agenda.models import EventoAgenda
from apps.cursos.models import CalendarioLetivo
from apps.matriculas.models import AproveitamentoComponente, CertificadoDiploma, DependenciaAcademica, Matricula

from .serializers import (
    AgendaAcademicaItemSerializer,
    AproveitamentoEstudosSerializer,
    CertificadoDiplomaSerializer,
    DependenciaAcademicaSerializer,
    VidaAcademicaSnapshotSerializer,
)


def _display_user(user):
    if not user:
        return ""
    full_name = user.get_full_name().strip()
    return full_name or user.username


def _decimal_percent(part, total):
    if not total:
        return None
    value = (Decimal(part) / Decimal(total)) * Decimal("100")
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _decimal_media(notas):
    if not notas:
        return None

    soma = Decimal("0")
    pesos = Decimal("0")
    for nota in notas:
        soma += nota.valor * nota.peso
        pesos += nota.peso

    if not pesos:
        return None

    return (soma / pesos).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _latest_diario(matricula, periodo_filter=""):
    diarios = list(matricula.turma.diarios.all())
    if periodo_filter:
        diarios = [d for d in diarios if periodo_filter.lower() in (d.periodo or "").lower()]
    if not diarios:
        return None
    diarios.sort(key=lambda d: d.id, reverse=True)
    return diarios[0]


def _build_snapshot(matricula, periodo_filter=""):
    diario = _latest_diario(matricula, periodo_filter=periodo_filter)

    notas = list(matricula.notas.all())
    frequencias = list(matricula.frequencias.all())
    transferencias = list(matricula.transferencias.all())
    aproveitamentos = list(matricula.aproveitamentos.all())
    dependencias = list(matricula.dependencias.all())

    professor = getattr(matricula.turma, "professor_responsavel", None)
    consolidacao = getattr(matricula, "consolidacao", None)

    presencas = sum(1 for f in frequencias if f.presente)
    dependencias_ativas = sum(1 for d in dependencias if d.status == "ATIVA")

    return {
        "matricula_id": matricula.id,
        "matricula_aluno": matricula.numero_matricula,
        "aluno_nome": _display_user(matricula.aluno),
        "disciplina": (diario.componente_curricular if diario else "") or "",
        "nota": _decimal_media(notas),
        "frequencia": _decimal_percent(presencas, len(frequencias)),
        "situacao": consolidacao.get_situacao_display() if consolidacao else matricula.get_status_display(),
        "periodo": (diario.periodo if diario else str(matricula.turma.ano_letivo)) or str(matricula.turma.ano_letivo),
        "turma": matricula.turma.nome,
        "professor": _display_user(professor),
        "curso": matricula.curso.nome,
        "status_matricula": matricula.get_status_display(),
        "transferencias": len(transferencias),
        "aproveitamentos": len(aproveitamentos),
        "dependencias_ativas": dependencias_ativas,
    }


class _VidaAcademicaPermissionMixin:
    permission_classes = [CanAccessModule]
    module_name = "matriculas"
    access_surface = "api"
    access_action = "view"

    def get_permissions(self):
        if self.request.method in {"POST", "PATCH", "PUT", "DELETE"}:
            self.access_action = "manage"
        else:
            self.access_action = "view"
        return super().get_permissions()


class VidaAcademicaListApiView(_VidaAcademicaPermissionMixin, generics.ListAPIView):
    serializer_class = VidaAcademicaSnapshotSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Matricula.objects.select_related(
            "aluno__pessoa",
            "curso",
            "turma",
            "turma__professor_responsavel",
            "consolidacao",
        ).prefetch_related(
            "notas",
            "frequencias",
            "transferencias",
            "aproveitamentos",
            "dependencias",
            "turma__diarios",
        ).order_by("-data_matricula", "-id")

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        curso_id = self.request.query_params.get("curso", "").strip()
        turma_id = self.request.query_params.get("turma", "").strip()
        professor_id = self.request.query_params.get("professor", "").strip()
        periodo = self.request.query_params.get("periodo", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        if turma_id:
            queryset = queryset.filter(turma_id=turma_id)

        if professor_id:
            queryset = queryset.filter(turma__professor_responsavel_id=professor_id)

        if periodo:
            queryset = queryset.filter(turma__diarios__periodo__icontains=periodo)

        if search:
            queryset = queryset.filter(
                Q(numero_matricula__icontains=search)
                | Q(aluno__username__icontains=search)
                | Q(aluno__cpf__icontains=search)
                | Q(aluno__first_name__icontains=search)
                | Q(aluno__last_name__icontains=search)
                | Q(aluno__pessoa__nome_completo__icontains=search)
                | Q(curso__nome__icontains=search)
                | Q(turma__nome__icontains=search)
                | Q(turma__professor_responsavel__first_name__icontains=search)
                | Q(turma__professor_responsavel__last_name__icontains=search)
                | Q(turma__diarios__componente_curricular__icontains=search)
            )

        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        periodo = request.query_params.get("periodo", "").strip()
        disciplina = request.query_params.get("disciplina", "").strip().lower()

        snapshots = []
        for matricula in self.get_queryset():
            snapshot = _build_snapshot(matricula, periodo_filter=periodo)
            if disciplina and disciplina not in snapshot["disciplina"].lower():
                continue
            snapshots.append(snapshot)

        page = self.paginate_queryset(snapshots)
        serializer = self.get_serializer(page if page is not None else snapshots, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


class VidaAcademicaDetailApiView(_VidaAcademicaPermissionMixin, generics.RetrieveAPIView):
    serializer_class = VidaAcademicaSnapshotSerializer
    queryset = Matricula.objects.select_related(
        "aluno__pessoa",
        "curso",
        "turma",
        "turma__professor_responsavel",
        "consolidacao",
    ).prefetch_related(
        "notas",
        "frequencias",
        "transferencias",
        "aproveitamentos",
        "dependencias",
        "turma__diarios",
    )

    def retrieve(self, request, *args, **kwargs):
        matricula = self.get_object()
        periodo = request.query_params.get("periodo", "").strip()
        payload = _build_snapshot(matricula, periodo_filter=periodo)
        serializer = self.get_serializer(payload)
        return Response(serializer.data)


class VidaAcademicaStatusActionApiView(_VidaAcademicaPermissionMixin, APIView):
    action_map = {
        "TRANCAR": "TRANCADA",
        "CANCELAR": "CANCELADA",
        "REATIVAR": "ATIVA",
        "CONCLUIR": "CONCLUIDA",
    }

    def post(self, request, pk):
        matricula = get_object_or_404(Matricula.objects.select_related("turma", "curso", "aluno"), pk=pk)
        acao = (request.data.get("acao") or "").strip().upper()

        if acao not in self.action_map:
            return Response(
                {
                    "detail": "Acao invalida. Use: TRANCAR, CANCELAR, REATIVAR ou CONCLUIR.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        matricula.status = self.action_map[acao]
        try:
            matricula.save()
        except ValidationError as exc:
            return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)

        return Response(MatriculaSerializer(matricula).data)


class DependenciaAcademicaListApiView(_VidaAcademicaPermissionMixin, generics.ListCreateAPIView):
    serializer_class = DependenciaAcademicaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = DependenciaAcademica.objects.select_related(
            "matricula",
            "matricula__aluno__pessoa",
            "matricula__curso",
            "matricula__turma",
        ).order_by("-data_registro", "-id")

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        matricula_id = self.request.query_params.get("matricula", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if matricula_id:
            queryset = queryset.filter(matricula_id=matricula_id)

        if search:
            queryset = queryset.filter(
                Q(componente__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
                | Q(matricula__curso__nome__icontains=search)
            )

        return queryset.distinct()


class DependenciaAcademicaDetailApiView(_VidaAcademicaPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DependenciaAcademicaSerializer
    queryset = DependenciaAcademica.objects.select_related(
        "matricula",
        "matricula__aluno__pessoa",
        "matricula__curso",
        "matricula__turma",
    )


class AproveitamentoEstudosListApiView(_VidaAcademicaPermissionMixin, generics.ListCreateAPIView):
    serializer_class = AproveitamentoEstudosSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = AproveitamentoComponente.objects.select_related(
            "matricula",
            "matricula__aluno__pessoa",
            "decisao_por",
        ).order_by("-data_solicitacao", "-id")

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        matricula_id = self.request.query_params.get("matricula", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if matricula_id:
            queryset = queryset.filter(matricula_id=matricula_id)

        if search:
            queryset = queryset.filter(
                Q(componente_origem__icontains=search)
                | Q(componente_destino__icontains=search)
                | Q(instituicao_origem__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        status_value = serializer.validated_data.get("status")
        if status_value in {"APROVADO", "INDEFERIDO"} and not serializer.validated_data.get("decisao_por"):
            serializer.save(decisao_por=self.request.user)
            return
        serializer.save()


class AproveitamentoEstudosDetailApiView(_VidaAcademicaPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AproveitamentoEstudosSerializer
    queryset = AproveitamentoComponente.objects.select_related(
        "matricula",
        "matricula__aluno__pessoa",
        "decisao_por",
    )

    def perform_update(self, serializer):
        status_value = serializer.validated_data.get("status")
        if status_value in {"APROVADO", "INDEFERIDO"} and not serializer.validated_data.get("decisao_por"):
            serializer.save(decisao_por=self.request.user)
            return
        serializer.save()


class AgendaAcademicaListApiView(_VidaAcademicaPermissionMixin, APIView):
    access_action = "view"

    def get(self, request):
        curso_id = request.query_params.get("curso", "").strip()
        turma_id = request.query_params.get("turma", "").strip()
        professor_id = request.query_params.get("professor", "").strip()
        ano_letivo = request.query_params.get("ano_letivo", "").strip()

        calendarios = CalendarioLetivo.objects.select_related("curso")
        eventos = EventoAgenda.objects.select_related("turma", "turma__curso", "turma__professor_responsavel")

        if curso_id:
            calendarios = calendarios.filter(curso_id=curso_id)
            eventos = eventos.filter(turma__curso_id=curso_id)

        if turma_id:
            eventos = eventos.filter(turma_id=turma_id)
            turma_curso = eventos.values_list("turma__curso_id", flat=True).first()
            if turma_curso:
                calendarios = calendarios.filter(curso_id=turma_curso)

        if professor_id:
            eventos = eventos.filter(turma__professor_responsavel_id=professor_id)

        if ano_letivo:
            calendarios = calendarios.filter(ano_letivo=ano_letivo)
            eventos = eventos.filter(inicio__year=ano_letivo)

        items = []
        for calendario in calendarios:
            inicio_dt = timezone.make_aware(datetime.combine(calendario.data_inicio, time.min))
            fim_dt = timezone.make_aware(datetime.combine(calendario.data_fim, time.max))

            items.append(
                {
                    "tipo": "INICIO_SEMESTRE",
                    "titulo": f"Inicio do semestre {calendario.ano_letivo}",
                    "descricao": calendario.descricao or "",
                    "periodo": str(calendario.ano_letivo),
                    "data_inicio": inicio_dt,
                    "data_fim": inicio_dt,
                    "curso": calendario.curso.nome,
                    "turma": "",
                    "professor": "",
                    "origem": "CALENDARIO_LETIVO",
                }
            )
            items.append(
                {
                    "tipo": "FIM_SEMESTRE",
                    "titulo": f"Fim do semestre {calendario.ano_letivo}",
                    "descricao": calendario.descricao or "",
                    "periodo": str(calendario.ano_letivo),
                    "data_inicio": fim_dt,
                    "data_fim": fim_dt,
                    "curso": calendario.curso.nome,
                    "turma": "",
                    "professor": "",
                    "origem": "CALENDARIO_LETIVO",
                }
            )

        for evento in eventos:
            texto = f"{evento.titulo} {evento.descricao}".lower()
            tipo = "EVENTO"
            if "feriado" in texto:
                tipo = "FERIADO"
            elif "recuper" in texto:
                tipo = "RECUPERACAO"

            diario = evento.turma.diarios.order_by("-id").first()
            periodo = diario.periodo if diario and diario.periodo else str(evento.inicio.year)

            items.append(
                {
                    "tipo": tipo,
                    "titulo": evento.titulo,
                    "descricao": evento.descricao or "",
                    "periodo": periodo,
                    "data_inicio": evento.inicio,
                    "data_fim": evento.fim,
                    "curso": evento.turma.curso.nome,
                    "turma": evento.turma.nome,
                    "professor": _display_user(evento.turma.professor_responsavel),
                    "origem": "EVENTO_AGENDA",
                }
            )

        items.sort(key=lambda item: item["data_inicio"])
        serializer = AgendaAcademicaItemSerializer(items, many=True)
        return Response(serializer.data)


class CertificadoDiplomaListApiView(_VidaAcademicaPermissionMixin, generics.ListCreateAPIView):
    serializer_class = CertificadoDiplomaSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = CertificadoDiploma.objects.select_related(
            "matricula",
            "matricula__aluno__pessoa",
            "emitido_por",
        ).order_by("-data_emissao", "-id")

        search = self.request.query_params.get("search", "").strip()
        status_value = self.request.query_params.get("status", "").strip()
        tipo = self.request.query_params.get("tipo", "").strip()
        matricula_id = self.request.query_params.get("matricula", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)

        if tipo:
            queryset = queryset.filter(tipo=tipo)

        if matricula_id:
            queryset = queryset.filter(matricula_id=matricula_id)

        if search:
            queryset = queryset.filter(
                Q(numero_registro__icontains=search)
                | Q(observacao__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        serializer.save(emitido_por=self.request.user if self.request.user.is_authenticated else None)


class CertificadoDiplomaDetailApiView(_VidaAcademicaPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CertificadoDiplomaSerializer
    queryset = CertificadoDiploma.objects.select_related(
        "matricula",
        "matricula__aluno__pessoa",
        "emitido_por",
    )

    def perform_update(self, serializer):
        emitido_por = serializer.validated_data.get("emitido_por")
        if not emitido_por and self.request.user.is_authenticated:
            serializer.save(emitido_por=self.request.user)
            return
        serializer.save()
