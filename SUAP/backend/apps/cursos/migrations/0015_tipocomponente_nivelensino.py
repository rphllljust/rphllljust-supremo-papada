from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0014_matrizcurricular_componentes_transicao'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoComponente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200, unique=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Tipo do Componente',
                'verbose_name_plural': 'Tipos do Componente',
                'ordering': ['descricao'],
            },
        ),
        migrations.CreateModel(
            name='NivelEnsino',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200, unique=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Nível de Ensino',
                'verbose_name_plural': 'Níveis de Ensino',
                'ordering': ['descricao'],
            },
        ),
    ]