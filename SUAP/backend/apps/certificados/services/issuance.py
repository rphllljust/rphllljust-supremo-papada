from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.certificados.models import (
    CertificadoEmitido,
    HistoricoEmissaoCertificado,
)

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
    if request:
        return request.build_absolute_uri(f"/api/v1/certificados/validar/{codigo_validacao}/")
    return f"/api/v1/certificados/validar/{codigo_validacao}/"


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


@transaction.atomic
def emitir_certificado(
    *,
    modelo,
    matricula,
    emissor,
    sobrescritas=None,
    request=None,
    gerar_pdf=False,
):
    sobrescritas = sobrescritas or {}
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
        livro=(sobrescritas.get("livro") or "").strip(),
        folha=(sobrescritas.get("folha") or "").strip(),
        termo=(sobrescritas.get("termo") or "").strip(),
        data_inicio=sobrescritas.get("data_inicio") or None,
        data_fim=sobrescritas.get("data_fim") or None,
        data_conclusao=sobrescritas.get("data_conclusao") or None,
        cidade=(sobrescritas.get("cidade") or getattr(unidade, "cidade", "")).strip(),
        estado=(sobrescritas.get("estado") or getattr(unidade, "uf", "")).strip(),
    )

    url_validacao = montar_url_validacao(certificado.codigo_validacao, request=request)
    qr_data_uri, _ = gerar_qr_code_data_uri(url_validacao)
    dados_dinamicos = montar_dados_certificado(
        modelo=modelo,
        matricula=matricula,
        certificado=certificado,
        sobrescritas=sobrescritas,
        url_validacao=url_validacao,
    )
    dados_dinamicos["qr_code_data_uri"] = qr_data_uri

    certificado.qr_code_validacao = url_validacao
    certificado.qr_code_data_uri = qr_data_uri
    certificado.nome_aluno_snapshot = dados_dinamicos.get("nome_aluno", "")
    certificado.cpf_aluno_snapshot = dados_dinamicos.get("cpf_aluno", "")
    certificado.curso_nome_snapshot = dados_dinamicos.get("curso_nome", "")
    certificado.texto_certificado_snapshot = dados_dinamicos.get("texto_certificado", "")
    certificado.dados_dinamicos = dados_dinamicos

    if gerar_pdf:
        pdf = gerar_pdf_certificado(dados_certificado=dados_dinamicos, modelo=modelo)
        nome_pdf = f"{certificado.numero_certificado}.pdf"
        certificado.pdf_arquivo.save(nome_pdf, ContentFile(pdf), save=False)

    certificado.save()

    registrar_historico(
        acao="EMISSAO",
        descricao=f"Certificado {certificado.numero_certificado} emitido",
        dados={
            "numero_certificado": certificado.numero_certificado,
            "matricula_id": matricula.id if matricula else None,
            "modelo_id": modelo.id,
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
        descricao="Emissão em lote de certificados",
        dados={
            "modelo_id": modelo.id,
            "quantidade_sucesso": len(certificados),
            "quantidade_erro": len(erros),
            "erros": erros,
        },
        usuario=emissor,
        modelo=modelo,
        request=request,
    )
    return certificados, erros


def registrar_reimpressao(certificado, usuario=None, request=None):
    certificado.reimpressoes += 1
    certificado.ultima_reimpressao_em = timezone.now()
    certificado.save(update_fields=["reimpressoes", "ultima_reimpressao_em", "atualizado_em"])
    registrar_historico(
        acao="REIMPRESSAO",
        descricao=f"Reimpressão do certificado {certificado.numero_certificado}",
        dados={
            "numero_certificado": certificado.numero_certificado,
            "reimpressoes": certificado.reimpressoes,
        },
        usuario=usuario,
        certificado=certificado,
        modelo=certificado.modelo,
        request=request,
    )

