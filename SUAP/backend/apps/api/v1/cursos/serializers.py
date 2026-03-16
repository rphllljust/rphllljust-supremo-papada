from rest_framework import serializers

from apps.cursos.models import AreaCurso, ComponenteCurricular, Curso, EixoTecnologico


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


class ComponenteCurricularSerializer(serializers.ModelSerializer):
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all(), write_only=True)
    nome = serializers.CharField(read_only=True)
    descricao = serializers.CharField(source='nome')
    matriz_curricular = serializers.CharField(source='curso.nome', read_only=True)
    curso_id = serializers.IntegerField(source='curso_id', read_only=True)
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
            'nivel_ensino',
            'curso',
            'matriz_curricular',
            'curso_id',
            'grupo_atuacao',
            'carga_horaria',
            'hora_aula',
            'qtd_creditos',
            'esta_ativo',
            'sigla_qacademico',
            'observacao',
            'utilizado',
        ]

    def get_utilizado(self, obj):
        return True


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

    class Meta:
        model = Curso
        fields = [
            "id",
            "nome",
            "sigla",
            "unidade",
            "unidade_nome",
            "area_curso",
            "area_curso_nome",
            "eixo_tecnologico",
            "carga_horaria",
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