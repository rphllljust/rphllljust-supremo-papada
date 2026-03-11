from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0007_curso_area_curso'),
    ]

    operations = [
        migrations.AddField(
            model_name='componentecurricular',
            name='ativo',
            field=models.BooleanField(default=True, verbose_name='Está ativo'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='grupo_atuacao',
            field=models.CharField(blank=True, default='', max_length=120, verbose_name='Grupo de Atuação'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='hora_aula',
            field=models.PositiveIntegerField(default=0, verbose_name='Hora/aula'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='nivel_ensino',
            field=models.CharField(blank=True, default='', max_length=80, verbose_name='Nível de ensino'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='observacao',
            field=models.TextField(blank=True, default='', verbose_name='Observação'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='qtd_creditos',
            field=models.PositiveIntegerField(default=0, verbose_name='Qtd. de créditos'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='sigla',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='Sigla'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='sigla_qacademico',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='Sigla do Q-Acadêmico'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='tipo_componente',
            field=models.CharField(blank=True, default='', max_length=80, verbose_name='Tipo do Componente'),
        ),
    ]