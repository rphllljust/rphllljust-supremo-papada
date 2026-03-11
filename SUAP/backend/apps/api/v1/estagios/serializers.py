from datetime import date

from rest_framework import serializers

from apps.estagio.models import AcompanhamentoEstagio, Estagio, TermoCompromisso


MATRICULA_STATUS_LABELS = {
    "ATIVA": "Matriculado",
    "TRANCADA": "Trancado",
    "CANCELADA": "Cancelado",
    "CONCLUIDA": "Concluido",
}


def get_user_display_name(user):
    if not user:
        return "-"
    pessoa = getattr(user, "pessoa", None)
    if pessoa and pessoa.nome_completo:
        return pessoa.nome_completo
    full_name = user.get_full_name().strip()
    return full_name or user.username


class EstagioSerializer(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField(read_only=True)
    modalidade_display = serializers.CharField(source="get_modalidade_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    aluno_identificador = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    situacao_estagiario = serializers.SerializerMethodField(read_only=True)
    situacao_matricula_periodo = serializers.SerializerMethodField(read_only=True)
    curso_id = serializers.IntegerField(source="matricula.curso_id", read_only=True)
    curso_nome = serializers.CharField(source="matricula.curso.nome", read_only=True)
    campus_codigo = serializers.SerializerMethodField(read_only=True)
    campus_nome = serializers.CharField(source="matricula.curso.unidade.nome", read_only=True)
    concedente_nome = serializers.SerializerMethodField(read_only=True)
    convenio_id = serializers.IntegerField(source="convenio_id", read_only=True)
    situacao_convenio = serializers.SerializerMethodField(read_only=True)
    professor_orientador = serializers.SerializerMethodField(read_only=True)
    data_prevista_encerramento = serializers.DateField(source="data_fim_prevista", read_only=True)
    data_encerramento = serializers.DateField(source="data_fim_real", read_only=True)
    possui_aditivo = serializers.SerializerMethodField(read_only=True)
    aguardando_assinatura_coordenador = serializers.SerializerMethodField(read_only=True)
    pendencia_relatorio_estagiario = serializers.SerializerMethodField(read_only=True)
    pendencia_relatorio_supervisor = serializers.SerializerMethodField(read_only=True)
    sem_assinatura_relatorios = serializers.SerializerMethodField(read_only=True)
    apto_para_encerramento = serializers.SerializerMethodField(read_only=True)
    aditivos_contratuais = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Estagio
        fields = [
            "id",
            "tipo",
            "modalidade",
            "modalidade_display",
            "status",
            "status_display",
            "aluno_nome",
            "aluno_identificador",
            "situacao_estagiario",
            "situacao_matricula_periodo",
            "curso_id",
            "curso_nome",
            "campus_codigo",
            "campus_nome",
            "convenio_id",
            "concedente_nome",
            "situacao_convenio",
            "professor_orientador",
            "data_inicio",
            "data_prevista_encerramento",
            "data_encerramento",
            "possui_aditivo",
            "aguardando_assinatura_coordenador",
            "pendencia_relatorio_estagiario",
            "pendencia_relatorio_supervisor",
            "sem_assinatura_relatorios",
            "apto_para_encerramento",
            "aditivos_contratuais",
        ]

    def get_tipo(self, obj):
        return "Estagio"

    def get_aluno_nome(self, obj):
        return get_user_display_name(obj.matricula.aluno)

    def get_situacao_estagiario(self, obj):
        return MATRICULA_STATUS_LABELS.get(obj.matricula.status, obj.matricula.get_status_display())

    def get_situacao_matricula_periodo(self, obj):
        return MATRICULA_STATUS_LABELS.get(obj.matricula.status, obj.matricula.get_status_display())

    def get_campus_codigo(self, obj):
        codigo = getattr(obj.matricula.curso.unidade, "codigo", "") or ""
        return codigo.upper()

    def get_concedente_nome(self, obj):
        if obj.convenio_id:
            return obj.convenio.empresa
        return obj.empresa or "-"

    def get_situacao_convenio(self, obj):
        if not obj.convenio_id:
            return "-"
        return obj.convenio.get_status_display()

    def get_professor_orientador(self, obj):
        orientador = obj.orientador_idep
        if not orientador:
            return "-"
        return f"{get_user_display_name(orientador)} ({orientador.username})"

    def get_possui_aditivo(self, obj):
        return obj.termos.filter(status="ADITADO").exists()

    def get_aguardando_assinatura_coordenador(self, obj):
        return obj.termos.filter(status="PENDENTE").exists()

    def get_pendencia_relatorio_estagiario(self, obj):
        return not obj.acompanhamentos.filter(tipo="RELATORIO").exists()

    def get_pendencia_relatorio_supervisor(self, obj):
        return not obj.acompanhamentos.filter(tipo="AVALIACAO").exists()

    def get_sem_assinatura_relatorios(self, obj):
        return obj.termos.filter(status="PENDENTE").exists()

    def get_apto_para_encerramento(self, obj):
        if obj.status != "EM_ANDAMENTO" or not obj.data_fim_prevista:
            return False
        return obj.data_fim_prevista <= date.today()

    def get_aditivos_contratuais(self, obj):
        aditivos = obj.termos.filter(status="ADITADO").order_by("-id")
        if not aditivos.exists():
            return []

        return [
            {
                "id": termo.id,
                "descricao": termo.observacao or "Aditivo contratual registrado.",
                "status": termo.get_status_display(),
            }
            for termo in aditivos[:3]
        ]


class TermoCompromissoDetailSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = TermoCompromisso
        fields = [
            "id",
            "numero_termo",
            "data_assinatura",
            "status",
            "status_display",
            "assinado_aluno",
            "assinado_empresa",
            "assinado_idep",
            "observacao",
        ]


class AcompanhamentoEstagioDetailSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    registrado_por_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AcompanhamentoEstagio
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "data",
            "descricao",
            "registrado_por_nome",
        ]

    def get_registrado_por_nome(self, obj):
        return get_user_display_name(obj.registrado_por)


class EstagioDetailSerializer(EstagioSerializer):
    empresa_local = serializers.CharField(source="empresa", read_only=True)
    supervisor_empresa = serializers.CharField(read_only=True)
    carga_horaria_total = serializers.IntegerField(read_only=True)
    carga_horaria_semanal = serializers.IntegerField(read_only=True)
    bolsa_mensal = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    seguro_numero = serializers.CharField(read_only=True)
    observacao = serializers.CharField(read_only=True)
    turma_nome = serializers.CharField(source="matricula.turma.nome", read_only=True)
    matricula_tipo = serializers.CharField(source="matricula.get_tipo_matricula_display", read_only=True)
    turno = serializers.CharField(source="matricula.get_turno_display", read_only=True)
    convenio_numero = serializers.CharField(source="convenio.numero_convenio", read_only=True)
    convenio_responsavel = serializers.SerializerMethodField(read_only=True)
    termos = TermoCompromissoDetailSerializer(many=True, read_only=True)
    acompanhamentos = AcompanhamentoEstagioDetailSerializer(many=True, read_only=True)

    class Meta(EstagioSerializer.Meta):
        fields = EstagioSerializer.Meta.fields + [
            "empresa_local",
            "supervisor_empresa",
            "carga_horaria_total",
            "carga_horaria_semanal",
            "bolsa_mensal",
            "seguro_numero",
            "observacao",
            "turma_nome",
            "matricula_tipo",
            "turno",
            "convenio_numero",
            "convenio_responsavel",
            "termos",
            "acompanhamentos",
        ]

    def get_convenio_responsavel(self, obj):
        if not obj.convenio_id:
            return "-"
        return get_user_display_name(obj.convenio.responsavel_idep)