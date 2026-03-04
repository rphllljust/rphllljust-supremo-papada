from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.cursos.models import Curso
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
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='matriculas')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='matriculas')
    data_matricula = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ATIVA')

    def clean(self):
        if self.turma_id and not self.curso_id:
            self.curso = self.turma.curso

        if self.curso_id and self.turma_id and self.turma.curso_id != self.curso_id:
            raise ValidationError({'turma': 'A turma selecionada nao pertence ao curso informado.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.aluno} - {self.curso} / {self.turma}"
