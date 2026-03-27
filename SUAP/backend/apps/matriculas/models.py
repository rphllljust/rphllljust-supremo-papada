from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.cursos.models import Curso
from apps.turmas.models import Turma
from apps.usuarios.models import PerfilUsuario


class Matricula(models.Model):
    STATUS_CHOICES = (
        ('ATIVA', 'Ativa'),
        ('TRANCADA', 'Trancada'),
        ('CANCELADA', 'Cancelada'),
        ('CONCLUIDA', 'Concluída'),
    )

    TRANSICOES_STATUS = {
        'ATIVA': {'TRANCADA', 'CANCELADA', 'CONCLUIDA'},
        'TRANCADA': {'ATIVA', 'CANCELADA'},
        'CANCELADA': set(),
        'CONCLUIDA': set(),
    }

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

    numero_matricula = models.CharField(max_length=24, unique=True, editable=False, blank=True)
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matriculas',
        limit_choices_to={'tipo': PerfilUsuario.ALUNO}
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

        if not self.pk:
            return

        original = Matricula.objects.filter(pk=self.pk).values_list('status', flat=True).first()
        if not original or original == self.status:
            return

        permitidos = self.TRANSICOES_STATUS.get(original, set())
        if self.status not in permitidos:
            raise ValidationError({'status': f'Transicao de status invalida: {original} -> {self.status}.'})

    def save(self, *args, **kwargs):
        if not self.numero_matricula:
            self.numero_matricula = self._gerar_numero_matricula()
        self.full_clean()
        return super().save(*args, **kwargs)

    def _gerar_numero_matricula(self):
        from django.utils import timezone

        ano = self.turma.ano_letivo if self.turma_id else timezone.now().year
        sigla = (self.curso.sigla or '').strip().upper() if self.curso_id else ''
        if not sigla:
            nome = (self.curso.nome if self.curso_id else 'CURSO').upper()
            sigla = ''.join(ch for ch in nome if ch.isalpha())[:3] or 'CUR'

        prefixo = f'{ano}-{sigla}-'
        ultima = (
            Matricula.objects
            .filter(numero_matricula__startswith=prefixo)
            .order_by('-numero_matricula')
            .first()
        )
        seq = 1
        if ultima:
            try:
                seq = int(ultima.numero_matricula.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = Matricula.objects.filter(numero_matricula__startswith=prefixo).count() + 1
        return f'{prefixo}{seq:06d}'

    def __str__(self):
        return f"{self.numero_matricula} - {self.aluno} - {self.curso} / {self.turma}"

    @property
    def tem_pendencia(self):
        return self.pendencias.filter(status='ABERTA').exists()

    @property
    def documentos_conferidos(self):
        return self.documentos.filter(status='VALIDADO').count()

    @property
    def total_documentos(self):
        return self.documentos.count()


class DocumentoMatricula(models.Model):
    """UC01 - include: Conferir Documentacao / Registrar no Sistema"""

    TIPO_DOCUMENTO_CHOICES = (
        ('RG', 'RG / Documento de Identidade'),
        ('CPF', 'CPF'),
        ('COMPROVANTE_RESIDENCIA', 'Comprovante de Residencia'),
        ('HISTORICO_ESCOLAR', 'Historico Escolar'),
        ('FOTO', 'Foto 3x4'),
        ('CERTIDAO_NASCIMENTO', 'Certidao de Nascimento'),
        ('DECLARACAO_TRANSFERENCIA', 'Declaracao de Transferencia'),
        ('OUTROS', 'Outros'),
    )

    STATUS_CHOICES = (
        ('PENDENTE', 'Pendente'),
        ('RECEBIDO', 'Recebido'),
        ('VALIDADO', 'Validado'),
        ('RECUSADO', 'Recusado'),
    )

    TRANSICOES_STATUS = {
        'PENDENTE': {'RECEBIDO'},
        'RECEBIDO': {'VALIDADO', 'RECUSADO'},
        'RECUSADO': {'RECEBIDO'},
        'VALIDADO': set(),
    }

    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='documentos')
    tipo_documento = models.CharField(max_length=40, choices=TIPO_DOCUMENTO_CHOICES, verbose_name='Tipo de Documento')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    entregue = models.BooleanField(default=False, verbose_name='Entregue')
    data_entrega = models.DateField(null=True, blank=True, verbose_name='Data de Entrega')
    data_recebimento = models.DateField(null=True, blank=True, verbose_name='Data de Recebimento')
    arquivo = models.FileField(upload_to='matriculas/documentos/', null=True, blank=True, verbose_name='Arquivo')
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='documentos_matricula_validados',
        verbose_name='Validado por',
    )
    data_validacao = models.DateField(null=True, blank=True, verbose_name='Data de Validacao')
    motivo_recusa = models.CharField(max_length=255, blank=True, verbose_name='Motivo da Recusa')
    observacao = models.CharField(max_length=255, blank=True, verbose_name='Observacao')

    class Meta:
        verbose_name = 'Documento da Matricula'
        verbose_name_plural = 'Documentos da Matricula'
        unique_together = ('matricula', 'tipo_documento')
        ordering = ['tipo_documento']

    def clean(self):
        if not self.pk:
            original = None
        else:
            original = DocumentoMatricula.objects.filter(pk=self.pk).values_list('status', flat=True).first()

        if original and original != self.status:
            permitidos = self.TRANSICOES_STATUS.get(original, set())
            if self.status not in permitidos:
                raise ValidationError({'status': f'Transicao de status invalida: {original} -> {self.status}.'})

        if self.status in {'RECEBIDO', 'VALIDADO', 'RECUSADO'} and not self.data_recebimento:
            raise ValidationError({'data_recebimento': 'Informe a data de recebimento do documento.'})

        if self.status == 'VALIDADO':
            if not self.data_validacao:
                raise ValidationError({'data_validacao': 'Informe a data de validacao.'})
            if not self.validado_por_id:
                raise ValidationError({'validado_por': 'Informe quem validou o documento.'})

        if self.status == 'RECUSADO' and not self.motivo_recusa:
            raise ValidationError({'motivo_recusa': 'Informe o motivo da recusa.'})

    def save(self, *args, **kwargs):
        self.entregue = self.status in {'RECEBIDO', 'VALIDADO', 'RECUSADO'}
        self.data_entrega = self.data_recebimento if self.entregue else None
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_documento_display()} - {self.matricula} [{self.get_status_display()}]"


class PendenciaDocumental(models.Model):
    """UC01 - extend: Abrir Pendência Documental"""

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
        return f"Pendência [{self.get_status_display()}] - {self.matricula}"


class DocumentoEmitido(models.Model):
    """UC02 - Emitir Documentos (Declaração / Histórico / Guia de Transferência)"""

    TIPO_CHOICES = (
        ('DECLARACAO_MATRICULA', 'Declaração de Matrícula'),
        ('DECLARACAO_FREQUENCIA', 'Declaração de Frequência'),
        ('DECLARACAO_CONCLUSAO', 'Declaração de Conclusão de Curso'),
        ('HISTORICO_ESCOLAR', 'Histórico Escolar'),
        ('GUIA_TRANSFERENCIA', 'Guia de Transferência'),
    )

    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='documentos_emitidos')
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name='Tipo de Documento')
    numero_protocolo = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº de Protocolo')
    data_emissao = models.DateField(auto_now_add=True, verbose_name='Data de Emissão')
    observacao = models.TextField(blank=True, verbose_name='Observação')

    validado = models.BooleanField(default=False, verbose_name='Validado')
    data_validacao = models.DateField(null=True, blank=True, verbose_name='Data de Validação')
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='documentos_validados',
        verbose_name='Validado por',
    )

    entregue = models.BooleanField(default=False, verbose_name='Entregue')
    data_entrega = models.DateField(null=True, blank=True, verbose_name='Data de Entrega')
    recebido_por = models.CharField(max_length=200, blank=True, verbose_name='Recebido por')

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
        return f"{self.numero_protocolo} - {self.get_tipo_display()} ({self.matricula.aluno})"


class TermoAssinado(models.Model):
    TIPO_CHOICES = (
        ('MATRICULA', 'Termo de Matricula'),
        ('CIENCIA_PENDENCIA', 'Ciencia de Pendencia Documental'),
        ('LGPD', 'Ciencia de Tratamento de Dados (LGPD)'),
        ('OUTRO', 'Outro'),
    )

    matricula = models.ForeignKey(Matricula, on_delete=models.CASCADE, related_name='termos_assinados')
    tipo_termo = models.CharField(max_length=30, choices=TIPO_CHOICES)
    data_assinatura = models.DateField()
    assinado_por = models.CharField(max_length=200)
    arquivo = models.FileField(upload_to='matriculas/termos/', null=True, blank=True)
    observacao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Termo Assinado'
        verbose_name_plural = 'Termos Assinados'
        ordering = ['-data_assinatura', '-id']

    def __str__(self):
        return f'{self.get_tipo_termo_display()} - {self.matricula.numero_matricula}'


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


# ── P01 – Fluxo de Matrícula ───────────────────────────────────────���─────────

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
        limit_choices_to={'tipo': PerfilUsuario.ALUNO},
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
        ('ARQUIVADO',               'Arquivamento'),
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


# ── Aproveitamento de Componentes / Equivalência ──────────────────────────────

class AproveitamentoComponente(models.Model):
    """Registro de aproveitamento ou equivalência de componente curricular."""

    STATUS_CHOICES = (
        ('SOLICITADO', 'Solicitado'),
        ('APROVADO',   'Aprovado'),
        ('INDEFERIDO', 'Indeferido'),
    )

    matricula           = models.ForeignKey(
        Matricula, on_delete=models.CASCADE,
        related_name='aproveitamentos',
        verbose_name='Matrícula',
    )
    componente_origem   = models.CharField(max_length=255, verbose_name='Componente de Origem')
    instituicao_origem  = models.CharField(max_length=255, blank=True, verbose_name='Instituição de Origem')
    carga_horaria       = models.PositiveIntegerField(verbose_name='Carga Horária (h)')
    componente_destino  = models.CharField(max_length=255, verbose_name='Componente Equivalente no Curso')
    status              = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SOLICITADO', verbose_name='Status')
    data_solicitacao    = models.DateField(auto_now_add=True, verbose_name='Data da Solicitação')
    data_decisao        = models.DateField(null=True, blank=True, verbose_name='Data da Decisão')
    decisao_por         = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='aproveitamentos_decididos',
        verbose_name='Decisão por',
    )
    justificativa       = models.TextField(blank=True, verbose_name='Justificativa / Observação')

    class Meta:
        verbose_name = 'Aproveitamento de Componente'
        verbose_name_plural = 'Aproveitamentos de Componentes'
        ordering = ['-data_solicitacao']

    def __str__(self):
        return f'Aproveitamento [{self.get_status_display()}] – {self.componente_origem} → {self.componente_destino} ({self.matricula.aluno})'


# ── Fechamento e Conclusão ────────────────────────────────────────────────────

class DependenciaAcademica(models.Model):
    """Controle de componentes em dependência por matrícula."""

    STATUS_CHOICES = (
        ("ATIVA", "Ativa"),
        ("CUMPRIDA", "Cumprida"),
        ("DISPENSADA", "Dispensada"),
    )
    MOTIVO_CHOICES = (
        ("NOTA", "Nota"),
        ("FREQUENCIA", "Frequência"),
        ("AMBOS", "Nota e Frequência"),
        ("OUTRO", "Outro"),
    )

    matricula = models.ForeignKey(
        Matricula,
        on_delete=models.CASCADE,
        related_name="dependencias",
        verbose_name="Matrícula",
    )
    componente = models.CharField(max_length=255, verbose_name="Componente/Disciplina")
    periodo_referencia = models.CharField(max_length=50, blank=True, verbose_name="Período de Referência")
    motivo = models.CharField(max_length=15, choices=MOTIVO_CHOICES, default="NOTA", verbose_name="Motivo")
    nota_obtida = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Nota Obtida")
    frequencia_percentual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Frequência (%)",
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="ATIVA", verbose_name="Status")
    data_registro = models.DateField(auto_now_add=True, verbose_name="Data de Registro")
    data_resolucao = models.DateField(null=True, blank=True, verbose_name="Data de Resolução")
    observacao = models.TextField(blank=True, verbose_name="Observação")

    class Meta:
        verbose_name = "Dependência Acadêmica"
        verbose_name_plural = "Dependências Acadêmicas"
        ordering = ["-data_registro", "-id"]

    def __str__(self):
        return f"Dependência [{self.get_status_display()}] – {self.componente} ({self.matricula.numero_matricula})"


class ConselhoClasse(models.Model):
    """Registro do Conselho de Classe por turma/período."""

    STATUS_CHOICES = (
        ('AGENDADO',   'Agendado'),
        ('REALIZADO',  'Realizado'),
        ('CANCELADO',  'Cancelado'),
    )

    turma           = models.ForeignKey(
        'turmas.Turma', on_delete=models.CASCADE,
        related_name='conselhos',
        verbose_name='Turma',
    )
    periodo         = models.CharField(max_length=50, verbose_name='Período de Referência')
    data_reuniao    = models.DateField(verbose_name='Data da Reunião')
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='AGENDADO', verbose_name='Status')
    pauta           = models.TextField(blank=True, verbose_name='Pauta')
    ata             = models.TextField(blank=True, verbose_name='Ata da Reunião')
    responsavel     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='conselhos_presididos',
        verbose_name='Responsável',
    )

    class Meta:
        verbose_name = 'Conselho de Classe'
        verbose_name_plural = 'Conselhos de Classe'
        ordering = ['-data_reuniao']

    def __str__(self):
        return f'Conselho – {self.turma} / {self.periodo} [{self.get_status_display()}]'


class AtaResultado(models.Model):
    """Ata de resultado final publicada após o conselho de classe."""

    conselho        = models.OneToOneField(
        ConselhoClasse, on_delete=models.CASCADE,
        related_name='ata_resultado',
        verbose_name='Conselho de Classe',
    )
    data_publicacao = models.DateField(verbose_name='Data de Publicação')
    conteudo        = models.TextField(verbose_name='Conteúdo da Ata')
    publicado_por   = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='atas_publicadas',
        verbose_name='Publicado por',
    )
    numero_ata      = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº da Ata')

    class Meta:
        verbose_name = 'Ata de Resultado'
        verbose_name_plural = 'Atas de Resultado'
        ordering = ['-data_publicacao']

    def save(self, *args, **kwargs):
        if not self.numero_ata:
            from django.utils import timezone
            ano = timezone.now().year
            ultimo = AtaResultado.objects.filter(numero_ata__startswith=f'ATA-{ano}-').order_by('-numero_ata').first()
            seq = 1
            if ultimo:
                try:
                    seq = int(ultimo.numero_ata.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = AtaResultado.objects.filter(numero_ata__startswith=f'ATA-{ano}-').count() + 1
            self.numero_ata = f'ATA-{ano}-{seq:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.numero_ata} – {self.conselho}'


class CertificadoDiploma(models.Model):
    """Certificado ou diploma emitido ao concluir o curso."""

    TIPO_CHOICES = (
        ('CERTIFICADO', 'Certificado'),
        ('DIPLOMA',     'Diploma'),
    )
    STATUS_CHOICES = (
        ('PENDENTE',  'Pendente'),
        ('EMITIDO',   'Emitido'),
        ('ENTREGUE',  'Entregue'),
        ('CANCELADO', 'Cancelado'),
    )

    matricula       = models.ForeignKey(
        Matricula, on_delete=models.CASCADE,
        related_name='certificados',
        verbose_name='Matrícula',
    )
    tipo            = models.CharField(max_length=15, choices=TIPO_CHOICES, default='CERTIFICADO', verbose_name='Tipo')
    numero_registro = models.CharField(max_length=20, unique=True, editable=False, verbose_name='Nº de Registro')
    data_emissao    = models.DateField(null=True, blank=True, verbose_name='Data de Emissão')
    data_entrega    = models.DateField(null=True, blank=True, verbose_name='Data de Entrega')
    status          = models.CharField(max_length=15, choices=STATUS_CHOICES, default='PENDENTE', verbose_name='Status')
    emitido_por     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='certificados_emitidos',
        verbose_name='Emitido por',
    )
    observacao      = models.TextField(blank=True, verbose_name='Observação')

    class Meta:
        verbose_name = 'Certificado / Diploma'
        verbose_name_plural = 'Certificados / Diplomas'
        ordering = ['-data_emissao']

    def save(self, *args, **kwargs):
        if not self.numero_registro:
            from django.utils import timezone
            ano = timezone.now().year
            prefixo = 'CER' if self.tipo == 'CERTIFICADO' else 'DIP'
            ultimo = CertificadoDiploma.objects.filter(numero_registro__startswith=f'{prefixo}-{ano}-').order_by('-numero_registro').first()
            seq = 1
            if ultimo:
                try:
                    seq = int(ultimo.numero_registro.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = CertificadoDiploma.objects.filter(numero_registro__startswith=f'{prefixo}-{ano}-').count() + 1
            self.numero_registro = f'{prefixo}-{ano}-{seq:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.numero_registro} – {self.get_tipo_display()} – {self.matricula.aluno}'


# ── Documento Oficial: Ata Escolar ───────────────────────────────────────────

class AtaEscolar(models.Model):
    """
    Documento formal da Ata Escolar para impressão e arquivo oficial.
    Gerado a partir do ConselhoClasse com estrutura completa para assinatura.
    """

    TIPO_CHOICES = (
        ('CONSELHO_CLASSE',    'Conselho de Classe'),
        ('RESULTADO_FINAL',    'Resultado Final'),
        ('REUNIAO_PEDAGOGICA', 'Reunião Pedagógica'),
    )

    conselho        = models.OneToOneField(
        ConselhoClasse, on_delete=models.CASCADE,
        related_name='ata_escolar',
        verbose_name='Conselho de Classe',
    )
    numero_documento = models.CharField(max_length=25, unique=True, editable=False, verbose_name='Nº do Documento')
    tipo            = models.CharField(max_length=25, choices=TIPO_CHOICES, default='CONSELHO_CLASSE', verbose_name='Tipo de Ata')
    titulo          = models.CharField(max_length=200, verbose_name='Título')
    unidade_nome    = models.CharField(max_length=200, verbose_name='Unidade Escolar')
    local_reuniao   = models.CharField(max_length=200, verbose_name='Local da Reunião')
    data_reuniao    = models.DateField(verbose_name='Data da Reunião')
    hora_inicio     = models.TimeField(null=True, blank=True, verbose_name='Hora de Início')
    hora_fim        = models.TimeField(null=True, blank=True, verbose_name='Hora de Encerramento')
    presidente      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='atas_presididas',
        verbose_name='Presidente da Reunião',
    )
    secretario      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='atas_secretariadas',
        verbose_name='Secretário(a)',
    )
    membros_presentes = models.TextField(
        verbose_name='Membros Presentes',
        help_text='Um por linha: Nome – Cargo',
    )
    abertura        = models.TextField(verbose_name='Texto de Abertura')
    deliberacoes    = models.TextField(verbose_name='Deliberações / Decisões')
    encerramento    = models.TextField(verbose_name='Texto de Encerramento')
    assinado        = models.BooleanField(default=False, verbose_name='Assinado')
    data_assinatura = models.DateField(null=True, blank=True, verbose_name='Data de Assinatura')

    class Meta:
        verbose_name = 'Ata Escolar'
        verbose_name_plural = 'Atas Escolares'
        ordering = ['-data_reuniao']

    def save(self, *args, **kwargs):
        if not self.numero_documento:
            from django.utils import timezone
            ano = timezone.now().year
            ultimo = AtaEscolar.objects.filter(
                numero_documento__startswith=f'ATA-ESC-{ano}-'
            ).order_by('-numero_documento').first()
            seq = 1
            if ultimo:
                try:
                    seq = int(ultimo.numero_documento.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = AtaEscolar.objects.filter(
                        numero_documento__startswith=f'ATA-ESC-{ano}-'
                    ).count() + 1
            self.numero_documento = f'ATA-ESC-{ano}-{seq:04d}'
        super().save(*args, **kwargs)

    @staticmethod
    def _data_pt(d) -> str:
        meses = ['janeiro','fevereiro','março','abril','maio','junho',
                 'julho','agosto','setembro','outubro','novembro','dezembro']
        return f'{d.day:02d} de {meses[d.month - 1]} de {d.year}'

    def gerar_documento(self) -> str:
        """
        Retorna a Ata Escolar no formato padrão SEDUC-RO para impressão/arquivo.
        Inclui cabeçalho institucional, texto declaratório, membros, tabela de
        resultados por aluno e bloco de assinaturas.
        """
        W = 92

        unidade   = self.conselho.turma.curso.unidade
        municipio = (f"{unidade.cidade} – {unidade.uf}"
                     if unidade.cidade else "Porto Velho – RO")
        pres_nome = (self.presidente.get_full_name()
                     if self.presidente else '________________________________')
        sec_nome  = (self.secretario.get_full_name()
                     if self.secretario else '________________________________')
        hora_ini  = self.hora_inicio.strftime('%Hh%M') if self.hora_inicio else '__h__'
        hora_fim  = self.hora_fim.strftime('%Hh%M') if self.hora_fim else '__h__'

        membros_lines = [m.strip() for m in self.membros_presentes.splitlines() if m.strip()]
        membros_fmt   = '\n'.join(f'  {i + 1}. {m}' for i, m in enumerate(membros_lines))

        matriculas = (
            self.conselho.turma.matriculas
            .select_related('aluno')
            .order_by('aluno__last_name', 'aluno__first_name')
        )

        def _res(mat):
            try:
                c      = mat.consolidacao
                media  = f"{c.media_final:.2f}".replace('.', ',') if c.media_final else '----'
                freq   = (f"{c.percentual_frequencia:.1f}%".replace('.', ',')
                          if c.percentual_frequencia else '----')
                result = c.get_situacao_display()
            except Exception:
                media = freq = '----'
                result = 'Pendente'
            return media, freq, result

        doc = [
            f"\n{'=' * W}",
            f"  GOVERNO DO ESTADO DE RONDÔNIA",
            f"  SECRETARIA DE ESTADO DA EDUCAÇÃO – SEDUC/RO",
            f"  {unidade.nome.upper()}",
            (f"  Endereço: {unidade.endereco}  –  {municipio}"
             if unidade.endereco else f"  {municipio}"),
            f"{'=' * W}",
            f"",
            f"  {self.numero_documento}",
            f"",
            f"  {self.titulo.upper():^{W - 4}}",
            f"",
            f"{'─' * W}",
            f"",
            f"  {self.abertura}",
            f"",
            f"  LOCAL   : {self.local_reuniao}",
            f"  DATA    : {self._data_pt(self.data_reuniao)}",
            f"  HORÁRIO : {hora_ini} às {hora_fim}",
            f"",
            f"  MEMBROS PRESENTES:",
            membros_fmt,
            f"",
            f"{'─' * W}",
            f"",
            f"  DELIBERAÇÕES:",
            f"",
            f"  {self.deliberacoes}",
            f"",
            f"{'─' * W}",
            f"",
            f"  RESULTADO FINAL POR ALUNO",
            f"  Turma: {self.conselho.turma.nome}   Curso: {self.conselho.turma.curso.nome}"
            f"   Período: {self.conselho.periodo}",
            f"",
            f"  {'N°':>3}  {'NOME DO ALUNO':<38}  {'MÉDIA':>6}  {'FREQ%':>6}  {'RESULTADO':<25}",
            f"  {'─' * 3}  {'─' * 38}  {'─' * 6}  {'─' * 6}  {'─' * 25}",
        ]

        for i, mat in enumerate(matriculas, 1):
            nome  = mat.aluno.get_full_name().upper()[:38]
            media, freq, result = _res(mat)
            doc.append(f"  {i:3d}  {nome:<38}  {media:>6}  {freq:>6}  {result:<25}")

        doc += [
            f"  {'─' * W}",
            f"",
            f"  {self.encerramento}",
            f"",
            f"  {municipio}, {self._data_pt(self.data_reuniao)}",
            f"",
            f"",
            f"  {'─' * 38}          {'─' * 38}",
            f"  {pres_nome:<38}          {sec_nome:<38}",
            f"  Presidente do Conselho de Classe          Secretário(a) Escolar",
            f"",
        ]

        outros = membros_lines[2:]
        if outros:
            doc.append(f"  Demais Membros Presentes:")
            for j in range(0, len(outros), 2):
                par = outros[j:j + 2]
                sigs = '  '.join(['─' * 35] * len(par))
                noms = '  '.join([f'{p:<35}' for p in par])
                doc += [f"  {sigs}", f"  {noms}"]
            doc.append(f"")

        doc.append(f"{'=' * W}")
        return '\n'.join(doc)

    def __str__(self):
        return f'{self.numero_documento} – {self.titulo}'


# ── Documento Oficial: Diploma Escolar ───────────────────────────────────────

class DiplomaEscolar(models.Model):
    """
    Documento formal do Diploma/Certificado de Conclusão para impressão
    e registro oficial. Gerado a partir do CertificadoDiploma com todos
    os dados necessários para validade legal.
    """

    certificado     = models.OneToOneField(
        CertificadoDiploma, on_delete=models.CASCADE,
        related_name='diploma_escolar',
        verbose_name='Certificado / Diploma',
    )
    numero_diploma  = models.CharField(max_length=25, unique=True, editable=False, verbose_name='Nº do Diploma')
    codigo_verificacao = models.CharField(max_length=36, unique=True, editable=False, verbose_name='Código de Verificação')

    # Dados do aluno (copiados na emissão para garantir imutabilidade)
    nome_completo   = models.CharField(max_length=200, verbose_name='Nome Completo do Aluno')
    data_nascimento = models.DateField(verbose_name='Data de Nascimento')
    local_nascimento = models.CharField(max_length=100, verbose_name='Local de Nascimento')
    nome_pai        = models.CharField(max_length=200, blank=True, verbose_name='Nome do Pai')
    nome_mae        = models.CharField(max_length=200, blank=True, verbose_name='Nome da Mãe')
    cpf             = models.CharField(max_length=14, verbose_name='CPF')
    rg              = models.CharField(max_length=20, blank=True, verbose_name='RG')

    # Dados do curso (copiados na emissão)
    curso_nome      = models.CharField(max_length=200, verbose_name='Curso')
    habilitacao     = models.CharField(max_length=200, blank=True, verbose_name='Habilitação')
    carga_horaria   = models.PositiveIntegerField(verbose_name='Carga Horária Total (h)')
    data_inicio_curso  = models.DateField(verbose_name='Data de Início do Curso')
    data_conclusao  = models.DateField(verbose_name='Data de Conclusão')
    media_final     = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='Média Final')

    # Dados da unidade
    unidade_nome    = models.CharField(max_length=200, verbose_name='Unidade Escolar')
    municipio_uf    = models.CharField(max_length=100, verbose_name='Município/UF')

    # Assinaturas
    diretor_nome    = models.CharField(max_length=200, verbose_name='Nome do Diretor(a)')
    diretor_cargo   = models.CharField(max_length=100, default='Diretor(a)', verbose_name='Cargo do Diretor(a)')
    secretario_nome = models.CharField(max_length=200, verbose_name='Nome do(a) Secretário(a) Escolar')

    data_emissao    = models.DateField(verbose_name='Data de Emissão')

    class Meta:
        verbose_name = 'Diploma Escolar'
        verbose_name_plural = 'Diplomas Escolares'
        ordering = ['-data_emissao']

    def save(self, *args, **kwargs):
        if not self.numero_diploma:
            from django.utils import timezone
            ano = timezone.now().year
            ultimo = DiplomaEscolar.objects.filter(
                numero_diploma__startswith=f'DIP-{ano}-'
            ).order_by('-numero_diploma').first()
            seq = 1
            if ultimo:
                try:
                    seq = int(ultimo.numero_diploma.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    seq = DiplomaEscolar.objects.filter(
                        numero_diploma__startswith=f'DIP-{ano}-'
                    ).count() + 1
            self.numero_diploma = f'DIP-{ano}-{seq:04d}'
        if not self.codigo_verificacao:
            import uuid
            self.codigo_verificacao = str(uuid.uuid4()).upper()
        super().save(*args, **kwargs)

    @staticmethod
    def _data_pt(d) -> str:
        meses = ['janeiro','fevereiro','março','abril','maio','junho',
                 'julho','agosto','setembro','outubro','novembro','dezembro']
        return f'{d.day:02d} de {meses[d.month - 1]} de {d.year}'

    def gerar_documento(self) -> str:
        """Retorna o texto formatado completo do diploma para impressão."""
        media_str = f'{self.media_final:.2f}' if self.media_final else 'N/A'
        pai_mae = ''
        if self.nome_pai or self.nome_mae:
            partes = []
            if self.nome_pai:
                partes.append(f'pai: {self.nome_pai}')
            if self.nome_mae:
                partes.append(f'mãe: {self.nome_mae}')
            pai_mae = f"\n  Filiação      : {' | '.join(partes)}"

        W = 92
        doc = [
            f"\n{'=' * W}",
            f"  GOVERNO DO ESTADO DE RONDÔNIA",
            f"  SECRETARIA DE ESTADO DA EDUCAÇÃO – SEDUC/RO",
            f"  {self.unidade_nome.upper()}",
            f"  {self.municipio_uf}",
            f"{'=' * W}",
            f"",
            f"  Nº {self.numero_diploma}",
            f"  Código de Verificação: {self.codigo_verificacao}",
            f"",
            f"  {'C E R T I F I C A D O   D E   C O N C L U S Ã O   D E   C U R S O   T É C N I C O':^{W - 4}}",
            f"",
            f"{'─' * W}",
            f"",
            f"  A {self.unidade_nome},",
            f"  situada em {self.municipio_uf},",
            f"  CERTIFICA que",
            f"",
            f"  {'*' * 3} {self.nome_completo.upper()} {'*' * 3}",
            f"",
            f"  nascido(a) em {self.data_nascimento.strftime('%d/%m/%Y')}, em {self.local_nascimento},{pai_mae}",
            f"  CPF: {self.cpf}" + (f"  |  RG: {self.rg}" if self.rg else ""),
            f"",
            f"  concluiu com aproveitamento o Curso Técnico de Nível Médio em",
            f"",
            f"  {'*' * 3} {self.curso_nome.upper()} {'*' * 3}",
        ]
        if self.habilitacao:
            doc.append(f"  Habilitação: {self.habilitacao}")
        doc += [
            f"",
            f"  Carga Horária Total : {self.carga_horaria} horas",
            f"  Período             : {self.data_inicio_curso.strftime('%d/%m/%Y')}"
            f" a {self.data_conclusao.strftime('%d/%m/%Y')}",
            f"  Média Final         : {media_str}",
            f"",
            f"{'─' * W}",
            f"",
            f"  {self.municipio_uf}, {self._data_pt(self.data_emissao)}",
            f"",
            f"",
            f"  {'─' * 38}          {'─' * 38}",
            f"  {self.diretor_nome:<38}          {self.secretario_nome:<38}",
            f"  {self.diretor_cargo:<38}          Secretário(a) Escolar",
            f"",
            f"{'=' * W}",
        ]
        return '\n'.join(doc)

    def __str__(self):
        return f'{self.numero_diploma} – {self.nome_completo} – {self.curso_nome}'


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
