"""
Auditoria – LogAuditoria: rastreia quem fez o quê, quando e em qual objeto.
Cobre o requisito 'LogAuditoria (quem/quando/o quê)' do Class Diagram.
"""

from django.conf import settings
from django.db import models


class LogAuditoria(models.Model):
    """Registro imutável de cada ação relevante realizada no sistema."""

    ACAO_CHOICES = (
        ('CRIACAO',       'Criação'),
        ('EDICAO',        'Edição'),
        ('EXCLUSAO',      'Exclusão'),
        ('VISUALIZACAO',  'Visualização'),
        ('LOGIN',         'Login'),
        ('LOGOUT',        'Logout'),
        ('AVANCO_FLUXO',  'Avanço de Fluxo'),
        ('OUTRO',         'Outro'),
    )

    usuario    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='logs_auditoria',
        verbose_name='Usuário',
    )
    acao       = models.CharField(max_length=20, choices=ACAO_CHOICES, verbose_name='Ação')
    modelo     = models.CharField(max_length=100, blank=True, verbose_name='Modelo / Entidade')
    objeto_id  = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID do Objeto')
    descricao  = models.TextField(blank=True, verbose_name='Descrição da Ação')
    dados      = models.JSONField(null=True, blank=True, verbose_name='Dados (JSON)')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='Endereço IP')
    data       = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')

    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-data']

    def __str__(self):
        return f'[{self.data:%d/%m/%Y %H:%M}] {self.get_acao_display()} – {self.usuario} – {self.modelo}'

    @classmethod
    def registrar(cls, usuario, acao, modelo='', objeto_id=None, descricao='', dados=None, request=None):
        """Helper para criar um log a partir de qualquer view."""
        ip = None
        if request:
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
        cls.objects.create(
            usuario=usuario,
            acao=acao,
            modelo=modelo,
            objeto_id=objeto_id,
            descricao=descricao,
            dados=dados,
            ip_address=ip,
        )
