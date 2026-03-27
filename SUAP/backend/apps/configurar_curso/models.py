from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EstruturaCurso(TimeStampedModel):
    nome = models.CharField(max_length=150, unique=True)
    descricao = models.TextField(blank=True, default="")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "id"]
        verbose_name = "Estrutura de curso"
        verbose_name_plural = "Estruturas de curso"

    def save(self, *args, **kwargs):
        self.nome = (self.nome or "").strip()
        self.descricao = (self.descricao or "").strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome


class MatrizCurricular(TimeStampedModel):
    nome = models.CharField(max_length=180)
    codigo = models.CharField(max_length=60)
    versao = models.CharField(max_length=20)
    carga_horaria_total = models.PositiveIntegerField()
    estrutura_curso = models.ForeignKey(
        EstruturaCurso,
        on_delete=models.PROTECT,
        related_name="matrizes_curriculares",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "versao", "id"]
        verbose_name = "Matriz curricular"
        verbose_name_plural = "Matrizes curriculares"
        constraints = [
            models.UniqueConstraint(fields=["codigo", "versao"], name="uniq_config_curso_matriz_codigo_versao"),
        ]

    def clean(self):
        errors = {}

        self.nome = (self.nome or "").strip()
        self.codigo = (self.codigo or "").strip()
        self.versao = (self.versao or "").strip()

        if not self.nome:
            errors["nome"] = "Informe o nome da matriz curricular."

        if not self.codigo:
            errors["codigo"] = "Informe o codigo da matriz curricular."

        if not self.versao:
            errors["versao"] = "Informe a versao da matriz curricular."

        if (self.carga_horaria_total or 0) <= 0:
            errors["carga_horaria_total"] = "A carga horaria total deve ser maior que zero."

        if not self.estrutura_curso_id:
            errors["estrutura_curso"] = "A matriz curricular depende de uma estrutura de curso."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome} (v{self.versao})"


class ComponenteCurricular(TimeStampedModel):
    TIPO_OBRIGATORIO = "OBRIGATORIO"
    TIPO_OPTATIVO = "OPTATIVO"
    TIPO_PRATICO = "PRATICO"

    TIPO_CHOICES = (
        (TIPO_OBRIGATORIO, "Obrigatorio"),
        (TIPO_OPTATIVO, "Optativo"),
        (TIPO_PRATICO, "Pratico"),
    )

    codigo = models.CharField(max_length=60, unique=True)
    nome = models.CharField(max_length=180)
    carga_horaria = models.PositiveIntegerField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default=TIPO_OBRIGATORIO)
    ementa = models.TextField(blank=True, default="")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "id"]
        verbose_name = "Componente curricular"
        verbose_name_plural = "Componentes curriculares"

    def clean(self):
        errors = {}

        self.codigo = (self.codigo or "").strip()
        self.nome = (self.nome or "").strip()
        self.ementa = (self.ementa or "").strip()

        if not self.codigo:
            errors["codigo"] = "Informe o codigo do componente curricular."

        if not self.nome:
            errors["nome"] = "Informe o nome do componente curricular."

        if (self.carga_horaria or 0) <= 0:
            errors["carga_horaria"] = "A carga horaria deve ser maior que zero."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class MatrizComponente(models.Model):
    matriz_curricular = models.ForeignKey(
        MatrizCurricular,
        on_delete=models.CASCADE,
        related_name="componentes_vinculados",
    )
    componente_curricular = models.ForeignKey(
        ComponenteCurricular,
        on_delete=models.PROTECT,
        related_name="matrizes_vinculadas",
    )
    periodo = models.PositiveSmallIntegerField()
    carga_horaria = models.PositiveIntegerField()
    obrigatorio = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=1)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["matriz_curricular_id", "periodo", "ordem", "id"]
        verbose_name = "Vinculo matriz x componente"
        verbose_name_plural = "Vinculos matriz x componente"
        constraints = [
            models.UniqueConstraint(
                fields=["matriz_curricular", "componente_curricular"],
                name="uniq_config_curso_matriz_componente",
            ),
            models.UniqueConstraint(
                fields=["matriz_curricular", "periodo", "ordem"],
                name="uniq_config_curso_matriz_periodo_ordem",
            ),
        ]

    def clean(self):
        errors = {}

        if (self.periodo or 0) <= 0:
            errors["periodo"] = "Informe um periodo valido."

        if (self.carga_horaria or 0) <= 0:
            errors["carga_horaria"] = "A carga horaria deve ser maior que zero."

        if (self.ordem or 0) <= 0:
            errors["ordem"] = "A ordem deve ser maior que zero."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.carga_horaria and self.componente_curricular_id:
            self.carga_horaria = self.componente_curricular.carga_horaria

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.matriz_curricular} - {self.componente_curricular}"


class PreRequisito(models.Model):
    componente = models.ForeignKey(
        ComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="pre_requisitos",
    )
    requisito = models.ForeignKey(
        ComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="e_requisito_de",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["componente_id", "requisito_id"]
        verbose_name = "Pre-requisito"
        verbose_name_plural = "Pre-requisitos"
        constraints = [
            models.UniqueConstraint(
                fields=["componente", "requisito"],
                name="uniq_config_curso_prerequisito",
            ),
            models.CheckConstraint(
                condition=~Q(componente=models.F("requisito")),
                name="chk_config_curso_prerequisito_no_self",
            ),
        ]

    def __str__(self):
        return f"{self.componente} <- {self.requisito}"


class CoRequisito(models.Model):
    componente = models.ForeignKey(
        ComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="co_requisitos",
    )
    requisito = models.ForeignKey(
        ComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="e_co_requisito_de",
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["componente_id", "requisito_id"]
        verbose_name = "Co-requisito"
        verbose_name_plural = "Co-requisitos"
        constraints = [
            models.UniqueConstraint(
                fields=["componente", "requisito"],
                name="uniq_config_curso_corequisito",
            ),
            models.CheckConstraint(
                condition=~Q(componente=models.F("requisito")),
                name="chk_config_curso_corequisito_no_self",
            ),
        ]

    def __str__(self):
        return f"{self.componente} <-> {self.requisito}"


class Curso(TimeStampedModel):
    SITUACAO_EM_CONFIGURACAO = "EM_CONFIGURACAO"
    SITUACAO_ATIVO = "ATIVO"
    SITUACAO_INATIVO = "INATIVO"

    SITUACAO_CHOICES = (
        (SITUACAO_EM_CONFIGURACAO, "Em configuracao"),
        (SITUACAO_ATIVO, "Ativo"),
        (SITUACAO_INATIVO, "Inativo"),
    )

    MODALIDADE_PRESENCIAL = "PRESENCIAL"
    MODALIDADE_EAD = "EAD"
    MODALIDADE_HIBRIDO = "HIBRIDO"

    MODALIDADE_CHOICES = (
        (MODALIDADE_PRESENCIAL, "Presencial"),
        (MODALIDADE_EAD, "EAD"),
        (MODALIDADE_HIBRIDO, "Hibrido"),
    )

    codigo = models.CharField(max_length=60, unique=True)
    nome = models.CharField(max_length=180)
    nome_curto = models.CharField(max_length=80)
    modalidade = models.CharField(max_length=20, choices=MODALIDADE_CHOICES, default=MODALIDADE_PRESENCIAL)
    carga_horaria_total = models.PositiveIntegerField()
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default=SITUACAO_EM_CONFIGURACAO)
    matriz_curricular = models.ForeignKey(
        MatrizCurricular,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="cursos",
    )
    estrutura_curso = models.ForeignKey(
        EstruturaCurso,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cursos",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "id"]
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    def clean(self):
        errors = {}

        self.codigo = (self.codigo or "").strip()
        self.nome = (self.nome or "").strip()
        self.nome_curto = (self.nome_curto or "").strip()

        if not self.codigo:
            errors["codigo"] = "Informe o codigo do curso."

        if not self.nome:
            errors["nome"] = "Informe o nome do curso."

        if not self.nome_curto:
            errors["nome_curto"] = "Informe o nome curto do curso."

        if (self.carga_horaria_total or 0) <= 0:
            errors["carga_horaria_total"] = "A carga horaria total deve ser maior que zero."

        if self.matriz_curricular_id and self.estrutura_curso_id:
            if self.matriz_curricular.estrutura_curso_id != self.estrutura_curso_id:
                errors["estrutura_curso"] = "A estrutura do curso deve ser compativel com a matriz vinculada."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.matriz_curricular_id and not self.estrutura_curso_id:
            self.estrutura_curso = self.matriz_curricular.estrutura_curso

        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Coordenador(TimeStampedModel):
    nome = models.CharField(max_length=180)
    email = models.EmailField(unique=True)
    matricula = models.CharField(max_length=40, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome", "id"]
        verbose_name = "Coordenador"
        verbose_name_plural = "Coordenadores"

    def save(self, *args, **kwargs):
        self.nome = (self.nome or "").strip()
        self.email = (self.email or "").strip().lower()
        self.matricula = (self.matricula or "").strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.matricula})"


class CursoCoordenador(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="vinculos_coordenadores")
    coordenador = models.ForeignKey(Coordenador, on_delete=models.CASCADE, related_name="vinculos_cursos")
    principal = models.BooleanField(default=False)
    inicio_vigencia = models.DateField()
    fim_vigencia = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-principal", "-inicio_vigencia", "id"]
        verbose_name = "Vinculo curso x coordenador"
        verbose_name_plural = "Vinculos curso x coordenador"
        constraints = [
            models.UniqueConstraint(
                fields=["curso", "coordenador", "inicio_vigencia"],
                name="uniq_config_curso_coordenador_vigencia",
            ),
            models.UniqueConstraint(
                fields=["curso"],
                condition=Q(principal=True, fim_vigencia__isnull=True),
                name="uniq_config_curso_coordenador_principal_ativo",
            ),
        ]

    def clean(self):
        errors = {}

        if self.fim_vigencia and self.inicio_vigencia and self.fim_vigencia < self.inicio_vigencia:
            errors["fim_vigencia"] = "A fim de vigencia nao pode ser anterior ao inicio de vigencia."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.curso} - {self.coordenador}"


class ConfiguracaoCursoWizard(TimeStampedModel):
    ETAPA_ESTRUTURA = "estrutura"
    ETAPA_MATRIZ = "matriz"
    ETAPA_COMPONENTES = "componentes"
    ETAPA_REQUISITOS = "requisitos"
    ETAPA_CURSO = "curso"
    ETAPA_COORDENADORES = "coordenadores"
    ETAPA_RESUMO = "resumo"
    ETAPA_CONCLUIDO = "concluido"

    ETAPA_CHOICES = (
        (ETAPA_ESTRUTURA, "Estrutura de curso"),
        (ETAPA_MATRIZ, "Matriz curricular"),
        (ETAPA_COMPONENTES, "Componentes"),
        (ETAPA_REQUISITOS, "Requisitos"),
        (ETAPA_CURSO, "Curso"),
        (ETAPA_COORDENADORES, "Coordenadores"),
        (ETAPA_RESUMO, "Resumo"),
        (ETAPA_CONCLUIDO, "Concluido"),
    )

    STATUS_RASCUNHO = "rascunho"
    STATUS_EM_ANDAMENTO = "em_andamento"
    STATUS_CONCLUIDO = "concluido"

    STATUS_CHOICES = (
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_EM_ANDAMENTO, "Em andamento"),
        (STATUS_CONCLUIDO, "Concluido"),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="configuracoes_curso_wizard",
    )
    etapa_atual = models.CharField(max_length=20, choices=ETAPA_CHOICES, default=ETAPA_ESTRUTURA)
    estrutura_curso = models.ForeignKey(
        EstruturaCurso,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wizards",
    )
    matriz_curricular = models.ForeignKey(
        MatrizCurricular,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wizards",
    )
    curso = models.ForeignKey(
        Curso,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wizards",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    payload_parcial = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-atualizado_em", "-id"]
        verbose_name = "Configuracao de curso (wizard)"
        verbose_name_plural = "Configuracoes de curso (wizard)"

    def __str__(self):
        return f"Wizard #{self.id} - {self.get_status_display()}"


class Auditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="auditorias_configurar_curso",
    )
    acao = models.CharField(max_length=60)
    entidade = models.CharField(max_length=120)
    entidade_id = models.PositiveBigIntegerField()
    dados_anteriores = models.JSONField(default=dict, blank=True)
    dados_novos = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "Auditoria configurar curso"
        verbose_name_plural = "Auditoria configurar curso"

    def __str__(self):
        return f"{self.acao} - {self.entidade}#{self.entidade_id}"
