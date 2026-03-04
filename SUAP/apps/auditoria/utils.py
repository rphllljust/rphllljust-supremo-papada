from functools import wraps
from typing import Any, Callable, Optional

from django.http import HttpRequest

from .models import LogAuditoria


def resolve_ip(request: Optional[HttpRequest]) -> Optional[str]:
    """Extrai IP do request de forma segura."""
    if not request:
        return None
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def audit_log(
    acao: str,
    modelo: Optional[str] = None,
    get_objeto: Optional[Callable[..., Any]] = None,
    descricao: Optional[str] = None,
    dados: Optional[Any] = None,
):
    """
    Decorador para views function-based.
    Exemplo:
        @audit_log(\"CRIACAO\", modelo=\"Matricula\", get_objeto=lambda req,*a,**k: k.get(\"pk\"))\n        def minha_view(...):
            ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            try:
                objeto = get_objeto(request, response, *args, **kwargs) if get_objeto else None
                objeto_id = getattr(objeto, \"pk\", objeto) if objeto is not None else None
                LogAuditoria.registrar(
                    usuario=request.user if getattr(request, \"user\", None) and request.user.is_authenticated else None,
                    acao=acao,
                    modelo=modelo or objeto.__class__.__name__ if objeto is not None else modelo,
                    objeto_id=objeto_id,
                    descricao=descricao or \"\",\n                    dados=dados,
                    request=request,
                )
            except Exception:
                # Não interrompe o fluxo da view caso o log falhe.
                pass
            return response

        return _wrapped_view

    return decorator


class AuditLogMixin:
    """
    Mixin simples para CBVs. Chame self.log_audit(...) após salvar.
    """

    acao_auditoria: Optional[str] = None
    modelo_auditoria: Optional[str] = None

    def log_audit(self, acao: Optional[str] = None, modelo: Optional[str] = None, objeto=None, descricao: str = \"\", dados=None):
        try:
            LogAuditoria.registrar(
                usuario=getattr(self, \"request\", None).user if getattr(self, \"request\", None) and self.request.user.is_authenticated else None,
                acao=acao or self.acao_auditoria or \"OUTRO\",\n                modelo=modelo or self.modelo_auditoria or (objeto.__class__.__name__ if objeto is not None else None),
                objeto_id=getattr(objeto, \"pk\", objeto) if objeto is not None else None,
                descricao=descricao,
                dados=dados,
                request=getattr(self, \"request\", None),
            )
        except Exception:
            pass

