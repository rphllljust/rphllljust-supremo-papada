from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from apps.setores.models import Setor
from apps.usuarios.models import PerfilUsuario, Pessoa
from apps.usuarios.profile_compat import get_matricula_servidor_safe


Usuario = get_user_model()


def split_name(nome_completo):
    partes = [parte for parte in (nome_completo or "").strip().split() if parte]
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], ""
    return partes[0], " ".join(partes[1:])


class ServidorSerializer(serializers.ModelSerializer):
    nome_completo = serializers.SerializerMethodField()
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    setor_nome = serializers.CharField(source="setor.nome", read_only=True)
    matricula_servidor = serializers.SerializerMethodField(read_only=True)
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

    def validate(self, attrs):
        if not self.instance:
            password = attrs.get("password", "")
            if not password:
                raise serializers.ValidationError({"password": "Informe uma senha para o servidor."})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
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
        return usuario

    @transaction.atomic
    def update(self, instance, validated_data):
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

        return instance

    def get_nome_completo(self, obj):
        if getattr(obj, "pessoa", None) and obj.pessoa.nome_completo:
            return obj.pessoa.nome_completo
        return obj.get_full_name().strip() or obj.username

    def get_matricula_servidor(self, obj):
        return get_matricula_servidor_safe(obj)