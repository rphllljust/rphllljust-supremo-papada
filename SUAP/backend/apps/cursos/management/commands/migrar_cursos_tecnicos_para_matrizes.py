from django.core.management.base import BaseCommand

from apps.cursos.services import migrate_technical_courses_to_initial_matrizes, rollback_initial_matrices


class Command(BaseCommand):
    help = 'Cria matrizes curriculares iniciais para cursos técnicos existentes e vincula seus componentes.'

    def add_arguments(self, parser):
        parser.add_argument('--ano', type=int, dest='ano_referencia', help='Ano de referência para a matriz inicial.')
        parser.add_argument('--curso-id', type=int, action='append', dest='course_ids', help='Limita a execução a cursos específicos.')
        parser.add_argument('--rollback', action='store_true', help='Desfaz a migração inicial removendo as matrizes geradas e desvinculando componentes.')

    def handle(self, *args, **options):
        ano_referencia = options.get('ano_referencia')
        course_ids = options.get('course_ids') or None

        if options.get('rollback'):
            result = rollback_initial_matrices(ano_referencia=ano_referencia, course_ids=course_ids)
            self.stdout.write(self.style.WARNING('Rollback de matrizes iniciais executado.'))
            self.stdout.write(f"Matrizes removidas: {result['matrizes_removidas']}")
            self.stdout.write(f"Componentes desvinculados: {result['componentes_desvinculados']}")
            self.stdout.write(f"Cursos limpos: {result['cursos_limpos']}")
            return

        summary = migrate_technical_courses_to_initial_matrizes(ano_referencia=ano_referencia, course_ids=course_ids)
        self.stdout.write(self.style.SUCCESS('Migração de cursos técnicos para matrizes concluída.'))
        self.stdout.write(f'Cursos técnicos encontrados: {summary.technical_courses_found}')
        self.stdout.write(f'Matrizes criadas: {summary.matrizes_created}')
        self.stdout.write(f'Matrizes reaproveitadas: {summary.matrizes_reused}')
        self.stdout.write(f'Componentes vinculados: {summary.componentes_linked}')
        self.stdout.write(f'Cursos atualizados: {summary.cursos_updated}')