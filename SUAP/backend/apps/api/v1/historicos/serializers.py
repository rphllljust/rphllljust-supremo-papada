from rest_framework import serializers

from apps.documentos.models import HistoricoEscolarEvento, HistoricoEscolarItem, HistoricoEscolarTecnicoDocumento


class HistoricoEscolarItemSerializer(serializers.ModelSerializer):
    resultado_display = serializers.CharField(source="get_resultado_display", read_only=True)

    class Meta:
        model = HistoricoEscolarItem
        fields = [
            "id",
            "componente_curricular",
            "componente_nome",
            "modulo_periodo",
            "carga_horaria",
            "nota",
            "frequencia",
            "resultado",
            "resultado_display",
            "ordem_exibicao",
        ]


class HistoricoEscolarEventoSerializer(serializers.ModelSerializer):
    tipo_evento_display = serializers.CharField(source="get_tipo_evento_display", read_only=True)
    usuario_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HistoricoEscolarEvento
        fields = [
            "id",
            "tipo_evento",
            "tipo_evento_display",
            "descricao",
            "motivo",
            "usuario",
            "usuario_nome",
            "ip_address",
            "criado_em",
        ]

    def get_usuario_nome(self, obj):
        usuario = obj.usuario
        if not usuario:
            return ""
        pessoa = getattr(usuario, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return usuario.get_full_name().strip() or usuario.username


class HistoricoEscolarTecnicoDocumentoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    situacao_final_display = serializers.CharField(source="get_situacao_final_display", read_only=True)
    aluno_nome = serializers.SerializerMethodField(read_only=True)
    cpf_aluno = serializers.SerializerMethodField(read_only=True)
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    eixo_tecnologico = serializers.CharField(source="curso.eixo_tecnologico", read_only=True)
    matricula_numero = serializers.CharField(source="matricula.numero_matricula", read_only=True)
    emitido_por_nome = serializers.SerializerMethodField(read_only=True)
    pdf_url = serializers.SerializerMethodField(read_only=True)
    qrcode_url = serializers.SerializerMethodField(read_only=True)
    itens = HistoricoEscolarItemSerializer(many=True, read_only=True)
    eventos = HistoricoEscolarEventoSerializer(many=True, read_only=True)
    hash_resumido = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HistoricoEscolarTecnicoDocumento
        fields = [
            "id",
            "uuid",
            "aluno",
            "aluno_nome",
            "cpf_aluno",
            "matricula",
            "matricula_numero",
            "curso",
            "curso_nome",
            "eixo_tecnologico",
            "numero_registro",
            "livro",
            "folha",
            "pagina",
            "versao",
            "status",
            "status_display",
            "hash_documento",
            "hash_resumido",
            "codigo_validacao",
            "data_emissao",
            "data_cancelamento",
            "motivo_cancelamento",
            "historico_substituido",
            "emitido_por",
            "emitido_por_nome",
            "observacoes",
            "pdf_url",
            "qrcode_url",
            "carga_horaria_total",
            "situacao_final",
            "situacao_final_display",
            "data_conclusao",
            "criado_em",
            "atualizado_em",
            "itens",
            "eventos",
        ]
        read_only_fields = fields

    def get_aluno_nome(self, obj):
        aluno = obj.aluno
        pessoa = getattr(aluno, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return aluno.get_full_name().strip() or aluno.username

    def get_cpf_aluno(self, obj):
        return obj.aluno.cpf

    def get_emitido_por_nome(self, obj):
        usuario = obj.emitido_por
        if not usuario:
            return ""
        pessoa = getattr(usuario, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return usuario.get_full_name().strip() or usuario.username

    def get_pdf_url(self, obj):
        if not obj.pdf_arquivo:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.pdf_arquivo.url)
        return obj.pdf_arquivo.url

    def get_qrcode_url(self, obj):
        if not obj.qrcode_imagem:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.qrcode_imagem.url)
        return obj.qrcode_imagem.url

    def get_hash_resumido(self, obj):
        if not obj.hash_documento:
            return ""
        return obj.hash_documento[:16]


class EmitirHistoricoSerializer(serializers.Serializer):
    matricula_id = serializers.IntegerField(required=False)
    aluno_id = serializers.IntegerField(required=False)
    observacoes = serializers.CharField(required=False, allow_blank=True)
    livro = serializers.CharField(required=False, allow_blank=True, max_length=30)
    folha = serializers.CharField(required=False, allow_blank=True, max_length=30)
    pagina = serializers.CharField(required=False, allow_blank=True, max_length=30)

    def validate(self, attrs):
        if not attrs.get("matricula_id") and not attrs.get("aluno_id"):
            raise serializers.ValidationError("Informe matricula_id ou aluno_id para emissao.")
        return attrs


class ReemitirHistoricoSerializer(serializers.Serializer):
    motivo = serializers.CharField(min_length=3, max_length=500)


class CancelarHistoricoSerializer(serializers.Serializer):
    motivo = serializers.CharField(min_length=3, max_length=500)


class HistoricoPreviewSerializer(serializers.Serializer):
    matricula_id = serializers.IntegerField(required=False)
    aluno_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if not attrs.get("matricula_id") and not attrs.get("aluno_id"):
            raise serializers.ValidationError("Informe matricula_id ou aluno_id para preview.")
        return attrs
