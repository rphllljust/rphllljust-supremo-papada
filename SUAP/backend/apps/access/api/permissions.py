from rest_framework.permissions import BasePermission

from apps.access.policies import can_access_module, can_export_to_ava, can_view_object


class CanAccessModule(BasePermission):
    message = "Usuario sem permissao para acessar este modulo."

    def has_permission(self, request, view):
        module_name = getattr(view, "module_name", None)
        if not module_name:
            return False
        action = getattr(view, "access_action", "view")
        surface = getattr(view, "access_surface", "api")
        return can_access_module(request.user, module_name, action=action, surface=surface)


class CanExportToAva(BasePermission):
    message = "Usuario sem permissao para exportar dados para o AVA."

    def has_permission(self, request, view):
        module_name = getattr(view, "module_name", None)
        return can_export_to_ava(request.user, module_name=module_name)


class CanViewObject(BasePermission):
    message = "Usuario sem permissao para visualizar este objeto."

    def has_permission(self, request, view):
        return bool(getattr(request.user, "is_authenticated", False))

    def has_object_permission(self, request, view, obj):
        return can_view_object(request.user, obj)
