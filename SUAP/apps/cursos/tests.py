from django.test import TestCase
from django.urls import reverse

from apps.unidades.models import Unidade

from .models import Curso


class CursoCrudTests(TestCase):
    def setUp(self):
        self.unidade = Unidade.objects.create(nome="Campus Norte", codigo="NOR")

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
