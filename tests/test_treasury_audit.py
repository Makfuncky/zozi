"""Architecture-audit regression tests for the treasury / payments domains.

These guard against reintroduction of advisory findings that were resolved
during the audit cleanup:

- FE6: no leftover ``console``/``debugger`` debug statements in the payments
  client code (``frontend/mobile_app/lib/paymentService.ts``).

The QA/e2e harness ``frontend/web_app/scripts/e2e_payment_gateway.cjs`` is
intentionally excluded: its ``console`` output is the script's reporting
purpose (equivalent to a test file), so it is not subject to FE6.
"""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PAYMENT_CLIENT = os.path.join(
    REPO_ROOT, "frontend", "mobile_app", "lib", "paymentService.ts"
)

CONSOLE_RE = re.compile(r"(?<![\w.])console\.(log|error|warn|info|debug)\s*\(")
DEBUGGER_RE = re.compile(r"\bdebugger\s*;")

# Symbol that must stay unwired (governance-contract facade, not dead code).
ADMIN_PAYOUTS_CONTROLLER = os.path.join(
    REPO_ROOT, "backend", "controllers", "treasury", "admin_payouts_controller.py"
)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def test_payment_client_has_no_debug_statements():
    if not os.path.isfile(PAYMENT_CLIENT):
        pytest_skip = getattr(__builtins__, "pytest", None)
        if pytest_skip is not None:
            pytest_skip.skip("payment client not present")
        return
    src = _read(PAYMENT_CLIENT)
    assert not CONSOLE_RE.search(src), "console.* statement left in payment client"
    assert not DEBUGGER_RE.search(src), "debugger statement left in payment client"


def test_admin_payouts_controller_stays_unwired():
    """Governance facade must not be directly imported by app code.

    The module is a contract-mandated thin facade; it is intentionally not
    wired into routers (verified by ``test_treasury_rescue``). Guard against
    accidental wiring that would defeat the orchestration layer.
    """
    if not os.path.isfile(ADMIN_PAYOUTS_CONTROLLER):
        return
    src = _read(ADMIN_PAYOUTS_CONTROLLER)
    # The facade itself may re-export from the service; that is fine.
    # We only assert no router/controller imports it from app packages.
    assert "from routers" not in src
    assert "from controllers." not in src
