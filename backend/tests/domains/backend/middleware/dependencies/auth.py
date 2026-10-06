"""Import-law + fail-closed coverage for ``middleware.dependencies.auth``.

Covers the FILE 161 Architectural FAIL: ``middleware/dependencies/auth.py``
must not statically import a domain module (Law 1 / Law 97 allow
``middleware -> {rbac, infrastructure}`` only), while keeping the full
historical auth surface intact and every authorisation check failing closed.

The tests below are deliberately written so that a future "fix" which stubs,
bypasses or weakens any auth dependency makes them FAIL, not pass.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest
from fastapi import HTTPException

import middleware.dependencies.auth as auth_deps

_MODULE_PATH = (
    Path(__file__).resolve().parents[5] / "middleware" / "dependencies" / "auth.py"
)

#: The exact historical surface re-exported by the module (frozen by contract).
EXPECTED_EXPORTS = (
    "bearer_scheme",
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
    "require_coupon_admin",
    "require_customer",
    "require_employee",
    "require_logistics",
    "require_permissions",
    "require_roles",
    "require_staff",
    "require_super_admin",
    "require_supplier",
    "require_treasury_access",
    "start_otp",
    "verify_otp",
)


class _User:
    """Minimal stand-in for the ORM ``User`` row the auth deps receive."""

    def __init__(self, role: str):
        self.role = role
        self.is_active = True


# ── FAIL entry 1: the static middleware -> domains import edge ─────────────


def test_module_has_no_static_domains_import() -> None:
    """No module-level ``from domains...`` import in the middleware auth module.

    This is the FAIL being corrected. Any static ``ImportFrom`` whose module
    starts with ``domains`` puts the upward edge back into the import graph,
    regardless of the docstring that claims otherwise.
    """
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    offenders = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.split(".")[0] == "domains"
    ]
    assert offenders == [], f"middleware must not statically import {offenders}"


def test_auth_dependencies_come_from_the_infrastructure_layer() -> None:
    """The re-export must source from ``infrastructure.security.dependencies``."""
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))
    sources = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module is not None
        and node.module.startswith("infrastructure")
    }
    assert "infrastructure.security.dependencies" in sources


def test_module_imports_without_pulling_in_a_static_domain_edge() -> None:
    """The verify command from the worklist: the import must succeed."""
    from middleware.dependencies.auth import get_current_user  # noqa: F401

    assert callable(get_current_user)


# ── the surface must stay complete and must not be stubbed ────────────────


@pytest.mark.parametrize("name", EXPECTED_EXPORTS)
def test_symbol_is_exported_and_not_a_stub(name: str) -> None:
    """Every historical symbol is present, non-None, and ``__all__`` lists it."""
    assert hasattr(auth_deps, name), f"{name} disappeared from the surface"
    value = getattr(auth_deps, name)
    assert value is not None, f"{name} was stubbed out to None"
    assert name in auth_deps.__all__, f"{name} missing from __all__"
    if name != "bearer_scheme":  # HTTPBearer instance, not a callable
        assert callable(value), f"{name} is no longer callable"


def test_get_current_user_signature_is_unchanged() -> None:
    """The wrapper used by the infrastructure shim must not hide the params."""
    params = list(inspect.signature(auth_deps.get_current_user).parameters)
    assert params == ["credentials", "db"]


# ── fail-closed: the checks still reject unauthenticated / unauthorised ────


def test_get_current_user_rejects_missing_credentials() -> None:
    """Adversarial input 1: no Authorization header at all -> 401, never a user."""
    with pytest.raises(HTTPException) as exc:
        auth_deps.get_current_user(credentials=None, db=None)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Not authenticated"


def test_get_current_user_rejects_blank_bearer_token() -> None:
    """Adversarial input 2: header present but empty credential -> 401."""
    from fastapi.security import HTTPAuthorizationCredentials

    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")
    with pytest.raises(HTTPException) as exc:
        auth_deps.get_current_user(credentials=creds, db=None)
    assert exc.value.status_code == 401


def test_get_current_user_optional_returns_none_for_missing_credentials() -> None:
    """The optional variant degrades to ``None`` -- it must not fabricate a user."""
    assert auth_deps.get_current_user_optional(credentials=None, db=None) is None


@pytest.mark.parametrize(
    "gate",
    [
        "require_admin",
        "require_super_admin",
        "require_supplier",
        "require_logistics",
        "require_treasury_access",
        "require_coupon_admin",
    ],
)
def test_role_gates_reject_a_customer(gate: str) -> None:
    """Adversarial input 3: a low-privilege user hitting an elevated gate -> 403.

    If any gate were turned into a no-op this raises ``TypeError``/fails, so a
    bypass cannot be introduced silently.
    """
    with pytest.raises(HTTPException) as exc:
        getattr(auth_deps, gate)(current_user=_User("customer"))
    assert exc.value.status_code == 403


def test_require_roles_factory_rejects_unprivileged_user() -> None:
    checker = auth_deps.require_roles("admin", "super_admin")
    with pytest.raises(HTTPException) as exc:
        checker(current_user=_User("customer"))
    assert exc.value.status_code == 403