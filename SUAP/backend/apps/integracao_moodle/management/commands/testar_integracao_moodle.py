from django.core.management.base import BaseCommand, CommandError

from apps.integracao_moodle.exceptions import MoodleAPIError, MoodleAuthenticationError, MoodleConfigurationError
from apps.integracao_moodle.services import get_moodle_courses


class Command(BaseCommand):
    help = "Testa a integracao com o Moodle consultando a lista de cursos disponiveis."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=5, help="Quantidade de cursos exibidos na saida.")

    def handle(self, *args, **options):
        try:
            courses = get_moodle_courses()
        except MoodleConfigurationError as exc:
            raise CommandError(str(exc)) from exc
        except MoodleAuthenticationError as exc:
            raise CommandError("Falha de autenticacao na API do Moodle. Verifique as credenciais configuradas.") from exc
        except MoodleAPIError as exc:
            raise CommandError(f"Falha ao consultar cursos no Moodle: {exc}") from exc

        self.stdout.write(self.style.SUCCESS(f"{len(courses)} cursos retornados pelo Moodle."))

        limit = max(options["limit"], 0)
        for course in courses[:limit]:
            self.stdout.write(f"- [{course.get('id')}] {course.get('shortname', '')} :: {course.get('fullname', '')}")