import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cursos", "0020_componentecurricular_conteudo_modulo"),
        ("matriculas", "0015_matricula_version"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentoObrigatorioCurso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo_documento",
                    models.CharField(
                        choices=[
                            ("RG", "RG / Documento de Identidade"),
                            ("CPF", "CPF"),
                            ("COMPROVANTE_RESIDENCIA", "Comprovante de Residencia"),
                            ("HISTORICO_ESCOLAR", "Historico Escolar"),
                            ("FOTO", "Foto 3x4"),
                            ("CERTIDAO_NASCIMENTO", "Certidao de Nascimento"),
                            ("DECLARACAO_TRANSFERENCIA", "Declaracao de Transferencia"),
                            ("OUTROS", "Outros"),
                        ],
                        max_length=40,
                        verbose_name="Tipo de Documento",
                    ),
                ),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "curso",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documentos_obrigatorios",
                        to="cursos.curso",
                    ),
                ),
            ],
            options={
                "verbose_name": "Documento Obrigatorio por Curso",
                "verbose_name_plural": "Documentos Obrigatorios por Curso",
                "ordering": ["curso__nome", "tipo_documento"],
                "unique_together": {("curso", "tipo_documento")},
            },
        ),
    ]
