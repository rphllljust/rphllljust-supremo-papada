class HistoricoDigitalError(Exception):
    """Erro base da emissao digital de historicos."""


class HistoricoDigitalBusinessError(HistoricoDigitalError):
    """Erro de regra de negocio da emissao."""


class HistoricoDigitalValidationError(HistoricoDigitalError):
    """Erro de validacao estrutural/documental."""
