from django.test import TestCase
from django.urls import reverse

from .models import Unidade


class UnidadeCrudTests(TestCase):
    def test_seed_fixed_unidades(self):
        unidades = list(Unidade.objects.order_by("nome").values_list("codigo", "nome"))

        self.assertEqual(
            unidades,
            [("flora", "Flora"), ("rio_branco", "Rio Branco"), ("sede", "Sede")],
        )

    def test_create_unidade_is_blocked(self):
        total_before = Unidade.objects.count()

        response = self.client.post(
            reverse("unidades:unidades_create"),
            {"nome": "Campus Natal", "codigo": "NAT"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Unidade.objects.count(), total_before)
        self.assertContains(response, "As unidades sao fixas")

    def test_delete_unidade_is_blocked(self):
        unidade = Unidade.objects.get(codigo="sede")

        response = self.client.post(reverse("unidades:unidades_delete", args=[unidade.pk]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Unidade.objects.filter(pk=unidade.pk).exists())
        self.assertContains(response, "As unidades sao fixas")
