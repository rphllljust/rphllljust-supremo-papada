from rest_framework import serializers

from .models import (
    CoRequisito,
    ComponenteCurricular,
    ConfiguracaoCursoWizard,
    Coordenador,
    Curso,
    CursoCoordenador,
    EstruturaCurso,
    MatrizComponente,
    MatrizCurricular,
    PreRequisito,
)
from .validators import (
    WIZARD_FLOW,
    validate_componentes_compartilham_matriz,
    validate_corequisito_auto_referencia,
    validate_corequisito_duplicado,
    validate_matriz_componente_duplicado,
    validate_prerequisito_auto_referencia,
    validate_prerequisito_sem_ciclo,
)


class EstruturaCursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstruturaCurso
        fields = [
            "id",
            "nome",
            "descricao",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]


class MatrizCurricularSerializer(serializers.ModelSerializer):
    estrutura_curso_nome = serializers.CharField(source="estrutura_curso.nome", read_only=True)

    class Meta:
        model = MatrizCurricular
        fields = [
            "id",
            "nome",
            "codigo",
            "versao",
            "carga_horaria_total",
            "estrutura_curso",
            "estrutura_curso_nome",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em", "estrutura_curso_nome"]


class ComponenteCurricularSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = ComponenteCurricular
        fields = [
            "id",
            "codigo",
            "nome",
            "carga_horaria",
            "tipo",
            "tipo_display",
            "ementa",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em", "tipo_display"]


class MatrizComponenteSerializer(serializers.ModelSerializer):
    matriz_curricular_nome = serializers.CharField(source="matriz_curricular.nome", read_only=True)
    componente_curricular_nome = serializers.CharField(source="componente_curricular.nome", read_only=True)
    componente_curricular_codigo = serializers.CharField(source="componente_curricular.codigo", read_only=True)

    class Meta:
        model = MatrizComponente
        fields = [
            "id",
            "matriz_curricular",
            "matriz_curricular_nome",
            "componente_curricular",
            "componente_curricular_nome",
            "componente_curricular_codigo",
            "periodo",
            "carga_horaria",
            "obrigatorio",
            "ordem",
            "criado_em",
        ]
        read_only_fields = [
            "criado_em",
            "matriz_curricular_nome",
            "componente_curricular_nome",
            "componente_curricular_codigo",
        ]

    def validate(self, attrs):
        matriz = attrs.get("matriz_curricular") or getattr(self.instance, "matriz_curricular", None)
        componente = attrs.get("componente_curricular") or getattr(self.instance, "componente_curricular", None)

        if matriz and componente:
            validate_matriz_componente_duplicado(
                matriz.id,
                componente.id,
                instance_id=getattr(self.instance, "id", None),
            )

        return attrs


class PreRequisitoSerializer(serializers.ModelSerializer):
    componente_nome = serializers.CharField(source="componente.nome", read_only=True)
    requisito_nome = serializers.CharField(source="requisito.nome", read_only=True)

    class Meta:
        model = PreRequisito
        fields = [
            "id",
            "componente",
            "componente_nome",
            "requisito",
            "requisito_nome",
            "criado_em",
        ]
        read_only_fields = ["criado_em", "componente_nome", "requisito_nome"]

    def validate(self, attrs):
        componente = attrs.get("componente") or getattr(self.instance, "componente", None)
        requisito = attrs.get("requisito") or getattr(self.instance, "requisito", None)

        if componente and requisito:
            validate_prerequisito_auto_referencia(componente.id, requisito.id)
            validate_componentes_compartilham_matriz(componente.id, requisito.id, field_name="requisito")
            validate_prerequisito_sem_ciclo(
                componente.id,
                requisito.id,
                instance_id=getattr(self.instance, "id", None),
            )

        return attrs


class CoRequisitoSerializer(serializers.ModelSerializer):
    componente_nome = serializers.CharField(source="componente.nome", read_only=True)
    requisito_nome = serializers.CharField(source="requisito.nome", read_only=True)

    class Meta:
        model = CoRequisito
        fields = [
            "id",
            "componente",
            "componente_nome",
            "requisito",
            "requisito_nome",
            "criado_em",
        ]
        read_only_fields = ["criado_em", "componente_nome", "requisito_nome"]

    def validate(self, attrs):
        componente = attrs.get("componente") or getattr(self.instance, "componente", None)
        requisito = attrs.get("requisito") or getattr(self.instance, "requisito", None)

        if componente and requisito:
            validate_corequisito_auto_referencia(componente.id, requisito.id)
            validate_componentes_compartilham_matriz(componente.id, requisito.id, field_name="requisito")
            validate_corequisito_duplicado(
                componente.id,
                requisito.id,
                instance_id=getattr(self.instance, "id", None),
            )

        return attrs


class CursoSerializer(serializers.ModelSerializer):
    modalidade_display = serializers.CharField(source="get_modalidade_display", read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)
    matriz_curricular_nome = serializers.CharField(source="matriz_curricular.nome", read_only=True)
    estrutura_curso_nome = serializers.CharField(source="estrutura_curso.nome", read_only=True)

    class Meta:
        model = Curso
        fields = [
            "id",
            "codigo",
            "nome",
            "nome_curto",
            "modalidade",
            "modalidade_display",
            "carga_horaria_total",
            "situacao",
            "situacao_display",
            "matriz_curricular",
            "matriz_curricular_nome",
            "estrutura_curso",
            "estrutura_curso_nome",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "criado_em",
            "atualizado_em",
            "modalidade_display",
            "situacao_display",
            "matriz_curricular_nome",
            "estrutura_curso_nome",
        ]


class CoordenadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordenador
        fields = [
            "id",
            "nome",
            "email",
            "matricula",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]


class CursoCoordenadorSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    coordenador_nome = serializers.CharField(source="coordenador.nome", read_only=True)

    class Meta:
        model = CursoCoordenador
        fields = [
            "id",
            "curso",
            "curso_nome",
            "coordenador",
            "coordenador_nome",
            "principal",
            "inicio_vigencia",
            "fim_vigencia",
        ]
        read_only_fields = ["curso_nome", "coordenador_nome"]


class ConfiguracaoCursoWizardSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source="usuario.username", read_only=True)
    estrutura_curso_nome = serializers.CharField(source="estrutura_curso.nome", read_only=True)
    matriz_curricular_nome = serializers.CharField(source="matriz_curricular.nome", read_only=True)
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    etapa_atual_display = serializers.CharField(source="get_etapa_atual_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ConfiguracaoCursoWizard
        fields = [
            "id",
            "usuario",
            "usuario_username",
            "etapa_atual",
            "etapa_atual_display",
            "estrutura_curso",
            "estrutura_curso_nome",
            "matriz_curricular",
            "matriz_curricular_nome",
            "curso",
            "curso_nome",
            "status",
            "status_display",
            "payload_parcial",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "criado_em",
            "atualizado_em",
            "usuario_username",
            "estrutura_curso_nome",
            "matriz_curricular_nome",
            "curso_nome",
            "etapa_atual_display",
            "status_display",
        ]


class WizardSalvarEtapaSerializer(serializers.Serializer):
    etapa = serializers.ChoiceField(choices=WIZARD_FLOW, required=False)
    payload = serializers.JSONField(required=False)
    estrutura_curso = serializers.IntegerField(required=False, allow_null=True)
    matriz_curricular = serializers.IntegerField(required=False, allow_null=True)
    curso = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Informe ao menos um campo para salvar a etapa.")
        return attrs


class WizardAcaoResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    etapa_atual = serializers.CharField()
    status = serializers.CharField()


class WizardResumoResponseSerializer(serializers.Serializer):
    resumo = serializers.JSONField()
