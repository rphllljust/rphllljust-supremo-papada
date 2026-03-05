from django.test import TestCase
from django.urls import reverse

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
