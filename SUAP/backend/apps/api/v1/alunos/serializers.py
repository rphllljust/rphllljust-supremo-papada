import html
import re
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email as django_validate_email
from django.db import transaction
from rest_framework import serializers

from apps.accounts.utils import normalize_cpf
from apps.usuarios.models import Aluno, PerfilUsuario, Pessoa


Usuario = get_user_model()

_SCRIPT_RE = re.compile(r'<[^>]+>', re.IGNORECASE)


def sanitize_text(value: str) -> str:
    """Remove tags HTML/JS de campos de texto livre."""
    cleaned = _SCRIPT_RE.sub('', str(value or ''))
    return html.unescape(cleaned).strip()


def _calcular_idade(data_nascimento: date) -> int:
    today = date.today()
    return today.year - data_nascimento.year - (
        (today.month, today.day) < (data_nascimento.month, data_nascimento.day)
    )


def split_name(nome_completo):
    partes = [parte for parte in (nome_completo or "").strip().split() if parte]
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0][:150], ""
    first_name = partes[0][:150]
    last_name = " ".join(partes[1:])[:150]
    return first_name, last_name


class NomeCompletoField(serializers.Field):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, obj):
        if getattr(obj, "pessoa", None) and obj.pessoa.nome_completo:
            return obj.pessoa.nome_completo
        return obj.get_full_name().strip() or obj.username

    def to_internal_value(self, data):
        value = str(data or "").strip()
        if not value:
            raise serializers.ValidationError("Informe o nome completo do aluno.")
        return value


class SituacaoAlunoField(serializers.Field):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, obj):
        aluno = getattr(getattr(obj, "pessoa", None), "aluno", None)
        return aluno.situacao if aluno else Aluno.SITUACAO_CHOICES[0][0]

    def to_internal_value(self, data):
        value = str(data or "").strip() or Aluno.SITUACAO_CHOICES[0][0]
        situacoes_validas = {choice for choice, _label in Aluno.SITUACAO_CHOICES}
        if value not in situacoes_validas:
            raise serializers.ValidationError("Situacao do aluno invalida.")
        return value


class DataIngressoField(serializers.Field):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, obj):
        aluno = getattr(getattr(obj, "pessoa", None), "aluno", None)
        return aluno.data_ingresso.isoformat() if aluno and aluno.data_ingresso else None

    def to_internal_value(self, data):
        raise serializers.ValidationError("Campo somente leitura.")


class AlunoSerializer(serializers.ModelSerializer):
    nome_completo = NomeCompletoField()
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    tipo = serializers.CharField(read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    situacao = SituacaoAlunoField(required=False)
    data_ingresso = DataIngressoField(read_only=True)
    # Campos extras recebidos na criação/edição para validação de menor
    data_nascimento = serializers.DateField(required=False, write_only=True)
    responsavel_nome = serializers.CharField(required=False, allow_blank=True, write_only=True)

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
            "situacao",
            "data_ingresso",
            "data_nascimento",
            "responsavel_nome",
        ]

    def validate_cpf(self, value):
        try:
            cpf = normalize_cpf(value)
        except Exception as exc:
            raise serializers.ValidationError(str(exc)) from exc

        instance = getattr(self, "instance", None)
        # Verifica unicidade em AMBAS as tabelas (Usuario e Pessoa) para evitar
        # cadastro duplicado quando o CPF ainda não está na tabela Usuario.
        queryset = Usuario.objects.filter(cpf=cpf)
        if instance:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise serializers.ValidationError("Ja existe um aluno cadastrado com este CPF.")

        from apps.usuarios.models import Pessoa as PessoaModel
        pessoa_qs = PessoaModel.objects.filter(cpf=cpf)
        if instance and instance.pessoa_id:
            pessoa_qs = pessoa_qs.exclude(pk=instance.pessoa_id)
        if pessoa_qs.exists():
            raise serializers.ValidationError("Ja existe uma pessoa cadastrada com este CPF.")

        return cpf

    def validate_nome_completo(self, value):
        nome = sanitize_text(value)
        if len(nome) > 200:
            raise serializers.ValidationError("Nome completo muito longo. Limite de 200 caracteres.")
        return nome

    def validate_email(self, value):
        email = sanitize_text(value).lower()
        if not email:
            return ""
        try:
            django_validate_email(email)
        except DjangoValidationError as exc:
            raise serializers.ValidationError("Informe um e-mail válido no formato RFC.") from exc
        return email

    def validate_situacao(self, value):
        situacoes_validas = {choice for choice, _label in Aluno.SITUACAO_CHOICES}
        if value not in situacoes_validas:
            raise serializers.ValidationError("Situacao do aluno invalida.")
        return value

    def validate(self, attrs):
        nome_completo = (attrs.get("nome_completo") or "").strip()
        if not nome_completo:
            raise serializers.ValidationError({"nome_completo": "Informe o nome completo do aluno."})
        attrs["nome_completo"] = nome_completo
        attrs.setdefault("situacao", Aluno.SITUACAO_CHOICES[0][0])

        # Responsável obrigatório para alunos menores de 18 anos (T007 / T034)
        data_nascimento = attrs.get("data_nascimento")
        if data_nascimento and _calcular_idade(data_nascimento) < 18:
            responsavel = (attrs.get("responsavel_nome") or "").strip()
            if not responsavel:
                raise serializers.ValidationError(
                    {"responsavel_nome": "Informe o responsavel: alunos menores de 18 anos exigem responsavel."}
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        nome_completo = validated_data.pop("nome_completo")
        situacao = validated_data.pop("situacao", Aluno.SITUACAO_CHOICES[0][0])
        first_name, last_name = split_name(nome_completo)

        pessoa = Pessoa.objects.create(
            nome_completo=nome_completo,
            cpf=validated_data["cpf"],
            email=validated_data.get("email", ""),
            ativo=validated_data.get("is_active", True),
        )

        usuario = Usuario.objects.create(
            pessoa=pessoa,
            username=validated_data["cpf"],
            first_name=first_name,
            last_name=last_name,
            tipo=PerfilUsuario.ALUNO,
            **validated_data,
        )
        usuario.set_unusable_password()
        usuario.save(update_fields=["password"])

        Aluno.objects.create(
            pessoa=pessoa,
            situacao=situacao,
        )

        return usuario

    @transaction.atomic
    def update(self, instance, validated_data):
        nome_completo = validated_data.pop("nome_completo", None)
        situacao = validated_data.pop("situacao", None)

        for field, value in validated_data.items():
            setattr(instance, field, value)

        instance.tipo = PerfilUsuario.ALUNO
        instance.username = instance.cpf

        if nome_completo is not None:
            first_name, last_name = split_name(nome_completo)
            instance.first_name = first_name
            instance.last_name = last_name

            if instance.pessoa_id:
                instance.pessoa.nome_completo = nome_completo
            else:
                instance.pessoa = Pessoa(
                    nome_completo=nome_completo,
                    cpf=instance.cpf,
                    email=instance.email or "",
                    ativo=instance.is_active,
                )
                instance.pessoa.save()

        if instance.pessoa:
            instance.pessoa.cpf = instance.cpf
            instance.pessoa.email = instance.email or ""
            instance.pessoa.ativo = instance.is_active
            instance.pessoa.save()

            aluno, _created = Aluno.objects.get_or_create(
                pessoa=instance.pessoa,
                defaults={"situacao": situacao or Aluno.SITUACAO_CHOICES[0][0]},
            )
            if situacao is not None and aluno.situacao != situacao:
                aluno.situacao = situacao
                aluno.save(update_fields=["situacao"])

        instance.save()
        return instance
