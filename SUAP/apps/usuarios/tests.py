from django.test import TestCase
from django.urls import reverse

from .models import Usuario


class AlunoCrudTests(TestCase):
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
