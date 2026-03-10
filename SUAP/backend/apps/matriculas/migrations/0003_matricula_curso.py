from django.db import migrations, models
import django.db.models.deletion


def backfill_curso_from_turma(apps, schema_editor):
    Matricula = apps.get_model("matriculas", "Matricula")

    for matricula in Matricula.objects.select_related("turma").all():
        matricula.curso_id = matricula.turma.curso_id
        matricula.save(update_fields=["curso"])


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0001_initial"),
        ("matriculas", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="matricula",
            name="curso",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="matriculas",
                to="cursos.curso",
            ),
        ),
        migrations.RunPython(backfill_curso_from_turma, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="matricula",
            name="curso",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="matriculas",
                to="cursos.curso",
            ),
        ),
    ]

