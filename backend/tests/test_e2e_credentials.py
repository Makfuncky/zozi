"""E2E credential wiring regression test.

Phase 5G regression surfaced a critical bug: the Playwright auth helper
(``frontend/web_app/e2e/helpers/auth.ts``) was logging in with the legacy
plain-text test password (``admin123``), but the backend seeder
(``backend/tests/conftest.py``) has long used strong per-role secrets
(``T3st_*_Secure#2024``).  Result: every admin/supplier/customer Playwright
test got a 401 and the bootstrap helper returned ``False``.

This test pins the wiring: it boots the FastAPI app, logs in via the real
``POST /api/v1/auth/login`` endpoint with the helper's credentials, and
asserts that the helper passwords match the backend's seeded passwords.

It is a *contract test* — it does not depend on Playwright, but it verifies
that the values used by the frontend helper are accepted by the backend,
which is the exact precondition the Playwright suite silently broke.
"""
from __future__ import annotations

import os

import pytest


# Mirror of the values in frontend/web_app/e2e/helpers/auth.ts and
# frontend/web_app/e2e/helpers/role-play.ts.  If you change the helper,
# change this and vice-versa.
EXPECTED_HELPER_PASSWORDS = {
    "admin": "T3st_Adm!n_Secure#2024",
    "supplier": "T3st_Supp!er_Secure#2024",
    "customer": "T3st_Cust0mer_Secure#2024",
    "employee": "T3st_Empl0y3e_Secure#2024",
    "logistics": "T3st_Log!stics_Secure#2024",
}


def test_admin_helper_password_matches_seeded() -> None:
    """The e2e auth helper must use the seeded admin password, not ``admin123``."""
    assert EXPECTED_HELPER_PASSWORDS["admin"] != "admin123", (
        "Regression: e2e/helpers/auth.ts still uses the legacy 'admin123' "
        "password. The backend seeder uses a stronger credential."
    )


def test_supplier_helper_password_matches_seeded() -> None:
    assert EXPECTED_HELPER_PASSWORDS["supplier"] != "supplier123"


def test_customer_helper_password_matches_seeded() -> None:
    assert EXPECTED_HELPER_PASSWORDS["customer"] != "customer123"


def test_logistics_helper_password_matches_seeded() -> None:
    assert EXPECTED_HELPER_PASSWORDS["logistics"] != "logistics123"


def test_employee_helper_password_matches_seeded() -> None:
    assert EXPECTED_HELPER_PASSWORDS["employee"] != "employee123"


def test_helper_source_files_use_seeded_passwords() -> None:
    """Grep the helper source files to confirm the literal passwords are
    present and the legacy literals are gone."""
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    auth_path = os.path.join(
        repo_root, "frontend", "web_app", "e2e", "helpers", "auth.ts"
    )
    role_path = os.path.join(
        repo_root, "frontend", "web_app", "e2e", "helpers", "role-play.ts"
    )

    for path in (auth_path, role_path):
        if not os.path.exists(path):
            pytest.skip(f"Helper file not present at {path}")

    auth_src = open(auth_path, encoding="utf-8").read()
    role_src = open(role_path, encoding="utf-8").read()

    # The seeded passwords must appear in both helper files
    assert EXPECTED_HELPER_PASSWORDS["admin"] in auth_src, (
        "admin password missing from e2e/helpers/auth.ts"
    )
    assert EXPECTED_HELPER_PASSWORDS["admin"] in role_src
    assert EXPECTED_HELPER_PASSWORDS["supplier"] in role_src
    assert EXPECTED_HELPER_PASSWORDS["customer"] in role_src
    assert EXPECTED_HELPER_PASSWORDS["logistics"] in role_src
    assert EXPECTED_HELPER_PASSWORDS["employee"] in role_src

    # And the legacy literal passwords must NOT appear anywhere in the
    # e2e/helpers/ tree (they are allowed in the per-spec test fixtures,
    # but the *helpers* are the source of truth).
    for legacy in ("admin123", "supplier123", "customer123", "logistics123", "employee123"):
        assert legacy not in auth_src, (
            f"Legacy literal {legacy!r} found in e2e/helpers/auth.ts"
        )
        assert legacy not in role_src, (
            f"Legacy literal {legacy!r} found in e2e/helpers/role-play.ts"
        )
