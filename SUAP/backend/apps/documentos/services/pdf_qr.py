from __future__ import annotations

import base64
from io import BytesIO

from .mec_xml import HistoricoRenderPayload


def build_qr_data_uri(payload_url: str) -> str:
    """
    Gera QR Code em data URI PNG quando biblioteca qrcode estiver disponivel.
    Fallback: data URI textual para nao interromper emissao.
    """
    try:
        import qrcode  # type: ignore

        image = qrcode.make(payload_url)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{encoded}"
    except Exception:
        encoded_text = base64.b64encode(payload_url.encode("utf-8")).decode("ascii")
        return f"data:text/plain;base64,{encoded_text}"


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def generate_simple_pdf_bytes(
    payload: HistoricoRenderPayload,
    *,
    chave_autenticacao: str,
    hash_documento: str,
    validation_url: str,
) -> bytes:
    """
    Gera PDF institucional basico sem dependencias externas.
    """
    lines = [
        "INSTITUTO DE DESENVOLVIMENTO EDUCACIONAL PROFISSIONAL DE RONDONIA",
        "HISTORICO ESCOLAR DIGITAL",
        "",
        f"Aluno: {payload.aluno_nome}",
        f"CPF: {payload.aluno_cpf}",
        f"Curso: {payload.curso_nome}",
        f"Matricula: {payload.matricula_numero}",
        f"Tipo documento MEC: {payload.tipo_documento}",
        f"Protocolo: {payload.numero_protocolo}",
        f"Numero unico: {payload.versao}",
        f"Hash: {hash_documento}",
        f"Chave autenticacao: {chave_autenticacao}",
        f"Validacao: {validation_url}",
    ]

    # PDF minimalista 1 pagina
    content_stream = "BT /F1 10 Tf 50 780 Td 12 TL\n"
    first = True
    for line in lines:
        if not first:
            content_stream += "T*\n"
        first = False
        content_stream += f"({_escape_pdf_text(line)}) Tj\n"
    content_stream += "ET"
    stream_bytes = content_stream.encode("latin-1", errors="replace")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        f"5 0 obj << /Length {len(stream_bytes)} >> stream\n".encode("ascii")
        + stream_bytes
        + b"\nendstream endobj\n"
    )

    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj

    xref_start = len(pdf)
    pdf += f"xref\n0 {len(offsets)}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")
    pdf += (
        f"trailer << /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF".encode("ascii")
    )
    return pdf
