from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.setores.models import Setor
from apps.usuarios.models import PerfilUsuario, Pessoa, ServidorPerfil
from apps.usuarios.profile_compat import get_matricula_servidor_safe


Usuario = get_user_model()

PROFILE_FIELD_NAMES = [
    "matricula_servidor",
    "nome_usual",
    "email_institucional",
    "email_siape",
    "email_secundario_recuperacao",
    "email_notificacoes",
    "email_google_sala",
    "telefones_institucionais",
    "telefones_pessoais",
    "em_pgd",
    "nao_tem_impressao_digital",
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
    "identidade",
    "orgao_expedidor",
    "uf_rg",
    "data_expedicao",
    "titulo_eleitor_numero",
    "titulo_eleitor_zona",
    "titulo_eleitor_secao",
    "titulo_eleitor_uf",
    "posicao_atual",
    "cargo_atual",
    "regime_trabalho",
    "jornada_trabalho",
    "classe_funcional",
    "nivel_funcional",
    "banco",
    "agencia",
    "conta_corrente",
]


class ProfileValueMixin:
    def __init__(self, *args, profile_attr=None, **kwargs):
        self.profile_attr = profile_attr
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        perfil = getattr(instance, "perfil_servidor", None)
        if not perfil:
            return None
        return getattr(perfil, self.profile_attr, None)


class ProfileCharField(ProfileValueMixin, serializers.CharField):
    pass


class ProfileEmailField(ProfileValueMixin, serializers.EmailField):
    pass


class ProfileBooleanField(ProfileValueMixin, serializers.BooleanField):
    pass


class ProfileIntegerField(ProfileValueMixin, serializers.IntegerField):
    pass


class ProfileDateField(ProfileValueMixin, serializers.DateField):
    pass


def split_name(nome_completo):
    partes = [parte for parte in (nome_completo or "").strip().split() if parte]
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], ""
    return partes[0], " ".join(partes[1:])


def build_default_matricula(usuario):
    username = (usuario.username or "").strip()
    if username.isdigit():
        return username
    return str(usuario.id).zfill(7)


def build_default_profile_data(usuario):
    pessoa = getattr(usuario, "pessoa", None)
    nome_completo = getattr(pessoa, "nome_completo", "") or usuario.get_full_name().strip()
    nome_usual = (usuario.first_name or "").strip() or (nome_completo.split()[0] if nome_completo else usuario.username)
    return {
        "matricula_servidor": get_matricula_servidor_safe(usuario) or build_default_matricula(usuario),
        "nome_usual": nome_usual,
        "email_institucional": usuario.email or "",
        "cargo_atual": usuario.get_tipo_display(),
        "posicao_atual": "Em exercicio",
    }


class ServidorSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    setor_nome = serializers.CharField(source="setor.nome", read_only=True)
    matricula_servidor = ProfileCharField(profile_attr="matricula_servidor", required=False, allow_blank=True)
    nome_usual = ProfileCharField(profile_attr="nome_usual", required=False, allow_blank=True)
    email_institucional = ProfileEmailField(profile_attr="email_institucional", required=False, allow_blank=True)
    email_siape = ProfileEmailField(profile_attr="email_siape", required=False, allow_blank=True)
    email_secundario_recuperacao = ProfileEmailField(profile_attr="email_secundario_recuperacao", required=False, allow_blank=True)
    email_notificacoes = ProfileEmailField(profile_attr="email_notificacoes", required=False, allow_blank=True)
    email_google_sala = ProfileEmailField(profile_attr="email_google_sala", required=False, allow_blank=True)
    telefones_institucionais = ProfileCharField(profile_attr="telefones_institucionais", required=False, allow_blank=True)
    telefones_pessoais = ProfileCharField(profile_attr="telefones_pessoais", required=False, allow_blank=True)
    em_pgd = ProfileBooleanField(profile_attr="em_pgd", required=False)
    nao_tem_impressao_digital = ProfileBooleanField(profile_attr="nao_tem_impressao_digital", required=False)
    estado_civil = ProfileCharField(profile_attr="estado_civil", required=False, allow_blank=True)
    naturalidade = ProfileCharField(profile_attr="naturalidade", required=False, allow_blank=True)
    sexo = ProfileCharField(profile_attr="sexo", required=False, allow_blank=True)
    grupo_sanguineo_rh = ProfileCharField(profile_attr="grupo_sanguineo_rh", required=False, allow_blank=True)
    dependentes_ir = ProfileIntegerField(profile_attr="dependentes_ir", required=False, allow_null=True, min_value=0)
    raca_etnia = ProfileCharField(profile_attr="raca_etnia", required=False, allow_blank=True)
    nome_pai = ProfileCharField(profile_attr="nome_pai", required=False, allow_blank=True)
    nome_mae = ProfileCharField(profile_attr="nome_mae", required=False, allow_blank=True)
    pis_pasep = ProfileCharField(profile_attr="pis_pasep", required=False, allow_blank=True)
    titulacao = ProfileCharField(profile_attr="titulacao", required=False, allow_blank=True)
    escolaridade = ProfileCharField(profile_attr="escolaridade", required=False, allow_blank=True)
    identidade = ProfileCharField(profile_attr="identidade", required=False, allow_blank=True)
    orgao_expedidor = ProfileCharField(profile_attr="orgao_expedidor", required=False, allow_blank=True)
    uf_rg = ProfileCharField(profile_attr="uf_rg", required=False, allow_blank=True)
    data_expedicao = ProfileDateField(profile_attr="data_expedicao", required=False, allow_null=True)
    titulo_eleitor_numero = ProfileCharField(profile_attr="titulo_eleitor_numero", required=False, allow_blank=True)
    titulo_eleitor_zona = ProfileCharField(profile_attr="titulo_eleitor_zona", required=False, allow_blank=True)
    titulo_eleitor_secao = ProfileCharField(profile_attr="titulo_eleitor_secao", required=False, allow_blank=True)
    titulo_eleitor_uf = ProfileCharField(profile_attr="titulo_eleitor_uf", required=False, allow_blank=True)
    posicao_atual = ProfileCharField(profile_attr="posicao_atual", required=False, allow_blank=True)
    cargo_atual = ProfileCharField(profile_attr="cargo_atual", required=False, allow_blank=True)
    regime_trabalho = ProfileCharField(profile_attr="regime_trabalho", required=False, allow_blank=True)
    jornada_trabalho = ProfileCharField(profile_attr="jornada_trabalho", required=False, allow_blank=True)
    classe_funcional = ProfileCharField(profile_attr="classe_funcional", required=False, allow_blank=True)
    nivel_funcional = ProfileCharField(profile_attr="nivel_funcional", required=False, allow_blank=True)
    banco = ProfileCharField(profile_attr="banco", required=False, allow_blank=True)
    agencia = ProfileCharField(profile_attr="agencia", required=False, allow_blank=True)
    conta_corrente = ProfileCharField(profile_attr="conta_corrente", required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={"input_type": "password"})

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "nome_completo",
            "email",
            "cpf",
            "tipo",
            "tipo_display",
            "is_active",
            "setor",
            "setor_nome",
            "matricula_servidor",
            "nome_usual",
            "email_institucional",
            "email_siape",
            "email_secundario_recuperacao",
            "email_notificacoes",
            "email_google_sala",
            "telefones_institucionais",
            "telefones_pessoais",
            "em_pgd",
            "nao_tem_impressao_digital",
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
            "identidade",
            "orgao_expedidor",
            "uf_rg",
            "data_expedicao",
            "titulo_eleitor_numero",
            "titulo_eleitor_zona",
            "titulo_eleitor_secao",
            "titulo_eleitor_uf",
            "posicao_atual",
            "cargo_atual",
            "regime_trabalho",
            "jornada_trabalho",
            "classe_funcional",
            "nivel_funcional",
            "banco",
            "agencia",
            "conta_corrente",
            "password",
        ]

    def validate_tipo(self, value):
        if value == PerfilUsuario.ALUNO:
            raise serializers.ValidationError("Servidor nao pode ter perfil de aluno.")
        return value

    def validate_setor(self, value):
        if value and not Setor.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError("Setor informado nao encontrado.")
        return value

    def validate_cpf(self, value):
        instance = getattr(self, "instance", None)
        queryset = Pessoa.objects.filter(cpf=value)
        if instance and instance.pessoa_id:
            queryset = queryset.exclude(pk=instance.pessoa_id)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe uma pessoa cadastrada com este CPF.")
        return value

    def validate_matricula_servidor(self, value):
        if not value:
            return value

        queryset = ServidorPerfil.objects.filter(matricula_servidor=value)
        instance = getattr(self, "instance", None)
        perfil = getattr(instance, "perfil_servidor", None) if instance else None
        if perfil:
            queryset = queryset.exclude(pk=perfil.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe um servidor cadastrado com esta matricula.")
        return value

    def validate(self, attrs):
        if not self.instance:
            password = attrs.get("password", "")
            if not password:
                raise serializers.ValidationError({"password": "Informe uma senha para o servidor."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        profile_data = self._extract_profile_data(validated_data)
        nome_completo = validated_data.pop("nome_completo")
        password = validated_data.pop("password")
        first_name, last_name = split_name(nome_completo)

        pessoa = Pessoa.objects.create(
            nome_completo=nome_completo,
            cpf=validated_data["cpf"],
            email=validated_data.get("email", ""),
        )

        usuario = Usuario.objects.create(
            pessoa=pessoa,
            first_name=first_name,
            last_name=last_name,
            **validated_data,
        )
        usuario.set_password(password)
        usuario.save(update_fields=["password"])
        self._sync_profile(usuario, profile_data)
        return usuario

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = self._extract_profile_data(validated_data)
        nome_completo = validated_data.pop("nome_completo", None)
        password = validated_data.pop("password", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        if nome_completo is not None:
            first_name, last_name = split_name(nome_completo)
            instance.first_name = first_name
            instance.last_name = last_name

            if instance.pessoa_id:
                instance.pessoa.nome_completo = nome_completo
                instance.pessoa.cpf = instance.cpf
                instance.pessoa.email = instance.email
                instance.pessoa.save(update_fields=["nome_completo", "cpf", "email"])
            else:
                instance.pessoa = Pessoa.objects.create(
                    nome_completo=nome_completo,
                    cpf=instance.cpf,
                    email=instance.email,
                )
        elif instance.pessoa_id:
            instance.pessoa.cpf = validated_data.get("cpf", instance.cpf)
            instance.pessoa.email = validated_data.get("email", instance.email)
            instance.pessoa.save(update_fields=["cpf", "email"])

        instance.save()

        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])

        self._sync_profile(instance, profile_data)

        return instance

    def get_nome_completo(self, obj):
        if getattr(obj, "pessoa", None) and obj.pessoa.nome_completo:
            return obj.pessoa.nome_completo
        return obj.get_full_name().strip() or obj.username

    def _extract_profile_data(self, validated_data):
        profile_data = {}
        for field_name in PROFILE_FIELD_NAMES:
            if field_name in validated_data:
                profile_data[field_name] = validated_data.pop(field_name)
        return profile_data

    def _sync_profile(self, usuario, profile_data):
        defaults = build_default_profile_data(usuario)
        perfil, created = ServidorPerfil.objects.get_or_create(usuario=usuario, defaults=defaults)

        changed_fields = []
        for field_name, default_value in defaults.items():
            current_value = getattr(perfil, field_name)
            if not current_value:
                setattr(perfil, field_name, default_value)
                changed_fields.append(field_name)

        for field_name, value in profile_data.items():
            if getattr(perfil, field_name) != value:
                setattr(perfil, field_name, value)
                changed_fields.append(field_name)

        if changed_fields:
            if created:
                perfil.save()
            else:
                perfil.save(update_fields=[*sorted(set(changed_fields)), "atualizado_em"])