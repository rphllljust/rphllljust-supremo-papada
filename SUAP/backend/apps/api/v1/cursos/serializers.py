from rest_framework import serializers

from apps.cursos.models import AreaCurso, CalendarioLetivo, ComponenteCurricular, Curso, EixoTecnologico, MatrizCurricular, MatrizCurricularLog, NivelEnsino, TipoComponente


class EixoTecnologicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EixoTecnologico
        fields = ['id', 'descricao']


class EixoTecnologicoManageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EixoTecnologico
        fields = ['id', 'descricao']

    def validate_descricao(self, value):
        descricao = value.strip()
        if not descricao:
            raise serializers.ValidationError('Informe a descrição do eixo tecnológico.')
        return descricao

    def update(self, instance, validated_data):
        descricao_anterior = instance.descricao
        instance = super().update(instance, validated_data)
        if descricao_anterior != instance.descricao:
            Curso.objects.filter(eixo_tecnologico=descricao_anterior).update(eixo_tecnologico=instance.descricao)
        return instance


class TipoComponenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoComponente
        fields = ['id', 'descricao']

    def validate_descricao(self, value):
        descricao = value.strip()
        if not descricao:
            raise serializers.ValidationError('Informe a descrição do tipo do componente.')
        return descricao


class NivelEnsinoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NivelEnsino
        fields = ['id', 'descricao']

    def validate_descricao(self, value):
        descricao = value.strip()
        if not descricao:
            raise serializers.ValidationError('Informe a descrição do nível de ensino.')
        return descricao


class ComponenteCurricularSerializer(serializers.ModelSerializer):
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all(), write_only=True, required=False)
    nome = serializers.CharField(read_only=True)
    descricao = serializers.CharField(source='nome')
    matriz_curricular = serializers.SerializerMethodField(read_only=True)
    matriz_curricular_id = serializers.PrimaryKeyRelatedField(source='matriz_curricular', queryset=MatrizCurricular.objects.all(), required=False, allow_null=True)
    matriz_curricular_nome = serializers.SerializerMethodField(read_only=True)
    tipo_componente_id = serializers.PrimaryKeyRelatedField(source='tipo_componente_catalogo', queryset=TipoComponente.objects.all(), required=False, allow_null=True)
    tipo_componente_nome = serializers.CharField(source='tipo_componente_catalogo.descricao', read_only=True)
    nivel_ensino_id = serializers.PrimaryKeyRelatedField(source='nivel_ensino_catalogo', queryset=NivelEnsino.objects.all(), required=False, allow_null=True)
    nivel_ensino_nome = serializers.CharField(source='nivel_ensino_catalogo.descricao', read_only=True)
    curso_id = serializers.IntegerField(read_only=True)
    curso_nome = serializers.CharField(source='curso.nome', read_only=True)
    esta_ativo = serializers.BooleanField(source='ativo', required=False)
    utilizado = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ComponenteCurricular
        fields = [
            'id',
            'abreviatura',
            'sigla',
            'nome',
            'descricao',
            'descricao_diploma_historico',
            'diretoria',
            'tipo_componente',
            'tipo_componente_id',
            'tipo_componente_nome',
            'nivel_ensino',
            'nivel_ensino_id',
            'nivel_ensino_nome',
            'curso',
            'matriz_curricular',
            'matriz_curricular_id',
            'matriz_curricular_nome',
            'curso_id',
            'curso_nome',
            'grupo_atuacao',
            'carga_horaria',
            'hora_aula',
            'qtd_creditos',
            'modulo_numero',
            'modulo_nome',
            'ordem_no_modulo',
            'esta_ativo',
            'sigla_qacademico',
            'observacao',
            'utilizado',
        ]

    def get_utilizado(self, obj):
        return True

    def get_matriz_curricular(self, obj):
        return obj.matriz_curricular_efetiva_nome

    def get_matriz_curricular_nome(self, obj):
        return obj.matriz_curricular_efetiva_nome

    def validate(self, attrs):
        matriz = attrs.get('matriz_curricular', getattr(self.instance, 'matriz_curricular', None))
        curso = attrs.get('curso', getattr(self.instance, 'curso', None))
        tipo_catalogo = attrs.get('tipo_componente_catalogo', getattr(self.instance, 'tipo_componente_catalogo', None))
        nivel_catalogo = attrs.get('nivel_ensino_catalogo', getattr(self.instance, 'nivel_ensino_catalogo', None))

        tipo_texto = attrs.get('tipo_componente', getattr(self.instance, 'tipo_componente', ''))
        nivel_texto = attrs.get('nivel_ensino', getattr(self.instance, 'nivel_ensino', ''))

        if matriz and curso is None:
            attrs['curso'] = matriz.curso_base
            curso = attrs['curso']

        if curso is None:
            raise serializers.ValidationError({'curso': 'Informe o curso ou a matriz curricular do componente.'})

        if matriz and matriz.curso_base_id != curso.id:
            raise serializers.ValidationError({'matriz_curricular_id': 'A matriz curricular deve pertencer ao mesmo curso informado.'})

        if tipo_catalogo is None and (tipo_texto or '').strip():
            attrs['tipo_componente_catalogo'], _ = TipoComponente.objects.get_or_create(descricao=tipo_texto.strip())
        if nivel_catalogo is None and (nivel_texto or '').strip():
            attrs['nivel_ensino_catalogo'], _ = NivelEnsino.objects.get_or_create(descricao=nivel_texto.strip())

        if 'tipo_componente_catalogo' in attrs and attrs.get('tipo_componente_catalogo') is None and 'tipo_componente' not in attrs:
            attrs['tipo_componente'] = ''
        if 'nivel_ensino_catalogo' in attrs and attrs.get('nivel_ensino_catalogo') is None and 'nivel_ensino' not in attrs:
            attrs['nivel_ensino'] = ''

        if attrs.get('tipo_componente_catalogo') is not None:
            attrs['tipo_componente'] = attrs['tipo_componente_catalogo'].descricao
        elif 'tipo_componente' in attrs:
            attrs['tipo_componente'] = (attrs.get('tipo_componente') or '').strip()

        if attrs.get('nivel_ensino_catalogo') is not None:
            attrs['nivel_ensino'] = attrs['nivel_ensino_catalogo'].descricao
        elif 'nivel_ensino' in attrs:
            attrs['nivel_ensino'] = (attrs.get('nivel_ensino') or '').strip()

        return attrs


class AreaCursoSerializer(serializers.ModelSerializer):
    descricao = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AreaCurso
        fields = [
            'id',
            'descricao',
            'codigo_cine',
            'codigo_area_detalhada',
            'codigo_area_especifica',
            'codigo_area_geral',
            'cine',
            'area_detalhada',
            'area_especifica',
            'area_geral',
        ]

    def get_descricao(self, obj):
        return obj.cine or obj.area_detalhada or obj.descricao

    def create(self, validated_data):
        validated_data['descricao'] = self._build_descricao(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['descricao'] = self._build_descricao(validated_data, instance)
        return super().update(instance, validated_data)

    def _build_descricao(self, validated_data, instance=None):
        cine = validated_data.get('cine', getattr(instance, 'cine', ''))
        area_detalhada = validated_data.get('area_detalhada', getattr(instance, 'area_detalhada', ''))
        descricao_atual = getattr(instance, 'descricao', '') if instance else ''
        return (cine or area_detalhada or descricao_atual).strip()


class CursoSerializer(serializers.ModelSerializer):
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)
    area_curso_nome = serializers.CharField(source="area_curso.descricao", read_only=True)
    origem = serializers.SerializerMethodField(read_only=True)
    matriz_curricular_id = serializers.PrimaryKeyRelatedField(source='matriz_curricular', queryset=MatrizCurricular.objects.all(), required=False, allow_null=True)
    matriz_curricular_nome = serializers.CharField(source='matriz_curricular.nome', read_only=True)
    matriz_curricular_status = serializers.CharField(source='matriz_curricular.status', read_only=True)

    class Meta:
        model = Curso
        fields = [
            "id",
            "nome",
            "tipo_curso",
            "sigla",
            "moodle_course_id",
            "moodle_shortname",
            "origem",
            "unidade",
            "unidade_nome",
            "area_curso",
            "area_curso_nome",
            "eixo_tecnologico",
            "carga_horaria",
            "matriz_curricular_id",
            "matriz_curricular_nome",
            "matriz_curricular_status",
        ]

    def validate_nome(self, value):
        nome = value.strip()
        if not nome:
            raise serializers.ValidationError('Informe o nome do curso.')
        return nome

    def validate_sigla(self, value):
        return value.strip()

    def validate_eixo_tecnologico(self, value):
        return value.strip()

    def create(self, validated_data):
        self._sync_eixo_tecnologico(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._sync_eixo_tecnologico(validated_data)
        return super().update(instance, validated_data)

    def _sync_eixo_tecnologico(self, validated_data):
        descricao = validated_data.get('eixo_tecnologico', '')
        if descricao:
            EixoTecnologico.objects.get_or_create(descricao=descricao)

    def get_origem(self, obj):
        return 'moodle' if obj.moodle_course_id else 'manual'


class CalendarioLetivoSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source='curso.nome', read_only=True)

    class Meta:
        model = CalendarioLetivo
        fields = [
            'id',
            'ano_letivo',
            'curso',
            'curso_nome',
            'data_inicio',
            'data_fim',
            'dias_letivos',
            'status',
            'descricao',
        ]


class MatrizCurricularLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrizCurricularLog
        fields = ['id', 'evento', 'status', 'mensagem', 'payload', 'created_at']


class MatrizCurricularSerializer(serializers.ModelSerializer):
    curso_base_nome = serializers.CharField(source='curso_base.nome', read_only=True)
    curso_base_sigla = serializers.CharField(source='curso_base.sigla', read_only=True)
    curso_base_tipo = serializers.CharField(source='curso_base.tipo_curso', read_only=True)
    total_componentes = serializers.IntegerField(source='componentes.count', read_only=True)
    total_modulos = serializers.IntegerField(read_only=True)
    permite_edicao = serializers.BooleanField(read_only=True)
    pode_publicar = serializers.BooleanField(read_only=True)
    pode_encerrar = serializers.BooleanField(read_only=True)
    pode_definir_vigente = serializers.BooleanField(read_only=True)
    pode_clonar = serializers.SerializerMethodField(read_only=True)
    possui_template_moodle = serializers.BooleanField(read_only=True)
    pode_sincronizar_template = serializers.BooleanField(read_only=True)
    template_status = serializers.SerializerMethodField(read_only=True)
    componentes_por_modulo = serializers.SerializerMethodField(read_only=True)
    logs_recentes = MatrizCurricularLogSerializer(source='logs.all', many=True, read_only=True)

    class Meta:
        model = MatrizCurricular
        fields = [
            'id',
            'curso_base',
            'curso_base_nome',
            'curso_base_sigla',
            'curso_base_tipo',
            'nome',
            'ano_referencia',
            'versao',
            'status',
            'ativa',
            'descricao',
            'moodle_template_course_id',
            'moodle_template_shortname',
            'moodle_template_category_id',
            'last_sync_at',
            'last_sync_status',
            'last_sync_message',
            'created_at',
            'updated_at',
            'total_componentes',
            'total_modulos',
            'permite_edicao',
            'pode_publicar',
            'pode_encerrar',
            'pode_definir_vigente',
            'pode_clonar',
            'possui_template_moodle',
            'pode_sincronizar_template',
            'template_status',
            'componentes_por_modulo',
            'logs_recentes',
        ]
        read_only_fields = [
            'moodle_template_course_id',
            'moodle_template_shortname',
            'moodle_template_category_id',
            'last_sync_at',
            'last_sync_status',
            'last_sync_message',
            'created_at',
            'updated_at',
            'total_componentes',
            'total_modulos',
            'permite_edicao',
            'pode_publicar',
            'pode_encerrar',
            'pode_definir_vigente',
            'pode_clonar',
            'possui_template_moodle',
            'pode_sincronizar_template',
            'template_status',
            'componentes_por_modulo',
            'logs_recentes',
        ]

    def validate_nome(self, value):
        nome = value.strip()
        if not nome:
            raise serializers.ValidationError('Informe o nome da matriz curricular.')
        return nome

    def validate_versao(self, value):
        versao = value.strip()
        if not versao:
            raise serializers.ValidationError('Informe a versão da matriz curricular.')
        return versao

    def validate(self, attrs):
        if self.instance and self.instance.status == 'VIGENTE':
            raise serializers.ValidationError('Matrizes vigentes não podem ser editadas diretamente. Clone a matriz para gerar uma nova versão.')

        curso_base = attrs.get('curso_base', getattr(self.instance, 'curso_base', None))
        if curso_base and curso_base.tipo_curso != 'tecnico':
            raise serializers.ValidationError({'curso_base': 'A matriz curricular explícita está disponível apenas para cursos técnicos nesta fase.'})
        return attrs

    def get_pode_clonar(self, obj):
        return True

    def get_componentes_por_modulo(self, obj):
        grupos = []
        for modulo in obj.componentes_por_modulo():
            grupos.append(
                {
                    'modulo_numero': modulo['modulo_numero'],
                    'modulo_nome': modulo['modulo_nome'],
                    'componentes': ComponenteCurricularSerializer(modulo['componentes'], many=True, context=self.context).data,
                }
            )
        return grupos

    def get_template_status(self, obj):
        return {
            'possui_template_moodle': obj.possui_template_moodle,
            'pode_sincronizar_template': obj.pode_sincronizar_template,
            'moodle_template_course_id': obj.moodle_template_course_id,
            'moodle_template_shortname': obj.moodle_template_shortname,
            'moodle_template_category_id': obj.moodle_template_category_id,
            'last_sync_at': obj.last_sync_at,
            'last_sync_status': obj.last_sync_status,
            'last_sync_message': obj.last_sync_message,
        }