from datetime import date

from django.db.models import Q
from rest_framework import generics

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.estagio.models import Convenio, Estagio

from .serializers import MATRICULA_STATUS_LABELS, EstagioDetailSerializer, EstagioSerializer


class EstagioListApiView(generics.ListAPIView):
    permission_classes = [CanAccessModule]
    module_name = "estagio"
    access_surface = "api"
    access_action = "view"
    serializer_class = EstagioSerializer
    pagination_class = StandardResultsSetPagination

    def get_base_queryset(self):
        return Estagio.objects.select_related(
            "matricula__aluno__pessoa",
            "matricula__curso__unidade",
            "convenio",
            "orientador_idep__pessoa",
        ).prefetch_related("termos", "acompanhamentos").order_by("-data_inicio", "-id")

    def apply_filters(self, queryset, include_tab=True):
        params = self.request.query_params
        search = params.get("search", "").strip()
        modalidade = params.get("modalidade", "").strip()
        status = params.get("status", "").strip()
        matricula_status = params.get("matricula_status", "").strip()
        curso = params.get("curso", "").strip()
        campus = params.get("campus", "").strip()
        possui_aditivo = params.get("possui_aditivo", "").strip()
        aguardando_assinatura = params.get("aguardando_assinatura", "").strip()
        convenio = params.get("convenio", "").strip()
        data_inicio_de = params.get("data_inicio_de", "").strip()
        data_inicio_ate = params.get("data_inicio_ate", "").strip()
        data_prevista_de = params.get("data_prevista_de", "").strip()
        data_prevista_ate = params.get("data_prevista_ate", "").strip()
        data_encerramento_de = params.get("data_encerramento_de", "").strip()
        data_encerramento_ate = params.get("data_encerramento_ate", "").strip()

        if search:
            queryset = queryset.filter(
                Q(empresa__icontains=search)
                | Q(convenio__empresa__icontains=search)
                | Q(matricula__numero_matricula__icontains=search)
                | Q(matricula__aluno__username__icontains=search)
                | Q(matricula__aluno__first_name__icontains=search)
                | Q(matricula__aluno__last_name__icontains=search)
                | Q(matricula__aluno__pessoa__nome_completo__icontains=search)
                | Q(matricula__curso__nome__icontains=search)
                | Q(orientador_idep__username__icontains=search)
                | Q(orientador_idep__first_name__icontains=search)
                | Q(orientador_idep__last_name__icontains=search)
                | Q(orientador_idep__pessoa__nome_completo__icontains=search)
            )

        if modalidade:
            queryset = queryset.filter(modalidade=modalidade)
        if status:
            queryset = queryset.filter(status=status)
        if matricula_status:
            queryset = queryset.filter(matricula__status=matricula_status)
        if curso:
            queryset = queryset.filter(matricula__curso_id=curso)
        if campus:
            queryset = queryset.filter(matricula__curso__unidade__codigo=campus)
        if convenio:
            queryset = queryset.filter(convenio_id=convenio)
        if possui_aditivo == "SIM":
            queryset = queryset.filter(termos__status="ADITADO")
        elif possui_aditivo == "NAO":
            queryset = queryset.exclude(termos__status="ADITADO")
        if aguardando_assinatura == "SIM":
            queryset = queryset.filter(termos__status="PENDENTE")
        elif aguardando_assinatura == "NAO":
            queryset = queryset.exclude(termos__status="PENDENTE")

        if data_inicio_de:
            queryset = queryset.filter(data_inicio__gte=data_inicio_de)
        if data_inicio_ate:
            queryset = queryset.filter(data_inicio__lte=data_inicio_ate)
        if data_prevista_de:
            queryset = queryset.filter(data_fim_prevista__gte=data_prevista_de)
        if data_prevista_ate:
            queryset = queryset.filter(data_fim_prevista__lte=data_prevista_ate)
        if data_encerramento_de:
            queryset = queryset.filter(data_fim_real__gte=data_encerramento_de)
        if data_encerramento_ate:
            queryset = queryset.filter(data_fim_real__lte=data_encerramento_ate)

        if include_tab:
            aba = params.get("aba", "TODOS").strip() or "TODOS"
            today = date.today()
            if aba == "EM_ANDAMENTO":
                queryset = queryset.filter(status="EM_ANDAMENTO")
            elif aba == "MATRICULAS_IRREGULARES":
                queryset = queryset.exclude(matricula__status="ATIVA")
            elif aba == "DATA_PREVISTA_ATINGIDA":
                queryset = queryset.filter(status="EM_ANDAMENTO", data_fim_prevista__isnull=False, data_fim_prevista__lte=today)
            elif aba == "PENDENCIA_RELATORIO_ESTAGIARIO":
                queryset = queryset.exclude(acompanhamentos__tipo="RELATORIO")
            elif aba == "PENDENCIA_RELATORIO_SUPERVISOR":
                queryset = queryset.exclude(acompanhamentos__tipo="AVALIACAO")
            elif aba == "SEM_ASSINATURA_RELATORIOS":
                queryset = queryset.filter(termos__status="PENDENTE")
            elif aba == "APTO_ENCERRAMENTO":
                queryset = queryset.filter(status="EM_ANDAMENTO", data_fim_prevista__isnull=False, data_fim_prevista__lte=today)
            elif aba == "ENCERRADOS":
                queryset = queryset.filter(status="CONCLUIDO")

        return queryset.distinct()

    def get_queryset(self):
        return self.apply_filters(self.get_base_queryset(), include_tab=True)

    def build_filter_options(self, queryset):
        cursos = queryset.values("matricula__curso_id", "matricula__curso__nome").distinct().order_by("matricula__curso__nome")
        campi = queryset.values("matricula__curso__unidade__codigo", "matricula__curso__unidade__nome").distinct().order_by("matricula__curso__unidade__nome")
        convenios = Convenio.objects.order_by("empresa").values("id", "empresa")

        return {
            "modalidades": [{"value": value, "label": label} for value, label in Estagio.MODALIDADE_CHOICES],
            "status": [{"value": value, "label": label} for value, label in Estagio.STATUS_CHOICES],
            "matricula_status": [{"value": value, "label": label} for value, label in MATRICULA_STATUS_LABELS.items()],
            "cursos": [
                {"value": item["matricula__curso_id"], "label": item["matricula__curso__nome"]}
                for item in cursos
                if item["matricula__curso_id"]
            ],
            "campi": [
                {"value": item["matricula__curso__unidade__codigo"], "label": item["matricula__curso__unidade__nome"]}
                for item in campi
                if item["matricula__curso__unidade__codigo"]
            ],
            "convenios": [
                {"value": item["id"], "label": item["empresa"]}
                for item in convenios
            ],
        }

    def build_tab_counts(self, queryset):
        today = date.today()
        return {
            "TODOS": queryset.count(),
            "EM_ANDAMENTO": queryset.filter(status="EM_ANDAMENTO").count(),
            "MATRICULAS_IRREGULARES": queryset.exclude(matricula__status="ATIVA").count(),
            "DATA_PREVISTA_ATINGIDA": queryset.filter(status="EM_ANDAMENTO", data_fim_prevista__isnull=False, data_fim_prevista__lte=today).count(),
            "PENDENCIA_RELATORIO_ESTAGIARIO": queryset.exclude(acompanhamentos__tipo="RELATORIO").distinct().count(),
            "PENDENCIA_RELATORIO_SUPERVISOR": queryset.exclude(acompanhamentos__tipo="AVALIACAO").distinct().count(),
            "SEM_ASSINATURA_RELATORIOS": queryset.filter(termos__status="PENDENTE").distinct().count(),
            "APTO_ENCERRAMENTO": queryset.filter(status="EM_ANDAMENTO", data_fim_prevista__isnull=False, data_fim_prevista__lte=today).count(),
            "ENCERRADOS": queryset.filter(status="CONCLUIDO").count(),
        }

    def list(self, request, *args, **kwargs):
        base_queryset = self.apply_filters(self.get_base_queryset(), include_tab=False)
        response = super().list(request, *args, **kwargs)
        response.data["summary"] = {
            "tab_counts": self.build_tab_counts(base_queryset),
            "filter_options": self.build_filter_options(self.get_base_queryset()),
        }
        return response


class EstagioDetailApiView(generics.RetrieveAPIView):
    permission_classes = [CanAccessModule]
    module_name = "estagio"
    access_surface = "api"
    access_action = "view"
    serializer_class = EstagioDetailSerializer
    queryset = Estagio.objects.select_related(
        "matricula__aluno__pessoa",
        "matricula__curso__unidade",
        "convenio",
        "orientador_idep__pessoa",
    ).prefetch_related("termos", "acompanhamentos")