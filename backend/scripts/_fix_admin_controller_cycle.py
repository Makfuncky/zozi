"""Break the admin_controller circular-import cycle (fast: index built once)."""
from __future__ import annotations
import os, re, sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"venv", "__pycache__", ".git"}
SHIM = os.path.abspath(os.path.join(BACKEND, "domains", "governance", "services", "admin_controller.py"))

DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", re.M)
ASSIGN_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*=", re.M)

_index = {}  # name -> list of dotted module paths defining it

def build_index():
    for top in ("domains", "modules", "infrastructure", "providers", "rbac", "kernel", "jobs"):
        root = os.path.join(BACKEND, top)
        if not os.path.isdir(root):
            continue
        for dp, dn, fn in os.walk(root):
            if os.path.basename(dp) in SKIP:
                dn[:] = []; continue
            for f in fn:
                if not f.endswith(".py"):
                    continue
                full = os.path.abspath(os.path.join(dp, f))
                if full == SHIM:
                    continue
                mod = dp.replace(os.sep, ".").replace(BACKEND.replace(os.sep, ".") + ".", "")
                if mod.startswith("."):
                    mod = mod[1:]
                dotted = f"{mod}.{f[:-3]}" if f != "__init__.py" else mod
                try:
                    txt = open(full, encoding="utf-8").read()
                except Exception:
                    continue
                for m in DEF_RE.finditer(txt):
                    _index.setdefault(m.group(1), []).append(dotted)
                for m in ASSIGN_RE.finditer(txt):
                    if m.group(1) not in _index:
                        _index.setdefault(m.group(1), []).append(dotted)

SHIM = os.path.abspath(os.path.join(BACKEND, "domains", "governance", "services", "admin_controller.py"))
SHIM_MODULE = "domains.governance.services.admin_controller"
# Names that exist ONLY as shim re-exports / aliases.
SHIM_ALIASES = {
    "get_current_admin", "get_ticket_detail", "require_admin_2fa_enabled",
    "require_admin_2fa_verified", "require_roles",
}

def defs_of(name):
    if name in SHIM_ALIASES:
        return [SHIM_MODULE]
    cands = _index.get(name, [])
    cands = [c for c in cands if c != SHIM_MODULE]
    cands.sort(key=lambda m: (0 if ".services." in m else 1, m))
    return cands

IMPORT_RE = re.compile(
    r"^(?P<indent>\s*)from\s+domains\.governance\.services\.admin_controller\s+import\s+(?P<names>.*)$")

def main():
    build_index()
    dry = "--apply" not in sys.argv
    unknown = {}
    changed = 0
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(root, f)
            if os.path.abspath(p) == SHIM:
                continue
            rel = os.path.relpath(p, BACKEND)
            if rel.startswith("scripts" + os.sep) or rel.startswith("tests" + os.sep):
                continue
            try:
                lines = open(p, encoding="utf-8").read().split("\n")
            except Exception:
                continue
            new = list(lines); did = False
            for i, ln in enumerate(lines):
                m = IMPORT_RE.match(ln)
                if not m:
                    continue
                rest = m.group("names")
                if "(" in rest:
                    j = i
                    while j < len(lines) and ")" not in lines[j]:
                        j += 1
                    block = " ".join(lines[k].rstrip() for k in range(i, j + 1))
                    inner = block[block.index("(") + 1: block.rindex(")")]
                    names = [x.split(" as ")[0].strip() for x in re.split(r",", inner) if x.strip()]
                    end = j
                else:
                    names = [x.split(" as ")[0].strip() for x in re.split(r",", rest) if x.strip()]
                    end = i
                by_target = {}
                ok = True
                for nm in names:
                    cands = defs_of(nm)
                    if not cands:
                        unknown.setdefault(nm, rel); ok = False; continue
                    by_target.setdefault(cands[0], []).append(nm)
                if not ok:
                    continue
                indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
                repl = [f"{indent}from {tgt} import {', '.join(nms)}" for tgt, nms in by_target.items()]
                new[i:end + 1] = repl
                did = True
            if did:
                changed += 1
                if not dry:
                    open(p, "w", encoding="utf-8").write("\n".join(new))
    print(f"[dry={dry}] files changed: {changed}")
    if unknown:
        print("UNKNOWN names (no def found):")
        for k in sorted(unknown):
            print("  ", k, "<-", unknown[k])

if __name__ == "__main__":
    main()
