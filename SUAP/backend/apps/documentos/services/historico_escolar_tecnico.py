from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from decimal import Decimal
from io import BytesIO
from typing import Any

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone

from apps.auditoria.models import LogAuditoria
from apps.cursos.models import ComponenteCurricular
from apps.documentos.models import (
    AssinaturaDocumento,
    ConfiguracaoHistorico,
    DocumentoValidacao,
    HistoricoEscolarEvento,
    HistoricoEscolarItem,
    HistoricoEscolarTecnicoDocumento,
)
from apps.estagio.models import Estagio
from apps.frequencia.models import Frequencia
from apps.matriculas.models import Matricula
from apps.notas.models import Nota
from apps.usuarios.models import PerfilUsuario


class HistoricoTecnicoError(Exception):
    pass


@dataclass
class ConsolidacaoHistorico:
    matricula: Matricula
    aluno_nome: str
    aluno_cpf: str
    curso_nome: str
    eixo_tecnologico: str
    ato_autorizativo: str
    forma_ingresso: str
    unidade_nome: str
    municipio_unidade: str
    carga_horaria_total: int
    carga_horaria_curso: int
    data_conclusao: Any
    situacao_final: str
    observacoes: str
    itens: list[dict[str, Any]]
    estagios: list[dict[str, Any]]
    tcc_pratica: list[dict[str, Any]]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _mask_cpf(cpf: str) -> str:
    digits = re.sub(r"\D", "", cpf or "")
    if len(digits) != 11:
        return "***.***.***-**"
    return f"***.{digits[3:6]}.{digits[6:9]}-**"


def _display_user_name(user) -> str:
    pessoa = getattr(user, "pessoa", None)
    if pessoa and getattr(pessoa, "nome_completo", ""):
        return pessoa.nome_completo
    full_name = user.get_full_name().strip()
    return full_name or user.username


def _media_ponderada(notas: list[Nota]) -> Decimal | None:
    if not notas:
        return None
    soma = Decimal("0")
    pesos = Decimal("0")
    for nota in notas:
        soma += nota.valor * nota.peso
        pesos += nota.peso
    if pesos <= 0:
        return None
    return (soma / pesos).quantize(Decimal("0.01"))


def _frequencia_percentual(frequencias: list[Frequencia]) -> Decimal | None:
    if not frequencias:
        return None
    presencas = sum(1 for item in frequencias if item.presente)
    total = len(frequencias)
    return (Decimal(presencas) * Decimal("100") / Decimal(total)).quantize(Decimal("0.01"))


def _build_component_tokens(componente: ComponenteCurricular) -> list[str]:
    values = [
        componente.nome,
        componente.sigla,
        componente.abreviatura,
        componente.descricao_diploma_historico,
    ]
    return [v for v in (_normalize(value) for value in values) if v]


def serializar_itens_consolidacao(itens: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for item in itens:
        componente = item.get("componente_curricular")
        payload.append(
            {
                "componente_curricular_id": getattr(componente, "id", None),
                "componente_nome": item.get("componente_nome"),
                "modulo_periodo": item.get("modulo_periodo"),
                "carga_horaria": item.get("carga_horaria"),
                "nota": item.get("nota"),
                "frequencia": item.get("frequencia"),
                "resultado": item.get("resultado"),
                "ordem_exibicao": item.get("ordem_exibicao"),
            }
        )
    return payload


def _get_config() -> ConfiguracaoHistorico:
    config = ConfiguracaoHistorico.objects.filter(ativo=True).order_by("-atualizado_em", "-id").first()
    if config:
        return config
    return ConfiguracaoHistorico.objects.create(ativo=True)


def consolidar_dados_historico(*, matricula_id: int | None = None, aluno_id: int | None = None) -> ConsolidacaoHistorico:
    if not matricula_id and not aluno_id:
        raise HistoricoTecnicoError("Informe matricula_id ou aluno_id para consolidacao.")

    queryset = (
        Matricula.objects.select_related("aluno__pessoa", "curso__unidade", "turma", "consolidacao")
        .prefetch_related("curso__componentes", "estagios")
        .order_by("-data_matricula", "-id")
    )

    matricula = queryset.filter(pk=matricula_id).first() if matricula_id else queryset.filter(aluno_id=aluno_id).first()
    if not matricula:
        raise HistoricoTecnicoError("Matricula nao encontrada.")

    if not matricula.aluno_id:
        raise HistoricoTecnicoError("Nao foi possivel emitir historico sem aluno vinculado.")

    if not matricula.curso_id:
        raise HistoricoTecnicoError("Nao foi possivel emitir historico sem curso vinculado.")

    if (matricula.curso.tipo_curso or "").strip().lower() != "tecnico":
        raise HistoricoTecnicoError("O historico escolar deste modulo eh exclusivo para cursos tecnicos.")

    componentes = list(
        matricula.curso.componentes.filter(ativo=True).order_by("modulo_numero", "ordem_no_modulo", "ordem", "nome")
    )
    if not componentes:
        raise HistoricoTecnicoError("Nao foi possivel emitir historico sem componentes curriculares cadastrados.")

    notas = list(Nota.objects.filter(matricula=matricula).order_by("data_lancamento", "id"))
    if not notas:
        raise HistoricoTecnicoError("Nao foi possivel emitir historico sem registros de notas.")

    frequencias = list(Frequencia.objects.filter(matricula=matricula).order_by("data", "id"))
    if not frequencias:
        raise HistoricoTecnicoError("Nao foi possivel emitir historico sem registros de frequencia.")

    media_global = _media_ponderada(notas)
    frequencia_global = _frequencia_percentual(frequencias)

    config = _get_config()
    nota_minima = config.nota_minima_aprovacao
    freq_minima = config.frequencia_minima_aprovacao

    notas_norm = [(_normalize(nota.descricao), nota) for nota in notas]

    itens: list[dict[str, Any]] = []
    carga_total_itens = 0

    for index, componente in enumerate(componentes, start=1):
        tokens = _build_component_tokens(componente)
        notas_componente = [
            nota for descricao, nota in notas_norm if any(token and token in descricao for token in tokens)
        ]
        media_componente = _media_ponderada(notas_componente) if notas_componente else media_global
        frequencia_componente = frequencia_global

        if media_componente is None or frequencia_componente is None:
            raise HistoricoTecnicoError("Notas/frequencia insuficientes para consolidacao do historico.")

        resultado = (
            HistoricoEscolarItem.ResultadoItem.APROVADO
            if media_componente >= nota_minima and frequencia_componente >= freq_minima
            else HistoricoEscolarItem.ResultadoItem.REPROVADO
        )

        carga = int(componente.carga_horaria or 0)
        carga_total_itens += carga

        itens.append(
            {
                "componente_curricular": componente,
                "componente_nome": componente.descricao_diploma_historico or componente.nome,
                "modulo_periodo": componente.modulo_nome or (f"Modulo {componente.modulo_numero}" if componente.modulo_numero else ""),
                "carga_horaria": carga,
                "nota": media_componente,
                "frequencia": frequencia_componente,
                "resultado": resultado,
                "ordem_exibicao": index,
            }
        )

    consolidacao = getattr(matricula, "consolidacao", None)
    if consolidacao:
        situacao_raw = (consolidacao.situacao or "").upper()
        if "APROV" in situacao_raw:
            situacao_final = HistoricoEscolarTecnicoDocumento.SituacaoFinal.APROVADO
        elif "REPROV" in situacao_raw:
            situacao_final = HistoricoEscolarTecnicoDocumento.SituacaoFinal.REPROVADO
        else:
            situacao_final = HistoricoEscolarTecnicoDocumento.SituacaoFinal.INDEFINIDA
    else:
        situacao_final = (
            HistoricoEscolarTecnicoDocumento.SituacaoFinal.APROVADO
            if all(item["resultado"] == HistoricoEscolarItem.ResultadoItem.APROVADO for item in itens)
            else HistoricoEscolarTecnicoDocumento.SituacaoFinal.REPROVADO
        )

    data_conclusao = None
    if consolidacao and consolidacao.data_consolidacao:
        data_conclusao = consolidacao.data_consolidacao
    elif matricula.status == "CONCLUIDA":
        data_conclusao = matricula.data_matricula

    estagios_qs = Estagio.objects.filter(matricula=matricula).order_by("data_inicio", "id")
    estagios = [
        {
            "empresa": estagio.empresa,
            "modalidade": estagio.get_modalidade_display(),
            "status": estagio.get_status_display(),
            "carga_horaria_total": estagio.carga_horaria_total,
            "periodo": f"{estagio.data_inicio} a {estagio.data_fim_real or estagio.data_fim_prevista or '-'}",
        }
        for estagio in estagios_qs
    ]

    tcc_pratica = []
    for item in itens:
        nome = _normalize(item["componente_nome"])
        if "tcc" in nome or "trabalho de conclusao" in nome or "pratica" in nome:
            tcc_pratica.append(item)

    unidade = matricula.curso.unidade
    municipio_unidade = ", ".join(part for part in [unidade.cidade, unidade.uf] if part)

    aluno_nome = _display_user_name(matricula.aluno)
    aluno_cpf = matricula.aluno.cpf

    observacoes = ""
    if consolidacao and consolidacao.observacao:
        observacoes = consolidacao.observacao

    return ConsolidacaoHistorico(
        matricula=matricula,
        aluno_nome=aluno_nome,
        aluno_cpf=aluno_cpf,
        curso_nome=matricula.curso.nome,
        eixo_tecnologico=matricula.curso.eixo_tecnologico or "Nao informado",
        ato_autorizativo="Nao informado",
        forma_ingresso=matricula.get_tipo_matricula_display(),
        unidade_nome=unidade.nome,
        municipio_unidade=municipio_unidade,
        carga_horaria_total=carga_total_itens,
        carga_horaria_curso=int(matricula.curso.carga_horaria or 0),
        data_conclusao=data_conclusao,
        situacao_final=situacao_final,
        observacoes=observacoes,
        itens=itens,
        estagios=estagios,
        tcc_pratica=tcc_pratica,
    )


def gerar_numero_registro() -> str:
    ano = timezone.now().year
    prefixo = f"HIST-{ano}-"
    ultimo = (
        HistoricoEscolarTecnicoDocumento.objects.filter(numero_registro__startswith=prefixo)
        .order_by("-numero_registro")
        .first()
    )
    seq = 1
    if ultimo and ultimo.numero_registro:
        try:
            seq = int(ultimo.numero_registro.split("-")[-1]) + 1
        except (ValueError, IndexError):
            seq = HistoricoEscolarTecnicoDocumento.objects.filter(numero_registro__startswith=prefixo).count() + 1
    return f"{prefixo}{seq:06d}"


def gerar_codigo_validacao() -> str:
    while True:
        code = uuid.uuid4().hex[:12].upper()
        if not HistoricoEscolarTecnicoDocumento.objects.filter(codigo_validacao=code).exists():
            return code


def gerar_hash_documento(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def gerar_qrcode_validacao(url_validacao: str) -> bytes:
    qr = qrcode.QRCode(version=2, box_size=8, border=2)
    qr.add_data(url_validacao)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _logo_path() -> str | None:
    local_file = settings.BASE_DIR / "static" / "img" / "idep-ro-logo.png"
    if local_file.exists():
        return str(local_file)
    return None


def renderizar_pdf_historico(*, historico: HistoricoEscolarTecnicoDocumento, consolidacao: ConsolidacaoHistorico, url_validacao: str, qr_code_bytes: bytes) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name="HistoricoTitle", parent=styles["Heading1"], fontSize=14, leading=18, alignment=1)
    section_style = ParagraphStyle(name="HistoricoSection", parent=styles["Heading2"], fontSize=10, leading=12, textColor=colors.HexColor("#1C2B4A"))

    story = []

    logo = _logo_path()
    if logo:
        story.append(Image(logo, width=28 * mm, height=28 * mm))

    story.append(Paragraph("IDEP-ETEC/RO", title_style))
    story.append(Paragraph("HISTORICO ESCOLAR", title_style))
    story.append(Spacer(1, 4 * mm))

    info_rows = [
        ["Aluno", consolidacao.aluno_nome],
        ["CPF", consolidacao.aluno_cpf],
        ["Curso Tecnico", consolidacao.curso_nome],
        ["Eixo Tecnologico", consolidacao.eixo_tecnologico],
        ["Forma de Ingresso", consolidacao.forma_ingresso],
        ["Instituicao/Unidade", consolidacao.unidade_nome],
        ["Municipio/UF", consolidacao.municipio_unidade or "-"],
        ["Livro/Folha/Pagina", f"{historico.livro}/{historico.folha}/{historico.pagina}"],
        ["Numero de Registro", historico.numero_registro],
        ["Codigo de Validacao", historico.codigo_validacao],
        ["Versao", str(historico.versao)],
        ["Hash", historico.hash_documento],
    ]

    info_table = Table(info_rows, colWidths=[42 * mm, 138 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef2f7")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d0d7de")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Componentes Curriculares", section_style))

    componentes_rows = [["#", "Componente", "Modulo/Periodo", "CH", "Nota", "Freq.(%)", "Resultado"]]
    for item in historico.itens.order_by("ordem_exibicao", "id"):
        componentes_rows.append(
            [
                str(item.ordem_exibicao),
                item.componente_nome,
                item.modulo_periodo or "-",
                str(item.carga_horaria),
                "-" if item.nota is None else str(item.nota),
                "-" if item.frequencia is None else str(item.frequencia),
                item.get_resultado_display(),
            ]
        )

    componentes_table = Table(
        componentes_rows,
        colWidths=[9 * mm, 63 * mm, 32 * mm, 14 * mm, 18 * mm, 18 * mm, 26 * mm],
        repeatRows=1,
    )
    componentes_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1C2B4A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d0d7de")),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(componentes_table)
    story.append(Spacer(1, 5 * mm))

    resumo_rows = [
        ["Carga Horaria Total Integralizada", str(historico.carga_horaria_total)],
        ["Carga Horaria Total do Curso", str(consolidacao.carga_horaria_curso)],
        ["Situacao Final", historico.get_situacao_final_display()],
        ["Data de Conclusao", "-" if not historico.data_conclusao else historico.data_conclusao.strftime("%d/%m/%Y")],
    ]
    resumo_table = Table(resumo_rows, colWidths=[80 * mm, 100 * mm])
    resumo_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f6f8fa")),
                ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c2cc")),
                ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d0d7de")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(resumo_table)
    story.append(Spacer(1, 4 * mm))

    if consolidacao.estagios:
        story.append(Paragraph("Estagio", section_style))
        estagio_rows = [["Empresa", "Modalidade", "Status", "CH", "Periodo"]]
        for estagio in consolidacao.estagios:
            estagio_rows.append(
                [
                    estagio["empresa"],
                    estagio["modalidade"],
                    estagio["status"],
                    str(estagio["carga_horaria_total"]),
                    estagio["periodo"],
                ]
            )
        estagio_table = Table(estagio_rows, colWidths=[58 * mm, 30 * mm, 24 * mm, 12 * mm, 56 * mm], repeatRows=1)
        estagio_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e3edf7")),
                    ("BOX", (0, 0), (-1, -1), 0.3, colors.HexColor("#b8c2cc")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.2, colors.HexColor("#d0d7de")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(estagio_table)
        story.append(Spacer(1, 4 * mm))

    if historico.observacoes:
        story.append(Paragraph("Observacoes Academicas", section_style))
        story.append(Paragraph(historico.observacoes, styles["Normal"]))
        story.append(Spacer(1, 4 * mm))

    qr_image = Image(BytesIO(qr_code_bytes), width=28 * mm, height=28 * mm)
    qr_block = Table([[qr_image, Paragraph(f"Autenticacao publica: {url_validacao}", styles["Normal"])]], colWidths=[30 * mm, 150 * mm])
    qr_block.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(qr_block)
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Documento emitido eletronicamente e valido para autenticacao publica por QR Code/codigo.", styles["Italic"]))

    doc.build(story)
    return output.getvalue()


def _build_validation_url(historico_uuid: str) -> str:
    configured = str(getattr(settings, "HISTORICO_VALIDACAO_BASE_URL", "")).strip()
    if configured:
        return f"{configured.rstrip('/')}/{historico_uuid}/"
    return f"http://localhost:5175/validacao/historico/{historico_uuid}/"


def _create_evento(*, historico: HistoricoEscolarTecnicoDocumento, tipo: str, usuario=None, descricao: str = "", motivo: str = "", request=None):
    ip = None
    if request:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")

    HistoricoEscolarEvento.objects.create(
        historico=historico,
        tipo_evento=tipo,
        descricao=descricao,
        motivo=motivo,
        usuario=usuario,
        ip_address=ip,
    )


def _registrar_auditoria(*, usuario, acao: str, historico: HistoricoEscolarTecnicoDocumento, descricao: str, dados: dict[str, Any], request=None):
    LogAuditoria.registrar(
        usuario=usuario,
        acao=acao,
        modelo="HistoricoEscolarTecnicoDocumento",
        objeto_id=historico.id,
        descricao=descricao,
        dados=dados,
        request=request,
    )


def emitir_historico(*, matricula_id: int | None = None, aluno_id: int | None = None, emitido_por=None, request=None, observacoes: str = "", livro: str = "", folha: str = "", pagina: str = "") -> HistoricoEscolarTecnicoDocumento:
    if emitido_por and not getattr(emitido_por, "is_superuser", False):
        if emitido_por.tipo not in {PerfilUsuario.ADMIN, PerfilUsuario.SECRETARIA, PerfilUsuario.COORDENACAO}:
            raise HistoricoTecnicoError("Somente perfis de administracao/secretaria/direcao podem emitir historico.")

    with transaction.atomic():
        consolidacao = consolidar_dados_historico(matricula_id=matricula_id, aluno_id=aluno_id)
        config = _get_config()

        versao = (HistoricoEscolarTecnicoDocumento.objects.filter(matricula=consolidacao.matricula).aggregate(v=Max("versao")).get("v") or 0) + 1
        numero_registro = gerar_numero_registro()
        codigo_validacao = gerar_codigo_validacao()

        payload_hash = {
            "matricula": consolidacao.matricula.numero_matricula,
            "aluno": consolidacao.aluno_nome,
            "curso": consolidacao.curso_nome,
            "carga_horaria_total": consolidacao.carga_horaria_total,
            "situacao_final": consolidacao.situacao_final,
            "data_conclusao": consolidacao.data_conclusao,
            "itens": [
                {
                    "componente": item["componente_nome"],
                    "ch": item["carga_horaria"],
                    "nota": item["nota"],
                    "frequencia": item["frequencia"],
                    "resultado": item["resultado"],
                }
                for item in consolidacao.itens
            ],
            "versao": versao,
            "codigo_validacao": codigo_validacao,
            "numero_registro": numero_registro,
        }
        hash_documento = gerar_hash_documento(payload_hash)

        documento = HistoricoEscolarTecnicoDocumento.objects.create(
            aluno=consolidacao.matricula.aluno,
            matricula=consolidacao.matricula,
            curso=consolidacao.matricula.curso,
            numero_registro=numero_registro,
            livro=(livro or config.livro_padrao or "").strip(),
            folha=(folha or config.folha_padrao or "").strip(),
            pagina=(pagina or config.pagina_padrao or "").strip(),
            versao=versao,
            status=HistoricoEscolarTecnicoDocumento.StatusDocumento.EMITIDO,
            hash_documento=hash_documento,
            codigo_validacao=codigo_validacao,
            data_emissao=timezone.now(),
            emitido_por=emitido_por,
            observacoes=(observacoes or consolidacao.observacoes or "").strip(),
            carga_horaria_total=consolidacao.carga_horaria_total,
            situacao_final=consolidacao.situacao_final,
            data_conclusao=consolidacao.data_conclusao,
        )

        HistoricoEscolarItem.objects.bulk_create(
            [
                HistoricoEscolarItem(
                    historico=documento,
                    componente_curricular=item["componente_curricular"],
                    componente_nome=item["componente_nome"],
                    modulo_periodo=item["modulo_periodo"],
                    carga_horaria=item["carga_horaria"],
                    nota=item["nota"],
                    frequencia=item["frequencia"],
                    resultado=item["resultado"],
                    ordem_exibicao=item["ordem_exibicao"],
                )
                for item in consolidacao.itens
            ]
        )

        if config.assinatura_1_nome and config.assinatura_1_cargo:
            AssinaturaDocumento.objects.create(
                historico=documento,
                nome=config.assinatura_1_nome,
                cargo=config.assinatura_1_cargo,
            )
        if config.assinatura_2_nome and config.assinatura_2_cargo:
            AssinaturaDocumento.objects.create(
                historico=documento,
                nome=config.assinatura_2_nome,
                cargo=config.assinatura_2_cargo,
            )

        url_validacao = _build_validation_url(str(documento.uuid))
        qr_bytes = gerar_qrcode_validacao(url_validacao)
        pdf_bytes = renderizar_pdf_historico(
            historico=documento,
            consolidacao=consolidacao,
            url_validacao=url_validacao,
            qr_code_bytes=qr_bytes,
        )

        documento.qrcode_imagem.save(
            f"historico-{documento.uuid}-qr.png",
            ContentFile(qr_bytes),
            save=False,
        )
        documento.pdf_arquivo.save(
            f"historico-{documento.uuid}.pdf",
            ContentFile(pdf_bytes),
            save=False,
        )
        documento.save(update_fields=["qrcode_imagem", "pdf_arquivo", "atualizado_em"])

        DocumentoValidacao.objects.create(
            historico=documento,
            hash_documento=documento.hash_documento,
            hash_resumido=documento.hash_documento[:16],
            url_validacao=url_validacao,
            valido=True,
        )

        _create_evento(
            historico=documento,
            tipo=HistoricoEscolarEvento.TipoEvento.EMISSAO,
            usuario=emitido_por,
            descricao="Historico escolar tecnico emitido.",
            request=request,
        )

        _registrar_auditoria(
            usuario=emitido_por,
            acao="CRIACAO",
            historico=documento,
            descricao="Emissao de historico escolar tecnico.",
            dados={
                "numero_registro": documento.numero_registro,
                "codigo_validacao": documento.codigo_validacao,
                "versao": documento.versao,
            },
            request=request,
        )

        return documento


def reemitir_historico(*, historico_id: int, motivo: str, usuario=None, request=None) -> HistoricoEscolarTecnicoDocumento:
    if not motivo.strip():
        raise HistoricoTecnicoError("Motivo da reemissao eh obrigatorio.")

    original = HistoricoEscolarTecnicoDocumento.objects.select_related("matricula", "aluno", "curso").filter(pk=historico_id).first()
    if not original:
        raise HistoricoTecnicoError("Historico original nao encontrado para reemissao.")

    novo = emitir_historico(
        matricula_id=original.matricula_id,
        emitido_por=usuario,
        request=request,
        observacoes=original.observacoes,
        livro=original.livro,
        folha=original.folha,
        pagina=original.pagina,
    )

    novo.historico_substituido = original
    novo.versao = original.versao + 1
    novo.save(update_fields=["historico_substituido", "versao", "atualizado_em"])

    original.status = HistoricoEscolarTecnicoDocumento.StatusDocumento.SUBSTITUIDO
    original.save(update_fields=["status", "atualizado_em"])

    DocumentoValidacao.objects.filter(historico=original).update(valido=False, observacoes="Documento substituido por nova versao")

    _create_evento(
        historico=novo,
        tipo=HistoricoEscolarEvento.TipoEvento.REEMISSAO,
        usuario=usuario,
        descricao="Historico reemitido a partir de versao anterior.",
        motivo=motivo.strip(),
        request=request,
    )

    _registrar_auditoria(
        usuario=usuario,
        acao="EDICAO",
        historico=novo,
        descricao="Reemissao de historico escolar tecnico.",
        dados={
            "historico_anterior_id": original.id,
            "historico_novo_id": novo.id,
            "motivo": motivo.strip(),
        },
        request=request,
    )

    return novo


def cancelar_historico(*, historico_id: int, motivo: str, usuario=None, request=None) -> HistoricoEscolarTecnicoDocumento:
    if not motivo.strip():
        raise HistoricoTecnicoError("Motivo de cancelamento eh obrigatorio.")

    historico = HistoricoEscolarTecnicoDocumento.objects.filter(pk=historico_id).first()
    if not historico:
        raise HistoricoTecnicoError("Historico nao encontrado para cancelamento.")

    if historico.status == HistoricoEscolarTecnicoDocumento.StatusDocumento.CANCELADO:
        return historico

    historico.status = HistoricoEscolarTecnicoDocumento.StatusDocumento.CANCELADO
    historico.data_cancelamento = timezone.now()
    historico.motivo_cancelamento = motivo.strip()
    historico.save(update_fields=["status", "data_cancelamento", "motivo_cancelamento", "atualizado_em"])

    DocumentoValidacao.objects.filter(historico=historico).update(valido=False, observacoes="Documento cancelado")

    _create_evento(
        historico=historico,
        tipo=HistoricoEscolarEvento.TipoEvento.CANCELAMENTO,
        usuario=usuario,
        descricao="Historico cancelado.",
        motivo=motivo.strip(),
        request=request,
    )

    _registrar_auditoria(
        usuario=usuario,
        acao="EDICAO",
        historico=historico,
        descricao="Cancelamento de historico escolar tecnico.",
        dados={"motivo": motivo.strip()},
        request=request,
    )

    return historico


def validar_historico_publicamente(*, historico_uuid: str | None = None, codigo_validacao: str | None = None, request=None) -> dict[str, Any]:
    filters = {}
    if historico_uuid:
        filters["uuid"] = historico_uuid
    elif codigo_validacao:
        filters["codigo_validacao"] = codigo_validacao
    else:
        raise HistoricoTecnicoError("Informe uuid ou codigo de validacao para consulta publica.")

    historico = (
        HistoricoEscolarTecnicoDocumento.objects.select_related("curso", "aluno__pessoa", "validacao")
        .filter(**filters)
        .first()
    )

    if not historico:
        return {
            "documento_encontrado": False,
            "autenticidade": "INVALIDO",
            "mensagem": "Documento nao encontrado.",
        }

    status_autenticidade = "VALIDO"
    if historico.status == HistoricoEscolarTecnicoDocumento.StatusDocumento.CANCELADO:
        status_autenticidade = "CANCELADO"
    elif historico.status == HistoricoEscolarTecnicoDocumento.StatusDocumento.SUBSTITUIDO:
        status_autenticidade = "SUBSTITUIDO"

    _create_evento(
        historico=historico,
        tipo=HistoricoEscolarEvento.TipoEvento.VALIDACAO_PUBLICA,
        descricao="Consulta de autenticidade publica.",
        request=request,
    )

    _registrar_auditoria(
        usuario=None,
        acao="VISUALIZACAO",
        historico=historico,
        descricao="Consulta publica de historico escolar tecnico.",
        dados={"status_autenticidade": status_autenticidade},
        request=request,
    )

    aluno_nome = _display_user_name(historico.aluno)
    aluno_cpf = _mask_cpf(historico.aluno.cpf)
    hash_resumido = historico.hash_documento[:16] if historico.hash_documento else ""

    return {
        "documento_encontrado": True,
        "uuid": str(historico.uuid),
        "codigo_validacao": historico.codigo_validacao,
        "nome_aluno": aluno_nome,
        "cpf_mascarado": aluno_cpf,
        "curso_tecnico": historico.curso.nome,
        "eixo_tecnologico": historico.curso.eixo_tecnologico or "Nao informado",
        "carga_horaria_total": historico.carga_horaria_total,
        "situacao_final": historico.get_situacao_final_display(),
        "data_conclusao": historico.data_conclusao,
        "numero_registro": historico.numero_registro,
        "autenticidade": status_autenticidade,
        "hash_resumido": hash_resumido,
        "data_emissao": historico.data_emissao,
        "versao": historico.versao,
        "status_documento": historico.get_status_display(),
        "motivo_cancelamento": historico.motivo_cancelamento,
        "historico_substituido_id": historico.historico_substituido_id,
    }
