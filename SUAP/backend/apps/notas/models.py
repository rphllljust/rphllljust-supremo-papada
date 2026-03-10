from django.db import models

from apps.matriculas.models import Matricula


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name="notas")
    descricao = models.CharField(max_length=120)
    valor = models.DecimalField(max_digits=5, decimal_places=2)
    peso = models.DecimalField(max_digits=4, decimal_places=2, default=1)
    data_lancamento = models.DateField()

    class Meta:
        ordering = ["-data_lancamento", "descricao"]

    def __str__(self):
        return f"{self.matricula} - {self.descricao}"

