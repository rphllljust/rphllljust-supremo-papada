"""
Captacao / Inscricao / Selecao / Convocacao
Fluxo: PublicacaoInscricao -> Inscricao -> ProcessoSeletivo -> Candidato -> Recurso
"""

from django.conf import settings
from django.db import models

from apps.cursos.models import Curso


class PublicacaoInscricao(models.Model):
    """Edital/publicacao de abertura de inscricoes para um curso."""

    MODALIDADE_INGRESSO_CHOICES = (
        ("PROCESSO_SELETIVO", "Processo Seletivo"),
        ("SORTEIO", "Sorteio"),
    )
    STATUS_CHOICES = (
        ("RASCUNHO", "Rascunho"),
        ("PUBLICADO", "Publicado"),
        ("ENCERRADO", "Encerrado"),
    )

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="publicacoes_inscricao", verbose_name="Curso")
    codigo_edital = models.CharField(max_length=60, blank=True, db_index=True, verbose_name="Codigo do Edital")
    titulo = models.CharField(max_length=255, verbose_name="Titulo do Edital")
    descricao = models.TextField(blank=True, verbose_name="Descricao / Requisitos")
    vagas = models.PositiveIntegerField(default=0, verbose_name="Numero de Vagas")
    modalidade_ingresso = models.CharField(
        max_length=20,
        choices=MODALIDADE_INGRESSO_CHOICES,
        default="PROCESSO_SELETIVO",
        verbose_name="Modalidade de Ingresso",
    )
    nota_corte = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Nota de Corte")
    usa_cotas_lei_12711 = models.BooleanField(default=True, verbose_name="Aplica Lei de Cotas")
    data_inicio = models.DateField(verbose_name="Inicio das Inscricoes")
    data_fim = models.DateField(verbose_name="Fim das Inscricoes")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="RASCUNHO", verbose_name="Status")
    publicado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="publicacoes_inscricao",
        verbose_name="Publicado por",
    )

    class Meta:
        verbose_name = "Publicacao de Inscricao"
        verbose_name_plural = "Publicacoes de Inscricao"
        ordering = ["-data_inicio"]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            raise ValidationError({"data_fim": "A data de fim deve ser posterior ao inicio."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.titulo} - {self.curso.nome} [{self.get_status_display()}]"


class Inscricao(models.Model):
    """Inscricao de um candidato em uma publicacao."""

    MODALIDADE_CONCORRENCIA_CHOICES = (
        ("AMPLA", "Ampla Concorrencia"),
        ("COTAS", "Cotas"),
    )
    STATUS_CHOICES = (
        ("PENDENTE", "Pendente de Validacao"),
        ("VALIDADA", "Validada"),
        ("INDEFERIDA", "Indeferida"),
    )
    STATUS_CANDIDATO_CHOICES = (
        ("INSCRITO", "Inscrito"),
        ("HOMOLOGADO", "Homologado"),
        ("CLASSIFICADO", "Classificado"),
        ("CONVOCADO", "Convocado"),
        ("MATRICULADO", "Matriculado"),
        ("LISTA_ESPERA", "Lista de Espera"),
        ("INDEFERIDO", "Indeferido"),
        ("DESISTENTE", "Desistente"),
    )

    publicacao = models.ForeignKey(PublicacaoInscricao, on_delete=models.CASCADE, related_name="inscricoes", verbose_name="Edital")
    nome_candidato = models.CharField(max_length=200, verbose_name="Nome do Candidato")
    cpf = models.CharField(max_length=11, verbose_name="CPF")
    email = models.EmailField(verbose_name="E-mail")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="PENDENTE", verbose_name="Status")
    modalidade_concorrencia = models.CharField(
        max_length=10,
        choices=MODALIDADE_CONCORRENCIA_CHOICES,
        default="AMPLA",
        verbose_name="Modalidade de Concorrencia",
    )
    cota_codigo_opcao = models.CharField(max_length=40, blank=True, verbose_name="Codigo da Cota")
    status_candidato = models.CharField(
        max_length=20,
        choices=STATUS_CANDIDATO_CHOICES,
        default="INSCRITO",
        verbose_name="Status do Candidato",
    )
    data_inscricao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Inscricao")
    numero_inscricao = models.CharField(max_length=20, unique=True, editable=False, verbose_name="Numero de Inscricao")
    observacao = models.TextField(blank=True, verbose_name="Observacao")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscricoes",
        verbose_name="Usuario do Sistema",
    )

    class Meta:
        verbose_name = "Inscricao"
        verbose_name_plural = "Inscricoes"
        ordering = ["-data_inscricao"]

    def save(self, *args, **kwargs):
        if not self.numero_inscricao:
            self.numero_inscricao = self._gerar_numero()
        super().save(*args, **kwargs)

    @staticmethod
    def _gerar_numero():
        from django.utils import timezone

        ano = timezone.now().year
        ultimo = Inscricao.objects.filter(numero_inscricao__startswith=f"INS-{ano}-").order_by("-numero_inscricao").first()
        seq = 1
        if ultimo:
            try:
                seq = int(ultimo.numero_inscricao.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = Inscricao.objects.filter(numero_inscricao__startswith=f"INS-{ano}-").count() + 1
        return f"INS-{ano}-{seq:04d}"

    def __str__(self):
        return f"{self.numero_inscricao} - {self.nome_candidato} [{self.get_status_display()}]"


class DocumentoInscricao(models.Model):
    """Documentos enviados junto com a inscricao."""

    TIPO_CHOICES = (
        ("RG", "RG / Documento de Identidade"),
        ("CPF", "CPF"),
        ("COMPROVANTE_RESIDENCIA", "Comprovante de Residencia"),
        ("HISTORICO_ESCOLAR", "Historico Escolar"),
        ("FOTO", "Foto 3x4"),
        ("OUTROS", "Outros"),
    )
    STATUS_VALIDACAO_CHOICES = (
        ("PENDENTE", "Pendente"),
        ("VALIDO", "Valido"),
        ("INVALIDO", "Invalido"),
    )

    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name="documentos", verbose_name="Inscricao")
    tipo = models.CharField(max_length=25, choices=TIPO_CHOICES, verbose_name="Tipo de Documento")
    entregue = models.BooleanField(default=False, verbose_name="Entregue")
    arquivo = models.FileField(upload_to="inscricoes/documentos/%Y/%m", null=True, blank=True, verbose_name="Arquivo Digital")
    status_validacao = models.CharField(
        max_length=10,
        choices=STATUS_VALIDACAO_CHOICES,
        default="PENDENTE",
        verbose_name="Status de Validacao",
    )
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_inscricao_validados",
        verbose_name="Validado por",
    )
    data_validacao = models.DateField(null=True, blank=True, verbose_name="Data de Validacao")
    justificativa_validacao = models.TextField(blank=True, verbose_name="Justificativa da Validacao")
    data_entrega = models.DateField(null=True, blank=True, verbose_name="Data de Entrega")
    observacao = models.CharField(max_length=255, blank=True, verbose_name="Observacao")

    class Meta:
        verbose_name = "Documento da Inscricao"
        verbose_name_plural = "Documentos da Inscricao"
        unique_together = ("inscricao", "tipo")

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.inscricao}"


class ProcessoSeletivo(models.Model):
    """Processo de selecao/convocacao vinculado a uma publicacao."""

    MODALIDADE_CHOICES = (
        ("SORTEIO", "Sorteio"),
        ("DEMANDA_ESPONTANEA", "Demanda Espontanea"),
        ("PROVA", "Prova"),
        ("ANALISE_CURRICULO", "Analise de Curriculo"),
        ("ENTREVISTA", "Entrevista"),
    )
    STATUS_CHOICES = (
        ("PREVISTO", "Previsto"),
        ("EM_ANDAMENTO", "Em Andamento"),
        ("CONCLUIDO", "Concluido"),
    )

    publicacao = models.OneToOneField(
        PublicacaoInscricao,
        on_delete=models.CASCADE,
        related_name="processo_seletivo",
        verbose_name="Publicacao",
    )
    modalidade = models.CharField(max_length=25, choices=MODALIDADE_CHOICES, verbose_name="Modalidade")
    data_realizacao = models.DateField(null=True, blank=True, verbose_name="Data de Realizacao")
    data_resultado = models.DateField(null=True, blank=True, verbose_name="Data do Resultado")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="PREVISTO", verbose_name="Status")
    nota_corte = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Nota de Corte")
    usa_cotas_lei_12711 = models.BooleanField(default=True, verbose_name="Aplica Lei de Cotas")
    criterios = models.TextField(blank=True, verbose_name="Criterios de Classificacao")
    resultado = models.TextField(blank=True, verbose_name="Resultado Publicado")
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processos_seletivos",
        verbose_name="Responsavel",
    )

    class Meta:
        verbose_name = "Processo Seletivo"
        verbose_name_plural = "Processos Seletivos"
        ordering = ["-data_realizacao"]

    def __str__(self):
        return f"Selecao - {self.publicacao.titulo} [{self.get_status_display()}]"


class Candidato(models.Model):
    """Candidato classificado em um processo seletivo."""

    SITUACAO_CHOICES = (
        ("CONVOCADO", "Convocado"),
        ("MATRICULADO", "Matriculado"),
        ("LISTA_ESPERA", "Lista de Espera"),
        ("RECLASSIFICADO", "Reclassificado"),
        ("NAO_COMPARECEU", "Nao Compareceu"),
        ("DESISTENTE", "Desistente"),
        ("ELIMINADO", "Eliminado"),
    )
    MODALIDADE_VAGA_CHOICES = (
        ("AMPLA", "Ampla Concorrencia"),
        ("COTAS", "Cotas"),
    )

    processo = models.ForeignKey(ProcessoSeletivo, on_delete=models.CASCADE, related_name="candidatos", verbose_name="Processo Seletivo")
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name="candidatos", verbose_name="Inscricao")
    classificacao = models.PositiveIntegerField(verbose_name="Classificacao")
    pontuacao = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Pontuacao")
    modalidade_vaga = models.CharField(
        max_length=10,
        choices=MODALIDADE_VAGA_CHOICES,
        default="AMPLA",
        verbose_name="Modalidade de Vaga",
    )
    cota_codigo = models.CharField(max_length=40, blank=True, verbose_name="Codigo da Cota")
    situacao = models.CharField(max_length=15, choices=SITUACAO_CHOICES, default="CONVOCADO", verbose_name="Situacao")
    chamada_atual = models.ForeignKey(
        "ChamadaProcessoSeletivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidatos_atuais",
        verbose_name="Chamada Atual",
    )
    data_convocacao = models.DateField(null=True, blank=True, verbose_name="Data da Convocacao")
    observacao = models.TextField(blank=True, verbose_name="Observacao")

    class Meta:
        verbose_name = "Candidato"
        verbose_name_plural = "Candidatos"
        ordering = ["classificacao"]
        unique_together = ("processo", "inscricao")

    def __str__(self):
        return f"{self.classificacao}o - {self.inscricao.nome_candidato} [{self.get_situacao_display()}]"


class CotaProcessoSeletivo(models.Model):
    """Configuracao de cotas por processo seletivo."""

    processo = models.ForeignKey(
        ProcessoSeletivo,
        on_delete=models.CASCADE,
        related_name="cotas",
        verbose_name="Processo Seletivo",
    )
    codigo = models.CharField(max_length=40, verbose_name="Codigo da Cota")
    nome = models.CharField(max_length=120, verbose_name="Nome da Cota")
    percentual_vagas = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Percentual de Vagas")
    vagas_reservadas = models.PositiveIntegerField(default=0, verbose_name="Vagas Reservadas")
    ordem_remanejamento = models.PositiveIntegerField(default=0, verbose_name="Ordem de Remanejamento")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")

    class Meta:
        verbose_name = "Cota do Processo Seletivo"
        verbose_name_plural = "Cotas do Processo Seletivo"
        ordering = ["processo_id", "ordem_remanejamento", "id"]
        unique_together = ("processo", "codigo")

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ChamadaProcessoSeletivo(models.Model):
    """Controle de chamadas regulares e reclassificacoes por processo seletivo."""

    TIPO_CHOICES = (
        ("REGULAR", "Regular"),
        ("RECLASSIFICACAO", "Reclassificacao"),
    )
    STATUS_CHOICES = (
        ("RASCUNHO", "Rascunho"),
        ("PUBLICADA", "Publicada"),
        ("ENCERRADA", "Encerrada"),
    )

    processo = models.ForeignKey(
        ProcessoSeletivo,
        on_delete=models.CASCADE,
        related_name="chamadas",
        verbose_name="Processo Seletivo",
    )
    numero = models.PositiveIntegerField(verbose_name="Numero da Chamada")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="REGULAR", verbose_name="Tipo")
    data_publicacao = models.DateField(null=True, blank=True, verbose_name="Data de Publicacao")
    prazo_matricula_inicio = models.DateField(null=True, blank=True, verbose_name="Inicio do Prazo de Matricula")
    prazo_matricula_fim = models.DateField(null=True, blank=True, verbose_name="Fim do Prazo de Matricula")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="RASCUNHO", verbose_name="Status")
    observacao = models.TextField(blank=True, verbose_name="Observacao")

    class Meta:
        verbose_name = "Chamada do Processo Seletivo"
        verbose_name_plural = "Chamadas do Processo Seletivo"
        ordering = ["processo_id", "numero", "id"]
        unique_together = ("processo", "numero")

    def __str__(self):
        return f"{self.processo.publicacao.titulo} - Chamada {self.numero}"


class ConvocacaoCandidato(models.Model):
    """Registro de convocacao de candidato em uma chamada."""

    STATUS_CHOICES = (
        ("CONVOCADO", "Convocado"),
        ("MATRICULADO", "Matriculado"),
        ("INDEFERIDO", "Indeferido"),
        ("NAO_COMPARECEU", "Nao Compareceu"),
        ("DESISTENTE", "Desistente"),
        ("RECLASSIFICADO", "Reclassificado"),
    )

    chamada = models.ForeignKey(
        ChamadaProcessoSeletivo,
        on_delete=models.CASCADE,
        related_name="convocacoes",
        verbose_name="Chamada",
    )
    candidato = models.ForeignKey(
        Candidato,
        on_delete=models.CASCADE,
        related_name="convocacoes",
        verbose_name="Candidato",
    )
    modalidade_vaga = models.CharField(max_length=10, default="AMPLA", verbose_name="Modalidade da Vaga")
    cota_codigo = models.CharField(max_length=40, blank=True, verbose_name="Codigo da Cota")
    classificacao_na_chamada = models.PositiveIntegerField(null=True, blank=True, verbose_name="Classificacao na Chamada")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="CONVOCADO", verbose_name="Status")
    data_status = models.DateField(null=True, blank=True, verbose_name="Data do Status")
    observacao = models.TextField(blank=True, verbose_name="Observacao")

    class Meta:
        verbose_name = "Convocacao de Candidato"
        verbose_name_plural = "Convocacoes de Candidatos"
        ordering = ["chamada_id", "classificacao_na_chamada", "id"]
        unique_together = ("chamada", "candidato")

    def __str__(self):
        return f"{self.candidato.inscricao.nome_candidato} - {self.chamada}"


class RecursoInscricao(models.Model):
    """Recurso apresentado por candidato contra resultado do processo seletivo."""

    STATUS_CHOICES = (
        ("ABERTO", "Aberto"),
        ("DEFERIDO", "Deferido"),
        ("INDEFERIDO", "Indeferido"),
    )

    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE, related_name="recursos", verbose_name="Candidato")
    motivo = models.TextField(verbose_name="Motivo do Recurso")
    data_recurso = models.DateField(auto_now_add=True, verbose_name="Data do Recurso")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="ABERTO", verbose_name="Status")
    resposta = models.TextField(blank=True, verbose_name="Resposta / Decisao")
    data_decisao = models.DateField(null=True, blank=True, verbose_name="Data da Decisao")
    decidido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recursos_decididos",
        verbose_name="Decidido por",
    )

    class Meta:
        verbose_name = "Recurso de Inscricao"
        verbose_name_plural = "Recursos de Inscricao"
        ordering = ["-data_recurso"]

    def __str__(self):
        return f"Recurso [{self.get_status_display()}] - {self.candidato}"
