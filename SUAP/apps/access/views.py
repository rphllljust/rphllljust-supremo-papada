from django.shortcuts import render


DEFAULT_ACCESS_DENIED_MESSAGE = "Voce nao possui permissao para acessar este recurso."


def render_access_denied(request, message=None, *, status=403):
    return render(
        request,
        "base/acesso_negado.html",
        {"mensagem": message or DEFAULT_ACCESS_DENIED_MESSAGE},
        status=status,
    )


def acesso_negado(request, exception=None):
    return render_access_denied(request)
