"""Baseline + scanner for routers that embed business logic.

A hand-written router "embeds business logic" when it imports the ``models``
layer (ORM/response models belong in services) or performs a SQLAlchemy write
(``commit``/``add``/``merge``/``flush``/``bulk_*``). The contract is
routers -> controllers -> services; routers must stay thin.

``_router_logic_baseline.txt`` freezes the current set of offending routers.
The architecture gate fails only on *new* offenders so the count can only
decrease. Regenerate the baseline (after an intentional migration) with::

    python scripts/_gen_router_baseline.py
"""
from __future__ import annotations

import ast
import glob
import os

def _find_backend_root() -> str:
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "modules")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BACKEND = _find_backend_root()
ROUTERS_DIR = os.path.join(BACKEND, "modules")
BASELINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_router_logic_baseline.txt")

# Unambiguous SQLAlchemy session write operations. ``add`` is narrowed: in-memory
# ``set.add`` bookkeeping (e.g. WebSocket connection managers, dedup lists) is NOT a
# DB write and is excluded. A receiver is treated as an in-memory set when it is a name
# bound to ``set(...)`` (module- or function-local), an inline ``set().add(...)``, or an
# attribute/subscript chain rooted at ``self._*`` (e.g. ``self._rooms...add``,
# ``self._user_info[uid]["rooms"].add``). A chain that mentions a session name
# (``db``/``session``/...) is still treated as a real DB write and is NOT excluded.
DB_WRITE_METHODS = {
    "commit", "add_all", "merge", "flush",
    "bulk_save_objects", "bulk_insert_mappings",
    "bulk_update_mappings", "bulk_save",
}

# Names that almost always denote a SQLAlchemy session (real DB write target).
SESSION_NAMES = {"db", "session", "sess", "dbsession", "db_session"}

# Never treated as an offending router (it is the generator, not a route surface).
GENERATOR_MODULE = "generated/auto_router.py"


def _set_names_in_scope(tree: ast.AST) -> set:
    """Names bound to a ``set(...)`` constructor within the given scope."""
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            if getattr(n.value.func, "id", None) == "set" and isinstance(n.targets[0], ast.Name):
                names.add(n.targets[0].id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.value, ast.Call):
            if getattr(n.value.func, "id", None) == "set" and isinstance(n.target, ast.Name):
                names.add(n.target.id)
    return names


def _subtree_has_set_constructor(node) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "set":
            return True
    return False


def _receiver_is_in_memory_set(recv, module_sets, local_sets) -> bool:
    """True when ``.add()`` is called on an in-memory set rather than a DB session."""
    if isinstance(recv, ast.Name):
        return recv.id in module_sets or recv.id in local_sets
    # A receiver that creates/returns a set (e.g. ``set()``, ``x.setdefault(k, set())``,
    # ``set().union(...)``) is in-memory bookkeeping, not a DB write.
    if _subtree_has_set_constructor(recv):
        return True
    if isinstance(recv, (ast.Attribute, ast.Subscript)):
        ids = set()
        cur = recv
        while isinstance(cur, ast.Attribute):
            ids.add(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            ids.add(cur.id)
        if ids & SESSION_NAMES:
            return False
        return True
    return False


def _contains_identity(container, target) -> bool:
    for child in ast.walk(container):
        if child is target:
            return True
    return False


def _local_sets_for(call, module_sets, func_set_map) -> set:
    sets = set(module_sets)
    for fn, fsets in func_set_map.items():
        if _contains_identity(fn, call):
            sets |= fsets
    return sets


def _router_logic_flags(tree: ast.Module) -> tuple[bool, bool]:
    """Return (imports_models, db_write) for a router module."""
    imports_models = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "models" or mod.startswith("models."):
                imports_models = True

    module_sets = _set_names_in_scope(tree)
    func_set_map = {
        fn: _set_names_in_scope(fn)
        for fn in ast.walk(tree)
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    db_write = False
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        f = call.func
        attr = f.attr if isinstance(f, ast.Attribute) else ""
        if attr in DB_WRITE_METHODS:
            db_write = True
        elif attr == "add":
            local_sets = _local_sets_for(call, module_sets, func_set_map)
            if not _receiver_is_in_memory_set(f.value, module_sets, local_sets):
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
        fh.write(    "# Regenerate with scripts/_gen_router_baseline.py after an intentional migration.\n")
        fh.write("\n".join(baseline) + "\n")
    return baseline


if __name__ == "__main__":
    base = regenerate()
    print(f"Wrote {len(base)} baseline routers to {BASELINE_PATH}")
