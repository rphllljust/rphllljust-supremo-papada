from functools import lru_cache

from django.db import connection
from django.db.utils import OperationalError, ProgrammingError


@lru_cache(maxsize=1)
def has_servidor_profile_table():
    try:
        return "usuarios_servidorperfil" in connection.introspection.table_names()
    except (OperationalError, ProgrammingError):
        return False


def get_matricula_servidor_safe(user):
    if not has_servidor_profile_table():
        return ""

    try:
        perfil = getattr(user, "perfil_servidor", None)
        return getattr(perfil, "matricula_servidor", "") or ""
    except (OperationalError, ProgrammingError):
        return ""