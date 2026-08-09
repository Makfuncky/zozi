"""Verify A2 'orphan module' findings against ACTUAL import usage.

The audit's check_dead_modules flags any module with fan_in == 0.
Two detection gaps cause mass false positives:
  1. main.py loads routers via importlib.import_module(f"routers.{name}")
     using an f-string VARIABLE -> the audit (constant-string only) sees
     no edge main -> router -> controller -> service.
  2. `from package import submodule` is resolved to the *package*, not the
     *submodule*, so the submodule's fan_in stays 0 and it is flagged.

This script rebuilds the import graph CORRECTLY (resolving package-style
imports to submodules and honoring main.py's dynamic router list) and
reports, per A2-flagged module, whether it is actually referenced.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
REPORT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\SYSTEM_AUDIT_REPORT.md")

A2_RE = re.compile(
    r"\|\s*A2\s*\|\s*backend\s*\|\s*(?P<path>[^|]+?)\s*\|\s*module has no inbound imports",
    re.MULTILINE,
)


def module_name_for(pyfile: Path) -> str | None:
    rel = pyfile.relative_to(BACKEND).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def collect_modules() -> dict[str, Path]:
    mods: dict[str, Path] = {}
    for py in BACKEND.rglob("*.py"):
        m = module_name_for(py)
        if m:
            mods[m] = py
    return mods


def resolve_relative(level: int, module: str | None, pkg: list[str]) -> str | None:
    if level == 0:
        return module
    if not pkg:
        return None
    base = pkg[: len(pkg) - (level - 1)] if level - 1 < len(pkg) else pkg
    if module:
        return ".".join(base + module.split("."))
    return ".".join(base)


def main_router_basenames() -> set[str]:
    """Extract router names from main.py's router_names list (dynamic load)."""
    names: set[str] = set()
    text = (BACKEND / "main.py").read_text(encoding="utf-8", errors="ignore")
    # router_names = [ ("auth", ...), ("users", ...), ... ]
    for m in re.finditer(r'"\s*([a-zA-Z_][\w]*)\s*"\s*,\s*"', text):
        names.add(m.group(1))
    return names


def build_references(mods: dict[str, Path]) -> dict[str, set[str]]:
    """Map target-module -> set of files that reference it (correctly resolved)."""
    refs: dict[str, set[str]] = {m: set() for m in mods}
    router_names = main_router_basenames()
    for src, py in mods.items():
        try:
            tree = ast.parse(py.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        try:
            pkg = list(py.relative_to(BACKEND).parent.parts)
        except ValueError:
            pkg = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    tgt = alias.name
                    if tgt in mods:
                        refs[tgt].add(src)
                    # `import package.submodule` might itself be a module
            elif isinstance(node, ast.ImportFrom):
                base = resolve_relative(node.level, node.module, pkg)
                if not base:
                    continue
                for alias in node.names:
                    cand = f"{base}.{alias.name}"
                    if cand in mods:
                        refs[cand].add(src)
                    # `from package import submodule` where submodule is a module
                    if alias.name in router_names and f"routers.{alias.name}" in mods:
                        refs[f"routers.{alias.name}"].add(src)
            elif isinstance(node, ast.Call):
                fname = None
                if isinstance(node.func, ast.Name):
                    fname = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fname = node.func.attr
                if fname in {"import_module", "__import__"} and node.args:
                    a = node.args[0]
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        if a.value in mods:
                            refs[a.value].add(src)
    return refs


def parse_a2_paths() -> list[str]:
    text = REPORT.read_text(encoding="utf-8", errors="ignore")
    out = []
    for m in A2_RE.finditer(text):
        p = m.group("path").strip().replace("\\", "/")
        out.append(p)
    return out


def main() -> int:
    mods = collect_modules()
    refs = build_references(mods)
    a2_paths = parse_a2_paths()

    false_pos = []
    real_orphans = []
    not_found = []
    for p in a2_paths:
        dotted = ".".join(Path(p).with_suffix("").parts)
        if dotted not in mods:
            not_found.append(p)
            continue
        if refs.get(dotted):
            false_pos.append((dotted, sorted(refs[dotted])))
        else:
            real_orphans.append(dotted)

    print("=" * 70)
    print(f"A2 flagged in report          : {len(a2_paths)}")
    print(f"  not found on disk           : {len(not_found)}")
    print(f"  ACTUALLY REFERENCED (FP)    : {len(false_pos)}")
    print(f"  UNREFERENCED (real orphan?) : {len(real_orphans)}")
    print("=" * 70)

    print("\n--- UNREFERENCED (candidate real orphans) ---")
    for m in sorted(real_orphans):
        print("  ", m)

    # write detailed report
    out = BACKEND.parent / "_extra_files" / "a2_verification.txt"
    with out.open("w", encoding="utf-8") as f:
        f.write(f"A2 flagged: {len(a2_paths)}\n")
        f.write(f"false positives (referenced): {len(false_pos)}\n")
        f.write(f"real orphans: {len(real_orphans)}\n\n")
        f.write("REAL ORPHANS:\n")
        for m in sorted(real_orphans):
            f.write(f"  {m}\n")
        f.write("\nFALSE POSITIVES (referenced by):\n")
        for m, by in sorted(false_pos):
            f.write(f"  {m}  <-  {', '.join(by)}\n")
    print(f"\nDetailed report written to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
