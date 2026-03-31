from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.certificados.models import CertificadoEmitido
from apps.certificados.services import (
    gerar_pdf_certificado,
    montar_dados_certificado,
    montar_url_validacao,
    registrar_historico,
)
from apps.certificados.services.issuance import _gerar_hash_integridade
from apps.certificados.services.qrcode_service import gerar_qr_code_data_uri


class Command(BaseCommand):
    help = "Implanta/atualiza QR Code e URL de validacao nos certificados existentes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ids",
            default="",
            help="Lista de IDs separados por virgula para processar somente certificados especificos.",
        )
        parser.add_argument(
            "--status-documento",
            default="EMITIDO",
            help='Status documental para filtrar (padrao: "EMITIDO"). Use "ALL" para ignorar filtro.',
        )
        parser.add_argument(
            "--skip-pdf",
            action="store_true",
            help="Nao regenera o PDF; atualiza apenas URL/QR/hash.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas simula sem gravar alteracoes.",
        )

    def _parse_ids(self, ids_raw: str):
        ids = []
        for chunk in (ids_raw or "").split(","):
            value = chunk.strip()
            if not value:
                continue
            ids.append(int(value))
        return ids

    def _build_queryset(self, ids, status_documento):
        queryset = (
            CertificadoEmitido.objects.select_related(
                "modelo",
                "matricula__curso__unidade",
                "matricula__turma",
                "matricula__aluno__pessoa",
                "aluno__pessoa",
            )
            .order_by("id")
        )
        if ids:
            queryset = queryset.filter(id__in=ids)
        if (status_documento or "").upper() != "ALL":
            queryset = queryset.filter(status_documento=(status_documento or "").upper())
        return queryset

    def handle(self, *args, **options):
        ids = self._parse_ids(options.get("ids"))
        status_documento = (options.get("status_documento") or "EMITIDO").upper()
        skip_pdf = bool(options.get("skip_pdf"))
        dry_run = bool(options.get("dry_run"))

        queryset = self._build_queryset(ids, status_documento)
        total = queryset.count()

        self.stdout.write(
            self.style.NOTICE(
                f"Processando {total} certificado(s) | status={status_documento} | skip_pdf={skip_pdf} | dry_run={dry_run}"
            )
        )

        atualizados = 0
        falhas = 0

        for certificado in queryset.iterator(chunk_size=100):
            try:
                url_validacao = montar_url_validacao(certificado.codigo_validacao)
                qr_data_uri, qr_png = gerar_qr_code_data_uri(url_validacao)

                dados_dinamicos = dict(certificado.dados_dinamicos or {})
                if not dados_dinamicos:
                    dados_dinamicos = montar_dados_certificado(
                        modelo=certificado.modelo,
                        matricula=certificado.matricula,
                        certificado=certificado,
                        url_validacao=url_validacao,
                    )

                dados_dinamicos["url_validacao"] = url_validacao
                dados_dinamicos["qr_code_validacao"] = url_validacao
                dados_dinamicos["qr_code_data_uri"] = qr_data_uri

                pdf_bytes = None
                if not skip_pdf:
                    pdf_bytes = gerar_pdf_certificado(
                        dados_certificado=dados_dinamicos,
                        modelo=certificado.modelo,
                    )

                if dry_run:
                    atualizados += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"[DRY-RUN] Certificado #{certificado.id} pronto para atualizacao."
                        )
                    )
                    continue

                with transaction.atomic():
                    certificado.url_validacao = url_validacao
                    certificado.qr_code_validacao = url_validacao
                    certificado.qr_code_data_uri = qr_data_uri
                    certificado.dados_dinamicos = dados_dinamicos
                    certificado.qr_code_image.save(
                        f"qrcode-{certificado.codigo_validacao}.png",
                        ContentFile(qr_png),
                        save=False,
                    )

                    if pdf_bytes is not None:
                        nome_pdf = f"{certificado.numero_registro or certificado.numero_certificado}.pdf"
                        certificado.pdf_arquivo.save(nome_pdf, ContentFile(pdf_bytes), save=False)

                    certificado.hash_integridade = _gerar_hash_integridade(
                        certificado=certificado,
                        dados_dinamicos=dados_dinamicos,
                        pdf_bytes=pdf_bytes,
                    )
                    certificado.save()

                    registrar_historico(
                        acao="GERACAO_PDF" if pdf_bytes is not None else "ALTERACAO_MODELO",
                        descricao=(
                            "Implantacao/atualizacao de QR Code e URL de validacao "
                            f"no documento {certificado.numero_registro or certificado.numero_certificado}"
                        ),
                        dados={
                            "certificado_id": certificado.id,
                            "numero_registro": certificado.numero_registro,
                            "tipo_documento": certificado.tipo_documento,
                            "url_validacao": url_validacao,
                            "pdf_regenerado": pdf_bytes is not None,
                        },
                        certificado=certificado,
                        modelo=certificado.modelo,
                    )

                atualizados += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Certificado #{certificado.id} atualizado com sucesso."
                    )
                )
            except Exception as exc:  # pragma: no cover - robustez operacional
                falhas += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"Falha ao atualizar certificado #{certificado.id}: {exc}"
                    )
                )

        if falhas:
            self.stdout.write(
                self.style.WARNING(
                    f"Concluido com alertas: {atualizados} atualizado(s), {falhas} falha(s)."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Concluido: {atualizados} certificado(s) atualizado(s), nenhuma falha."
                )
            )
