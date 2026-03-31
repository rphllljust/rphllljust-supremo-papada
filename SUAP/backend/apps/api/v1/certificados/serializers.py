from django.utils import timezone
from rest_framework import serializers

from apps.certificados.models import (
    AssinaturaCertificado,
    CertificadoEmitido,
    ConfiguracaoVisualCertificado,
    HistoricoEmissaoCertificado,
    ModeloCertificado,
)
from apps.usuarios.models import PerfilUsuario


ALLOWED_STATUS_TRANSITIONS = {
    "DIPLOMA_EM_PREPARACAO": {"DIPLOMA_REGISTRADO", "CERTIFICADO_CANCELADO"},
    "DIPLOMA_REGISTRADO": {"DIPLOMA_DISPONIVEL_RETIRADA", "CERTIFICADO_CANCELADO"},
    "DIPLOMA_DISPONIVEL_RETIRADA": {"DIPLOMA_ENTREGUE", "CERTIFICADO_CANCELADO"},
    "DIPLOMA_ENTREGUE": {"CERTIFICADO_CANCELADO"},
    "CERTIFICADO_CANCELADO": set(),
}


class AssinaturaCertificadoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = AssinaturaCertificado
        fields = [
            "id",
            "modelo",
            "nome",
            "cargo",
            "imagem_assinatura",
            "ordem",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]


class ConfiguracaoVisualCertificadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoVisualCertificado
        fields = [
            "id",
            "modelo",
            "nome_da_instituicao",
            "sigla_instituicao",
            "brasao_instituicao",
            "logo_instituicao",
            "logos_rodape",
            "marca_dagua",
            "cidade_padrao",
            "estado_padrao",
            "cor_primaria",
            "cor_secundaria",
            "cor_destaque",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]


class ModeloCertificadoSerializer(serializers.ModelSerializer):
    assinaturas = AssinaturaCertificadoSerializer(many=True, required=False)
    configuracao_visual = ConfiguracaoVisualCertificadoSerializer(required=False, allow_null=True)
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)

    class Meta:
        model = ModeloCertificado
        fields = [
            "id",
            "nome",
            "slug",
            "descricao",
            "tipo",
            "curso",
            "curso_nome",
            "unidade",
            "unidade_nome",
            "template_html",
            "stylesheet_css",
            "texto_certificado",
            "campos_dinamicos",
            "metadados",
            "ativo",
            "assinaturas",
            "configuracao_visual",
            "criado_por",
            "atualizado_por",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "slug",
            "criado_por",
            "atualizado_por",
            "criado_em",
            "atualizado_em",
        ]

    def _upsert_assinaturas(self, modelo, assinaturas):
        if assinaturas is None:
            return
        ids_recebidos = []
        for assinatura_data in assinaturas:
            assinatura_id = assinatura_data.get("id")
            assinatura_data = {**assinatura_data, "modelo": modelo}
            if assinatura_id:
                assinatura = AssinaturaCertificado.objects.filter(id=assinatura_id, modelo=modelo).first()
                if assinatura:
                    for key, value in assinatura_data.items():
                        setattr(assinatura, key, value)
                    assinatura.save()
                    ids_recebidos.append(assinatura.id)
                    continue
            nova = AssinaturaCertificado.objects.create(**assinatura_data)
            ids_recebidos.append(nova.id)

        AssinaturaCertificado.objects.filter(modelo=modelo).exclude(id__in=ids_recebidos).delete()

    def _upsert_configuracao(self, modelo, configuracao):
        if configuracao is None:
            return
        ConfiguracaoVisualCertificado.objects.update_or_create(
            modelo=modelo,
            defaults=configuracao,
        )

    def create(self, validated_data):
        assinaturas = validated_data.pop("assinaturas", None)
        configuracao = validated_data.pop("configuracao_visual", None)
        request = self.context.get("request")
        if request and getattr(request, "user", None):
            validated_data["criado_por"] = request.user
            validated_data["atualizado_por"] = request.user
        modelo = super().create(validated_data)
        self._upsert_assinaturas(modelo, assinaturas)
        self._upsert_configuracao(modelo, configuracao)
        return modelo

    def update(self, instance, validated_data):
        assinaturas = validated_data.pop("assinaturas", None)
        configuracao = validated_data.pop("configuracao_visual", None)
        request = self.context.get("request")
        if request and getattr(request, "user", None):
            validated_data["atualizado_por"] = request.user
        instance = super().update(instance, validated_data)
        self._upsert_assinaturas(instance, assinaturas)
        self._upsert_configuracao(instance, configuracao)
        return instance


class CertificadoEmitidoSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_documento_display = serializers.CharField(source="get_status_documento_display", read_only=True)
    tipo_documento_display = serializers.CharField(source="get_tipo_documento_display", read_only=True)
    modelo_nome = serializers.CharField(source="modelo.nome", read_only=True)
    aluno_nome = serializers.CharField(source="nome_aluno_snapshot", read_only=True)
    curso_nome = serializers.CharField(source="curso_nome_snapshot", read_only=True)
    unidade_nome = serializers.CharField(source="unidade.nome", read_only=True)
    usuario_emissor_nome = serializers.SerializerMethodField(read_only=True)
    pdf_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CertificadoEmitido
        fields = [
            "id",
            "modelo",
            "modelo_nome",
            "aluno",
            "matricula",
            "curso",
            "turma",
            "unidade",
            "unidade_nome",
            "usuario_emissor",
            "usuario_emissor_nome",
            "tipo_documento",
            "tipo_documento_display",
            "numero_certificado",
            "numero_registro",
            "livro",
            "folha",
            "pagina",
            "termo",
            "codigo_validacao",
            "hash_integridade",
            "url_validacao",
            "qr_code_validacao",
            "qr_code_image",
            "qr_code_data_uri",
            "status",
            "status_display",
            "status_documento",
            "status_documento_display",
            "data_inicio",
            "data_fim",
            "data_conclusao",
            "data_emissao",
            "data_registro",
            "data_entrega",
            "cidade",
            "estado",
            "observacoes",
            "aluno_nome",
            "curso_nome",
            "cpf_aluno_snapshot",
            "texto_certificado_snapshot",
            "dados_dinamicos",
            "reemitido_de",
            "reimpressoes",
            "ultima_reimpressao_em",
            "pdf_arquivo",
            "pdf_url",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "numero_certificado",
            "numero_registro",
            "codigo_validacao",
            "hash_integridade",
            "url_validacao",
            "qr_code_validacao",
            "qr_code_image",
            "qr_code_data_uri",
            "usuario_emissor",
            "reimpressoes",
            "ultima_reimpressao_em",
            "pdf_arquivo",
            "pdf_url",
            "criado_em",
            "atualizado_em",
        ]

    def get_usuario_emissor_nome(self, obj):
        usuario = getattr(obj, "usuario_emissor", None)
        if not usuario:
            return ""
        pessoa = getattr(usuario, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return (usuario.get_full_name() or "").strip() or usuario.username

    def get_pdf_url(self, obj):
        if not obj.pdf_arquivo:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.pdf_arquivo.url)
        return obj.pdf_arquivo.url

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if not instance:
            return attrs

        status_novo = attrs.get("status")
        status_atual = instance.status
        if not status_novo or status_novo == status_atual:
            return attrs

        permitidos = ALLOWED_STATUS_TRANSITIONS.get(status_atual, set())
        if status_novo not in permitidos:
            raise serializers.ValidationError(
                {
                    "status": (
                        f"Transicao de status invalida: {status_atual} -> {status_novo}. "
                        "Fluxo permitido: preparo -> registrado -> disponivel para retirada -> entregue."
                    )
                }
            )

        request = self.context.get("request")
        if request and getattr(request, "user", None):
            perfil = getattr(request.user, "tipo", "")
            if perfil not in {PerfilUsuario.SECRETARIA, PerfilUsuario.ADMIN}:
                raise serializers.ValidationError(
                    {"status": "Somente usuarios da secretaria ou administradores podem alterar o status."}
                )

        return attrs

    def update(self, instance, validated_data):
        status_novo = validated_data.get("status")
        if status_novo and status_novo != instance.status:
            if status_novo == "DIPLOMA_REGISTRADO" and not validated_data.get("data_registro"):
                validated_data["data_registro"] = timezone.localdate()
            if status_novo == "DIPLOMA_ENTREGUE" and not validated_data.get("data_entrega"):
                validated_data["data_entrega"] = timezone.localdate()

        return super().update(instance, validated_data)


class EmitirCertificadoSerializer(serializers.Serializer):
    modelo_id = serializers.IntegerField()
    matricula_id = serializers.IntegerField(required=False)
    turma_id = serializers.IntegerField(required=False)
    tipo_documento = serializers.ChoiceField(choices=CertificadoEmitido.TIPO_DOCUMENTO_CHOICES, default="DIPLOMA")
    sobrescritas = serializers.JSONField(required=False)
    gerar_pdf = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if not attrs.get("matricula_id") and not attrs.get("turma_id"):
            raise serializers.ValidationError("Informe matricula_id para emissão individual ou turma_id para emissão em lote.")
        return attrs


class PreviewRascunhoCertificadoSerializer(serializers.Serializer):
    modelo_id = serializers.IntegerField()
    matricula_id = serializers.IntegerField(required=False)
    tipo_documento = serializers.ChoiceField(choices=CertificadoEmitido.TIPO_DOCUMENTO_CHOICES, default="DIPLOMA")
    sobrescritas = serializers.JSONField(required=False)


class HistoricoEmissaoCertificadoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.SerializerMethodField(read_only=True)
    numero_certificado = serializers.CharField(source="certificado.numero_certificado", read_only=True)
    modelo_nome = serializers.CharField(source="modelo.nome", read_only=True)
    acao_display = serializers.CharField(source="get_acao_display", read_only=True)

    class Meta:
        model = HistoricoEmissaoCertificado
        fields = [
            "id",
            "certificado",
            "numero_certificado",
            "modelo",
            "modelo_nome",
            "usuario",
            "usuario_nome",
            "acao",
            "acao_display",
            "descricao",
            "dados",
            "ip_origem",
            "criado_em",
        ]

    def get_usuario_nome(self, obj):
        usuario = getattr(obj, "usuario", None)
        if not usuario:
            return ""
        pessoa = getattr(usuario, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return (usuario.get_full_name() or "").strip() or usuario.username
