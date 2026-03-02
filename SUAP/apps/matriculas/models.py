from django.db import models
from django.conf import settings
from apps.turmas.models import Turma


class Matricula(models.Model):
    STATUS_CHOICES = (
        ('ATIVA', 'Ativa'),
        ('TRANCADA', 'Trancada'),
        ('CANCELADA', 'Cancelada'),
        ('CONCLUIDA', 'Concluída'),
    )

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matriculas',
        limit_choices_to={'tipo': 'ALUNO'}
    )
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='matriculas')
    data_matricula = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVA')

    def __str__(self):
        return f"{self.aluno} - {self.turma}"