from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from apps.unidades.models import Unidade


class EixoTecnologico(models.Model):
    descricao = models.CharField(max_length=200, unique=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Eixo Tecnológico'
        verbose_name_plural = 'Eixos Tecnológicos'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class TipoComponente(models.Model):
    descricao = models.CharField(max_length=200, unique=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Tipo do Componente'
        verbose_name_plural = 'Tipos do Componente'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class NivelEnsino(models.Model):
    descricao = models.CharField(max_length=200, unique=True, verbose_name='Descrição')

    class Meta:
        verbose_name = 'Nível de Ensino'
        verbose_name_plural = 'Níveis de Ensino'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class AreaCurso(models.Model):
    descricao = models.CharField(max_length=200, unique=True, verbose_name='Descrição')
    codigo_cine = models.CharField(max_length=20, blank=True, default='', verbose_name='Código CINE')
    codigo_area_detalhada = models.CharField(max_length=20, blank=True, default='', verbose_name='Código da Área Detalhada')
    codigo_area_especifica = models.CharField(max_length=20, blank=True, default='', verbose_name='Código da Área Específica')
    codigo_area_geral = models.CharField(max_length=20, blank=True, default='', verbose_name='Código da Área Geral')
    cine = models.CharField(max_length=200, blank=True, default='', verbose_name='CINE')
    area_detalhada = models.CharField(max_length=200, blank=True, default='', verbose_name='Área Detalhada')
    area_especifica = models.CharField(max_length=200, blank=True, default='', verbose_name='Área Específica')
    area_geral = models.CharField(max_length=200, blank=True, default='', verbose_name='Área Geral')

    class Meta:
        verbose_name = 'Área de Curso'
        verbose_name_plural = 'Áreas de Cursos'
        ordering = ['descricao']

    def __str__(self):
        titulo = self.cine or self.area_detalhada or self.descricao
        return f'{self.codigo_cine} - {titulo}'.strip(' -')


class Curso(models.Model):
    TIPO_CURSO_CHOICES = [
        ("tecnico", "Educação Profissional Técnica"),
        ("formacao_inicial", "Formação Inicial e Continuada"),
        ("itinerante", "Qualificação Profissional Itinerante"),
    ]
    tipo_curso = models.CharField(
        max_length=32,
        choices=TIPO_CURSO_CHOICES,
        default="formacao_inicial",
        verbose_name="Tipo de Curso"
    )
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE, related_name='cursos')
    area_curso = models.ForeignKey('AreaCurso', on_delete=models.SET_NULL, related_name='cursos', null=True, blank=True, verbose_name='Área do Curso')
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=16, blank=True, default='', verbose_name='Sigla')
    moodle_course_id = models.PositiveIntegerField(null=True, blank=True, unique=True, verbose_name='ID do Curso no Moodle')
    moodle_shortname = models.CharField(max_length=100, blank=True, default='', verbose_name='Shortname do Moodle')
    eixo_tecnologico = models.CharField(max_length=200, blank=True, default='', verbose_name='Eixo Tecnológico')
    carga_horaria = models.PositiveIntegerField()
    matriz_curricular = models.ForeignKey(
        'MatrizCurricular',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cursos_ofertados',
        verbose_name='Matriz Curricular de Referência',
    )

    def __str__(self):
        return self.nome


class MatrizCurricular(models.Model):
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('VIGENTE', 'Vigente'),
        ('ENCERRADA', 'Encerrada'),
    ]

    curso_base = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='matrizes_curriculares',
        verbose_name='Curso Base',
    )
    nome = models.CharField(max_length=200, verbose_name='Nome')
    ano_referencia = models.PositiveIntegerField(verbose_name='Ano de Referência')
    versao = models.CharField(max_length=40, default='1.0', verbose_name='Versão')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RASCUNHO', verbose_name='Status')
    ativa = models.BooleanField(default=True, verbose_name='Ativa')
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    moodle_template_course_id = models.PositiveIntegerField(null=True, blank=True, unique=True, verbose_name='ID do Curso Modelo no Moodle')
    moodle_template_shortname = models.CharField(max_length=100, blank=True, default='', verbose_name='Shortname do Curso Modelo no Moodle')
    moodle_template_category_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID da Categoria do Curso Modelo no Moodle')
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name='Última Sincronização')
    last_sync_status = models.CharField(max_length=20, blank=True, default='', verbose_name='Status da Última Sincronização')
    last_sync_message = models.TextField(blank=True, default='', verbose_name='Mensagem da Última Sincronização')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Matriz Curricular'
        verbose_name_plural = 'Matrizes Curriculares'
        ordering = ['-ano_referencia', 'curso_base__nome', 'nome', 'versao']
        constraints = [
            models.UniqueConstraint(
                fields=['curso_base', 'ano_referencia', 'versao'],
                name='uniq_matriz_curricular_por_versao',
            ),
            models.UniqueConstraint(
                fields=['curso_base', 'ano_referencia'],
                condition=Q(status='VIGENTE'),
                name='uniq_matriz_curricular_vigente_por_ano',
            ),
        ]

    def clean(self):
        if self.curso_base_id and self.curso_base.tipo_curso != 'tecnico':
            raise ValidationError({'curso_base': 'Matrizes curriculares explícitas são suportadas apenas para cursos técnicos nesta fase.'})

        if not (self.nome or '').strip():
            raise ValidationError({'nome': 'Informe o nome da matriz curricular.'})

        if not self.ano_referencia:
            raise ValidationError({'ano_referencia': 'Informe o ano de referência da matriz curricular.'})

        if not (self.versao or '').strip():
            raise ValidationError({'versao': 'Informe a versão da matriz curricular.'})

        if not (self.status or '').strip():
            raise ValidationError({'status': 'Informe o status da matriz curricular.'})

    def save(self, *args, **kwargs):
        self.nome = (self.nome or '').strip()
        self.versao = (self.versao or '').strip()
        self.last_sync_status = (self.last_sync_status or '').strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    @property
    def permite_edicao(self):
        return self.status != 'VIGENTE'

    @property
    def pode_publicar(self):
        return self.status == 'RASCUNHO'

    @property
    def pode_encerrar(self):
        return self.status != 'ENCERRADA'

    @property
    def pode_definir_vigente(self):
        return self.status != 'ENCERRADA'

    @property
    def total_modulos(self):
        return (
            self.componentes.exclude(modulo_numero__isnull=True)
            .values('modulo_numero')
            .distinct()
            .count()
        )

    def componentes_por_modulo(self):
        componentes = list(
            self.componentes.order_by('modulo_numero', 'ordem_no_modulo', 'ordem', 'nome')
        )
        agrupados = []
        atual = None

        for componente in componentes:
            chave_modulo = componente.modulo_numero or 0
            if atual is None or atual['modulo_numero'] != chave_modulo:
                atual = {
                    'modulo_numero': componente.modulo_numero,
                    'modulo_nome': componente.modulo_nome or (f'Módulo {componente.modulo_numero}' if componente.modulo_numero else 'Sem módulo'),
                    'componentes': [],
                }
                agrupados.append(atual)

            atual['componentes'].append(componente)

        return agrupados


class ComponenteCurricular(models.Model):
    """Componente da matriz curricular de um curso."""

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='componentes', verbose_name='Curso')
    matriz_curricular = models.ForeignKey(
        MatrizCurricular,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='componentes',
        verbose_name='Matriz Curricular',
    )
    nome = models.CharField(max_length=200, verbose_name='Nome')
    abreviatura = models.CharField(max_length=30, blank=True, default='', verbose_name='Abreviatura')
    sigla = models.CharField(max_length=30, blank=True, default='', verbose_name='Sigla')
    descricao_diploma_historico = models.CharField(max_length=200, blank=True, default='', verbose_name='Descrição no Diploma e Histórico')
    diretoria = models.CharField(max_length=120, blank=True, default='', verbose_name='Diretoria')
    ativo = models.BooleanField(default=True, verbose_name='Está ativo')
    tipo_componente = models.CharField(max_length=80, blank=True, default='', verbose_name='Tipo do Componente')
    nivel_ensino = models.CharField(max_length=80, blank=True, default='', verbose_name='Nível de ensino')
    tipo_componente_catalogo = models.ForeignKey(
        TipoComponente,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='componentes_curriculares',
        verbose_name='Tipo do Componente (Catálogo)',
    )
    nivel_ensino_catalogo = models.ForeignKey(
        NivelEnsino,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='componentes_curriculares',
        verbose_name='Nível de Ensino (Catálogo)',
    )
    grupo_atuacao = models.CharField(max_length=120, blank=True, default='', verbose_name='Grupo de Atuação')
    carga_horaria = models.PositiveIntegerField(default=0, verbose_name='Carga Horária (h)')
    hora_aula = models.PositiveIntegerField(default=0, verbose_name='Hora/aula')
    qtd_creditos = models.PositiveIntegerField(default=0, verbose_name='Qtd. de créditos')
    sigla_qacademico = models.CharField(max_length=50, blank=True, default='', verbose_name='Sigla do Q-Acadêmico')
    observacao = models.TextField(blank=True, default='', verbose_name='Observação')
    ordem = models.PositiveIntegerField(default=1, verbose_name='Ordem')
    modulo_numero = models.PositiveIntegerField(null=True, blank=True, verbose_name='Número do Módulo')
    modulo_nome = models.CharField(max_length=120, blank=True, default='', verbose_name='Nome do Módulo')
    ordem_no_modulo = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ordem no Módulo')

    class Meta:
        verbose_name = 'Componente Curricular'
        verbose_name_plural = 'Componentes Curriculares'
        ordering = ['modulo_numero', 'ordem_no_modulo', 'ordem', 'nome']
        constraints = [
            models.UniqueConstraint(
                fields=['curso', 'nome'],
                condition=Q(matriz_curricular__isnull=True),
                name='uniq_componente_legado_por_curso_nome',
            ),
            models.UniqueConstraint(
                fields=['matriz_curricular', 'nome'],
                condition=Q(matriz_curricular__isnull=False),
                name='uniq_componente_por_matriz_nome',
            ),
            models.UniqueConstraint(
                fields=['matriz_curricular', 'modulo_numero', 'ordem_no_modulo'],
                condition=Q(matriz_curricular__isnull=False) & Q(modulo_numero__isnull=False) & Q(ordem_no_modulo__isnull=False),
                name='uniq_ordem_componente_por_modulo_matriz',
            ),
        ]

    def clean(self):
        errors = {}

        self.nome = (self.nome or '').strip()
        self.tipo_componente = (self.tipo_componente or '').strip()
        self.nivel_ensino = (self.nivel_ensino or '').strip()
        self.modulo_nome = (self.modulo_nome or '').strip()

        self._sync_catalog_fields()

        if not self.nome:
            errors['nome'] = 'Informe o nome do componente curricular.'

        if (self.carga_horaria or 0) <= 0:
            errors['carga_horaria'] = 'A carga horária deve ser maior que zero.'

        if self.matriz_curricular_id:
            if self.curso_id and self.matriz_curricular.curso_base_id != self.curso_id:
                errors['matriz_curricular'] = 'A matriz curricular selecionada não pertence ao curso informado.'

            if self.matriz_curricular.curso_base.tipo_curso == 'tecnico':
                if self.modulo_numero is None:
                    errors['modulo_numero'] = 'Informe o módulo para componentes vinculados a matrizes técnicas.'
                if self.ordem_no_modulo is None:
                    errors['ordem_no_modulo'] = 'Informe a ordem do componente dentro do módulo.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def _sync_catalog_fields(self):
        tipo_texto = (self.tipo_componente or '').strip()
        nivel_texto = (self.nivel_ensino or '').strip()

        if self.tipo_componente_catalogo_id:
            self.tipo_componente = self.tipo_componente_catalogo.descricao
        elif tipo_texto:
            self.tipo_componente_catalogo, _ = TipoComponente.objects.get_or_create(descricao=tipo_texto)
            self.tipo_componente = self.tipo_componente_catalogo.descricao
        else:
            self.tipo_componente_catalogo = None

        if self.nivel_ensino_catalogo_id:
            self.nivel_ensino = self.nivel_ensino_catalogo.descricao
        elif nivel_texto:
            self.nivel_ensino_catalogo, _ = NivelEnsino.objects.get_or_create(descricao=nivel_texto)
            self.nivel_ensino = self.nivel_ensino_catalogo.descricao
        else:
            self.nivel_ensino_catalogo = None

    @property
    def matriz_curricular_efetiva(self):
        return self.matriz_curricular or getattr(self.curso, 'matriz_curricular', None)

    @property
    def matriz_curricular_efetiva_nome(self):
        matriz = self.matriz_curricular_efetiva
        if matriz is not None:
            return matriz.nome
        if self.curso_id:
            return self.curso.nome
        return ''

    def __str__(self):
        return f'{self.nome} ({self.curso.nome})'


class MatrizCurricularLog(models.Model):
    EVENTO_CHOICES = [
        ('criacao_matriz', 'Criação de Matriz'),
        ('clonagem_matriz', 'Clonagem de Matriz'),
        ('publicacao_matriz', 'Publicação de Matriz'),
        ('encerramento_matriz', 'Encerramento de Matriz'),
        ('definicao_vigencia', 'Definição de Vigência'),
        ('migracao_componentes', 'Migração de Componentes'),
        ('criacao_curso_modelo', 'Criação de Curso Modelo no Moodle'),
        ('atualizacao_curso_modelo', 'Atualização de Curso Modelo no Moodle'),
        ('criacao_oferta_real', 'Criação de Oferta Real'),
        ('importacao_conteudo', 'Importação/Cópia de Conteúdo'),
        ('falha_sincronizacao', 'Falha de Sincronização'),
    ]
    STATUS_CHOICES = [
        ('info', 'Informação'),
        ('success', 'Sucesso'),
        ('error', 'Erro'),
    ]

    matriz_curricular = models.ForeignKey(
        MatrizCurricular,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='logs',
        verbose_name='Matriz Curricular',
    )
    curso = models.ForeignKey(
        Curso,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='logs_matriz_curricular',
        verbose_name='Curso Relacionado',
    )
    evento = models.CharField(max_length=40, choices=EVENTO_CHOICES, verbose_name='Evento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='info', verbose_name='Status')
    mensagem = models.TextField(blank=True, default='', verbose_name='Mensagem')
    payload = models.JSONField(default=dict, blank=True, verbose_name='Payload')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Matriz Curricular'
        verbose_name_plural = 'Logs de Matrizes Curriculares'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_evento_display()} - {self.status}'

class CalendarioLetivo(models.Model):
    """Calendário Letivo por ano/curso  Entidade Acadêmica do Class Diagram."""

    STATUS_CHOICES = (
        ('PLANEJADO', 'Planejado'),
        ('VIGENTE',   'Vigente'),
        ('ENCERRADO', 'Encerrado'),
    )

    ano_letivo   = models.CharField(max_length=9, verbose_name='Ano Letivo')
    curso        = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='calendarios',
        verbose_name='Curso',
    )
    data_inicio  = models.DateField(verbose_name='Data de Início')
    data_fim     = models.DateField(verbose_name='Data de Fim')
    dias_letivos = models.PositiveIntegerField(default=200, verbose_name='Dias Letivos')
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PLANEJADO', verbose_name='Status')
    descricao    = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Calendário Letivo'
        verbose_name_plural = 'Calendários Letivos'
        unique_together = ('ano_letivo', 'curso')
        ordering = ['-ano_letivo', 'curso']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.data_inicio and self.data_fim and self.data_fim <= self.data_inicio:
            raise ValidationError({'data_fim': 'A data de fim deve ser posterior à data de início.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Calendário {self.ano_letivo}  {self.curso.nome} [{self.get_status_display()}]'


class OfertaCurso(models.Model):
    STATUS_CHOICES = [
        ('PLANEJADA', 'Planejada'),
        ('ATIVA', 'Ativa'),
        ('ENCERRADA', 'Encerrada'),
        ('CANCELADA', 'Cancelada'),
    ]
    TURNO_CHOICES = [
        ('MANHA', 'Manhã'),
        ('TARDE', 'Tarde'),
        ('NOITE', 'Noite'),
        ('INTEGRAL', 'Integral'),
    ]

    curso_base = models.ForeignKey(
        Curso,
        on_delete=models.CASCADE,
        related_name='ofertas',
        verbose_name='Curso Base',
    )
    matriz_curricular = models.ForeignKey(
        MatrizCurricular,
        on_delete=models.PROTECT,
        related_name='ofertas',
        verbose_name='Matriz Curricular',
    )
    polo = models.ForeignKey(
        Unidade,
        on_delete=models.PROTECT,
        related_name='ofertas_curso',
        verbose_name='Polo',
    )
    calendario_letivo = models.ForeignKey(
        CalendarioLetivo,
        on_delete=models.PROTECT,
        related_name='ofertas',
        verbose_name='Calendário Letivo',
    )
    nome = models.CharField(max_length=200, verbose_name='Nome da Oferta')
    codigo_turma = models.CharField(max_length=50, blank=True, default='', verbose_name='Turma')
    ano_oferta = models.PositiveIntegerField(verbose_name='Ano da Oferta')
    periodo_letivo = models.CharField(max_length=20, default='1', verbose_name='Período Letivo')
    turno = models.CharField(max_length=16, choices=TURNO_CHOICES, default='NOITE', verbose_name='Turno')
    vagas_totais = models.PositiveIntegerField(default=0, verbose_name='Vagas Totais')
    vagas_ocupadas = models.PositiveIntegerField(default=0, verbose_name='Vagas Ocupadas')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANEJADA', verbose_name='Status')
    observacao = models.TextField(blank=True, default='', verbose_name='Observações')
    moodle_course_id = models.PositiveIntegerField(null=True, blank=True, unique=True, verbose_name='ID do Curso da Oferta no Moodle')
    moodle_shortname = models.CharField(max_length=100, blank=True, default='', verbose_name='Shortname da Oferta no Moodle')
    moodle_category_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID da Categoria da Oferta no Moodle')
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name='Última Sincronização')
    last_sync_status = models.CharField(max_length=20, blank=True, default='', verbose_name='Status da Última Sincronização')
    last_sync_message = models.TextField(blank=True, default='', verbose_name='Mensagem da Última Sincronização')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Oferta de Curso'
        verbose_name_plural = 'Ofertas de Cursos'
        ordering = ['-ano_oferta', '-periodo_letivo', 'curso_base__nome', 'codigo_turma', 'nome']
        constraints = [
            models.UniqueConstraint(
                fields=['curso_base', 'matriz_curricular', 'polo', 'ano_oferta', 'periodo_letivo', 'codigo_turma'],
                name='uniq_oferta_curso_por_execucao',
            ),
        ]

    def clean(self):
        errors = {}

        self.nome = (self.nome or '').strip()
        self.codigo_turma = (self.codigo_turma or '').strip()
        self.periodo_letivo = (self.periodo_letivo or '').strip()
        self.observacao = (self.observacao or '').strip()
        self.moodle_shortname = (self.moodle_shortname or '').strip()
        self.last_sync_status = (self.last_sync_status or '').strip()

        if self.curso_base_id and self.curso_base.tipo_curso != 'tecnico':
            errors['curso_base'] = 'OfertaCurso está disponível apenas para cursos técnicos nesta fase.'

        if self.matriz_curricular_id and self.curso_base_id and self.matriz_curricular.curso_base_id != self.curso_base_id:
            errors['matriz_curricular'] = 'A matriz curricular selecionada não pertence ao curso base informado.'

        if self.calendario_letivo_id and self.curso_base_id and self.calendario_letivo.curso_id != self.curso_base_id:
            errors['calendario_letivo'] = 'O calendário letivo informado não pertence ao curso base selecionado.'

        if not self.nome:
            errors['nome'] = 'Informe o nome da oferta do curso.'

        if not self.ano_oferta:
            errors['ano_oferta'] = 'Informe o ano da oferta.'

        if not self.periodo_letivo:
            errors['periodo_letivo'] = 'Informe o período letivo da oferta.'

        if self.vagas_ocupadas > self.vagas_totais:
            errors['vagas_ocupadas'] = 'As vagas ocupadas não podem ser maiores que as vagas totais.'

        if self.matriz_curricular_id and self.matriz_curricular.status == 'ENCERRADA':
            errors['matriz_curricular'] = 'Não é possível criar oferta com matriz curricular encerrada.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def vagas_disponiveis(self):
        return max((self.vagas_totais or 0) - (self.vagas_ocupadas or 0), 0)

    @property
    def pode_sincronizar_moodle(self):
        return self.status in {'PLANEJADA', 'ATIVA'}

    @property
    def modulo_nomes(self):
        modulos = []
        for modulo in self.matriz_curricular.componentes_por_modulo():
            modulos.append(modulo['modulo_nome'])
        return modulos

    def __str__(self):
        return self.nome


class OfertaCursoLog(models.Model):
    EVENTO_CHOICES = [
        ('criacao_oferta', 'Criação de Oferta'),
        ('atualizacao_oferta', 'Atualização de Oferta'),
        ('sincronizacao_moodle', 'Sincronização com Moodle'),
        ('importacao_conteudo', 'Importação/Cópia de Conteúdo'),
        ('falha_sincronizacao', 'Falha de Sincronização'),
    ]
    STATUS_CHOICES = [
        ('info', 'Informação'),
        ('success', 'Sucesso'),
        ('error', 'Erro'),
    ]

    oferta_curso = models.ForeignKey(
        OfertaCurso,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Oferta do Curso',
    )
    evento = models.CharField(max_length=40, choices=EVENTO_CHOICES, verbose_name='Evento')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='info', verbose_name='Status')
    mensagem = models.TextField(blank=True, default='', verbose_name='Mensagem')
    payload = models.JSONField(default=dict, blank=True, verbose_name='Payload')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Oferta de Curso'
        verbose_name_plural = 'Logs de Ofertas de Cursos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_evento_display()} - {self.status}'
