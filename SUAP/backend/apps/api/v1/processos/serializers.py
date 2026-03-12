from rest_framework import serializers
from django.utils import timezone

from apps.processos.models import Processo, Tramitacao


class TramitacaoSerializer(serializers.ModelSerializer):
    acao_display = serializers.CharField(source="get_acao_display", read_only=True)
    responsavel_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tramitacao
        fields = [
            "id",
            "acao",
            "acao_display",
            "setor_destino",
            "observacao",
            "data",
            "responsavel_nome",
        ]

    def get_responsavel_nome(self, obj):
        if not obj.responsavel:
            return ""

        if getattr(obj.responsavel, "pessoa", None) and obj.responsavel.pessoa.nome_completo:
            return obj.responsavel.pessoa.nome_completo

        full_name = obj.responsavel.get_full_name().strip()
        return full_name or obj.responsavel.username


class ProcessoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    requerente_nome = serializers.SerializerMethodField(read_only=True)
    tramitacoes = TramitacaoSerializer(many=True, read_only=True)

    class Meta:
        model = Processo
        fields = [
            "id",
            "numero",
            "tipo",
            "tipo_display",
            "assunto",
            "descricao",
            "status",
            "status_display",
            "data_abertura",
            "data_conclusao",
            "requerente",
            "requerente_nome",
            "tramitacoes",
        ]
        read_only_fields = ["numero", "data_abertura"]

    def get_requerente_nome(self, obj):
        if not obj.requerente:
            return ""

        if getattr(obj.requerente, "pessoa", None) and obj.requerente.pessoa.nome_completo:
            return obj.requerente.pessoa.nome_completo

        full_name = obj.requerente.get_full_name().strip()
        return full_name or obj.requerente.username


class TramitarProcessoSerializer(serializers.Serializer):
    acao = serializers.ChoiceField(choices=Tramitacao.ACAO_CHOICES)
    setor_destino = serializers.CharField(max_length=100, allow_blank=True, required=False)
    observacao = serializers.CharField(allow_blank=True, required=False)

    def save(self, **kwargs):
        processo = self.context["processo"]
        responsavel = self.context.get("responsavel")

        tramitacao = Tramitacao.objects.create(
            processo=processo,
            responsavel=responsavel,
            acao=self.validated_data["acao"],
            setor_destino=self.validated_data.get("setor_destino", ""),
            observacao=self.validated_data.get("observacao", ""),
        )

        acao = tramitacao.acao
        if acao == "ARQUIVADO":
            processo.status = "ARQUIVADO"
            processo.data_conclusao = timezone.localdate()
        elif acao == "RESPONDIDO":
            processo.status = "CONCLUIDO"
            processo.data_conclusao = timezone.localdate()
        elif acao in {"ENCAMINHADO", "RECEBIDO", "DEVOLVIDO"}:
            processo.status = "EM_TRAMITACAO"
            processo.data_conclusao = None

        processo.save()
        return tramitacao