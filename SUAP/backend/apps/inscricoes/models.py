"""
Captação / Inscrição / Seleção / Convocação
Fluxo: PublicacaoInscricao → Inscricao → ProcessoSeletivo → Candidato → Recurso
"""

from django.conf import settings
from django.db import models

from apps.cursos.models import Curso


class PublicacaoInscricao(models.Model):
    """Edital / publicação de abertura de inscrições para um curso."""

    STATUS_CHOICES = (
        ('RASCUNHO',   'Rascunho'),
        ('PUBLICADO',  'Publicado'),
        ('ENCERRADO',  'Encerrado'),
    )

    curso             = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='publicacoes_inscricao', verbose_name='Curso')
    titulo            = models.CharField(max_length=255, verbose_name='Título do Edital')
    descricao         = models.TextField(blank=True, verbose_name='Descrição / Requisitos')
    vagas             = models.PositiveIntegerField(default=0, verbose_name='Nº de Vagas')
    data_inicio       = models.DateField(verbose_name='Início das Inscrições')
    data_fim          = models.DateField(verbose_name='Fim das Inscrições')
    status            = models.CharField(max_length=15, choices=STATUS_CHOICES, default='RASCUNHO', verbose_name='Status')
    publicado_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='publicacoes_inscricao',
        verbose_name='Publicado por',
    )

    class Meta:
        verbose_name = 'Publicação de Inscrição'
        verbose_name_plural = 'Publicações de Inscrição'
        ordering = ['-data_inicio']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({'data_fim': 'A data de fim deve ser posterior ao início.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.titulo} – {self.curso.nome} [{self.get_status_display()}]'


class Inscricao(models.Model):
    """Inscrição de um candidato em uma publicação."""

    STATUS_CHOICES = (
        ('PENDENTE',   'Pendente de Validação'),
        ('VALIDADA',   'Validada'),
        ('INDEFERIDA', 'Indeferida'),
    )

    publicacao        = models.ForeignKey(PublicacaoInscricao, on_delete=models.CASCADE, related_name='inscricoes', verbose_name='Edital')
    nome_candidato    = models.CharField(max_length=200, verbose_name='Nome do Candidato')
    cpf               = models.CharField(max_length=11, verbose_name='CPF')
    email             = models.EmailField(verbose_name='E-mail')
    telefone          = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    data_nascimento   = models.DateField(null=True, blank=True, verbose_name='Data de Nascimento')
    status            = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    data_inscricao    = models.DateTimeField(auto_now_add=True, verbose_name='Data da Inscrição')
    numero_inscricao  = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº de Inscrição')
    observacao        = models.TextField(blank=True, verbose_name='Observação')
    usuario           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='inscricoes',
        verbose_name='Usuário do Sistema',
    )

    class Meta:
        verbose_name = 'Inscrição'
        verbose_name_plural = 'Inscrições'
        ordering = ['-data_inscricao']

    def save(self, *args, **kwargs):
        if not self.numero_inscricao:
            self.numero_inscricao = self._gerar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_numero():
        from django.utils import timezone
        ano = timezone.now().year
        ultimo = Inscricao.objects.filter(numero_inscricao__startswith=f'INS-{ano}-').order_by('-numero_inscricao').first()
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero_inscricao.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = Inscricao.objects.filter(numero_inscricao__startswith=f'INS-{ano}-').count() + 1
        return f'INS-{ano}-{seq:04d}'

    def __str__(self):
        return f'{self.numero_inscricao} – {self.nome_candidato} [{self.get_status_display()}]'


class DocumentoInscricao(models.Model):
    """Documentos enviados junto com a inscrição."""

    TIPO_CHOICES = (
        ('RG',                   'RG / Documento de Identidade'),
        ('CPF',                  'CPF'),
        ('COMPROVANTE_RESIDENCIA', 'Comprovante de Residência'),
        ('HISTORICO_ESCOLAR',    'Histórico Escolar'),
        ('FOTO',                 'Foto 3x4'),
        ('OUTROS',               'Outros'),
    )

    inscricao     = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name='documentos', verbose_name='Inscrição')
    tipo          = models.CharField(max_length=25, choices=TIPO_CHOICES, verbose_name='Tipo de Documento')
    entregue      = models.BooleanField(default=False, verbose_name='Entregue')
    data_entrega  = models.DateField(null=True, blank=True, verbose_name='Data de Entrega')
    observacao    = models.CharField(max_length=255, blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Documento da Inscrição'
        verbose_name_plural = 'Documentos da Inscrição'
        unique_together = ('inscricao', 'tipo')

    def __str__(self):
        return f'{self.get_tipo_display()} – {self.inscricao}'


class ProcessoSeletivo(models.Model):
    """Processo de seleção/convocação vinculado a uma publicação."""

    MODALIDADE_CHOICES = (
        ('SORTEIO',       'Sorteio'),
        ('DEMANDA_ESPONTANEA', 'Demanda Espontânea'),
        ('PROVA',         'Prova'),
        ('ANALISE_CURRICULO', 'Análise de Currículo'),
        ('ENTREVISTA',    'Entrevista'),
    )
    STATUS_CHOICES = (
        ('PREVISTO',    'Previsto'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('CONCLUIDO',   'Concluído'),
    )

    publicacao      = models.OneToOneField(
        PublicacaoInscricao, on_delete=models.CASCADE,
        related_name='processo_seletivo',
        verbose_name='Publicação',
    )
    modalidade      = models.CharField(max_length=25, choices=MODALIDADE_CHOICES, verbose_name='Modalidade')
    data_realizacao = models.DateField(null=True, blank=True, verbose_name='Data de Realização')
    data_resultado  = models.DateField(null=True, blank=True, verbose_name='Data do Resultado')
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PREVISTO', verbose_name='Status')
    criterios       = models.TextField(blank=True, verbose_name='Critérios de Classificação')
    resultado       = models.TextField(blank=True, verbose_name='Resultado Publicado')
    responsavel     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processos_seletivos',
        verbose_name='Responsável',
    )

    class Meta:
        verbose_name = 'Processo Seletivo'
        verbose_name_plural = 'Processos Seletivos'
        ordering = ['-data_realizacao']

    def __str__(self):
        return f'Seleção – {self.publicacao.titulo} [{self.get_status_display()}]'


class Candidato(models.Model):
    """Candidato classificado em um processo seletivo."""

    SITUACAO_CHOICES = (
        ('CONVOCADO',    'Convocado'),
        ('MATRICULADO',  'Matriculado'),
        ('DESISTENTE',   'Desistente'),
        ('ELIMINADO',    'Eliminado'),
    )

    processo      = models.ForeignKey(ProcessoSeletivo, on_delete=models.CASCADE, related_name='candidatos', verbose_name='Processo Seletivo')
    inscricao     = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name='candidatos', verbose_name='Inscrição')
    classificacao = models.PositiveIntegerField(verbose_name='Classificação')
    pontuacao     = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name='Pontuação')
    situacao      = models.CharField(max_length=15, choices=SITUACAO_CHOICES, default='CONVOCADO', verbose_name='Situação')
    data_convocacao = models.DateField(null=True, blank=True, verbose_name='Data da Convocação')
    observacao    = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Candidato'
        verbose_name_plural = 'Candidatos'
        ordering = ['classificacao']
        unique_together = ('processo', 'inscricao')

    def __str__(self):
        return f'{self.classificacao}º – {self.inscricao.nome_candidato} [{self.get_situacao_display()}]'


class RecursoInscricao(models.Model):
    """Recurso apresentado por candidato contra resultado do processo seletivo."""

    STATUS_CHOICES = (
        ('ABERTO',    'Aberto'),
        ('DEFERIDO',  'Deferido'),
        ('INDEFERIDO', 'Indeferido'),
    )

    candidato    = models.ForeignKey(Candidato, on_delete=models.CASCADE, related_name='recursos', verbose_name='Candidato')
    motivo       = models.TextField(verbose_name='Motivo do Recurso')
    data_recurso = models.DateField(auto_now_add=True, verbose_name='Data do Recurso')
    status       = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ABERTO', verbose_name='Status')
    resposta     = models.TextField(blank=True, verbose_name='Resposta / Decisão')
    data_decisao = models.DateField(null=True, blank=True, verbose_name='Data da Decisão')
    decidido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='recursos_decididos',
        verbose_name='Decidido por',
    )

    class Meta:
        verbose_name = 'Recurso de Inscrição'
        verbose_name_plural = 'Recursos de Inscrição'
        ordering = ['-data_recurso']

    def __str__(self):
        return f'Recurso [{self.get_status_display()}] – {self.candidato}'
