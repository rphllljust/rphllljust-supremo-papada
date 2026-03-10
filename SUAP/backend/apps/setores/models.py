from django.core.exceptions import ValidationError
from django.db import models


class Setor(models.Model):
    nome = models.CharField(max_length=200, unique=True)
    sigla = models.CharField(max_length=30, blank=True, default="")
    codigo = models.CharField(max_length=30, unique=True)
    setor_superior = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subsetores",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "codigo"]
        verbose_name = "Setor"
        verbose_name_plural = "Setores"

    def clean(self):
        self.nome = (self.nome or "").strip()
        self.sigla = (self.sigla or "").strip().upper()
        self.codigo = (self.codigo or "").strip().upper()

        if not self.nome:
            raise ValidationError({"nome": "Informe o nome do setor."})

        if not self.codigo:
            raise ValidationError({"codigo": "Informe o codigo do setor."})

        if self.pk and self.setor_superior and self.setor_superior.pk == self.pk:
            raise ValidationError({"setor_superior": "Um setor nao pode ser superior de si mesmo."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"