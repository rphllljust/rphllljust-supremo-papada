from django.db.models import Q
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.api.permissions import CanAccessModule
from apps.api.v1.pagination import StandardResultsSetPagination
from apps.cursos.models import OfertaCurso
from apps.cursos.services import log_oferta_event, sync_oferta_curso_to_moodle

from .serializers import OfertaCursoLogSerializer, OfertaCursoSerializer


class OfertaCursoListApiView(generics.ListCreateAPIView):
    permission_classes = [CanAccessModule]
    module_name = 'cursos'
    access_surface = 'api'
    access_action = 'view'
    serializer_class = OfertaCursoSerializer
    pagination_class = StandardResultsSetPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            self.access_action = 'manage'
        else:
            self.access_action = 'view'
        return super().get_permissions()

    def get_queryset(self):
        queryset = OfertaCurso.objects.select_related(
            'curso_base',
            'matriz_curricular',
            'polo',
            'calendario_letivo',
        ).prefetch_related('logs')
        params = self.request.query_params
        search = (params.get('search') or '').strip()
        curso_base = (params.get('curso_base') or '').strip()
        matriz_curricular = (params.get('matriz_curricular') or '').strip()
        polo = (params.get('polo') or '').strip()
        ano_oferta = (params.get('ano_oferta') or '').strip()
        status = (params.get('status') or '').strip().upper()
        sync_status = (params.get('last_sync_status') or '').strip().lower()

        if curso_base:
            queryset = queryset.filter(curso_base_id=curso_base)
        if matriz_curricular:
            queryset = queryset.filter(matriz_curricular_id=matriz_curricular)
        if polo:
            queryset = queryset.filter(polo_id=polo)
        if ano_oferta:
            queryset = queryset.filter(ano_oferta=ano_oferta)
        if status:
            queryset = queryset.filter(status=status)
        if sync_status:
            queryset = queryset.filter(last_sync_status__iexact=sync_status)
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search)
                | Q(curso_base__nome__icontains=search)
                | Q(matriz_curricular__nome__icontains=search)
                | Q(polo__nome__icontains=search)
                | Q(codigo_turma__icontains=search)
            )

        return queryset.order_by('-ano_oferta', '-periodo_letivo', 'nome', 'id')


class OfertaCursoDetailApiView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [CanAccessModule]
    module_name = 'cursos'
    access_surface = 'api'
    serializer_class = OfertaCursoSerializer
    queryset = OfertaCurso.objects.select_related('curso_base', 'matriz_curricular', 'polo', 'calendario_letivo').prefetch_related('logs')

    def get_permissions(self):
        if self.request.method in {'PUT', 'PATCH', 'DELETE'}:
            self.access_action = 'manage'
        else:
            self.access_action = 'view'
        return super().get_permissions()

    def perform_update(self, serializer):
        instance = serializer.save()
        log_oferta_event(
            oferta=instance,
            evento='atualizacao_oferta',
            status='success',
            mensagem='Oferta de curso atualizada com sucesso.',
            payload={'oferta_id': instance.id},
        )

    def perform_destroy(self, instance):
        if instance.moodle_course_id:
            raise ValidationError('Não é possível excluir uma oferta já sincronizada com o Moodle nesta fase.')
        instance.delete()


class OfertaCursoLogsApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'cursos'
    access_surface = 'api'
    access_action = 'view'

    def get(self, request, pk):
        oferta = OfertaCurso.objects.prefetch_related('logs').get(pk=pk)
        serializer = OfertaCursoLogSerializer(oferta.logs.all(), many=True)
        return Response(serializer.data)


class OfertaCursoSyncMoodleApiView(APIView):
    permission_classes = [CanAccessModule]
    module_name = 'cursos'
    access_surface = 'api'
    access_action = 'manage'

    def post(self, request, pk):
        oferta = OfertaCurso.objects.select_related('curso_base', 'matriz_curricular', 'polo', 'calendario_letivo').get(pk=pk)
        try:
            result = sync_oferta_curso_to_moodle(oferta, unidade_codigo=(request.data.get('unidade_codigo') or oferta.polo.codigo or 'sede'))
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        serializer = OfertaCursoSerializer(result['oferta'], context={'request': request})
        return Response(
            {
                'detail': 'Oferta sincronizada com o Moodle.',
                'oferta': serializer.data,
                'moodle': result['moodle'],
            }
        )
