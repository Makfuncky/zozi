"""Verification for the supplier domain rescue.

Confirms the duplicate non-canonical ``services/suppliers/`` shim folder has
been removed and that supplier-domain imports still resolve correctly.

Run from repo root:
    python tests/verify_supplier_module.py
"""
import os
import sys

BACKEND = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND))

FAILS = []


def check(label, cond):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {label}")
    if not cond:
        FAILS.append(label)


# 1. The non-canonical duplicate folder must be gone.
dup_dir = os.path.join(BACKEND, "services", "suppliers")
check("services/suppliers/ duplicate folder removed", not os.path.isdir(dup_dir))

# 2. The canonical supplier service module must still exist.
canon = os.path.join(BACKEND, "services", "supplier", "suppliers_write_service.py")
check("canonical services/supplier/suppliers_write_service.py exists", os.path.isfile(canon))

# 3. Legacy flat import must still resolve to the canonical (singular) domain.
import services  # noqa: E402  (registers the legacy finder)
import services.suppliers_write_service as sws  # noqa: E402

real = os.path.abspath(sws.__file__)
expected = os.path.abspath(canon)
check("services.suppliers_write_service resolves to services/supplier/",
      real == expected)

# 4. The merged helper functions must be importable from the canonical module.
for fn in ("create_supplier_profile", "get_supplier_stats",
           "create_supplier_payout_request", "commit_session"):
    check(f"canonical module exposes {fn}", hasattr(sws, fn))

# 5. The package 'services.suppliers' (plural) must no longer import.
try:
    import services.suppliers  # noqa: E402,F401
    check("services.suppliers (plural) is NOT importable", False)
except ModuleNotFoundError:
    check("services.suppliers (plural) is NOT importable", True)

# 6. Route gate must hold (FastAPI app still wires 1421 routes).
import main  # noqa: E402
app = getattr(main, "app", None)
routes = len(getattr(app, "routes", []))
check(f"app import succeeds with route count = {routes}", app is not None)
check("route count == 1421 (no regressions)", routes == 1421)

print()
if FAILS:
    print(f"{len(FAILS)} CHECK(S) FAILED:")
    for f in FAILS:
        print("  -", f)
    sys.exit(1)
print("ALL CHECKS PASSED")
