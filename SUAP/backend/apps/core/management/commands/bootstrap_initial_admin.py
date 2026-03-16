import os

from django.core.management.base import BaseCommand

from apps.accounts.services import ensure_initial_admin


class Command(BaseCommand):
    help = "Cria ou recria o administrador inicial do ambiente atual."

    def add_arguments(self, parser):
        parser.add_argument("--cpf", default=os.getenv("INITIAL_ADMIN_CPF", "12345678909"))
        parser.add_argument("--password", default=os.getenv("INITIAL_ADMIN_PASSWORD", "admin"))
        parser.add_argument("--first-name", default=os.getenv("INITIAL_ADMIN_FIRST_NAME", "Administrador"))
        parser.add_argument("--last-name", default=os.getenv("INITIAL_ADMIN_LAST_NAME", "Inicial"))
        parser.add_argument(
            "--no-force-password-change",
            action="store_true",
            help="Nao marca o usuario para troca obrigatoria de senha no primeiro acesso.",
        )

    def handle(self, *args, **options):
        usuario = ensure_initial_admin(
            cpf=options["cpf"],
            password=options["password"],
            first_name=options["first_name"],
            last_name=options["last_name"],
            force_password_change=not options["no_force_password_change"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Administrador inicial pronto: cpf={usuario.cpf} must_change_password={usuario.must_change_password}"
            )
        )