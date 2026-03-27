import base64
from io import BytesIO

import qrcode


def gerar_qr_code_data_uri(texto: str):
    qr = qrcode.QRCode(
        version=3,
        box_size=8,
        border=2,
    )
    qr.add_data(texto)
    qr.make(fit=True)
    imagem = qr.make_image(fill_color="#0c2d48", back_color="white")

    buffer = BytesIO()
    imagem.save(buffer, format="PNG")
    conteudo = buffer.getvalue()
    base64_png = base64.b64encode(conteudo).decode("utf-8")
    data_uri = f"data:image/png;base64,{base64_png}"
    return data_uri, conteudo

