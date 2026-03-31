from io import BytesIO

from django.conf import settings
from django.template import Context, Template
from django.utils.html import escape
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from .context_builder import obter_brasao_rondonia_data_uri
from .default_templates import DEFAULT_CERTIFICADO_CSS, DEFAULT_CERTIFICADO_TEMPLATE


def _normalizar_template_html(template_html: str) -> str:
    template_html = (template_html or "").strip()
    if not template_html:
        return DEFAULT_CERTIFICADO_TEMPLATE

    lowered = template_html.lower()
    if "<html" in lowered and "<body" in lowered:
        return template_html

    return (
        "<!DOCTYPE html><html lang='pt-BR'><head><meta charset='UTF-8'>"
        "<title>Certificado</title><style>{{ stylesheet_css|safe }}</style>"
        "</head><body>"
        f"{template_html}"
        "</body></html>"
    )


def _inject_validation_overlay_if_missing(html: str, dados_certificado: dict) -> str:
    html_lower = (html or "").lower()
    has_validation_block = any(
        marker in html_lower
        for marker in (
            "qr code de validacao",
            "codigo de validacao",
            "url de verificacao",
            "qr_code_data_uri",
        )
    )
    if has_validation_block:
        return html

    qr_data_uri = (dados_certificado.get("qr_code_data_uri") or "").strip()
    codigo_validacao = escape(dados_certificado.get("codigo_validacao") or "-")
    url_validacao = escape(dados_certificado.get("url_validacao") or dados_certificado.get("qr_code_validacao") or "-")
    hash_integridade = escape(dados_certificado.get("hash_integridade") or "-")

    img_html = ""
    if qr_data_uri:
        img_html = (
            f'<img src="{qr_data_uri}" alt="QR Code de validacao" '
            'style="width:76px;height:76px;object-fit:contain;" />'
        )

    overlay_html = (
        '<section id="certificado-validacao-fallback" '
        'style="position:fixed;right:12mm;bottom:10mm;z-index:9999;'
        'display:flex;gap:8px;align-items:flex-start;'
        'background:rgba(255,255,255,0.94);border:1px solid #cfd7df;'
        'border-radius:8px;padding:7px 9px;max-width:120mm;'
        'font-family:Arial,sans-serif;color:#24313f;font-size:10px;line-height:1.25;">'
        '<div style="width:82px;height:82px;display:flex;align-items:center;justify-content:center;'
        'background:#fff;border:1px solid #d8dfe6;border-radius:4px;">'
        f"{img_html}"
        "</div>"
        "<div>"
        f'<div><strong>Codigo:</strong> {codigo_validacao}</div>'
        f'<div><strong>Validacao:</strong> {url_validacao}</div>'
        f'<div><strong>Hash:</strong> {hash_integridade}</div>'
        "</div>"
        "</section>"
    )

    body_close_index = html_lower.rfind("</body>")
    if body_close_index == -1:
        return f"{html}{overlay_html}"
    return f"{html[:body_close_index]}{overlay_html}{html[body_close_index:]}"


def _inject_historico_overlay_if_missing(html: str, dados_certificado: dict) -> str:
    tipo_documento = (dados_certificado.get("tipo_documento") or "").upper()
    if tipo_documento != "HISTORICO":
        return html

    html_lower = (html or "").lower()
    has_historico_block = any(
        marker in html_lower
        for marker in (
            "consolidacao do historico",
            "media final",
            "frequencia final",
            "situacao final",
            "disciplinas",
        )
    )
    if has_historico_block:
        return html

    disciplinas = dados_certificado.get("disciplinas") or []
    linhas_html = ""
    for disciplina in disciplinas[:8]:
        descricao = escape(disciplina.get("descricao") or "-")
        nota = escape(disciplina.get("nota") or "-")
        peso = escape(disciplina.get("peso") or "-")
        situacao = escape(disciplina.get("situacao") or "-")
        linhas_html += (
            "<tr>"
            f"<td style='padding:1px 2px;border:1px solid #d7dde3;'>{descricao}</td>"
            f"<td style='padding:1px 2px;border:1px solid #d7dde3;text-align:center;'>{nota}</td>"
            f"<td style='padding:1px 2px;border:1px solid #d7dde3;text-align:center;'>{peso}</td>"
            f"<td style='padding:1px 2px;border:1px solid #d7dde3;'>{situacao}</td>"
            "</tr>"
        )

    if not linhas_html:
        linhas_html = (
            "<tr>"
            "<td colspan='4' style='padding:2px;border:1px solid #d7dde3;'>"
            "Sem disciplinas consolidadas no momento."
            "</td>"
            "</tr>"
        )

    media_final = escape(dados_certificado.get("media_final") or "-")
    frequencia_final = escape(dados_certificado.get("frequencia_final") or "-")
    situacao_final = escape(
        dados_certificado.get("situacao_final_display")
        or dados_certificado.get("situacao_final")
        or "-"
    )
    quantidade_disciplinas = escape(str(dados_certificado.get("quantidade_disciplinas") or 0))

    overlay_html = (
        '<section id="certificado-historico-fallback" '
        'style="position:fixed;left:12mm;bottom:10mm;z-index:9998;'
        'background:rgba(255,255,255,0.95);border:1px solid #cfd7df;border-radius:8px;'
        'padding:6px 7px;width:150mm;font-family:Arial,sans-serif;color:#24313f;'
        'font-size:9px;line-height:1.2;">'
        '<div style="display:flex;gap:10px;margin-bottom:4px;">'
        f'<span><strong>Media final:</strong> {media_final}</span>'
        f'<span><strong>Frequencia:</strong> {frequencia_final}</span>'
        f'<span><strong>Situacao:</strong> {situacao_final}</span>'
        f'<span><strong>Disciplinas:</strong> {quantidade_disciplinas}</span>'
        "</div>"
        '<table style="width:100%;border-collapse:collapse;font-size:8px;">'
        "<thead><tr>"
        "<th style='padding:1px 2px;border:1px solid #d7dde3;text-align:left;'>Disciplina</th>"
        "<th style='padding:1px 2px;border:1px solid #d7dde3;text-align:center;'>Nota</th>"
        "<th style='padding:1px 2px;border:1px solid #d7dde3;text-align:center;'>Peso</th>"
        "<th style='padding:1px 2px;border:1px solid #d7dde3;text-align:left;'>Situacao</th>"
        "</tr></thead>"
        f"<tbody>{linhas_html}</tbody>"
        "</table>"
        "</section>"
    )

    body_close_index = html_lower.rfind("</body>")
    if body_close_index == -1:
        return f"{html}{overlay_html}"
    return f"{html[:body_close_index]}{overlay_html}{html[body_close_index:]}"


def renderizar_html_certificado(*, dados_certificado: dict, modelo=None):
    template_html = _normalizar_template_html(
        getattr(modelo, "template_html", "") if modelo else ""
    )
    stylesheet_css = (
        getattr(modelo, "stylesheet_css", "") if modelo else ""
    ) or DEFAULT_CERTIFICADO_CSS

    template = Template(template_html)
    contexto = Context(
        {
            "certificado": dados_certificado,
            "stylesheet_css": stylesheet_css,
            "brasao_rondonia_data_uri": obter_brasao_rondonia_data_uri(),
        }
    )
    html = template.render(contexto)
    html = _inject_historico_overlay_if_missing(html, dados_certificado)
    html = _inject_validation_overlay_if_missing(html, dados_certificado)
    return html, stylesheet_css


def _fallback_pdf_reportlab(dados_certificado: dict):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    c.setTitle(f"Certificado {dados_certificado.get('numero_certificado', '')}")
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 80, "CERTIFICADO")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 130, dados_certificado.get("nome_aluno", ""))

    c.setFont("Helvetica", 11)
    texto = (
        dados_certificado.get("texto_certificado")
        or "Documento emitido em modo de compatibilidade PDF."
    )
    linhas = []
    bloco = ""
    for palavra in texto.split():
        tentativa = f"{bloco} {palavra}".strip()
        if len(tentativa) > 110:
            linhas.append(bloco)
            bloco = palavra
        else:
            bloco = tentativa
    if bloco:
        linhas.append(bloco)

    y = height - 170
    for linha in linhas[:10]:
        c.drawCentredString(width / 2, y, linha)
        y -= 16

    c.setFont("Helvetica", 10)
    c.drawString(60, 70, f"Certificado: {dados_certificado.get('numero_certificado', '')}")
    c.drawString(60, 54, f"Código de validação: {dados_certificado.get('codigo_validacao', '')}")
    c.drawRightString(width - 60, 54, f"{dados_certificado.get('cidade', '')} - {dados_certificado.get('estado', '')}")
    c.showPage()
    c.save()
    return buffer.getvalue()


def gerar_pdf_certificado(*, dados_certificado: dict, modelo=None):
    html, _ = renderizar_html_certificado(dados_certificado=dados_certificado, modelo=modelo)

    try:
        from weasyprint import HTML

        return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    except Exception:
        return _fallback_pdf_reportlab(dados_certificado)
