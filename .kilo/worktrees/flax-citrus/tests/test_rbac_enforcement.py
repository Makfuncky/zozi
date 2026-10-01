"""P2 verification: rbac.require_feature / require_module real enforcement (Law 4).

Run with:  backend\\venv\\Scripts\\python.exe tests\\test_rbac_enforcement.py
"""
import os
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from fastapi import HTTPException

import rbac.catalog as catalog
from rbac.dependencies import require_feature, require_module


class FakeUser:
    def __init__(self, role, module=None):
        self.role = role
        self.module = module


def call_dep(dep_factory, feature_or_module, user):
    dep = dep_factory(feature_or_module)
    try:
        dep(current_user=user)
        return None  # allowed
    except HTTPException as e:
        return e.status_code


def main():
    failures = []

    # 1. finance.ledger.post is now a registered feature (Law 4 single-source).
    if not catalog.is_known("finance.ledger.post"):
        failures.append("finance.ledger.post NOT in catalog")
    if "finance.ledger.post" not in catalog.all_features():
        failures.append("finance.ledger.post missing from all_features()")

    # 2. require_feature: unauthorized actor -> 403.
    cust = FakeUser("customer")
    code = call_dep(require_feature, "finance.ledger.post", cust)
    if code != 403:
        failures.append(f"customer require_feature(finance.ledger.post) expected 403 got {code}")

    # 3. require_feature: admin (wildcard *) -> allowed (None).
    admin = FakeUser("admin")
    code = call_dep(require_feature, "finance.ledger.post", admin)
    if code is not None:
        failures.append(f"admin require_feature(finance.ledger.post) expected allow got {code}")

    # 4. require_feature: finance_manager employee -> has finance.ledger.post + reporting.*.
    fm = FakeUser("finance_manager")
    code = call_dep(require_feature, "finance.ledger.post", fm)
    if code is not None:
        failures.append(f"finance_manager require_feature(finance.ledger.post) expected allow got {code}")
    code = call_dep(require_feature, "finance.reporting.export", fm)
    if code is not None:
        failures.append(f"finance_manager require_feature(finance.reporting.export) expected allow got {code}")

    # 5. require_feature: unknown literal -> 403 (CI should also catch).
    code = call_dep(require_feature, "finance.does.not.exist", admin)
    if code != 403:
        failures.append(f"unknown feature expected 403 got {code}")

    # 6. require_module: customer cannot enter admin module.
    code = call_dep(require_module, "admin", cust)
    if code != 403:
        failures.append(f"customer require_module(admin) expected 403 got {code}")

    # 7. require_module: admin reaches any module.
    code = call_dep(require_module, "admin", admin)
    if code is not None:
        failures.append(f"admin require_module(admin) expected allow got {code}")

    # 8. require_module: supplier reaches supplier module.
    sup = FakeUser("supplier")
    code = call_dep(require_module, "supplier", sup)
    if code is not None:
        failures.append(f"supplier require_module(supplier) expected allow got {code}")

    # 9. re-export surface from rbac package.
    import rbac
    if not hasattr(rbac, "require_feature") or not hasattr(rbac, "require_module"):
        failures.append("rbac package does not re-export require_feature/require_module")

    if failures:
        print("FAIL:")
        for f in failures:
            print("  -", f)
        sys.exit(1)
    print("P2 RBAC ENFORCEMENT VERIFIED: all checks passed")


if __name__ == "__main__":
    main()
