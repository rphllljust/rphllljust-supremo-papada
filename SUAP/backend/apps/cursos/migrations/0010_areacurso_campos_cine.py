from django.db import migrations, models


def backfill_area_curso_fields(apps, schema_editor):
    AreaCurso = apps.get_model('cursos', 'AreaCurso')
    for area in AreaCurso.objects.all():
        base = (area.descricao or '').strip()
        updates = []
        if base and not area.cine:
            area.cine = base
            updates.append('cine')
        if base and not area.area_detalhada:
            area.area_detalhada = base
            updates.append('area_detalhada')
        if base and not area.area_especifica:
            area.area_especifica = base
            updates.append('area_especifica')
        if base and not area.area_geral:
            area.area_geral = base
            updates.append('area_geral')
        if updates:
            area.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0009_componentecurricular_campos_detalhe'),
    ]

    operations = [
        migrations.AddField(
            model_name='areacurso',
            name='area_detalhada',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Área Detalhada'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='area_especifica',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Área Específica'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='area_geral',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Área Geral'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='cine',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='CINE'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='codigo_area_detalhada',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Código da Área Detalhada'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='codigo_area_especifica',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Código da Área Específica'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='codigo_area_geral',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Código da Área Geral'),
        ),
        migrations.AddField(
            model_name='areacurso',
            name='codigo_cine',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Código CINE'),
        ),
        migrations.RunPython(backfill_area_curso_fields, migrations.RunPython.noop),
    ]