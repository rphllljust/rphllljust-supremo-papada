from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0008_componentecurricular_metadados'),
    ]

    operations = [
        migrations.AddField(
            model_name='componentecurricular',
            name='abreviatura',
            field=models.CharField(blank=True, default='', max_length=30, verbose_name='Abreviatura'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='descricao_diploma_historico',
            field=models.CharField(blank=True, default='', max_length=200, verbose_name='Descrição no Diploma e Histórico'),
        ),
        migrations.AddField(
            model_name='componentecurricular',
            name='diretoria',
            field=models.CharField(blank=True, default='', max_length=120, verbose_name='Diretoria'),
        ),
    ]