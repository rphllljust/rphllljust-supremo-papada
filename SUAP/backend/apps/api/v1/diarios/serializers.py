from decimal import Decimal, ROUND_HALF_UP

from rest_framework import serializers

from apps.matriculas.models import Matricula
from apps.turmas.models import DiarioAcademico, DiarioMaterialAula, DiarioOcorrencia


def get_usuario_nome(usuario):
    if not usuario:
        return None

    nome = usuario.get_full_name().strip()
    return nome or usuario.username


def get_aluno_nome(matricula):
    aluno = matricula.aluno
    if getattr(aluno, 'pessoa', None) and aluno.pessoa.nome_completo:
        return aluno.pessoa.nome_completo

    nome = aluno.get_full_name().strip()
    return nome or aluno.username


def quantize_value(value, places='0.01'):
    if value is None:
        return None
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def build_student_diary_snapshot(matricula: Matricula):
    notas = sorted(matricula.notas.all(), key=lambda item: (item.data_lancamento, item.id))
    frequencias = list(matricula.frequencias.all())

    if notas:
        soma = sum((nota.valor * nota.peso for nota in notas), Decimal('0'))
        pesos = sum((nota.peso for nota in notas), Decimal('0'))
        media = quantize_value(soma / pesos) if pesos else None
    else:
        media = None

    if frequencias:
        presencas = sum(1 for item in frequencias if item.presente)
        percentual = quantize_value((Decimal(presencas) / Decimal(len(frequencias))) * Decimal('100'))
    else:
        percentual = None

    consolidacao = getattr(matricula, 'consolidacao', None)
    media_final = quantize_value(getattr(consolidacao, 'media_final', None) if consolidacao else media)
    percentual_final = quantize_value(getattr(consolidacao, 'percentual_frequencia', None) if consolidacao else percentual)

    if consolidacao:
        situacao = consolidacao.get_situacao_display()
    elif media_final is None and percentual_final is None:
        situacao = 'Pendente'
    elif media_final is not None and media_final < Decimal('6.00') and percentual_final is not None and percentual_final < Decimal('75.00'):
        situacao = 'Reprovado por Nota e Frequência'
    elif media_final is not None and media_final < Decimal('6.00'):
        situacao = 'Reprovado por Nota'
    elif percentual_final is not None and percentual_final < Decimal('75.00'):
        situacao = 'Reprovado por Frequência'
    else:
        situacao = 'Aprovado'

    return {
        'id': matricula.id,
        'numero_matricula': matricula.numero_matricula,
        'aluno_nome': get_aluno_nome(matricula),
        'status': matricula.status,
        'status_display': matricula.get_status_display(),
        'media_final': media_final,
        'percentual_frequencia': percentual_final,
        'situacao': situacao,
        'total_notas': len(notas),
        'total_registros_frequencia': len(frequencias),
        'notas': [
            {
                'id': nota.id,
                'descricao': nota.descricao,
                'valor': nota.valor,
                'peso': nota.peso,
                'data_lancamento': nota.data_lancamento,
            }
            for nota in notas
        ],
    }


class DiarioMaterialAulaSerializer(serializers.ModelSerializer):
    criado_por_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DiarioMaterialAula
        fields = [
            'id',
            'titulo',
            'descricao',
            'url_material',
            'data_referencia',
            'criado_por',
            'criado_por_nome',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['criado_por', 'created_at', 'updated_at']

    def get_criado_por_nome(self, obj):
        return get_usuario_nome(obj.criado_por)


class DiarioOcorrenciaSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    registrado_por_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DiarioOcorrencia
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'descricao',
            'data_ocorrencia',
            'registrado_por',
            'registrado_por_nome',
            'created_at',
        ]
        read_only_fields = ['registrado_por', 'created_at']

    def get_registrado_por_nome(self, obj):
        return get_usuario_nome(obj.registrado_por)


class DiarioSerializer(serializers.ModelSerializer):
    turma_nome = serializers.CharField(source='turma.nome', read_only=True)
    ano_letivo = serializers.IntegerField(source='turma.ano_letivo', read_only=True)
    curso = serializers.IntegerField(source='turma.curso_id', read_only=True)
    curso_nome = serializers.CharField(source='turma.curso.nome', read_only=True)
    unidade = serializers.IntegerField(source='turma.curso.unidade_id', read_only=True)
    unidade_nome = serializers.CharField(source='turma.curso.unidade.nome', read_only=True)
    professor = serializers.IntegerField(source='turma.professor_responsavel_id', read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    aberto_por_nome = serializers.SerializerMethodField(read_only=True)
    fechado_por_nome = serializers.SerializerMethodField(read_only=True)
    total_matriculados = serializers.IntegerField(read_only=True)
    notas_pendentes = serializers.IntegerField(read_only=True)
    frequencias_pendentes = serializers.IntegerField(read_only=True)
    observacoes_resumo = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DiarioAcademico
        fields = [
            'id',
            'turma',
            'turma_nome',
            'ano_letivo',
            'curso',
            'curso_nome',
            'unidade',
            'unidade_nome',
            'professor',
            'professor_nome',
            'periodo',
            'componente_curricular',
            'data_abertura',
            'data_fechamento',
            'status',
            'status_display',
            'observacoes',
            'observacoes_resumo',
            'aberto_por',
            'aberto_por_nome',
            'fechado_por',
            'fechado_por_nome',
            'total_matriculados',
            'notas_pendentes',
            'frequencias_pendentes',
        ]
        read_only_fields = ['aberto_por', 'fechado_por', 'data_abertura', 'data_fechamento']

    def get_professor_nome(self, obj):
        return get_usuario_nome(obj.turma.professor_responsavel)

    def get_aberto_por_nome(self, obj):
        return get_usuario_nome(obj.aberto_por)

    def get_fechado_por_nome(self, obj):
        return get_usuario_nome(obj.fechado_por)

    def get_observacoes_resumo(self, obj):
        if not obj.observacoes:
            return ''
        return obj.observacoes[:140] + ('...' if len(obj.observacoes) > 140 else '')


class DiarioDetailSerializer(DiarioSerializer):
    estudantes = serializers.SerializerMethodField(read_only=True)
    materiais_aula = DiarioMaterialAulaSerializer(many=True, read_only=True)
    ocorrencias = serializers.SerializerMethodField(read_only=True)
    suspensoes = serializers.SerializerMethodField(read_only=True)
    estatisticas = serializers.SerializerMethodField(read_only=True)

    class Meta(DiarioSerializer.Meta):
        fields = DiarioSerializer.Meta.fields + [
            'estudantes',
            'materiais_aula',
            'ocorrencias',
            'suspensoes',
            'estatisticas',
        ]

    def get_estudantes(self, obj):
        matriculas = list(obj.turma.matriculas.all())
        return [build_student_diary_snapshot(matricula) for matricula in matriculas]

    def get_ocorrencias(self, obj):
        ocorrencias = [item for item in obj.ocorrencias.all() if item.tipo == 'OCORRENCIA']
        return DiarioOcorrenciaSerializer(ocorrencias, many=True).data

    def get_suspensoes(self, obj):
        suspensoes = [item for item in obj.ocorrencias.all() if item.tipo == 'SUSPENSAO']
        return DiarioOcorrenciaSerializer(suspensoes, many=True).data

    def get_estatisticas(self, obj):
        snapshots = self.get_estudantes(obj)
        total = len(snapshots)
        com_notas = sum(1 for item in snapshots if item['total_notas'] > 0)
        com_frequencia = sum(1 for item in snapshots if item['total_registros_frequencia'] > 0)
        medias = [item['media_final'] for item in snapshots if item['media_final'] is not None]
        frequencias = [item['percentual_frequencia'] for item in snapshots if item['percentual_frequencia'] is not None]

        return {
            'total_alunos': total,
            'alunos_com_notas': com_notas,
            'alunos_sem_notas': total - com_notas,
            'alunos_com_frequencia': com_frequencia,
            'alunos_sem_frequencia': total - com_frequencia,
            'media_geral': quantize_value(sum(medias, Decimal('0')) / Decimal(len(medias))) if medias else None,
            'frequencia_media': quantize_value(sum(frequencias, Decimal('0')) / Decimal(len(frequencias))) if frequencias else None,
            'aprovados': sum(1 for item in snapshots if item['situacao'] == 'Aprovado'),
            'pendentes': sum(1 for item in snapshots if item['situacao'] == 'Pendente'),
            'materiais_publicados': obj.materiais_aula.count(),
            'ocorrencias_registradas': sum(1 for item in obj.ocorrencias.all() if item.tipo == 'OCORRENCIA'),
            'suspensoes_registradas': sum(1 for item in obj.ocorrencias.all() if item.tipo == 'SUSPENSAO'),
        }