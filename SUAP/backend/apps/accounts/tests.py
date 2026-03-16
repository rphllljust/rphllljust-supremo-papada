from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.usuarios.models import PerfilUsuario, Pessoa, Usuario


def gerar_cpf(seed: int) -> str:
    base = f"{seed:09d}"[-9:]

    def dv(parcial: str) -> str:
        peso_inicial = len(parcial) + 1
        total = sum(int(digito) * (peso_inicial - indice) for indice, digito in enumerate(parcial))
        resto = 11 - (total % 11)
        return "0" if resto >= 10 else str(resto)

    d1 = dv(base)
    d2 = dv(base + d1)
    return f"{base}{d1}{d2}"


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

    def test_login_form_does_not_offer_aluno_profile(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '<option value="ALUNO">')

    def test_profile_login_rejects_mismatch(self):
        cpf = gerar_cpf(123456780)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha123", "perfil": PerfilUsuario.COORDENACAO},
            follow=True,
        )
        self.assertContains(response, "nao corresponde ao perfil da sua conta")

    def test_profile_login_blocks_aluno_even_when_professor_selected(self):
        cpf = gerar_cpf(123456781)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.ALUNO,
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha123", "perfil": PerfilUsuario.PROFESSOR},
            follow=True,
        )
        self.assertContains(response, "Perfil Aluno nao possui acesso")

    def test_login_informs_when_account_not_found(self):
        cpf = gerar_cpf(987654321)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha123", "perfil": PerfilUsuario.PROFESSOR},
            follow=True,
        )
        self.assertContains(response, "Conta nao encontrada")

    def test_login_informs_when_password_is_wrong(self):
        cpf = gerar_cpf(123456782)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.PROFESSOR,
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha_errada", "perfil": PerfilUsuario.PROFESSOR},
            follow=True,
        )
        self.assertContains(response, "Senha incorreta")

    def test_signup_redirects_to_login_with_confirmation_message(self):
        cpf = gerar_cpf(123456783)
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Novo",
                "last_name": "Usuario",
                "email": "novo@example.com",
                "cpf": cpf,
                "perfil": PerfilUsuario.PROFESSOR,
                "password1": "senha12345",
                "password2": "senha12345",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Conta criada com sucesso")
        self.assertContains(response, "Agora faca login")
        self.assertTrue(Usuario.objects.filter(username=cpf, tipo=PerfilUsuario.PROFESSOR).exists())

    def test_login_redirects_to_password_change_when_first_access_is_required(self):
        cpf = gerar_cpf(123456798)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.ADMIN,
            password="senha12345",
            must_change_password=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha12345", "perfil": PerfilUsuario.ADMIN},
        )

        self.assertRedirects(response, reverse("accounts:password_change"))

    def test_signup_rejects_weak_password(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Novo",
                "last_name": "Usuario",
                "email": "fraca@example.com",
                "cpf": gerar_cpf(123456799),
                "perfil": PerfilUsuario.PROFESSOR,
                "password1": "12345678",
                "password2": "12345678",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "muito comum")

    def test_signup_rejects_invalid_cpf(self):
        cpf_valido = gerar_cpf(123456788)
        ultimo = "0" if cpf_valido[-1] != "0" else "1"
        cpf_invalido = f"{cpf_valido[:-1]}{ultimo}"
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Novo",
                "last_name": "Usuario",
                "email": "novo2@example.com",
                "cpf": cpf_invalido,
                "perfil": PerfilUsuario.PROFESSOR,
                "password1": "senha12345",
                "password2": "senha12345",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CPF invalido")

    def test_signup_normalizes_email_and_blocks_case_insensitive_duplicate(self):
        cpf = gerar_cpf(123456784)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.PROFESSOR,
            email="existente@example.com",
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Outro",
                "last_name": "Cadastro",
                "email": "Existente@Example.com",
                "cpf": gerar_cpf(123456785),
                "perfil": PerfilUsuario.PROFESSOR,
                "password1": "senha12345",
                "password2": "senha12345",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ja existe cadastro com este e-mail")

    def test_signup_rejects_case_insensitive_duplicate_email_from_pessoa(self):
        Pessoa.objects.create(nome_completo="Pessoa Existente", cpf=gerar_cpf(123456786), email="pessoa@example.com")
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "Nova",
                "last_name": "Pessoa",
                "email": "Pessoa@Example.com",
                "cpf": gerar_cpf(123456787),
                "perfil": PerfilUsuario.PROFESSOR,
                "password1": "senha12345",
                "password2": "senha12345",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ja existe cadastro com este e-mail")

    def test_signup_shows_required_field_feedback(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "first_name": "",
                "last_name": "",
                "email": "",
                "cpf": "",
                "perfil": "",
                "password1": "",
                "password2": "",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revise os campos obrigatorios destacados no formulario")


class ApiJwtAuthenticationTests(TestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.cpf_secretaria = gerar_cpf(123456789)
        self.secretaria = Usuario.objects.create_user(
            username=self.cpf_secretaria,
            cpf=self.cpf_secretaria,
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
            first_name="Ana",
            last_name="Secretaria",
        )

    def test_token_obtain_pair_returns_tokens_and_user_payload(self):
        response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["cpf"], self.cpf_secretaria)
        self.assertEqual(response.data["user"]["perfil"], PerfilUsuario.SECRETARIA)
        self.assertIn("access_context", response.data["user"])
        self.assertIn("claims_version", response.data["user"]["access_context"])
        self.assertEqual(response.data["user"]["access_context"]["claims_version"], 1)
        self.assertIn("web:matriculas:view", response.data["user"]["access_context"]["permission_claims"])

    def test_access_token_contains_computed_access_claims(self):
        response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )

        token = AccessToken(response.data["access"])

        self.assertEqual(token["perfil"], PerfilUsuario.SECRETARIA)
        self.assertIn("claims_version", token)
        self.assertEqual(token["claims_version"], 1)
        self.assertIn("module_access", token)
        self.assertIn("permission_claims", token)
        self.assertIn("ava_export_modules", token)
        self.assertIn("usuarios", token["module_access"]["api"])
        self.assertIn("api:usuarios:view", token["permission_claims"])

    def test_token_obtain_pair_rejects_profile_mismatch(self):
        response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.COORDENACAO,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.data)
        self.assertIn("nao corresponde ao perfil", response.data["detail"][0])

    def test_token_obtain_pair_blocks_aluno(self):
        cpf_aluno = gerar_cpf(123456790)
        Usuario.objects.create_user(
            username=cpf_aluno,
            cpf=cpf_aluno,
            tipo=PerfilUsuario.ALUNO,
            password="senha123",
        )

        response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": cpf_aluno,
                "password": "senha123",
                "perfil": PerfilUsuario.PROFESSOR,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Perfil Aluno nao possui acesso", response.data["detail"][0])

    def test_refresh_endpoint_returns_new_access_token(self):
        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )

        refresh_response = self.api_client.post(
            reverse("api_v1_auth:token_refresh"),
            {"refresh": token_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)
        self.assertIn("refresh", refresh_response.data)

    def test_logout_blacklists_refresh_token(self):
        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )

        access_token = token_response.data["access"]
        refresh_token = token_response.data["refresh"]

        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_response = self.api_client.post(
            reverse("api_v1_auth:logout"),
            {"refresh": refresh_token},
            format="json",
        )

        self.assertEqual(logout_response.status_code, 200)

        refresh_response = self.api_client.post(
            reverse("api_v1_auth:token_refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_bearer_token_grants_access_to_protected_api(self):
        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )
        access_token = token_response.data["access"]

        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.api_client.get(reverse("api_v1_usuarios:list"))

        self.assertEqual(response.status_code, 200)

    def test_me_endpoint_returns_authenticated_user(self):
        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )
        access_token = token_response.data["access"]

        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.api_client.get(reverse("api_v1_auth:me"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cpf"], self.cpf_secretaria)
        self.assertEqual(response.data["perfil"], PerfilUsuario.SECRETARIA)
        self.assertIn("access_context", response.data)
        self.assertIn("api:usuarios:view", response.data["access_context"]["permission_claims"])

    def test_token_and_me_include_first_access_flag(self):
        self.secretaria.must_change_password = True
        self.secretaria.save(update_fields=["must_change_password"])

        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )

        self.assertEqual(token_response.status_code, 200)
        self.assertTrue(token_response.data["user"]["must_change_password"])

        access_token = token_response.data["access"]
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_response = self.api_client.get(reverse("api_v1_auth:me"))

        self.assertEqual(me_response.status_code, 200)
        self.assertTrue(me_response.data["must_change_password"])

    def test_change_password_clears_first_access_flag(self):
        self.secretaria.must_change_password = True
        self.secretaria.save(update_fields=["must_change_password"])

        token_response = self.api_client.post(
            reverse("api_v1_auth:token_obtain_pair"),
            {
                "cpf": self.cpf_secretaria,
                "password": "senha123",
                "perfil": PerfilUsuario.SECRETARIA,
            },
            format="json",
        )
        access_token = token_response.data["access"]

        self.api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.api_client.post(
            reverse("api_v1_auth:change-password"),
            {
                "current_password": "senha123",
                "new_password": "SenhaSegura123!",
                "new_password_confirm": "SenhaSegura123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["must_change_password"])
        self.secretaria.refresh_from_db()
        self.assertFalse(self.secretaria.must_change_password)
