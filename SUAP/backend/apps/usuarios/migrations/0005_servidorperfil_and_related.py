from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("setores", "0001_initial"),
        ("usuarios", "0004_usuario_setor"),
    ]

    operations = [
        migrations.CreateModel(
            name="ServidorPerfil",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("matricula_servidor", models.CharField(max_length=20, unique=True)),
                ("nome_usual", models.CharField(blank=True, max_length=120)),
                ("email_institucional", models.EmailField(blank=True, max_length=254)),
                ("email_siape", models.EmailField(blank=True, max_length=254)),
                ("email_secundario_recuperacao", models.EmailField(blank=True, max_length=254)),
                ("email_notificacoes", models.EmailField(blank=True, max_length=254)),
                ("email_google_sala", models.EmailField(blank=True, max_length=254)),
                ("telefones_institucionais", models.CharField(blank=True, max_length=255)),
                ("telefones_pessoais", models.CharField(blank=True, max_length=255)),
                ("em_pgd", models.BooleanField(default=False)),
                ("nao_tem_impressao_digital", models.BooleanField(default=False)),
                ("estado_civil", models.CharField(blank=True, max_length=80)),
                ("naturalidade", models.CharField(blank=True, max_length=120)),
                ("sexo", models.CharField(blank=True, max_length=30)),
                ("grupo_sanguineo_rh", models.CharField(blank=True, max_length=20)),
                ("dependentes_ir", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("raca_etnia", models.CharField(blank=True, max_length=80)),
                ("nome_pai", models.CharField(blank=True, max_length=200)),
                ("nome_mae", models.CharField(blank=True, max_length=200)),
                ("pis_pasep", models.CharField(blank=True, max_length=40)),
                ("titulacao", models.CharField(blank=True, max_length=120)),
                ("escolaridade", models.CharField(blank=True, max_length=120)),
                ("identidade", models.CharField(blank=True, max_length=40)),
                ("orgao_expedidor", models.CharField(blank=True, max_length=80)),
                ("uf_rg", models.CharField(blank=True, max_length=2)),
                ("data_expedicao", models.DateField(blank=True, null=True)),
                ("titulo_eleitor_numero", models.CharField(blank=True, max_length=40)),
                ("titulo_eleitor_zona", models.CharField(blank=True, max_length=20)),
                ("titulo_eleitor_secao", models.CharField(blank=True, max_length=20)),
                ("titulo_eleitor_uf", models.CharField(blank=True, max_length=2)),
                ("posicao_atual", models.CharField(blank=True, max_length=120)),
                ("cargo_atual", models.CharField(blank=True, max_length=120)),
                ("jornada_trabalho", models.CharField(blank=True, max_length=80)),
                ("classe_funcional", models.CharField(blank=True, max_length=80)),
                ("nivel_funcional", models.CharField(blank=True, max_length=80)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
                ("usuario", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="perfil_servidor", to="usuarios.usuario")),
            ],
            options={"ordering": ["usuario__pessoa__nome_completo", "usuario__username"]},
        ),
        migrations.CreateModel(
            name="ServidorHistoricoFuncional",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=160)),
                ("tipo_evento", models.CharField(blank=True, max_length=80)),
                ("data_evento", models.DateField(default=django.utils.timezone.now)),
                ("descricao", models.TextField(blank=True)),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historico_funcional", to="usuarios.servidorperfil")),
            ],
            options={"ordering": ["-data_evento", "-id"]},
        ),
        migrations.CreateModel(
            name="ServidorOcorrenciaAfastamento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("titulo", models.CharField(max_length=160)),
                ("tipo", models.CharField(choices=[("OCORRENCIA", "Ocorrencia"), ("AFASTAMENTO", "Afastamento"), ("LICENCA", "Licenca"), ("CESSAO", "Cessao")], default="OCORRENCIA", max_length=20)),
                ("situacao", models.CharField(choices=[("ATIVO", "Ativo"), ("ENCERRADO", "Encerrado"), ("PROGRAMADO", "Programado")], default="ATIVO", max_length=20)),
                ("data_inicio", models.DateField(default=django.utils.timezone.now)),
                ("data_fim", models.DateField(blank=True, null=True)),
                ("descricao", models.TextField(blank=True)),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ocorrencias_afastamentos", to="usuarios.servidorperfil")),
            ],
            options={"ordering": ["-data_inicio", "-id"]},
        ),
        migrations.CreateModel(
            name="ServidorSetorHistorico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo_vinculo", models.CharField(blank=True, max_length=120)),
                ("principal", models.BooleanField(default=False)),
                ("data_inicio", models.DateField(default=django.utils.timezone.now)),
                ("data_fim", models.DateField(blank=True, null=True)),
                ("observacao", models.TextField(blank=True)),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="setores_historico", to="usuarios.servidorperfil")),
                ("setor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="historico_servidores", to="setores.setor")),
            ],
            options={"ordering": ["-principal", "-data_inicio", "-id"]},
        ),
        migrations.CreateModel(
            name="ServidorFerias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("exercicio", models.CharField(max_length=9)),
                ("periodo_inicio", models.DateField()),
                ("periodo_fim", models.DateField()),
                ("situacao", models.CharField(choices=[("PROGRAMADA", "Programada"), ("EM_ANDAMENTO", "Em andamento"), ("GOZADA", "Gozada")], default="PROGRAMADA", max_length=20)),
                ("observacao", models.TextField(blank=True)),
                ("perfil", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="ferias", to="usuarios.servidorperfil")),
            ],
            options={"ordering": ["-periodo_inicio", "-id"]},
        ),
    ]