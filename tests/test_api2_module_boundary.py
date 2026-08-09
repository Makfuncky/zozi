"""Regression guard for the API2 (public-API stability) audit finding.

The API2 rule flags a private symbol (name starts with ``_`` and is not a
dunder) that is *used* in a module different from the one that defines it.  Such
usages are either:

  * UNDEFINED  - the external module reads/calls the name without ever binding
                 or importing it -> a latent ``NameError`` at runtime, or
  * IMPORTED   - the external module does ``from <defining module> import _name``
                 -> a genuine private-symbol leak across the module boundary.

Both are real boundary violations. LOCAL (the external module defines its own
same-named symbol), ATTRIBUTE (only ever seen as ``obj._name``) and DUNDER
names are false positives and intentionally ignored here.

This test reuses the architecture audit's own symbol index so it passes exactly
when the audit would report zero genuine cross-boundary private-symbol leaks.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from collections import defaultdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]  # tests/ -> zozi (repo root)
AUDIT = REPO / "scripts" / "system_trackers" / "system_architecture_audit.py"


def _load_audit():
    spec = importlib.util.spec_from_file_location("_zozi_arch_audit_api2", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _Facts:
    def __init__(self, tree: ast.Module):
        self.bound: set[str] = set()
        self.from_imports: dict[str, str] = {}
        self.name_loads: set[str] = set()
        self.attr_loads: set[str] = set()
        self.has_star = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self.bound.add(node.name)
            elif isinstance(node, ast.arg):
                self.bound.add(node.arg)
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, (ast.Store, ast.Del)):
                    self.bound.add(node.id)
                else:
                    self.name_loads.add(node.id)
            elif isinstance(node, ast.Attribute):
                self.attr_loads.add(node.attr)
            elif isinstance(node, (ast.Global, ast.Nonlocal)):
                self.bound.update(node.names)
            elif isinstance(node, ast.ImportFrom):
                src = node.module or ""
                for a in node.names:
                    if a.name == "*":
                        self.has_star = True
                        continue
                    self.bound.add(a.asname or a.name)
                    self.from_imports[a.asname or a.name] = src
            elif isinstance(node, ast.Import):
                for a in node.names:
                    self.bound.add(a.asname or a.name.split(".")[0])


def _norm(m: str) -> str:
    return m[len("backend."):] if m.startswith("backend.") else m


def test_no_genuine_private_symbol_boundary_leaks():
    aud = _load_audit()
    eff = aud.load_rules(REPO, None)
    aud.ensure_required_ignore_dirs(eff)
    aud._ACTIVE_EFF = eff
    graph = aud.build_module_graph(REPO, eff)
    index = aud.build_symbol_index(REPO, eff, graph)

    facts: dict[str, _Facts] = {}
    for module, f in graph.modules.items():
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, ValueError, OSError):
            continue
        facts[module] = _Facts(tree)

    genuine = []
    for name, symbols in index.symbols.items():
        if not name.startswith("_") or (name.startswith("__") and name.endswith("__")):
            continue
        usages = index.symbol_usages.get(name, [])
        for sym in symbols:
            external = [
                (m, _l) for m, _l in usages
                if m != sym.module and not m.startswith(sym.module + ".")
            ]
            if not external:
                continue
            for m, _l in external:
                mf = facts.get(m)
                if mf is None:
                    continue
                src = mf.from_imports.get(name)
                if src is not None and _norm(src) == sym.module:
                    genuine.append((name, sym.module, m, "IMPORTED"))
                elif name in mf.name_loads and not mf.has_star and name not in mf.bound:
                    genuine.append((name, sym.module, m, "UNDEFINED"))

    if genuine:
        detail = "\n".join(f"  {n} ({c}) defined in {d}, used in {m}" for n, d, m, c in genuine)
        pytest.fail(
            f"{len(genuine)} genuine private-symbol boundary leak(s) remain:\n{detail}"
        )
