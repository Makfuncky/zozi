"""Backward-compat shim — canonical location is rbac/staff_permissions.py."""
# Direct imports with circular import handling
try:
    from rbac.staff_permissions import default_permissions_for_role, sanitize_staff_permissions, STAFF_PERMISSION_GROUPS
except ImportError:
    # Circular import fallback - lazy import
    import importlib
    def _get_attr(name):
        mod = importlib.import_module('rbac.staff_permissions')
        return getattr(mod, name)
    def default_permissions_for_role(*args, **kwargs):
        return _get_attr('default_permissions_for_role')(*args, **kwargs)
    def sanitize_staff_permissions(*args, **kwargs):
        return _get_attr('sanitize_staff_permissions')(*args, **kwargs)
    STAFF_PERMISSION_GROUPS = _get_attr('STAFF_PERMISSION_GROUPS')
