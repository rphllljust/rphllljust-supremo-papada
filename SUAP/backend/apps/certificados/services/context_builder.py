import base64
import re
from datetime import date, datetime
from pathlib import Path

from django.utils import timezone

from apps.certificados.models import TEXTO_PADRAO_CERTIFICADO
from apps.usuarios.models import Aluno, DocumentoPessoal


TOKEN_RE = re.compile(r"\[([a-zA-Z0-9_]+)\]")
BRASAO_RONDONIA_PATH = Path(__file__).resolve().parent.parent / "assets" / "brasao_rondonia.svg"
_BRASAO_RONDONIA_DATA_URI = None


def obter_brasao_rondonia_data_uri() -> str:
    global _BRASAO_RONDONIA_DATA_URI
    if _BRASAO_RONDONIA_DATA_URI is not None:
        return _BRASAO_RONDONIA_DATA_URI

    try:
        conteudo = BRASAO_RONDONIA_PATH.read_bytes()
        base64_svg = base64.b64encode(conteudo).decode("ascii")
        _BRASAO_RONDONIA_DATA_URI = f"data:image/svg+xml;base64,{base64_svg}"
    except Exception:
        _BRASAO_RONDONIA_DATA_URI = ""
    return _BRASAO_RONDONIA_DATA_URI


def formatar_cpf(valor: str) -> str:
    digits = "".join(ch for ch in (valor or "") if ch.isdigit())
    if len(digits) != 11:
        return valor or ""
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def formatar_data(valor) -> str:
    if isinstance(valor, datetime):
        valor = valor.date()
    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")
    if valor is None:
        return ""
    return str(valor)


def aplicar_template_texto(template_texto: str, dados: dict) -> str:
    texto = template_texto or TEXTO_PADRAO_CERTIFICADO
    return TOKEN_RE.sub(lambda match: str(dados.get(match.group(1), "")), texto)


def resolver_aluno_por_matricula(matricula):
    if not matricula or not getattr(matricula, "aluno", None):
        return None
    pessoa_id = getattr(matricula.aluno, "pessoa_id", None)
    if not pessoa_id:
        return None
    return Aluno.objects.filter(pessoa_id=pessoa_id).first()


def obter_rg_do_aluno(aluno, matricula):
    pessoa = None
    if aluno and getattr(aluno, "pessoa", None):
        pessoa = aluno.pessoa
    elif matricula and getattr(matricula.aluno, "pessoa", None):
        pessoa = matricula.aluno.pessoa

    if not pessoa:
        return ""

    documento = (
        DocumentoPessoal.objects.filter(pessoa=pessoa, tipo="RG")
        .order_by("id")
        .first()
    )
    return documento.numero if documento else ""


def montar_dados_certificado(
    *,
    modelo,
    matricula=None,
    certificado=None,
    sobrescritas=None,
    url_validacao="",
):
    sobrescritas = sobrescritas or {}
    configuracao = getattr(modelo, "configuracao_visual", None)
    curso = getattr(matricula, "curso", None) or getattr(certificado, "curso", None) or modelo.curso
    unidade = getattr(curso, "unidade", None) or getattr(certificado, "unidade", None) or modelo.unidade
    turma = getattr(matricula, "turma", None) or getattr(certificado, "turma", None)
    aluno = getattr(certificado, "aluno", None) or resolver_aluno_por_matricula(matricula)
    usuario_aluno = getattr(matricula, "aluno", None)

    nome_aluno = ""
    cpf_aluno = ""
    data_nascimento = ""
    if aluno and getattr(aluno, "pessoa", None):
        nome_aluno = aluno.pessoa.nome_completo or ""
        cpf_aluno = formatar_cpf(aluno.pessoa.cpf or "")
        data_nascimento = formatar_data(getattr(aluno.pessoa, "data_nascimento", None))
    elif usuario_aluno:
        nome_aluno = (
            (usuario_aluno.get_full_name() or "").strip()
            or getattr(usuario_aluno, "username", "")
        )
        cpf_aluno = formatar_cpf(getattr(usuario_aluno, "cpf", ""))
        data_nascimento = formatar_data(
            getattr(getattr(usuario_aluno, "pessoa", None), "data_nascimento", None)
        )

    assinaturas = list(
        modelo.assinaturas.filter(ativo=True).order_by("ordem", "id")[:2]
    )
    assinante_1 = assinaturas[0] if len(assinaturas) >= 1 else None
    assinante_2 = assinaturas[1] if len(assinaturas) >= 2 else None

    dados = {
        "nome_da_instituicao": getattr(configuracao, "nome_da_instituicao", "Instituto Estadual de Desenvolvimento da Educação Profissional de Rondônia"),
        "sigla_instituicao": getattr(configuracao, "sigla_instituicao", "IDEP"),
        "brasao_instituicao": getattr(configuracao, "brasao_instituicao", ""),
        "logo_instituicao": getattr(configuracao, "logo_instituicao", ""),
        "nome_aluno": nome_aluno,
        "cpf_aluno": cpf_aluno,
        "rg_aluno": obter_rg_do_aluno(aluno, matricula),
        "data_nascimento": data_nascimento,
        "curso_nome": getattr(curso, "nome", ""),
        "eixo_tecnologico": getattr(curso, "eixo_tecnologico", ""),
        "modalidade": (curso.get_tipo_curso_display() if curso else ""),
        "carga_horaria": getattr(curso, "carga_horaria", ""),
        "data_inicio": formatar_data(sobrescritas.get("data_inicio") or getattr(certificado, "data_inicio", None) or getattr(matricula, "data_matricula", None)),
        "data_fim": formatar_data(sobrescritas.get("data_fim") or getattr(certificado, "data_fim", None) or timezone.localdate()),
        "data_conclusao": formatar_data(sobrescritas.get("data_conclusao") or getattr(certificado, "data_conclusao", None) or timezone.localdate()),
        "cidade": getattr(unidade, "cidade", "") or getattr(configuracao, "cidade_padrao", ""),
        "estado": getattr(unidade, "uf", "") or getattr(configuracao, "estado_padrao", ""),
        "data_emissao": formatar_data(sobrescritas.get("data_emissao") or getattr(certificado, "data_emissao", None) or timezone.localdate()),
        "numero_certificado": getattr(certificado, "numero_certificado", ""),
        "livro": sobrescritas.get("livro") or getattr(certificado, "livro", ""),
        "folha": sobrescritas.get("folha") or getattr(certificado, "folha", ""),
        "codigo_validacao": getattr(certificado, "codigo_validacao", ""),
        "qr_code_validacao": url_validacao or getattr(certificado, "qr_code_validacao", ""),
        "qr_code_data_uri": getattr(certificado, "qr_code_data_uri", ""),
        "texto_certificado": "",
        "nome_assinante_1": sobrescritas.get("nome_assinante_1") or (assinante_1.nome if assinante_1 else "Assinatura 1"),
        "cargo_assinante_1": sobrescritas.get("cargo_assinante_1") or (assinante_1.cargo if assinante_1 else "Secretaria Escolar"),
        "nome_assinante_2": sobrescritas.get("nome_assinante_2") or (assinante_2.nome if assinante_2 else "Assinatura 2"),
        "cargo_assinante_2": sobrescritas.get("cargo_assinante_2") or (assinante_2.cargo if assinante_2 else "Direção Geral"),
        "logos_rodape": getattr(configuracao, "logos_rodape", []) or [],
        "marca_dagua": getattr(configuracao, "marca_dagua", ""),
        "turma_nome": getattr(turma, "nome", ""),
        "matricula_numero": getattr(matricula, "numero_matricula", ""),
    }

    dados.update({key: value for key, value in sobrescritas.items() if value not in [None, ""]})
    dados["texto_certificado"] = aplicar_template_texto(
        sobrescritas.get("texto_certificado") or modelo.texto_certificado or TEXTO_PADRAO_CERTIFICADO,
        dados,
    )
    return dados
