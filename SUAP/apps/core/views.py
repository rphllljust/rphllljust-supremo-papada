# File: apps/core/views.py
from django.http import Http404
from django.shortcuts import render


def dashboard(request):
    """Renderiza `core/dashboard.html` com dados mockados."""
    context = {
        "total_students": 1240,
        "total_courses": 18,
        "total_classes": 42,
        "total_enrollments": 987,
        "avg_grade": 8.4,

        "in_person_students": 860,
        "remote_students": 380,

        "in_person_classes": 28,
        "remote_classes": 14,

        "announcements": [
            {
                "level": "success",
                "title": "Período letivo iniciado",
                "body": "As aulas do primeiro semestre começaram com sucesso."
            },
            {
                "level": "warning",
                "title": "Atenção aos prazos",
                "body": "O prazo para ajustes de matrícula termina nesta sexta-feira."
            },
            {
                "level": "info",
                "title": "Novo comunicado",
                "body": "O sistema estará em manutenção no sábado das 08h às 12h."
            },
        ],

        "recent_enrollments": [
            {
                "student": {"full_name": "Ana Beatriz Souza"},
                "school_class": "1º Ano A - Informática",
                "status": "active",
            },
            {
                "student": {"full_name": "Carlos Henrique Lima"},
                "school_class": "2º Ano B - Administração",
                "status": "transferred",
            },
            {
                "student": {"full_name": "Juliana Martins Rocha"},
                "school_class": "3º Ano A - Edificações",
                "status": "completed",
            },
            {
                "student": {"full_name": "Pedro Augusto Silva"},
                "school_class": "1º Ano C - Redes",
                "status": "active",
            },
        ],

        "recent_attendance": [
            {
                "attendance_date": "2026-03-01",
                "enrollment": {"student": {"full_name": "Ana Beatriz Souza"}},
                "present": True,
            },
            {
                "attendance_date": "2026-03-01",
                "enrollment": {"student": {"full_name": "Carlos Henrique Lima"}},
                "present": False,
            },
            {
                "attendance_date": "2026-03-02",
                "enrollment": {"student": {"full_name": "Juliana Martins Rocha"}},
                "present": True,
            },
            {
                "attendance_date": "2026-03-02",
                "enrollment": {"student": {"full_name": "Pedro Augusto Silva"}},
                "present": True,
            },
        ],

        "class_distribution": {
            "labels": ["1º Ano A", "1º Ano B", "2º Ano A", "2º Ano B", "3º Ano A"],
            "values": [32, 28, 30, 25, 21],
        }
    }

    return render(request, "core/dashboard.html", context)


def acesso_negado(request, exception=None):
    return render(
        request,
        "base/acesso_negado.html",
        {"mensagem": "Você não possui permissão para acessar este recurso."},
        status=403,
    )


def ensino_item_indisponivel(request, item_slug):
    raise Http404(f"A funcionalidade de ensino '{item_slug}' ainda não foi implementada.")
