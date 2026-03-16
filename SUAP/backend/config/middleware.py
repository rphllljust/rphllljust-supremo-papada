from django.conf import settings
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.urls import reverse


class BlockDjangoTemplateUIMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.DJANGO_TEMPLATE_UI_ENABLED:
            return self.get_response(request)

        path = request.path or '/'
        allowed_prefixes = tuple(
            prefix
            for prefix in (
                '/api/',
                settings.STATIC_URL,
                settings.MEDIA_URL,
            )
            if prefix
        )

        if any(path.startswith(prefix) for prefix in allowed_prefixes):
            return self.get_response(request)

        return HttpResponseNotFound('Django template UI is disabled.')


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)

        if not user or not getattr(user, "is_authenticated", False):
            return self.get_response(request)

        if not getattr(user, "must_change_password", False):
            return self.get_response(request)

        path = request.path or "/"
        allowed_paths = {
            reverse("accounts:password_change"),
            reverse("accounts:password_change_done"),
            reverse("accounts:logout"),
            reverse("accounts:logout_confirmado"),
        }
        allowed_prefixes = tuple(
            prefix
            for prefix in (
                "/api/",
                "/admin/logout/",
                settings.STATIC_URL,
                settings.MEDIA_URL,
            )
            if prefix
        )

        if path in allowed_paths or any(path.startswith(prefix) for prefix in allowed_prefixes):
            return self.get_response(request)

        return redirect("accounts:password_change")