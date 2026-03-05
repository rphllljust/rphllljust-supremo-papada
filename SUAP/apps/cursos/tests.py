from django.test import TestCase
from django.urls import reverse

from apps.unidades.models import Unidade
from apps.usuarios.models import Usuario

from .models import Curso


class CursoCrudTests(TestCase):
    def setUp(self):
        self.unidade, _ = Unidade.objects.get_or_create(codigo="sede", defaults={"nome": "Sede"})
        self.secretaria = Usuario.objects.create_user(
            username="sec_cursos",
            cpf="92345678901",
            tipo="SECRETARIA",
            password="x",
        )
        self.client.force_login(self.secretaria)

    def test_create_curso(self):
        response = self.client.post(
            reverse("cursos:cursos_create"),
            {
                "unidade": self.unidade.pk,
                "nome": "Informatica",
                "carga_horaria": 1200,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Curso.objects.filter(nome="Informatica").exists())

    def test_list_cursos(self):
        Curso.objects.create(unidade=self.unidade, nome="Administracao", carga_horaria=1000)

        response = self.client.get(reverse("cursos:cursos_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Administracao")

    def test_delete_curso(self):
        curso = Curso.objects.create(unidade=self.unidade, nome="Quimica", carga_horaria=1400)

        response = self.client.post(reverse("cursos:cursos_delete", args=[curso.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Curso.objects.filter(pk=curso.pk).exists())
