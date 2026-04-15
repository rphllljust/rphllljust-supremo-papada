"""
Comando para criar/atualizar o ModeloCertificado com o novo layout
visual 'Diploma IDEP-ETEC' (clone fiel do modelo oficial em papel).

Uso:
    python manage.py implantar_diploma_idep
    python manage.py implantar_diploma_idep --force   # sobrescreve se já existir
"""

from django.core.management.base import BaseCommand

from apps.certificados.models import ModeloCertificado
from apps.certificados.services.default_templates import (
    DIPLOMA_IDEP_CSS,
    DIPLOMA_IDEP_TEMPLATE,
)

NOME_MODELO = "Diploma IDEP-ETEC — Modelo Oficial"

TEXTO_PADRAO = (
    "Certificamos que [nome_aluno], de nacionalidade [nacionalidade], "
    "portador(a) do CPF n° [cpf_aluno] e RG n° [rg_aluno], nascido(a) em "
    "[data_nascimento], residente e domiciliado(a) em [naturalidade], "
    "concluiu com aproveitamento o Curso Profissionalizante em [curso_nome], "
    "pertencente ao eixo tecnológico [eixo_tecnologico], com carga horária "
    "total de [carga_horaria] horas, no ano de [data_conclusao], "
    "fazendo jus ao presente diploma."
)


class Command(BaseCommand):
    help = "Cria ou atualiza o modelo de certificado 'Diploma IDEP-ETEC'"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Sobrescreve template_html e stylesheet_css mesmo se o modelo já existir.",
        )

    def handle(self, *args, **options):
        force = options["force"]

        modelo, criado = ModeloCertificado.objects.get_or_create(
            nome=NOME_MODELO,
            defaults={
                "tipo": "DIPLOMA",
                "descricao": (
                    "Layout oficial do Diploma IDEP-ETEC — fundo pergaminho, "
                    "borda ornamental verde, brasão do Estado de Rondônia, "
                    "3 colunas de assinatura e QR code de validação."
                ),
                "template_html": DIPLOMA_IDEP_TEMPLATE,
                "stylesheet_css": DIPLOMA_IDEP_CSS,
                "texto_certificado": TEXTO_PADRAO,
                "ativo": True,
            },
        )

        if criado:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Modelo '{NOME_MODELO}' criado com sucesso (id={modelo.pk})."
                )
            )
        elif force:
            modelo.template_html = DIPLOMA_IDEP_TEMPLATE
            modelo.stylesheet_css = DIPLOMA_IDEP_CSS
            modelo.texto_certificado = TEXTO_PADRAO
            modelo.save(update_fields=["template_html", "stylesheet_css", "texto_certificado", "atualizado_em"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Modelo '{NOME_MODELO}' atualizado (id={modelo.pk})."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"[SKIP] Modelo '{NOME_MODELO}' já existe (id={modelo.pk}). "
                    "Use --force para sobrescrever."
                )
            )
