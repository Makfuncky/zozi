"""One-off migration helper: rewrite ``from services.<surface>.<module> import ...``
and ``from controllers.<surface>.<module> import ...`` to their new homes under
``domains.<d>.services`` / ``domains.<d>.*``.

This is the Wave-B/C wiring: the flat ``services``/``controllers`` packages were
migrated into ``domains/*/services`` (and router shells into modules), but the
imports inside the re-homed routers were never rewritten. We resolve each leaf
module name to its new location via a registry scan.

Usage:
    python scripts/_remap_services_controllers.py --apply
"""
from __future__ import annotations

import argparse
import os
import re
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules"}

# Old surface tokens that map to a domain folder name.
SURFACE_TO_DOMAIN = {
    "finance": "finance",
    "treasury": "finance",
    "accounts": "accounts",
    "catalog": "catalog",
    "commerce": "catalog",
    "comms": "comms",
    "communication": "comms",
    "country": "country",
    "customers": "customers",
    "customer": "customers",
    "orders": "orders",
    "order": "orders",
    "payments": "payments",
    "payment": "payments",
    "logistics": "logistics",
    "suppliers": "suppliers",
    "supplier": "suppliers",
    "hr": "hr",
    "employee": "hr",
    "media": "media",
    "governance": "governance",
    "admin": "governance",
}

# Leaf modules that live outside domains/<d>/services (shared infra/kernel/utils).
LEAF_SPECIAL = {
    "storage": "infrastructure.storage",
}


def iter_py_files():
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


def find_module_leaf(target_leaf: str, surface: str):
    """Return dotted module path for a leaf module name, or None."""
    if target_leaf in LEAF_SPECIAL:
        return LEAF_SPECIAL[target_leaf]
    if surface in SURFACE_TO_DOMAIN:
        d = SURFACE_TO_DOMAIN[surface]
        cand = f"domains.{d}.services.{target_leaf}"
        if _module_exists(cand):
            return cand
    # search all domains/<d>/services for a submodule named target_leaf
    best = None
    for root, dirs, files in os.walk(os.path.join(BACKEND, "domains")):
        if "services" not in root.replace(os.sep, "/").split("/"):
            continue
        for f in files:
            if f == target_leaf + ".py":
                mod = os.path.join(root, f)[:-3].replace(os.sep, ".").replace(
                    ".__init__", ""
                )
                if mod.endswith(".services." + target_leaf) or (
                    ".services" in mod and mod.endswith(target_leaf)
                ):
                    if best is None:
                        best = mod
    return best


_module_cache = {}


def _module_exists(dotted: str):
    if dotted in _module_cache:
        return _module_cache[dotted]
    path = os.path.join(BACKEND, *dotted.split(".")) + ".py"
    pkg = os.path.join(BACKEND, *dotted.split("."), "__init__.py")
    ok = os.path.exists(path) or os.path.exists(pkg)
    _module_cache[dotted] = ok
    return ok


IMPORT_RE = re.compile(
    r"^(?P<indent>\s*)from\s+(?P<pkg>services|controllers)(?P<rest>(?:\.\w+)+)\s+import\s+(?P<names>.*)$"
)


def parse_names(inner: str):
    out = []
    for chunk in re.split(r",", inner.replace("\n", " ")):
        chunk = chunk.split("#")[0].strip()
        if not chunk:
            continue
        if not re.match(r"^[A-Za-z_]\w*$", chunk.split(" as ")[0].strip()):
            continue
        if re.match(r"^F\d+$", chunk.split(" as ")[0].strip()):
            continue
        parts = [c.strip() for c in chunk.split(" as ")]
        out.append((parts[0], parts[1] if len(parts) > 1 else None))
    return out


def find_blocks(lines):
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        m = IMPORT_RE.match(lines[i])
        if m:
            rest = m.group("names")
            start = i
            if "(" in rest:
                end = i
                while end < n and ")" not in lines[end]:
                    end += 1
                block = " ".join(lines[k].rstrip() for k in range(i, end + 1))
                inside = block[block.index("(") + 1 : block.rindex(")")]
                names = parse_names(inside)
                blocks.append((i, end, m.group("pkg"), m.group("rest"), names))
                i = end + 1
            else:
                blocks.append((i, i, m.group("pkg"), m.group("rest"), parse_names(rest)))
                i += 1
        else:
            i += 1
    return blocks


def remap_file(path, dry_run, unresolved):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    blocks = find_blocks(lines)
    if not blocks:
        return False
    new_lines = list(lines)
    for (start, end, pkg, rest, names) in reversed(blocks):
        # rest = .surface.leaf  (could be deeper, but leaf is last segment)
        segs = [s for s in rest.split(".") if s]
        surface = segs[0] if segs else ""
        leaf = segs[-1]
        target = find_module_leaf(leaf, surface)
        if target is None:
            unresolved.add(f"{pkg}.{'.'.join(segs)}")
            continue
        indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
        repl = []
        for (orig, asname) in names:
            suffix = f" as {asname}" if asname else ""
            repl.append(f"{indent}from {target} import {orig}{suffix}")
        new_lines[start : end + 1] = repl
    if dry_run:
        return True
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(new_lines))
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry_run = not args.apply

    files = iter_py_files()
    unresolved = set()
    changed = 0
    for path in files:
        rel = os.path.relpath(path, BACKEND)
        if rel.startswith("tests" + os.sep) or rel.startswith("scripts" + os.sep):
            continue
        if os.path.basename(path) in (
            "_remap_services_controllers.py",
            "_remap_legacy_to_domains.py",
            "_patch_inits.py",
            "_boot_check.py",
            "_tmp_scan.py",
        ):
            continue
        try:
            if remap_file(path, dry_run, unresolved):
                changed += 1
        except Exception as e:  # noqa
            print(f"ERROR {rel}: {e}", file=sys.stderr)
    print(f"[dry_run={dry_run}] changed files: {changed}")
    if unresolved:
        print(f"UNRESOLVED ({len(unresolved)}):")
        for u in sorted(unresolved)[:60]:
            print("  -", u)


if __name__ == "__main__":
    main()
