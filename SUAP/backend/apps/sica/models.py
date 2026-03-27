from django.core.exceptions import ValidationError
from django.db import models

from apps.cursos.models import Curso


class SicaMatrizCurricular(models.Model):
    STATUS_CHOICES = (
        ("RASCUNHO", "Rascunho"),
        ("VIGENTE", "Vigente"),
        ("ARQUIVADA", "Arquivada"),
    )

    curso = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name="sica_matrizes",
        verbose_name="Curso",
    )
    versao = models.CharField(max_length=30, verbose_name="Versao")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="RASCUNHO", verbose_name="Status")
    descricao = models.CharField(max_length=255, blank=True, default="", verbose_name="Descricao")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Matriz Curricular SICA"
        verbose_name_plural = "Matrizes Curriculares SICA"
        ordering = ["curso__nome", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["curso", "versao"], name="uniq_sica_matriz_curso_versao"),
        ]

    def clean(self):
        self.versao = (self.versao or "").strip()
        self.descricao = (self.descricao or "").strip()
        if not self.versao:
            raise ValidationError({"versao": "Informe a versao da matriz curricular."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.curso.nome} - v{self.versao}"


class SicaComponenteCurricular(models.Model):
    TIPO_CHOICES = (
        ("OBRIGATORIO", "Obrigatorio"),
        ("OPTATIVO", "Optativo"),
        ("PRATICO", "Pratico"),
    )

    matriz = models.ForeignKey(
        SicaMatrizCurricular,
        on_delete=models.CASCADE,
        related_name="componentes",
        verbose_name="Matriz Curricular",
    )
    periodo = models.PositiveSmallIntegerField(verbose_name="Periodo")
    componente = models.CharField(max_length=200, verbose_name="Componente")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="OBRIGATORIO", verbose_name="Tipo do componente")
    carga_horaria = models.PositiveIntegerField(verbose_name="Carga horaria")
    ementa = models.TextField(blank=True, default="", verbose_name="Ementa")
    prerequisitos = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="SicaPreRequisito",
        related_name="e_prerequisito_de",
        blank=True,
    )
    equivalencias = models.ManyToManyField(
        "self",
        symmetrical=False,
        through="SicaEquivalencia",
        related_name="equivalente_de",
        blank=True,
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Componente Curricular SICA"
        verbose_name_plural = "Componentes Curriculares SICA"
        ordering = ["periodo", "componente", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "periodo", "componente"],
                name="uniq_sica_componente_matriz_periodo_nome",
            ),
        ]

    def clean(self):
        self.componente = (self.componente or "").strip()
        self.ementa = (self.ementa or "").strip()

        errors = {}

        if not self.componente:
            errors["componente"] = "Informe o nome do componente."

        if (self.periodo or 0) <= 0:
            errors["periodo"] = "Informe um periodo valido."

        if (self.carga_horaria or 0) <= 0:
            errors["carga_horaria"] = "A carga horaria deve ser maior que zero."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def curso(self):
        return self.matriz.curso

    def __str__(self):
        return f"{self.componente} ({self.matriz})"


class SicaPreRequisito(models.Model):
    componente = models.ForeignKey(
        SicaComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="relacoes_prerequisito",
    )
    prerequisito = models.ForeignKey(
        SicaComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="relacoes_dependencia",
    )

    class Meta:
        verbose_name = "Pre-requisito SICA"
        verbose_name_plural = "Pre-requisitos SICA"
        constraints = [
            models.UniqueConstraint(
                fields=["componente", "prerequisito"],
                name="uniq_sica_prerequisito",
            ),
        ]

    def clean(self):
        errors = {}
        if self.componente_id == self.prerequisito_id:
            errors["prerequisito"] = "Um componente nao pode ser pre-requisito de si mesmo."

        if self.componente_id and self.prerequisito_id and self.componente.matriz_id != self.prerequisito.matriz_id:
            errors["prerequisito"] = "Pre-requisitos devem pertencer a mesma matriz curricular."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.componente} <- {self.prerequisito}"


class SicaEquivalencia(models.Model):
    componente = models.ForeignKey(
        SicaComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="relacoes_equivalencia_origem",
    )
    equivalente = models.ForeignKey(
        SicaComponenteCurricular,
        on_delete=models.CASCADE,
        related_name="relacoes_equivalencia_destino",
    )

    class Meta:
        verbose_name = "Equivalencia SICA"
        verbose_name_plural = "Equivalencias SICA"
        constraints = [
            models.UniqueConstraint(
                fields=["componente", "equivalente"],
                name="uniq_sica_equivalencia",
            ),
        ]

    def clean(self):
        errors = {}
        if self.componente_id == self.equivalente_id:
            errors["equivalente"] = "Um componente nao pode ser equivalente a si mesmo."

        if self.componente_id and self.equivalente_id and self.componente.matriz.curso_id != self.equivalente.matriz.curso_id:
            errors["equivalente"] = "Equivalencias devem pertencer ao mesmo curso."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.componente} ~= {self.equivalente}"
