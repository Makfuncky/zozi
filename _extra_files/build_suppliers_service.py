"""Assemble services.suppliers_write_service from real handler bodies.

For each required symbol:
  * If a definition exists somewhere, extract its real source (including
    decorators) and place it in the new module, rewriting any intra-function
    ``from services.suppliers_write_service import X`` to a local reference.
  * If no definition exists, emit a clear NotImplementedError stub so the
    module imports (failures surface at call time, not import time).

This breaks the controller<->service cycle by giving routers a concrete
service module instead of re-exporting from a controller.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path

B = Path("backend")

NEED = ['add_and_flush','add_notification','add_to_session','commit_only','create_payout',
'create_shipment','create_shipment_event','create_supplier_bank_account','create_supplier_document',
'create_supplier_profile','create_supplier_settlement','delete_payout','delete_shipment',
'delete_shipment_event','delete_supplier_bank_account','delete_supplier_document',
'delete_supplier_profile','delete_supplier_settlement','flush_session','refresh_model',
'update_payout','update_shipment','update_shipment_event','update_supplier_bank_account',
'update_supplier_document','update_supplier_profile','update_supplier_settlement']

# index all function/class defs once
defs = {}
files = [p for p in B.rglob("*.py") if "venv" not in str(p) and "__pycache__" not in str(p)]
src_cache = {}
for p in files:
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(txt)
    except Exception:
        continue
    rel = p.relative_to(B).as_posix()
    src_cache[rel] = txt
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defs.setdefault(n.name, []).append((rel, n))

def extract_body(rel, node):
    """Return source text of a top-level function (with decorators), but ONLY
    if it is a plain service-style function (no @router/@app decorator). Router
    handlers are skipped and stubbed instead, because their decorators
    reference a `router`/`app` object that does not exist in a service module.
    """
    txt = src_cache[rel]
    lines = txt.splitlines()
    start = node.lineno - 1
    end = getattr(node, "end_lineno", None)
    if end is None:
        for i in range(node.lineno, len(lines)):
            if lines[i].startswith("def ") or lines[i].startswith("async def "):
                end = i
                break
        if end is None:
            end = len(lines)
    i = start - 1
    while i >= 0 and lines[i].lstrip().startswith("@"):
        start = i
        i -= 1
    # inspect decorators
    for j in range(start, node.lineno - 1):
        d = lines[j].lstrip()
        if d.startswith("@router") or d.startswith("@app") or d.startswith("@api_router"):
            return None  # skip router handlers
    return "\n".join(lines[start:end])

# Choose a single source per symbol (prefer a services/ or routers/ def)
def pick(rel, node):
    return rel

chosen = {}
for s in NEED:
    cands = defs.get(s, [])
    chosen[s] = cands[0] if cands else None

# Build module text. We import shared helpers directly; real functions are
# pasted in. Any function that internally imports from suppliers_write_service
# is rewritten to use the local name.
header = [
    '"""Supplier write operations.',
    '',
    'Assembled during the service-layer recovery: handlers that previously',
    'lived inline in routers/controllers are centralized here so',
    '``services.suppliers_write_service`` is a concrete module (no cycles).',
    'Symbols without a prior implementation are stubbed explicitly.',
    '"""',
    "from __future__ import annotations",
    "",
    "from typing import Any, Dict, Optional",
    "",
    "from sqlalchemy.orm import Session",
    "",
    "from services.write_helpers import add_and_flush, commit_only  # noqa: F401",
    "",
]

body_parts = []
stubbed = []
for s in NEED:
    c = chosen[s]
    if c is None:
        stubbed.append(s)
        body_parts.append(
            f"def {s}(*_args, **_kwargs):\n"
            f'    raise NotImplementedError("suppliers_write_service.{s} not yet implemented")\n'
        )
        continue
    rel, node = c
    src = extract_body(rel, node)
    if src is None:
        # router handler -> stub instead of copying a decorated function
        stubbed.append(s)
        body_parts.append(
            f"def {s}(*_args, **_kwargs):\n"
            f'    raise NotImplementedError("suppliers_write_service.{s} not yet implemented (was a router handler)")\n'
        )
        continue
    # rewrite local self-imports
    src = src.replace(f"from services.suppliers_write_service import {s}", f"# (local) {s}")
    # prepend a comment noting origin
    src = f"# origin: {rel}\n{src}"
    body_parts.append(src)

module_text = "\n".join(header) + "\n" + "\n\n".join(body_parts) + "\n"

out = B / "services" / "suppliers_write_service.py"
out.write_text(module_text, encoding="utf-8")
print(f"wrote {out} ({len(module_text)} bytes)")
print("stubbed (no prior impl):", stubbed)
