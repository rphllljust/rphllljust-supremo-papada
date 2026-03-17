from django.core.management.base import BaseCommand, CommandError

from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.services import import_moodle_courses_to_formacao_inicial


class Command(BaseCommand):
    help = "Importa cursos do Moodle para o catalogo interno de cursos, vinculando-os como formacao inicial por enquanto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--unidade-codigo",
            default="sede",
            help="Codigo da unidade que recebera os cursos importados. Padrao: sede.",
        )

    def handle(self, *args, **options):
        unidade_codigo = (options["unidade_codigo"] or "sede").strip().lower()

        try:
            summary = import_moodle_courses_to_formacao_inicial(unidade_codigo=unidade_codigo)
        except MoodleConfigurationError as exc:
            raise CommandError(str(exc)) from exc
        except MoodleAuthenticationError as exc:
            raise CommandError("Falha de autenticacao na API do Moodle. Verifique as credenciais configuradas.") from exc
        except MoodleAPIError as exc:
            raise CommandError(f"Falha ao importar cursos do Moodle: {exc}") from exc
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Importacao de cursos do Moodle concluida."))
        self.stdout.write(f"- Unidade: {summary.unidade_codigo}")
        self.stdout.write(f"- Cursos recebidos do Moodle: {summary.total_received}")
        if summary.catalog_storage is not None:
            self.stdout.write(f"- Categorias armazenadas/atualizadas localmente: {summary.catalog_storage.categories_received}")
            self.stdout.write(f"- Cursos armazenados/atualizados localmente: {summary.catalog_storage.courses_received}")
        self.stdout.write(f"- Cursos criados: {summary.created}")
        self.stdout.write(f"- Cursos atualizados: {summary.updated}")
        self.stdout.write(f"- Cursos vinculados a registros existentes: {summary.linked_existing}")
        self.stdout.write(f"- Cursos ignorados: {summary.skipped}")