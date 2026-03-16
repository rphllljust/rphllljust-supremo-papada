from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuarios", "0006_servidorperfil_regime_bancarios"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="must_change_password",
            field=models.BooleanField(default=False),
        ),
    ]