from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
import json

from apps.integracao_moodle.api.views import MoodleCategoriesResetAndSyncAPIView


class Command(BaseCommand):
    help = "Test Moodle categories reset/sync endpoint locally by calling the view with admin user"

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username="12345678909")
        except User.DoesNotExist:
            self.stderr.write("Admin user not found (username=12345678909)")
            return

        factory = APIRequestFactory()
        request = factory.post(
            "/api/v1/integracoes/moodle/reset-sync-categorias/",
            {},
            content_type='application/json'
        )

        force_authenticate(request, user=user)

        view = MoodleCategoriesResetAndSyncAPIView.as_view()
        response = view(request)

        try:
            content = json.dumps(response.data, default=str, ensure_ascii=False, indent=2)
        except Exception:
            content = str(response.data)

        self.stdout.write("Status: %s" % getattr(response, "status_code", "?"))
        self.stdout.write(content)
