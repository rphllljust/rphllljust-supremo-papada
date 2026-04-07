from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from apps.access.views import render_access_denied
from apps.usuarios.models import PerfilUsuario


def _frontend_dashboard_url():
    base_url = str(getattr(settings, "CERTIFICADOS_VALIDATION_FRONTEND_BASE_URL", "") or "").rstrip("/")
    if base_url:
        return f"{base_url}/dashboard"
    return "/dashboard"


@login_required
def index(request):
    if not request.user.is_active:
        logout(request)
        return redirect("accounts:login")

    perfil = getattr(request.user, "tipo", "")
    perfis_validos = {
        PerfilUsuario.SECRETARIA,
        PerfilUsuario.COORDENACAO,
        PerfilUsuario.PROFESSOR,
        PerfilUsuario.ADMIN,
    }
    if perfil == PerfilUsuario.ALUNO:
        return render_access_denied(request, "Perfil Aluno nao possui acesso ao sistema SUAP.")
    if perfil not in perfis_validos:
        return render_access_denied(request, "Seu perfil ainda nao esta habilitado para o painel.")

    return redirect(_frontend_dashboard_url())
