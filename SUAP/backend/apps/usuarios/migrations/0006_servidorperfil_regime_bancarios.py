from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0005_servidorperfil_and_related"),
    ]

    operations = [
        migrations.AddField(
            model_name="servidorperfil",
            name="agencia",
            field=models.CharField(blank=True, max_length=40),
        ),
        migrations.AddField(
            model_name="servidorperfil",
            name="banco",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="servidorperfil",
            name="conta_corrente",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="servidorperfil",
            name="regime_trabalho",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]