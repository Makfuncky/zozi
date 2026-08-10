"""Compare shadowed flat model modules against their canonical package modules.

Read-only helper: reports classes/tables present in the flat (dead, shadowed)
module that are missing from the canonical package module, so nothing is lost
when the flat module is converted into a re-export shim.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models")

PAIRS = [
    ("core.py", "comms/core.py"),
    ("finance.py", "finance/general_ledger.py"),
    ("logistics.py", "logistics/logistics_entities.py"),
    ("orders.py", "orders/order_entities.py"),
    ("permissions.py", "permissions/permission_entities.py"),
]


def collect(path: Path) -> dict[str, str | None]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    out: dict[str, str | None] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            table = None
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for t in stmt.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            if isinstance(stmt.value, ast.Constant):
                                table = str(stmt.value.value)
            out[node.name] = table
    return out


def collect_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("__"):
                    names.add(t.id)
    return names


def main() -> int:
    for flat_rel, pkg_rel in PAIRS:
        flat = ROOT / flat_rel
        pkg = ROOT / pkg_rel
        print("=" * 78)
        print(f"FLAT: {flat_rel}   vs   PKG: {pkg_rel}")
        if not flat.exists() or not pkg.exists():
            print("  MISSING FILE")
            continue
        fc, pc = collect(flat), collect(pkg)
        fs, ps = collect_symbols(flat), collect_symbols(pkg)
        missing_cls = sorted(set(fc) - set(pc))
        extra_cls = sorted(set(pc) - set(fc))
        print(f"  flat classes={len(fc)}  pkg classes={len(pc)}")
        print(f"  classes ONLY in flat (WOULD BE LOST): {missing_cls or 'none'}")
        print(f"  classes only in pkg  (superset gain): {len(extra_cls)} -> {extra_cls[:12]}")
        # table-level
        ftab = {v for v in fc.values() if v}
        ptab = {v for v in pc.values() if v}
        print(f"  tables ONLY in flat (WOULD BE LOST): {sorted(ftab - ptab) or 'none'}")
        # non-class symbols
        sym_missing = sorted(s for s in (fs - ps) if s not in fc)
        print(f"  non-class symbols only in flat: {sym_missing or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
