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

    TIPO_CHOICES = (
        ('NOVA', 'Nova Matrícula'),
        ('REMATRICULA', 'Rematrícula'),
    )

    TURNO_CHOICES = (
        ('MANHA',    'Manhã'),
        ('TARDE',    'Tarde'),
        ('NOITE',    'Noite'),
        ('INTEGRAL', 'Integral'),
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
    tipo_matricula = models.CharField(max_length=20, choices=TIPO_CHOICES, default='NOVA', verbose_name='Tipo')
    turno = models.CharField(max_length=10, choices=TURNO_CHOICES, blank=True, verbose_name='Turno')

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

    @property
    def tem_pendencia(self):
        return self.pendencias.filter(status='ABERTA').exists()

    @property
    def documentos_conferidos(self):
        return self.documentos.filter(entregue=True).count()

    @property
    def total_documentos(self):
        return self.documentos.count()


class DocumentoMatricula(models.Model):
    """UC01 – include: Conferir Documentação / Registrar no Sistema"""

    TIPO_DOCUMENTO_CHOICES = (
        ('RG', 'RG / Documento de Identidade'),
        ('CPF', 'CPF'),
        ('COMPROVANTE_RESIDENCIA', 'Comprovante de Residência'),
        ('HISTORICO_ESCOLAR', 'Histórico Escolar'),
        ('FOTO', 'Foto 3x4'),
        ('CERTIDAO_NASCIMENTO', 'Certidão de Nascimento'),
        ('DECLARACAO_TRANSFERENCIA', 'Declaração de Transferência'),
        ('OUTROS', 'Outros'),
    )

    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=40, choices=TIPO_DOCUMENTO_CHOICES, verbose_name='Tipo de Documento')
    entregue = models.BooleanField(default=False, verbose_name='Entregue')
    data_entrega = models.DateField(null=True, blank=True, verbose_name='Data de Entrega')
    observacao = models.CharField(max_length=255, blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Documento da Matrícula'
        verbose_name_plural = 'Documentos da Matrícula'
        unique_together = ('matricula', 'tipo_documento')
        ordering = ['tipo_documento']

    def __str__(self):
        return f"{self.get_tipo_documento_display()} – {self.matricula}"


class PendenciaDocumental(models.Model):
    """UC01 – extend: Abrir Pendência Documental"""

    STATUS_CHOICES = (
        ('ABERTA', 'Aberta'),
        ('RESOLVIDA', 'Resolvida'),
    )

    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='pendencias')
    descricao = models.CharField(max_length=255, verbose_name='Descrição da Pendência')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTA', verbose_name='Status')
    data_abertura = models.DateField(auto_now_add=True, verbose_name='Data de Abertura')
    prazo = models.DateField(null=True, blank=True, verbose_name='Prazo para Resolução')
    data_resolucao = models.DateField(null=True, blank=True, verbose_name='Data de Resolução')
    orientacao_aluno = models.TextField(blank=True, verbose_name='Orientação ao Aluno')
    observacao = models.TextField(blank=True, verbose_name='Observação (Interno)')

    class Meta:
        verbose_name = 'Pendência Documental'
        verbose_name_plural = 'Pendências Documentais'
        ordering = ['-data_abertura']

    def __str__(self):
        return f"Pendência [{self.get_status_display()}] – {self.matricula}"


class DocumentoEmitido(models.Model):
    """UC02 – Emitir Documentos (Declaração / Histórico / Guia de Transferência)"""

    TIPO_CHOICES = (
        ('DECLARACAO_MATRICULA',  'Declaração de Matrícula'),
        ('DECLARACAO_FREQUENCIA', 'Declaração de Frequência'),
        ('DECLARACAO_CONCLUSAO',  'Declaração de Conclusão de Curso'),
        ('HISTORICO_ESCOLAR',     'Histórico Escolar'),
        ('GUIA_TRANSFERENCIA',    'Guia de Transferência'),
    )

    matricula    = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='documentos_emitidos')
    tipo         = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name='Tipo de Documento')
    numero_protocolo = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº de Protocolo')
    data_emissao = models.DateField(auto_now_add=True, verbose_name='Data de Emissão')
    observacao   = models.TextField(blank=True, verbose_name='Observação')

    # include: Assinar/Validar
    validado        = models.BooleanField(default=False, verbose_name='Validado')
    data_validacao  = models.DateField(null=True, blank=True, verbose_name='Data de Validação')
    validado_por    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='documentos_validados',
        verbose_name='Validado por',
    )

    # include: Registrar Entrega (Protocolo)
    entregue        = models.BooleanField(default=False, verbose_name='Entregue')
    data_entrega    = models.DateField(null=True, blank=True, verbose_name='Data de Entrega')
    recebido_por    = models.CharField(max_length=200, blank=True, verbose_name='Recebido por')

    class Meta:
        verbose_name = 'Documento Emitido'
        verbose_name_plural = 'Documentos Emitidos'
        ordering = ['-data_emissao']

    def save(self, *args, **kwargs):
        if not self.numero_protocolo:
            self.numero_protocolo = self._gerar_protocolo()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_protocolo():
        from django.utils import timezone
        ano = timezone.now().year
        ultimo = (
            DocumentoEmitido.objects
            .filter(numero_protocolo__startswith=f'DOC-{ano}-')
            .order_by('-numero_protocolo')
            .first()
        )
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero_protocolo.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = DocumentoEmitido.objects.filter(
                    numero_protocolo__startswith=f'DOC-{ano}-'
                ).count() + 1
        return f'DOC-{ano}-{seq:04d}'

    def __str__(self):
        return f'{self.numero_protocolo} – {self.get_tipo_display()} ({self.matricula.aluno})'


# ── UC03 – Transferência (Entrada/Saída) ─────────────────────────────────────

class Transferencia(models.Model):
    TIPO_CHOICES = (
        ('ENTRADA', 'Entrada'),
        ('SAIDA',   'Saída'),
    )
    STATUS_CHOICES = (
        ('SOLICITADA', 'Solicitada'),
        ('APROVADA',   'Aprovada'),
        ('CONCLUIDA',  'Concluída'),
        ('CANCELADA',  'Cancelada'),
    )

    matricula         = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='transferencias')
    tipo              = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name='Tipo')
    escola_origem     = models.CharField(max_length=200, blank=True, verbose_name='Escola de Origem')
    escola_destino    = models.CharField(max_length=200, blank=True, verbose_name='Escola de Destino')
    data_solicitacao  = models.DateField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_transferencia = models.DateField(null=True, blank=True, verbose_name='Data da Transferência')
    status            = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SOLICITADA', verbose_name='Status')
    numero_guia       = models.CharField(max_length=20, blank=True, verbose_name='Nº da Guia')
    observacao        = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Transferência'
        verbose_name_plural = 'Transferências'
        ordering = ['-data_solicitacao']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.tipo == 'ENTRADA' and not self.escola_origem:
            raise ValidationError({'escola_origem': 'Informe a escola de origem para transferência de entrada.'})
        if self.tipo == 'SAIDA' and not self.escola_destino:
            raise ValidationError({'escola_destino': 'Informe a escola de destino para transferência de saída.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Transferência {self.get_tipo_display()} – {self.matricula.aluno} [{self.get_status_display()}]'


# ── UC04 – Consolidar Notas e Frequência ─────────────────────────────────────

class RegraAcademica(models.Model):
    """Configuração local: média mínima e frequência mínima por curso."""

    curso             = models.OneToOneField(Curso, on_delete=models.CASCADE, related_name='regra_academica')
    media_minima      = models.DecimalField(max_digits=4, decimal_places=2, default=6.0, verbose_name='Média Mínima')
    frequencia_minima = models.DecimalField(max_digits=5, decimal_places=2, default=75.0, verbose_name='Frequência Mínima (%)')

    class Meta:
        verbose_name = 'Regra Acadêmica'
        verbose_name_plural = 'Regras Acadêmicas'

    def __str__(self):
        return f'Regra – {self.curso.nome} (média ≥ {self.media_minima}, freq ≥ {self.frequencia_minima}%)'


class ConsolidacaoAcademica(models.Model):
    """UC04 – Resultado consolidado por matrícula."""

    SITUACAO_CHOICES = (
        ('PENDENTE',               'Pendente'),
        ('APROVADO',               'Aprovado'),
        ('REPROVADO_NOTA',         'Reprovado por Nota'),
        ('REPROVADO_FREQUENCIA',   'Reprovado por Frequência'),
        ('REPROVADO_AMBOS',        'Reprovado por Nota e Frequência'),
        ('EM_RECUPERACAO',         'Em Recuperação'),
    )

    matricula              = models.OneToOneField(Matricula, on_delete=models.CASCADE, related_name='consolidacao')
    media_final            = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Média Final')
    percentual_frequencia  = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Frequência (%)')
    situacao               = models.CharField(max_length=25, choices=SITUACAO_CHOICES, default='PENDENTE', verbose_name='Situação')
    data_consolidacao      = models.DateField(null=True, blank=True, verbose_name='Data da Consolidação')
    observacao             = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Consolidação Acadêmica'
        verbose_name_plural = 'Consolidações Acadêmicas'

    def consolidar(self):
        """Calcula média ponderada e frequência e determina a situação."""
        from django.utils import timezone
        from decimal import Decimal

        notas = self.matricula.notas.all()
        if notas.exists():
            soma = sum(n.valor * n.peso for n in notas)
            pesos = sum(n.peso for n in notas)
            self.media_final = round(soma / pesos, 2) if pesos else Decimal('0')
        else:
            self.media_final = None

        frequencias = self.matricula.frequencias.all()
        total = frequencias.count()
        if total:
            presencas = frequencias.filter(presente=True).count()
            self.percentual_frequencia = round(Decimal(presencas) / Decimal(total) * 100, 2)
        else:
            self.percentual_frequencia = None

        try:
            regra = self.matricula.curso.regra_academica
        except RegraAcademica.DoesNotExist:
            regra = None

        media_min = regra.media_minima if regra else Decimal('6.0')
        freq_min  = regra.frequencia_minima if regra else Decimal('75.0')

        reprov_nota = self.media_final is not None and self.media_final < media_min
        reprov_freq = self.percentual_frequencia is not None and self.percentual_frequencia < freq_min

        if reprov_nota and reprov_freq:
            self.situacao = 'REPROVADO_AMBOS'
        elif reprov_nota:
            self.situacao = 'REPROVADO_NOTA'
        elif reprov_freq:
            self.situacao = 'REPROVADO_FREQUENCIA'
        elif self.media_final is not None or self.percentual_frequencia is not None:
            self.situacao = 'APROVADO'
        else:
            self.situacao = 'PENDENTE'

        self.data_consolidacao = timezone.now().date()
        self.save()

    def __str__(self):
        return f'Consolidação – {self.matricula} [{self.get_situacao_display()}]'


# ── P01 – Fluxo de Matrícula ─────────────────────────────────────────────────

class FluxoMatricula(models.Model):
    """
    P01 – Máquina de estados do fluxo completo de matrícula.
    Swimlanes: Aluno | Secretaria | Sistema
    """

    ETAPA_CHOICES = (
        # (etapa, label, ator_responsável)
        ('REQUERIMENTO_RECEBIDO',  'Receber Requerimento'),       # Aluno → Secretaria
        ('DOCUMENTOS_CONFERIDOS',  'Conferir Documentos'),        # Secretaria
        ('PENDENCIA_ABERTA',       'Pendência + Prazo'),           # Secretaria → Aluno
        ('REQUISITOS_VALIDADOS',   'Validar Requisitos'),          # Sistema
        ('MATRICULA_REGISTRADA',   'Registrar Matrícula'),         # Sistema
        ('ALUNO_ENTURMADO',        'Enturmar / Alocar Turno'),     # Secretaria
        ('COMPROVANTE_EMITIDO',    'Emitir Comprovante'),          # Sistema
        ('ARQUIVADO',              'Arquivar (Classificar + Indexar)'),  # Secretaria
    )

    # Quem é o ator principal de cada etapa (para swimlane)
    ATOR_ETAPA = {
        'REQUERIMENTO_RECEBIDO': 'aluno',
        'DOCUMENTOS_CONFERIDOS': 'secretaria',
        'PENDENCIA_ABERTA':      'secretaria',
        'REQUISITOS_VALIDADOS':  'sistema',
        'MATRICULA_REGISTRADA':  'sistema',
        'ALUNO_ENTURMADO':       'secretaria',
        'COMPROVANTE_EMITIDO':   'sistema',
        'ARQUIVADO':             'secretaria',
    }

    ORDEM_ETAPAS = [e[0] for e in ETAPA_CHOICES]

    aluno           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fluxos_matricula',
        limit_choices_to={'tipo': 'ALUNO'},
        verbose_name='Aluno',
    )
    tipo_matricula  = models.CharField(max_length=20, choices=Matricula.TIPO_CHOICES, default='NOVA', verbose_name='Tipo')
    etapa_atual     = models.CharField(max_length=30, choices=ETAPA_CHOICES, default='REQUERIMENTO_RECEBIDO', verbose_name='Etapa Atual')
    data_inicio     = models.DateField(auto_now_add=True, verbose_name='Data de Início')
    concluido       = models.BooleanField(default=False, verbose_name='Concluído')
    observacoes     = models.TextField(blank=True, verbose_name='Observações')

    # Vínculos com registros criados em cada etapa
    matricula               = models.OneToOneField(
        Matricula, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo',
        verbose_name='Matrícula',
    )
    documento_comprovante   = models.OneToOneField(
        DocumentoEmitido, null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo_comprovante',
        verbose_name='Comprovante Emitido',
    )

    class Meta:
        verbose_name = 'Fluxo de Matrícula'
        verbose_name_plural = 'Fluxos de Matrícula'
        ordering = ['-data_inicio']

    def get_indice_etapa(self):
        try:
            return self.ORDEM_ETAPAS.index(self.etapa_atual)
        except ValueError:
            return 0

    def get_proxima_etapa(self):
        idx = self.get_indice_etapa()
        if idx < len(self.ORDEM_ETAPAS) - 1:
            return self.ORDEM_ETAPAS[idx + 1]
        return None

    def avancar(self, proxima_etapa=None):
        """Avança para a próxima etapa (ou para uma etapa específica)."""
        if proxima_etapa:
            self.etapa_atual = proxima_etapa
        else:
            prox = self.get_proxima_etapa()
            if prox:
                self.etapa_atual = prox
        if self.etapa_atual == 'ARQUIVADO':
            self.concluido = True
        self.save()

    def etapas_info(self):
        """Retorna lista de dicts com info de cada etapa para o template."""
        idx_atual = self.get_indice_etapa()
        resultado = []
        for i, (codigo, label) in enumerate(self.ETAPA_CHOICES):
            resultado.append({
                'codigo': codigo,
                'label': label,
                'ator': self.ATOR_ETAPA.get(codigo, 'sistema'),
                'concluida': i < idx_atual,
                'atual': i == idx_atual,
                'futura': i > idx_atual,
            })
        return resultado

    def __str__(self):
        return f'P01 – {self.aluno} [{self.get_etapa_atual_display()}]'


class EtapaFluxo(models.Model):
    """Log de auditoria de cada transição do P01."""

    fluxo           = models.ForeignKey(FluxoMatricula, on_delete=models.CASCADE, related_name='log_etapas')
    etapa           = models.CharField(max_length=30, choices=FluxoMatricula.ETAPA_CHOICES, verbose_name='Etapa')
    responsavel     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etapas_fluxo',
        verbose_name='Responsável',
    )
    data            = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    observacao      = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Etapa do Fluxo'
        verbose_name_plural = 'Etapas do Fluxo'
        ordering = ['data']

    def __str__(self):
        return f'{self.fluxo} → {self.etapa} ({self.data:%d/%m/%Y %H:%M})'


# ── P02 – Fluxo de Emissão de Histórico/Declaração ───────────────────────────

class FluxoEmissaoDocumento(models.Model):
    """
    P02 – Máquina de estados para emissão de Histórico Escolar ou Declaração.
    Swimlanes: Aluno/Solicitante | Secretaria | Sistema
    """

    ETAPA_CHOICES = (
        ('PROTOCOLO_ABERTO',        'Abrir Protocolo'),
        ('ELEGIBILIDADE_VERIFICADA','Verificar Elegibilidade'),
        ('DOCUMENTO_GERADO',        'Gerar Documento Padrão'),
        ('DOCUMENTO_VALIDADO',      'Assinar / Validar'),
        ('ENTREGA_REGISTRADA',      'Registrar Entrega'),
        ('ARQUIVADO',               'Arquivar via Protocolo'),
    )

    ATOR_ETAPA = {
        'PROTOCOLO_ABERTO':         'secretaria',
        'ELEGIBILIDADE_VERIFICADA': 'sistema',
        'DOCUMENTO_GERADO':         'sistema',
        'DOCUMENTO_VALIDADO':       'secretaria',
        'ENTREGA_REGISTRADA':       'secretaria',
        'ARQUIVADO':                'sistema',
    }

    ORDEM_ETAPAS = [e[0] for e in ETAPA_CHOICES]

    solicitante      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fluxos_emissao',
        verbose_name='Solicitante',
    )
    matricula        = models.ForeignKey(
        Matricula,
        on_delete=models.CASCADE,
        related_name='fluxos_emissao',
        verbose_name='Matrícula',
    )
    tipo_documento   = models.CharField(
        max_length=30,
        choices=DocumentoEmitido.TIPO_CHOICES,
        verbose_name='Tipo de Documento',
    )
    etapa_atual      = models.CharField(
        max_length=30,
        choices=ETAPA_CHOICES,
        default='PROTOCOLO_ABERTO',
        verbose_name='Etapa Atual',
    )
    data_inicio      = models.DateField(auto_now_add=True, verbose_name='Data de Início')
    concluido        = models.BooleanField(default=False, verbose_name='Concluído')
    elegivel         = models.BooleanField(null=True, blank=True, verbose_name='Elegível')
    motivo_inelegivel = models.CharField(max_length=255, blank=True, verbose_name='Motivo de Inelegibilidade')
    observacoes      = models.TextField(blank=True, verbose_name='Observações')

    # Vínculos criados em cada etapa
    processo         = models.OneToOneField(
        'processos.Processo',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo_emissao',
        verbose_name='Protocolo',
    )
    documento_emitido = models.OneToOneField(
        DocumentoEmitido,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo_emissao',
        verbose_name='Documento Emitido',
    )

    class Meta:
        verbose_name = 'Fluxo de Emissão de Documento'
        verbose_name_plural = 'Fluxos de Emissão de Documentos'
        ordering = ['-data_inicio']

    def get_indice_etapa(self):
        try:
            return self.ORDEM_ETAPAS.index(self.etapa_atual)
        except ValueError:
            return 0

    def get_proxima_etapa(self):
        idx = self.get_indice_etapa()
        if idx < len(self.ORDEM_ETAPAS) - 1:
            return self.ORDEM_ETAPAS[idx + 1]
        return None

    def avancar(self, proxima_etapa=None):
        if proxima_etapa:
            self.etapa_atual = proxima_etapa
        else:
            prox = self.get_proxima_etapa()
            if prox:
                self.etapa_atual = prox
        if self.etapa_atual == 'ARQUIVADO':
            self.concluido = True
        self.save()

    def verificar_elegibilidade(self):
        """Etapa 2 – Verifica automaticamente se o aluno pode receber o documento."""
        tipo = self.tipo_documento
        matricula = self.matricula
        motivo = ''

        if matricula.status == 'CANCELADA':
            motivo = 'Matrícula cancelada.'
        elif tipo == 'DECLARACAO_CONCLUSAO' and matricula.status != 'CONCLUIDA':
            motivo = 'Declaração de Conclusão exige matrícula com status Concluída.'
        elif tipo == 'GUIA_TRANSFERENCIA' and matricula.status not in ('ATIVA', 'TRANCADA'):
            motivo = 'Guia de Transferência exige matrícula Ativa ou Trancada.'
        elif tipo == 'HISTORICO_ESCOLAR' and not matricula.notas.exists():
            motivo = 'Histórico Escolar: nenhuma nota lançada na matrícula.'

        self.elegivel = not bool(motivo)
        self.motivo_inelegivel = motivo
        self.save()
        return self.elegivel

    def etapas_info(self):
        idx_atual = self.get_indice_etapa()
        resultado = []
        for i, (codigo, label) in enumerate(self.ETAPA_CHOICES):
            resultado.append({
                'codigo': codigo,
                'label': label,
                'ator': self.ATOR_ETAPA.get(codigo, 'sistema'),
                'concluida': i < idx_atual,
                'atual': i == idx_atual,
                'futura': i > idx_atual,
            })
        return resultado

    def __str__(self):
        return f'P02 – {self.solicitante} / {self.get_tipo_documento_display()} [{self.get_etapa_atual_display()}]'


class EtapaFluxoEmissao(models.Model):
    """Log de auditoria das transições do P02."""

    fluxo        = models.ForeignKey(FluxoEmissaoDocumento, on_delete=models.CASCADE, related_name='log_etapas')
    etapa        = models.CharField(max_length=30, choices=FluxoEmissaoDocumento.ETAPA_CHOICES, verbose_name='Etapa')
    responsavel  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etapas_fluxo_emissao',
        verbose_name='Responsável',
    )
    data         = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    observacao   = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Etapa do Fluxo de Emissão'
        verbose_name_plural = 'Etapas do Fluxo de Emissão'
        ordering = ['data']

    def __str__(self):
        return f'{self.fluxo} → {self.etapa} ({self.data:%d/%m/%Y %H:%M})'


# ── P03 – Fluxo de Transferência ─────────────────────────────────────────────

class FluxoTransferencia(models.Model):
    """
    P03 – Máquina de estados para o processo de Transferência (Entrada/Saída).
    Swimlanes: Aluno | Secretaria | Sistema
    """

    ETAPA_CHOICES = (
        ('SOLICITACAO',       'Solicitação'),
        ('CONFERENCIA_DADOS', 'Conferência de Dados'),
        ('GUIA_EMITIDA',      'Emitir Guia / Histórico Parcial'),
        ('BAIXA_ATUALIZADA',  'Baixa / Atualização no Sistema'),
        ('ARQUIVADO',         'Arquivamento'),
    )

    ATOR_ETAPA = {
        'SOLICITACAO':       'aluno',
        'CONFERENCIA_DADOS': 'secretaria',
        'GUIA_EMITIDA':      'sistema',
        'BAIXA_ATUALIZADA':  'sistema',
        'ARQUIVADO':         'secretaria',
    }

    ORDEM_ETAPAS = [e[0] for e in ETAPA_CHOICES]

    matricula    = models.ForeignKey(
        Matricula,
        on_delete=models.CASCADE,
        related_name='fluxos_transferencia',
        verbose_name='Matrícula',
    )
    etapa_atual  = models.CharField(
        max_length=20,
        choices=ETAPA_CHOICES,
        default='SOLICITACAO',
        verbose_name='Etapa Atual',
    )
    data_inicio  = models.DateField(auto_now_add=True, verbose_name='Data de Início')
    concluido    = models.BooleanField(default=False, verbose_name='Concluído')
    observacoes  = models.TextField(blank=True, verbose_name='Observações')

    # Vínculos criados em cada etapa
    transferencia = models.OneToOneField(
        Transferencia,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo',
        verbose_name='Transferência',
    )
    processo = models.OneToOneField(
        'processos.Processo',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo_transferencia',
        verbose_name='Protocolo',
    )
    documento_emitido = models.OneToOneField(
        DocumentoEmitido,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='fluxo_transferencia',
        verbose_name='Documento Emitido',
    )

    class Meta:
        verbose_name = 'Fluxo de Transferência'
        verbose_name_plural = 'Fluxos de Transferência'
        ordering = ['-data_inicio']

    def get_indice_etapa(self):
        try:
            return self.ORDEM_ETAPAS.index(self.etapa_atual)
        except ValueError:
            return 0

    def get_proxima_etapa(self):
        idx = self.get_indice_etapa()
        if idx < len(self.ORDEM_ETAPAS) - 1:
            return self.ORDEM_ETAPAS[idx + 1]
        return None

    def avancar(self, proxima_etapa=None):
        if proxima_etapa:
            self.etapa_atual = proxima_etapa
        else:
            prox = self.get_proxima_etapa()
            if prox:
                self.etapa_atual = prox
        if self.etapa_atual == 'ARQUIVADO':
            self.concluido = True
        self.save()

    def etapas_info(self):
        idx_atual = self.get_indice_etapa()
        resultado = []
        for i, (codigo, label) in enumerate(self.ETAPA_CHOICES):
            resultado.append({
                'codigo': codigo,
                'label': label,
                'ator': self.ATOR_ETAPA.get(codigo, 'sistema'),
                'concluida': i < idx_atual,
                'atual': i == idx_atual,
                'futura': i > idx_atual,
            })
        return resultado

    def __str__(self):
        return f'P03 – {self.matricula.aluno} [{self.get_etapa_atual_display()}]'


class EtapaFluxoTransferencia(models.Model):
    """Log de auditoria das transições do P03."""

    fluxo       = models.ForeignKey(FluxoTransferencia, on_delete=models.CASCADE, related_name='log_etapas')
    etapa       = models.CharField(max_length=20, choices=FluxoTransferencia.ETAPA_CHOICES, verbose_name='Etapa')
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='etapas_fluxo_transferencia',
        verbose_name='Responsável',
    )
    data        = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    observacao  = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Etapa do Fluxo de Transferência'
        verbose_name_plural = 'Etapas do Fluxo de Transferência'
        ordering = ['data']

    def __str__(self):
        return f'{self.fluxo} → {self.etapa} ({self.data:%d/%m/%Y %H:%M})'
