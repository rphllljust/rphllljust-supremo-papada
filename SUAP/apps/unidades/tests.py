from django.test import TestCase
from django.urls import reverse

from .models import Unidade


class UnidadeCrudTests(TestCase):
    def test_create_unidade(self):
        response = self.client.post(
            reverse("unidades:unidades_create"),
            {"nome": "Campus Natal", "codigo": "NAT"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Unidade.objects.filter(codigo="NAT").exists())

    def test_list_unidades(self):
        Unidade.objects.create(nome="Campus Mossoro", codigo="MOS")

        response = self.client.get(reverse("unidades:unidades_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Campus Mossoro")

    def test_delete_unidade(self):
        unidade = Unidade.objects.create(nome="Campus Caico", codigo="CAC")

        response = self.client.post(reverse("unidades:unidades_delete", args=[unidade.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Unidade.objects.filter(pk=unidade.pk).exists())
