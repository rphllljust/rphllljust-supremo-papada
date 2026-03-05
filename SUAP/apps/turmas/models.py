from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.cursos.models import Curso


class Turma(models.Model):
    STATUS_CHOICES = (
        ('PLANEJADA', 'Planejada'),
        ('ATIVA', 'Ativa'),
        ('ENCERRADA', 'Encerrada'),
        ('CANCELADA', 'Cancelada'),
    )

    TRANSICOES_STATUS = {
        'PLANEJADA': {'ATIVA', 'CANCELADA'},
        'ATIVA': {'ENCERRADA', 'CANCELADA'},
        'ENCERRADA': set(),
        'CANCELADA': set(),
    }

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='turmas')
    nome = models.CharField(max_length=100)
    ano_letivo = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PLANEJADA')
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turmas_responsavel',
        limit_choices_to={'tipo': 'PROFESSOR'}
    )

    def clean(self):
        if not self.pk:
            return

        original = Turma.objects.filter(pk=self.pk).values_list('status', flat=True).first()
        if not original or original == self.status:
            return

        permitidos = self.TRANSICOES_STATUS.get(original, set())
        if self.status not in permitidos:
            raise ValidationError({'status': f'Transicao de status invalida: {original} -> {self.status}.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo}"