from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario, Usuario


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


class AlunoCrudTests(TestCase):
    def setUp(self):
        cpf_secretaria = gerar_cpf(223456780)
        self.secretaria = Usuario.objects.create_user(
            username="sec_usuarios",
            cpf=cpf_secretaria,
            tipo=PerfilUsuario.SECRETARIA,
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_aluno_sets_tipo_aluno(self):
        cpf_aluno = gerar_cpf(123456780)
        response = self.client.post(
            reverse("usuarios:alunos_create"),
            {
                "first_name": "Ana",
                "last_name": "Silva",
                "email": "ana@example.com",
                "cpf": cpf_aluno,
                "is_active": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        aluno = Usuario.objects.get(cpf=cpf_aluno)
        self.assertEqual(aluno.tipo, PerfilUsuario.ALUNO)
        self.assertEqual(aluno.username, cpf_aluno)

    def test_create_form_does_not_show_username_field(self):
        response = self.client.get(reverse("usuarios:alunos_create"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="username"')

    def test_list_shows_only_alunos(self):
        cpf_aluno = gerar_cpf(123456781)
        Usuario.objects.create_user(
            username=cpf_aluno,
            cpf=cpf_aluno,
            tipo=PerfilUsuario.ALUNO,
            password="x",
        )
        Usuario.objects.create_user(
            username="prof1",
            cpf=gerar_cpf(123456782),
            tipo=PerfilUsuario.PROFESSOR,
            password="x",
        )

        response = self.client.get(reverse("usuarios:alunos_list"))

        self.assertContains(response, cpf_aluno)
        self.assertNotContains(response, "prof1")

    def test_delete_aluno(self):
        cpf_aluno = gerar_cpf(123456783)
        aluno = Usuario.objects.create_user(
            username=cpf_aluno,
            cpf=cpf_aluno,
            tipo=PerfilUsuario.ALUNO,
            password="x",
        )

        response = self.client.post(reverse("usuarios:alunos_delete", args=[aluno.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Usuario.objects.filter(pk=aluno.pk).exists())


class ProfessorCrudTests(TestCase):
    def setUp(self):
        self.secretaria = Usuario.objects.create_user(
            username="sec_usuarios_2",
            cpf=gerar_cpf(223456781),
            tipo=PerfilUsuario.SECRETARIA,
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_professor_sets_tipo_professor(self):
        cpf_professor = gerar_cpf(123456784)
        response = self.client.post(
            reverse("usuarios:professores_create"),
            {
                "first_name": "Joao",
                "last_name": "Pereira",
                "email": "joao@example.com",
                "cpf": cpf_professor,
                "is_active": "on",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        professor = Usuario.objects.get(cpf=cpf_professor)
        self.assertEqual(professor.tipo, PerfilUsuario.PROFESSOR)

    def test_list_shows_only_professores(self):
        Usuario.objects.create_user(
            username="prof3",
            cpf=gerar_cpf(123456785),
            tipo=PerfilUsuario.PROFESSOR,
            password="x",
        )
        cpf_aluno = gerar_cpf(123456786)
        Usuario.objects.create_user(
            username=cpf_aluno,
            cpf=cpf_aluno,
            tipo=PerfilUsuario.ALUNO,
            password="x",
        )

        response = self.client.get(reverse("usuarios:professores_list"))

        self.assertContains(response, "prof3")
        self.assertNotContains(response, cpf_aluno)

    def test_delete_professor(self):
        professor = Usuario.objects.create_user(
            username="prof4",
            cpf=gerar_cpf(123456787),
            tipo=PerfilUsuario.PROFESSOR,
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
        cpf = gerar_cpf(323456780)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha123", "perfil": PerfilUsuario.SECRETARIA},
        )
        self.assertRedirects(response, reverse("matriculas:matriculas_list"))

    def test_coordenacao_redirect_after_login(self):
        cpf = gerar_cpf(323456781)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.COORDENACAO,
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login"),
            {"username": cpf, "password": "senha123", "perfil": PerfilUsuario.COORDENACAO},
        )
        self.assertRedirects(response, reverse("dashboard:index"))

    def test_login_respects_next_parameter(self):
        cpf = gerar_cpf(323456782)
        Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.SECRETARIA,
            password="senha123",
        )
        response = self.client.post(
            reverse("accounts:login") + "?next=/turmas/",
            {"username": cpf, "password": "senha123", "perfil": PerfilUsuario.SECRETARIA},
        )
        self.assertRedirects(response, "/turmas/")

    def test_login_rejects_wrong_profile_selection(self):
        cpf = gerar_cpf(323456783)
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
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "nao corresponde ao perfil da sua conta")

    def test_login_blocks_aluno_profile(self):
        cpf = gerar_cpf(323456784)
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
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Perfil Aluno nao possui acesso")

    def test_logout_requires_post_and_shows_confirmation_page(self):
        cpf = gerar_cpf(323456785)
        usuario = Usuario.objects.create_user(
            username=cpf,
            cpf=cpf,
            tipo=PerfilUsuario.SECRETARIA,
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
        cpf = gerar_cpf(323456786)
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
        self.assertTrue(Usuario.objects.filter(username=cpf, tipo=PerfilUsuario.PROFESSOR).exists())
