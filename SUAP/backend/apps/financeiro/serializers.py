from datetime import date

from rest_framework import serializers

from .models import ContratoFinanceiro, Mensalidade, PlanoPagamento


class PlanoPagamentoSerializer(serializers.ModelSerializer):
    curso_nome = serializers.CharField(source='curso.nome', read_only=True)

    class Meta:
        model = PlanoPagamento
        fields = [
            'id', 'curso', 'curso_nome', 'valor_total', 'valor_parcela',
            'quantidade_parcelas', 'periodicidade', 'permite_bolsa',
            'percentual_bolsa_maximo', 'ativo', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class ContratoFinanceiroSerializer(serializers.ModelSerializer):
    matricula_numero = serializers.CharField(source='matricula.numero_matricula', read_only=True)
    aluno_nome = serializers.CharField(source='matricula.aluno.pessoa.nome_completo', read_only=True)
    plano_nome = serializers.CharField(source='plano.curso.nome', read_only=True)
    valor_parcela = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    parcelas_pagas = serializers.IntegerField(read_only=True)
    parcelas_vencidas = serializers.IntegerField(read_only=True)
    esta_inadimplente = serializers.BooleanField(read_only=True)

    class Meta:
        model = ContratoFinanceiro
        fields = [
            'id', 'matricula', 'matricula_numero', 'aluno_nome', 'plano',
            'plano_nome', 'status', 'valor_total', 'valor_original',
            'quantidade_parcelas', 'valor_parcela', 'tipo_bolsa',
            'percentual_bolsa', 'parcelas_pagas', 'parcelas_vencidas',
            'esta_inadimplente', 'observacao', 'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']

    def validate(self, attrs):
        if attrs.get('percentual_bolsa', 0) > 0 and attrs.get('tipo_bolsa', 'SEM_BOLSA') == 'SEM_BOLSA':
            raise serializers.ValidationError(
                {'tipo_bolsa': 'Informe o tipo de bolsa quando houver percentual de desconto.'}
            )
        return attrs


class MensalidadeSerializer(serializers.ModelSerializer):
    contrato_numero = serializers.CharField(
        source='contrato.matricula.numero_matricula', read_only=True
    )
    aluno_nome = serializers.CharField(
        source='contrato.matricula.aluno.pessoa.nome_completo', read_only=True
    )
    valor_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Mensalidade
        fields = [
            'id', 'contrato', 'contrato_numero', 'aluno_nome', 'numero_parcela',
            'data_vencimento', 'valor_original', 'valor_pago', 'desconto',
            'multa', 'juros', 'valor_total', 'status', 'data_pagamento',
            'forma_pagamento', 'numero_boleto', 'linha_digitavel', 'observacao',
            'criado_em', 'atualizado_em',
        ]
        read_only_fields = ['criado_em', 'atualizado_em']


class RegistrarPagamentoSerializer(serializers.Serializer):
    valor_pago = serializers.DecimalField(max_digits=10, decimal_places=2)
    data_pagamento = serializers.DateField()
    forma_pagamento = serializers.CharField(required=False, allow_blank=True)
    numero_boleto = serializers.CharField(required=False, allow_blank=True)

    def validate_valor_pago(self, value):
        if value <= 0:
            raise serializers.ValidationError('O valor pago deve ser maior que zero.')
        return value

    def validate_data_pagamento(self, value):
        if value > date.today():
            raise serializers.ValidationError('A data de pagamento nao pode ser futura.')
        return value
