"""Baseline + scanner for Law 3 (cross-domain direct imports).

Law 3: cross-domain *reads* go via ``domains/<d>/ports.py``; cross-domain
*writes* go via ``domains/<d>/events.py``. Any direct ``from domains.X.models``
or ``from domains.X.services`` import in a file living under ``domains/Y/``
(where ``X != Y``) is a Law 3 violation.

We freeze the current offenders in ``_cross_domain_baseline.txt`` and the
architecture gate fails only on *new* ones.

Sanctioned exceptions:
    - ``domains/<d>/ports.py``  — the Law 3 sanctioned cross-domain read surface.
    - ``domains/<d>/events.py`` — the Law 3 sanctioned cross-domain write surface.

Format of each baseline line:
    ``domains/<src_domain>/<relpath>:<lineno>: <import>``

Regenerate with:
    python scripts/_gen_cross_domain_baseline.py
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
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BACKEND = _find_backend_root()
BASELINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cross_domain_baseline.txt")
DOMAINS = os.path.join(BACKEND, "domains")

# Sanctioned cross-domain surface per Law 3.
EXCLUDE_FILES = {
    "ports.py",
    "events.py",
}


def _domain_names() -> set[str]:
    return {n for n in os.listdir(DOMAINS) if os.path.isdir(os.path.join(DOMAINS, n)) and not n.startswith("_")}


def _src_domain(rel: str, names: set[str]) -> str | None:
    parts = rel.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "domains" and parts[1] in names:
        return parts[1]
    return None


def _target_domain(mod: str, names: set[str]) -> str | None:
    parts = mod.split(".")
    if len(parts) >= 3 and parts[0] == "domains" and parts[1] in names and parts[2] in ("models", "services"):
        return parts[1]
    return None


def scan_cross_domain() -> list[str]:
    """Yield ``relpath:lineno: import`` strings for every cross-domain direct import."""
    out: list[str] = []
    names = _domain_names()
    for path in glob.glob(os.path.join(DOMAINS, "**", "*.py"), recursive=True):
        rel = os.path.relpath(path, BACKEND).replace("\\", "/")
        if os.path.basename(path) in EXCLUDE_FILES:
            continue
        sd = _src_domain(rel, names)
        if not sd:
            continue
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                t = _target_domain(node.module, names)
                if t and t != sd:
                    out.append(f"{rel}:{node.lineno}: from {node.module} import {', '.join(a.name for a in node.names)}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    t = _target_domain(alias.name, names)
                    if t and t != sd:
                        out.append(f"{rel}:{node.lineno}: import {alias.name}")
    return sorted(set(out))


def load_baseline() -> set[str]:
    if not os.path.exists(BASELINE_PATH):
        return set()
    out: set[str] = set()
    for line in open(BASELINE_PATH, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.add(line)
    return out


def regenerate() -> list[str]:
    lines = scan_cross_domain()
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        fh.write("# Cross-domain direct imports (Law 3: reads via ports.py, writes via events.py).\n")
        fh.write("# Baseline frozen by the architecture gate; the count must only DECREASE.\n")
        fh.write("# Regenerate with scripts/_gen_cross_domain_baseline.py after an intentional move.\n")
        fh.write("# Format: domains/<src>/<relpath>:<lineno>: <import>\n\n")
        for ln in lines:
            fh.write(ln + "\n")
    return lines


if __name__ == "__main__":
    lines = regenerate()
    print(f"Wrote {len(lines)} baseline offenders to {BASELINE_PATH}")
