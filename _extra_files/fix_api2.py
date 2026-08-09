"""API2 fixer (optimized): make leaked private module-level symbols public.

Precomputes reverse indices once, then renames definition + all external
import/attribute references. Skips dunders, test, migration files, and
collisions. DRY RUN by default; --apply to write.
"""
from __future__ import annotations
import ast
import os
import sys
from pathlib import Path

BACKEND = Path("backend")
SKIP = {"venv", "node_modules", "__pycache__", ".venv", ".git", "experiments"}


def module_of(path: Path) -> str:
    rel = path.relative_to(BACKEND).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def is_test(parts) -> bool:
    return any(x in parts for x in {"tests", "test", "e2e", "testing",
                                    "loadtests", "validation"})


def is_migration(parts) -> bool:
    return "alembic" in parts and "versions" in parts


def resolve_relative(m2: str, level: int, module: str | None) -> str:
    parts = m2.split(".")
    base = parts[:len(parts) - level] if level > 0 else parts
    if module:
        base = base + module.split(".")
    return ".".join(base)


def main():
    apply = "--apply" in sys.argv
    paths = []
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f.endswith(".py"):
                paths.append(Path(root) / f)
    mods = {module_of(p): p for p in paths}

    defs = {}
    facts = {}
    for mod, path in mods.items():
        try:
            src = path.read_text(encoding="utf-8")
            tree = ast.parse(src)
        except Exception:
            continue
        syms = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_") and not (node.name.startswith("__") and node.name.endswith("__")):
                    syms[node.name] = node
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.startswith("_") and not (t.id.startswith("__") and t.id.endswith("__")):
                        syms[t.id] = node
        defs[mod] = (syms, src, tree)
        alias_map = {}
        from_imp = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    alias_map[n.asname or n.name.split(".")[0]] = n.name
            elif isinstance(node, ast.ImportFrom):
                from_imp.append((node.level, node.module, node.names))
        facts[mod] = (alias_map, from_imp, tree)

    # reverse indices: (m2, target_mod) -> list of import alias nodes / attr nodes
    from_index = {}
    attr_index = {}
    for m2, (alias_map, from_imp, tree) in facts.items():
        for (level, fmod, names) in from_imp:
            tmod = resolve_relative(m2, level, fmod) if level else fmod
            from_index.setdefault((m2, tmod), []).extend(names)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                base = node.value
                if isinstance(base, ast.Name) and base.id in alias_map:
                    tmod = alias_map[base.id]
                    attr_index.setdefault((m2, tmod), []).append(node)

    edits = {}
    leak_count = 0
    for mod, (syms, _, _) in defs.items():
        parts = mod.split(".")
        if is_test(parts) or is_migration(parts):
            continue
        for name, defnode in syms.items():
            new = name.lstrip("_")
            if not new or new == name or new in syms:
                continue
            ref_files = set()
            for m2, path in mods.items():
                if m2 == mod or m2.startswith(mod + "."):
                    continue
                for a in from_index.get((m2, mod), []):
                    if a.name == name:
                        ref_files.add(path)
                for an in attr_index.get((m2, mod), []):
                    if an.attr == name:
                        ref_files.add(path)
            if not ref_files:
                continue
            leak_count += 1
            df = mods[mod]
            edits.setdefault((df, mod), []).append(("def", defnode, new))
            for rf in ref_files:
                rm = module_of(rf)
                el = edits.setdefault((rf, rm), [])
                for a in from_index.get((rm, mod), []):
                    if a.name == name:
                        el.append(("fromimp", a, new))
                for an in attr_index.get((rm, mod), []):
                    if an.attr == name:
                        el.append(("attr", an, new))

    total = 0
    for (path, mod), lst in edits.items():
        if not lst:
            continue
        src = path.read_text(encoding="utf-8")
        lines = src.splitlines(keepends=True)
        fe = [(kind, node.lineno, node.col_offset, new) for kind, node, new in lst]
        fe.sort(key=lambda e: (e[1], e[2]), reverse=True)
        new_lines = list(lines)
        for kind, ln, col, new in fe:
            b = new_lines[ln - 1].encode("utf-8")
            rest = b[col:]
            m = 0
            while m < len(rest) and (rest[m:m+1].isalnum() or rest[m:m+1] == b"_"):
                m += 1
            new_lines[ln - 1] = (b[:col] + new.encode("utf-8") + rest[m:]).decode("utf-8")
        if apply:
            path.write_text("".join(new_lines), encoding="utf-8")
            total += len(fe)
            print(f"  {len(fe):>3}  {path.relative_to(BACKEND)}")
        else:
            print(f"  (dry) {len(fe):>3}  {path.relative_to(BACKEND)}")
    print(f"\nGenuine leaks renamed: {leak_count}")
    print(f"Total identifier renames: {total}" if apply else f"DRY RUN: {total} renames planned. Pass --apply to write.")


if __name__ == "__main__":
    main()
