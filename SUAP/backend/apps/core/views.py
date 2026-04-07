"""Core legacy entrypoints."""

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect


def _frontend_dashboard_url():
    base_url = str(getattr(settings, "CERTIFICADOS_VALIDATION_FRONTEND_BASE_URL", "") or "").rstrip("/")
    if base_url:
        return f"{base_url}/dashboard"
    return "/dashboard"


def dashboard(request):
    return redirect(_frontend_dashboard_url())


def ensino_item_indisponivel(request, item_slug):
    raise Http404(f"A funcionalidade de ensino '{item_slug}' ainda nao foi implementada.")
