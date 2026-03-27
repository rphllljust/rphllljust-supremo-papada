from rest_framework import serializers

from apps.matriculas.models import AproveitamentoComponente, CertificadoDiploma, DependenciaAcademica


class VidaAcademicaSnapshotSerializer(serializers.Serializer):
    matricula_id = serializers.IntegerField()
    matricula_aluno = serializers.CharField()
    aluno_nome = serializers.CharField()
    disciplina = serializers.CharField(allow_blank=True)
    nota = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    frequencia = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    situacao = serializers.CharField()
    periodo = serializers.CharField()
    turma = serializers.CharField()
    professor = serializers.CharField(allow_blank=True)
    curso = serializers.CharField()
    status_matricula = serializers.CharField()
    transferencias = serializers.IntegerField()
    aproveitamentos = serializers.IntegerField()
    dependencias_ativas = serializers.IntegerField()


class DependenciaAcademicaSerializer(serializers.ModelSerializer):
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    curso_nome = serializers.CharField(source="matricula.curso.nome", read_only=True)
    turma_nome = serializers.CharField(source="matricula.turma.nome", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    motivo_display = serializers.CharField(source="get_motivo_display", read_only=True)

    class Meta:
        model = DependenciaAcademica
        fields = [
            "id",
            "matricula",
            "matricula_numero",
            "aluno_nome",
            "curso_nome",
            "turma_nome",
            "componente",
            "periodo_referencia",
            "motivo",
            "motivo_display",
            "nota_obtida",
            "frequencia_percentual",
            "status",
            "status_display",
            "data_registro",
            "data_resolucao",
            "observacao",
        ]
        read_only_fields = ["data_registro"]

    def get_aluno_nome(self, obj):
        aluno = obj.matricula.aluno
        if getattr(aluno, "pessoa", None) and aluno.pessoa.nome_completo:
            return aluno.pessoa.nome_completo
        full_name = aluno.get_full_name().strip()
        return full_name or aluno.username


class AproveitamentoEstudosSerializer(serializers.ModelSerializer):
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    decisao_por_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AproveitamentoComponente
        fields = [
            "id",
            "matricula",
            "matricula_numero",
            "aluno_nome",
            "componente_origem",
            "instituicao_origem",
            "carga_horaria",
            "componente_destino",
            "status",
            "status_display",
            "data_solicitacao",
            "data_decisao",
            "decisao_por",
            "decisao_por_nome",
            "justificativa",
        ]
        read_only_fields = ["data_solicitacao"]

    def get_aluno_nome(self, obj):
        aluno = obj.matricula.aluno
        if getattr(aluno, "pessoa", None) and aluno.pessoa.nome_completo:
            return aluno.pessoa.nome_completo
        full_name = aluno.get_full_name().strip()
        return full_name or aluno.username

    def get_decisao_por_nome(self, obj):
        if not obj.decisao_por:
            return None
        full_name = obj.decisao_por.get_full_name().strip()
        return full_name or obj.decisao_por.username


class AgendaAcademicaItemSerializer(serializers.Serializer):
    tipo = serializers.CharField()
    titulo = serializers.CharField()
    descricao = serializers.CharField(allow_blank=True)
    periodo = serializers.CharField()
    data_inicio = serializers.DateTimeField()
    data_fim = serializers.DateTimeField()
    curso = serializers.CharField(allow_blank=True)
    turma = serializers.CharField(allow_blank=True)
    professor = serializers.CharField(allow_blank=True)
    origem = serializers.CharField()


class CertificadoDiplomaSerializer(serializers.ModelSerializer):
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    emitido_por_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CertificadoDiploma
        fields = [
            "id",
            "matricula",
            "matricula_numero",
            "aluno_nome",
            "tipo",
            "tipo_display",
            "numero_registro",
            "data_emissao",
            "data_entrega",
            "status",
            "status_display",
            "emitido_por",
            "emitido_por_nome",
            "observacao",
        ]
        read_only_fields = ["numero_registro"]

    def get_aluno_nome(self, obj):
        aluno = obj.matricula.aluno
        if getattr(aluno, "pessoa", None) and aluno.pessoa.nome_completo:
            return aluno.pessoa.nome_completo
        full_name = aluno.get_full_name().strip()
        return full_name or aluno.username

    def get_emitido_por_nome(self, obj):
        if not obj.emitido_por:
            return None
        full_name = obj.emitido_por.get_full_name().strip()
        return full_name or obj.emitido_por.username
