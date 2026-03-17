from django.db.models import Count, ExpressionWrapper, F, IntegerField, Prefetch, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.access.policies import filter_professor_scoped_queryset, professor_owns_related_resource
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.matriculas.models import Matricula
from apps.turmas.models import DiarioAcademico, DiarioMaterialAula, DiarioOcorrencia

from .serializers import (
    DiarioDetailSerializer,
    DiarioMaterialAulaSerializer,
    DiarioOcorrenciaSerializer,
    DiarioSerializer,
)


TAB_FILTERS = {
    'TODOS': lambda queryset: queryset,
    'EM_ANDAMENTO': lambda queryset: queryset.filter(status__in=['ABERTO', 'REVISAO']),
    'SEM_PROFESSOR': lambda queryset: queryset.filter(turma__professor_responsavel__isnull=True),
    'SEM_ALUNOS': lambda queryset: queryset.filter(total_matriculados=0),
    'NOTAS_PENDENTES': lambda queryset: queryset.filter(notas_pendentes__gt=0),
    'FREQUENCIAS_PENDENTES': lambda queryset: queryset.filter(frequencias_pendentes__gt=0),
    'FECHADOS': lambda queryset: queryset.filter(status='FECHADO'),
}


def annotate_diario_queryset(queryset):
    return queryset.annotate(
        total_matriculados=Count('turma__matriculas', filter=Q(turma__matriculas__status='ATIVA'), distinct=True),
        alunos_com_notas=Count(
            'turma__matriculas',
            filter=Q(turma__matriculas__status='ATIVA', turma__matriculas__notas__isnull=False),
            distinct=True,
        ),
        alunos_com_frequencia=Count(
            'turma__matriculas',
            filter=Q(turma__matriculas__status='ATIVA', turma__matriculas__frequencias__isnull=False),
            distinct=True,
        ),
    ).annotate(
        notas_pendentes=ExpressionWrapper(F('total_matriculados') - F('alunos_com_notas'), output_field=IntegerField()),
        frequencias_pendentes=ExpressionWrapper(F('total_matriculados') - F('alunos_com_frequencia'), output_field=IntegerField()),
    )


def apply_common_filters(queryset, params):
    search = params.get('search', '').strip()
    ano_letivo = params.get('ano_letivo', '').strip()
    periodo = params.get('periodo', '').strip()
    unidade = params.get('unidade', '').strip()
    curso = params.get('curso', '').strip()
    turma = params.get('turma', '').strip()
    professor = params.get('professor', '').strip()
    status_value = params.get('status', '').strip()

    if ano_letivo:
        queryset = queryset.filter(turma__ano_letivo=ano_letivo)
    if periodo:
        queryset = queryset.filter(periodo__icontains=periodo)
    if unidade:
        queryset = queryset.filter(turma__curso__unidade_id=unidade)
    if curso:
        queryset = queryset.filter(turma__curso_id=curso)
    if turma:
        queryset = queryset.filter(turma_id=turma)
    if professor:
        queryset = queryset.filter(turma__professor_responsavel_id=professor)
    if status_value:
        queryset = queryset.filter(status=status_value)

    if search:
        queryset = queryset.filter(
            Q(periodo__icontains=search)
            | Q(componente_curricular__icontains=search)
            | Q(observacoes__icontains=search)
            | Q(turma__nome__icontains=search)
            | Q(turma__curso__nome__icontains=search)
            | Q(turma__curso__unidade__nome__icontains=search)
            | Q(turma__professor_responsavel__first_name__icontains=search)
            | Q(turma__professor_responsavel__last_name__icontains=search)
        )

    return queryset

class DiarioListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'view'
    serializer_class = DiarioSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            self.access_action = 'academic_diary'
        else:
            self.access_action = 'view'
        return super().get_permissions()

    def get_queryset(self):
        queryset = DiarioAcademico.objects.select_related(
            'turma__curso__unidade',
            'turma__professor_responsavel',
            'aberto_por',
            'fechado_por',
        ).order_by('-turma__ano_letivo', 'turma__nome', '-id')
        queryset = filter_professor_scoped_queryset(
            self.request.user,
            queryset,
            professor_lookup='turma__professor_responsavel_id',
        )

        queryset = annotate_diario_queryset(queryset)
        queryset = apply_common_filters(queryset, self.request.query_params)
        return queryset.distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        aba = (request.query_params.get('aba') or 'TODOS').strip().upper()
        summary = {
            key: TAB_FILTERS[key](queryset).count()
            for key in TAB_FILTERS
        }

        filtered = TAB_FILTERS.get(aba, TAB_FILTERS['TODOS'])(queryset)
        page = self.paginate_queryset(filtered)
        serializer = self.get_serializer(page if page is not None else filtered, many=True)

        def normalize_results(rows):
            results = []
            source_rows = page if page is not None else filtered
            for row, data in zip(source_rows, rows):
                data['notas_pendentes'] = max(0, getattr(row, 'notas_pendentes', 0) or 0)
                data['frequencias_pendentes'] = max(0, getattr(row, 'frequencias_pendentes', 0) or 0)
                results.append(data)
            return results

        if page is not None:
            paginated = self.get_paginated_response(normalize_results(serializer.data))
            paginated.data['summary'] = summary
            paginated.data['active_tab'] = aba
            return paginated

        return Response({'results': normalize_results(serializer.data), 'summary': summary, 'active_tab': aba})

    def perform_create(self, serializer):
        turma = serializer.validated_data.get('turma')
        professor_id = getattr(turma, 'professor_responsavel_id', None)
        if not professor_owns_related_resource(self.request.user, professor_id=professor_id):
            raise PermissionDenied('Professor so pode operar diarios das turmas sob sua responsabilidade.')
        serializer.save(aberto_por=self.request.user)


class DiarioDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'view'

    def get_queryset(self):
        matriculas_qs = Matricula.objects.filter(status='ATIVA').select_related(
            'aluno__pessoa',
            'consolidacao',
        ).prefetch_related('notas', 'frequencias').order_by('aluno__last_name', 'aluno__first_name', 'id')

        return filter_professor_scoped_queryset(
            self.request.user,
            annotate_diario_queryset(DiarioAcademico.objects.select_related(
            'turma__curso__unidade',
            'turma__professor_responsavel',
            'aberto_por',
            'fechado_por',
        ).prefetch_related(
            Prefetch('turma__matriculas', queryset=matriculas_qs),
            Prefetch('materiais_aula', queryset=DiarioMaterialAula.objects.select_related('criado_por')),
            Prefetch('ocorrencias', queryset=DiarioOcorrencia.objects.select_related('registrado_por')),
        )),
            professor_lookup='turma__professor_responsavel_id',
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return DiarioDetailSerializer
        return DiarioSerializer

    def get_permissions(self):
        if self.request.method in {'PATCH', 'PUT', 'DELETE'}:
            self.access_action = 'academic_diary'
        else:
            self.access_action = 'view'
        return super().get_permissions()


class DiarioFecharApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'academic_diary'

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            DiarioAcademico.objects.all(),
            professor_lookup='turma__professor_responsavel_id',
        )

    def post(self, request, pk):
        diario = generics.get_object_or_404(self.get_queryset(), pk=pk)
        diario.status = 'FECHADO'
        diario.data_fechamento = timezone.localdate()
        diario.fechado_por = request.user
        diario.save(update_fields=['status', 'data_fechamento', 'fechado_por'])
        return Response(DiarioSerializer(diario).data)


class DiarioReabrirApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'academic_diary'

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            DiarioAcademico.objects.all(),
            professor_lookup='turma__professor_responsavel_id',
        )

    def post(self, request, pk):
        diario = generics.get_object_or_404(self.get_queryset(), pk=pk)
        diario.status = 'ABERTO'
        diario.data_fechamento = None
        diario.fechado_por = None
        diario.save(update_fields=['status', 'data_fechamento', 'fechado_por'])
        return Response(DiarioSerializer(diario).data)


class DiarioDocumentoApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'view'

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            DiarioAcademico.objects.all(),
            professor_lookup='turma__professor_responsavel_id',
        )

    def get(self, request, pk):
        diario = generics.get_object_or_404(self.get_queryset(), pk=pk)
        return Response({'documento': diario.gerar_documento()})


class DiarioMaterialCreateApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'academic_diary'

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            DiarioAcademico.objects.all(),
            professor_lookup='turma__professor_responsavel_id',
        )

    def post(self, request, pk):
        diario = generics.get_object_or_404(self.get_queryset(), pk=pk)
        serializer = DiarioMaterialAulaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(diario=diario, criado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DiarioOcorrenciaCreateApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'turmas'
    access_surface = 'api'
    access_action = 'academic_diary'

    def get_queryset(self):
        return filter_professor_scoped_queryset(
            self.request.user,
            DiarioAcademico.objects.all(),
            professor_lookup='turma__professor_responsavel_id',
        )

    def post(self, request, pk):
        diario = generics.get_object_or_404(self.get_queryset(), pk=pk)
        serializer = DiarioOcorrenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(diario=diario, registrado_por=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)