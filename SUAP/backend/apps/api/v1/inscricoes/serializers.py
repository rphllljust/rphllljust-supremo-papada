from rest_framework import serializers

from apps.inscricoes.models import (
    Candidato,
    ChamadaProcessoSeletivo,
    ConvocacaoCandidato,
    CotaProcessoSeletivo,
    Inscricao,
    ProcessoSeletivo,
)


class InscricaoSerializer(serializers.ModelSerializer):
    publicacao_titulo = serializers.CharField(source="publicacao.titulo", read_only=True)
    curso_nome = serializers.CharField(source="publicacao.curso.nome", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_candidato_display = serializers.CharField(source="get_status_candidato_display", read_only=True)
    usuario_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Inscricao
        fields = [
            "id",
            "publicacao",
            "publicacao_titulo",
            "curso_nome",
            "nome_candidato",
            "cpf",
            "email",
            "telefone",
            "data_nascimento",
            "status",
            "status_display",
            "modalidade_concorrencia",
            "cota_codigo_opcao",
            "status_candidato",
            "status_candidato_display",
            "data_inscricao",
            "numero_inscricao",
            "observacao",
            "usuario",
            "usuario_nome",
        ]
        read_only_fields = ["data_inscricao", "numero_inscricao", "usuario"]

    def get_usuario_nome(self, obj):
        if not obj.usuario:
            return None

        full_name = obj.usuario.get_full_name().strip()
        return full_name or obj.usuario.username


class ProcessoSeletivoSerializer(serializers.ModelSerializer):
    publicacao_titulo = serializers.CharField(source="publicacao.titulo", read_only=True)
    responsavel_nome = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProcessoSeletivo
        fields = [
            "id",
            "publicacao",
            "publicacao_titulo",
            "modalidade",
            "data_realizacao",
            "data_resultado",
            "status",
            "nota_corte",
            "usa_cotas_lei_12711",
            "criterios",
            "resultado",
            "responsavel",
            "responsavel_nome",
        ]

    def get_responsavel_nome(self, obj):
        if not obj.responsavel:
            return None

        full_name = obj.responsavel.get_full_name().strip()
        return full_name or obj.responsavel.username


class CandidatoSerializer(serializers.ModelSerializer):
    processo_titulo = serializers.CharField(source="processo.publicacao.titulo", read_only=True)
    inscricao_numero = serializers.CharField(source="inscricao.numero_inscricao", read_only=True)
    inscricao_nome = serializers.CharField(source="inscricao.nome_candidato", read_only=True)

    class Meta:
        model = Candidato
        fields = [
            "id",
            "processo",
            "processo_titulo",
            "inscricao",
            "inscricao_numero",
            "inscricao_nome",
            "classificacao",
            "pontuacao",
            "modalidade_vaga",
            "cota_codigo",
            "situacao",
            "chamada_atual",
            "data_convocacao",
            "observacao",
        ]


class CotaProcessoSeletivoSerializer(serializers.ModelSerializer):
    processo_titulo = serializers.CharField(source="processo.publicacao.titulo", read_only=True)

    class Meta:
        model = CotaProcessoSeletivo
        fields = [
            "id",
            "processo",
            "processo_titulo",
            "codigo",
            "nome",
            "percentual_vagas",
            "vagas_reservadas",
            "ordem_remanejamento",
            "ativa",
        ]


class ChamadaProcessoSeletivoSerializer(serializers.ModelSerializer):
    processo_titulo = serializers.CharField(source="processo.publicacao.titulo", read_only=True)

    class Meta:
        model = ChamadaProcessoSeletivo
        fields = [
            "id",
            "processo",
            "processo_titulo",
            "numero",
            "tipo",
            "data_publicacao",
            "prazo_matricula_inicio",
            "prazo_matricula_fim",
            "status",
            "observacao",
        ]


class ConvocacaoCandidatoSerializer(serializers.ModelSerializer):
    chamada_numero = serializers.IntegerField(source="chamada.numero", read_only=True)
    candidato_nome = serializers.CharField(source="candidato.inscricao.nome_candidato", read_only=True)

    class Meta:
        model = ConvocacaoCandidato
        fields = [
            "id",
            "chamada",
            "chamada_numero",
            "candidato",
            "candidato_nome",
            "modalidade_vaga",
            "cota_codigo",
            "classificacao_na_chamada",
            "status",
            "data_status",
            "observacao",
        ]
