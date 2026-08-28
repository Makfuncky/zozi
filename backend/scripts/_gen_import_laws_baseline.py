"""Baseline + scanner for Law 1 (arrows point down only).

Law 1: ``modules -> domains -> infrastructure``. The platform layers below the
domain boundary must never statically import ``domains`` or ``modules``:

    kernel / infrastructure / providers / rbac   ->  must NOT import domains, modules
    domains                                     ->  must NOT import modules

Only *module-level* (static) imports are flagged. Lazily imported names that
live inside a function body (e.g. an import inside a ``try`` or a guard) are
excluded, because they do not create a hard dependency arrow at import time.

``_import_laws_baseline.txt`` freezes the current offenders. The architecture
gate fails only on *new* offenders so the debt can be chipped away safely,
one migration at a time. Regenerate the baseline after an intentional move::

    python scripts/_gen_import_laws_baseline.py
"""
from __future__ import annotations

import ast
import glob
import os

def _find_backend_root() -> str:
    """Walk up from this file to the backend root (contains main.py + modules/)."""
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.exists(os.path.join(d, "main.py")) and os.path.isdir(os.path.join(d, "modules")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # Fallback: scripts live at <backend>/tests/architecture/
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BACKEND = _find_backend_root()
BASELINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_import_laws_baseline.txt")

# Sanctioned upward reference: rbac/catalog.py aggregates every domain's
# features.py (Law 4). It MUST import domains, so it is excluded from the
# Law 1 debt baseline rather than frozen as a violation.
EXCLUDE_PATHS = {
    "rbac/catalog.py",
    # Sanctioned re-export shims (P6 merge/shim, no-delete policy): the canonical
    # implementation moved down into a domains/* module, and these infrastructure
    # files stay as thin backward-compat shims. They intentionally import domains
    # at module scope; the AST count is a backlog signal, not a per-edit gate.
    "infrastructure/utils/audit.py",
    "infrastructure/utils/common_asset_tracking.py",
    "infrastructure/utils/write_help.py",
    "infrastructure/utils/async_workers.py",
    "infrastructure/utils/upload_job_service.py",
    "infrastructure/utils/asset_tracking.py",
    "infrastructure/utils/image_ai_service.py",
    # Service registry: intentionally aggregates every domain's service modules
    # at module scope to wire them centrally. Like the shims above, it MUST
    # import domains, so it is excluded from the per-edit gate (AST debt signal).
    "infrastructure/service_registry.py",
    # DB seeder: loads domain models/engine to populate reference data; an
    # infrastructure script that must import domains (same sanctioned-shim rule).
    "infrastructure/database/seed_data.py",
}

# For each scanned layer root, the top-level modules it must NOT statically import.
FORBIDDEN: dict[str, set[str]] = {
    "kernel": {"domains", "modules"},
    "infrastructure": {"domains", "modules"},
    "providers": {"domains", "modules"},
    "rbac": {"domains", "modules"},
    "domains": {"modules"},
}


def _static_upward_imports(tree: ast.Module, forbidden: set[str]) -> bool:
    """True if the module imports a forbidden top-level package at module scope."""
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in forbidden:
                    return True
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.split(".")[0] in forbidden:
                return True
    return False


def scan_layer(layer: str):
    """Yield (relpath, forbidden_top_modules) for every offending module in a layer."""
    root = os.path.join(BACKEND, layer)
    if not os.path.isdir(root):
        return
    forbidden = FORBIDDEN[layer]
    for path in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
        if os.path.basename(path) == "__init__.py":
            continue
        rel = os.path.relpath(path, BACKEND).replace(os.sep, "/")
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        if _static_upward_imports(tree, forbidden):
            yield rel


def scan_all():
    for layer in FORBIDDEN:
        for rel in scan_layer(layer):
            if rel in EXCLUDE_PATHS:
                continue
            yield rel


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
    baseline = sorted(scan_all())
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        fh.write("# Static upward imports (Law 1: arrows point down only).\n")
        fh.write("# Baseline frozen by the architecture gate; the count must only DECREASE.\n")
        fh.write(    "# Regenerate with scripts/_gen_import_laws_baseline.py after an intentional move.\n")
        fh.write("\n".join(baseline) + "\n")
    return baseline


if __name__ == "__main__":
    base = regenerate()
    print(f"Wrote {len(base)} baseline offenders to {BASELINE_PATH}")
