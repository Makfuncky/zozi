"""CA3 regression guard.

The audit flagged ``routers/customer_coupons_mgmt.py:52`` — a customer-surface
router *defining* ``_require_admin`` (surface-inappropriate operation:
admin-token function name in a customer router).

Fixes (2026-08-10):
- ``routers/customer_coupons_mgmt.py`` no longer defines ``_require_admin``.
  Its admin-gated endpoints (list/create/delete coupon) now depend on the
  canonical ``utils.dependencies.require_admin`` (admin | super_admin), the
  same gate used by the canonical commerce coupons controller and 24 other
  routers. None of the endpoints use the resolved user beyond auth, so the
  swap is behavior-compatible with the coupon-management surface's intent.

These tests lock the seam: no customer-surface router may *define* an
admin-token function, and the coupon router must resolve admin through the
shared dependency.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

ROUTERS = BACKEND / "routers"

CUSTOMER_SURFACE_ROUTERS = [
    "customer_coupons_mgmt.py",
]


def _func_defs(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


# ── 1. No customer-surface router defines an admin-token function (CA3 scope) ──
def test_no_admin_defined_function_in_customer_coupons_router():
    src = (ROUTERS / "customer_coupons_mgmt.py").read_text(encoding="utf-8")
    for name in _func_defs(ROUTERS / "customer_coupons_mgmt.py"):
        assert "admin" not in re.split(r"[\-_]+", name.lower()), (
            f"customer-surface router defines admin operation {name!r}"
        )
    assert "_require_admin" not in src, "local _require_admin must be removed"


# ── 2. The coupon router resolves admin via the shared dependency ──
def test_coupon_router_uses_canonical_require_admin():
    src = (ROUTERS / "customer_coupons_mgmt.py").read_text(encoding="utf-8")
    assert "from utils.dependencies import require_admin" in src
    # every admin-gated endpoint depends on the canonical guard
    admin_uses = re.findall(r"Depends\((require_admin|_require_admin)\)", src)
    assert admin_uses, "expected at least one admin-gated endpoint"
    assert set(admin_uses) == {"require_admin"}


# ── 3. The canonical guard actually enforces the role gate ──
def test_canonical_require_admin_semantics():
    from utils.dependencies import _require_role

    class _User:
        def __init__(self, role):
            self.role = role

    from fastapi import HTTPException

    for role in ("admin", "super_admin"):
        assert _require_role(_User(role), "admin", "super_admin").role == role
    try:
        _require_role(_User("customer"), "admin", "super_admin")
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("non-admin role must be rejected")


# ── 4. Endpoint signatures still compile and register ──
def test_coupon_router_imports_and_registers():
    import routers.customer_coupons_mgmt as mod

    assert len(mod.router.routes) == 4
    assert not hasattr(mod, "_require_admin")


# ── 5. Sanity: no other customer-surface router (stem contains 'customer') defines admin ops ──
def test_no_customer_surface_router_defines_admin_ops():
    offenders = []
    for path in sorted(ROUTERS.glob("*.py")):
        if "customer" not in re.split(r"[\-_]+", path.stem.lower()):
            continue
        for name in _func_defs(path):
            if "admin" in re.split(r"[\-_]+", name.lower()):
                offenders.append(f"{path.name}:{name}")
    assert not offenders, f"customer-surface routers define admin ops: {offenders}"
