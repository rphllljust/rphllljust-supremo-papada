from django.core.exceptions import ValidationError
from django.db import models


class Unidade(models.Model):
    # Lista fixa de unidades permitidas (código -> nome)
    FIXED_UNITS = (
        ("sede", "Sede"),
        ("rio_branco", "Rio Branco"),
        ("flora", "Flora"),
    )
    FIXED_CODES = {code for code, _ in FIXED_UNITS}
    CODE_TO_NAME = dict(FIXED_UNITS)

    nome = models.CharField(max_length=200, unique=True)
    codigo = models.CharField(max_length=20, unique=True, choices=FIXED_UNITS)
    endereco = models.CharField(max_length=300, blank=True, default="")
    cidade = models.CharField(max_length=100, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="")

    def clean(self):
        self.codigo = (self.codigo or "").strip().lower()
        expected_name = self.CODE_TO_NAME.get(self.codigo)
        if expected_name is None:
            raise ValidationError({"codigo": "Codigo de unidade invalido."})
        if (self.nome or "").strip() != expected_name:
            raise ValidationError({"nome": f"Nome da unidade deve ser '{expected_name}' para o codigo informado."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.nome
