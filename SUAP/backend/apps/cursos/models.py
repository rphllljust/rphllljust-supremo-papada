from django.db import models
from apps.unidades.models import Unidade


class AreaCurso(models.Model):
    descricao = models.CharField(max_length=200, unique=True, verbose_name='Descrição')
    codigo_cine = models.CharField(max_length=20, blank=True, default='', verbose_name='Código CINE')
    codigo_area_detalhada = models.CharField(max_length=20, blank=True, default='', verbose_name='Código da Área Detalhada')
    codigo_area_especifica = models.CharField(max_length=20, blank=True, default='', verbose_name='Código da Área Específica')
    codigo_area_geral = models.CharField(max_length=20, blank=True, default='', verbose_name='Código da Área Geral')
    cine = models.CharField(max_length=200, blank=True, default='', verbose_name='CINE')
    area_detalhada = models.CharField(max_length=200, blank=True, default='', verbose_name='Área Detalhada')
    area_especifica = models.CharField(max_length=200, blank=True, default='', verbose_name='Área Específica')
    area_geral = models.CharField(max_length=200, blank=True, default='', verbose_name='Área Geral')

    class Meta:
        verbose_name = 'Área de Curso'
        verbose_name_plural = 'Áreas de Cursos'
        ordering = ['descricao']

    def __str__(self):
        titulo = self.cine or self.area_detalhada or self.descricao
        return f'{self.codigo_cine} - {titulo}'.strip(' -')


class Curso(models.Model):
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='cursos')
    area_curso = models.ForeignKey('AreaCurso', on_delete=models.SET_NULL, related_name='cursos', null=True, blank=True, verbose_name='Área do Curso')
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=16, blank=True, default='', verbose_name='Sigla')
    eixo_tecnologico = models.CharField(max_length=200, blank=True, default='', verbose_name='Eixo Tecnológico')
    carga_horaria = models.PositiveIntegerField()

    def __str__(self):
        return self.nome


class ComponenteCurricular(models.Model):
    """Componente da matriz curricular de um curso."""

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='componentes', verbose_name='Curso')
    nome = models.CharField(max_length=200, verbose_name='Nome')
    abreviatura = models.CharField(max_length=30, blank=True, default='', verbose_name='Abreviatura')
    sigla = models.CharField(max_length=30, blank=True, default='', verbose_name='Sigla')
    descricao_diploma_historico = models.CharField(max_length=200, blank=True, default='', verbose_name='Descrição no Diploma e Histórico')
    diretoria = models.CharField(max_length=120, blank=True, default='', verbose_name='Diretoria')
    ativo = models.BooleanField(default=True, verbose_name='Está ativo')
    tipo_componente = models.CharField(max_length=80, blank=True, default='', verbose_name='Tipo do Componente')
    nivel_ensino = models.CharField(max_length=80, blank=True, default='', verbose_name='Nível de ensino')
    grupo_atuacao = models.CharField(max_length=120, blank=True, default='', verbose_name='Grupo de Atuação')
    carga_horaria = models.PositiveIntegerField(default=0, verbose_name='Carga Horária (h)')
    hora_aula = models.PositiveIntegerField(default=0, verbose_name='Hora/aula')
    qtd_creditos = models.PositiveIntegerField(default=0, verbose_name='Qtd. de créditos')
    sigla_qacademico = models.CharField(max_length=50, blank=True, default='', verbose_name='Sigla do Q-Acadêmico')
    observacao = models.TextField(blank=True, default='', verbose_name='Observação')
    ordem = models.PositiveIntegerField(default=1, verbose_name='Ordem')

    class Meta:
        verbose_name = 'Componente Curricular'
        verbose_name_plural = 'Componentes Curriculares'
        ordering = ['ordem', 'nome']
        unique_together = ('curso', 'nome')

    def __str__(self):
        return f'{self.nome} ({self.curso.nome})'

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
