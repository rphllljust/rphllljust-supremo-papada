from django.db import migrations, models


FIXED_UNITS = (
    ("sede", "Sede"),
    ("rio_branco", "Rio Branco"),
    ("flora", "Flora"),
)

ALIASES = {
    "sede": "sede",
    "campus sede": "sede",
    "rio branco": "rio_branco",
    "riobranco": "rio_branco",
    "campus rio branco": "rio_branco",
    "flora": "flora",
    "campus flora": "flora",
}


def _normalize(value):
    value = (value or "").strip().lower()
    return " ".join(value.replace("_", " ").replace("-", " ").split())


def forwards(apps, schema_editor):
    Unidade = apps.get_model("unidades", "Unidade")
    Curso = apps.get_model("cursos", "Curso")

    canonical = {}
    for codigo, nome in FIXED_UNITS:
        unidade, _ = Unidade.objects.update_or_create(codigo=codigo, defaults={"nome": nome})
        canonical[codigo] = unidade

    sede = canonical["sede"]
    canonical_ids = {item.pk for item in canonical.values()}

    for unidade in Unidade.objects.exclude(pk__in=canonical_ids):
        normalized_code = _normalize(unidade.codigo)
        normalized_name = _normalize(unidade.nome)
        target_code = ALIASES.get(normalized_code) or ALIASES.get(normalized_name) or "sede"
        target = canonical.get(target_code, sede)

        Curso.objects.filter(unidade_id=unidade.pk).update(unidade_id=target.pk)
        unidade.delete()


def backwards(apps, schema_editor):
    # Mantemos apenas rollback no-op para evitar recriar dados legados removidos.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("unidades", "0001_initial"),
        ("cursos", "0003_curso_sigla"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name="unidade",
            name="nome",
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name="unidade",
            name="codigo",
            field=models.CharField(
                choices=[("sede", "Sede"), ("rio_branco", "Rio Branco"), ("flora", "Flora")],
                max_length=20,
                unique=True,
            ),
        ),
    ]

