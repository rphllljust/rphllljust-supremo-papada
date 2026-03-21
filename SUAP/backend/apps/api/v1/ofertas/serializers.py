from rest_framework import serializers

from apps.cursos.models import CalendarioLetivo, Curso, MatrizCurricular, OfertaCurso, OfertaCursoLog
from apps.cursos.services import create_oferta_curso
from apps.unidades.models import Unidade


class OfertaCursoLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfertaCursoLog
        fields = ['id', 'evento', 'status', 'mensagem', 'payload', 'created_at']


class OfertaCursoSerializer(serializers.ModelSerializer):
    curso_base_id = serializers.PrimaryKeyRelatedField(source='curso_base', queryset=Curso.objects.filter(tipo_curso='tecnico'))
    curso_base_nome = serializers.CharField(source='curso_base.nome', read_only=True)
    matriz_curricular_id = serializers.PrimaryKeyRelatedField(source='matriz_curricular', queryset=MatrizCurricular.objects.all(), required=False, allow_null=True)
    matriz_curricular_nome = serializers.CharField(source='matriz_curricular.nome', read_only=True)
    polo_id = serializers.PrimaryKeyRelatedField(source='polo', queryset=Unidade.objects.all())
    polo_nome = serializers.CharField(source='polo.nome', read_only=True)
    calendario_letivo_id = serializers.PrimaryKeyRelatedField(source='calendario_letivo', queryset=CalendarioLetivo.objects.all())
    calendario_letivo_nome = serializers.SerializerMethodField(read_only=True)
    vagas_disponiveis = serializers.IntegerField(read_only=True)
    pode_sincronizar_moodle = serializers.BooleanField(read_only=True)
    modulos_previstos = serializers.IntegerField(source='matriz_curricular.total_modulos', read_only=True)
    usou_template_moodle = serializers.BooleanField(read_only=True)
    template_moodle_disponivel = serializers.BooleanField(read_only=True)
    moodle_sync_mode_label = serializers.SerializerMethodField(read_only=True)
    logs_recentes = OfertaCursoLogSerializer(source='logs.all', many=True, read_only=True)

    class Meta:
        model = OfertaCurso
        fields = [
            'id',
            'curso_base_id',
            'curso_base_nome',
            'matriz_curricular_id',
            'matriz_curricular_nome',
            'polo_id',
            'polo_nome',
            'calendario_letivo_id',
            'calendario_letivo_nome',
            'nome',
            'codigo_turma',
            'ano_oferta',
            'periodo_letivo',
            'turno',
            'vagas_totais',
            'vagas_ocupadas',
            'vagas_disponiveis',
            'status',
            'observacao',
            'moodle_course_id',
            'moodle_shortname',
            'moodle_category_id',
            'moodle_sync_mode',
            'moodle_sync_mode_label',
            'moodle_template_applied',
            'moodle_template_source_course_id',
            'moodle_template_source_shortname',
            'moodle_sync_fallback_reason',
            'last_sync_at',
            'last_sync_status',
            'last_sync_message',
            'pode_sincronizar_moodle',
            'modulos_previstos',
            'usou_template_moodle',
            'template_moodle_disponivel',
            'logs_recentes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'moodle_course_id',
            'moodle_shortname',
            'moodle_category_id',
            'moodle_sync_mode',
            'moodle_template_applied',
            'moodle_template_source_course_id',
            'moodle_template_source_shortname',
            'moodle_sync_fallback_reason',
            'last_sync_at',
            'last_sync_status',
            'last_sync_message',
            'vagas_disponiveis',
            'pode_sincronizar_moodle',
            'modulos_previstos',
            'usou_template_moodle',
            'template_moodle_disponivel',
            'moodle_sync_mode_label',
            'logs_recentes',
            'created_at',
            'updated_at',
        ]

    def get_calendario_letivo_nome(self, obj):
        return f'{obj.calendario_letivo.ano_letivo} [{obj.calendario_letivo.status}]'

    def get_moodle_sync_mode_label(self, obj):
        return obj.get_moodle_sync_mode_display() if obj.moodle_sync_mode else ''

    def validate(self, attrs):
        curso_base = attrs.get('curso_base', getattr(self.instance, 'curso_base', None))
        matriz = attrs.get('matriz_curricular', getattr(self.instance, 'matriz_curricular', None))
        calendario = attrs.get('calendario_letivo', getattr(self.instance, 'calendario_letivo', None))

        if curso_base and matriz is None:
            matriz = curso_base.matriz_curricular
            if matriz is None:
                raise serializers.ValidationError({'matriz_curricular_id': 'O curso base não possui matriz curricular vigente ou vinculada.'})
            attrs['matriz_curricular'] = matriz

        if curso_base and matriz and matriz.curso_base_id != curso_base.id:
            raise serializers.ValidationError({'matriz_curricular_id': 'A matriz curricular deve pertencer ao curso base selecionado.'})

        if curso_base and calendario and calendario.curso_id != curso_base.id:
            raise serializers.ValidationError({'calendario_letivo_id': 'O calendário letivo deve pertencer ao mesmo curso base.'})

        nome = attrs.get('nome')
        if nome is not None:
            attrs['nome'] = nome.strip()

        codigo_turma = attrs.get('codigo_turma')
        if codigo_turma is not None:
            attrs['codigo_turma'] = codigo_turma.strip()

        periodo_letivo = attrs.get('periodo_letivo')
        if periodo_letivo is not None:
            attrs['periodo_letivo'] = periodo_letivo.strip()

        observacao = attrs.get('observacao')
        if observacao is not None:
            attrs['observacao'] = observacao.strip()

        return attrs

    def create(self, validated_data):
        return create_oferta_curso(**validated_data)
