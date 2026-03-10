from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


def seed_categories(apps, schema_editor):
    NotificacaoCategoria = apps.get_model("notificacoes", "NotificacaoCategoria")
    categories = [
        {
            "slug": "alerta-dispositivo",
            "titulo": "Alerta de dispositivo desconhecido",
            "descricao": "Notificações de acesso a partir de dispositivo ou IP não reconhecido.",
            "icone": "shield-alert",
            "ordem": 10,
            "ativa": True,
        },
        {
            "slug": "processos",
            "titulo": "Processos e requerimentos",
            "descricao": "Atualizações sobre abertura, tramitação e conclusão de processos.",
            "icone": "file-stack",
            "ordem": 20,
            "ativa": True,
        },
        {
            "slug": "documentos",
            "titulo": "Documentos acadêmicos",
            "descricao": "Emissão, disponibilidade e andamento de documentos institucionais.",
            "icone": "file-text",
            "ordem": 30,
            "ativa": True,
        },
        {
            "slug": "sistema",
            "titulo": "Sistema e segurança",
            "descricao": "Avisos gerais do sistema, autenticação e manutenção.",
            "icone": "bell-ring",
            "ordem": 40,
            "ativa": True,
        },
        {
            "slug": "rh",
            "titulo": "Gestão de Pessoas",
            "descricao": "Comunicados funcionais, férias, afastamentos e atualizações cadastrais.",
            "icone": "users",
            "ordem": 50,
            "ativa": True,
        },
    ]
    for payload in categories:
        NotificacaoCategoria.objects.update_or_create(slug=payload["slug"], defaults=payload)


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificacaoCategoria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(max_length=80, unique=True)),
                ("titulo", models.CharField(max_length=120)),
                ("descricao", models.TextField(blank=True)),
                ("icone", models.CharField(blank=True, max_length=40)),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                ("ativa", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Categoria de notificação",
                "verbose_name_plural": "Categorias de notificação",
                "ordering": ["ordem", "titulo"],
            },
        ),
        migrations.CreateModel(
            name="Notificacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=180)),
                ("resumo", models.CharField(blank=True, max_length=255)),
                ("mensagem", models.TextField()),
                ("tipo", models.CharField(choices=[("INFO", "Informação"), ("ALERTA", "Alerta"), ("SUCESSO", "Sucesso"), ("ERRO", "Erro")], default="INFO", max_length=16)),
                ("link", models.CharField(blank=True, max_length=255)),
                ("link_label", models.CharField(blank=True, max_length=80)),
                ("via_suap", models.BooleanField(default=True)),
                ("via_email", models.BooleanField(default=False)),
                ("data_evento", models.DateTimeField(default=timezone.now)),
                ("lida_em", models.DateTimeField(blank=True, null=True)),
                ("ocultada_em", models.DateTimeField(blank=True, null=True)),
                ("metadados", models.JSONField(blank=True, default=dict)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("categoria", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="notificacoes", to="notificacoes.notificacaocategoria")),
                ("usuario", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="notificacoes", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Notificação",
                "verbose_name_plural": "Notificações",
                "ordering": ["lida_em", "-data_evento", "-id"],
            },
        ),
        migrations.CreateModel(
            name="PreferenciaNotificacao",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("via_suap", models.BooleanField(default=True)),
                ("via_email", models.BooleanField(default=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("categoria", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="preferencias", to="notificacoes.notificacaocategoria")),
                ("usuario", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="preferencias_notificacao", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Preferência de notificação",
                "verbose_name_plural": "Preferências de notificação",
                "ordering": ["categoria__ordem", "categoria__titulo"],
                "unique_together": {("usuario", "categoria")},
            },
        ),
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
