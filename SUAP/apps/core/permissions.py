from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def role_required(*tipos_permitidos):
    """Simple role gate by Usuario.tipo with implicit ADMIN/superuser access."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if getattr(user, "is_superuser", False):
                return view_func(request, *args, **kwargs)

            tipo = getattr(user, "tipo", None)
            if tipo == "ADMIN" or tipo in tipos_permitidos:
                return view_func(request, *args, **kwargs)

            return render(
                request,
                "base/acesso_negado.html",
                {"mensagem": "Seu perfil não possui permissão para esta funcionalidade."},
                status=403,
            )

        return _wrapped

    return decorator

