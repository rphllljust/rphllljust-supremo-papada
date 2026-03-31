import hashlib
import json
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.certificados.models import CertificadoEmitido, HistoricoEmissaoCertificado

from .context_builder import montar_dados_certificado, resolver_aluno_por_matricula
from .pdf_service import gerar_pdf_certificado
from .qrcode_service import gerar_qr_code_data_uri


def obter_ip_request(request):
    if not request:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def montar_url_validacao(codigo_validacao: str, request=None) -> str:
    path = f"/validar-documento/{codigo_validacao}"
    base_configurada = (
        getattr(settings, "CERTIFICADOS_VALIDATION_FRONTEND_BASE_URL", "") or ""
    ).strip()

    if base_configurada:
        if "{codigo}" in base_configurada:
            return base_configurada.format(codigo=codigo_validacao)
        return f"{base_configurada.rstrip('/')}{path}"

    if request:
        origin = (request.META.get("HTTP_ORIGIN") or "").strip()
        if origin:
            return f"{origin.rstrip('/')}{path}"

        referer = (request.META.get("HTTP_REFERER") or "").strip()
        if referer:
            parsed = urlparse(referer)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}{path}"

        return request.build_absolute_uri(path)
    return path


def registrar_historico(
    *,
    acao,
    descricao="",
    dados=None,
    usuario=None,
    certificado=None,
    modelo=None,
    request=None,
):
    return HistoricoEmissaoCertificado.objects.create(
        acao=acao,
        descricao=descricao or "",
        dados=dados or {},
        usuario=usuario,
        certificado=certificado,
        modelo=modelo,
        ip_origem=obter_ip_request(request),
    )


def _resolver_tipo_documento(*, modelo, sobrescritas=None, tipo_documento=None):
    sobrescritas = sobrescritas or {}
    tipo = (tipo_documento or sobrescritas.get("tipo_documento") or "").strip().upper()
    if tipo in {"DIPLOMA", "HISTORICO"}:
        return tipo

    modelo_tipo = (getattr(modelo, "tipo", "") or "").strip().upper()
    if modelo_tipo == "DIPLOMA":
        return "DIPLOMA"
    return "HISTORICO"


def _obter_documento_ativo(matricula, tipo_documento):
    if not matricula:
        return None
    return (
        CertificadoEmitido.objects
        .filter(
            matricula=matricula,
            tipo_documento=tipo_documento,
            status_documento="EMITIDO",
        )
        .order_by("-criado_em", "-id")
        .first()
    )


def _gerar_hash_integridade(*, certificado, dados_dinamicos, pdf_bytes=None):
    payload = {
        "numero_certificado": certificado.numero_certificado,
        "numero_registro": certificado.numero_registro,
        "tipo_documento": certificado.tipo_documento,
        "codigo_validacao": certificado.codigo_validacao,
        "matricula_id": certificado.matricula_id,
        "aluno": certificado.nome_aluno_snapshot,
        "cpf": certificado.cpf_aluno_snapshot,
        "curso": certificado.curso_nome_snapshot,
        "data_emissao": str(certificado.data_emissao or ""),
        "data_registro": str(certificado.data_registro or ""),
        "livro": certificado.livro,
        "folha": certificado.folha,
        "pagina": certificado.pagina,
        "url_validacao": certificado.url_validacao or certificado.qr_code_validacao,
        "dados": dados_dinamicos or {},
    }
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    digest = hashlib.sha256()
    digest.update(canonical)
    if pdf_bytes:
        digest.update(pdf_bytes)
    return digest.hexdigest()


@transaction.atomic
def emitir_certificado(
    *,
    modelo,
    matricula,
    emissor,
    sobrescritas=None,
    request=None,
    gerar_pdf=False,
    tipo_documento=None,
    forcar_reemissao=False,
    referencia_reemissao=None,
):
    sobrescritas = sobrescritas or {}
    tipo_doc = _resolver_tipo_documento(modelo=modelo, sobrescritas=sobrescritas, tipo_documento=tipo_documento)

    documento_existente = _obter_documento_ativo(matricula, tipo_doc)
    if documento_existente and not forcar_reemissao:
        raise ValueError(
            f"Ja existe documento ativo para esta matricula ({tipo_doc}): {documento_existente.numero_registro or documento_existente.numero_certificado}."
        )

    if forcar_reemissao and not referencia_reemissao:
        referencia_reemissao = documento_existente

    aluno = resolver_aluno_por_matricula(matricula)
    curso = matricula.curso if matricula else modelo.curso
    unidade = curso.unidade if curso else modelo.unidade
    turma = matricula.turma if matricula else None

    certificado = CertificadoEmitido.objects.create(
        modelo=modelo,
        aluno=aluno,
        matricula=matricula,
        curso=curso,
        unidade=unidade,
        turma=turma,
        usuario_emissor=emissor,
        reemitido_de=referencia_reemissao,
        tipo_documento=tipo_doc,
        livro=(sobrescritas.get("livro") or "").strip(),
        folha=(sobrescritas.get("folha") or "").strip(),
        pagina=(sobrescritas.get("pagina") or "").strip(),
        termo=(sobrescritas.get("termo") or "").strip(),
        data_inicio=sobrescritas.get("data_inicio") or None,
        data_fim=sobrescritas.get("data_fim") or None,
        data_conclusao=sobrescritas.get("data_conclusao") or None,
        data_registro=sobrescritas.get("data_registro") or None,
        cidade=(sobrescritas.get("cidade") or getattr(unidade, "cidade", "")).strip(),
        estado=(sobrescritas.get("estado") or getattr(unidade, "uf", "")).strip(),
        status_documento="RASCUNHO",
        observacoes=(sobrescritas.get("observacoes") or "").strip(),
    )

    url_validacao = montar_url_validacao(certificado.codigo_validacao, request=request)
    qr_data_uri, qr_png = gerar_qr_code_data_uri(url_validacao)

    dados_dinamicos = montar_dados_certificado(
        modelo=modelo,
        matricula=matricula,
        certificado=certificado,
        sobrescritas={**sobrescritas, "tipo_documento": tipo_doc},
        url_validacao=url_validacao,
    )
    dados_dinamicos = json.loads(json.dumps(dados_dinamicos, ensure_ascii=False, default=str))
    dados_dinamicos["qr_code_data_uri"] = qr_data_uri

    certificado.url_validacao = url_validacao
    certificado.qr_code_validacao = url_validacao
    certificado.qr_code_data_uri = qr_data_uri
    certificado.nome_aluno_snapshot = dados_dinamicos.get("nome_aluno", "")
    certificado.cpf_aluno_snapshot = dados_dinamicos.get("cpf_aluno", "")
    certificado.curso_nome_snapshot = dados_dinamicos.get("curso_nome", "")
    certificado.texto_certificado_snapshot = dados_dinamicos.get("texto_certificado", "")
    certificado.dados_dinamicos = dados_dinamicos

    qr_nome = f"qrcode-{certificado.codigo_validacao}.png"
    certificado.qr_code_image.save(qr_nome, ContentFile(qr_png), save=False)

    pdf_bytes = None
    if gerar_pdf:
        pdf_bytes = gerar_pdf_certificado(dados_certificado=dados_dinamicos, modelo=modelo)
        nome_pdf = f"{certificado.numero_registro or certificado.numero_certificado}.pdf"
        certificado.pdf_arquivo.save(nome_pdf, ContentFile(pdf_bytes), save=False)

    certificado.hash_integridade = _gerar_hash_integridade(
        certificado=certificado,
        dados_dinamicos=dados_dinamicos,
        pdf_bytes=pdf_bytes,
    )
    certificado.status_documento = "EMITIDO"
    if not certificado.data_registro:
        certificado.data_registro = timezone.localdate()

    if certificado.status_documento == "CANCELADO":
        certificado.status = "CERTIFICADO_CANCELADO"
    else:
        certificado.status = "DIPLOMA_REGISTRADO"

    certificado.save()

    if referencia_reemissao and referencia_reemissao.status_documento != "CANCELADO":
        referencia_reemissao.status_documento = "REEMITIDO"
        referencia_reemissao.save(update_fields=["status_documento", "atualizado_em"])

    acao = "REEMISSAO" if referencia_reemissao else "EMISSAO"
    registrar_historico(
        acao=acao,
        descricao=f"Documento {certificado.numero_registro} emitido ({certificado.tipo_documento})",
        dados={
            "numero_certificado": certificado.numero_certificado,
            "numero_registro": certificado.numero_registro,
            "tipo_documento": certificado.tipo_documento,
            "matricula_id": matricula.id if matricula else None,
            "modelo_id": modelo.id,
            "reemitido_de": referencia_reemissao.id if referencia_reemissao else None,
        },
        usuario=emissor,
        certificado=certificado,
        modelo=modelo,
        request=request,
    )
    return certificado


@transaction.atomic
def emitir_certificados_em_lote(
    *,
    modelo,
    matriculas,
    emissor,
    sobrescritas=None,
    request=None,
    gerar_pdf=False,
    tipo_documento=None,
):
    certificados = []
    erros = []
    for matricula in matriculas:
        try:
            certificados.append(
                emitir_certificado(
                    modelo=modelo,
                    matricula=matricula,
                    emissor=emissor,
                    sobrescritas=sobrescritas,
                    request=request,
                    gerar_pdf=gerar_pdf,
                    tipo_documento=tipo_documento,
                )
            )
        except Exception as exc:
            erros.append(
                {
                    "matricula_id": matricula.id,
                    "numero_matricula": matricula.numero_matricula,
                    "erro": str(exc),
                }
            )

    registrar_historico(
        acao="EMISSAO_LOTE",
        descricao="Emissao em lote de documentos",
        dados={
            "modelo_id": modelo.id,
            "tipo_documento": _resolver_tipo_documento(modelo=modelo, sobrescritas=sobrescritas, tipo_documento=tipo_documento),
            "quantidade_sucesso": len(certificados),
            "quantidade_erro": len(erros),
            "erros": erros,
        },
        usuario=emissor,
        modelo=modelo,
        request=request,
    )
    return certificados, erros


@transaction.atomic
def cancelar_certificado(*, certificado, usuario=None, motivo="", request=None):
    if certificado.status_documento == "CANCELADO":
        return certificado

    certificado.status_documento = "CANCELADO"
    certificado.status = "CERTIFICADO_CANCELADO"
    if motivo:
        certificado.observacoes = f"{certificado.observacoes}\n[Cancelamento] {motivo}".strip()
    certificado.save(update_fields=["status_documento", "status", "observacoes", "atualizado_em"])

    registrar_historico(
        acao="CANCELAMENTO",
        descricao=f"Documento {certificado.numero_registro} cancelado",
        dados={"motivo": motivo or "", "certificado_id": certificado.id},
        usuario=usuario,
        certificado=certificado,
        modelo=certificado.modelo,
        request=request,
    )
    return certificado


@transaction.atomic
def reemitir_certificado(*, certificado, emissor, sobrescritas=None, request=None, gerar_pdf=True):
    if not certificado.matricula_id:
        raise ValueError("Nao e possivel reemitir documento sem matricula vinculada.")

    base_sobrescritas = {
        "livro": certificado.livro,
        "folha": certificado.folha,
        "pagina": certificado.pagina,
        "termo": certificado.termo,
        "cidade": certificado.cidade,
        "estado": certificado.estado,
        "data_inicio": certificado.data_inicio,
        "data_fim": certificado.data_fim,
        "data_conclusao": certificado.data_conclusao,
        "data_registro": certificado.data_registro,
        "observacoes": certificado.observacoes,
    }
    if sobrescritas:
        base_sobrescritas.update(sobrescritas)

    return emitir_certificado(
        modelo=certificado.modelo,
        matricula=certificado.matricula,
        emissor=emissor,
        sobrescritas=base_sobrescritas,
        request=request,
        gerar_pdf=gerar_pdf,
        tipo_documento=certificado.tipo_documento,
        forcar_reemissao=True,
        referencia_reemissao=certificado,
    )


def registrar_reimpressao(certificado, usuario=None, request=None):
    certificado.reimpressoes += 1
    certificado.ultima_reimpressao_em = timezone.now()
    certificado.save(update_fields=["reimpressoes", "ultima_reimpressao_em", "atualizado_em"])
    registrar_historico(
        acao="REIMPRESSAO",
        descricao=f"Reimpressao do documento {certificado.numero_registro or certificado.numero_certificado}",
        dados={
            "numero_certificado": certificado.numero_certificado,
            "numero_registro": certificado.numero_registro,
            "reimpressoes": certificado.reimpressoes,
        },
        usuario=usuario,
        certificado=certificado,
        modelo=certificado.modelo,
        request=request,
    )
