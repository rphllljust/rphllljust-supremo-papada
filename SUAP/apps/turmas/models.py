from django.db import models
from django.conf import settings
from apps.cursos.models import Curso


class Turma(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='turmas')
    nome = models.CharField(max_length=100)
    ano_letivo = models.PositiveIntegerField()
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turmas_responsavel',
        limit_choices_to={'tipo': 'PROFESSOR'}
    )

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo}"