from __future__ import annotations

from typing import Iterable

from apps.usuarios.models import PerfilUsuario

from .permissions import ACCESS_MATRIX, AVA_EXPORT_PROFILES, OBJECT_OWNER_FIELDS, OBJECT_OWNER_ID_FIELDS


def is_authenticated_user(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def get_user_profile(user):
    return getattr(user, "tipo", None)


def is_admin_user(user) -> bool:
    if not is_authenticated_user(user):
        return False
    return bool(getattr(user, "is_superuser", False) or get_user_profile(user) == PerfilUsuario.ADMIN)


def _normalize_profiles(profiles: Iterable[object]) -> set[str]:
    normalized = set()
    for profile in profiles:
        normalized.add(profile.value if isinstance(profile, PerfilUsuario) else str(profile))
    return normalized


def has_any_profile(user, *profiles) -> bool:
    if not is_authenticated_user(user):
        return False
    if is_admin_user(user):
        return True
    return get_user_profile(user) in _normalize_profiles(profiles)


def get_allowed_profiles(module_name: str, *, action: str = "view", surface: str = "web"):
    module_rules = ACCESS_MATRIX.get(module_name, {})
    surface_rules = module_rules.get(surface, {})
    allowed_profiles = surface_rules.get(action)
    if allowed_profiles is None and action != "view":
        allowed_profiles = surface_rules.get("view")
    return allowed_profiles


def can_access_module(user, module_name: str, *, action: str = "view", surface: str = "web") -> bool:
    if not is_authenticated_user(user):
        return False
    if is_admin_user(user):
        return True
    if user.groups.filter(name__iexact=f"{module_name}_access").exists():
        return True
    permission_codename = f"{surface}_{action}_{module_name}" if action != "view" or surface != "web" else f"access_{module_name}"
    if user.has_perm(f"{module_name}.{permission_codename}"):
        return True

    allowed_profiles = get_allowed_profiles(module_name, action=action, surface=surface)
    if allowed_profiles is None:
        return False
    return has_any_profile(user, *allowed_profiles)


def can_export_to_ava(user, module_name: str | None = None) -> bool:
    if not is_authenticated_user(user):
        return False
    if is_admin_user(user):
        return True
    if user.groups.filter(name__iexact="ava_exporters").exists():
        return True
    if user.has_perm("integracao_moodle.export_to_ava"):
        return True
    if module_name:
        allowed_profiles = get_allowed_profiles(module_name, action="export", surface="api_ava")
        if allowed_profiles is not None:
            return has_any_profile(user, *allowed_profiles)
    return has_any_profile(user, *AVA_EXPORT_PROFILES)


def can_view_object(user, obj) -> bool:
    if not is_authenticated_user(user) or obj is None:
        return False
    if is_admin_user(user):
        return True

    for field_name in OBJECT_OWNER_FIELDS:
        related = getattr(obj, field_name, None)
        if related == user:
            return True
        if getattr(related, "usuario", None) == user:
            return True
        if getattr(related, "id", None) == getattr(user, "id", None):
            return True

    for field_name in OBJECT_OWNER_ID_FIELDS:
        if getattr(obj, field_name, None) == getattr(user, "id", None):
            return True

    meta = getattr(obj, "_meta", None)
    app_label = getattr(meta, "app_label", None)
    return can_access_module(user, app_label, surface="web", action="view") if app_label else False


def filter_queryset_for_user(user, queryset, *, action: str = "view", surface: str = "web"):
    if not is_authenticated_user(user):
        return queryset.none()
    if is_admin_user(user):
        return queryset

    app_label = queryset.model._meta.app_label
    if not can_access_module(user, app_label, action=action, surface=surface):
        return queryset.none()
    return queryset
