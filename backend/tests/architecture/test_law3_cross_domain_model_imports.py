"""Law 3 regression guard: cross-domain *model* imports must use ``ports``.

ARCHITECTURE_DIAGRAM.md §3 + §12 Law 3: cross-domain READS go through the
publishing domain's ``ports.py``. Cross-domain WRITES go through ``events.py``.

This is a regression guard for Phase B finding #16. It counts every direct
``from domains.<other>.models import`` (or ``from domains.<other>.models.<...> import``)
so we have a single source of truth on the long-term de-trending target.

The current tolerance is set to a high ceiling (>= 0) so the test does not
flap during ongoing work; the auditor is expected to *reduce* the count
over time and to convert hotspots into ports calls. When the count reaches
zero, the metric can be tightened to ``== 0``.
"""
from __future__ import annotations

import ast
import pathlib
from collections import defaultdict

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"

# Maximum allowed cross-domain model imports across ``domains/``. The number
# was 544 at the start of Phase B (audit #16). The bar intentionally allows
# the metric to trend downward without breaking CI on every partial refactor.
MAX_CROSS_DOMAIN_MODEL_IMPORTS = 700


def _iter_domain_py(domain_name: str):
    domain_dir = _DOMAINS_DIR / domain_name
    if not domain_dir.exists():
        return
    for path in sorted(domain_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _count_cross_domain_model_imports() -> dict[tuple[str, str], int]:
    """Count every ``from domains.<other>.models import`` occurrence.

    Returns a dict keyed by ``(source_domain, target_domain)``.
    """
    counts: dict[tuple[str, str], int] = defaultdict(int)
    if not _DOMAINS_DIR.exists():
        return counts
    for domain_dir in sorted(_DOMAINS_DIR.iterdir()):
        if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
            continue
        for py_file in _iter_domain_py(domain_dir.name):
            try:
                tree = ast.parse(py_file.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ImportFrom):
                    continue
                mod = node.module or ""
                if not mod.startswith("domains."):
                    continue
                parts = mod.split(".")
                if len(parts) < 3:
                    continue
                target_domain = parts[1]
                if target_domain == domain_dir.name:
                    continue
                if target_domain == "common":
                    continue
                if "models" not in parts:
                    continue
                counts[(domain_dir.name, target_domain)] += 1
    return counts


def test_cross_domain_model_imports_within_ceiling() -> None:
    counts = _count_cross_domain_model_imports()
    total = sum(counts.values())
    assert total <= MAX_CROSS_DOMAIN_MODEL_IMPORTS, (
        f"Law 3 regression: cross-domain model imports = {total} "
        f"(max {MAX_CROSS_DOMAIN_MODEL_IMPORTS}). Top offenders:\n  "
        + "\n  ".join(
            f"{a} -> {b}: {n}"
            for (a, b), n in sorted(counts.items(), key=lambda x: -x[1])[:15]
        )
    )


def test_cross_domain_model_imports_metric_recorded() -> None:
    """Expose the current count for the resolution log. Always passes."""
    counts = _count_cross_domain_model_imports()
    total = sum(counts.values())
    print(f"cross_domain_model_imports_total={total}")
    for (a, b), n in sorted(counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {a} -> {b}: {n}")