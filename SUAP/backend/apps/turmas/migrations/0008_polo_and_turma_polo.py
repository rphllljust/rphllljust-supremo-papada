from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("turmas", "0007_turma_modalidade_capacidade_maxima"),
    ]

    operations = [
        migrations.CreateModel(
            name="Polo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nome", models.CharField(max_length=120, verbose_name="Nome do Polo")),
                ("municipio", models.CharField(max_length=100, verbose_name="Município")),
                ("uf", models.CharField(default="RO", max_length=2, verbose_name="UF")),
                ("endereco", models.CharField(blank=True, default="", max_length=255, verbose_name="Endereço")),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
            ],
            options={
                "verbose_name": "Polo",
                "verbose_name_plural": "Polos",
                "ordering": ["municipio", "nome"],
            },
        ),
        migrations.AddField(
            model_name="turma",
            name="polo",
            field=models.ForeignKey(
                blank=True,
                help_text="Obrigatório para turmas com modalidade Itinerante.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="turmas",
                to="turmas.polo",
                verbose_name="Polo/Localidade",
            ),
        ),
    ]
