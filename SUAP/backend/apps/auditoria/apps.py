from django.apps import AppConfig


class AuditoriaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.auditoria"
    verbose_name = "Auditoria"

    def ready(self):
        """Conecta sinais de login/logout para registrar automaticamente."""

        from django.contrib.auth import signals as auth_signals

        from .models import LogAuditoria

        def _on_login(sender, request, user, **kwargs):
            LogAuditoria.registrar(
                usuario=user,
                acao="LOGIN",
                modelo="Auth",
                objeto_id=getattr(user, "pk", None),
                descricao="Login realizado",
                dados=None,
                request=request,
            )

        def _on_logout(sender, request, user, **kwargs):
            LogAuditoria.registrar(
                usuario=user,
                acao="LOGOUT",
                modelo="Auth",
                objeto_id=getattr(user, "pk", None),
                descricao="Logout realizado",
                dados=None,
                request=request,
            )

        def _on_login_failed(sender, credentials, request, **kwargs):
            LogAuditoria.registrar(
                usuario=None,
                acao="LOGIN",
                modelo="Auth",
                objeto_id=None,
                descricao="Tentativa de login falhou",
                dados={"username": credentials.get("username") if credentials else None},
                request=request,
            )

        auth_signals.user_logged_in.connect(_on_login, dispatch_uid="auditoria_login")
        auth_signals.user_logged_out.connect(_on_logout, dispatch_uid="auditoria_logout")
        auth_signals.user_login_failed.connect(
            _on_login_failed, dispatch_uid="auditoria_login_failed"
        )
