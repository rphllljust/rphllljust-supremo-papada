import csv
import hmac
from datetime import date, datetime
from io import StringIO
from itertools import chain
from urllib.parse import quote

from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matriculas.models import DocumentoMatricula, Matricula, PendenciaDocumental
from apps.notificacoes.models import Notificacao
from apps.turmas.models import Turma


def _student_name(matricula):
    if getattr(matricula.aluno, "pessoa", None) and matricula.aluno.pessoa.nome_completo:
        return matricula.aluno.pessoa.nome_completo

    full_name = matricula.aluno.get_full_name().strip()
    return full_name or matricula.aluno.username


def _build_dashboard_payload(*, user=None):
    today = timezone.localdate()
    next_seven_days = today + timezone.timedelta(days=7)

    recent_matriculas_qs = (
        Matricula.objects.select_related("aluno__pessoa", "curso", "turma")
        .order_by("-data_matricula", "-id")
    )
    recent_matriculas = list(recent_matriculas_qs[:5])

    pendencias_qs = (
        PendenciaDocumental.objects.select_related("matricula__aluno__pessoa", "matricula__curso", "matricula__turma")
        .filter(status="ABERTA")
        .order_by("prazo", "-data_abertura", "-id")
    )
    document_pending = list(pendencias_qs[:5])

    upcoming_deadlines_qs = pendencias_qs.filter(prazo__isnull=False, prazo__gte=today).order_by("prazo", "data_abertura", "id")
    upcoming_deadlines = list(upcoming_deadlines_qs[:5])

    turmas_sem_alunos_qs = (
        Turma.objects.select_related("curso")
        .filter(status="ATIVA")
        .annotate(total_alunos=Count("matriculas", filter=Q(matriculas__status="ATIVA"), distinct=True))
        .filter(total_alunos=0)
        .order_by("ano_letivo", "nome")
    )
    turmas_sem_alunos = list(turmas_sem_alunos_qs[:5])

    if user is not None and getattr(user, "is_authenticated", False):
        notificacoes_qs = (
            Notificacao.objects.select_related("categoria")
            .filter(usuario=user, ocultada_em__isnull=True)
            .order_by("lida_em", "-data_evento", "-id")
        )
    else:
        notificacoes_qs = Notificacao.objects.none()

    system_alerts = list(notificacoes_qs[:5])

    def _activity_order_key(item):
        raw_date = item.get("date")
        if isinstance(raw_date, datetime):
            return raw_date.isoformat()
        if isinstance(raw_date, date):
            return raw_date.isoformat()
        return ""

    activities = sorted(
        chain(
            [
                {
                    "kind": "matricula",
                    "title": f"Matricula criada: {item.numero_matricula}",
                    "description": f"{_student_name(item)} - {item.curso.nome} - {item.turma.nome}",
                    "date": item.data_matricula,
                    "href": "/matriculas",
                    "badge": "success",
                }
                for item in recent_matriculas_qs[:4]
            ],
            [
                {
                    "kind": "pendencia",
                    "title": "Pendencia documental aberta",
                    "description": f"{item.descricao} - {_student_name(item.matricula)}",
                    "date": item.data_abertura,
                    "href": "/matriculas",
                    "badge": "warning",
                }
                for item in pendencias_qs[:4]
            ],
            [
                {
                    "kind": "aviso",
                    "title": item.titulo,
                    "description": (item.resumo or item.categoria.titulo) if item.categoria else (item.resumo or "Aviso do sistema"),
                    "date": timezone.localtime(item.data_evento),
                    "href": item.link or "/comum/notificacoes",
                    "badge": "info" if item.is_unread else "secondary",
                }
                for item in notificacoes_qs[:4]
            ],
        ),
        key=_activity_order_key,
        reverse=True,
    )[:8]

    return {
        "summary": {
            "recent_enrollments": recent_matriculas_qs.filter(data_matricula__gte=today - timezone.timedelta(days=7)).count(),
            "document_pending": pendencias_qs.count() + DocumentoMatricula.objects.filter(status="PENDENTE").count(),
            "classes_without_students": turmas_sem_alunos_qs.count(),
            "system_alerts": notificacoes_qs.filter(lida_em__isnull=True).count(),
            "upcoming_deadlines": upcoming_deadlines_qs.filter(prazo__lte=next_seven_days).count(),
        },
        "recent_matriculas": [
            {
                "id": item.id,
                "numero_matricula": item.numero_matricula,
                "aluno_nome": _student_name(item),
                "curso_nome": item.curso.nome,
                "turma_nome": item.turma.nome,
                "status": item.status,
                "status_display": item.get_status_display(),
                "data_matricula": item.data_matricula,
                "href": "/matriculas",
            }
            for item in recent_matriculas
        ],
        "document_pending": [
            {
                "id": item.id,
                "descricao": item.descricao,
                "aluno_nome": _student_name(item.matricula),
                "numero_matricula": item.matricula.numero_matricula,
                "prazo": item.prazo,
                "status_display": item.get_status_display(),
                "href": "/matriculas",
            }
            for item in document_pending
        ],
        "turmas_sem_alunos": [
            {
                "id": item.id,
                "nome": item.nome,
                "curso_nome": item.curso.nome,
                "ano_letivo": item.ano_letivo,
                "status_display": item.get_status_display(),
                "href": "/turmas",
            }
            for item in turmas_sem_alunos
        ],
        "system_alerts": [
            {
                "id": item.id,
                "titulo": item.titulo,
                "resumo": item.resumo,
                "tipo_display": item.get_tipo_display(),
                "categoria_titulo": item.categoria.titulo if item.categoria else "Sistema",
                "data_evento": timezone.localtime(item.data_evento),
                "is_unread": item.is_unread,
                "href": item.link or "/comum/notificacoes",
            }
            for item in system_alerts
        ],
        "recent_activities": list(activities),
        "upcoming_deadlines": [
            {
                "id": item.id,
                "descricao": item.descricao,
                "aluno_nome": _student_name(item.matricula),
                "numero_matricula": item.matricula.numero_matricula,
                "prazo": item.prazo,
                "href": "/matriculas",
            }
            for item in upcoming_deadlines
        ],
    }


def _csv_date(value):
    if isinstance(value, datetime):
        return timezone.localtime(value).strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value or ""


def _build_dashboard_csv(payload):
    rows = StringIO(newline="")
    writer = csv.writer(rows)
    writer.writerow(["secao", "id", "titulo", "descricao", "valor", "data", "status", "href"])

    for key, value in payload.get("summary", {}).items():
        writer.writerow(["summary", key, key, "", value, "", "", ""])

    for item in payload.get("recent_matriculas", []):
        writer.writerow(
            [
                "recent_matriculas",
                item.get("id", ""),
                item.get("numero_matricula", ""),
                f'{item.get("aluno_nome", "")} - {item.get("curso_nome", "")} - {item.get("turma_nome", "")}',
                "",
                _csv_date(item.get("data_matricula")),
                item.get("status_display", ""),
                item.get("href", ""),
            ]
        )

    for item in payload.get("document_pending", []):
        writer.writerow(
            [
                "document_pending",
                item.get("id", ""),
                item.get("numero_matricula", ""),
                f'{item.get("aluno_nome", "")} - {item.get("descricao", "")}',
                "",
                _csv_date(item.get("prazo")),
                item.get("status_display", ""),
                item.get("href", ""),
            ]
        )

    for item in payload.get("upcoming_deadlines", []):
        writer.writerow(
            [
                "upcoming_deadlines",
                item.get("id", ""),
                item.get("numero_matricula", ""),
                f'{item.get("aluno_nome", "")} - {item.get("descricao", "")}',
                "",
                _csv_date(item.get("prazo")),
                "",
                item.get("href", ""),
            ]
        )

    for item in payload.get("turmas_sem_alunos", []):
        writer.writerow(
            [
                "turmas_sem_alunos",
                item.get("id", ""),
                item.get("nome", ""),
                item.get("curso_nome", ""),
                item.get("ano_letivo", ""),
                "",
                item.get("status_display", ""),
                item.get("href", ""),
            ]
        )

    return rows.getvalue()


def _build_csv_preview_rows(csv_content, limit=30):
    reader = csv.DictReader(StringIO(csv_content or ""))
    rows = []
    for index, row in enumerate(reader):
        if index >= limit:
            break
        rows.append(dict(row))
    return rows


def _resolve_sheets_public_base_url(request):
    configured = (getattr(settings, "GOOGLE_SHEETS_PUBLIC_BASE_URL", "") or "").strip().rstrip("/")
    if configured:
        return configured
    return request.build_absolute_uri("/").rstrip("/")


def _mask_token(token):
    if not token:
        return ""
    if len(token) <= 10:
        return "*" * len(token)
    return f"{token[:6]}...{token[-4:]}"


class DashboardOverviewApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_build_dashboard_payload(user=request.user))


class DashboardOverviewSheetsCsvApiView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        expected_token = (getattr(settings, "GOOGLE_SHEETS_EXPORT_TOKEN", "") or "").strip()
        if not expected_token:
            return Response(
                {"detail": "Integracao Google Sheets nao configurada. Defina GOOGLE_SHEETS_EXPORT_TOKEN."},
                status=503,
            )

        request_token = (request.query_params.get("token") or "").strip()
        if not hmac.compare_digest(request_token, expected_token):
            return Response({"detail": "Token de integracao invalido."}, status=403)

        csv_content = _build_dashboard_csv(_build_dashboard_payload(user=None))
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        return response


class DashboardSheetsModuleApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = (getattr(settings, "GOOGLE_SHEETS_EXPORT_TOKEN", "") or "").strip()
        public_base_url = _resolve_sheets_public_base_url(request)
        csv_path = "/api/v1/dashboard/overview-sheets.csv"
        export_url = f"{public_base_url}{csv_path}" if public_base_url else csv_path
        user_is_admin = str(getattr(request.user, "tipo", "")).upper() == "ADMIN"

        try:
            preview_limit = int(request.query_params.get("limit", "30"))
        except (TypeError, ValueError):
            preview_limit = 30
        preview_limit = max(5, min(preview_limit, 200))

        payload = _build_dashboard_payload(user=request.user)
        csv_content = _build_dashboard_csv(payload)
        preview_rows = _build_csv_preview_rows(csv_content, preview_limit)
        preview_columns = list(preview_rows[0].keys()) if preview_rows else [
            "secao",
            "id",
            "titulo",
            "descricao",
            "valor",
            "data",
            "status",
            "href",
        ]

        export_url_with_token = ""
        formula = ""
        if token and user_is_admin:
            token_encoded = quote(token, safe="")
            export_url_with_token = f"{export_url}?token={token_encoded}"
            formula = f'=IMPORTDATA("{export_url_with_token}")'

        return Response(
            {
                "integrated": bool(token),
                "module": "google_sheets_read",
                "status": "ok" if token else "token_not_configured",
                "message": "Integracao pronta para leitura no Google Sheets." if token else "Defina GOOGLE_SHEETS_EXPORT_TOKEN para ativar a exportacao.",
                "user_is_admin": user_is_admin,
                "public_base_url": public_base_url,
                "export_url": export_url,
                "export_url_with_token": export_url_with_token,
                "sheets_formula": formula,
                "token_configured": bool(token),
                "token_masked": _mask_token(token),
                "preview_limit": preview_limit,
                "preview_columns": preview_columns,
                "preview_rows": preview_rows,
                "summary": payload.get("summary", {}),
                "generated_at": timezone.now(),
            }
        )
