from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0018_ofertacurso_ofertacursolog'),
    ]

    operations = [
        migrations.AddField(
            model_name='ofertacurso',
            name='moodle_sync_fallback_reason',
            field=models.TextField(blank=True, default='', verbose_name='Motivo do Fallback da Sincronização Moodle'),
        ),
        migrations.AddField(
            model_name='ofertacurso',
            name='moodle_sync_mode',
            field=models.CharField(blank=True, choices=[('duplicate_template', 'Duplicação do Template'), ('import_template', 'Importação para Curso Existente'), ('update_existing', 'Atualização de Curso Existente'), ('create_fallback', 'Criação Sem Template')], default='', max_length=40, verbose_name='Modo da Última Sincronização com Moodle'),
        ),
        migrations.AddField(
            model_name='ofertacurso',
            name='moodle_template_applied',
            field=models.BooleanField(default=False, verbose_name='Última Sincronização Usou Template Moodle'),
        ),
        migrations.AddField(
            model_name='ofertacurso',
            name='moodle_template_source_course_id',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='ID do Template Usado na Última Sincronização'),
        ),
        migrations.AddField(
            model_name='ofertacurso',
            name='moodle_template_source_shortname',
            field=models.CharField(blank=True, default='', max_length=100, verbose_name='Shortname do Template Usado na Última Sincronização'),
        ),
        migrations.AlterField(
            model_name='ofertacursolog',
            name='evento',
            field=models.CharField(choices=[('criacao_oferta', 'Criação de Oferta'), ('atualizacao_oferta', 'Atualização de Oferta'), ('sincronizacao_moodle', 'Sincronização com Moodle'), ('importacao_conteudo', 'Importação/Cópia de Conteúdo'), ('sincronizacao_template', 'Aplicação de Template da Matriz'), ('falha_sincronizacao', 'Falha de Sincronização')], max_length=40, verbose_name='Evento'),
        ),
    ]
