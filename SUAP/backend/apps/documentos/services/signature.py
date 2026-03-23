from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from django.conf import settings


@dataclass(frozen=True)
class SignatureResult:
    xml_signed: str
    signed: bool
    metadata: dict


def sign_xml_if_configured(xml_content: str) -> SignatureResult:
    """
    Assina XML em modo enveloped quando configurado.
    Em fallback, retorna o XML original com metadados de nao assinatura.
    """
    enabled = bool(getattr(settings, "DOCUMENTOS_XMLDSIG_ENABLED", False))
    private_key_path = Path(str(getattr(settings, "DOCUMENTOS_XMLDSIG_PRIVATE_KEY_PATH", "")).strip())
    cert_path = Path(str(getattr(settings, "DOCUMENTOS_XMLDSIG_CERT_PATH", "")).strip())

    if not enabled:
        return SignatureResult(
            xml_signed=xml_content,
            signed=False,
            metadata={"signed": False, "reason": "xml_dsig_disabled"},
        )

    if not private_key_path.exists() or not cert_path.exists():
        return SignatureResult(
            xml_signed=xml_content,
            signed=False,
            metadata={
                "signed": False,
                "reason": "missing_key_or_certificate",
                "private_key_path": str(private_key_path),
                "cert_path": str(cert_path),
            },
        )

    try:
        from lxml import etree  # type: ignore
        from signxml import XMLSigner, methods  # type: ignore

        xml_tree = etree.fromstring(xml_content.encode("utf-8"))
        signer = XMLSigner(method=methods.enveloped, digest_algorithm="sha256", signature_algorithm="rsa-sha256")
        signed_tree = signer.sign(
            xml_tree,
            key=private_key_path.read_bytes(),
            cert=cert_path.read_bytes(),
        )
        xml_signed = etree.tostring(signed_tree, encoding="utf-8", xml_declaration=True).decode("utf-8")
        return SignatureResult(
            xml_signed=xml_signed,
            signed=True,
            metadata={
                "signed": True,
                "algorithm": "rsa-sha256",
                "digest": "sha256",
            },
        )
    except Exception as exc:
        return SignatureResult(
            xml_signed=xml_content,
            signed=False,
            metadata={
                "signed": False,
                "reason": "signature_error",
                "error": str(exc),
            },
        )
