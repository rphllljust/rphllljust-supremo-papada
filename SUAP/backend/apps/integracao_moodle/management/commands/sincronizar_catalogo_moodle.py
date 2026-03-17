from django.core.management.base import BaseCommand, CommandError

from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.services import sync_moodle_catalog_data


class Command(BaseCommand):
    help = "Sincroniza categorias e cursos do Moodle para o espelho local do SUAP, sem importar para o catalogo interno."

    def handle(self, *args, **options):
        try:
            summary, _ = sync_moodle_catalog_data()
        except MoodleConfigurationError as exc:
            raise CommandError(str(exc)) from exc
        except MoodleAuthenticationError as exc:
            raise CommandError("Falha de autenticacao na API do Moodle. Verifique as credenciais configuradas.") from exc
        except MoodleAPIError as exc:
            raise CommandError(f"Falha ao sincronizar catalogo do Moodle: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Sincronizacao do catalogo do Moodle concluida."))
        self.stdout.write(f"- Categorias recebidas do Moodle: {summary.categories_received}")
        self.stdout.write(f"- Categorias criadas localmente: {summary.categories_created}")
        self.stdout.write(f"- Categorias atualizadas localmente: {summary.categories_updated}")
        self.stdout.write(f"- Cursos recebidos do Moodle: {summary.courses_received}")
        self.stdout.write(f"- Cursos criados localmente: {summary.courses_created}")
        self.stdout.write(f"- Cursos atualizados localmente: {summary.courses_updated}")
        self.stdout.write(f"- Cursos vinculados ao catalogo interno: {summary.courses_linked_internal}")