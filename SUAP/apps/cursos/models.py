from django.db import models
from apps.unidades.models import Unidade


class Curso(models.Model):
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='cursos')
    nome = models.CharField(max_length=200)
    carga_horaria = models.PositiveIntegerField()

    def __str__(self):
        return self.nome

class CalendarioLetivo(models.Model):
    """Calendário Letivo por ano/curso  Entidade Acadêmica do Class Diagram."""

    STATUS_CHOICES = (
        ('PLANEJADO', 'Planejado'),
        ('VIGENTE',   'Vigente'),
        ('ENCERRADO', 'Encerrado'),
    )

    ano_letivo   = models.CharField(max_length=9, verbose_name='Ano Letivo')
    curso        = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='calendarios',
        verbose_name='Curso',
    )
    data_inicio  = models.DateField(verbose_name='Data de Início')
    data_fim     = models.DateField(verbose_name='Data de Fim')
    dias_letivos = models.PositiveIntegerField(default=200, verbose_name='Dias Letivos')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PLANEJADO', verbose_name='Status')
    descricao    = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Calendário Letivo'
        verbose_name_plural = 'Calendários Letivos'
        unique_together = ('ano_letivo', 'curso')
        ordering = ['-ano_letivo', 'curso']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValidationError({'data_fim': 'A data de fim deve ser posterior à data de início.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Calendário {self.ano_letivo}  {self.curso.nome} [{self.get_status_display()}]'
