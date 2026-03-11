from rest_framework import serializers

from apps.usuarios.models import (
    DocumentoPessoal,
    Endereco,
    ServidorFerias,
    ServidorHistoricoFuncional,
    ServidorOcorrenciaAfastamento,
    ServidorPerfil,
    ServidorSetorHistorico,
)


class ServidorOcorrenciaAfastamentoSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)

    class Meta:
        model = ServidorOcorrenciaAfastamento
        fields = ["id", "titulo", "tipo", "tipo_display", "situacao", "situacao_display", "data_inicio", "data_fim", "descricao"]


class ServidorSetorHistoricoSerializer(serializers.ModelSerializer):
    setor_nome = serializers.CharField(source="setor.nome", read_only=True)
    setor_sigla = serializers.CharField(source="setor.sigla", read_only=True)
    setor_codigo = serializers.CharField(source="setor.codigo", read_only=True)

    class Meta:
        model = ServidorSetorHistorico
        fields = ["id", "setor", "setor_nome", "setor_sigla", "setor_codigo", "tipo_vinculo", "principal", "data_inicio", "data_fim", "observacao"]


class ServidorHistoricoFuncionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServidorHistoricoFuncional
        fields = ["id", "titulo", "tipo_evento", "data_evento", "descricao"]


class ServidorFeriasSerializer(serializers.ModelSerializer):
    situacao_display = serializers.CharField(source="get_situacao_display", read_only=True)

    class Meta:
        model = ServidorFerias
        fields = ["id", "exercicio", "periodo_inicio", "periodo_fim", "situacao", "situacao_display", "observacao"]


class ServidorProfileSerializer(serializers.ModelSerializer):
    nome_registro = serializers.SerializerMethodField(read_only=True)
    cpf = serializers.CharField(source="usuario.cpf", read_only=True)
    ativo = serializers.BooleanField(source="usuario.is_active", read_only=True)
    username = serializers.CharField(source="usuario.username", read_only=True)
    perfil = serializers.CharField(source="usuario.tipo", read_only=True)
    perfil_display = serializers.CharField(source="usuario.get_tipo_display", read_only=True)
    setor_atual_nome = serializers.CharField(source="usuario.setor.nome", read_only=True)
    ultimo_login = serializers.DateTimeField(source="usuario.last_login", read_only=True)
    data_registro = serializers.DateTimeField(source="usuario.date_joined", read_only=True)
    nascimento = serializers.DateField(source="usuario.pessoa.data_nascimento", read_only=True)
    endereco = serializers.SerializerMethodField(read_only=True)
    ocorrencias_afastamentos = ServidorOcorrenciaAfastamentoSerializer(many=True, read_only=True)
    setores = ServidorSetorHistoricoSerializer(source="setores_historico", many=True, read_only=True)
    historico_funcional = ServidorHistoricoFuncionalSerializer(many=True, read_only=True)
    ferias = ServidorFeriasSerializer(many=True, read_only=True)
    posicao = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ServidorPerfil
        fields = [
            "id",
            "usuario",
            "matricula_servidor",
            "nome_usual",
            "nome_registro",
            "cpf",
            "ativo",
            "nao_tem_impressao_digital",
            "username",
            "perfil",
            "perfil_display",
            "ultimo_login",
            "data_registro",
            "email_institucional",
            "email_siape",
            "email_secundario_recuperacao",
            "email_notificacoes",
            "email_google_sala",
            "telefones_institucionais",
            "telefones_pessoais",
            "em_pgd",
            "nascimento",
            "estado_civil",
            "naturalidade",
            "sexo",
            "grupo_sanguineo_rh",
            "dependentes_ir",
            "raca_etnia",
            "nome_pai",
            "nome_mae",
            "pis_pasep",
            "titulacao",
            "escolaridade",
            "endereco",
            "identidade",
            "orgao_expedidor",
            "uf_rg",
            "data_expedicao",
            "titulo_eleitor_numero",
            "titulo_eleitor_zona",
            "titulo_eleitor_secao",
            "titulo_eleitor_uf",
            "setor_atual_nome",
            "ocorrencias_afastamentos",
            "setores",
            "historico_funcional",
            "ferias",
            "posicao",
        ]

    def get_nome_registro(self, obj):
        pessoa = getattr(obj.usuario, "pessoa", None)
        if pessoa and pessoa.nome_completo:
            return pessoa.nome_completo
        return obj.usuario.get_full_name().strip() or obj.usuario.username

    def get_endereco(self, obj):
        pessoa = getattr(obj.usuario, "pessoa", None)
        if not pessoa:
            return None
        endereco = pessoa.enderecos.order_by("-principal", "id").first()
        if not endereco:
            return None
        return {
            "cep": endereco.cep,
            "logradouro": endereco.logradouro,
            "numero": endereco.numero,
            "complemento": endereco.complemento,
            "bairro": endereco.bairro,
            "municipio": endereco.municipio,
            "uf": endereco.uf,
            "descricao": f"{endereco.logradouro}, {endereco.numero} - {endereco.bairro}, {endereco.municipio}/{endereco.uf}",
        }

    def get_posicao(self, obj):
        return {
            "posicao_atual": obj.posicao_atual,
            "cargo_atual": obj.cargo_atual or obj.usuario.get_tipo_display(),
            "jornada_trabalho": obj.jornada_trabalho,
            "classe_funcional": obj.classe_funcional,
            "nivel_funcional": obj.nivel_funcional,
            "setor_atual": getattr(obj.usuario.setor, "nome", ""),
        }