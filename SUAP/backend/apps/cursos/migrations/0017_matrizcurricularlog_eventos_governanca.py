from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cursos', '0016_componentecurricular_catalogo_fks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='matrizcurricularlog',
            name='evento',
            field=models.CharField(choices=[('criacao_matriz', 'Criação de Matriz'), ('clonagem_matriz', 'Clonagem de Matriz'), ('publicacao_matriz', 'Publicação de Matriz'), ('encerramento_matriz', 'Encerramento de Matriz'), ('definicao_vigencia', 'Definição de Vigência'), ('migracao_componentes', 'Migração de Componentes'), ('criacao_curso_modelo', 'Criação de Curso Modelo no Moodle'), ('atualizacao_curso_modelo', 'Atualização de Curso Modelo no Moodle'), ('criacao_oferta_real', 'Criação de Oferta Real'), ('importacao_conteudo', 'Importação/Cópia de Conteúdo'), ('falha_sincronizacao', 'Falha de Sincronização')], max_length=40, verbose_name='Evento'),
        ),
    ]