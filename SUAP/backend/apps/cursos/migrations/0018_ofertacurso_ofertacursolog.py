from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('unidades', '0003_merge_20260305_1203'),
        ('cursos', '0017_matrizcurricularlog_eventos_governanca'),
    ]

    operations = [
        migrations.CreateModel(
            name='OfertaCurso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, verbose_name='Nome da Oferta')),
                ('codigo_turma', models.CharField(blank=True, default='', max_length=50, verbose_name='Turma')),
                ('ano_oferta', models.PositiveIntegerField(verbose_name='Ano da Oferta')),
                ('periodo_letivo', models.CharField(default='1', max_length=20, verbose_name='Período Letivo')),
                ('turno', models.CharField(choices=[('MANHA', 'Manhã'), ('TARDE', 'Tarde'), ('NOITE', 'Noite'), ('INTEGRAL', 'Integral')], default='NOITE', max_length=16, verbose_name='Turno')),
                ('vagas_totais', models.PositiveIntegerField(default=0, verbose_name='Vagas Totais')),
                ('vagas_ocupadas', models.PositiveIntegerField(default=0, verbose_name='Vagas Ocupadas')),
                ('status', models.CharField(choices=[('PLANEJADA', 'Planejada'), ('ATIVA', 'Ativa'), ('ENCERRADA', 'Encerrada'), ('CANCELADA', 'Cancelada')], default='PLANEJADA', max_length=20, verbose_name='Status')),
                ('observacao', models.TextField(blank=True, default='', verbose_name='Observações')),
                ('moodle_course_id', models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name='ID do Curso da Oferta no Moodle')),
                ('moodle_shortname', models.CharField(blank=True, default='', max_length=100, verbose_name='Shortname da Oferta no Moodle')),
                ('moodle_category_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID da Categoria da Oferta no Moodle')),
                ('last_sync_at', models.DateTimeField(blank=True, null=True, verbose_name='Última Sincronização')),
                ('last_sync_status', models.CharField(blank=True, default='', max_length=20, verbose_name='Status da Última Sincronização')),
                ('last_sync_message', models.TextField(blank=True, default='', verbose_name='Mensagem da Última Sincronização')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('calendario_letivo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ofertas', to='cursos.calendarioletivo', verbose_name='Calendário Letivo')),
                ('curso_base', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ofertas', to='cursos.curso', verbose_name='Curso Base')),
                ('matriz_curricular', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ofertas', to='cursos.matrizcurricular', verbose_name='Matriz Curricular')),
                ('polo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ofertas_curso', to='unidades.unidade', verbose_name='Polo')),
            ],
            options={
                'verbose_name': 'Oferta de Curso',
                'verbose_name_plural': 'Ofertas de Cursos',
                'ordering': ['-ano_oferta', '-periodo_letivo', 'curso_base__nome', 'codigo_turma', 'nome'],
            },
        ),
        migrations.CreateModel(
            name='OfertaCursoLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evento', models.CharField(choices=[('criacao_oferta', 'Criação de Oferta'), ('atualizacao_oferta', 'Atualização de Oferta'), ('sincronizacao_moodle', 'Sincronização com Moodle'), ('importacao_conteudo', 'Importação/Cópia de Conteúdo'), ('falha_sincronizacao', 'Falha de Sincronização')], max_length=40, verbose_name='Evento')),
                ('status', models.CharField(choices=[('info', 'Informação'), ('success', 'Sucesso'), ('error', 'Erro')], default='info', max_length=20, verbose_name='Status')),
                ('mensagem', models.TextField(blank=True, default='', verbose_name='Mensagem')),
                ('payload', models.JSONField(blank=True, default=dict, verbose_name='Payload')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('oferta_curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='cursos.ofertacurso', verbose_name='Oferta do Curso')),
            ],
            options={
                'verbose_name': 'Log de Oferta de Curso',
                'verbose_name_plural': 'Logs de Ofertas de Cursos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='ofertacurso',
            constraint=models.UniqueConstraint(fields=('curso_base', 'matriz_curricular', 'polo', 'ano_oferta', 'periodo_letivo', 'codigo_turma'), name='uniq_oferta_curso_por_execucao'),
        ),
    ]