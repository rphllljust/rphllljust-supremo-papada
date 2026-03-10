from django.core.exceptions import ValidationError


def normalize_cpf(value: str) -> str:
    cpf = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(cpf) != 11:
        raise ValidationError("Informe um CPF com 11 digitos.")

    # Reject obvious invalid sequences like 00000000000 or 11111111111.
    if cpf == cpf[0] * 11:
        raise ValidationError("CPF invalido.")

    def calcular_digito(parcial: str) -> str:
        peso_inicial = len(parcial) + 1
        total = sum(int(digito) * (peso_inicial - indice) for indice, digito in enumerate(parcial))
        resto = 11 - (total % 11)
        return "0" if resto >= 10 else str(resto)

    d1 = calcular_digito(cpf[:9])
    d2 = calcular_digito(cpf[:9] + d1)
    if cpf[-2:] != f"{d1}{d2}":
        raise ValidationError("CPF invalido.")

    return cpf

