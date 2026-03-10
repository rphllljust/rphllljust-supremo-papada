from django.conf import settings
from django.http import HttpResponseNotFound


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