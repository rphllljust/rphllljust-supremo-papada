from pathlib import Path


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "certificados"


FALLBACK_CSS = """
@page { size: A4 landscape; margin: 0; }
html, body { margin: 0; padding: 0; width: 297mm; height: 210mm; }
"""


FALLBACK_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <title>Certificado</title>
    <style>{{ stylesheet_css|safe }}</style>
  </head>
  <body>
    <article>{{ certificado.nome_aluno }}</article>
  </body>
</html>
"""


def _load_template_file(filename: str, fallback: str) -> str:
    path = TEMPLATES_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return fallback


DEFAULT_CERTIFICADO_CSS = _load_template_file("certificado_oficial.css", FALLBACK_CSS)
DEFAULT_CERTIFICADO_TEMPLATE = _load_template_file("certificado_oficial.html", FALLBACK_HTML)
