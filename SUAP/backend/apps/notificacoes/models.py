from django.conf import settings
from django.db import models
from django.utils import timezone


class NotificacaoCategoria(models.Model):
    slug = models.SlugField(max_length=80, unique=True)
    titulo = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=40, blank=True)
    ordem = models.PositiveSmallIntegerField(default=0)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordem", "titulo"]
        verbose_name = "Categoria de notificação"
        verbose_name_plural = "Categorias de notificação"

    def __str__(self):
        return self.titulo


class PreferenciaNotificacao(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferencias_notificacao")
    categoria = models.ForeignKey(NotificacaoCategoria, on_delete=models.CASCADE, related_name="preferencias")
    via_suap = models.BooleanField(default=True)
    via_email = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["categoria__ordem", "categoria__titulo"]
        unique_together = ("usuario", "categoria")
        verbose_name = "Preferência de notificação"
        verbose_name_plural = "Preferências de notificação"

    def __str__(self):
        return f"{self.usuario} - {self.categoria}"


class Notificacao(models.Model):
    TIPO_CHOICES = (
        ("INFO", "Informação"),
        ("ALERTA", "Alerta"),
        ("SUCESSO", "Sucesso"),
        ("ERRO", "Erro"),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificacoes")
    categoria = models.ForeignKey(NotificacaoCategoria, on_delete=models.SET_NULL, null=True, blank=True, related_name="notificacoes")
    titulo = models.CharField(max_length=180)
    resumo = models.CharField(max_length=255, blank=True)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=16, choices=TIPO_CHOICES, default="INFO")
    link = models.CharField(max_length=255, blank=True)
    link_label = models.CharField(max_length=80, blank=True)
    via_suap = models.BooleanField(default=True)
    via_email = models.BooleanField(default=False)
    data_evento = models.DateTimeField(default=timezone.now)
    lida_em = models.DateTimeField(null=True, blank=True)
    ocultada_em = models.DateTimeField(null=True, blank=True)
    metadados = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lida_em", "-data_evento", "-id"]
        verbose_name = "Notificação"
        verbose_name_plural = "Notificações"

    def __str__(self):
        return f"{self.usuario} - {self.titulo}"

    @property
    def is_unread(self):
        return self.lida_em is None and self.ocultada_em is None
