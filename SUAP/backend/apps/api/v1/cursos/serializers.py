from rest_framework import serializers

from apps.cursos.models import AreaCurso, ComponenteCurricular, Curso


class EixoTecnologicoSerializer(serializers.Serializer):
    descricao = serializers.CharField(source='eixo_tecnologico')


class ComponenteCurricularSerializer(serializers.ModelSerializer):
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