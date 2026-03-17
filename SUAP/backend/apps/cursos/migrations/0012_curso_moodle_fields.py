from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cursos", "0011_eixotecnologico"),
    ]

    operations = [
        migrations.AddField(
            model_name="curso",
            name="moodle_course_id",
            field=models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name="ID do Curso no Moodle"),
        ),
        migrations.AddField(
            model_name="curso",
            name="moodle_shortname",
            field=models.CharField(blank=True, default="", max_length=100, verbose_name="Shortname do Moodle"),
        ),
    ]