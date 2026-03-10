from django.db import models

from apps.matriculas.models import Matricula


class Frequencia(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name="frequencias")
    data = models.DateField()
    presente = models.BooleanField(default=True)
    observacao = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-data"]
        unique_together = ("matricula", "data")

    def __str__(self):
        return f"{self.matricula} - {self.data}"

