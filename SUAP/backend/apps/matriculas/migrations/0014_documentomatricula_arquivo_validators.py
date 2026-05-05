from django.db import migrations, models
import apps.matriculas.models


class Migration(migrations.Migration):

    dependencies = [
        ("matriculas", "0013_dependenciaacademica"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentomatricula",
            name="arquivo",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="matriculas/documentos/",
                validators=[apps.matriculas.models.validar_arquivo_documento],
                verbose_name="Arquivo",
            ),
        ),
    ]
