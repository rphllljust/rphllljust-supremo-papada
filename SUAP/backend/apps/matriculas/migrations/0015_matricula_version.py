from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("matriculas", "0014_documentomatricula_arquivo_validators"),
    ]

    operations = [
        migrations.AddField(
            model_name="matricula",
            name="version",
            field=models.PositiveIntegerField(default=0, verbose_name="Versão"),
        ),
    ]
