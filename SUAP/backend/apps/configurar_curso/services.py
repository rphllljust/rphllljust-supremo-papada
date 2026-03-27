from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal

from django.db import transaction
from django.forms.models import model_to_dict
from rest_framework.exceptions import ValidationError

from .models import (
    Auditoria,
    CoRequisito,
    ConfiguracaoCursoWizard,
    Curso,
    MatrizComponente,
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
    validate_wizard_step_completion,
)


def _normalize_json_value(value):
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]

    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]

    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}

    if hasattr(value, "pk"):
        return value.pk

    return str(value)


def serialize_instance(instance, fields=None):
    if not instance:
        return {}

    data = model_to_dict(instance, fields=fields)
    return _normalize_json_value(data)


class AuditoriaService:
    @staticmethod
    def registrar(user, acao, entidade, entidade_id, dados_anteriores=None, dados_novos=None):
        Auditoria.objects.create(
            usuario=user if getattr(user, "is_authenticated", False) else None,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            dados_anteriores=_normalize_json_value(dados_anteriores or {}),
            dados_novos=_normalize_json_value(dados_novos or {}),
        )

    @staticmethod
    def registrar_criacao(user, instance, dados_novos=None):
        payload = dados_novos or serialize_instance(instance)
        AuditoriaService.registrar(
            user=user,
            acao="criado",
            entidade=instance._meta.label,
            entidade_id=instance.pk,
            dados_anteriores={},
            dados_novos=payload,
        )

    @staticmethod
    def registrar_edicao(user, instance, dados_anteriores=None, dados_novos=None):
        AuditoriaService.registrar(
            user=user,
            acao="editado",
            entidade=instance._meta.label,
            entidade_id=instance.pk,
            dados_anteriores=dados_anteriores or {},
            dados_novos=dados_novos or serialize_instance(instance),
        )

    @staticmethod
    def registrar_exclusao_logica(user, instance, dados_anteriores=None):
        AuditoriaService.registrar(
            user=user,
            acao="inativado",
            entidade=instance._meta.label,
            entidade_id=instance.pk,
            dados_anteriores=dados_anteriores or {},
            dados_novos=serialize_instance(instance),
        )


class MatrizComponenteService:
    @staticmethod
    @transaction.atomic
    def criar_vinculo(*, matriz_curricular, componente_curricular, periodo, carga_horaria, obrigatorio=True, ordem=1):
        validate_matriz_componente_duplicado(matriz_curricular.id, componente_curricular.id)

        vinculo = MatrizComponente.objects.create(
            matriz_curricular=matriz_curricular,
            componente_curricular=componente_curricular,
            periodo=periodo,
            carga_horaria=carga_horaria or componente_curricular.carga_horaria,
            obrigatorio=obrigatorio,
            ordem=ordem,
        )
        return vinculo


class RequisitoService:
    @staticmethod
    @transaction.atomic
    def criar_pre_requisito(*, componente, requisito):
        validate_prerequisito_auto_referencia(componente.id, requisito.id)
        validate_componentes_compartilham_matriz(componente.id, requisito.id, field_name="requisito")
        validate_prerequisito_sem_ciclo(componente.id, requisito.id)
        return PreRequisito.objects.create(componente=componente, requisito=requisito)

    @staticmethod
    @transaction.atomic
    def criar_co_requisito(*, componente, requisito):
        validate_corequisito_auto_referencia(componente.id, requisito.id)
        validate_componentes_compartilham_matriz(componente.id, requisito.id, field_name="requisito")
        validate_corequisito_duplicado(componente.id, requisito.id)
        return CoRequisito.objects.create(componente=componente, requisito=requisito)


class WizardService:
    RELATION_FIELDS = ("estrutura_curso", "matriz_curricular", "curso")

    @staticmethod
    @transaction.atomic
    def criar_wizard(*, user, payload=None):
        payload = payload or {}
        wizard = ConfiguracaoCursoWizard.objects.create(
            usuario=user if getattr(user, "is_authenticated", False) else None,
            etapa_atual=payload.get("etapa_atual") or ConfiguracaoCursoWizard.ETAPA_ESTRUTURA,
            status=payload.get("status") or ConfiguracaoCursoWizard.STATUS_RASCUNHO,
            payload_parcial=payload.get("payload_parcial") or {},
        )

        WizardService._aplicar_vinculos(wizard, payload)
        wizard.save(update_fields=["estrutura_curso", "matriz_curricular", "curso", "atualizado_em"])
        AuditoriaService.registrar_criacao(user, wizard)
        return wizard

    @staticmethod
    @transaction.atomic
    def salvar_etapa(*, wizard, user, etapa=None, payload=None):
        etapa = etapa or wizard.etapa_atual

        if etapa not in {item for item in WIZARD_FLOW}:
            raise ValidationError({"etapa": "Etapa invalida para salvar progresso."})

        dados_anteriores = serialize_instance(wizard)
        payload = payload or {}

        WizardService._aplicar_vinculos(wizard, payload)

        payload_wizard = deepcopy(wizard.payload_parcial or {})
        payload_wizard[etapa] = _normalize_json_value(payload)

        wizard.payload_parcial = payload_wizard
        wizard.etapa_atual = etapa

        if wizard.status == ConfiguracaoCursoWizard.STATUS_RASCUNHO:
            wizard.status = ConfiguracaoCursoWizard.STATUS_EM_ANDAMENTO

        wizard.save()

        AuditoriaService.registrar_edicao(
            user,
            wizard,
            dados_anteriores=dados_anteriores,
            dados_novos=serialize_instance(wizard),
        )
        return wizard

    @staticmethod
    @transaction.atomic
    def avancar(*, wizard, user):
        etapa_atual = wizard.etapa_atual

        if etapa_atual not in WIZARD_FLOW:
            raise ValidationError({"etapa_atual": "Etapa atual invalida para avancar."})

        validate_wizard_step_completion(wizard, step=etapa_atual)

        dados_anteriores = serialize_instance(wizard)

        index = WIZARD_FLOW.index(etapa_atual)
        if index < len(WIZARD_FLOW) - 1:
            wizard.etapa_atual = WIZARD_FLOW[index + 1]

        if wizard.status == ConfiguracaoCursoWizard.STATUS_RASCUNHO:
            wizard.status = ConfiguracaoCursoWizard.STATUS_EM_ANDAMENTO

        wizard.save(update_fields=["etapa_atual", "status", "atualizado_em"])
        AuditoriaService.registrar_edicao(user, wizard, dados_anteriores=dados_anteriores, dados_novos=serialize_instance(wizard))
        return wizard

    @staticmethod
    @transaction.atomic
    def voltar(*, wizard, user):
        etapa_atual = wizard.etapa_atual

        if etapa_atual not in WIZARD_FLOW:
            raise ValidationError({"etapa_atual": "Etapa atual invalida para voltar."})

        dados_anteriores = serialize_instance(wizard)
        index = WIZARD_FLOW.index(etapa_atual)
        if index > 0:
            wizard.etapa_atual = WIZARD_FLOW[index - 1]
            wizard.save(update_fields=["etapa_atual", "atualizado_em"])
            AuditoriaService.registrar_edicao(user, wizard, dados_anteriores=dados_anteriores, dados_novos=serialize_instance(wizard))

        return wizard

    @staticmethod
    def resumo(*, wizard):
        return WizardService._build_summary(wizard)

    @staticmethod
    @transaction.atomic
    def concluir(*, wizard, user):
        validate_wizard_step_completion(wizard, step=ConfiguracaoCursoWizard.ETAPA_RESUMO)

        dados_anteriores = serialize_instance(wizard)
        wizard.etapa_atual = ConfiguracaoCursoWizard.ETAPA_CONCLUIDO
        wizard.status = ConfiguracaoCursoWizard.STATUS_CONCLUIDO
        wizard.save(update_fields=["etapa_atual", "status", "atualizado_em"])

        if wizard.curso_id and wizard.curso.situacao == Curso.SITUACAO_EM_CONFIGURACAO:
            wizard.curso.situacao = Curso.SITUACAO_ATIVO
            wizard.curso.save(update_fields=["situacao", "atualizado_em"])

        AuditoriaService.registrar_edicao(
            user,
            wizard,
            dados_anteriores=dados_anteriores,
            dados_novos=serialize_instance(wizard),
        )

        return wizard

    @staticmethod
    def _aplicar_vinculos(wizard, payload):
        for field in WizardService.RELATION_FIELDS:
            if field in payload:
                setattr(wizard, f"{field}_id", payload.get(field) or None)

        if wizard.matriz_curricular_id and not wizard.estrutura_curso_id:
            wizard.estrutura_curso = wizard.matriz_curricular.estrutura_curso

        if wizard.curso_id:
            if wizard.curso.matriz_curricular_id and not wizard.matriz_curricular_id:
                wizard.matriz_curricular = wizard.curso.matriz_curricular

            if wizard.curso.estrutura_curso_id and not wizard.estrutura_curso_id:
                wizard.estrutura_curso = wizard.curso.estrutura_curso

            if wizard.matriz_curricular_id and wizard.curso.matriz_curricular_id != wizard.matriz_curricular_id:
                wizard.curso.matriz_curricular_id = wizard.matriz_curricular_id
                wizard.curso.save(update_fields=["matriz_curricular", "atualizado_em"])

    @staticmethod
    def _build_summary(wizard):
        curso = wizard.curso
        matriz = wizard.matriz_curricular
        estrutura = wizard.estrutura_curso

        matriz_componentes_qs = MatrizComponente.objects.filter(matriz_curricular=matriz).select_related("componente_curricular") if matriz else MatrizComponente.objects.none()

        pre_requisitos_qs = PreRequisito.objects.filter(
            componente_id__in=matriz_componentes_qs.values_list("componente_curricular_id", flat=True)
        ).select_related("componente", "requisito") if matriz else PreRequisito.objects.none()

        co_requisitos_qs = CoRequisito.objects.filter(
            componente_id__in=matriz_componentes_qs.values_list("componente_curricular_id", flat=True)
        ).select_related("componente", "requisito") if matriz else CoRequisito.objects.none()

        coordenadores_qs = curso.vinculos_coordenadores.select_related("coordenador") if curso else []

        return {
            "wizard": {
                "id": wizard.id,
                "status": wizard.status,
                "etapa_atual": wizard.etapa_atual,
                "criado_em": wizard.criado_em,
                "atualizado_em": wizard.atualizado_em,
            },
            "estrutura_curso": serialize_instance(estrutura),
            "matriz_curricular": serialize_instance(matriz),
            "componentes_vinculados": [
                {
                    "id": item.id,
                    "matriz_curricular": item.matriz_curricular_id,
                    "componente_curricular": item.componente_curricular_id,
                    "componente_codigo": item.componente_curricular.codigo,
                    "componente_nome": item.componente_curricular.nome,
                    "periodo": item.periodo,
                    "carga_horaria": item.carga_horaria,
                    "obrigatorio": item.obrigatorio,
                    "ordem": item.ordem,
                }
                for item in matriz_componentes_qs
            ],
            "pre_requisitos": [
                {
                    "id": item.id,
                    "componente": item.componente_id,
                    "componente_nome": item.componente.nome,
                    "requisito": item.requisito_id,
                    "requisito_nome": item.requisito.nome,
                }
                for item in pre_requisitos_qs
            ],
            "co_requisitos": [
                {
                    "id": item.id,
                    "componente": item.componente_id,
                    "componente_nome": item.componente.nome,
                    "requisito": item.requisito_id,
                    "requisito_nome": item.requisito.nome,
                }
                for item in co_requisitos_qs
            ],
            "curso": serialize_instance(curso),
            "coordenadores": [
                {
                    "id": item.id,
                    "curso": item.curso_id,
                    "coordenador": item.coordenador_id,
                    "coordenador_nome": item.coordenador.nome,
                    "principal": item.principal,
                    "inicio_vigencia": item.inicio_vigencia,
                    "fim_vigencia": item.fim_vigencia,
                }
                for item in coordenadores_qs
            ],
            "payload_parcial": _normalize_json_value(wizard.payload_parcial or {}),
        }
