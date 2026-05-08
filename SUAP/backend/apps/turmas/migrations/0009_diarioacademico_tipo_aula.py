from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("turmas", "0008_polo_and_turma_polo"),
    ]

    operations = [
        migrations.AddField(
            model_name="diarioacademico",
            name="tipo_aula",
            field=models.CharField(
                choices=[
                    ("REGULAR", "Regular"),
                    ("ONLINE", "Online"),
                    ("ENCONTRO_ITINERANTE", "Encontro Itinerante"),
                ],
                default="REGULAR",
                max_length=20,
                verbose_name="Tipo de Aula",
            ),
        ),
    ]
