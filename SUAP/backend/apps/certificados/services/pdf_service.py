from io import BytesIO

from django.conf import settings
from django.template import Context, Template
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
