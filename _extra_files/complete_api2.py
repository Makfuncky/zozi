"""Complete the API2 renames that the buggy renamer left inconsistent.

State after buggy apply + wrong repair:
  * renamed symbols:  def == `_old` (private), internal calls == `_old`,
                      external references == `old` (public, already renamed)
    => ImportError at runtime (external `from M import old` can't find `old`)
  * unrenamed symbols: def == `_old`, internal == `_old`, external == `_old`
    => consistent; leave alone

Detection: for module M and private symbol `_old`, it was renamed iff some
external module references the PUBLIC name `old` from M AND none references
`_old` from M. For those, rename every code-identifier `_old` -> `old` inside M
(def + internal calls). External refs are already `old`.

DRY RUN by default; --apply to write.
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


def resolve_relative(m2, level, module):
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

    # exported private symbols per module
    priv = {}
    for mod, path in mods.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        names = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_") and not (node.name.startswith("__") and node.name.endswith("__")):
                    names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id.startswith("_") and not (t.id.startswith("__") and t.id.endswith("__")):
                        names.add(t.id)
        priv[mod] = names

    # external usage of `old` and `_old` referencing each module
    ext_old = {}
    ext__old = {}
    for mod, path in mods.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        alias_map = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    alias_map[n.asname or n.name.split(".")[0]] = n.name
            elif isinstance(node, ast.ImportFrom):
                tmod = resolve_relative(mod, node.level, node.module) if node.level else node.module
                for n in node.names:
                    ext_old.setdefault(tmod, set()).add(n.name)
                    ext__old.setdefault(tmod, set()).add(n.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                base = node.value
                if isinstance(base, ast.Name) and base.id in alias_map:
                    tmod = alias_map[base.id]
                    ext_old.setdefault(tmod, set()).add(node.attr)
                    ext__old.setdefault(tmod, set()).add(node.attr)

    # determine renamed symbols and complete them
    total = 0
    for mod, names in priv.items():
        to_fix = []
        for name in names:
            pub = name.lstrip("_")
            if not pub or pub == name:
                continue
            renamed = (pub in ext_old.get(mod, set())) and (name not in ext__old.get(mod, set()))
            if renamed:
                to_fix.append(name)
        if not to_fix:
            continue
        path = mods[mod]
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except Exception:
            print(f"  SKIP parse-fail {path}")
            continue
        edits = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in to_fix:
                edits.append((node.lineno, node.col_offset, node.name.lstrip("_")))
            elif isinstance(node, ast.Attribute) and node.attr in to_fix:
                edits.append((node.lineno, node.col_offset, node.attr.lstrip("_")))
            elif isinstance(node, ast.Name) and node.id in to_fix:
                edits.append((node.lineno, node.col_offset, node.id.lstrip("_")))
        edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
        lines = src.splitlines(keepends=True)
        new_lines = list(lines)
        for ln, col, new in edits:
            b = new_lines[ln - 1].encode("utf-8")
            rest = b[col:]
            m = 0
            while m < len(rest) and (rest[m:m+1].isalnum() or rest[m:m+1] == b"_"):
                m += 1
            new_lines[ln - 1] = (b[:col] + new.encode("utf-8") + rest[m:]).decode("utf-8")
        if apply:
            path.write_text("".join(new_lines), encoding="utf-8")
            total += len(edits)
            print(f"  {len(edits):>3}  {path.relative_to(BACKEND)}  fixed: {', '.join(to_fix)}")
        else:
            print(f"  (dry) {len(edits):>3}  {path.relative_to(BACKEND)}  would fix: {', '.join(to_fix)}")
    print(f"\nTotal identifier renames applied: {total}" if apply else f"DRY RUN complete. Apply with --apply.")


if __name__ == "__main__":
    main()
