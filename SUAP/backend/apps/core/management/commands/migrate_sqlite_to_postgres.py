from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


EXCLUDED_MODELS = [
    "admin.logentry",
    "sessions.session",
    "token_blacklist.outstandingtoken",
    "token_blacklist.blacklistedtoken",
]


class Command(BaseCommand):
    help = "Extrai dados de um SQLite e carrega no Postgres configurado como banco default."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default="db.sqlite3",
            help="Caminho do arquivo SQLite de origem.",
        )
        parser.add_argument(
            "--flush-target",
            action="store_true",
            help="Limpa o banco Postgres alvo antes de carregar os dados.",
        )
        parser.add_argument(
            "--skip-migrate",
            action="store_true",
            help="Pula o migrate no banco de destino se ele já estiver preparado.",
        )

    def handle(self, *args, **options):
        source_path = Path(options["source"]).expanduser()
        if not source_path.is_absolute():
            source_path = Path(settings.BASE_DIR) / source_path
        source_path = source_path.resolve()

        if not source_path.exists():
            raise CommandError(f"Arquivo SQLite não encontrado: {source_path}")

        target_config = settings.DATABASES["default"]
        target_engine = target_config.get("ENGINE", "")
        if "postgresql" not in target_engine:
            raise CommandError("O banco default atual não é PostgreSQL. Ajuste DATABASE_ENGINE antes de importar.")

        fixture_path = None
        source_alias = "sqlite_source"
        settings.DATABASES[source_alias] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(source_path),
            "USER": "",
            "PASSWORD": "",
            "HOST": "",
            "PORT": "",
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
            "OPTIONS": {},
            "TIME_ZONE": None,
            "TEST": {
                "CHARSET": None,
                "COLLATION": None,
                "MIGRATE": True,
                "MIRROR": None,
                "NAME": None,
            },
        }

        try:
            if not options["skip_migrate"]:
                self.stdout.write("Aplicando migrações no Postgres de destino...")
                call_command("migrate", interactive=False, database="default", verbosity=options["verbosity"])

            if options["flush_target"]:
                self.stdout.write(self.style.WARNING("Limpando dados atuais do Postgres de destino..."))
                call_command("flush", interactive=False, database="default", verbosity=options["verbosity"])

            with NamedTemporaryFile(suffix=".json", delete=False) as temporary_file:
                fixture_path = Path(temporary_file.name)

            self.stdout.write(f"Gerando fixture temporária a partir de {source_path}...")
            with fixture_path.open("w", encoding="utf-8") as fixture_file:
                call_command(
                    "dumpdata",
                    database=source_alias,
                    format="json",
                    indent=2,
                    exclude=EXCLUDED_MODELS,
                    use_natural_foreign_keys=True,
                    use_natural_primary_keys=True,
                    stdout=fixture_file,
                    verbosity=options["verbosity"],
                )

            self.stdout.write("Carregando dados no Postgres alvo...")
            call_command(
                "loaddata",
                str(fixture_path),
                database="default",
                verbosity=options["verbosity"],
            )
        finally:
            if source_alias in settings.DATABASES:
                settings.DATABASES.pop(source_alias, None)
            if source_alias in connections.databases:
                connections.databases.pop(source_alias, None)
            try:
                del connections[source_alias]
            except Exception:
                pass
            if fixture_path and fixture_path.exists():
                fixture_path.unlink()

        self.stdout.write(self.style.SUCCESS("Carga SQLite -> PostgreSQL concluída."))