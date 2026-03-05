from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.cursos.models import Curso
from apps.matriculas.models import Matricula
from apps.turmas.models import Turma
from apps.usuarios.models import Usuario


@login_required
def index(request):
    if not request.user.is_active:
        logout(request)
        return redirect("accounts:login")

    perfil = getattr(request.user, "tipo", "")
    perfis_validos = {"SECRETARIA", "COORDENACAO", "PROFESSOR", "ALUNO", "ADMIN"}
    if perfil not in perfis_validos:
        return render(
            request,
            "base/acesso_negado.html",
            {"mensagem": "Seu perfil ainda não está habilitado para o painel."},
            status=403,
        )

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

    is_secretaria = perfil in {"SECRETARIA", "ADMIN"}
    is_coordenacao = perfil == "COORDENACAO"
    is_professor = perfil == "PROFESSOR"
    is_aluno = perfil == "ALUNO"

    context = {
        "perfil": perfil,
        "is_secretaria": is_secretaria,
        "is_coordenacao": is_coordenacao,
        "is_professor": is_professor,
        "is_aluno": is_aluno,
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
