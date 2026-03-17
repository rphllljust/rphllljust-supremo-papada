from django.core.management.base import BaseCommand, CommandError

from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.services import sync_moodle_categories_data


class Command(BaseCommand):
    help = "Sincroniza as categorias do Moodle para o espelho local do SUAP."

    def handle(self, *args, **options):
        try:
            summary = sync_moodle_categories_data()
        except MoodleConfigurationError as exc:
            raise CommandError(str(exc)) from exc
        except MoodleAuthenticationError as exc:
            raise CommandError("Falha de autenticacao na API do Moodle. Verifique as credenciais configuradas.") from exc
        except MoodleAPIError as exc:
            raise CommandError(f"Falha ao sincronizar categorias do Moodle: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Sincronizacao de categorias do Moodle concluida."))
        self.stdout.write(f"- Categorias recebidas do Moodle: {summary.categories_received}")
        self.stdout.write(f"- Categorias criadas localmente: {summary.categories_created}")
        self.stdout.write(f"- Categorias atualizadas localmente: {summary.categories_updated}")