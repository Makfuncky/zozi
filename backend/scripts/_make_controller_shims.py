"""Create re-export shim modules for missing old controller modules.

Some routers do `import controllers.<surface>.<module> as ctrl` or
`from controllers.<surface>.<module> import <names>` where the old controller
module no longer exists but the *symbols* it exposed live in `domains/*/services/*`.
For each such module, collect every symbol referenced, resolve each to its defining
module, and emit a shim at `domains/<domain>/services/<module>.py` that re-exports
them. Router imports are then rewritten to the shim.
"""
from __future__ import annotations
import os, re, sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"venv", "__pycache__", ".git", "_legacy", "_lagacy"}

SURFACE_TO_DOMAIN = {
    "finance": "finance", "accounts": "accounts", "catalog": "catalog",
    "commerce": "catalog", "comms": "comms", "country": "country",
    "customers": "customers", "customer": "customers", "orders": "orders",
    "payments": "payments", "logistics": "logistics", "suppliers": "suppliers",
    "supplier": "suppliers", "hr": "hr", "media": "media", "governance": "governance",
    "admin": "governance", "security": "governance", "risk": "governance",
    "iam": "governance", "audit": "governance", "fraud": "governance",
    "geography": "country", "core": "governance", "ai": "media",
    "automation": "media", "auth": "governance",
}

_name_index = {}
_mod_index = {}

def _build():
    for top in ("domains", "modules", "infrastructure", "providers", "rbac", "kernel", "jobs"):
        root = os.path.join(BACKEND, top)
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            if os.path.basename(dp) in SKIP:
                dn[:] = []; continue
            for f in fn:
                if not f.endswith(".py") or f == "__init__.py":
                    continue
                full = os.path.join(dp, f)
                mod = dp.replace(os.sep, ".").replace(BACKEND.replace(os.sep, ".") + ".", "")
                if mod.startswith("."):
                    mod = mod[1:]
                dotted = f"{mod}.{f[:-3]}"
                _mod_index.setdefault(f[:-3], []).append(dotted)
                try:
                    txt = open(full, encoding="utf-8").read()
                except Exception:
                    continue
                for m in re.finditer(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", txt, re.M):
                    _name_index.setdefault(m.group(1), []).append(dotted)
                for m in re.finditer(r"^\s*class\s+([A-Za-z_]\w*)\b", txt, re.M):
                    _name_index.setdefault(m.group(1), []).append(dotted)
                for m in re.finditer(r"^\s*([A-Za-z_]\w*)\s*=", txt, re.M):
                    _name_index.setdefault(m.group(1), []).append(dotted)

def _resolve_name(nm):
    cands = [c for c in _name_index.get(nm, []) if "controllers" not in c]
    cands.sort(key=lambda m: (0 if ".services." in m else 1, m))
    return cands[0] if cands else None

def _resolve_module(basename):
    cands = [c for c in _mod_index.get(basename, []) if "controllers" not in c]
    cands.sort(key=lambda m: (0 if ".services." in m else 1, m))
    return cands[0] if cands else None

USAGE_RE = re.compile(r"controllers\.(?P<surface>\w+)\.(?P<module>\w+)(?:\s+as\s+(?P<asalias>\w+))?")
FROM_IMPORT_RE = re.compile(r"from\s+controllers\.\w+\.(?P<module>\w+)\s+import\s+(?P<names>.*)")

def main():
    _build()
    dry = "--apply" not in sys.argv
    # module -> set of names
    usage = {}
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, BACKEND)
            if rel.startswith("scripts" + os.sep) or rel.startswith("tests" + os.sep) or f.startswith("_remap") or f.startswith("_fix") or f.startswith("_boot"):
                continue
            try:
                txt = open(p, encoding="utf-8").read()
            except Exception:
                continue
            for m in FROM_IMPORT_RE.finditer(txt):
                mod = m.group("module")
                if _resolve_module(mod):
                    continue  # already a real file somewhere
                names = re.split(r",", m.group("names"))
                names = [x.split(" as ")[0].strip().strip("()") for x in names]
                names = [x for x in names if x and re.match(r"^[A-Za-z_]\w*$", x)]
                usage.setdefault(mod, set()).update(names)
            for m in USAGE_RE.finditer(txt):
                mod = m.group("module")
                if _resolve_module(mod):
                    continue
                # module alias import: we don't know names; leave for manual/alt handling
                usage.setdefault("__alias__" + mod, set())
    # Build shims for modules with known names
    shims = {}
    for mod, names in usage.items():
        if mod.startswith("__alias__"):
            continue
        surface = None
        # recover surface from a usage line is hard; infer domain from resolved names
        by_tgt = {}
        unresolved = set()
        for nm in names:
            tgt = _resolve_name(nm)
            if tgt:
                by_tgt.setdefault(tgt, []).append(nm)
            else:
                unresolved.add(nm)
        if not by_tgt:
            print(f"SKIP shim {mod}: no resolvable names")
            continue
        # pick domain by most common resolved target's domain prefix
        dom_counts = {}
        for tgt in by_tgt:
            d = tgt.split(".")[1] if tgt.startswith("domains.") else "governance"
            dom_counts[d] = dom_counts.get(d, 0) + 1
        domain = max(dom_counts, key=dom_counts.get)
        shim_path = os.path.join(BACKEND, "domains", domain, "services", mod + ".py")
        if os.path.exists(shim_path):
            print(f"EXISTS shim {shim_path}")
            continue
        shims[shim_path] = (by_tgt, unresolved, mod)
    if dry:
        for sp, (bt, un, mod) in shims.items():
            print(f"WOULD CREATE {sp}  ({len(bt)} targets, unresolved={sorted(un)})")
        return
    created = 0
    for sp, (by_tgt, unresolved, mod) in shims.items():
        lines = ['"""Migration re-export shim for the old controller module '
                 f'`{mod}`.\nSymbols resolve to their real domain/infra homes.', '"""',
                 "from __future__ import annotations", ""]
        for tgt, nms in by_tgt.items():
            lines.append(f"from {tgt} import {', '.join(sorted(set(nms)))}")
        if unresolved:
            lines.append("")
            lines.append(f"# Unresolved during migration: {', '.join(sorted(unresolved))}")
        os.makedirs(os.path.dirname(sp), exist_ok=True)
        open(sp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        created += 1
    print(f"Created {created} shim modules")
    _rewrite_to_shims()

def _rewrite_to_shims():
    """Rewrite `controllers.<surface>.<module>` references to the created shims."""
    rew = 0
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, BACKEND)
            if rel.startswith("scripts" + os.sep) or rel.startswith("tests" + os.sep) or f.startswith("_remap") or f.startswith("_fix") or f.startswith("_boot") or f.startswith("_make"):
                continue
            try:
                lines = open(p, encoding="utf-8").read().split("\n")
            except Exception:
                continue
            new = list(lines); did = False
            for i, ln in enumerate(lines):
                def _map(m):
                    surface = m.group("surface"); module = m.group("module")
                    domain = SURFACE_TO_DOMAIN.get(surface, surface)
                    shim = os.path.join(BACKEND, "domains", domain, "services", module + ".py")
                    if not os.path.exists(shim):
                        return None
                    return f"domains.{domain}.services.{module}"
                for rgx, grp in ((re.compile(r"from\s+controllers\.(?P<surface>\w+)\.(?P<module>\w+)\s+import\s"), None),
                               (re.compile(r"import\s+controllers\.(?P<surface>\w+)\.(?P<module>\w+)(?:\s+as\s+(?P<as>\w+))?"), None)):
                    mm = rgx.search(ln)
                    if mm:
                        tgt = _map(mm)
                        if not tgt:
                            continue
                        asname = mm.groupdict().get("as")
                        if rgx.pattern.startswith("from"):
                            new[i] = re.sub(r"controllers\.\w+\.\w+", tgt, ln, count=1)
                        else:
                            suffix = f" as {asname}" if asname else ""
                            new[i] = re.sub(r"controllers\.\w+\.\w+", tgt, ln, count=1)
                        did = True
                        break
            if did:
                rew += 1
                open(p, "w", encoding="utf-8").write("\n".join(new))
    print(f"Rewrote {rew} files to shim modules")


if __name__ == "__main__":
    main()
