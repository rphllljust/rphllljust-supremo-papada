from apps.access.api.permissions import CanAccessModule


class CanAccessConfigurarCurso(CanAccessModule):
    message = "Usuario sem permissao para acessar o modulo de configuracao de curso."

    def has_permission(self, request, view):
        if not hasattr(view, "module_name"):
            view.module_name = "configurar_curso"

        if not hasattr(view, "access_surface"):
            view.access_surface = "api"

        if not hasattr(view, "access_action"):
            view.access_action = "view"

        return super().has_permission(request, view)
