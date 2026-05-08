from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from apps.turmas.models import Turma


class TurmaSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    curso_sigla = serializers.CharField(source="curso.sigla", read_only=True)
    professor_nome = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    modalidade_display = serializers.CharField(source="get_modalidade_display", read_only=True)
    total_alunos = serializers.IntegerField(read_only=True)
    total_diarios = serializers.IntegerField(read_only=True)

    class Meta:
        model = Turma
        fields = [
            "id",
            "nome",
            "ano_letivo",
            "status",
            "status_display",
            "modalidade",
            "modalidade_display",
            "polo",
            "curso",
            "curso_nome",
            "curso_sigla",
            "professor_responsavel",
            "professor_nome",
            "total_alunos",
            "total_diarios",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance
        modalidade = attrs.get("modalidade") or (instance.modalidade if instance else None)
        polo = attrs.get("polo") if "polo" in attrs else (instance.polo_id if instance else None)
        if modalidade == "ITINERANTE" and not polo:
            raise serializers.ValidationError(
                {"polo": "Polo/localidade é obrigatório para turmas com modalidade ITINERANTE."}
            )
        return attrs

    def validate_via_model(self, instance):
        """Executa o clean() do model para garantir consistência com as regras de negócio."""
        try:
            instance.full_clean(exclude=["id"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc

    def get_professor_nome(self, obj):
        if obj.professor_responsavel:
            return f"{obj.professor_responsavel.first_name} {obj.professor_responsavel.last_name}".strip()
        return None