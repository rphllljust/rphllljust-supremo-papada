from rest_framework import serializers

from apps.setores.models import Setor


class SetorSerializer(serializers.ModelSerializer):
    setor_superior_nome = serializers.CharField(source="setor_superior.nome", read_only=True)

    class Meta:
        model = Setor
        fields = [
            "id",
            "nome",
            "sigla",
            "codigo",
            "setor_superior",
            "setor_superior_nome",
            "ativo",
        ]

    def validate_setor_superior(self, value):
        if self.instance and value and value.pk == self.instance.pk:
            raise serializers.ValidationError("Um setor nao pode ser superior de si mesmo.")
        return value