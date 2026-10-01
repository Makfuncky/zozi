"""Regression guard for the supplier_payouts W1 rescue.

W1 contract: routers must not own DB writes (db.add/commit/...); the
service layer owns the transaction. This test is structural (AST-only)
so it runs without a DB engine and is not blocked by unrelated mapper bugs.
"""
import ast
import os

import pytest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROUTER = os.path.join(BACKEND, "routers", "supplier_payouts.py")
SERVICE = os.path.join(BACKEND, "services", "supplier", "supplier_payout_service.py")

SESSION_WRITES = {"add", "add_all", "commit", "flush", "delete", "merge", "begin_nested"}


def _session_write_calls(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            obj = node.func.value
            if isinstance(obj, ast.Name) and obj.id in {"db", "session", "sess", "s"}:
                if node.func.attr in SESSION_WRITES:
                    found.append(node.func.attr)
    return found


def test_router_has_no_session_writes():
    assert _session_write_calls(ROUTER) == [], "router must not write to DB (W1 violation)"


def test_service_owns_write():
    assert "commit" in _session_write_calls(SERVICE), "service must own the DB transaction"
