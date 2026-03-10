from functools import wraps

from django.contrib.auth.decorators import login_required

from apps.usuarios.models import PerfilUsuario

from .policies import can_access_module, can_export_to_ava, has_any_profile
from .views import render_access_denied


def role_required(*profiles):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if has_any_profile(request.user, *profiles):
                return view_func(request, *args, **kwargs)

            if getattr(request.user, "tipo", None) == PerfilUsuario.ALUNO:
                return render_access_denied(request, "Perfil Aluno nao possui acesso ao sistema SUAP.")

            return render_access_denied(request, "Seu perfil nao possui permissao para esta funcionalidade.")

        return _wrapped

    return decorator


def module_access_required(module_name: str):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if can_access_module(request.user, module_name):
                return view_func(request, *args, **kwargs)
            return render_access_denied(request, f"Seu perfil nao possui acesso ao modulo {module_name}.")

        return _wrapped

    return decorator


def export_to_ava_required(view_func):
    @login_required
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if can_export_to_ava(request.user):
            return view_func(request, *args, **kwargs)
        return render_access_denied(request, "Seu perfil nao possui permissao para exportar dados para o AVA.")

    return _wrapped
