from io import BytesIO
from urllib.parse import urlencode

from django.urls import NoReverseMatch, reverse


def gerar_qr_code_buffer(texto):
    import qrcode

    qr = qrcode.QRCode(version=2, box_size=6, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _data_pt(value):
    return value.strftime("%d/%m/%Y") if value else "-"


def _aluno_nome(historico):
    aluno = getattr(historico, "aluno", None)
    if not aluno:
        return "-"
    nome = getattr(aluno, "nome", None)
    if nome:
        return nome
    pessoa = getattr(aluno, "pessoa", None)
    if pessoa and getattr(pessoa, "nome_completo", None):
        return pessoa.nome_completo
    return str(aluno)


def _aluno_cpf(historico):
    aluno = getattr(historico, "aluno", None)
    if not aluno:
        return "-"
    cpf = getattr(aluno, "cpf", None)
    if cpf:
        return cpf
    pessoa = getattr(aluno, "pessoa", None)
    if pessoa and getattr(pessoa, "cpf", None):
        return pessoa.cpf
    return "-"


def _iter_relacao(historico, nome_relacao):
    rel = getattr(historico, nome_relacao, None)
    if not rel:
        return []
    try:
        qs = rel.all()
        if nome_relacao == "disciplinas":
            return list(qs.order_by("ordem", "id"))
        return list(qs.order_by("id"))
    except Exception:
        return []


def _exists_relacao(historico, nome_relacao):
    rel = getattr(historico, nome_relacao, None)
    if not rel:
        return False
    try:
        return rel.exists()
    except Exception:
        return False


def _resolver_url_validacao(historico, request):
    codigo = getattr(historico, "codigo_validacao", "")
    try:
        path = reverse("historico_digital:validar_historico_publico", args=[codigo])
    except NoReverseMatch:
        path = f"{reverse('api_v1_historicos_digitais:validar_publico')}?{urlencode({'chave': codigo})}"
    return request.build_absolute_uri(path)


def gerar_pdf_historico(historico, request):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    estilo_titulo = ParagraphStyle(
        name="TituloCentral",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=14,
        leading=18,
        spaceAfter=8,
    )

    estilo_subtitulo = ParagraphStyle(
        name="SubtituloCentral",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=12,
        spaceAfter=6,
    )

    estilo_secao = ParagraphStyle(
        name="Secao",
        parent=styles["Heading2"],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0F5132"),
        spaceBefore=8,
        spaceAfter=4,
    )

    story = []

    url_validacao = _resolver_url_validacao(historico, request)

    qr_buffer = gerar_qr_code_buffer(url_validacao)
    qr_img = Image(qr_buffer, width=35 * mm, height=35 * mm)

    instituicao_nome = getattr(getattr(historico, "instituicao", None), "nome", "") or "-"
    curso_nome = getattr(getattr(historico, "curso", None), "nome", "") or "-"

    story.append(Paragraph("REPUBLICA FEDERATIVA DO BRASIL", estilo_subtitulo))
    story.append(Paragraph("GOVERNO DO ESTADO DE RONDONIA", estilo_subtitulo))
    story.append(Paragraph(instituicao_nome.upper(), estilo_subtitulo))
    story.append(Paragraph("HISTORICO ESCOLAR DIGITAL", estilo_titulo))
    story.append(Spacer(1, 6))

    dados_gerais = [
        ["Aluno", _aluno_nome(historico)],
        ["CPF", _aluno_cpf(historico)],
        ["Curso", curso_nome],
        ["Instituicao", instituicao_nome],
        ["Codigo de validacao", getattr(historico, "codigo_validacao", "-")],
        ["Data de emissao", _data_pt(getattr(historico, "data_emissao_historico", None))],
        ["Forma de acesso", getattr(historico, "forma_acesso", "-")],
    ]

    tabela_dados = Table(dados_gerais, colWidths=[43 * mm, 94 * mm])
    tabela_dados.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E9F5EE")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    bloco_superior = Table(
        [[tabela_dados, qr_img]],
        colWidths=[137 * mm, 35 * mm],
    )
    bloco_superior.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ]
        )
    )

    story.append(bloco_superior)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Disciplinas", estilo_secao))

    linhas_disciplinas = [["Codigo", "Disciplina", "Periodo", "CH", "Nota"]]
    for disciplina in _iter_relacao(historico, "disciplinas"):
        linhas_disciplinas.append(
            [
                getattr(disciplina, "codigo_disciplina", getattr(disciplina, "codigo", "-")),
                getattr(disciplina, "nome_disciplina", getattr(disciplina, "nome", "-")),
                getattr(disciplina, "periodo_letivo", getattr(disciplina, "periodo", "-")),
                str(getattr(disciplina, "carga_horaria", "-")),
                str(getattr(disciplina, "nota", "-")),
            ]
        )

    if len(linhas_disciplinas) == 1:
        linhas_disciplinas.append(["-", "Sem disciplinas vinculadas.", "-", "-", "-"])

    tabela_disciplinas = Table(
        linhas_disciplinas,
        colWidths=[25 * mm, 80 * mm, 25 * mm, 18 * mm, 18 * mm],
        repeatRows=1,
    )
    tabela_disciplinas.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F5132")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(tabela_disciplinas)
    story.append(Spacer(1, 8))

    if _exists_relacao(historico, "estagios"):
        story.append(Paragraph("Estagio Supervisionado", estilo_secao))
        for estagio in _iter_relacao(historico, "estagios"):
            story.append(
                Paragraph(
                    f"<b>Codigo:</b> {getattr(estagio, 'codigo_unidade_curricular', '-')}<br/>"
                    f"<b>Periodo:</b> {_data_pt(getattr(estagio, 'data_inicio', None))} a {_data_pt(getattr(estagio, 'data_fim', None))}<br/>"
                    f"<b>Concedente:</b> {getattr(estagio, 'razao_social_concedente', '-')}<br/>"
                    f"<b>Carga horaria:</b> {getattr(estagio, 'carga_horaria', '-')} h<br/>"
                    f"<b>Descricao:</b> {getattr(estagio, 'descricao', '-')}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 6))

    if _exists_relacao(historico, "atividades_complementares"):
        story.append(Paragraph("Atividades Complementares", estilo_secao))
        for atividade in _iter_relacao(historico, "atividades_complementares"):
            story.append(
                Paragraph(
                    f"<b>Codigo:</b> {getattr(atividade, 'codigo_atividade', '-')}<br/>"
                    f"<b>Tipo:</b> {getattr(atividade, 'tipo_atividade', '-')}<br/>"
                    f"<b>Periodo:</b> {_data_pt(getattr(atividade, 'data_inicio', None))} a {_data_pt(getattr(atividade, 'data_fim', None))}<br/>"
                    f"<b>Carga horaria:</b> {getattr(atividade, 'carga_horaria', '-')} h<br/>"
                    f"<b>Descricao:</b> {getattr(atividade, 'descricao', '-')}",
                    styles["Normal"],
                )
            )
            story.append(Spacer(1, 6))

    story.append(Paragraph("Situacao Final", estilo_secao))
    situacao_final = (
        f"<b>Conclusao do curso:</b> {_data_pt(getattr(historico, 'data_conclusao_curso', None))}<br/>"
        f"<b>Colacao:</b> {_data_pt(getattr(historico, 'data_colacao_grau', None))}<br/>"
        f"<b>Expedicao do diploma:</b> {_data_pt(getattr(historico, 'data_expedicao_diploma', None))}<br/>"
        f"<b>Carga horaria integralizada:</b> {getattr(historico, 'carga_horaria_integralizada', 0)}<br/>"
        f"<b>Carga horaria do curso:</b> {getattr(historico, 'carga_horaria_curso', 0)}"
    )
    story.append(Paragraph(situacao_final, styles["Normal"]))
    story.append(Spacer(1, 10))

    if getattr(historico, "informacoes_adicionais", ""):
        story.append(Paragraph("Informacoes Adicionais", estilo_secao))
        story.append(Paragraph(historico.informacoes_adicionais, styles["Normal"]))
        story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            f"Validacao publica: {url_validacao}",
            styles["Normal"],
        )
    )

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
