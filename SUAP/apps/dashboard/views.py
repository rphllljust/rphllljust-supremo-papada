from django.shortcuts import render

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.usuarios.models import Usuario


def index(request):
    total_students = Usuario.objects.filter(tipo="ALUNO").count()
    total_courses = Curso.objects.count()
    total_classes = Turma.objects.count()
    total_enrollments = Matricula.objects.filter(status="ATIVA").count()

    latest_matriculas = Matricula.objects.select_related("aluno", "turma", "curso").order_by("-id")[:5]

    recent_enrollments = [
        {
            "student": {
                "full_name": matricula.aluno.get_full_name() or matricula.aluno.username,
            },
            "school_class": f"{matricula.turma.nome} - {matricula.curso.nome}",
            "status": matricula.status,
        }
        for matricula in latest_matriculas
    ]

    context = {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_classes": total_classes,
        "total_enrollments": total_enrollments,
        "avg_grade": 0,
        "in_person_students": 0,
        "remote_students": 0,
        "in_person_classes": 0,
        "remote_classes": 0,
        "announcements": [
            {
                "level": "success",
                "title": "Período letivo iniciado",
                "body": "As aulas do primeiro semestre começaram com sucesso.",
            },
            {
                "level": "warning",
                "title": "Atenção aos prazos",
                "body": "O prazo para ajustes de matrícula termina nesta sexta-feira.",
            },
        ],
        "recent_enrollments": recent_enrollments,
        "recent_attendance": [],
        "class_distribution": {
            "labels": ["1º Ano A", "1º Ano B", "2º Ano A", "2º Ano B", "3º Ano A"],
            "values": [32, 28, 30, 25, 21],
        },
    }

    return render(request, "dashboard/index.html", context)
