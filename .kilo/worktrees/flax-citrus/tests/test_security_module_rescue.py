"""Regression test for the SECURITY module rescue.

Verifies the concrete fixes applied while rescuing the security domain:
  * Duplicate root controller shims (controllers/iam_controller.py,
    controllers/risk_controller.py) removed; routers now import from
    controllers.security.* (resolves W4 + MV1).
  * Scratch one-off script backend/check_auth_head.py removed (resolves P1 + MV2).
  * utils/auth.py no longer swallows exceptions with bare `except Exception: pass`
    (resolves QUAL1 weak exception handling).

This is a static/structural test (no app runtime / DB required) so it can run
with ``pytest --noconftest`` alongside the other governance tests in this folder.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def test_duplicate_root_iam_controller_shim_removed():
    # W4 + MV1: the root re-export shim must be gone; canonical lives in security/.
    assert not (BACKEND / "controllers" / "iam_controller.py").exists(), (
        "Duplicate root controllers/iam_controller.py should be removed; "
        "use controllers.security.iam_controller instead."
    )
    assert (BACKEND / "controllers" / "security" / "iam_controller.py").exists()


def test_duplicate_root_risk_controller_shim_removed():
    assert not (BACKEND / "controllers" / "risk_controller.py").exists(), (
        "Duplicate root controllers/risk_controller.py should be removed; "
        "use controllers.security.risk_controller instead."
    )
    assert (BACKEND / "controllers" / "security" / "risk_controller.py").exists()


def test_scratch_check_auth_head_script_removed():
    # P1 + MV2: one-off scratch script must not sit at backend root.
    assert not (BACKEND / "check_auth_head.py").exists(), (
        "Scratch script backend/check_auth_head.py should be removed/moved out of backend root."
    )


def test_security_routers_import_from_security_subpackage():
    access_src = _read(BACKEND / "routers" / "api_security_access.py")
    assert "from controllers.security.iam_controller import" in access_src, (
        "api_security_access.py must import from controllers.security.iam_controller"
    )
    assert "from controllers.iam_controller import" not in access_src

    scoring_src = _read(BACKEND / "routers" / "api_security_scoring.py")
    assert "from controllers.security.risk_controller import" in scoring_src, (
        "api_security_scoring.py must import from controllers.security.risk_controller"
    )
    assert "from controllers.risk_controller import" not in scoring_src


def test_auth_utils_no_swallowed_exceptions():
    # QUAL1: no `except Exception:` whose body is only `pass`.
    src = _read(BACKEND / "utils" / "auth.py")
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if line.rstrip() == "except Exception:":
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            assert nxt.strip() != "pass", (
                f"utils/auth.py still swallows an exception at line {i + 1}; "
                "log or re-raise instead of `pass`."
            )
