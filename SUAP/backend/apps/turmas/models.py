from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.cursos.models import Curso
from apps.usuarios.models import PerfilUsuario


class Polo(models.Model):
    """Localidade/polo de atendimento para turmas itinerantes."""

    nome = models.CharField(max_length=120, verbose_name='Nome do Polo')
    municipio = models.CharField(max_length=100, verbose_name='Município')
    uf = models.CharField(max_length=2, default='RO', verbose_name='UF')
    endereco = models.CharField(max_length=255, blank=True, default='', verbose_name='Endereço')
    ativo = models.BooleanField(default=True, verbose_name='Ativo')

    class Meta:
        verbose_name = 'Polo'
        verbose_name_plural = 'Polos'
        ordering = ['municipio', 'nome']

    def __str__(self):
        return f'{self.nome} — {self.municipio}/{self.uf}'


class Turma(models.Model):
    STATUS_CHOICES = (
        ('PLANEJADA', 'Planejada'),
        ('ATIVA', 'Ativa'),
        ('ENCERRADA', 'Encerrada'),
        ('CANCELADA', 'Cancelada'),
    )

    MODALIDADE_CHOICES = (
        ('PRESENCIAL', 'Presencial'),
        ('REMOTO', 'Remoto'),
        ('ITINERANTE', 'Itinerante'),
        ('HIBRIDO', 'Híbrido'),
    )

    TRANSICOES_STATUS = {
        'PLANEJADA': {'ATIVA', 'CANCELADA'},
        'ATIVA': {'ENCERRADA', 'CANCELADA'},
        'ENCERRADA': set(),
        'CANCELADA': set(),
    }

    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='turmas')
    nome = models.CharField(max_length=100)
    ano_letivo = models.PositiveIntegerField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PLANEJADA')
    modalidade = models.CharField(
        max_length=15,
        choices=MODALIDADE_CHOICES,
        default='PRESENCIAL',
        verbose_name='Modalidade',
    )
    capacidade_maxima = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Capacidade Máxima',
        help_text='Deixe em branco para sem limite.',
    )
    # T033: polo obrigatório para turmas itinerantes
    polo = models.ForeignKey(
        Polo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turmas',
        verbose_name='Polo/Localidade',
        help_text='Obrigatório para turmas com modalidade Itinerante.',
    )
    professor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turmas_responsavel',
        limit_choices_to={'tipo': PerfilUsuario.PROFESSOR}
    )

    def clean(self):
        errors = {}

        if self.modalidade == "REMOTO":
            unidade = getattr(self.curso, "unidade", None)
            if unidade is None:
                errors["modalidade"] = "Turmas remotas exigem um curso vinculado a uma unidade."
            else:
                unidade_codigo = (unidade.codigo or "").strip().lower()
                if unidade_codigo != "sede":
                    errors["modalidade"] = f"Turmas remotas devem estar vinculadas a cursos da unidade Sede (codigo 'sede'), nao a '{unidade.codigo}'."

        # T033: polo obrigatório para turmas itinerantes
        if self.modalidade == "ITINERANTE" and not self.polo_id:
            errors["polo"] = "Polo/localidade é obrigatório para turmas itinerantes."

        if not self.pk:
            if errors:
                raise ValidationError(errors)
            return

        original = Turma.objects.filter(pk=self.pk).values_list('status', flat=True).first()
        if not original or original == self.status:
            if errors:
                raise ValidationError(errors)
            return

        permitidos = self.TRANSICOES_STATUS.get(original, set())
        if self.status not in permitidos:
            errors["status"] = f'Transicao de status invalida: {original} -> {self.status}.'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo}"


class DiarioAcademico(models.Model):
    """Diário de Classe por turma — padrão SEDUC-RO."""

    STATUS_CHOICES = (
        ('ABERTO',  'Aberto'),
        ('FECHADO', 'Fechado'),
        ('REVISAO', 'Em Revisão'),
    )

    # T037/T042: tipo de encontro para distinção entre presencial, online e itinerante
    TIPO_AULA_CHOICES = (
        ('REGULAR', 'Regular'),
        ('ONLINE', 'Online'),
        ('ENCONTRO_ITINERANTE', 'Encontro Itinerante'),
    )

    turma                 = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='diarios', verbose_name='Turma')
    periodo               = models.CharField(max_length=50, verbose_name='Período (ex: 2025/1)')
    componente_curricular = models.CharField(max_length=100, blank=True, default='', verbose_name='Componente Curricular')
    tipo_aula             = models.CharField(
        max_length=20,
        choices=TIPO_AULA_CHOICES,
        default='REGULAR',
        verbose_name='Tipo de Aula',
    )
    data_abertura         = models.DateField(auto_now_add=True, verbose_name='Data de Abertura')
    data_fechamento       = models.DateField(null=True, blank=True, verbose_name='Data de Fechamento')
    status                = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ABERTO', verbose_name='Status')
    observacoes           = models.TextField(blank=True, verbose_name='Observações')
    aberto_por            = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diarios_abertos',
        verbose_name='Aberto por',
    )
    fechado_por           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='diarios_fechados',
        verbose_name='Fechado por',
    )

    class Meta:
        verbose_name = 'Diário Acadêmico'
        verbose_name_plural = 'Diários Acadêmicos'
        ordering = ['-data_abertura']
        unique_together = ('turma', 'periodo')

    def __str__(self):
        return f'Diário – {self.turma} / {self.periodo} [{self.get_status_display()}]'

    # ── Documento oficial padrão SEDUC-RO ────────────────────────────────────

    @staticmethod
    def _meses():
        return ['janeiro','fevereiro','março','abril','maio','junho',
                'julho','agosto','setembro','outubro','novembro','dezembro']

    @staticmethod
    def _meses_abr():
        return ['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']

    @staticmethod
    def _dpt(d) -> str:
        m = ['janeiro','fevereiro','março','abril','maio','junho',
             'julho','agosto','setembro','outubro','novembro','dezembro']
        return f'{d.day:02d} de {m[d.month - 1]} de {d.year}'

    def gerar_documento(self) -> str:
        """
        Retorna o Diário de Classe no formato padrão SEDUC-RO para impressão/arquivo.
        Inclui: identificação, controle de frequência e quadro de notas/resultado.
        """
        from apps.notas.models import Nota
        from apps.frequencia.models import Frequencia

        W = 92
        MAB = self._meses_abr()

        unidade  = self.turma.curso.unidade
        municipio = (f"{unidade.cidade} – {unidade.uf}" if unidade.cidade else "Porto Velho – RO")
        prof_nome = (self.turma.professor_responsavel.get_full_name()
                     if self.turma.professor_responsavel else '________________________________')
        comp = self.componente_curricular or 'Componente Curricular'

        matriculas = list(
            self.turma.matriculas.select_related('aluno')
            .order_by('aluno__last_name', 'aluno__first_name')
        )

        # Todas as datas com registro de frequência
        todas_datas = sorted(set(
            Frequencia.objects.filter(matricula__in=matriculas)
            .values_list('data', flat=True)
        ))

        # Mapa frequência: (matricula_id, data) → bool
        freq_map = {
            (f.matricula_id, f.data): f.presente
            for f in Frequencia.objects.filter(matricula__in=matriculas)
        }

        # Mapa notas: matricula_id → [Nota, ...]
        notas_map = {}
        for n in Nota.objects.filter(matricula__in=matriculas).order_by('data_lancamento'):
            notas_map.setdefault(n.matricula_id, []).append(n)

        def _fmt(v):
            return f'{v:.1f}'.replace('.', ',') if v is not None else '---'

        # ── CABEÇALHO ─────────────────────────────────────────────────────────
        doc = [
            f"\n{'=' * W}",
            f"  GOVERNO DO ESTADO DE RONDÔNIA",
            f"  SECRETARIA DE ESTADO DA EDUCAÇÃO – SEDUC/RO",
            f"  {unidade.nome.upper()}",
            (f"  Endereço: {unidade.endereco}  –  {municipio}" if unidade.endereco
             else f"  {municipio}"),
            f"{'=' * W}",
            f"",
            f"  {'D I Á R I O   D E   C L A S S E':^{W - 4}}",
            f"",
            f"{'─' * W}",
            f"  Escola         : {unidade.nome}",
            f"  Turma          : {self.turma.nome:<25}  Ano Letivo : {self.turma.ano_letivo}",
            f"  Curso          : {self.turma.curso.nome}",
            f"  Componente     : {comp}",
            f"  Professor(a)   : {prof_nome}",
            f"  Período        : {self.periodo}",
            f"  Abertura       : {self._dpt(self.data_abertura)}"
            + (f"   |   Fechamento: {self._dpt(self.data_fechamento)}"
               if self.data_fechamento else ""),
            f"  Status         : {self.get_status_display().upper()}",
            f"{'─' * W}",
        ]

        # ── FREQUÊNCIA ────────────────────────────────────────────────────────
        doc += [f"", f"  {'CONTROLE DE FREQUÊNCIA':^{W - 4}}", f""]

        if todas_datas:
            MAX_COLS = 18
            for ci in range(0, len(todas_datas), MAX_COLS):
                chunk = todas_datas[ci:ci + MAX_COLS]
                col_w = 5  # chars per date column
                hdr_datas = ''.join(
                    f"{d.day:02d}/{MAB[d.month - 1]}".ljust(col_w + 1) for d in chunk
                )
                sep_datas = '─' * (len(chunk) * (col_w + 1))
                doc.append(
                    f"  {'N°':>3}  {'NOME DO ALUNO':<32}  {hdr_datas}  {'FAL':>3}  {'%FREQ':>5}"
                )
                doc.append(f"  {'─' * 3}  {'─' * 32}  {sep_datas}  {'─' * 3}  {'─' * 5}")

                for idx, mat in enumerate(matriculas, 1):
                    nome = mat.aluno.get_full_name().upper()[:32]
                    presencas = ''.join(
                        ('P ' if freq_map.get((mat.id, d)) is True
                         else 'F ' if freq_map.get((mat.id, d)) is False
                         else '- ').ljust(col_w + 1)
                        for d in chunk
                    )
                    faltas = sum(
                        1 for d in todas_datas
                        if freq_map.get((mat.id, d)) is False
                    )
                    total = len(todas_datas)
                    pct = (f"{(total - faltas) / total * 100:.0f}%"
                           if total else '---')
                    doc.append(
                        f"  {idx:3d}  {nome:<32}  {presencas}  {faltas:>3}  {pct:>5}"
                    )
                doc.append(f"  {'─' * W}")
        else:
            doc.append("  (Sem registros de frequência)")

        doc.append(f"  Total de Aulas Registradas: {len(todas_datas)}")

        # ── NOTAS / RESULTADO ─────────────────────────────────────────────────
        doc += [
            f"",
            f"{'─' * W}",
            f"  {'NOTAS E RESULTADO FINAL':^{W - 4}}",
            f"",
            f"  {'N°':>3}  {'NOME DO ALUNO':<32}  {'Av.1':>5}  {'Av.2':>5}  {'Av.3':>5}  {'Av.4':>5}  {'MÉDIA':>6}  {'FREQ%':>5}  {'RESULTADO':<22}",
            f"  {'─' * 3}  {'─' * 32}  {'─' * 5}  {'─' * 5}  {'─' * 5}  {'─' * 5}  {'─' * 6}  {'─' * 5}  {'─' * 22}",
        ]

        for idx, mat in enumerate(matriculas, 1):
            nl = notas_map.get(mat.id, [])
            nv = [_fmt(n.valor) for n in nl[:4]]
            while len(nv) < 4:
                nv.append('---')
            try:
                cons = mat.consolidacao
                media   = _fmt(cons.media_final)
                freq_p  = (f"{cons.percentual_frequencia:.1f}%".replace('.', ',')
                           if cons.percentual_frequencia else '---')
                result  = cons.get_situacao_display()
            except Exception:
                media = freq_p = '---'
                result = 'Pendente'

            nome = mat.aluno.get_full_name().upper()[:32]
            doc.append(
                f"  {idx:3d}  {nome:<32}  {nv[0]:>5}  {nv[1]:>5}  {nv[2]:>5}  {nv[3]:>5}  {media:>6}  {freq_p:>5}  {result:<22}"
            )

        doc.append(f"  {'─' * W}")

        # ── ASSINATURAS ───────────────────────────────────────────────────────
        data_ref = self.data_fechamento or self.data_abertura
        doc += [
            f"",
            f"  {municipio}, {self._dpt(data_ref)}",
            f"",
            f"",
            f"  {'─' * 38}          {'─' * 38}",
            f"  {prof_nome:<38}          {'________________________________':<38}",
            f"  Professor(a) / Componente Curricular          Coordenador(a) Pedagógico(a)",
            f"",
            f"",
            f"  {'─' * 38}",
            f"  {'________________________________':<38}",
            f"  Diretor(a)",
            f"",
            f"{'=' * W}",
        ]

        return '\n'.join(doc)


class DiarioMaterialAula(models.Model):
    diario = models.ForeignKey(DiarioAcademico, on_delete=models.CASCADE, related_name='materiais_aula')
    titulo = models.CharField(max_length=160, verbose_name='Título')
    descricao = models.TextField(blank=True, default='', verbose_name='Descrição')
    url_material = models.URLField(blank=True, default='', verbose_name='URL do material')
    data_referencia = models.DateField(null=True, blank=True, verbose_name='Data de referência')
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diarios_materiais_criados',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Material de Aula do Diário'
        verbose_name_plural = 'Materiais de Aula dos Diários'
        ordering = ['-data_referencia', '-created_at']

    def __str__(self):
        return f'{self.titulo} - {self.diario}'


class DiarioOcorrencia(models.Model):
    TIPO_CHOICES = (
        ('OCORRENCIA', 'Ocorrência'),
        ('SUSPENSAO', 'Suspensão'),
    )

    diario = models.ForeignKey(DiarioAcademico, on_delete=models.CASCADE, related_name='ocorrencias')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OCORRENCIA', verbose_name='Tipo')
    titulo = models.CharField(max_length=160, verbose_name='Título')
    descricao = models.TextField(verbose_name='Descrição')
    data_ocorrencia = models.DateField(verbose_name='Data da ocorrência')
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diarios_ocorrencias_registradas',
        verbose_name='Registrado por',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Ocorrência do Diário'
        verbose_name_plural = 'Ocorrências dos Diários'
        ordering = ['-data_ocorrencia', '-created_at']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.titulo}'
