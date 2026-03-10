from rest_framework import serializers
from apps.unidades.models import Unidade

class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = ["id", "nome", "codigo"]