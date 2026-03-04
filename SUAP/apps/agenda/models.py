from django.db import models

from apps.turmas.models import Turma


class EventoAgenda(models.Model):
    titulo = models.CharField(max_length=150)
    descricao = models.TextField(blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="eventos")
    inicio = models.DateTimeField()
    fim = models.DateTimeField()

    class Meta:
        ordering = ["inicio"]

    def __str__(self):
        return self.titulo

