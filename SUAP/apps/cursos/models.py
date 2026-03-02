from django.db import models
from apps.unidades.models import Unidade


class Curso(models.Model):
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='cursos')
    nome = models.CharField(max_length=200)
    carga_horaria = models.PositiveIntegerField()

    def __str__(self):
        return self.nome