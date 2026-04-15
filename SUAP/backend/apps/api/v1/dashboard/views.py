import csv
import hmac
import json
from datetime import date, datetime
from io import StringIO
from itertools import chain
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, urlencode, urlparse
from urllib.request import Request, urlopen

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


def _parse_csv_preview(csv_content, limit=30):
    safe_content = csv_content or ""
    sample = safe_content[:4096]
    dialect = csv.excel

    if sample.strip():
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        except csv.Error:
            dialect = csv.excel

    reader = csv.DictReader(StringIO(safe_content), dialect=dialect)
    columns = list(reader.fieldnames or [])
    rows = []
    for index, row in enumerate(reader):
        if index >= limit:
            break
        rows.append(dict(row))

    return columns, rows


def _extract_google_sheet_source_info(source_url):
    raw = (source_url or "").strip()
    if not raw:
        raise ValueError("Informe a URL da planilha Google Sheets.")

    parsed = urlparse(raw)
    if parsed.scheme != "https":
        raise ValueError("Use uma URL HTTPS do Google Sheets.")

    host = (parsed.netloc or "").lower()
    if host != "docs.google.com":
        raise ValueError("Use uma URL valida do Google Sheets (docs.google.com).")

    path_parts = [part for part in (parsed.path or "").split("/") if part]
    query = parse_qs(parsed.query or "")
    fragment_query = parse_qs((parsed.fragment or "").replace("#", ""))

    gid = query.get("gid", [None])[0] or fragment_query.get("gid", [None])[0] or "0"

    if "spreadsheets" not in path_parts:
        raise ValueError("URL do Google Sheets invalida.")

    if len(path_parts) >= 3 and path_parts[0] == "spreadsheets" and path_parts[1] == "u":
        raise ValueError(
            "Essa URL abre a lista de planilhas. Abra cada arquivo e use a URL completa "
            "no formato /spreadsheets/d/<ID>/edit."
        )

    if "d" in path_parts:
        index = path_parts.index("d")
        if len(path_parts) <= index + 1:
            raise ValueError("Nao foi possivel identificar o ID da planilha.")

        if path_parts[index + 1] == "e":
            if len(path_parts) <= index + 2:
                raise ValueError("Nao foi possivel identificar o ID da planilha publicada.")
            published_id = path_parts[index + 2]
            published_query = {"output": "csv"}
            if gid:
                published_query["gid"] = gid
            published_csv_url = f"https://docs.google.com/spreadsheets/d/e/{published_id}/pub?{urlencode(published_query)}"
            csv_candidates = _normalize_source_urls([published_csv_url, raw])
            return {
                "input_url": raw,
                "sheet_id": "",
                "gid": gid,
                "csv_url": csv_candidates[0],
                "csv_candidates": csv_candidates,
            }

        sheet_id = path_parts[index + 1]
        query_string = urlencode({"format": "csv", "gid": gid})
        export_csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?{query_string}"
        gviz_query = urlencode({"tqx": "out:csv", "gid": gid})
        gviz_csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?{gviz_query}"
        csv_candidates = _normalize_source_urls([export_csv_url, gviz_csv_url, raw])

        return {
            "input_url": raw,
            "sheet_id": sheet_id,
            "gid": gid,
            "csv_url": csv_candidates[0],
            "csv_candidates": csv_candidates,
        }

    raise ValueError("URL do Google Sheets invalida para leitura CSV.")


def _extract_google_sheet_csv_url(source_url):
    return _extract_google_sheet_source_info(source_url)["csv_url"]


def _fetch_external_csv_content(csv_url, source_info=None, timeout=20):
    candidates = [csv_url]
    if source_info:
        candidates.extend(source_info.get("csv_candidates", []) or [])

    candidate_urls = _normalize_source_urls(candidates)
    if not candidate_urls:
        raise ValueError("URL CSV da planilha nao informada.")

    last_http_error = None
    last_connection_error = None
    saw_html_response = False

    for candidate in candidate_urls:
        request = Request(
            candidate,
            headers={
                "User-Agent": "SUAP-IDEP/1.0 (+google-sheets-integration)",
                "Accept": "text/csv,text/plain,*/*",
            },
        )

        try:
            with urlopen(request, timeout=timeout) as response:
                payload = response.read()
        except HTTPError as exc:
            last_http_error = exc
            if exc.code in {401, 403}:
                continue
            raise ValueError(f"Google Sheets retornou erro HTTP {exc.code}.") from exc
        except URLError as exc:
            last_connection_error = exc
            continue

        text = payload.decode("utf-8-sig", errors="replace")
        if "<html" in text[:400].lower():
            saw_html_response = True
            continue
        return text

    if source_info and source_info.get("sheet_id") and (saw_html_response or (last_http_error and last_http_error.code in {401, 403})):
        return _fetch_external_csv_content_via_service_account(
            source_info.get("sheet_id"),
            source_info.get("gid"),
            timeout=timeout,
        )

    if last_http_error:
        raise ValueError(f"Google Sheets retornou erro HTTP {last_http_error.code}.")

    if last_connection_error:
        raise ValueError("Nao foi possivel conectar na URL do Google Sheets.") from last_connection_error

    if saw_html_response:
        raise ValueError("A planilha nao esta publica em CSV. Publique ou compartilhe para leitura.")

    raise ValueError("Nao foi possivel ler os dados da planilha Google Sheets.")


def _summary_from_external_rows(preview_rows):
    summary = {
        "recent_enrollments": 0,
        "document_pending": 0,
        "classes_without_students": 0,
        "system_alerts": 0,
        "upcoming_deadlines": 0,
    }

    mapped = {
        "recent_enrollments": "recent_enrollments",
        "document_pending": "document_pending",
        "classes_without_students": "classes_without_students",
        "system_alerts": "system_alerts",
        "upcoming_deadlines": "upcoming_deadlines",
    }

    has_summary_rows = False
    for row in preview_rows:
        if str(row.get("secao", "")).strip().lower() != "summary":
            continue
        has_summary_rows = True
        key = str(row.get("id", "") or row.get("titulo", "")).strip()
        if key not in mapped:
            continue

        raw_value = str(row.get("valor", "")).strip()
        try:
            value = int(float(raw_value))
        except (TypeError, ValueError):
            value = 0
        summary[mapped[key]] += value

    if not has_summary_rows:
        summary["recent_enrollments"] = len(preview_rows)

    return summary


def _normalize_source_urls(values):
    urls = []
    seen = set()

    for value in values:
        if value is None:
            continue
        text = str(value).replace("\r", "\n")
        for raw_item in text.split("\n"):
            item = raw_item.strip()
            if not item:
                continue
            if item in seen:
                continue
            seen.add(item)
            urls.append(item)

    return urls


def _resolve_google_source_urls(request):
    configured_single = (getattr(settings, "GOOGLE_SHEETS_SOURCE_URL", "") or "").strip()
    configured_multiple = list(getattr(settings, "GOOGLE_SHEETS_SOURCE_URLS", []) or [])

    requested_values = []
    requested_values.extend(request.query_params.getlist("source_url"))
    requested_values.extend(request.query_params.getlist("source_urls"))
    requested_values.append(request.query_params.get("source_urls_text"))

    requested_urls = _normalize_source_urls(requested_values)
    if requested_urls:
        return requested_urls

    configured_urls = _normalize_source_urls([*configured_multiple, configured_single])
    return configured_urls


def _merge_external_sources(source_urls, preview_limit):
    merged_columns = ["planilha"]
    merged_rows = []
    source_csv_urls = []
    source_details = []
    source_errors = []

    remaining_rows = preview_limit

    for source_url in source_urls:
        if remaining_rows <= 0:
            break

        try:
            info = _extract_google_sheet_source_info(source_url)
            csv_content = _fetch_external_csv_content(info["csv_url"], source_info=info)
            source_columns, source_rows = _parse_csv_preview(csv_content, remaining_rows)
        except ValueError as exc:
            source_errors.append(
                {
                    "source_url": source_url,
                    "detail": str(exc),
                }
            )
            continue

        source_label = f'{info["sheet_id"]}:{info["gid"]}'
        source_csv_urls.append(info["csv_url"])

        for column in source_columns:
            if column and column not in merged_columns:
                merged_columns.append(column)

        consumed_rows = 0
        for row in source_rows:
            if remaining_rows <= 0:
                break

            merged_row = {"planilha": source_label}
            for column in source_columns:
                merged_row[column] = row.get(column, "")

            merged_rows.append(merged_row)
            consumed_rows += 1
            remaining_rows -= 1

        source_details.append(
            {
                "source_url": source_url,
                "csv_url": info["csv_url"],
                "sheet_id": info["sheet_id"],
                "gid": info["gid"],
                "rows_loaded": consumed_rows,
            }
        )

    normalized_rows = []
    for row in merged_rows:
        normalized_rows.append({column: row.get(column, "") for column in merged_columns})

    return {
        "columns": merged_columns,
        "rows": normalized_rows,
        "source_csv_urls": source_csv_urls,
        "source_details": source_details,
        "source_errors": source_errors,
    }


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


def _is_truthy(value):
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _resolve_service_account_local_path():
    configured = (getattr(settings, "GOOGLE_SHEETS_SERVICE_ACCOUNT_LOCAL_FILE", "") or "").strip()
    if not configured:
        return None
    return Path(configured)


def _normalize_service_account_info(raw_payload):
    if isinstance(raw_payload, str):
        payload_text = raw_payload.strip()
        if not payload_text:
            raise ValueError("JSON da conta de servico vazio.")
        try:
            info = json.loads(payload_text)
        except json.JSONDecodeError as exc:
            raise ValueError("JSON da conta de servico invalido.") from exc
    elif isinstance(raw_payload, dict):
        info = raw_payload
    else:
        raise ValueError("Conta de servico deve ser enviada como JSON.")

    if not isinstance(info, dict):
        raise ValueError("Conta de servico deve ser um objeto JSON.")
    if str(info.get("type", "")).strip() != "service_account":
        raise ValueError("Credencial invalida: campo type precisa ser service_account.")
    if not str(info.get("client_email", "")).strip():
        raise ValueError("Credencial invalida: client_email ausente.")
    if not str(info.get("private_key", "")).strip():
        raise ValueError("Credencial invalida: private_key ausente.")

    return info


def _load_google_service_account_info():
    raw_json = (getattr(settings, "GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", "") or "").strip()
    if raw_json:
        return _normalize_service_account_info(raw_json)

    file_path = (getattr(settings, "GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE", "") or "").strip()
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError as exc:
            raise ValueError("Arquivo GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE nao encontrado.") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("Arquivo GOOGLE_SHEETS_SERVICE_ACCOUNT_FILE invalido.") from exc

        return _normalize_service_account_info(data)

    local_path = _resolve_service_account_local_path()
    if local_path and local_path.exists():
        try:
            with local_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError("Arquivo local de conta de servico invalido.") from exc
        return _normalize_service_account_info(data)

    return None


def _save_google_service_account_info_locally(raw_payload):
    info = _normalize_service_account_info(raw_payload)
    local_path = _resolve_service_account_local_path()
    if not local_path:
        raise ValueError("Defina GOOGLE_SHEETS_SERVICE_ACCOUNT_LOCAL_FILE para salvar credenciais localmente.")

    local_path.parent.mkdir(parents=True, exist_ok=True)
    with local_path.open("w", encoding="utf-8") as handle:
        json.dump(info, handle, ensure_ascii=False, indent=2)
    return info


def _delete_google_service_account_info_locally():
    local_path = _resolve_service_account_local_path()
    if local_path and local_path.exists():
        local_path.unlink()


def _get_google_service_account_email():
    info = _load_google_service_account_info()
    if not info:
        return ""
    return str(info.get("client_email", "") or "").strip()


def _fetch_external_csv_content_via_service_account(sheet_id, gid, timeout=20):
    info = _load_google_service_account_info()
    if not info:
        raise ValueError(
            "Planilha privada (401/403). Compartilhe publicamente ou configure GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON/FILE."
        )

    try:
        from google.auth.transport.requests import AuthorizedSession
        from google.oauth2 import service_account
    except ImportError as exc:
        raise ValueError(
            "Dependencia google-auth ausente para leitura autenticada. Instale google-auth no backend."
        ) from exc

    credentials = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    session = AuthorizedSession(credentials)

    try:
        gid_number = int(str(gid or "0"))
    except (TypeError, ValueError):
        gid_number = 0

    metadata_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}"
        "?fields=sheets(properties(sheetId,title))"
    )
    metadata_response = session.get(metadata_url, timeout=timeout)
    if metadata_response.status_code >= 400:
        raise ValueError(
            "Falha ao consultar metadados da planilha no Google API. Verifique compartilhamento com a conta de servico."
        )

    metadata_json = metadata_response.json() or {}
    sheets = metadata_json.get("sheets", []) or []
    selected_sheet = None
    for item in sheets:
        properties = item.get("properties", {}) or {}
        try:
            sheet_id_num = int(properties.get("sheetId", -1))
        except (TypeError, ValueError):
            sheet_id_num = -1
        if sheet_id_num == gid_number:
            selected_sheet = properties
            break
    if not selected_sheet and sheets:
        selected_sheet = (sheets[0].get("properties", {}) or {})

    sheet_title = str((selected_sheet or {}).get("title", "") or "").strip()
    if not sheet_title:
        raise ValueError("Nao foi possivel identificar a aba da planilha para leitura.")

    encoded_range = quote(f"'{sheet_title}'", safe="")
    values_url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{encoded_range}"
        "?majorDimension=ROWS"
    )
    values_response = session.get(values_url, timeout=timeout)
    if values_response.status_code >= 400:
        raise ValueError(
            "Falha ao ler dados da planilha via Google API. Verifique permissao da conta de servico nessa planilha."
        )

    values_json = values_response.json() or {}
    values_rows = values_json.get("values", []) or []
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerows(values_rows)
    return output.getvalue()


def _apply_no_cache_headers(response):
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


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
        return _apply_no_cache_headers(response)


class DashboardSheetsModuleApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = (getattr(settings, "GOOGLE_SHEETS_EXPORT_TOKEN", "") or "").strip()
        source_input_urls = _resolve_google_source_urls(request)
        public_base_url = _resolve_sheets_public_base_url(request)
        csv_path = "/api/v1/dashboard/overview-sheets.csv"
        export_url = f"{public_base_url}{csv_path}" if public_base_url else csv_path
        user_is_admin = str(getattr(request.user, "tipo", "")).upper() == "ADMIN"

        try:
            preview_limit = int(request.query_params.get("limit", "30"))
        except (TypeError, ValueError):
            preview_limit = 30
        preview_limit = max(5, min(preview_limit, 2000))

        source_mode = "internal_dashboard"
        source_csv_url = ""
        source_csv_urls = []
        source_details = []
        source_errors = []

        if source_input_urls:
            merged_result = _merge_external_sources(source_input_urls, preview_limit)
            preview_columns = merged_result["columns"]
            preview_rows = merged_result["rows"]
            source_csv_urls = merged_result["source_csv_urls"]
            source_details = merged_result["source_details"]
            source_errors = merged_result["source_errors"]

            source_csv_url = source_csv_urls[0] if source_csv_urls else ""
            summary = _summary_from_external_rows(preview_rows)
            source_mode = "external_google_sheets_batch" if len(source_input_urls) > 1 else "external_google_sheets"
        else:
            payload = _build_dashboard_payload(user=request.user)
            csv_content = _build_dashboard_csv(payload)
            preview_columns, preview_rows = _parse_csv_preview(csv_content, preview_limit)
            summary = payload.get("summary", {})

        if not preview_columns:
            preview_columns = [
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

        service_account_error = ""
        try:
            service_account_email = _get_google_service_account_email()
        except ValueError as exc:
            service_account_email = ""
            service_account_error = str(exc)

        response = Response(
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
                "summary": summary,
                "source_mode": source_mode,
                "source_is_external": source_mode.startswith("external_google_sheets"),
                "source_input_url": source_input_urls[0] if source_input_urls else "",
                "source_input_urls": source_input_urls,
                "source_csv_url": source_csv_url,
                "source_csv_urls": source_csv_urls,
                "source_total_requested": len(source_input_urls),
                "source_total_loaded": len(source_details),
                "source_details": source_details,
                "source_errors": source_errors,
                "service_account_email": service_account_email,
                "service_account_configured": bool(service_account_email),
                "service_account_error": service_account_error,
                "generated_at": timezone.now(),
            }
        )
        return _apply_no_cache_headers(response)

    def post(self, request):
        if str(getattr(request.user, "tipo", "")).upper() != "ADMIN":
            return Response({"detail": "Apenas perfil ADMIN pode alterar credenciais Google Sheets."}, status=403)

        if _is_truthy(request.data.get("clear_service_account")):
            _delete_google_service_account_info_locally()
            return Response(
                {
                    "message": "Credencial Google Sheets removida.",
                    "service_account_email": "",
                    "service_account_configured": False,
                }
            )

        payload = request.data.get("service_account_json")
        if payload is None:
            return Response({"detail": "Informe service_account_json para salvar a credencial."}, status=400)

        try:
            info = _save_google_service_account_info_locally(payload)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(
            {
                "message": "Credencial Google Sheets salva com sucesso.",
                "service_account_email": str(info.get("client_email", "")),
                "service_account_configured": True,
            }
        )
