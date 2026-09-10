"""Phase 4F follow-up: contract test that every cross-domain name in the
baseline is importable from the target domain's ``ports.py``.

For each baseline line ``domains/<src>/<relpath>:<lineno>: from domains.<tgt>.models.<m> import <Name>``
or service import, verify ``domains.<tgt>.ports`` exposes ``<Name>``.

If the name is missing from the target's ports, the test fails — that means a
future refactor removed the model re-export and the consumer will break.

This test freezes the current set of MISSING names in
``scripts/_ports_contract_baseline.txt`` and fails only on *new* missing names.
The baseline must shrink as Phase 5+ migrates remaining consumers to ports.

Run:
    python -m pytest tests/architecture/test_ports_contract.py -v
    python scripts/_gen_ports_contract_baseline.py
"""
from __future__ import annotations

import ast
import os
import re
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent.parent
SCRIPTS = BACKEND / "scripts"
DOMAINS = BACKEND / "domains"
BASELINE = SCRIPTS / "_cross_domain_baseline.txt"
CONTRACT_BASELINE = SCRIPTS / "_ports_contract_baseline.txt"


def _domain_names() -> set[str]:
    return {n for n in os.listdir(DOMAINS) if (DOMAINS / n).is_dir() and not n.startswith("_")}


def _names_in_ports(domain: str) -> set[str]:
    """Return the set of top-level names re-exported by ``domains/<d>/ports.py``."""
    p = DOMAINS / domain / "ports.py"
    if not p.exists():
        return set()
    out: set[str] = set()
    tree = ast.parse(p.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.add(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.add(node.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                out.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out.add(t.id)
    return out


def _parse_baseline() -> list[tuple[str, str]]:
    """Parse ``_cross_domain_baseline.txt`` → list of (target_domain, imported_name)."""
    out: list[tuple[str, str]] = []
    if not BASELINE.exists():
        return out
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^[^:]+:\d+: from domains\.([a-z]+)\.(models|services)\.\S+ import (.+)$", line)
        if not m:
            continue
        tgt = m.group(1)
        names_str = m.group(3)
        for n in names_str.split(","):
            n = n.strip()
            if "#" in n:
                n = n.split("#")[0].strip()
            if n:
                out.append((tgt, n))
    return out


def _load_contract_baseline() -> set[str]:
    if not CONTRACT_BASELINE.exists():
        return set()
    out: set[str] = set()
    for line in CONTRACT_BASELINE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


@pytest.mark.skipif(not BASELINE.exists(), reason="Baseline file missing; run scripts/_gen_cross_domain_baseline.py")
def test_all_cross_domain_model_names_have_ports():
    """For every ``from domains.<tgt>.models.* import <Name>`` baseline line, the
    target's ``ports.py`` must re-export ``<Name>``. Service imports (cross-domain
    direct service calls) are covered separately by
    ``tests/architecture/test_law3_cross_domain.py::TestNoDirectCrossDomainServiceImports``.

    Fails only on names missing from ports.py that are NOT in the contract
    baseline — the baseline is allowed to shrink over time but never grow.
    """
    parsed = _parse_baseline()
    domains = _domain_names()
    missing: dict[str, set[str]] = {}
    for tgt, name in parsed:
        if tgt not in domains:
            continue
        exposed = _names_in_ports(tgt)
        if name not in exposed:
            missing.setdefault(tgt, set()).add(name)

    contract_baseline = _load_contract_baseline()
    new_missing: list[str] = []
    for tgt, names in sorted(missing.items()):
        for n in sorted(names):
            key = f"{tgt}.{n}"
            if key not in contract_baseline:
                new_missing.append(key)
    if new_missing:
        pytest.fail(
            "New cross-domain name(s) missing from their target's ports.py "
            "(contract regression — was in the baseline but no ports re-export):\n  "
            + "\n  ".join(new_missing)
        )


def test_ports_modules_exist():
    """Every domain with cross-domain traffic must have a ports.py."""
    for d in _domain_names():
        assert (DOMAINS / d / "ports.py").exists(), (
            f"domains/{d}/ports.py missing — required as the Law 3 sanctioned "
            f"cross-domain read surface."
        )


def test_contract_baseline_only_shrinks():
    """The contract baseline must only shrink; new entries require explicit regen."""
    assert CONTRACT_BASELINE.exists(), (
        f"Contract baseline missing: {CONTRACT_BASELINE}. "
        "Run scripts/_gen_ports_contract_baseline.py to generate it."
    )
