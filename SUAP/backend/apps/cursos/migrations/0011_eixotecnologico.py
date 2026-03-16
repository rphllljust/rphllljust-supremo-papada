from django.db import migrations, models


def criar_eixos_existentes(apps, schema_editor):
    Curso = apps.get_model('cursos', 'Curso')
    EixoTecnologico = apps.get_model('cursos', 'EixoTecnologico')

    descricoes = (
        Curso.objects.exclude(eixo_tecnologico='')
        .values_list('eixo_tecnologico', flat=True)
        .distinct()
    )

    for descricao in descricoes:
        descricao_normalizada = (descricao or '').strip()
        if descricao_normalizada:
            EixoTecnologico.objects.get_or_create(descricao=descricao_normalizada)


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0010_areacurso_campos_cine'),
    ]

    operations = [
        migrations.CreateModel(
            name='EixoTecnologico',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=200, unique=True, verbose_name='Descrição')),
            ],
            options={
                'verbose_name': 'Eixo Tecnológico',
                'verbose_name_plural': 'Eixos Tecnológicos',
                'ordering': ['descricao'],
            },
        ),
        migrations.RunPython(criar_eixos_existentes, migrations.RunPython.noop),
    ]