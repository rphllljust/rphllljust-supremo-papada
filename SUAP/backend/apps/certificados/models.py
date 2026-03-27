import uuid

from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone


TEXTO_PADRAO_CERTIFICADO = (
    "O(a) [nome_da_instituicao] certifica que [nome_aluno], portador(a) do CPF [cpf_aluno], "
    "concluiu com êxito o curso [curso_nome], pertencente ao eixo tecnológico [eixo_tecnologico], "
    "com carga horária total de [carga_horaria] horas, realizado no período de [data_inicio] a [data_fim], "
    "com conclusão em [data_conclusao]."
)

CAMPO_DINAMICO_OBRIGATORIO = [
    "nome_da_instituicao",
    "sigla_instituicao",
    "brasao_instituicao",
    "logo_instituicao",
    "nome_aluno",
    "cpf_aluno",
    "rg_aluno",
    "data_nascimento",
    "curso_nome",
    "eixo_tecnologico",
    "modalidade",
    "carga_horaria",
    "data_inicio",
    "data_fim",
    "data_conclusao",
    "cidade",
    "estado",
    "data_emissao",
    "numero_certificado",
    "livro",
    "folha",
    "codigo_validacao",
    "qr_code_validacao",
    "texto_certificado",
    "nome_assinante_1",
    "cargo_assinante_1",
    "nome_assinante_2",
    "cargo_assinante_2",
    "logos_rodape",
    "marca_dagua",
]


def campos_dinamicos_padrao():
    return list(CAMPO_DINAMICO_OBRIGATORIO)


class ModeloCertificado(models.Model):
    TIPO_CHOICES = (
        ("CERTIFICADO", "Certificado"),
        ("DIPLOMA", "Diploma"),
        ("CERTIFICADO_CONCLUSAO", "Certificado de Conclusão"),
    )

    nome = models.CharField(max_length=160, unique=True)
    slug = models.SlugField(max_length=190, unique=True, editable=False)
    descricao = models.TextField(blank=True, default="")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, default="CERTIFICADO")
    curso = models.ForeignKey(
        "cursos.Curso",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modelos_certificado",
    )
    unidade = models.ForeignKey(
        "unidades.Unidade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modelos_certificado",
    )
    template_html = models.TextField(blank=True, default="")
    stylesheet_css = models.TextField(blank=True, default="")
    texto_certificado = models.TextField(default=TEXTO_PADRAO_CERTIFICADO)
    campos_dinamicos = models.JSONField(default=campos_dinamicos_padrao)
    metadados = models.JSONField(default=dict, blank=True)
    ativo = models.BooleanField(default=True)
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modelos_certificado_criados",
    )
    atualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="modelos_certificado_atualizados",
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-atualizado_em", "nome"]
        verbose_name = "Modelo de Certificado"
        verbose_name_plural = "Modelos de Certificado"

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nome) or "modelo-certificado"
            slug = base_slug
            seq = 2
            while ModeloCertificado.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{seq}"
                seq += 1
            self.slug = slug
        super().save(*args, **kwargs)


class ConfiguracaoVisualCertificado(models.Model):
    modelo = models.OneToOneField(
        ModeloCertificado,
        on_delete=models.CASCADE,
        related_name="configuracao_visual",
    )
    nome_da_instituicao = models.CharField(max_length=220, default="Instituto Estadual de Desenvolvimento da Educação Profissional de Rondônia")
    sigla_instituicao = models.CharField(max_length=20, default="IDEP")
    brasao_instituicao = models.URLField(blank=True, default="")
    logo_instituicao = models.URLField(blank=True, default="")
    logos_rodape = models.JSONField(default=list, blank=True)
    marca_dagua = models.URLField(blank=True, default="")
    cidade_padrao = models.CharField(max_length=120, default="Porto Velho")
    estado_padrao = models.CharField(max_length=2, default="RO")
    cor_primaria = models.CharField(max_length=20, default="#0b2f4b")
    cor_secundaria = models.CharField(max_length=20, default="#0f6c3d")
    cor_destaque = models.CharField(max_length=20, default="#f1c40f")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração Visual de Certificado"
        verbose_name_plural = "Configurações Visuais de Certificados"

    def __str__(self):
        return f"Visual {self.modelo.nome}"


class AssinaturaCertificado(models.Model):
    modelo = models.ForeignKey(
        ModeloCertificado,
        on_delete=models.CASCADE,
        related_name="assinaturas",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=200)
    cargo = models.CharField(max_length=140)
    imagem_assinatura = models.ImageField(upload_to="certificados/assinaturas/", null=True, blank=True)
    ordem = models.PositiveSmallIntegerField(default=1)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordem", "nome"]
        verbose_name = "Assinatura de Certificado"
        verbose_name_plural = "Assinaturas de Certificados"

    def __str__(self):
        return f"{self.nome} ({self.cargo})"


class CertificadoEmitido(models.Model):
    STATUS_CHOICES = (
        ("DIPLOMA_EM_PREPARACAO", "diploma em preparação"),
        ("DIPLOMA_REGISTRADO", "diploma registrado"),
        ("DIPLOMA_DISPONIVEL_RETIRADA", "diploma disponível para retirada"),
        ("DIPLOMA_ENTREGUE", "diploma entregue"),
        ("CERTIFICADO_CANCELADO", "certificado cancelado"),
    )

    modelo = models.ForeignKey(
        ModeloCertificado,
        on_delete=models.PROTECT,
        related_name="certificados_emitidos",
    )
    aluno = models.ForeignKey(
        "usuarios.Aluno",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_emitidos",
    )
    matricula = models.ForeignKey(
        "matriculas.Matricula",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_emitidos_v2",
    )
    curso = models.ForeignKey(
        "cursos.Curso",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_emitidos",
    )
    unidade = models.ForeignKey(
        "unidades.Unidade",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_emitidos",
    )
    turma = models.ForeignKey(
        "turmas.Turma",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_emitidos",
    )
    usuario_emissor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificados_emitidos_institucionais",
    )

    numero_certificado = models.CharField(max_length=40, unique=True, editable=False)
    livro = models.CharField(max_length=20, blank=True, default="")
    folha = models.CharField(max_length=20, blank=True, default="")
    termo = models.CharField(max_length=20, blank=True, default="")
    codigo_validacao = models.CharField(max_length=40, unique=True, editable=False)
    qr_code_validacao = models.URLField(max_length=800, blank=True, default="")
    qr_code_data_uri = models.TextField(blank=True, default="")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="DIPLOMA_EM_PREPARACAO")

    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    data_conclusao = models.DateField(null=True, blank=True)
    data_emissao = models.DateField(default=timezone.localdate)
    data_registro = models.DateField(null=True, blank=True)
    data_entrega = models.DateField(null=True, blank=True)
    cidade = models.CharField(max_length=120, blank=True, default="")
    estado = models.CharField(max_length=2, blank=True, default="")

    nome_aluno_snapshot = models.CharField(max_length=220, blank=True, default="")
    cpf_aluno_snapshot = models.CharField(max_length=14, blank=True, default="")
    curso_nome_snapshot = models.CharField(max_length=220, blank=True, default="")
    texto_certificado_snapshot = models.TextField(blank=True, default="")
    dados_dinamicos = models.JSONField(default=dict, blank=True)

    reimpressoes = models.PositiveIntegerField(default=0)
    ultima_reimpressao_em = models.DateTimeField(null=True, blank=True)
    pdf_arquivo = models.FileField(upload_to="certificados/pdfs/", null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "Certificado Emitido"
        verbose_name_plural = "Certificados Emitidos"

    def __str__(self):
        return f"{self.numero_certificado} - {self.nome_aluno_snapshot or 'Aluno'}"

    @classmethod
    def gerar_numero_certificado(cls):
        ano = timezone.now().year
        prefixo = f"CERT-{ano}-"
        ultimo = (
            cls.objects
            .filter(numero_certificado__startswith=prefixo)
            .order_by("-numero_certificado")
            .first()
        )
        sequencial = 1
        if ultimo:
            try:
                sequencial = int(ultimo.numero_certificado.split("-")[-1]) + 1
            except (ValueError, IndexError):
                sequencial = cls.objects.filter(numero_certificado__startswith=prefixo).count() + 1
        return f"{prefixo}{sequencial:06d}"

    @classmethod
    def gerar_codigo_validacao(cls):
        while True:
            codigo = uuid.uuid4().hex[:20].upper()
            if not cls.objects.filter(codigo_validacao=codigo).exists():
                return codigo

    def save(self, *args, **kwargs):
        if not self.numero_certificado:
            self.numero_certificado = self.gerar_numero_certificado()
        if not self.codigo_validacao:
            self.codigo_validacao = self.gerar_codigo_validacao()
        super().save(*args, **kwargs)


class HistoricoEmissaoCertificado(models.Model):
    ACAO_CHOICES = (
        ("EMISSAO", "Emissão"),
        ("EMISSAO_LOTE", "Emissão em lote"),
        ("PREVIEW", "Pré-visualização"),
        ("GERACAO_PDF", "Geração de PDF"),
        ("REIMPRESSAO", "Reimpressão"),
        ("VALIDACAO_PUBLICA", "Validação pública"),
        ("ALTERACAO_MODELO", "Alteração de modelo"),
        ("ALTERACAO_STATUS", "Alteração de status"),
    )

    certificado = models.ForeignKey(
        CertificadoEmitido,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historico_emissao",
    )
    modelo = models.ForeignKey(
        ModeloCertificado,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historico_emissao",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historico_emissao_certificados",
    )
    acao = models.CharField(max_length=30, choices=ACAO_CHOICES)
    descricao = models.TextField(blank=True, default="")
    dados = models.JSONField(default=dict, blank=True)
    ip_origem = models.GenericIPAddressField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "Histórico de Emissão de Certificado"
        verbose_name_plural = "Históricos de Emissão de Certificados"

    def __str__(self):
        return f"{self.get_acao_display()} em {self.criado_em:%d/%m/%Y %H:%M}"
