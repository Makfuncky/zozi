"""Resolve leftover `from controllers...` / `import controllers...` imports by SYMBOL.

The comprehensive remapper resolved these by the old controller *module* name
(e.g. `analytics_controller`), which no longer exists. The referenced symbols
actually live in `domains/*/services/*`. This fixer resolves each imported name
to the module that DEFINES it (and handles package-style `from controllers.geography
import country_controller` and `import controllers.x.y as ctrl` by module file).
"""
from __future__ import annotations
import os, re, sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"venv", "__pycache__", ".git", "_legacy", "_lagacy"}

# Build name -> [defining module] and basename -> [dotted module] indexes (once).
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
    cands = _name_index.get(nm, [])
    cands = [c for c in cands if "controllers" not in c]
    cands.sort(key=lambda m: (0 if ".services." in m else 1, m))
    return cands[0] if cands else None

def _resolve_module(basename):
    cands = _mod_index.get(basename, [])
    cands = [c for c in cands if "controllers" not in c]
    cands.sort(key=lambda m: (0 if ".services." in m else 1, m))
    return cands[0] if cands else None

FROM_MOD_RE = re.compile(r"^(?P<indent>\s*)from\s+controllers\.(?P<rest>(?:\w+\.)+)\s+import\s+(?P<names>.*?)\r?$")
FROM_PKG_RE = re.compile(r"^(?P<indent>\s*)from\s+controllers\.\w+\s+import\s+(?P<names>.*?)\r?$")
IMPORT_RE = re.compile(r"^(?P<indent>\s*)import\s+controllers\.(?P<rest>(?:\w+\.)+)(?P<as>\w+)?\r?$")

def main():
    _build()
    dry = "--apply" not in sys.argv
    changed = 0
    unresolved = {}
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
                lines = open(p, encoding="utf-8").read().split("\n")
            except Exception:
                continue
            new = list(lines); did = False
            for i, ln in enumerate(lines):
                # import controllers.x.y [as Z]
                im = IMPORT_RE.match(ln)
                if im:
                    modbase = im.group("rest").rstrip(".").split(".")[-1]
                    tgt = _resolve_module(modbase)
                    if not tgt:
                        unresolved.setdefault(modbase, rel); continue
                    asname = im.group("as")
                    suffix = f" as {asname}" if asname else ""
                    new[i] = f"{im.group('indent')}import {tgt}{suffix}"
                    did = True
                    continue
                # from controllers.surface.module import names
                fm = FROM_MOD_RE.match(ln)
                if fm:
                    names = _parse_names(fm.group("names"), lines, i)
                    end = names[1]
                    inner = names[0]
                    by_tgt = {}
                    ok = True
                    for nm in inner:
                        tgt = _resolve_name(nm)
                        if not tgt:
                            unresolved.setdefault(nm, rel); ok = False; continue
                        by_tgt.setdefault(tgt, []).append(nm)
                    if not ok:
                        continue
                    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                    repl = [f"{indent}from {t} import {', '.join(ns)}" for t, ns in by_tgt.items()]
                    new[i:end + 1] = repl
                    did = True
                    continue
                # from controllers.surface import modulename  (package style)
                fp = FROM_PKG_RE.match(ln)
                if fp:
                    names = _parse_names(fp.group("names"), lines, i)
                    end = names[1]
                    inner = names[0]
                    repl = []
                    indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                    ok = True
                    for nm in inner:
                        tgt = _resolve_module(nm)
                        if not tgt:
                            unresolved.setdefault(nm, rel); ok = False; continue
                        repl.append(f"{indent}from {tgt} import {nm}")
                    if not ok:
                        continue
                    new[i:end + 1] = repl
                    did = True
            if did:
                changed += 1
                if not dry:
                    open(p, "w", encoding="utf-8").write("\n".join(new))
    print(f"[dry={dry}] files changed: {changed}")
    if unresolved:
        print("UNRESOLVED:")
        for k in sorted(unresolved):
            print("  ", k, "<-", unresolved[k])

def _parse_names(block, lines, i):
    rest = block
    if "(" in rest:
        j = i
        while j < len(lines) and ")" not in lines[j]:
            j += 1
        joined = " ".join(lines[k].rstrip() for k in range(i, j + 1))
        inner = joined[joined.index("(") + 1: joined.rindex(")")]
        names = [x.split(" as ")[0].strip() for x in re.split(r",", inner) if x.strip()]
        return names, j
    return [x.split(" as ")[0].strip() for x in re.split(r",", rest) if x.strip()], i

if __name__ == "__main__":
    main()
