"""One-off migration helper: rewrite ``from _legacy.models[.sub] import ...``
references to their real ``domains.<d>.models.<m>`` (or ``infrastructure.database``)
homes. This is NOT ``coherence_gate.py`` and does not touch ``_legacy`` itself —
it removes references to the deleted strangler shim so the app boots under the
new structure defined in documents/NEW_STRUCTURE.md.

Usage:
    python scripts/_remap_legacy_to_domains.py --dry-run
    python scripts/_remap_legacy_to_domains.py --apply
"""
from __future__ import annotations

import argparse
import os
import re
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Modules we intentionally leave alone (tests/scripts are handled separately or
# not part of the running app).
SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules"}

# Class names that live outside domains/<d>/models but are imported via
# ``_legacy.models``.
SPECIAL = {
    "Base": "infrastructure.database.base",
}


def iter_py_files():
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            yield os.path.join(root, f)


def build_registry():
    """Map each top-level class/enum name -> dotted module path.

    Priority: domains/<d>/models/* first, then a whole-tree fallback.
    """
    reg: dict[str, str] = {}
    preferred: dict[str, str] = {}

    tree_files = list(iter_py_files())
    # First pass: prefer domain model modules.
    for path in tree_files:
        rel = os.path.relpath(path, BACKEND)
        parts = rel.replace(os.sep, "/").split("/")
        if len(parts) >= 4 and parts[0] == "domains" and parts[2] == "models":
            mod = rel[:-3].replace(os.sep, ".").replace(".__init__", "")
            _index_classes(path, preferred)
    # Second pass: whole-tree fallback for anything unresolved.
    for path in tree_files:
        rel = os.path.relpath(path, BACKEND)
        mod = rel[:-3].replace(os.sep, ".").replace(".__init__", "")
        _index_classes(path, reg)
    # Prefer domain-models hits.
    for name, mod in preferred.items():
        reg[name] = mod
    return reg


def _index_classes(path, reg: dict[str, str]):
    try:
        src = open(path, encoding="utf-8").read()
    except Exception:
        return
    for m in re.finditer(r"^\s*class\s+(\w+)", src, re.M):
        reg.setdefault(m.group(1), None)
        # store module only if not already set
        if reg[m.group(1)] is None:
            rel = os.path.relpath(path, BACKEND)
            reg[m.group(1)] = rel[:-3].replace(os.sep, ".").replace(".__init__", "")


IMPORT_RE = re.compile(
    r"^(?P<indent>\s*)from\s+_legacy\.models(?P<sub>(?:\.\w+)+)?\s+import\s+(?P<rest>.*)$"
)


def legacy_submodule_to_domain(tail: str):
    """`_legacy.models.comms.communication` -> `domains.comms.models.communication`."""
    parts = tail.lstrip(".").split(".")
    if len(parts) >= 2 and parts[0] in {
        "comms", "country", "accounts", "catalog", "orders", "payments",
        "logistics", "suppliers", "customers", "hr", "media", "finance",
        "governance",
    }:
        return "domains." + parts[0] + ".models." + ".".join(parts[1:])
    return None


def parse_names(inner: str):
    """Parse a comma-separated import list, honouring 'as' and comments."""
    names = []
    # handle newlines inside the inner string
    inner = inner.replace("\n", " ")
    # strip trailing comma / comments
    for chunk in re.split(r",", inner):
        chunk = chunk.strip()
        if not chunk:
            continue
        # strip inline comment
        chunk = chunk.split("#")[0].strip()
        if not chunk:
            continue
        _ident = chunk.split(" as ")[0].strip()
        if not re.match(r"^[A-Za-z_]\w*$", _ident):
            # not an identifier (e.g. a flake8 noqa code) — skip
            continue
        if re.match(r"^F\d+$", _ident):
            # flake8 code leaked from an inline '# noqa: F401,F403' comment
            continue
        parts = [c.strip() for c in chunk.split(" as ")]
        names.append((parts[0], parts[1] if len(parts) > 1 else None))
    return names


def find_blocks(lines):
    """Return list of (start, end, sub, [(orig, asname), ...])."""
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        m = IMPORT_RE.match(lines[i])
        if m:
            rest = m.group("rest")
            start = i
            if "(" in rest:
                end = i
                while end < n and ")" not in lines[end]:
                    end += 1
                block = " ".join(lines[k].rstrip() for k in range(i, end + 1))
                inside = block[block.index("(") + 1 : block.rindex(")")]
                names = parse_names(inside)
                blocks.append((i, end, m.group("sub"), names))
                i = end + 1
            else:
                names = parse_names(rest)
                blocks.append((i, i, m.group("sub"), names))
                i += 1
        else:
            i += 1
    return blocks


def remap_file(path, reg, dry_run, unresolved):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")

    blocks = find_blocks(lines)
    if not blocks:
        return False

    # Build replacements per block.
    new_lines = list(lines)
    # process from bottom to top so indices stay valid
    for (start, end, sub, names) in reversed(blocks):
        # resolve each name to a target module
        by_mod: dict[str, list] = {}
        for (orig, asname) in names:
            target = SPECIAL.get(orig) or reg.get(orig)
            if target is None:
                # Wildcard / dunder re-exports: transform the legacy submodule
                # path to its domain equivalent (e.g. comms.* -> domains.comms.models.*)
                if orig in ("*", "__all__") and sub:
                    mapped = legacy_submodule_to_domain(sub)
                    if mapped:
                        target = mapped
                if target is None:
                    unresolved.add(orig)
                    # keep original so the file still parses; will error at import
                    target = "_legacy.models" + (sub or "")
            by_mod.setdefault(target, []).append((orig, asname))
        repl = []
        for target, pairs in sorted(by_mod.items()):
            indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
            for (orig, asname) in pairs:
                suffix = f" as {asname}" if asname else ""
                repl.append(f"{indent}from {target} import {orig}{suffix}")
        # replace slice
        new_lines[start : end + 1] = repl

    if dry_run:
        return True

    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--paths", nargs="*", default=None,
                    help="limit to these directories/files relative to backend")
    args = ap.parse_args()

    dry_run = not args.apply
    reg = build_registry()
    reg.update(SPECIAL)

    files = iter_py_files()
    if args.paths:
        wanted = [os.path.join(BACKEND, p.replace("/", os.sep)) for p in args.paths]
        files = [f for f in files if any(f.startswith(w) for w in wanted)]

    unresolved = set()
    changed = 0
    for path in files:
        rel = os.path.relpath(path, BACKEND)
        # skip tests and scripts (handled separately / not part of boot)
        if rel.startswith("tests" + os.sep) or rel.startswith("scripts" + os.sep):
            continue
        # skip the migration helper itself and _tmp_scan.py
        if os.path.basename(path) in ("_remap_legacy_to_domains.py", "_tmp_scan.py"):
            continue
        try:
            if remap_file(path, reg, dry_run, unresolved):
                changed += 1
        except Exception as e:  # noqa
            print(f"ERROR {rel}: {e}", file=sys.stderr)

    print(f"[dry_run={dry_run}] would/changed files: {changed}")
    if unresolved:
        print(f"UNRESOLVED names ({len(unresolved)}):")
        for n in sorted(unresolved):
            print("  -", n)


if __name__ == "__main__":
    main()
