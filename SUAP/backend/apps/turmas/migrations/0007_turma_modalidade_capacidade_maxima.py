from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("turmas", "0006_diariomaterialaula_diarioocorrencia"),
    ]

    operations = [
        migrations.AddField(
            model_name="turma",
            name="modalidade",
            field=models.CharField(
                choices=[
                    ("PRESENCIAL", "Presencial"),
                    ("REMOTO", "Remoto"),
                    ("ITINERANTE", "Itinerante"),
                    ("HIBRIDO", "Híbrido"),
                ],
                default="PRESENCIAL",
                max_length=15,
                verbose_name="Modalidade",
            ),
        ),
        migrations.AddField(
            model_name="turma",
            name="capacidade_maxima",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name="Capacidade Máxima",
                help_text="Deixe em branco para sem limite.",
            ),
        ),
    ]
