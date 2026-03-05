from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario


class AccountsFlowTests(TestCase):
    def test_login_route_exists(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_signup_route_exists(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_route_exists(self):
        response = self.client.get(reverse("accounts:password_reset"))
        self.assertEqual(response.status_code, 200)

    def test_profile_login_rejects_mismatch(self):
        Usuario.objects.create_user(
            username="acc_sec",
            cpf="92345678916",
            tipo="SECRETARIA",
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "acc_sec", "password": "senha123", "perfil": "ALUNO"},
            follow=True,
        )
        self.assertContains(response, "Perfil selecionado nao corresponde")
