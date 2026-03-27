from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.usuarios.models import PerfilUsuario


class AtendimentoPedagogico(models.Model):
    STATUS_CHOICES = (
        ("RISCO_REPROVACAO", "Risco de reprovacao"),
        ("RISCO_EVASAO", "Risco de evasao"),
        ("PLANO_RECUPERACAO", "Plano de recuperacao"),
        ("ACOMPANHAMENTO_PSICOPEDAGOGICO", "Acompanhamento psicopedagogico"),
        ("CONCLUIDO", "Concluido"),
    )

    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="atendimentos_pedagogicos",
        verbose_name="Aluno",
    )
    pedagogia_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="atendimentos_pedagogicos_responsavel",
        verbose_name="Pedagogia responsavel",
    )
    data_atendimento = models.DateField(default=timezone.localdate, verbose_name="Data do atendimento")
    diagnostico = models.TextField(verbose_name="Diagnostico")
    plano_acao = models.TextField(verbose_name="Plano de acao")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="RISCO_REPROVACAO", verbose_name="Status")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Atendimento pedagogico"
        verbose_name_plural = "Atendimentos pedagogicos"
        ordering = ["-data_atendimento", "-id"]

    def clean(self):
        errors = {}

        if self.aluno_id and self.aluno.tipo != PerfilUsuario.ALUNO:
            errors["aluno"] = "Selecione um usuario com perfil de aluno."

        if self.pedagogia_responsavel_id and self.pedagogia_responsavel.tipo == PerfilUsuario.ALUNO:
            errors["pedagogia_responsavel"] = "O responsavel pedagogico nao pode possuir perfil de aluno."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        aluno_nome = getattr(getattr(self.aluno, "pessoa", None), "nome_completo", "") or self.aluno.get_full_name().strip() or self.aluno.username
        return f"{aluno_nome} - {self.get_status_display()} ({self.data_atendimento:%d/%m/%Y})"
