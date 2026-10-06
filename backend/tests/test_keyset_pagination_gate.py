"""Keyset pagination gate (B6 / R6, 100Ks-scale readiness).

Hot, high-cardinality list endpoints must seek via ``keyset_offset_window``
instead of SQL ``OFFSET``. This is a runnable regression guard (run:
``pytest tests/test_keyset_pagination_gate.py -q``).

Scope: ``domains/suppliers/services`` — the first domain migrated to keyset.
Any ``.offset(`` call there must appear inside a function that is explicitly
frozen in OFFSET_ALLOWLIST (a justified case that cannot derive sort keys from
a scalar select). New ``.offset(`` on a hot list fails the build until it is
either migrated to ``keyset_offset_window`` or added to the allowlist with a
reason. As more domains are migrated, extend SCOPE_DIRS.
"""
from __future__ import annotations

import ast
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Domain service dirs under active keyset migration. Add here as migration grows.
SCOPE_DIRS = [
    os.path.join(BACKEND, "domains", "suppliers", "services"),
]

# (relative path from BACKEND, enclosing function name) -> reason it is allowed
# to keep a bare ``.offset(``. These are the ONLY accepted OFFSET users; the
# count must not grow without an explicit, reasoned addition.
OFFSET_ALLOWLIST = {
    (
        "domains/suppliers/services/orders/supplier_orders.py",
        "get_supplier_orders",
    ): "scalar-select query (order_id-only) cannot derive sort columns for keyset; refactor to entity select before migrating",
}


def _iter_py(scope: str):
    for dirpath, _, files in os.walk(scope):
        for fn in files:
            if fn.endswith(".py") and fn != "__init__.py":
                yield os.path.join(dirpath, fn)


def _function_for_node(tree: ast.Module, target: ast.AST):
    """Return the name of the enclosing function/method for ``target``."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is target:
                    return node.name
    return "<module>"


def test_no_new_offset_on_hot_lists():
    """Every ``.offset(`` in scope must be in OFFSET_ALLOWLIST."""
    offenders = []
    for path in _iter_py_multi():
        rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError as e:
            offenders.append(f"{rel}: syntax error: {e}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "offset":
                    func = _function_for_node(tree, node)
                    key = (rel, func)
                    if key not in OFFSET_ALLOWLIST:
                        offenders.append(f"{rel}: .offset() in '{func}' (not allowlisted)")
    assert not offenders, (
        "Found .offset() pagination on a hot list that is not in the keyset "
        "allowlist (B6/R6 100Ks seek path). Migrate to keyset_offset_window, or "
        "add a reasoned entry to OFFSET_ALLOWLIST. Offenders:\n  "
        + "\n  ".join(sorted(offenders))
    )


def _iter_py_multi():
    for scope in SCOPE_DIRS:
        if os.path.isdir(scope):
            yield from _iter_py(scope)


def test_allowlist_entries_still_present():
    """Guard against drift: every allowlisted entry must still be a real .offset()
    usage, so the allowlist cannot silently freeze a non-existent exception."""
    live = set()
    for path in _iter_py_multi():
        rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "offset":
                    live.add((rel, _function_for_node(tree, node)))
    missing = [k for k in OFFSET_ALLOWLIST if k not in live]
    assert not missing, (
        "OFFSET_ALLOWLIST entries no longer correspond to a live .offset() call; "
        "remove the stale entry(ies):\n  " + "\n  ".join(f"{p}:{f}" for p, f in missing)
    )


def test_allowlist_paths_resolve_to_real_files():
    """Guard against stale allowlist paths: every entry must point to a real file."""
    bad = []
    for (rel_path, _func), _reason in OFFSET_ALLOWLIST.items():
        abs_path = os.path.join(BACKEND, rel_path)
        if not os.path.isfile(abs_path):
            bad.append(rel_path)
    assert not bad, (
        "OFFSET_ALLOWLIST contains paths that do not resolve to real source files; "
        "fix the stale path(es):\n  " + "\n  ".join(bad)
    )


def test_offset_implies_limit():
    """Every .offset() call in scope must be paired with a .limit() in the same function."""
    offenders = []
    for path in _iter_py_multi():
        rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "offset":
                    func = _function_for_node(tree, node)
                    fn_node = next(
                        (n for n in ast.walk(tree)
                         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                         and n.name == func),
                        None,
                    )
                    if fn_node is None:
                        continue
                    has_limit = any(
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "limit"
                        for child in ast.walk(fn_node)
                    )
                    if not has_limit:
                        offenders.append(f"{rel}: .offset() in '{func}' has no paired .limit()")
    assert not offenders, (
        "Found .offset() without a paired .limit() — unbounded offset queries can "
        "return an entire table. Fix:\n  " + "\n  ".join(sorted(offenders))
    )
