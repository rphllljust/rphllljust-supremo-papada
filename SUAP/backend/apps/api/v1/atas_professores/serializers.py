import json

from rest_framework import serializers

from apps.documentos.models import AtaAnexo, AtaOficioMemorando


class AtaAnexoSerializer(serializers.ModelSerializer):
    tipo_label = serializers.CharField(source="get_tipo_anexo_display", read_only=True)
    arquivo_nome = serializers.SerializerMethodField(read_only=True)
    arquivo_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AtaAnexo
        fields = ["id", "tipo_anexo", "tipo_label", "descricao", "arquivo_nome", "arquivo_url"]

    def get_arquivo_nome(self, obj):
        if not obj.arquivo:
            return ""
        return obj.arquivo.name.split("/")[-1]

    def get_arquivo_url(self, obj):
        if not obj.arquivo:
            return ""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.arquivo.url)
        return obj.arquivo.url


class AtaProfessoresSerializer(serializers.ModelSerializer):
    tipo_reuniao_label = serializers.SerializerMethodField(read_only=True)
    modalidade_label = serializers.CharField(source="get_modalidade_display", read_only=True)
    situacao_label = serializers.CharField(source="get_situacao_display", read_only=True)
    emitido_por_nome = serializers.SerializerMethodField(read_only=True)
    processo = serializers.PrimaryKeyRelatedField(queryset=__import__("apps.processos.models", fromlist=["Processo"]).Processo.objects.all(), required=False, allow_null=True)
    processo_numero = serializers.CharField(source="processo.numero", read_only=True)
    participantes_count = serializers.SerializerMethodField(read_only=True)
    anexos = AtaAnexoSerializer(source="anexos_upload", many=True, read_only=True)
    acao = serializers.CharField(write_only=True, required=False, allow_blank=True)
    participantes = serializers.JSONField(required=False)
    pauta = serializers.JSONField(required=False)
    deliberacoes = serializers.JSONField(required=False)
    encaminhamentos = serializers.JSONField(required=False)
    assinaturas = serializers.JSONField(required=False)
    anexos_metadata = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = AtaOficioMemorando
        fields = [
            "id",
            "numero_ata",
            "numero_protocolo",
            "assunto",
            "data_emissao",
            "data_reuniao",
            "tipo_reuniao_registro",
            "tipo_reuniao_label",
            "modalidade",
            "modalidade_label",
            "local_reuniao",
            "plataforma",
            "link_reuniao",
            "cidade_uf",
            "livro",
            "folha_pagina",
            "ano",
            "presidente_reuniao",
            "responsavel_lavratura",
            "horario_inicio",
            "horario_termino",
            "horario_encerramento",
            "texto_final",
            "forma_assinatura",
            "tipo_reuniao_outro",
            "processo",
            "situacao",
            "situacao_label",
            "emitido_por_nome",
            "processo_numero",
            "participantes_count",
            "participantes",
            "pauta",
            "deliberacoes",
            "encaminhamentos",
            "assinaturas",
            "anexos",
            "anexos_metadata",
            "acao",
            "observacao",
        ]

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()

        for field_name in ["participantes", "pauta", "deliberacoes", "encaminhamentos", "assinaturas", "anexos_metadata"]:
            raw_value = data.get(field_name)
            if isinstance(raw_value, str) and raw_value:
                try:
                    data[field_name] = json.loads(raw_value)
                except json.JSONDecodeError as exc:
                    raise serializers.ValidationError({field_name: "JSON invalido."}) from exc

        return super().to_internal_value(data)

    def get_tipo_reuniao_label(self, obj):
        if obj.tipo_reuniao_registro == "OUTRO" and obj.tipo_reuniao_outro:
            return obj.tipo_reuniao_outro
        return obj.get_tipo_reuniao_registro_display() or "Nao informado"

    def get_emitido_por_nome(self, obj):
        if not obj.emitido_por:
            return ""

        if getattr(obj.emitido_por, "pessoa", None) and obj.emitido_por.pessoa.nome_completo:
            return obj.emitido_por.pessoa.nome_completo

        full_name = obj.emitido_por.get_full_name().strip()
        return full_name or obj.emitido_por.username

    def get_participantes_count(self, obj):
        return len(obj.participantes or [])

    def validate(self, attrs):
        acao = (attrs.get("acao") or "rascunho").strip().lower()
        participantes = attrs.get("participantes") or []
        pauta = attrs.get("pauta") or []
        deliberacoes = attrs.get("deliberacoes") or []
        assinaturas = attrs.get("assinaturas") or []
        modalidade = attrs.get("modalidade") or getattr(self.instance, "modalidade", "")
        plataforma = (attrs.get("plataforma") or getattr(self.instance, "plataforma", "") or "").strip()
        tipo_reuniao = attrs.get("tipo_reuniao_registro") or getattr(self.instance, "tipo_reuniao_registro", "")
        tipo_outro = (attrs.get("tipo_reuniao_outro") or getattr(self.instance, "tipo_reuniao_outro", "") or "").strip()
        horario_inicio = attrs.get("horario_inicio") or getattr(self.instance, "horario_inicio", None)
        horario_termino = attrs.get("horario_termino") or getattr(self.instance, "horario_termino", None)
        horario_encerramento = attrs.get("horario_encerramento") or getattr(self.instance, "horario_encerramento", None)

        if horario_inicio and horario_termino and horario_termino < horario_inicio:
            raise serializers.ValidationError({"horario_termino": "O horario de termino nao pode ser menor que o horario de inicio."})

        if horario_inicio and horario_encerramento and horario_encerramento < horario_inicio:
            raise serializers.ValidationError({"horario_encerramento": "O horario de encerramento nao pode ser menor que o horario de inicio."})

        if modalidade in {"ONLINE", "HIBRIDA"} and not plataforma:
            raise serializers.ValidationError({"plataforma": "Informe a plataforma para reunioes online ou hibridas."})

        if tipo_reuniao == "OUTRO" and not tipo_outro:
            raise serializers.ValidationError({"tipo_reuniao_outro": "Informe o tipo de reuniao quando selecionar 'Outro'."})

        if acao == "emitir":
            campos_obrigatorios = [
                "numero_ata",
                "ano",
                "tipo_reuniao_registro",
                "data_reuniao",
                "horario_inicio",
                "local_reuniao",
                "modalidade",
                "cidade_uf",
                "presidente_reuniao",
                "responsavel_lavratura",
            ]
            errors = {}
            for campo in campos_obrigatorios:
                valor = attrs.get(campo)
                if valor in (None, "") and not getattr(self.instance, campo, None):
                    errors[campo] = "Campo obrigatorio para emissao da ata."
            if not participantes:
                errors["participantes"] = "Adicione ao menos um participante."
            if not pauta:
                errors["pauta"] = "Adicione ao menos um item de pauta."
            if not deliberacoes:
                errors["deliberacoes"] = "Informe pelo menos uma deliberacao."
            if not assinaturas:
                errors["assinaturas"] = "Inclua ao menos uma assinatura."
            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    def _save_anexos(self, instance, anexos_metadata):
        request = self.context.get("request")
        files = getattr(request, "FILES", None)
        existentes = {anexo.id: anexo for anexo in instance.anexos_upload.all()}
        mantidos = set()

        for index, anexo in enumerate(anexos_metadata or []):
            anexo_id = anexo.get("id")
            tipo = (anexo.get("tipo") or "OUTROS").strip() or "OUTROS"
            descricao = (anexo.get("descricao") or "").strip()
            arquivo = files.get(f"anexo_arquivo_{index}") if files else None

            if anexo_id and anexo_id in existentes:
                atual = existentes[anexo_id]
                atual.tipo_anexo = tipo
                atual.descricao = descricao
                if arquivo is not None:
                    atual.arquivo = arquivo
                atual.save()
                mantidos.add(atual.id)
                continue

            criado = AtaAnexo.objects.create(
                ata=instance,
                tipo_anexo=tipo,
                descricao=descricao,
                arquivo=arquivo,
            )
            mantidos.add(criado.id)

        for anexo_id, anexo in existentes.items():
            if anexo_id not in mantidos:
                anexo.delete()

    def _apply_emit_rules(self, instance, acao):
        if acao == "emitir":
            instance.emitir()
        else:
            instance.tipo = "ATA"
            instance.situacao = "RASCUNHO"
            if not instance.texto_final:
                instance.texto_final = (
                    "Nada mais havendo a tratar, deu-se por encerrada a reuniao. "
                    "Eu, [responsavel], lavrei a presente ata, que apos lida e aprovada, "
                    "segue assinada eletronicamente pelos participantes."
                )

    def create(self, validated_data):
        anexos_metadata = validated_data.pop("anexos_metadata", [])
        acao = (validated_data.pop("acao", "rascunho") or "rascunho").strip().lower()
        request = self.context["request"]
        instance = AtaOficioMemorando(**validated_data)
        instance.emitido_por = request.user
        self._apply_emit_rules(instance, acao)
        instance.save()
        self._save_anexos(instance, anexos_metadata)
        return instance

    def update(self, instance, validated_data):
        if instance.situacao == "EMITIDO":
            raise serializers.ValidationError({"detail": "Esta ata ja foi emitida e esta em modo somente leitura."})

        anexos_metadata = validated_data.pop("anexos_metadata", None)
        acao = (validated_data.pop("acao", "rascunho") or "rascunho").strip().lower()

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.emitido_por = self.context["request"].user
        self._apply_emit_rules(instance, acao)
        instance.save()

        if anexos_metadata is not None:
            self._save_anexos(instance, anexos_metadata)

        return instance