from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Max
from django.utils import timezone

from apps.auditoria.models import LogAuditoria
from apps.documentos.models import HistoricoEscolar, HistoricoEscolarDigital
from apps.usuarios.models import PerfilUsuario

from .exceptions import HistoricoDigitalBusinessError, HistoricoDigitalValidationError
from .mec_xml import build_render_payload, render_historico_xml
from .pdf_qr import build_qr_data_uri, generate_simple_pdf_bytes
from .signature import sign_xml_if_configured
from .xsd import validate_xml_against_xsd


@dataclass(frozen=True)
class EmissaoHistoricoDigitalInput:
    tipo_documento: str
    assinar_xml: bool = False
    forcar_reemissao: bool = False
    referencia_original_id: int | None = None


def _next_version(historico: HistoricoEscolar) -> int:
    current = historico.versoes_digitais.aggregate(max_version=Max("versao"))["max_version"] or 0
    return current + 1


def _validation_url(chave_autenticacao: str) -> str:
    base_url = str(
        getattr(
            settings,
            "DOCUMENTOS_VALIDATION_BASE_URL",
            "http://localhost:8000/api/v1/historicos-digitais/validar-publico/",
        )
    ).strip()
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}chave={chave_autenticacao}"


def _validate_business_rules(historico: HistoricoEscolar, tipo_documento: str):
    matricula = historico.matricula
    if not matricula:
        raise HistoricoDigitalBusinessError("Historico sem matricula vinculada.")

    if tipo_documento == "FINAL":
        if matricula.status != "CONCLUIDA":
            raise HistoricoDigitalBusinessError(
                "Historico final exige matricula concluida."
            )
        consolidacao = getattr(matricula, "consolidacao", None)
        if not consolidacao or consolidacao.situacao != "APROVADO":
            raise HistoricoDigitalBusinessError(
                "Historico final exige consolidacao academica aprovada."
            )


def _resolve_original_reference(
    historico: HistoricoEscolar,
    reference_id: int | None,
) -> HistoricoEscolarDigital:
    if reference_id:
        doc = HistoricoEscolarDigital.objects.filter(pk=reference_id, historico=historico).first()
        if doc:
            return doc
    doc = (
        historico.versoes_digitais
        .filter(revogado=False)
        .exclude(tipo_documento="SEGUNDA_VIA_NATO_FISICO")
        .order_by("-emitido_em")
        .first()
    )
    if not doc:
        raise HistoricoDigitalBusinessError(
            "Segunda via exige referencia a um historico digital original."
        )
    return doc


def emitir_historico_digital(
    *,
    historico: HistoricoEscolar,
    emissor,
    payload: EmissaoHistoricoDigitalInput,
    request=None,
) -> tuple[HistoricoEscolarDigital, bool]:
    tipo_documento = payload.tipo_documento
    if tipo_documento not in dict(HistoricoEscolarDigital.TIPO_DOCUMENTO_CHOICES):
        raise HistoricoDigitalBusinessError("Tipo de documento digital invalido.")

    if not emissor or not getattr(emissor, "is_authenticated", False):
        raise HistoricoDigitalBusinessError("Usuario emissor nao autenticado.")

    if getattr(emissor, "tipo", None) not in {PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN} and not getattr(emissor, "is_superuser", False):
        raise HistoricoDigitalBusinessError("Somente secretaria e administrador podem emitir documentos oficiais.")

    _validate_business_rules(historico, tipo_documento)

    if tipo_documento != "SEGUNDA_VIA_NATO_FISICO" and not payload.forcar_reemissao:
        existing = (
            historico.versoes_digitais
            .filter(tipo_documento=tipo_documento, revogado=False)
            .order_by("-emitido_em")
            .first()
        )
        if existing:
            return existing, False

    referencia_original = None
    referencia_numero = ""
    if tipo_documento == "SEGUNDA_VIA_NATO_FISICO":
        referencia_original = _resolve_original_reference(historico, payload.referencia_original_id)
        referencia_numero = referencia_original.numero_unico

    versao = _next_version(historico)
    render_payload = build_render_payload(
        historico,
        tipo_documento=tipo_documento,
        versao=versao,
        referencia_original_numero=referencia_numero,
    )
    xml_content = render_historico_xml(render_payload)

    xsd_root = Path(str(getattr(settings, "DOCUMENTOS_MEC_XSD_ROOT", ""))).expanduser()
    if not xsd_root:
        xsd_root = settings.BASE_DIR / "schemas" / "mec" / "historico"
    main_xsd = xsd_root / "documentoHistoricoEscolar_v1.05.xsd"
    validation_result = validate_xml_against_xsd(xml_content, main_xsd)
    strict_xsd_validation = bool(getattr(settings, "DOCUMENTOS_XSD_STRICT_VALIDATION", False))
    if strict_xsd_validation and not validation_result.ok:
        raise HistoricoDigitalValidationError(
            "Falha na validacao XSD: " + " | ".join(validation_result.errors[:3])
        )

    signature_result = sign_xml_if_configured(xml_content) if payload.assinar_xml else None
    xml_for_hash = signature_result.xml_signed if signature_result else xml_content
    hash_documento = hashlib.sha256(xml_for_hash.encode("utf-8")).hexdigest()

    digital_doc = HistoricoEscolarDigital.objects.create(
        historico=historico,
        referencia_original=referencia_original,
        tipo_documento=tipo_documento,
        status=(
            "ASSINADO"
            if signature_result and signature_result.signed
            else ("VALIDADO" if validation_result.ok else "GERADO")
        ),
        versao=versao,
        hash_documento=hash_documento,
        xml_conteudo=xml_content,
        xml_assinado_conteudo=signature_result.xml_signed if signature_result else "",
        validacao_xsd_ok=validation_result.ok,
        validacao_xsd_erros=validation_result.errors,
        assinado_digitalmente=bool(signature_result and signature_result.signed),
        assinatura_metadados=signature_result.metadata if signature_result else {"signed": False, "reason": "not_requested"},
        emitido_por=emissor,
    )

    validation_url = _validation_url(digital_doc.chave_autenticacao)
    qr_data_uri = build_qr_data_uri(validation_url)
    pdf_bytes = generate_simple_pdf_bytes(
        render_payload,
        chave_autenticacao=digital_doc.chave_autenticacao,
        hash_documento=hash_documento,
        validation_url=validation_url,
    )

    digital_doc.qr_payload_url = validation_url
    digital_doc.qr_code_data_uri = qr_data_uri
    digital_doc.pdf_arquivo.save(
        f"{digital_doc.numero_unico}.pdf",
        ContentFile(pdf_bytes),
        save=False,
    )
    digital_doc.save(
        update_fields=[
            "qr_payload_url",
            "qr_code_data_uri",
            "pdf_arquivo",
            "atualizado_em",
        ]
    )

    LogAuditoria.registrar(
        usuario=emissor,
        acao="CRIACAO",
        modelo="HistoricoEscolarDigital",
        objeto_id=digital_doc.id,
        descricao="Emissao de historico escolar digital",
        dados={
            "numero_unico": digital_doc.numero_unico,
            "tipo_documento": digital_doc.tipo_documento,
            "historico_id": historico.id,
            "validacao_xsd_ok": digital_doc.validacao_xsd_ok,
            "assinado_digitalmente": digital_doc.assinado_digitalmente,
            "forcar_reemissao": payload.forcar_reemissao,
        },
        request=request,
    )

    return digital_doc, True


def revogar_historico_digital(*, documento: HistoricoEscolarDigital, motivo: str, emissor, request=None) -> HistoricoEscolarDigital:
    if documento.revogado:
        return documento

    if not motivo.strip():
        raise HistoricoDigitalBusinessError("Motivo de revogacao e obrigatorio.")

    if getattr(emissor, "tipo", None) not in {PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN} and not getattr(emissor, "is_superuser", False):
        raise HistoricoDigitalBusinessError("Somente secretaria e administrador podem revogar documentos oficiais.")

    documento.revogado = True
    documento.status = "REVOGADO"
    documento.motivo_revogacao = motivo.strip()
    documento.save(update_fields=["revogado", "status", "motivo_revogacao", "atualizado_em"])

    LogAuditoria.registrar(
        usuario=emissor,
        acao="EDICAO",
        modelo="HistoricoEscolarDigital",
        objeto_id=documento.id,
        descricao="Revogacao de historico escolar digital",
        dados={
            "numero_unico": documento.numero_unico,
            "motivo_revogacao": documento.motivo_revogacao,
        },
        request=request,
    )
    return documento
