import secrets
import string

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.services import ensure_initial_admin
from apps.usuarios.models import PerfilUsuario, Usuario


PASSWORD_ALPHABET = string.ascii_letters + string.digits
DEFAULT_GENERATED_PASSWORD_LENGTH = 16
MAX_CPF_GENERATION_ATTEMPTS = 1000


def _calculate_cpf_digit(partial_cpf: str) -> str:
    peso_inicial = len(partial_cpf) + 1
    total = sum(int(digito) * (peso_inicial - indice) for indice, digito in enumerate(partial_cpf))
    resto = 11 - (total % 11)
    return "0" if resto >= 10 else str(resto)


def _generate_valid_cpf() -> str:
    while True:
        base = "".join(secrets.choice(string.digits) for _ in range(9))
        if len(set(base)) == 1:
            continue
        d1 = _calculate_cpf_digit(base)
        d2 = _calculate_cpf_digit(base + d1)
        return f"{base}{d1}{d2}"


def _generate_random_password(length: int = DEFAULT_GENERATED_PASSWORD_LENGTH) -> str:
    return "".join(secrets.choice(PASSWORD_ALPHABET) for _ in range(length))


class Command(BaseCommand):
    help = "Cria o administrador inicial do ambiente atual quando ele ainda nao existe."

    def add_arguments(self, parser):
        parser.add_argument("--cpf", default=settings.INITIAL_ADMIN_CPF)
        parser.add_argument("--password", default=settings.INITIAL_ADMIN_PASSWORD)
        parser.add_argument("--first-name", default=settings.INITIAL_ADMIN_FIRST_NAME)
        parser.add_argument("--last-name", default=settings.INITIAL_ADMIN_LAST_NAME)
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recria o administrador inicial mesmo que um usuario com o CPF informado ja exista.",
        )
        parser.add_argument(
            "--generate-random-credentials",
            action="store_true",
            help=(
                "Gera CPF e senha automaticamente para o administrador. "
                "Se ja existir um ADMIN, reutiliza o CPF dele e apenas atualiza a senha."
            ),
        )
        parser.add_argument(
            "--force-password-change",
            action="store_true",
            help="Marca o usuario para troca obrigatoria de senha no primeiro acesso.",
        )

    def _get_unique_random_cpf(self):
        for _ in range(MAX_CPF_GENERATION_ATTEMPTS):
            cpf = _generate_valid_cpf()
            if not Usuario.objects.filter(cpf=cpf).exists():
                return cpf
        raise CommandError("Nao foi possivel gerar um CPF unico para o administrador inicial.")

    def _resolve_random_admin_credentials(self):
        existing_admin = Usuario.objects.filter(tipo=PerfilUsuario.ADMIN).order_by("id").first()
        cpf = existing_admin.cpf if existing_admin else self._get_unique_random_cpf()
        password = _generate_random_password()
        return cpf, password

    def handle(self, *args, **options):
        generated_random_credentials = options["generate_random_credentials"]
        cpf = options["cpf"]
        password = options["password"]
        recreate_existing = options["force"]

        if generated_random_credentials:
            cpf, password = self._resolve_random_admin_credentials()
            recreate_existing = True
            options["force_password_change"] = True

        if not cpf:
            raise CommandError(
                "Informe o CPF do administrador inicial via --cpf ou pela variavel de ambiente INITIAL_ADMIN_CPF."
            )

        usuario, created = ensure_initial_admin(
            cpf=cpf,
            password=password,
            first_name=options["first_name"],
            last_name=options["last_name"],
            force_password_change=options["force_password_change"],
            recreate_existing=recreate_existing,
        )

        if generated_random_credentials:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Credenciais ADMIN geradas automaticamente: cpf={usuario.cpf} senha={password}"
                )
            )

        if not created:
            self.stdout.write(
                self.style.WARNING(
                    f"Administrador inicial ja existe e foi preservado: cpf={usuario.cpf} must_change_password={usuario.must_change_password}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Administrador inicial pronto: cpf={usuario.cpf} must_change_password={usuario.must_change_password}"
            )
        )
