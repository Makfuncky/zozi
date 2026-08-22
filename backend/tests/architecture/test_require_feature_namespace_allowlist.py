"""B4 / R5 follow-up - namespace-wildcard change-control for require_feature.

The bare catch-all ban lives in test_require_feature_no_star.py. This test adds
the *second* half of B4/R5: any NAMESPACE wildcard used in require_feature
(e.g. "admin.*") must be declared in ``rbac.catalog.FEATURE_NAMESPACES`` (the
single source of truth). Adding a new namespace wildcard without declaring it
fails CI, forcing a review and preventing silent RBAC drift. The reverse is also
checked: a declared namespace that is no longer used anywhere is flagged as dead.

Run: pytest tests/architecture/test_require_feature_namespace_allowlist.py -q
"""
from __future__ import annotations

import os
import ast
import sys
import functools

import pytest

_ROOT = os.path.dirname(os.path.abspath(__file__))
while True:
    if os.path.exists(os.path.join(_ROOT, "main.py")) and os.path.isdir(os.path.join(_ROOT, "modules")):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent

# Ensure the backend package root is importable regardless of how pytest
# resolves rootdir/conftest (otherwise `import rbac` fails and the gates below
# silently pass vacuously on an empty fallback frozenset).
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import rbac.catalog as _catalog  # noqa: E402

_EXCLUDES = {"venv", ".git", "__pycache__", "_extra_files", "tests"}


def _is_require_feature(node):
    """True iff `node` is a call to require_feature (Name or Attribute)."""
    if not isinstance(node, ast.Call):
        return False
    f = node.func
    if isinstance(f, ast.Name):
        return f.id == "require_feature"
    if isinstance(f, ast.Attribute):
        return f.attr == "require_feature"
    return False


# Sanctioned namespace wildcards are the single source of truth declared in
# ``rbac/catalog.py`` (the ``FEATURE_NAMESPACES`` frozenset). Previously this
# list was hardcoded here and was polluted by docstring false-positives
# (``country.*`` / ``finance.*`` / ``orders.*`` appear only in feature-doc
# comments, never as real require_feature calls). Consuming the catalog keeps
# one authoritative declaration and lets the B4/R5 gate detect silent drift.
ALLOWLIST = {f"{n}.*" for n in _catalog.FEATURE_NAMESPACES}


@functools.cache
def _collect_namespace_wildcards():
    seen = set()
    for dirpath, dirnames, filenames in os.walk(_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDES]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    src = fh.read()
            except OSError:
                continue
            # Cheap pre-filter: only files that actually mention require_feature
            # can contain a namespace-wildcard call. Skips ast.parse on the
            # ~80% of the tree that is irrelevant and keeps this gate fast.
            if "require_feature" not in src:
                continue
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            # Only REAL call nodes count - docstring/comment examples of the
            # forbidden pattern (e.g. require_feature("X.*")) are ignored.
            for n in ast.walk(tree):
                if _is_require_feature(n) and n.args:
                    arg = n.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "*" in arg.value:
                        seen.add(arg.value)
    return seen

def test_namespace_wildcards_sanctioned():
    found = _collect_namespace_wildcards()
    unsanctioned = found - ALLOWLIST
    assert not unsanctioned, (
        "Unsanctioned require_feature namespace wildcard(s) found:\n"
        + "\n".join(sorted(unsanctioned))
        + "\nDeclare it in rbac.catalog.FEATURE_NAMESPACES (the single source of truth)."
    )

def test_all_declared_namespaces_used():
    """No dead namespace declarations - every declared wildcard is in active use."""
    found = _collect_namespace_wildcards()
    dead = ALLOWLIST - found
    assert not dead, (
        "Declared feature namespace wildcard(s) are not used anywhere:\n"
        + "\n".join(sorted(dead))
        + "\nRemove from rbac.catalog.FEATURE_NAMESPACES or add a router that uses it."
    )


def _known_atoms():
    """Union of every authoritative feature-atom registry.

    ``rbac.catalog`` aggregates ``domains/*/features.py`` (the Law-4 single
    source of truth for *domain* atoms). ``admin`` is a *module* namespace whose
    atoms are defined in ``governance/services/effective_permissions.py``
    (``HR_PERMISSION_MAP``) - a second, also-claimed "single source of truth".
    A declared namespace is "backed" if it has atoms in EITHER registry, so the
    gate does not raise a false positive on ``admin`` while still catching a
    genuinely phantom namespace (declared but with zero atoms anywhere).
    """
    atoms = set()
    try:
        atoms.update(_catalog.all_features())
    except Exception:
        pass
    try:
        from domains.governance.services.effective_permissions import HR_PERMISSION_MAP
        atoms.update(HR_PERMISSION_MAP.keys())
    except Exception:
        pass
    return atoms


def test_all_declared_namespaces_have_atoms():
    """Every declared namespace wildcard maps to a real feature subtree.

    A namespace granted via ``require_feature("X.*")`` only resolves when at
    least one atom ``X.<something>`` exists in an authoritative registry. A
    declared namespace with zero atoms in ANY registry is a phantom grant
    (authorizes nothing) and almost certainly a misconfigured feature subtree.
    This is the B4/R5 follow-up that ties each sanctioned wildcard back to a
    real backing atom set.
    """
    atoms = _known_atoms()
    empty = [
        n for n in sorted(_catalog.FEATURE_NAMESPACES)
        if not any(a == f"{n}.*" or a.startswith(f"{n}.") for a in atoms)
    ]
    assert not empty, (
        "Declared feature namespace(s) have no feature atoms in any registry:\n"
        + "\n".join(f"{n}.*" for n in empty)
        + "\nAdd the missing atoms to domains/*/features.py (or the governance "
        + "HR_PERMISSION_MAP) or remove the declaration from "
        + "rbac.catalog.FEATURE_NAMESPACES."
    )
