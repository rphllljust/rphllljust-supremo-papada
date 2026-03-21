from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0013_curso_tipo_curso'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatrizCurricular',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome')),
                ('ano_referencia', models.PositiveIntegerField(verbose_name='Ano de Referência')),
                ('versao', models.CharField(default='1.0', max_length=40, verbose_name='Versão')),
                ('status', models.CharField(choices=[('RASCUNHO', 'Rascunho'), ('VIGENTE', 'Vigente'), ('ENCERRADA', 'Encerrada')], default='RASCUNHO', max_length=20, verbose_name='Status')),
                ('ativa', models.BooleanField(default=True, verbose_name='Ativa')),
                ('descricao', models.TextField(blank=True, default='', verbose_name='Descrição')),
                ('moodle_template_course_id', models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name='ID do Curso Modelo no Moodle')),
                ('moodle_template_shortname', models.CharField(blank=True, default='', max_length=100, verbose_name='Shortname do Curso Modelo no Moodle')),
                ('moodle_template_category_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID da Categoria do Curso Modelo no Moodle')),
                ('last_sync_at', models.DateTimeField(blank=True, null=True, verbose_name='Última Sincronização')),
                ('last_sync_status', models.CharField(blank=True, default='', max_length=20, verbose_name='Status da Última Sincronização')),
                ('last_sync_message', models.TextField(blank=True, default='', verbose_name='Mensagem da Última Sincronização')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('curso_base', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='matrizes_curriculares', to='cursos.curso', verbose_name='Curso Base')),
            ],
            options={
                'verbose_name': 'Matriz Curricular',
                'verbose_name_plural': 'Matrizes Curriculares',
                'ordering': ['-ano_referencia', 'curso_base__nome', 'nome', 'versao'],
            },
        ),
        migrations.AddField(
            model_name='curso',
            name='matriz_curricular',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='cursos_ofertados', to='cursos.matrizcurricular', verbose_name='Matriz Curricular de Referência'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='matriz_curricular',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='componentes', to='cursos.matrizcurricular', verbose_name='Matriz Curricular'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='modulo_nome',
            field=models.CharField(blank=True, default='', max_length=120, verbose_name='Nome do Módulo'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='modulo_numero',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Número do Módulo'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='ordem_no_modulo',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Ordem no Módulo'),
        ),
        migrations.CreateModel(
            name='MatrizCurricularLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evento', models.CharField(choices=[('criacao_matriz', 'Criação de Matriz'), ('migracao_componentes', 'Migração de Componentes'), ('criacao_curso_modelo', 'Criação de Curso Modelo no Moodle'), ('atualizacao_curso_modelo', 'Atualização de Curso Modelo no Moodle'), ('criacao_oferta_real', 'Criação de Oferta Real'), ('importacao_conteudo', 'Importação/Cópia de Conteúdo'), ('falha_sincronizacao', 'Falha de Sincronização')], max_length=40, verbose_name='Evento')),
                ('status', models.CharField(choices=[('info', 'Informação'), ('success', 'Sucesso'), ('error', 'Erro')], default='info', max_length=20, verbose_name='Status')),
                ('mensagem', models.TextField(blank=True, default='', verbose_name='Mensagem')),
                ('payload', models.JSONField(blank=True, default=dict, verbose_name='Payload')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('curso', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='logs_matriz_curricular', to='cursos.curso', verbose_name='Curso Relacionado')),
                ('matriz_curricular', models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name='logs', to='cursos.matrizcurricular', verbose_name='Matriz Curricular')),
            ],
            options={
                'verbose_name': 'Log de Matriz Curricular',
                'verbose_name_plural': 'Logs de Matrizes Curriculares',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AlterModelOptions(
            name='componentecurricular',
            options={'ordering': ['modulo_numero', 'ordem_no_modulo', 'ordem', 'nome'], 'verbose_name': 'Componente Curricular', 'verbose_name_plural': 'Componentes Curriculares'},
        ),
        migrations.AlterUniqueTogether(
            name='componentecurricular',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='matrizcurricular',
            constraint=models.UniqueConstraint(fields=('curso_base', 'ano_referencia', 'versao'), name='uniq_matriz_curricular_por_versao'),
        ),
        migrations.AddConstraint(
            model_name='matrizcurricular',
            constraint=models.UniqueConstraint(condition=Q(('status', 'VIGENTE')), fields=('curso_base', 'ano_referencia'), name='uniq_matriz_curricular_vigente_por_ano'),
        ),
        migrations.AddConstraint(
            model_name='componentecurricular',
            constraint=models.UniqueConstraint(condition=Q(('matriz_curricular__isnull', True)), fields=('curso', 'nome'), name='uniq_componente_legado_por_curso_nome'),
        ),
        migrations.AddConstraint(
            model_name='componentecurricular',
            constraint=models.UniqueConstraint(condition=Q(('matriz_curricular__isnull', False)), fields=('matriz_curricular', 'nome'), name='uniq_componente_por_matriz_nome'),
        ),
        migrations.AddConstraint(
            model_name='componentecurricular',
            constraint=models.UniqueConstraint(condition=Q(('matriz_curricular__isnull', False), ('modulo_numero__isnull', False), ('ordem_no_modulo__isnull', False)), fields=('matriz_curricular', 'modulo_numero', 'ordem_no_modulo'), name='uniq_ordem_componente_por_modulo_matriz'),
        ),
    ]