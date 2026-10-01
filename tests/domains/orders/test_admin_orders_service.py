"""Tests for admin_orders_service exception logging (Law 58).

Contract: _audit/resolver/contracts/admin-orders-service.md
Finding fixed:
  LAW-058 — Silent exceptions: except blocks without logging
"""
from __future__ import annotations

import ast
from pathlib import Path


# ── Paths ─────────────────────────────────────────────────────────────────────

SERVICE_PATH = (
    Path(__file__).resolve().parents[3]
    / "backend"
    / "domains"
    / "orders"
    / "services"
    / "admin_orders_service.py"
)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_exception_logging():
    """Every except block must log at minimum DEBUG level (Law 58)."""
    source = SERVICE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            has_logging = any(
                isinstance(n, ast.Call)
                and isinstance(getattr(n, "func", None), ast.Attribute)
                and n.func.attr in (
                    "debug",
                    "exception",
                    "warning",
                    "error",
                    "critical",
                    "log",
                )
                for n in ast.walk(node)
            )
            assert has_logging, (
                f"except block at line {node.lineno} has no logging call"
            )
