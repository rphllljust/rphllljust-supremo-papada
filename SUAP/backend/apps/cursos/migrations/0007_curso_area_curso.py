from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0006_areacurso'),
    ]

    operations = [
        migrations.AddField(
            model_name='curso',
            name='area_curso',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='cursos', to='cursos.areacurso', verbose_name='Área do Curso'),
        ),
    ]