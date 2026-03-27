from rest_framework import serializers

from apps.sica.models import SicaComponenteCurricular, SicaMatrizCurricular


class SicaMatrizCurricularSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    total_componentes = serializers.IntegerField(source="componentes.count", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SicaMatrizCurricular
        fields = [
            "id",
            "curso",
            "curso_nome",
            "versao",
            "status",
            "status_display",
            "descricao",
            "total_componentes",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em", "total_componentes"]

    def validate_versao(self, value):
        versao = (value or "").strip()
        if not versao:
            raise serializers.ValidationError("Informe a versao da matriz curricular.")
        return versao

    def validate_descricao(self, value):
        return (value or "").strip()


class SicaRelacionamentoResumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SicaComponenteCurricular
        fields = ["id", "componente", "periodo"]


class SicaComponenteCurricularSerializer(serializers.ModelSerializer):
    matriz_versao = serializers.CharField(source="matriz.versao", read_only=True)
    curso = serializers.IntegerField(source="matriz.curso_id", read_only=True)
    curso_nome = serializers.CharField(source="matriz.curso.nome", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    prerequisitos = serializers.PrimaryKeyRelatedField(
        queryset=SicaComponenteCurricular.objects.select_related("matriz"),
        many=True,
        required=False,
    )
    equivalencias = serializers.PrimaryKeyRelatedField(
        queryset=SicaComponenteCurricular.objects.select_related("matriz", "matriz__curso"),
        many=True,
        required=False,
    )
    prerequisitos_info = SicaRelacionamentoResumoSerializer(source="prerequisitos.all", many=True, read_only=True)
    equivalencias_info = SicaRelacionamentoResumoSerializer(source="equivalencias.all", many=True, read_only=True)

    class Meta:
        model = SicaComponenteCurricular
        fields = [
            "id",
            "matriz",
            "matriz_versao",
            "curso",
            "curso_nome",
            "periodo",
            "componente",
            "tipo",
            "tipo_display",
            "carga_horaria",
            "ementa",
            "prerequisitos",
            "prerequisitos_info",
            "equivalencias",
            "equivalencias_info",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["criado_em", "atualizado_em"]

    def validate_componente(self, value):
        componente = (value or "").strip()
        if not componente:
            raise serializers.ValidationError("Informe o nome do componente.")
        return componente

    def validate_ementa(self, value):
        return (value or "").strip()

    def validate(self, attrs):
        matriz = attrs.get("matriz", getattr(self.instance, "matriz", None))
        prerequisitos = attrs.get("prerequisitos")
        equivalencias = attrs.get("equivalencias")
        instance_id = getattr(self.instance, "id", None)

        if prerequisitos is not None:
            for prereq in prerequisitos:
                if prereq.id == instance_id:
                    raise serializers.ValidationError({"prerequisitos": "Um componente nao pode ser pre-requisito de si mesmo."})
                if matriz and prereq.matriz_id != matriz.id:
                    raise serializers.ValidationError({"prerequisitos": "Pre-requisitos devem pertencer a mesma matriz curricular."})

        if equivalencias is not None:
            for equivalente in equivalencias:
                if equivalente.id == instance_id:
                    raise serializers.ValidationError({"equivalencias": "Um componente nao pode ser equivalente a si mesmo."})
                if matriz and equivalente.matriz.curso_id != matriz.curso_id:
                    raise serializers.ValidationError({"equivalencias": "Equivalencias devem pertencer ao mesmo curso da matriz."})

        return attrs

    def create(self, validated_data):
        prerequisitos = validated_data.pop("prerequisitos", [])
        equivalencias = validated_data.pop("equivalencias", [])
        instance = super().create(validated_data)
        instance.prerequisitos.set(prerequisitos)
        instance.equivalencias.set(equivalencias)
        return instance

    def update(self, instance, validated_data):
        prerequisitos = validated_data.pop("prerequisitos", None)
        equivalencias = validated_data.pop("equivalencias", None)
        instance = super().update(instance, validated_data)

        if prerequisitos is not None:
            instance.prerequisitos.set(prerequisitos)

        if equivalencias is not None:
            instance.equivalencias.set(equivalencias)

        return instance
