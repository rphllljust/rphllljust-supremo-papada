from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class AlunoCrudTests(TestCase):
    def setUp(self):
        self.secretaria = Usuario.objects.create_user(
            username="sec_usuarios",
            cpf="92345678904",
            tipo="SECRETARIA",
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_aluno_sets_tipo_aluno(self):
        response = self.client.post(
            reverse("usuarios:alunos_create"),
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "email": "ana@example.com",
                "cpf": "12345678901",
                "is_active": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        aluno = Usuario.objects.get(cpf="12345678901")
        self.assertEqual(aluno.tipo, "ALUNO")
        self.assertEqual(aluno.username, "12345678901")

    def test_create_form_does_not_show_username_field(self):
        response = self.client.get(reverse("usuarios:alunos_create"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="username"')

    def test_list_shows_only_alunos(self):
        Usuario.objects.create_user(
            username="aluno2",
            cpf="12345678902",
            tipo="ALUNO",
            password="x",
        )
        Usuario.objects.create_user(
            username="prof1",
            cpf="12345678903",
            tipo="PROFESSOR",
            password="x",
        )

        response = self.client.get(reverse("usuarios:alunos_list"))

        self.assertContains(response, "aluno2")
        self.assertNotContains(response, "prof1")

    def test_delete_aluno(self):
        aluno = Usuario.objects.create_user(
            username="aluno3",
            cpf="12345678904",
            tipo="ALUNO",
            password="x",
        )

        response = self.client.post(reverse("usuarios:alunos_delete", args=[aluno.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Usuario.objects.filter(pk=aluno.pk).exists())


class ProfessorCrudTests(TestCase):
    def setUp(self):
        self.secretaria = Usuario.objects.create_user(
            username="sec_usuarios_2",
            cpf="92345678905",
            tipo="SECRETARIA",
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_professor_sets_tipo_professor(self):
        response = self.client.post(
            reverse("usuarios:professores_create"),
            {
                "username": "prof2",
                "first_name": "Joao",
                "last_name": "Pereira",
                "email": "joao@example.com",
                "cpf": "12345678905",
                "is_active": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        professor = Usuario.objects.get(username="prof2")
        self.assertEqual(professor.tipo, "PROFESSOR")

    def test_list_shows_only_professores(self):
        Usuario.objects.create_user(
            username="prof3",
            cpf="12345678906",
            tipo="PROFESSOR",
            password="x",
        )
        Usuario.objects.create_user(
            username="aluno4",
            cpf="12345678907",
            tipo="ALUNO",
            password="x",
        )

        response = self.client.get(reverse("usuarios:professores_list"))

        self.assertContains(response, "prof3")
        self.assertNotContains(response, "aluno4")

    def test_delete_professor(self):
        professor = Usuario.objects.create_user(
            username="prof4",
            cpf="12345678908",
            tipo="PROFESSOR",
            password="x",
        )

        response = self.client.post(reverse("usuarios:professores_delete", args=[professor.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Usuario.objects.filter(pk=professor.pk).exists())


class AuthFlowTests(TestCase):
    def test_login_page_loads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acesso ao SUAP Escolar")

    def test_login_page_shows_session_expired_warning_when_next_exists(self):
        response = self.client.get(reverse("accounts:login") + "?next=/matriculas/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sua sessao expirou")

    def test_secretaria_redirect_after_login(self):
        Usuario.objects.create_user(
            username="sec_login",
            cpf="92345678909",
            tipo="SECRETARIA",
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "sec_login", "password": "senha123", "perfil": "SECRETARIA"},
        )
        self.assertRedirects(response, reverse("matriculas:matriculas_list"))

    def test_coordenacao_redirect_after_login(self):
        Usuario.objects.create_user(
            username="coord_login",
            cpf="92345678910",
            tipo="COORDENACAO",
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "coord_login", "password": "senha123", "perfil": "COORDENACAO"},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_login_respects_next_parameter(self):
        Usuario.objects.create_user(
            username="sec_next",
            cpf="92345678912",
            tipo="SECRETARIA",
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login") + "?next=/turmas/",
            {"username": "sec_next", "password": "senha123", "perfil": "SECRETARIA"},
        )
        self.assertRedirects(response, "/turmas/")

    def test_login_rejects_wrong_profile_selection(self):
        Usuario.objects.create_user(
            username="sec_mismatch",
            cpf="92345678913",
            tipo="SECRETARIA",
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "sec_mismatch", "password": "senha123", "perfil": "COORDENACAO"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Perfil selecionado nao corresponde")

    def test_logout_requires_post_and_shows_confirmation_page(self):
        usuario = Usuario.objects.create_user(
            username="sec_logout",
            cpf="92345678914",
            tipo="SECRETARIA",
            password="senha123",
        )
        self.client.force_login(usuario)

        get_response = self.client.get(reverse("accounts:logout"), follow=True)
        self.assertContains(get_response, "Use o botao Sair para encerrar a sessao")

        post_response = self.client.post(reverse("accounts:logout"), follow=True)
        self.assertEqual(post_response.status_code, 200)
        self.assertContains(post_response, "Logout realizado")
        self.assertContains(post_response, "Sessao encerrada com sucesso")

    def test_public_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "novo_usuario",
                "first_name": "Novo",
                "last_name": "Usuario",
                "email": "novo@example.com",
                "cpf": "92345678915",
                "perfil": "ALUNO",
                "password1": "senha12345",
                "password2": "senha12345",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Usuario.objects.filter(username="novo_usuario", tipo="ALUNO").exists())
