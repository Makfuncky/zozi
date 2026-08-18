"""Comprehensive wiring remapper (Wave-B/C completion).

Rewrite legacy top-level package imports to their NEW_STRUCTURE homes:
  from controllers.<surface>.<leaf> import ...   -> domains.<d>.services.<leaf>
  import controllers.<surface>.<leaf> [as Y]      -> domains.<d>.services.<leaf> [as Y]
  (same for services / models / routers roots)

Target module is resolved by surface->domain map first, then a filesystem
fallback search (preferring the importer's own domain, then domains/*/services,
then modules/*/routers). Unresolved leaves are reported and left untouched.
"""
from __future__ import annotations
import argparse, os, re, sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"venv", "__pycache__", ".git", "node_modules", ".hypothesis",
            ".pytest_cache", "_trash_zozi", "_scratch_modules_backup",
            "routers_backup", "routers_backup2", "routers_snap", "_legacy"}

SURFACE_TO_DOMAIN = {
    "finance": "finance", "treasury": "finance", "accounts": "accounts",
    "catalog": "catalog", "commerce": "catalog", "comms": "comms",
    "communication": "comms", "country": "country", "customers": "customers",
    "customer": "customers", "orders": "orders", "order": "orders",
    "payments": "payments", "payment": "payments", "logistics": "logistics",
    "suppliers": "suppliers", "supplier": "suppliers", "hr": "hr",
    "employee": "hr", "media": "media", "governance": "governance",
    "admin": "governance", "security": "governance", "risk": "governance",
    "iam": "governance", "audit": "governance", "fraud": "governance",
    "geography": "country", "core": "governance", "ai": "media",
    "automation": "media", "auth": "governance",
}

_roots = ("services", "controllers", "routers", "models")
_module_cache = {}

def _module_exists(dotted):
    if dotted in _module_cache:
        return _module_cache[dotted]
    base = os.path.join(BACKEND, *dotted.split("."))
    ok = os.path.exists(base + ".py") or os.path.exists(os.path.join(base, "__init__.py"))
    _module_cache[dotted] = ok
    return ok

def _candidate_modules(leaf):
    """All dotted module paths whose file is <leaf>.py (or a known variant) under
    searchable roots."""
    variants = [leaf, leaf + "_service", leaf + "_controller",
                leaf + "_controller_service", leaf + "_service_controller"]
    found = []
    for top in ("domains", "modules", "infrastructure", "rbac", "providers", "jobs", "kernel"):
        root = os.path.join(BACKEND, top)
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            if os.path.basename(dp) in SKIP_DIRS:
                dn[:] = []
                continue
            stems = {os.path.splitext(f)[0] for f in fn}
            for v in variants:
                if v in stems:
                    f = v + ".py"
                    mod = dp.replace(os.sep, ".").replace(BACKEND.replace(os.sep, ".") + ".", "")
                    if mod.startswith("."):
                        mod = mod[1:]
                    found.append(mod)
                    break
    return found

def resolve_target(root, surface, leaf, importer_dotted):
    # Preferred subfolder for the root
    if root == "models":
        subs = ("models", "schemas")
    elif root == "routers":
        subs = ("routers", "services")
    else:
        subs = ("services", "models", "schemas", "policies")

    if surface in SURFACE_TO_DOMAIN:
        d = SURFACE_TO_DOMAIN[surface]
        for sub in subs:
            cand = f"domains.{d}.{sub}.{leaf}"
            if _module_exists(cand):
                return cand
    # fallback search
    cands = _candidate_modules(leaf)
    if not cands:
        return None
    # preference: importer's own domain/services, then domains/*/services, then modules/*/routers, then any
    imp_domain = importer_dotted.split(".")[1] if importer_dotted.startswith("domains.") else None
    def score(m):
        s = 0
        if imp_domain and m.startswith(f"domains.{imp_domain}."):
            s += 100
        if ".services." in m:
            s += 10
        if "modules." in m and ".routers." in m:
            s += 5
        return s
    cands.sort(key=score, reverse=True)
    return cands[0]

FROM_RE = re.compile(
    r"^(?P<indent>\s*)from\s+(?P<root>" + "|".join(_roots) +
    r")(?P<rest>(?:\.\w+)+)\s+import\s+(?P<names>.*)$")
IMPORT_RE = re.compile(
    r"^(?P<indent>\s*)import\s+(?P<root>" + "|".join(_roots) +
    r")(?P<rest>(?:\.\w+)+)(?:\s+as\s+(?P<as>\w+))?$")

def parse_names(inner):
    out = []
    for chunk in re.split(r",", inner.replace("\n", " ")):
        chunk = chunk.split("#")[0].strip()
        if not chunk:
            continue
        if not re.match(r"^[A-Za-z_]\w*$", chunk.split(" as ")[0].strip()):
            continue
        parts = [c.strip() for c in chunk.split(" as ")]
        out.append((parts[0], parts[1] if len(parts) > 1 else None))
    return out

def find_blocks(lines, importer_dotted, unresolved, changed_files):
    blocks = []
    i, n = 0, len(lines)
    while i < n:
        fm = FROM_RE.match(lines[i])
        if fm:
            rest = fm.group("names"); start = i
            if "(" in rest:
                end = i
                while end < n and ")" not in lines[end]:
                    end += 1
                block = " ".join(lines[k].rstrip() for k in range(i, end + 1))
                inside = block[block.index("(") + 1: block.rindex(")")]
                names = parse_names(inside)
                blocks.append(("from", i, end, fm, names)); i = end + 1
            else:
                blocks.append(("from", i, i, fm, parse_names(rest))); i += 1
            continue
        im = IMPORT_RE.match(lines[i])
        if im:
            blocks.append(("import", i, i, im, None)); i += 1
            continue
        i += 1
    return blocks

def remap_file(path, dry_run, unresolved):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().split("\n")
    importer_dotted = os.path.relpath(path, BACKEND)[:-3].replace(os.sep, ".")
    blocks = find_blocks(lines, importer_dotted, unresolved, None)
    if not blocks:
        return False
    new_lines = list(lines)
    did = False
    for b in reversed(blocks):
        kind, start, end, m, names = b
        segs = [s for s in m.group("rest").split(".") if s]
        surface = segs[0] if segs else ""
        leaf = segs[-1]
        root = m.group("root")
        target = resolve_target(root, surface, leaf, importer_dotted)
        if target is None:
            unresolved.add(f"{root}.{'.'.join(segs)}  (in {importer_dotted})")
            continue
        indent = lines[start][: len(lines[start]) - len(lines[start].lstrip())]
        if kind == "from":
            repl = []
            for (orig, asname) in names:
                suffix = f" as {asname}" if asname else ""
                repl.append(f"{indent}from {target} import {orig}{suffix}")
            new_lines[start:end + 1] = repl
        else:
            asname = m.group("as")
            suffix = f" as {asname}" if asname else ""
            new_lines[start] = f"{indent}import {target}{suffix}"
        did = True
    if did and not dry_run:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(new_lines))
    return did

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    dry_run = not args.apply
    unresolved = set(); changed = 0
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, BACKEND)
            if rel.startswith("scripts" + os.sep) or rel.startswith("tests" + os.sep):
                continue
            if os.path.basename(p).startswith("_remap") or os.path.basename(p).startswith("_boot"):
                continue
            try:
                if remap_file(p, dry_run, unresolved):
                    changed += 1
            except Exception as e:
                print(f"ERROR {rel}: {e}", file=sys.stderr)
    print(f"[dry_run={dry_run}] changed files: {changed}")
    print(f"UNRESOLVED ({len(unresolved)}):")
    for u in sorted(unresolved):
        print("  -", u)

if __name__ == "__main__":
    main()
