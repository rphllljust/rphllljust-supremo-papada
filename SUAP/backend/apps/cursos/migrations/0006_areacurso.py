from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0005_alter_curso_sigla'),
    ]

    operations = [
        migrations.CreateModel(
            name='AreaCurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200, unique=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Área de Curso',
                'verbose_name_plural': 'Áreas de Cursos',
                'ordering': ['descricao'],
            },
        ),
    ]