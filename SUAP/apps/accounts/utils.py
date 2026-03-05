from django.core.exceptions import ValidationError


def normalize_cpf(value: str) -> str:
    cpf = "".join(ch for ch in (value or "") if ch.isdigit())
    if len(cpf) != 11:
        raise ValidationError("Informe um CPF com 11 digitos.")
    return cpf

