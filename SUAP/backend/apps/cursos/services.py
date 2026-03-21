from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from apps.integracao_moodle.models import MoodleCategory, MoodleCourse
from apps.integracao_moodle.services import create_moodle_categories, create_moodle_courses, duplicate_moodle_course, update_moodle_courses
from apps.unidades.models import Unidade

from .models import ComponenteCurricular, Curso, MatrizCurricular, MatrizCurricularLog


MATRIX_TEMPLATE_CATEGORY_NAME = 'CURSOS MODELO - MATRIZES'


@dataclass(slots=True)
class TechnicalMatrixMigrationSummary:
    technical_courses_found: int = 0
    matrizes_created: int = 0
    matrizes_reused: int = 0
    componentes_linked: int = 0
    cursos_updated: int = 0


def build_default_matriz_nome(curso: Curso, ano_referencia: int | None = None) -> str:
    ano = ano_referencia or timezone.now().year
    return f'Matriz {curso.nome} {ano}'


def log_matriz_event(
    *,
    matriz: MatrizCurricular | None,
    evento: str,
    status: str = 'info',
    mensagem: str = '',
    curso: Curso | None = None,
    payload: dict | None = None,
):
    return MatrizCurricularLog.objects.create(
        matriz_curricular=matriz,
        curso=curso or getattr(matriz, 'curso_base', None),
        evento=evento,
        status=status,
        mensagem=mensagem,
        payload=payload or {},
    )


@transaction.atomic
def create_initial_matrix_for_course(
    curso: Curso,
    *,
    ano_referencia: int | None = None,
    versao: str = '1.0',
    status: str = 'VIGENTE',
    ativa: bool = True,
) -> tuple[MatrizCurricular, bool, int]:
    if curso.tipo_curso != 'tecnico':
        raise ValueError('A criação automática de matriz inicial é suportada apenas para cursos técnicos.')

    ano = ano_referencia or timezone.now().year
    matriz, created = MatrizCurricular.objects.get_or_create(
        curso_base=curso,
        ano_referencia=ano,
        versao=versao,
        defaults={
            'nome': build_default_matriz_nome(curso, ano),
            'status': status,
            'ativa': ativa,
            'descricao': f'Matriz inicial gerada automaticamente para o curso técnico {curso.nome}.',
        },
    )

    if created:
        log_matriz_event(
            matriz=matriz,
            curso=curso,
            evento='criacao_matriz',
            status='success',
            mensagem='Matriz curricular inicial criada automaticamente.',
            payload={'curso_id': curso.id, 'ano_referencia': ano, 'versao': versao},
        )

    componentes_ligados = ComponenteCurricular.objects.filter(curso=curso, matriz_curricular__isnull=True).update(
        matriz_curricular=matriz
    )

    if componentes_ligados:
        log_matriz_event(
            matriz=matriz,
            curso=curso,
            evento='migracao_componentes',
            status='success',
            mensagem='Componentes curriculares legados vinculados à matriz curricular inicial.',
            payload={'componentes_ligados': componentes_ligados},
        )

    if curso.matriz_curricular_id != matriz.id:
        curso.matriz_curricular = matriz
        curso.save(update_fields=['matriz_curricular'])

    return matriz, created, componentes_ligados


def migrate_technical_courses_to_initial_matrizes(
    *,
    ano_referencia: int | None = None,
    course_ids: list[int] | None = None,
) -> TechnicalMatrixMigrationSummary:
    queryset = Curso.objects.filter(tipo_curso='tecnico').order_by('id')
    if course_ids:
        queryset = queryset.filter(id__in=course_ids)

    summary = TechnicalMatrixMigrationSummary(technical_courses_found=queryset.count())

    for curso in queryset:
        _, created, componentes_ligados = create_initial_matrix_for_course(curso, ano_referencia=ano_referencia)
        if created:
            summary.matrizes_created += 1
        else:
            summary.matrizes_reused += 1
        summary.componentes_linked += componentes_ligados
        summary.cursos_updated += 1

    return summary


def rollback_initial_matrices(*, ano_referencia: int | None = None, course_ids: list[int] | None = None) -> dict:
    queryset = MatrizCurricular.objects.filter(curso_base__tipo_curso='tecnico')
    if ano_referencia:
        queryset = queryset.filter(ano_referencia=ano_referencia)
    if course_ids:
        queryset = queryset.filter(curso_base_id__in=course_ids)

    matrizes = list(queryset.select_related('curso_base'))
    rollback_ids = [matriz.id for matriz in matrizes]
    if not rollback_ids:
        return {'matrizes_removidas': 0, 'componentes_desvinculados': 0, 'cursos_limpos': 0}

    componentes_desvinculados = ComponenteCurricular.objects.filter(matriz_curricular_id__in=rollback_ids).update(
        matriz_curricular=None,
        modulo_numero=None,
        modulo_nome='',
        ordem_no_modulo=None,
    )
    cursos_limpos = Curso.objects.filter(matriz_curricular_id__in=rollback_ids).update(matriz_curricular=None)
    matrizes_removidas = queryset.delete()[0]
    return {
        'matrizes_removidas': matrizes_removidas,
        'componentes_desvinculados': componentes_desvinculados,
        'cursos_limpos': cursos_limpos,
    }


def ensure_moodle_template_category() -> int:
    category = MoodleCategory.objects.filter(nome__iexact=MATRIX_TEMPLATE_CATEGORY_NAME).order_by('moodle_category_id').first()
    if category:
        return category.moodle_category_id

    response = create_moodle_categories(
        {
            'categories': [
                {
                    'name': MATRIX_TEMPLATE_CATEGORY_NAME,
                    'description': 'Cursos modelo de matrizes curriculares técnicas do SUAP.',
                    'parent': 0,
                    'descriptionformat': 1,
                    'idnumber': 'suap-matrizes-modelo',
                }
            ]
        }
    )
    payload = response[0] if isinstance(response, list) and response else response
    return int(payload['id'])


def sync_matriz_curricular_template_to_moodle(matriz: MatrizCurricular, *, unidade_codigo: str = 'sede') -> dict:
    category_id = matriz.moodle_template_category_id or ensure_moodle_template_category()
    shortname = matriz.moodle_template_shortname or _build_moodle_template_shortname(matriz)
    params = {
        'courses': [
            {
                'fullname': matriz.nome,
                'shortname': shortname,
                'categoryid': category_id,
                'idnumber': f'matriz-{matriz.id}',
                'summary': matriz.descricao or matriz.nome,
                'visible': 0,
                'format': 'topics',
                'courseformatoptions': [
                    {'name': 'numsections', 'value': max(matriz.total_modulos, 1)},
                ],
            }
        ]
    }

    try:
        if matriz.moodle_template_course_id:
            params['courses'][0]['id'] = matriz.moodle_template_course_id
            moodle_result = update_moodle_courses(
                params,
                unidade_codigo=unidade_codigo,
                persistir_espelho_local=True,
                integrar_catalogo_interno=False,
            )
            evento = 'atualizacao_curso_modelo'
            mensagem = 'Curso modelo Moodle atualizado a partir da matriz curricular.'
        else:
            moodle_result = create_moodle_courses(
                params,
                unidade_codigo=unidade_codigo,
                persistir_espelho_local=True,
                integrar_catalogo_interno=False,
            )
            evento = 'criacao_curso_modelo'
            mensagem = 'Curso modelo Moodle criado a partir da matriz curricular.'

        course_id = _resolve_course_id_from_result(moodle_result)
        matriz.moodle_template_course_id = course_id
        matriz.moodle_template_shortname = shortname
        matriz.moodle_template_category_id = category_id
        matriz.last_sync_at = timezone.now()
        matriz.last_sync_status = 'success'
        matriz.last_sync_message = mensagem
        matriz.save(update_fields=[
            'moodle_template_course_id',
            'moodle_template_shortname',
            'moodle_template_category_id',
            'last_sync_at',
            'last_sync_status',
            'last_sync_message',
            'updated_at',
        ])

        log_matriz_event(
            matriz=matriz,
            evento=evento,
            status='success',
            mensagem=mensagem,
            payload={'moodle_result': moodle_result},
        )

        if course_id:
            MoodleCourse.objects.filter(moodle_course_id=course_id).update(curso=None)

        return {'matriz': matriz, 'moodle': moodle_result}
    except Exception as exc:
        matriz.last_sync_at = timezone.now()
        matriz.last_sync_status = 'error'
        matriz.last_sync_message = str(exc)
        matriz.save(update_fields=['last_sync_at', 'last_sync_status', 'last_sync_message', 'updated_at'])
        log_matriz_event(
            matriz=matriz,
            evento='falha_sincronizacao',
            status='error',
            mensagem='Falha ao sincronizar curso modelo da matriz com o Moodle.',
            payload={'error': str(exc)},
        )
        raise


@transaction.atomic
def create_course_offer_from_matriz(
    matriz: MatrizCurricular,
    *,
    nome: str | None = None,
    sigla: str | None = None,
    unidade_id: int | None = None,
    unidade_codigo: str = 'sede',
    copiar_para_moodle: bool = True,
) -> dict:
    unidade = Unidade.objects.get(pk=unidade_id or matriz.curso_base.unidade_id)
    oferta = Curso.objects.create(
        tipo_curso='tecnico',
        unidade=unidade,
        area_curso=matriz.curso_base.area_curso,
        nome=(nome or f'{matriz.curso_base.nome} - Oferta {matriz.ano_referencia}').strip(),
        sigla=(sigla or matriz.curso_base.sigla or f'OF-{matriz.id}')[:16],
        eixo_tecnologico=matriz.curso_base.eixo_tecnologico,
        carga_horaria=matriz.curso_base.carga_horaria,
        matriz_curricular=matriz,
    )

    log_matriz_event(
        matriz=matriz,
        curso=oferta,
        evento='criacao_oferta_real',
        status='success',
        mensagem='Oferta real criada a partir da matriz curricular.',
        payload={'curso_id': oferta.id},
    )

    moodle_result = None
    if copiar_para_moodle:
        moodle_result = _replicate_matrix_to_offer_in_moodle(matriz, oferta, unidade_codigo=unidade_codigo)

    return {'curso': oferta, 'moodle': moodle_result}


def _replicate_matrix_to_offer_in_moodle(matriz: MatrizCurricular, oferta: Curso, *, unidade_codigo: str) -> dict | None:
    category_id = _resolve_offer_category_id(matriz)
    if category_id is None:
        return None

    if matriz.moodle_template_course_id:
        moodle_result = duplicate_moodle_course(
            {
                'courseid': matriz.moodle_template_course_id,
                'fullname': oferta.nome,
                'shortname': oferta.sigla,
                'categoryid': category_id,
                'visible': 1,
            },
            persistir_espelho_local=True,
        )
        log_matriz_event(
            matriz=matriz,
            curso=oferta,
            evento='importacao_conteudo',
            status='success',
            mensagem='Estrutura do curso modelo duplicada para a oferta real no Moodle.',
            payload={'moodle_result': moodle_result},
        )
    else:
        moodle_result = create_moodle_courses(
            {
                'courses': [
                    {
                        'fullname': oferta.nome,
                        'shortname': oferta.sigla,
                        'categoryid': category_id,
                        'idnumber': f'oferta-{oferta.id}',
                        'summary': oferta.nome,
                    }
                ]
            },
            unidade_codigo=unidade_codigo,
            persistir_espelho_local=True,
            integrar_catalogo_interno=False,
        )

    course_id = _resolve_course_id_from_result(moodle_result)
    if course_id:
        oferta.moodle_course_id = course_id
        oferta.moodle_shortname = oferta.sigla
        oferta.save(update_fields=['moodle_course_id', 'moodle_shortname'])
        MoodleCourse.objects.filter(moodle_course_id=course_id).update(curso=oferta)

    return moodle_result


def _resolve_offer_category_id(matriz: MatrizCurricular) -> int | None:
    if matriz.curso_base.moodle_course_id:
        local_course = MoodleCourse.objects.filter(moodle_course_id=matriz.curso_base.moodle_course_id).select_related('categoria').first()
        if local_course and local_course.categoria_id:
            return local_course.categoria.moodle_category_id

    local_course = MoodleCourse.objects.filter(curso=matriz.curso_base).select_related('categoria').first()
    if local_course and local_course.categoria_id:
        return local_course.categoria.moodle_category_id

    return None


def _build_moodle_template_shortname(matriz: MatrizCurricular) -> str:
    return f'MAT-{matriz.curso_base.sigla or matriz.curso_base.id}-{matriz.ano_referencia}-{matriz.versao}'.replace(' ', '-')[:100]


def _resolve_course_id_from_result(result: dict | list | None) -> int | None:
    if result is None:
        return None

    if isinstance(result, dict):
        course_ids = result.get('course_ids') or []
        if course_ids:
            return int(course_ids[0])

        response_payload = result.get('response_payload')
        return _resolve_course_id_from_result(response_payload)

    if isinstance(result, list) and result:
        item = result[0]
        if isinstance(item, dict) and item.get('id') is not None:
            return int(item['id'])

    return None