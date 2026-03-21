from django.db import migrations, models


def forwards(apps, schema_editor):
    ComponenteCurricular = apps.get_model('cursos', 'ComponenteCurricular')
    TipoComponente = apps.get_model('cursos', 'TipoComponente')
    NivelEnsino = apps.get_model('cursos', 'NivelEnsino')

    for componente in ComponenteCurricular.objects.all().iterator():
        updates = []

        descricao_tipo = (componente.tipo_componente or '').strip()
        descricao_nivel = (componente.nivel_ensino or '').strip()

        if descricao_tipo:
            tipo_obj, _ = TipoComponente.objects.get_or_create(descricao=descricao_tipo)
            componente.tipo_componente_catalogo_id = tipo_obj.id
            updates.append('tipo_componente_catalogo')

        if descricao_nivel:
            nivel_obj, _ = NivelEnsino.objects.get_or_create(descricao=descricao_nivel)
            componente.nivel_ensino_catalogo_id = nivel_obj.id
            updates.append('nivel_ensino_catalogo')

        if updates:
            componente.save(update_fields=updates)


def backwards(apps, schema_editor):
    ComponenteCurricular = apps.get_model('cursos', 'ComponenteCurricular')

    for componente in ComponenteCurricular.objects.select_related('tipo_componente_catalogo', 'nivel_ensino_catalogo').all().iterator():
        updates = []

        if componente.tipo_componente_catalogo_id and not (componente.tipo_componente or '').strip():
            componente.tipo_componente = componente.tipo_componente_catalogo.descricao
            updates.append('tipo_componente')

        if componente.nivel_ensino_catalogo_id and not (componente.nivel_ensino or '').strip():
            componente.nivel_ensino = componente.nivel_ensino_catalogo.descricao
            updates.append('nivel_ensino')

        if updates:
            componente.save(update_fields=updates)


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0015_tipocomponente_nivelensino'),
    ]

    operations = [
        migrations.AddField(
            model_name='componentecurricular',
            name='nivel_ensino_catalogo',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='componentes_curriculares', to='cursos.nivelensino', verbose_name='Nível de Ensino (Catálogo)'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='tipo_componente_catalogo',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='componentes_curriculares', to='cursos.tipocomponente', verbose_name='Tipo do Componente (Catálogo)'),
        ),
        migrations.RunPython(forwards, backwards),
    ]