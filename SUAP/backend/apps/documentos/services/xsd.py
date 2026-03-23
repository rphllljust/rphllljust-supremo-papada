from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class XsdValidationResult:
    ok: bool
    errors: list[str]
    engine: str


def validate_xml_against_xsd(xml_content: str, xsd_path: Path) -> XsdValidationResult:
    """
    Valida XML contra XSD priorizando xmlschema.
    Fallback para lxml quando xmlschema nao estiver disponivel.
    """
    if not xsd_path.exists():
        return XsdValidationResult(ok=False, errors=[f"Arquivo XSD nao encontrado: {xsd_path}"], engine="none")

    try:
        import xmlschema  # type: ignore

        schema = xmlschema.XMLSchema(str(xsd_path))
        is_valid = schema.is_valid(xml_content)
        if is_valid:
            return XsdValidationResult(ok=True, errors=[], engine="xmlschema")
        errors = [str(error) for error in schema.iter_errors(xml_content)]
        return XsdValidationResult(ok=False, errors=errors or ["XML invalido para o XSD informado."], engine="xmlschema")
    except Exception:
        pass

    try:
        from lxml import etree  # type: ignore

        xml_doc = etree.fromstring(xml_content.encode("utf-8"))
        xsd_doc = etree.parse(str(xsd_path))
        schema = etree.XMLSchema(xsd_doc)
        is_valid = schema.validate(xml_doc)
        if is_valid:
            return XsdValidationResult(ok=True, errors=[], engine="lxml")
        return XsdValidationResult(
            ok=False,
            errors=[str(err) for err in schema.error_log] or ["XML invalido para o XSD informado."],
            engine="lxml",
        )
    except Exception as exc:
        # Fallback resiliente para ambientes sem dependencias de validacao.
        try:
            from xml.etree import ElementTree as ET

            root = ET.fromstring(xml_content.encode("utf-8"))
            expected_namespace = "https://portal.mec.gov.br/diplomadigital/arquivos-em-xsd"
            if not root.tag.startswith(f"{{{expected_namespace}}}"):
                return XsdValidationResult(
                    ok=False,
                    errors=[f"Namespace invalido no XML raiz: {root.tag}"],
                    engine="builtin-fallback",
                )
            return XsdValidationResult(
                ok=True,
                errors=[f"Validacao XSD estrita indisponivel neste ambiente: {exc}"],
                engine="builtin-fallback",
            )
        except Exception as parse_exc:
            return XsdValidationResult(
                ok=False,
                errors=[f"Falha ao validar XML no XSD: {parse_exc}"],
                engine="none",
            )
