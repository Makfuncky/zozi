"""Generate the contract baseline of (target_domain, name) pairs that are
referenced cross-domain but not yet exposed via the target's ports.py.

The contract test fails on *new* entries in this baseline; the file must only
shrink over time.

Run after scripts/_gen_cross_domain_baseline.py.
"""
from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
SCRIPTS = BACKEND / "scripts"
DOMAINS = BACKEND / "domains"
BASELINE = SCRIPTS / "_cross_domain_baseline.txt"
CONTRACT_BASELINE = SCRIPTS / "_ports_contract_baseline.txt"


def _domain_names() -> set[str]:
    return {n for n in os.listdir(DOMAINS) if (DOMAINS / n).is_dir() and not n.startswith("_")}


def _names_in_ports(domain: str) -> set[str]:
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


def main() -> int:
    if not BASELINE.exists():
        print(f"ERROR: {BASELINE} not found. Run scripts/_gen_cross_domain_baseline.py first.")
        return 1
    names = _domain_names()
    missing: set[str] = set()
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^[^:]+:\d+: from domains\.([a-z]+)\.(models|services)\.\S+ import (.+)$", line)
        if not m:
            continue
        tgt = m.group(1)
        if tgt not in names:
            continue
        exposed = _names_in_ports(tgt)
        for n in m.group(3).split(","):
            n = n.strip()
            if "#" in n:
                n = n.split("#")[0].strip()
            if n and n not in exposed:
                missing.add(f"{tgt}.{n}")
    CONTRACT_BASELINE.write_text(
        "# Contract baseline: target_domain.name pairs that are referenced\n"
        "# cross-domain (in _cross_domain_baseline.txt) but NOT yet exposed\n"
        "# via the target's ports.py. The contract test fails only on\n"
        "# *new* entries; the file MUST only shrink.\n"
        "# Regenerate with scripts/_gen_ports_contract_baseline.py.\n\n"
        + "\n".join(sorted(missing)) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(missing)} contract-baseline entries to {CONTRACT_BASELINE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
