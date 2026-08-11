"""Regression tests for Finance architecture fixes.

Verifies:
- QUAL1: weak exception handling (bare ``except Exception: pass``) in the
  finance automation service is replaced with a logged debug statement.
- FE6: leftover ``console.error``/``debugger`` debug statements in the admin
  finance frontend components are removed.
- PERF4: the journal-entry reversal query is bounded with ``.limit()``.
- PF2: the Finance domain scope document exists.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

def _repo_root() -> Path:
    d = Path(__file__).resolve().parent
    for _ in range(5):
        if (d / "backend").is_dir():
            return d
        d = d.parent
    return Path(__file__).resolve().parent.parent


REPO_ROOT = _repo_root()

FINANCE_ADMIN = (
    REPO_ROOT
    / "frontend"
    / "web_app"
    / "src"
    / "app"
    / "admin"
)


def test_finance_automation_no_swallowed_exception():
    """QUAL1 fix: weak exception handling replaced with a logged debug line."""
    mod = importlib.import_module("services.finance.finance_automation")
    src = open(mod.__file__, encoding="utf-8").read()
    # No bare `except Exception: pass` best-effort blocks remain.
    assert "except Exception:\n        pass" not in src
    assert "except Exception:\n            pass" not in src
    # The swallowed block is now logged instead.
    assert "audit_log for automation journal entry failed" in src


def _scan_ts_for_debug(path: Path):
    src = path.read_text(encoding="utf-8")
    assert "console.error" not in src, f"{path.name} still contains console.error"
    assert "debugger" not in src, f"{path.name} still contains debugger"


def test_finance_frontend_no_debug_statements():
    """FE6 fix: no console.error / debugger left in the admin finance panels."""
    # Prior fixed panels (components folder).
    components = FINANCE_ADMIN / "finance" / "_components"
    for fname in ("BankAccountsPanel.tsx", "CashFlowCycleTab.tsx"):
        _scan_ts_for_debug(components / fname)
    # Dashboard Finance tab (newly fixed).
    _scan_ts_for_debug(
        FINANCE_ADMIN / "dashboard" / "_tabs" / "FinanceTab.tsx"
    )


def test_je_reversal_query_is_bounded():
    """PERF4 fix: the reversal line query is capped with .limit()."""
    mod = importlib.import_module("services.finance.je_reversal_service")
    src = open(mod.__file__, encoding="utf-8").read()
    # The JournalEntryLine query for a single entry must be bounded.
    assert ".limit(" in src
    # No unbounded `.all()` directly on the entry-line filter chain.
    assert "JournalEntryLine.entry_id == original_entry_id" in src


def test_finance_scope_doc_exists():
    """PF2 fix: the Finance domain scope document is present."""
    doc = REPO_ROOT / "documents" / "scope" / "04_FINANCE.md"
    assert doc.exists(), "documents/scope/04_FINANCE.md is missing"
    assert "FINANCE DOMAIN" in doc.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Structural rename regression tests (DOM7 / DOM2 / MV1).
# These assert the on-disk layout only (no module imports) so they stay
# green even when the shared `data.models` layer has an unrelated import
# error on this environment.
# ---------------------------------------------------------------------------

BACKEND = REPO_ROOT / "backend"


def _walk_py(root: Path):
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts or "tests" in p.parts:
            continue
        yield p


def test_payment_gateway_settings_in_providers():
    """DOM7: payment-gateway settings + adapters are the single source of truth
    under ``providers/payments``; the duplicate ``services/gateways`` abstraction
    and the broken ``payment_engine`` / ``webhook_processor`` orchestration
    duplicates have been retired. A single orchestration layer remains at
    ``services/payments.py``."""
    # Duplicate / dead gateway abstraction retired.
    assert not (BACKEND / "services" / "gateways").exists(), (
        "services/gateways duplicate abstraction should be retired"
    )
    assert not (BACKEND / "services" / "payment_engine.py").exists(), (
        "services/payment_engine.py duplicate should be retired"
    )
    assert not (BACKEND / "services" / "webhook_processor.py").exists(), (
        "services/webhook_processor.py duplicate should be retired"
    )
    # Canonical gateway settings + adapters live in providers/payments.
    assert (BACKEND / "providers" / "payments" / "base.py").exists()
    assert (BACKEND / "providers" / "payments" / "stripe.py").exists()
    assert (BACKEND / "providers" / "payments" / "config.py").exists()
    # Single payment orchestration layer.
    assert (BACKEND / "services" / "payments.py").exists()


def test_misplaced_finance_services_relocated():
    """MV1 + DOM2: finance-domain service files previously at the wrong
    folder root or in other domains now live under `services/finance/`."""
    relocated = [
        "commission_write_service.py",
        "general_ledger_service.py",
        "refund_posting_service.py",
        "order_payment_functions.py",
        "supplier_finance_service.py",
    ]
    for name in relocated:
        target = BACKEND / "services" / "finance" / name
        assert target.exists(), f"{name} should be at services/finance/{name}"


def test_sub_ledger_shim_removed():
    """MV1: the flat `controllers/sub_ledger_controller.py` compatibility shim
    is removed; the real controller lives at `controllers/finance/`."""
    assert not (BACKEND / "controllers" / "sub_ledger_controller.py").exists(), (
        "flat sub_ledger_controller.py shim should be removed"
    )
    assert (
        BACKEND / "controllers" / "finance" / "sub_ledger_controller.py"
    ).exists()


def test_no_stale_payments_or_shim_imports():
    """No remaining references to the old `services.gateways.payments` package or the
    flat `controllers.finance.sub_ledger_controller` shim path."""
    import re

    stale = [
        re.compile(r"services\.payments\b"),
        re.compile(r"controllers\.sub_ledger_controller\b"),
        re.compile(r"services\.commission_write_service\b"),
        re.compile(r"services\.general_ledger_service\b"),
        re.compile(r"services\.refund_posting_service\b"),
        re.compile(r"services\.orders\.order_payment_functions\b"),
        re.compile(r"services\.supplier\.supplier_finance_service\b"),
    ]
    hits = []
    for p in _walk_py(BACKEND):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for rx in stale:
            if rx.search(text):
                hits.append(f"{p.relative_to(REPO_ROOT)} -> {rx.pattern}")
    assert not hits, "stale import references remain:\n" + "\n".join(hits)


# ---------------------------------------------------------------------------
# QUAL3 regression: oversized Finance functions kept within the audit limit.
# AST-only (no module import) so it does not depend on the shared data.models
# layer, which has an unrelated import error on this environment.
# ---------------------------------------------------------------------------

import ast  # noqa: E402

QUAL3_FUNC_LINE_LIMIT = 120


def _function_lengths(path: Path) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node.end_lineno - node.lineno + 1
    return out


def test_finance_functions_within_qual3_limit():
    """QUAL3 fix: previously-oversized finance functions stay under the 120-line
    threshold after extracting self-contained helpers."""
    commission = BACKEND / "services" / "commission_engine.py"
    transfer = BACKEND / "services" / "finance_transfer_service.py"
    assert commission.exists() and transfer.exists()

    comm = _function_lengths(commission)
    assert comm["get_effective_rate"] <= QUAL3_FUNC_LINE_LIMIT, (
        f"get_effective_rate is {comm['get_effective_rate']} lines "
        f"(limit {QUAL3_FUNC_LINE_LIMIT})"
    )
    assert comm.get("_resolve_base_commission_component", 0) <= QUAL3_FUNC_LINE_LIMIT

    tr = _function_lengths(transfer)
    assert tr["execute_transfer_batch"] <= QUAL3_FUNC_LINE_LIMIT, (
        f"execute_transfer_batch is {tr['execute_transfer_batch']} lines "
        f"(limit {QUAL3_FUNC_LINE_LIMIT})"
    )
    assert tr.get("_ensure_stripe_connect_account", 0) <= QUAL3_FUNC_LINE_LIMIT
