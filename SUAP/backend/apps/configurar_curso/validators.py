from collections import defaultdict

from django.db.models import Q
from rest_framework.exceptions import ValidationError

from .models import (
    CoRequisito,
    ConfiguracaoCursoWizard,
    CursoCoordenador,
    MatrizComponente,
    PreRequisito,
)


WIZARD_FLOW = [
    ConfiguracaoCursoWizard.ETAPA_ESTRUTURA,
    ConfiguracaoCursoWizard.ETAPA_MATRIZ,
    ConfiguracaoCursoWizard.ETAPA_COMPONENTES,
    ConfiguracaoCursoWizard.ETAPA_REQUISITOS,
    ConfiguracaoCursoWizard.ETAPA_CURSO,
    ConfiguracaoCursoWizard.ETAPA_COORDENADORES,
    ConfiguracaoCursoWizard.ETAPA_RESUMO,
]


def validate_required_fields(payload, required_fields):
    missing = [field for field in required_fields if payload.get(field) in (None, "", [])]
    if missing:
        raise ValidationError({field: "Campo obrigatorio." for field in missing})


def validate_matriz_componente_duplicado(matriz_id, componente_id, instance_id=None):
    queryset = MatrizComponente.objects.filter(
        matriz_curricular_id=matriz_id,
        componente_curricular_id=componente_id,
    )

    if instance_id:
        queryset = queryset.exclude(pk=instance_id)

    if queryset.exists():
        raise ValidationError({
            "componente_curricular": "Este componente ja esta vinculado a matriz curricular informada.",
        })


def validate_componentes_compartilham_matriz(componente_id, requisito_id, field_name="requisito"):
    matrizes_componente = set(
        MatrizComponente.objects.filter(componente_curricular_id=componente_id).values_list("matriz_curricular_id", flat=True)
    )
    matrizes_requisito = set(
        MatrizComponente.objects.filter(componente_curricular_id=requisito_id).values_list("matriz_curricular_id", flat=True)
    )

    if not matrizes_componente or not matrizes_requisito or not (matrizes_componente & matrizes_requisito):
        raise ValidationError({
            field_name: "Os componentes devem estar vinculados a pelo menos uma mesma matriz curricular.",
        })


def validate_prerequisito_auto_referencia(componente_id, requisito_id):
    if componente_id == requisito_id:
        raise ValidationError({"requisito": "Um componente nao pode ser pre-requisito dele mesmo."})


def validate_corequisito_auto_referencia(componente_id, requisito_id):
    if componente_id == requisito_id:
        raise ValidationError({"requisito": "Um componente nao pode ser co-requisito dele mesmo."})


def _build_prerequisito_graph(exclude_id=None):
    queryset = PreRequisito.objects.all()

    if exclude_id:
        queryset = queryset.exclude(pk=exclude_id)

    graph = defaultdict(set)
    for componente_id, requisito_id in queryset.values_list("componente_id", "requisito_id"):
        graph[componente_id].add(requisito_id)

    return graph


def _has_path(graph, start, target):
    if start == target:
        return True

    visited = set()
    stack = [start]

    while stack:
        node = stack.pop()

        if node in visited:
            continue

        visited.add(node)

        for next_node in graph.get(node, set()):
            if next_node == target:
                return True
            if next_node not in visited:
                stack.append(next_node)

    return False


def validate_prerequisito_sem_ciclo(componente_id, requisito_id, instance_id=None):
    graph = _build_prerequisito_graph(exclude_id=instance_id)
    graph[componente_id].add(requisito_id)

    if _has_path(graph, requisito_id, componente_id):
        raise ValidationError({"requisito": "Relacao invalida: ciclo de pre-requisito identificado."})


def validate_corequisito_duplicado(componente_id, requisito_id, instance_id=None):
    queryset = CoRequisito.objects.filter(
        Q(componente_id=componente_id, requisito_id=requisito_id)
        | Q(componente_id=requisito_id, requisito_id=componente_id)
    )

    if instance_id:
        queryset = queryset.exclude(pk=instance_id)

    if queryset.exists():
        raise ValidationError({"requisito": "Este co-requisito ja foi cadastrado para o componente informado."})


def validate_curso_com_matriz(curso):
    if not curso or not curso.matriz_curricular_id:
        raise ValidationError({"curso": "Um curso nao pode ser concluido sem matriz curricular vinculada."})


def _validate_wizard_estrutura(wizard):
    if not wizard.estrutura_curso_id:
        raise ValidationError({"estrutura_curso": "Selecione ou cadastre uma estrutura de curso antes de avancar."})


def _validate_wizard_matriz(wizard):
    if not wizard.matriz_curricular_id:
        raise ValidationError({"matriz_curricular": "Cadastre ou selecione uma matriz curricular antes de avancar."})

    if not wizard.matriz_curricular.estrutura_curso_id:
        raise ValidationError({"matriz_curricular": "A matriz curricular precisa estar vinculada a uma estrutura de curso."})


def _validate_wizard_componentes(wizard):
    if not wizard.matriz_curricular_id:
        raise ValidationError({"matriz_curricular": "Selecione uma matriz curricular para vincular componentes."})

    quantidade = MatrizComponente.objects.filter(matriz_curricular_id=wizard.matriz_curricular_id).count()
    if quantidade <= 0:
        raise ValidationError({"componentes": "Vincule pelo menos um componente curricular a matriz antes de avancar."})


def _validate_wizard_curso(wizard):
    if not wizard.curso_id:
        raise ValidationError({"curso": "Cadastre o curso antes de avancar."})

    validate_curso_com_matriz(wizard.curso)


def _validate_wizard_coordenadores(wizard):
    if not wizard.curso_id:
        raise ValidationError({"curso": "Cadastre o curso antes de definir coordenadores."})

    possui_coordenador = CursoCoordenador.objects.filter(curso_id=wizard.curso_id).exists()
    if not possui_coordenador:
        raise ValidationError({"coordenadores": "Defina pelo menos um coordenador para o curso."})


def validate_wizard_step_completion(wizard, step=None):
    step = step or wizard.etapa_atual

    if step == ConfiguracaoCursoWizard.ETAPA_ESTRUTURA:
        _validate_wizard_estrutura(wizard)
        return

    if step == ConfiguracaoCursoWizard.ETAPA_MATRIZ:
        _validate_wizard_estrutura(wizard)
        _validate_wizard_matriz(wizard)
        return

    if step == ConfiguracaoCursoWizard.ETAPA_COMPONENTES:
        _validate_wizard_estrutura(wizard)
        _validate_wizard_matriz(wizard)
        _validate_wizard_componentes(wizard)
        return

    if step == ConfiguracaoCursoWizard.ETAPA_REQUISITOS:
        _validate_wizard_estrutura(wizard)
        _validate_wizard_matriz(wizard)
        _validate_wizard_componentes(wizard)
        return

    if step == ConfiguracaoCursoWizard.ETAPA_CURSO:
        _validate_wizard_estrutura(wizard)
        _validate_wizard_matriz(wizard)
        _validate_wizard_componentes(wizard)
        _validate_wizard_curso(wizard)
        return

    if step == ConfiguracaoCursoWizard.ETAPA_COORDENADORES:
        _validate_wizard_estrutura(wizard)
        _validate_wizard_matriz(wizard)
        _validate_wizard_componentes(wizard)
        _validate_wizard_curso(wizard)
        _validate_wizard_coordenadores(wizard)
        return

    if step in {ConfiguracaoCursoWizard.ETAPA_RESUMO, ConfiguracaoCursoWizard.ETAPA_CONCLUIDO}:
        _validate_wizard_estrutura(wizard)
        _validate_wizard_matriz(wizard)
        _validate_wizard_componentes(wizard)
        _validate_wizard_curso(wizard)
        _validate_wizard_coordenadores(wizard)
        return

    raise ValidationError({"etapa_atual": "Etapa do wizard invalida."})
