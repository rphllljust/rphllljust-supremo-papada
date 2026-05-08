from django.db import models
from django.core.exceptions import ValidationError

from apps.matriculas.models import Matricula
from apps.cursos.models import ComponenteCurricular


class Nota(models.Model):
    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name="notas")
    descricao = models.CharField(max_length=120, verbose_name='Descricao/Avaliacao')
    valor = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='Valor')
    peso = models.DecimalField(max_digits=4, decimal_places=2, default=1, verbose_name='Peso')
    componente_curricular = models.ForeignKey(
        ComponenteCurricular,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notas',
        verbose_name='Componente Curricular',
    )
    data_lancamento = models.DateField(verbose_name='Data de Lancamento')

    class Meta:
        ordering = ["-data_lancamento", "descricao"]
        verbose_name = 'Nota'
        verbose_name_plural = 'Notas'

    def clean(self):
        if self.valor is not None and (self.valor < 0 or self.valor > 10):
            raise ValidationError({'valor': 'A nota deve estar entre 0 e 10.'})
        if self.peso is not None and self.peso <= 0:
            raise ValidationError({'peso': 'O peso deve ser maior que zero.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        comp = f' [{self.componente_curricular.nome}]' if self.componente_curricular else ''
        return f"{self.matricula}{comp} - {self.descricao}: {self.valor}"

