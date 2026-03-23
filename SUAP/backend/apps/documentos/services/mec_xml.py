from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from xml.etree import ElementTree as ET

from apps.documentos.models import HistoricoEscolar

MEC_NAMESPACE = "https://portal.mec.gov.br/diplomadigital/arquivos-em-xsd"
DS_NAMESPACE = "https://www.w3.org/2000/09/xmldsig#"

ET.register_namespace("", MEC_NAMESPACE)
ET.register_namespace("ds", DS_NAMESPACE)

DOCUMENT_ROOT_BY_TYPE = {
    "PARCIAL": "DocumentoHistoricoEscolarParcial",
    "FINAL": "DocumentoHistoricoEscolarFinal",
    "SEGUNDA_VIA_NATO_FISICO": "DocumentoHistoricoEscolarSegundaViaNatoFisico",
}


@dataclass(frozen=True)
class HistoricoRenderPayload:
    historico_id: int
    numero_protocolo: str
    tipo_documento: str
    versao: int
    data_emissao_iso: str
    instituicao_nome: str
    unidade_nome: str
    aluno_nome: str
    aluno_cpf: str
    matricula_numero: str
    curso_nome: str
    carga_horaria_total: int
    componentes: list[dict[str, Any]]
    media_final: str
    frequencia_percentual: str
    situacao: str
    referencia_original_numero: str


def _as_decimal_text(value: Decimal | float | int | None) -> str:
    if value is None:
        return ""
    decimal_value = Decimal(str(value))
    return f"{decimal_value:.2f}"


def build_render_payload(
    historico: HistoricoEscolar,
    *,
    tipo_documento: str,
    versao: int,
    referencia_original_numero: str = "",
) -> HistoricoRenderPayload:
    matricula = historico.matricula
    curso = matricula.curso if matricula else None
    turma = matricula.turma if matricula else None
    unidade = curso.unidade if curso else None
    aluno = matricula.aluno if matricula else None
    pessoa = getattr(aluno, "pessoa", None) if aluno else None
    consolidacao = getattr(matricula, "consolidacao", None) if matricula else None

    notas = []
    if matricula:
        for nota in matricula.notas.order_by("data_lancamento", "id"):
            notas.append(
                {
                    "nome": nota.descricao,
                    "carga_horaria": 0,
                    "nota": _as_decimal_text(nota.valor),
                    "frequencia": "",
                    "situacao": "",
                }
            )

    if not notas and curso:
        for componente in curso.componentes.order_by("ordem", "nome"):
            notas.append(
                {
                    "nome": componente.nome,
                    "carga_horaria": componente.carga_horaria or 0,
                    "nota": "",
                    "frequencia": "",
                    "situacao": "",
                }
            )

    aluno_nome = ""
    aluno_cpf = ""
    if aluno:
        aluno_nome = (pessoa.nome_completo if pessoa and pessoa.nome_completo else aluno.get_full_name().strip()) or aluno.username
        aluno_cpf = aluno.cpf or ""

    situacao = ""
    media_final = ""
    frequencia_percentual = ""
    if consolidacao:
        situacao = consolidacao.get_situacao_display()
        media_final = _as_decimal_text(consolidacao.media_final)
        frequencia_percentual = _as_decimal_text(consolidacao.percentual_frequencia)

    return HistoricoRenderPayload(
        historico_id=historico.id,
        numero_protocolo=historico.numero_protocolo,
        tipo_documento=tipo_documento,
        versao=versao,
        data_emissao_iso=historico.data_emissao.isoformat() if historico.data_emissao else "",
        instituicao_nome="Instituto de Desenvolvimento Educacional Profissional de Rondonia",
        unidade_nome=unidade.nome if unidade else "",
        aluno_nome=aluno_nome,
        aluno_cpf=aluno_cpf,
        matricula_numero=matricula.numero_matricula if matricula else "",
        curso_nome=curso.nome if curso else "",
        carga_horaria_total=int(curso.carga_horaria or 0) if curso else 0,
        componentes=notas,
        media_final=media_final,
        frequencia_percentual=frequencia_percentual,
        situacao=situacao,
        referencia_original_numero=referencia_original_numero,
    )


def _node(tag: str) -> str:
    return f"{{{MEC_NAMESPACE}}}{tag}"


def _append_text(parent: ET.Element, tag: str, value: str) -> ET.Element:
    child = ET.SubElement(parent, _node(tag))
    child.text = value or ""
    return child


def render_historico_xml(payload: HistoricoRenderPayload) -> str:
    root_name = DOCUMENT_ROOT_BY_TYPE[payload.tipo_documento]
    root = ET.Element(_node(root_name), attrib={"versao": "1.05"})

    identificacao = ET.SubElement(root, _node("IdentificacaoDocumento"))
    _append_text(identificacao, "HistoricoId", str(payload.historico_id))
    _append_text(identificacao, "NumeroProtocolo", payload.numero_protocolo)
    _append_text(identificacao, "VersaoDocumento", str(payload.versao))
    _append_text(identificacao, "DataEmissao", payload.data_emissao_iso)

    if payload.referencia_original_numero:
        _append_text(identificacao, "ReferenciaOriginal", payload.referencia_original_numero)

    instituicao = ET.SubElement(root, _node("DadosInstituicao"))
    _append_text(instituicao, "NomeInstituicao", payload.instituicao_nome)
    _append_text(instituicao, "Unidade", payload.unidade_nome)

    aluno = ET.SubElement(root, _node("DadosAluno"))
    _append_text(aluno, "Nome", payload.aluno_nome)
    _append_text(aluno, "CPF", payload.aluno_cpf)
    _append_text(aluno, "NumeroMatricula", payload.matricula_numero)

    curso = ET.SubElement(root, _node("DadosCurso"))
    _append_text(curso, "NomeCurso", payload.curso_nome)
    _append_text(curso, "CargaHorariaTotal", str(payload.carga_horaria_total))
    _append_text(curso, "MediaFinal", payload.media_final)
    _append_text(curso, "FrequenciaPercentual", payload.frequencia_percentual)
    _append_text(curso, "SituacaoFinal", payload.situacao)

    componentes = ET.SubElement(root, _node("ComponentesCurriculares"))
    for item in payload.componentes:
        componente = ET.SubElement(componentes, _node("Componente"))
        _append_text(componente, "Nome", str(item.get("nome", "")))
        _append_text(componente, "CargaHoraria", str(item.get("carga_horaria", "")))
        _append_text(componente, "Nota", str(item.get("nota", "")))
        _append_text(componente, "Frequencia", str(item.get("frequencia", "")))
        _append_text(componente, "Situacao", str(item.get("situacao", "")))

    return ET.tostring(root, encoding="unicode", xml_declaration=True)
