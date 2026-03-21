from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from apps.integracao_moodle.models import MoodleCategory, MoodleCourse
from apps.integracao_moodle.services import MOODLE_COURSE_ROOT_CATEGORY_IDS, create_moodle_categories, create_moodle_courses, duplicate_moodle_course, get_moodle_categories, get_moodle_course_contents, import_moodle_course, update_moodle_courses, update_moodle_inplace_editable
from apps.unidades.models import Unidade

from .models import CalendarioLetivo, ComponenteCurricular, Curso, MatrizCurricular, MatrizCurricularLog, OfertaCurso, OfertaCursoLog


MATRIX_TEMPLATE_CATEGORY_NAME = 'CURSOS MODELO - MATRIZES'
OFFER_BRANCH_CATEGORY_NAME = 'OFERTAS SUAP'


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


def log_oferta_event(
    *,
    oferta: OfertaCurso,
    evento: str,
    status: str = 'info',
    mensagem: str = '',
    payload: dict | None = None,
):
    return OfertaCursoLog.objects.create(
        oferta_curso=oferta,
        evento=evento,
        status=status,
        mensagem=mensagem,
        payload=payload or {},
    )


def build_default_oferta_nome(oferta: OfertaCurso) -> str:
    turma = f' - Turma {oferta.codigo_turma}' if (oferta.codigo_turma or '').strip() else ''
    return f'{oferta.curso_base.nome} - {oferta.ano_oferta}.{oferta.periodo_letivo}{turma}'


def build_default_oferta_shortname(oferta: OfertaCurso) -> str:
    curso_sigla = (oferta.curso_base.sigla or f'CUR{oferta.curso_base_id}').replace(' ', '-')[:20]
    polo_sigla = (oferta.polo.codigo or 'polo').replace(' ', '-')[:12]
    turma_sigla = (oferta.codigo_turma or 'T1').replace(' ', '-')[:12]
    return f'OF-{curso_sigla}-{oferta.ano_oferta}{oferta.periodo_letivo}-{polo_sigla}-{turma_sigla}'[:100]


def _calculate_next_matrix_version(matriz: MatrizCurricular) -> str:
    existing_versions = set(
        MatrizCurricular.objects.filter(
            curso_base=matriz.curso_base,
            ano_referencia=matriz.ano_referencia,
        ).values_list('versao', flat=True)
    )
    current_version = (matriz.versao or '1.0').strip()

    try:
        next_version = str((Decimal(current_version) + Decimal('0.1')).normalize())
        if '.' not in next_version:
            next_version = f'{next_version}.0'
    except (InvalidOperation, ValueError):
        next_version = f'{current_version}.1'

    candidate = next_version
    counter = 1
    while candidate in existing_versions:
        candidate = f'{next_version}.{counter}'
        counter += 1

    return candidate


def _sync_course_reference_matrix(curso: Curso) -> None:
    vigente = (
        MatrizCurricular.objects.filter(curso_base=curso, status='VIGENTE')
        .order_by('-ano_referencia', '-updated_at', '-id')
        .first()
    )
    desired_id = vigente.id if vigente else None
    if curso.matriz_curricular_id != desired_id:
        curso.matriz_curricular_id = desired_id
        curso.save(update_fields=['matriz_curricular'])


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


@transaction.atomic
def clone_matriz_curricular(
    matriz: MatrizCurricular,
    *,
    versao: str | None = None,
    nome: str | None = None,
    ano_referencia: int | None = None,
    descricao: str | None = None,
) -> MatrizCurricular:
    clone = MatrizCurricular.objects.create(
        curso_base=matriz.curso_base,
        nome=(nome or matriz.nome).strip(),
        ano_referencia=ano_referencia or matriz.ano_referencia,
        versao=(versao or _calculate_next_matrix_version(matriz)).strip(),
        status='RASCUNHO',
        ativa=True,
        descricao=(descricao if descricao is not None else matriz.descricao),
        moodle_template_course_id=None,
        moodle_template_shortname='',
        moodle_template_category_id=matriz.moodle_template_category_id,
        last_sync_at=None,
        last_sync_status='',
        last_sync_message='',
    )

    componentes = []
    for componente in matriz.componentes.order_by('modulo_numero', 'ordem_no_modulo', 'ordem', 'nome'):
        componentes.append(
            ComponenteCurricular(
                curso=clone.curso_base,
                matriz_curricular=clone,
                nome=componente.nome,
                abreviatura=componente.abreviatura,
                sigla=componente.sigla,
                descricao_diploma_historico=componente.descricao_diploma_historico,
                diretoria=componente.diretoria,
                ativo=componente.ativo,
                tipo_componente=componente.tipo_componente,
                nivel_ensino=componente.nivel_ensino,
                tipo_componente_catalogo=componente.tipo_componente_catalogo,
                nivel_ensino_catalogo=componente.nivel_ensino_catalogo,
                grupo_atuacao=componente.grupo_atuacao,
                carga_horaria=componente.carga_horaria,
                hora_aula=componente.hora_aula,
                qtd_creditos=componente.qtd_creditos,
                sigla_qacademico=componente.sigla_qacademico,
                observacao=componente.observacao,
                ordem=componente.ordem,
                modulo_numero=componente.modulo_numero,
                modulo_nome=componente.modulo_nome,
                ordem_no_modulo=componente.ordem_no_modulo,
            )
        )

    if componentes:
        ComponenteCurricular.objects.bulk_create(componentes)

    log_matriz_event(
        matriz=clone,
        curso=clone.curso_base,
        evento='clonagem_matriz',
        status='success',
        mensagem='Matriz curricular clonada com sucesso.',
        payload={'matriz_origem_id': matriz.id, 'componentes_copiados': len(componentes)},
    )
    return clone


@transaction.atomic
def publish_matriz_curricular(matriz: MatrizCurricular) -> MatrizCurricular:
    if matriz.status == 'ENCERRADA':
        raise ValueError('Não é possível publicar uma matriz encerrada.')

    vigente_existente = MatrizCurricular.objects.filter(
        curso_base=matriz.curso_base,
        ano_referencia=matriz.ano_referencia,
        status='VIGENTE',
    ).exclude(pk=matriz.pk)

    if vigente_existente.exists():
        raise ValueError('Já existe uma matriz vigente para este curso técnico e ano de referência. Use a ação de definir vigente para substituir a atual.')

    matriz.status = 'VIGENTE'
    matriz.ativa = True
    matriz.save(update_fields=['status', 'ativa', 'updated_at'])
    _sync_course_reference_matrix(matriz.curso_base)
    log_matriz_event(
        matriz=matriz,
        curso=matriz.curso_base,
        evento='publicacao_matriz',
        status='success',
        mensagem='Matriz curricular publicada como vigente.',
        payload={'matriz_id': matriz.id},
    )
    return matriz


@transaction.atomic
def close_matriz_curricular(matriz: MatrizCurricular) -> MatrizCurricular:
    if matriz.status == 'ENCERRADA':
        return matriz

    matriz.status = 'ENCERRADA'
    matriz.ativa = False
    matriz.save(update_fields=['status', 'ativa', 'updated_at'])
    _sync_course_reference_matrix(matriz.curso_base)
    log_matriz_event(
        matriz=matriz,
        curso=matriz.curso_base,
        evento='encerramento_matriz',
        status='success',
        mensagem='Matriz curricular encerrada.',
        payload={'matriz_id': matriz.id},
    )
    return matriz


@transaction.atomic
def set_matriz_as_current(matriz: MatrizCurricular) -> MatrizCurricular:
    if matriz.status == 'ENCERRADA':
        raise ValueError('Não é possível definir uma matriz encerrada como vigente.')

    anteriores = list(
        MatrizCurricular.objects.filter(
            curso_base=matriz.curso_base,
            ano_referencia=matriz.ano_referencia,
            status='VIGENTE',
        ).exclude(pk=matriz.pk)
    )

    if anteriores:
        MatrizCurricular.objects.filter(pk__in=[item.pk for item in anteriores]).update(status='ENCERRADA', ativa=False)
        for anterior in anteriores:
            log_matriz_event(
                matriz=anterior,
                curso=anterior.curso_base,
                evento='encerramento_matriz',
                status='success',
                mensagem='Matriz encerrada automaticamente ao definir outra versão como vigente.',
                payload={'substituida_por_matriz_id': matriz.id},
            )

    matriz.status = 'VIGENTE'
    matriz.ativa = True
    matriz.save(update_fields=['status', 'ativa', 'updated_at'])
    _sync_course_reference_matrix(matriz.curso_base)
    log_matriz_event(
        matriz=matriz,
        curso=matriz.curso_base,
        evento='definicao_vigencia',
        status='success',
        mensagem='Matriz curricular definida como vigente.',
        payload={'matrizes_encerradas': [item.id for item in anteriores]},
    )
    return matriz


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
    expected_sections = max(matriz.total_modulos, 1)
    section_name_result = None
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
                    {'name': 'numsections', 'value': expected_sections},
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
        if course_id:
            section_name_result = _sync_course_section_names(course_id=course_id, section_names=_build_section_names_from_matriz(matriz))
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
            payload={
                'moodle_result': moodle_result,
                'numsections': expected_sections,
                'section_name_result': section_name_result,
            },
        )

        if course_id:
            MoodleCourse.objects.filter(moodle_course_id=course_id).update(curso=None)

        return {
            'matriz': matriz,
            'moodle': moodle_result,
            'section_name_result': section_name_result,
        }
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
def create_oferta_curso(
    *,
    curso_base: Curso,
    calendario_letivo: CalendarioLetivo,
    polo: Unidade,
    matriz_curricular: MatrizCurricular | None = None,
    nome: str | None = None,
    codigo_turma: str = '',
    ano_oferta: int | None = None,
    periodo_letivo: str = '1',
    turno: str = 'NOITE',
    vagas_totais: int = 0,
    vagas_ocupadas: int = 0,
    status: str = 'PLANEJADA',
    observacao: str = '',
) -> OfertaCurso:
    matriz = matriz_curricular or curso_base.matriz_curricular
    if matriz is None:
        raise ValueError('O curso base informado não possui matriz curricular vigente ou selecionada para gerar a oferta.')

    oferta = OfertaCurso(
        curso_base=curso_base,
        matriz_curricular=matriz,
        polo=polo,
        calendario_letivo=calendario_letivo,
        nome=(nome or '').strip(),
        codigo_turma=(codigo_turma or '').strip(),
        ano_oferta=ano_oferta or _resolve_offer_year(calendario_letivo),
        periodo_letivo=(periodo_letivo or '1').strip(),
        turno=(turno or 'NOITE').strip().upper(),
        vagas_totais=max(int(vagas_totais or 0), 0),
        vagas_ocupadas=max(int(vagas_ocupadas or 0), 0),
        status=(status or 'PLANEJADA').strip().upper(),
        observacao=(observacao or '').strip(),
    )
    if not oferta.nome:
        oferta.nome = build_default_oferta_nome(oferta)

    oferta.save()
    log_oferta_event(
        oferta=oferta,
        evento='criacao_oferta',
        status='success',
        mensagem='Oferta de curso criada com sucesso.',
        payload={
            'curso_base_id': curso_base.id,
            'matriz_curricular_id': matriz.id,
            'calendario_letivo_id': calendario_letivo.id,
            'polo_id': polo.id,
        },
    )
    return oferta


def sync_oferta_curso_to_moodle(oferta: OfertaCurso, *, unidade_codigo: str | None = None) -> dict:
    resolved_unidade_codigo = (unidade_codigo or oferta.polo.codigo or oferta.curso_base.unidade.codigo or 'sede').strip().lower()
    category_id = _ensure_offer_category_id(oferta)
    shortname = oferta.moodle_shortname or build_default_oferta_shortname(oferta)
    moodle_result = None
    expected_sections = max(oferta.matriz_curricular.total_modulos, 1)
    module_names = oferta.modulo_nomes
    sync_mode = ''
    template_applied = False
    template_course_id = oferta.matriz_curricular.moodle_template_course_id
    template_shortname = oferta.matriz_curricular.moodle_template_shortname
    fallback_reason = ''
    import_result = None
    section_name_result = None

    try:
        if oferta.moodle_course_id:
            moodle_result = _update_existing_oferta_course(
                oferta=oferta,
                shortname=shortname,
                category_id=category_id,
                expected_sections=expected_sections,
                unidade_codigo=resolved_unidade_codigo,
            )
            sync_mode = 'update_existing'
            if template_course_id:
                safe_to_import, safe_reason = _is_safe_to_import_template(oferta.moodle_course_id)
                if safe_to_import:
                    import_result = import_moodle_course(
                        {
                            'importfrom': template_course_id,
                            'importto': oferta.moodle_course_id,
                            'deletecontent': 1,
                        }
                    )
                    sync_mode = 'import_template'
                    template_applied = True
                    fallback_reason = ''
                    log_oferta_event(
                        oferta=oferta,
                        evento='sincronizacao_template',
                        status='success',
                        mensagem='Template da matriz importado para o curso da oferta já existente no Moodle.',
                        payload={'template_course_id': template_course_id, 'safe_reason': safe_reason, 'import_result': import_result},
                    )
                else:
                    fallback_reason = safe_reason
            else:
                fallback_reason = 'Matriz curricular sem curso modelo Moodle sincronizado.'
        elif template_course_id:
            moodle_result = duplicate_moodle_course(
                {
                    'courseid': template_course_id,
                    'fullname': oferta.nome,
                    'shortname': shortname,
                    'categoryid': category_id,
                    'visible': 1,
                },
                persistir_espelho_local=True,
            )
            sync_mode = 'duplicate_template'
            template_applied = True
            log_oferta_event(
                oferta=oferta,
                evento='importacao_conteudo',
                status='success',
                mensagem='Oferta criada no Moodle a partir do curso modelo da matriz curricular.',
                payload={'template_course_id': template_course_id},
            )
        else:
            moodle_result = create_moodle_courses(
                {
                    'courses': [
                        {
                            'fullname': oferta.nome,
                            'shortname': shortname,
                            'categoryid': category_id,
                            'idnumber': f'oferta-curso-{oferta.id}',
                            'summary': oferta.observacao or oferta.nome,
                            'visible': 1,
                            'format': 'topics',
                            'courseformatoptions': [
                                {'name': 'numsections', 'value': expected_sections},
                            ],
                        }
                    ]
                },
                unidade_codigo=resolved_unidade_codigo,
                persistir_espelho_local=True,
                integrar_catalogo_interno=False,
            )
            sync_mode = 'create_fallback'
            fallback_reason = 'Matriz curricular sem curso modelo Moodle sincronizado.'

        course_id = _resolve_course_id_from_result(moodle_result)
        if course_id:
            section_name_result = _sync_course_section_names(course_id=course_id, section_names=module_names)
        oferta.moodle_course_id = course_id
        oferta.moodle_shortname = shortname
        oferta.moodle_category_id = category_id
        oferta.moodle_sync_mode = sync_mode
        oferta.moodle_template_applied = template_applied
        oferta.moodle_template_source_course_id = template_course_id if template_applied else None
        oferta.moodle_template_source_shortname = template_shortname if template_applied else ''
        oferta.moodle_sync_fallback_reason = fallback_reason
        oferta.last_sync_at = timezone.now()
        oferta.last_sync_status = 'success'
        oferta.last_sync_message = _build_oferta_sync_message(sync_mode=sync_mode, fallback_reason=fallback_reason)
        oferta.save(update_fields=[
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
            'updated_at',
        ])
        if course_id:
            MoodleCourse.objects.filter(moodle_course_id=course_id).update(curso=None)

        log_oferta_event(
            oferta=oferta,
            evento='sincronizacao_moodle',
            status='success',
            mensagem='Oferta sincronizada com o Moodle com sucesso.',
            payload={
                'moodle_result': moodle_result,
                'import_result': import_result,
                'numsections': expected_sections,
                'module_names': module_names,
                'section_name_result': section_name_result,
                'moodle_sync_mode': sync_mode,
                'template_applied': template_applied,
                'template_course_id': template_course_id,
                'fallback_reason': fallback_reason,
            },
        )
        return {
            'oferta': oferta,
            'moodle': moodle_result,
            'import_result': import_result,
            'section_name_result': section_name_result,
        }
    except Exception as exc:
        oferta.last_sync_at = timezone.now()
        oferta.last_sync_status = 'error'
        oferta.last_sync_message = str(exc)
        oferta.save(update_fields=['last_sync_at', 'last_sync_status', 'last_sync_message', 'updated_at'])
        log_oferta_event(
            oferta=oferta,
            evento='falha_sincronizacao',
            status='error',
            mensagem='Falha ao sincronizar a oferta com o Moodle.',
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


def _update_existing_oferta_course(
    *,
    oferta: OfertaCurso,
    shortname: str,
    category_id: int,
    expected_sections: int,
    unidade_codigo: str,
) -> dict:
    return update_moodle_courses(
        {
            'courses': [
                {
                    'id': oferta.moodle_course_id,
                    'fullname': oferta.nome,
                    'shortname': shortname,
                    'categoryid': category_id,
                    'idnumber': f'oferta-curso-{oferta.id}',
                    'summary': oferta.observacao or oferta.nome,
                    'visible': 1,
                    'format': 'topics',
                    'courseformatoptions': [
                        {'name': 'numsections', 'value': expected_sections},
                    ],
                }
            ]
        },
        unidade_codigo=unidade_codigo,
        persistir_espelho_local=True,
        integrar_catalogo_interno=False,
    )


def _build_oferta_sync_message(*, sync_mode: str, fallback_reason: str = '') -> str:
    if sync_mode == 'duplicate_template':
        return 'Oferta sincronizada com o Moodle por duplicação do curso modelo da matriz.'
    if sync_mode == 'import_template':
        return 'Oferta sincronizada com o Moodle com importação do template da matriz para o curso existente.'
    if sync_mode == 'update_existing':
        return 'Oferta sincronizada com o Moodle pela atualização do curso existente.'
    if sync_mode == 'create_fallback':
        if fallback_reason:
            return f'Oferta sincronizada com o Moodle sem template da matriz. {fallback_reason}'
        return 'Oferta sincronizada com o Moodle sem template da matriz.'
    return 'Oferta sincronizada com o Moodle.'


def _build_section_names_from_matriz(matriz: MatrizCurricular) -> list[str]:
    return [modulo['modulo_nome'] for modulo in matriz.componentes_por_modulo()]


def _is_safe_to_import_template(moodle_course_id: int | None) -> tuple[bool, str]:
    if not moodle_course_id:
        return False, 'Curso da oferta ainda não existe no Moodle.'

    try:
        contents = get_moodle_course_contents(
            {
                'courseid': moodle_course_id,
                'options': [
                    {'name': 'excludecontents', 'value': 1},
                ],
            }
        )
    except Exception as exc:
        return False, f'Não foi possível inspecionar o curso existente no Moodle antes da importação: {exc}'

    for section in contents or []:
        if int(section.get('section') or 0) == 0:
            continue
        if section.get('modules'):
            return False, 'O curso existente no Moodle já possui atividades ou recursos e não será sobrescrito automaticamente.'

    return True, 'Curso existente sem atividades; importação do template permitida.'


def _sync_course_section_names(*, course_id: int | None, section_names: list[str]) -> dict:
    if not course_id or not section_names:
        return {'attempted': 0, 'updated': 0, 'skipped': 0, 'errors': []}

    try:
        contents = get_moodle_course_contents(
            {
                'courseid': course_id,
                'options': [
                    {'name': 'excludecontents', 'value': 1},
                ],
            }
        )
    except Exception as exc:
        return {'attempted': 0, 'updated': 0, 'skipped': 0, 'errors': [str(exc)]}

    sections_by_number = {
        int(section.get('section') or 0): section
        for section in contents or []
        if int(section.get('section') or 0) > 0
    }
    result = {'attempted': 0, 'updated': 0, 'skipped': 0, 'errors': []}

    for index, section_name in enumerate(section_names, start=1):
        normalized_name = (section_name or '').strip()
        if not normalized_name:
            result['skipped'] += 1
            continue

        section = sections_by_number.get(index)
        if not section:
            result['skipped'] += 1
            continue

        result['attempted'] += 1
        current_name = (section.get('name') or '').strip()
        if current_name == normalized_name:
            result['skipped'] += 1
            continue

        try:
            update_moodle_inplace_editable(
                {
                    'component': 'format_topics',
                    'itemtype': 'sectionname',
                    'itemid': int(section['id']),
                    'value': normalized_name,
                    'courseid': course_id,
                }
            )
            result['updated'] += 1
        except Exception as exc:
            result['errors'].append(f'Seção {index}: {exc}')

    return result


def _resolve_offer_year(calendario_letivo: CalendarioLetivo) -> int:
    try:
        return int(str(calendario_letivo.ano_letivo).split('/')[0])
    except (TypeError, ValueError, AttributeError):
        return timezone.now().year


def _ensure_offer_category_id(oferta: OfertaCurso) -> int:
    root_category_id = int(MOODLE_COURSE_ROOT_CATEGORY_IDS['tecnico'][0])
    branch_category_id = _ensure_moodle_category(
        name=OFFER_BRANCH_CATEGORY_NAME,
        idnumber='suap-ofertas-tecnico',
        parent_id=root_category_id,
        description='Ofertas operacionais de cursos técnicos criadas pelo SUAP.',
    )
    polo_category_id = _ensure_moodle_category(
        name=oferta.polo.nome,
        idnumber=f'suap-ofertas-polo-{oferta.polo.codigo}',
        parent_id=branch_category_id,
        description=f'Ofertas do polo {oferta.polo.nome}.',
    )
    return _ensure_moodle_category(
        name=oferta.curso_base.nome,
        idnumber=f'suap-ofertas-curso-{oferta.curso_base.id}',
        parent_id=polo_category_id,
        description=f'Ofertas do curso técnico {oferta.curso_base.nome}.',
    )


def _ensure_moodle_category(*, name: str, idnumber: str, parent_id: int, description: str = '') -> int:
    categories = get_moodle_categories()
    normalized_name = (name or '').strip()
    normalized_idnumber = (idnumber or '').strip()

    for category in categories:
        if (category.get('idnumber') or '').strip() == normalized_idnumber:
            return int(category['id'])

    for category in categories:
        if (category.get('parent') or 0) == parent_id and (category.get('name') or '').strip().lower() == normalized_name.lower():
            return int(category['id'])

    response = create_moodle_categories(
        {
            'categories': [
                {
                    'name': normalized_name,
                    'idnumber': normalized_idnumber,
                    'parent': parent_id,
                    'description': description,
                    'descriptionformat': 1,
                }
            ]
        }
    )
    payload = response[0] if isinstance(response, list) and response else response
    return int(payload['id'])


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