"""Baseline + scanner for routers that embed business logic.

A hand-written router "embeds business logic" when it imports the ``models``
layer (ORM/response models belong in services) or performs a SQLAlchemy write
(``commit``/``add``/``merge``/``flush``/``bulk_*``). The contract is
routers -> controllers -> services; routers must stay thin.

``_router_logic_baseline.txt`` freezes the current set of offending routers.
The architecture gate fails only on *new* offenders so the count can only
decrease. Regenerate the baseline (after an intentional migration) with::

    python tests/_gen_router_baseline.py
"""
from __future__ import annotations

import ast
import glob
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUTERS_DIR = os.path.join(BACKEND, "routers")
BASELINE_PATH = os.path.join(BACKEND, "tests", "_router_logic_baseline.txt")

# Unambiguous SQLAlchemy session write operations. ``add`` is narrowed: ``set.add``
# (dedup bookkeeping, common in routers) is excluded when the receiver is a locally
# declared ``set(...)`` variable.
DB_WRITE_METHODS = {
    "commit", "add_all", "merge", "flush",
    "bulk_save_objects", "bulk_insert_mappings",
    "bulk_update_mappings", "bulk_save",
}

# Never treated as an offending router (it is the generator, not a route surface).
GENERATOR_MODULE = "generated/auto_router.py"


def _local_set_names(func_node: ast.AST) -> set:
    names = set()
    for n in ast.walk(func_node):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            if getattr(n.value.func, "id", None) == "set" and isinstance(n.targets[0], ast.Name):
                names.add(n.targets[0].id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.value, ast.Call):
            if getattr(n.value.func, "id", None) == "set" and isinstance(n.target, ast.Name):
                names.add(n.target.id)
    return names


def _router_logic_flags(tree: ast.Module) -> tuple[bool, bool]:
    """Return (imports_models, db_write) for a router module."""
    imports_models = False
    db_write = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "models" or mod.startswith("models."):
                imports_models = True
        if isinstance(node, ast.Call):
            f = node.func
            attr = f.attr if isinstance(f, ast.Attribute) else ""
            if attr in DB_WRITE_METHODS:
                db_write = True
            elif attr == "add":
                recv = f.value
                recv_name = recv.id if isinstance(recv, ast.Name) else None
                if recv_name is None or recv_name not in _local_set_names(node):
                    db_write = True
    return imports_models, db_write


def is_generated(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as fh:
            return "AUTO-GENERATED" in fh.read(400)
    except Exception:
        return False


def scan_router_files():
    """Yield (relpath, imports_models, db_write) for every hand-written router."""
    for path in glob.glob(os.path.join(ROUTERS_DIR, "**", "*.py"), recursive=True):
        if os.path.basename(path) == "__init__.py":
            continue
        rel = os.path.relpath(path, ROUTERS_DIR).replace(os.sep, "/")
        if rel == GENERATOR_MODULE:
            continue
        if is_generated(path):
            continue
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        im, dw = _router_logic_flags(tree)
        yield rel, im, dw


def load_baseline() -> set:
    if not os.path.exists(BASELINE_PATH):
        return set()
    out = set()
    for line in open(BASELINE_PATH, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def regenerate():
    baseline = sorted(rel for rel, im, dw in scan_router_files() if im or dw)
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        fh.write("# Routers embedding business logic (import `models` or perform DB writes).\n")
        fh.write("# Baseline frozen by the architecture gate; the count must only DECREASE.\n")
        fh.write("# Regenerate with tests/_gen_router_baseline.py after an intentional migration.\n")
        fh.write("\n".join(baseline) + "\n")
    return baseline


if __name__ == "__main__":
    base = regenerate()
    print(f"Wrote {len(base)} baseline routers to {BASELINE_PATH}")
