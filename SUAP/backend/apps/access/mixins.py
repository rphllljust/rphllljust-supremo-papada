from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ImproperlyConfigured

from .policies import can_access_module, can_export_to_ava, has_any_profile
from .views import render_access_denied


class AccessPolicyMixin(LoginRequiredMixin):
    access_denied_message = "Voce nao possui permissao para acessar este recurso."

    def has_access(self):
        return True

    def get_access_denied_message(self):
        return self.access_denied_message

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not self.has_access():
            return render_access_denied(request, self.get_access_denied_message())
        return super().dispatch(request, *args, **kwargs)


class ModuleAccessRequiredMixin(AccessPolicyMixin):
    module_name = None

    def has_access(self):
        if not self.module_name:
            raise ImproperlyConfigured("ModuleAccessRequiredMixin requer module_name.")
        return can_access_module(self.request.user, self.module_name)

    def get_access_denied_message(self):
        return f"Seu perfil nao possui acesso ao modulo {self.module_name}."


class PermissionRequiredByProfileMixin(AccessPolicyMixin):
    allowed_profiles = ()

    def has_access(self):
        if not self.allowed_profiles:
            raise ImproperlyConfigured("PermissionRequiredByProfileMixin requer allowed_profiles.")
        return has_any_profile(self.request.user, *self.allowed_profiles)

    def get_access_denied_message(self):
        return "Seu perfil nao possui permissao para esta funcionalidade."


class ExportToAvaRequiredMixin(AccessPolicyMixin):
    access_denied_message = "Seu perfil nao possui permissao para exportar dados para o AVA."

    def has_access(self):
        return can_export_to_ava(self.request.user)
