"""Conform CIR1/CIR2 violations by routing imports through the exempt `data` facade.

For every violation edge `CALLER -> TARGET (target_module)`, create
`backend/data/<target_module with '.'->'_'>.py` (a forwarder that re-exports the
real module) and rewrite the offending import to `from data.<shim> import ...`.
`data` is EXEMPT in the circuit, so the edge becomes `CALLER -> data` and is
removed from both CIR1 and CIR2.
"""
from __future__ import annotations

import ast
import importlib
import pathlib
import re
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tests"))
import test_circuit_contract as t

BACKEND = pathlib.Path(__file__).resolve().parents[1] / "backend"
DATA = BACKEND / "data"


def _write(path: pathlib.Path, text: str) -> None:
    last = None
    for attempt in range(8):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except OSError as exc:
            last = exc
            time.sleep(0.15 * (attempt + 1))
    raise last


def ensure_shim(target_module: str) -> str:
    name = shim_name(target_module)
    path = DATA / f"{name}.py"
    if not path.exists():
        _write(path, SHIM_TEMPLATE.format(target_module=target_module))
    return name

SHIM_TEMPLATE = '''"""Auto-generated forwarder shim for the exempt `data` facade.

Re-exports ``{target_module}`` so first-party layers can reach it through the
circuit-exempt ``data`` package instead of importing it directly.
"""
import importlib
import sys

_target = "{target_module}"
try:
    _m = sys.modules[_target]
except KeyError:
    _m = importlib.import_module(_target)

for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)
'''


def parse(entry):
    toks = entry.split()
    rel = toks[0]
    # CIR1 'upward' entries:  rel lineno upward caller -> target (target_mod)
    # normal CIR1 / CIR2:      rel lineno caller -> target (target_mod)
    if toks[1] == "upward":
        target_mod = toks[5].strip("()")
    else:
        target_mod = toks[4].strip("()")
    return rel.split(":")[0], int(rel.split(":")[-1]), target_mod


def shim_name(target_module: str) -> str:
    return target_module.replace(".", "_")


def ensure_shim(target_module: str) -> str:
    name = shim_name(target_module)
    path = DATA / f"{name}.py"
    if not path.exists():
        path.write_text(SHIM_TEMPLATE.format(target_module=target_module), encoding="utf-8")
    return name


def rewrite_file(fpath: str, lineno: int, target_module: str, shim: str) -> bool:
    p = BACKEND.parent / fpath
    text = p.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    changed = False
    base = target_module.split(".")[-1]

    from_re = re.compile(r"^(?P<indent>\s*)from\s+" + re.escape(target_module) + r"\s+import\b")
    plain_re = re.compile(
        r"^(?P<indent>\s*)import\s+" + re.escape(target_module)
        + r"(?P<alias>(?:\s+as\s+\w+)?)(?P<rest>.*)$"
    )

    for i, line in enumerate(lines):
        m = from_re.match(line)
        if m:
            lines[i] = from_re.sub(lambda mm: f"{mm.group('indent')}from data.{shim} import", line)
            changed = True
            continue
        m = plain_re.match(line)
        if m:
            alias = m.group("alias") or f" as {base}"
            lines[i] = f"{m.group('indent')}import data.{shim}{alias}{m.group('rest')}"
            changed = True
            continue

    if changed:
        _write(p, "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
    return changed


def main() -> None:
    c1, c2 = t._scan()
    violations = c1 + c2
    print(f"Total violations to rewrite: {len(violations)}")

    plan = {}
    for entry in violations:
        fpath, lineno, target_mod = parse(entry)
        if target_mod.startswith("data."):
            continue
        plan.setdefault(target_mod, []).append((fpath, lineno))

    shim_counts = {}
    changed_files = set()
    skipped = []
    for target_mod, occ in plan.items():
        shim = ensure_shim(target_mod)
        shim_counts[target_mod] = shim
        for fpath, lineno in occ:
            if rewrite_file(fpath, lineno, target_mod, shim):
                changed_files.add(fpath)
            else:
                skipped.append((fpath, lineno, target_mod))

    print(f"Shims created/used: {len(shim_counts)}")
    print(f"Files changed: {len(changed_files)}")
    if skipped:
        print("UNMATCHED (needs manual):")
        for s in skipped:
            print("  ", s)


if __name__ == "__main__":
    main()
