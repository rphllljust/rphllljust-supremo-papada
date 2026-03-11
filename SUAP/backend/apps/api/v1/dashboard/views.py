from itertools import chain

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.matriculas.models import DocumentoMatricula, Matricula, PendenciaDocumental
from apps.notificacoes.models import Notificacao
from apps.turmas.models import Turma


class DashboardOverviewApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        next_seven_days = today + timezone.timedelta(days=7)

        recent_matriculas_qs = (
            Matricula.objects.select_related("aluno__pessoa", "curso", "turma")
            .order_by("-data_matricula", "-id")
        )
        recent_matriculas = list(recent_matriculas_qs[:5])

        pendencias_qs = (
            PendenciaDocumental.objects.select_related("matricula__aluno__pessoa", "matricula__curso", "matricula__turma")
            .filter(status="ABERTA")
            .order_by("prazo", "-data_abertura", "-id")
        )
        document_pending = list(pendencias_qs[:5])

        upcoming_deadlines_qs = pendencias_qs.filter(prazo__isnull=False, prazo__gte=today).order_by("prazo", "data_abertura", "id")
        upcoming_deadlines = list(upcoming_deadlines_qs[:5])

        turmas_sem_alunos_qs = (
            Turma.objects.select_related("curso")
            .filter(status="ATIVA")
            .annotate(total_alunos=Count("matriculas", filter=Q(matriculas__status="ATIVA"), distinct=True))
            .filter(total_alunos=0)
            .order_by("ano_letivo", "nome")
        )
        turmas_sem_alunos = list(turmas_sem_alunos_qs[:5])

        notificacoes_qs = (
            Notificacao.objects.select_related("categoria")
            .filter(usuario=request.user, ocultada_em__isnull=True)
            .order_by("lida_em", "-data_evento", "-id")
        )
        system_alerts = list(notificacoes_qs[:5])

        activities = sorted(
            chain(
                [
                    {
                        "kind": "matricula",
                        "title": f"Matrícula criada: {item.numero_matricula}",
                        "description": f"{self._student_name(item)} • {item.curso.nome} • {item.turma.nome}",
                        "date": item.data_matricula,
                        "href": "/matriculas",
                        "badge": "success",
                    }
                    for item in recent_matriculas_qs[:4]
                ],
                [
                    {
                        "kind": "pendencia",
                        "title": "Pendência documental aberta",
                        "description": f"{item.descricao} • {self._student_name(item.matricula)}",
                        "date": item.data_abertura,
                        "href": "/matriculas",
                        "badge": "warning",
                    }
                    for item in pendencias_qs[:4]
                ],
                [
                    {
                        "kind": "aviso",
                        "title": item.titulo,
                        "description": (item.resumo or item.categoria.titulo) if item.categoria else (item.resumo or "Aviso do sistema"),
                        "date": timezone.localtime(item.data_evento),
                        "href": item.link or "/comum/notificacoes",
                        "badge": "info" if item.is_unread else "secondary",
                    }
                    for item in notificacoes_qs[:4]
                ],
            ),
            key=lambda item: item["date"],
            reverse=True,
        )[:8]

        return Response({
            "summary": {
                "recent_enrollments": recent_matriculas_qs.filter(data_matricula__gte=today - timezone.timedelta(days=7)).count(),
                "document_pending": pendencias_qs.count() + DocumentoMatricula.objects.filter(status="PENDENTE").count(),
                "classes_without_students": turmas_sem_alunos_qs.count(),
                "system_alerts": notificacoes_qs.filter(lida_em__isnull=True).count(),
                "upcoming_deadlines": upcoming_deadlines_qs.filter(prazo__lte=next_seven_days).count(),
            },
            "recent_matriculas": [
                {
                    "id": item.id,
                    "numero_matricula": item.numero_matricula,
                    "aluno_nome": self._student_name(item),
                    "curso_nome": item.curso.nome,
                    "turma_nome": item.turma.nome,
                    "status": item.status,
                    "status_display": item.get_status_display(),
                    "data_matricula": item.data_matricula,
                    "href": "/matriculas",
                }
                for item in recent_matriculas
            ],
            "document_pending": [
                {
                    "id": item.id,
                    "descricao": item.descricao,
                    "aluno_nome": self._student_name(item.matricula),
                    "numero_matricula": item.matricula.numero_matricula,
                    "prazo": item.prazo,
                    "status_display": item.get_status_display(),
                    "href": "/matriculas",
                }
                for item in document_pending
            ],
            "turmas_sem_alunos": [
                {
                    "id": item.id,
                    "nome": item.nome,
                    "curso_nome": item.curso.nome,
                    "ano_letivo": item.ano_letivo,
                    "status_display": item.get_status_display(),
                    "href": "/turmas",
                }
                for item in turmas_sem_alunos
            ],
            "system_alerts": [
                {
                    "id": item.id,
                    "titulo": item.titulo,
                    "resumo": item.resumo,
                    "tipo_display": item.get_tipo_display(),
                    "categoria_titulo": item.categoria.titulo if item.categoria else "Sistema",
                    "data_evento": timezone.localtime(item.data_evento),
                    "is_unread": item.is_unread,
                    "href": item.link or "/comum/notificacoes",
                }
                for item in system_alerts
            ],
            "recent_activities": list(activities),
            "upcoming_deadlines": [
                {
                    "id": item.id,
                    "descricao": item.descricao,
                    "aluno_nome": self._student_name(item.matricula),
                    "numero_matricula": item.matricula.numero_matricula,
                    "prazo": item.prazo,
                    "href": "/matriculas",
                }
                for item in upcoming_deadlines
            ],
        })

    def _student_name(self, matricula):
        if getattr(matricula.aluno, "pessoa", None) and matricula.aluno.pessoa.nome_completo:
            return matricula.aluno.pessoa.nome_completo

        full_name = matricula.aluno.get_full_name().strip()
        return full_name or matricula.aluno.username