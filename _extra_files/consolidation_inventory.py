import os, re, ast, pathlib, hashlib, json

ROOT = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SVCS = ROOT / "services"

# ---------- 1. gather service files ----------
svc_files = [p for p in SVCS.rglob("*.py") if p.name != "__init__.py"]
print(f"TOTAL service .py files (excl __init__): {len(svc_files)}")

# ---------- 2. one-pass import graph ----------
# Store per importing file the set of import specs.
# spec forms:
#   ("import", "M")                      -> imports module M (and submodules)
#   ("from", "X", "Y")                   -> from X import Y  (Y may be submodule or symbol)
IMPORT_SPECS = {}   # file -> set of specs
all_py = list(ROOT.rglob("*.py"))
for p in all_py:
    try:
        t = p.read_text(encoding="utf-8", errors="replace")
    except:
        continue
    specs = set()
    for m in re.finditer(r"^\s*(?:from\s+([\w.]+)\s+import\s+([^\n#]+)|import\s+([\w.]+))", t, re.M):
        if m.group(1):  # from X import Y...
            X = m.group(1)
            rest = m.group(2)
            for Y in re.split(r"[,\s]+", rest):
                Y = Y.strip()
                if Y and Y not in ("*",):
                    specs.add(("from", X, Y))
        else:  # import M
            specs.add(("import", m.group(3), None))
            # also register the dotted prefix chain
    IMPORT_SPECS[str(p)] = specs

# Build set of all real module dotted-names (backend-relative, every .py, no __init__)
def module_rel(p):
    parts = p.with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    rel = parts[len(ROOT.parts):]
    return ".".join(rel)

MODULE_SET = set()
for p in all_py:
    MODULE_SET.add(module_rel(p))

def importers_of(mod):
    """Count files that import `mod` specifically.
    `from X import Y` counts as importing `X.Y` ONLY when `X.Y` is a real module file
    (otherwise Y is a symbol inside X's __init__, not a submodule)."""
    cnt = 0
    for f, specs in IMPORT_SPECS.items():
        hit = False
        for sp in specs:
            if sp[0] == "import":
                M = sp[1]
                if M == mod or M.startswith(mod + "."):
                    hit = True; break
            else:  # from X import Y
                X, Y = sp[1], sp[2]
                cand = f"{X}.{Y}"
                if cand in MODULE_SET:           # Y is a real submodule
                    if cand == mod or cand.startswith(mod + "."):
                        hit = True; break
                else:                            # Y is a symbol in X
                    if X == mod or X.startswith(mod + "."):
                        hit = True; break
        if hit:
            cnt += 1
    return cnt

def mod_of(p):
    parts = p.with_suffix("").parts
    i = parts.index("services")
    return ".".join(parts[i:])

# ---------- 3. per-file analysis ----------
def analyze(p):
    src = p.read_text(encoding="utf-8", errors="replace")
    lines = src.splitlines()
    n_lines = len(lines)
    n_bytes = len(src.encode("utf-8"))
    try:
        tree = ast.parse(src)
    except Exception:
        return dict(parse_error=True, n_lines=n_lines, n_bytes=n_bytes,
                    public=[], code_lines=0, import_lines=0)
    public = []
    import_lines = 0
    assign_lines = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines += 1
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                public.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    public.append(t.id)
    # real code lines = non-blank, non-import, non-comment-only
    code_lines = 0
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if re.match(r"^(from|import)\s", s):
            continue
        code_lines += 1
    return dict(parse_error=False, n_lines=n_lines, n_bytes=n_bytes,
                public=public, code_lines=code_lines, import_lines=import_lines)

data = {}
for p in svc_files:
    d = analyze(p)
    d["module"] = mod_of(p)
    d["importers"] = importers_of(d["module"])
    d["domain"] = p.parts[p.parts.index("services")+1]
    data[str(p)] = d

# ---------- 4. classifications ----------
dead = []          # 0 importers + (0 bytes OR small & no public)  -> safe delete candidate
unused_nontrivial = []  # 0 importers but has public symbols / code -> needs manual check
facade_hub = []    # many public syms + few code lines + importers>0 -> intentional facade
normal = []        # everything else with importers>0
for path, d in data.items():
    if d.get("parse_error"):
        normal.append((path,d)); continue
    if d["importers"] == 0:
        if d["n_bytes"] == 0 or (d["n_lines"] <= 30 and len(d["public"]) == 0):
            dead.append((path, d))
        else:
            unused_nontrivial.append((path, d))
    else:
        if len(d["public"]) >= 12 and d["code_lines"] <= 6:
            facade_hub.append((path, d))
        else:
            normal.append((path, d))

print(f"\nDEAD/empty-stub (0 importers, trivial): {len(dead)}")
print(f"UNUSED but non-trivial (0 importers, has API): {len(unused_nontrivial)}")
print(f"FACADE/HUB (intentional re-export, keep): {len(facade_hub)}")
print(f"NORMAL (imported, real logic): {len(normal)}")
print(f"(sum = {len(dead)+len(unused_nontrivial)+len(facade_hub)+len(normal)})")

# ---------- 5. exact duplicates (non-empty) ----------
by_hash = {}
for p in svc_files:
    b = p.read_bytes()
    if len(b) == 0:
        continue
    h = hashlib.md5(b).hexdigest()
    by_hash.setdefault(h, []).append(str(p))
dups = {h: v for h, v in by_hash.items() if len(v) > 1}
print(f"\nEXACT non-empty duplicates (groups): {len(dups)}")
for h, v in dups.items():
    print("  DUP:", v)

# ---------- 6. per-domain breakdown ----------
from collections import defaultdict
dom = defaultdict(lambda: [0,0,0])  # total, dead, unused
for path, d in data.items():
    dom[d["domain"]][0] += 1
    if (path, d) in dead or any(path==x[0] for x in dead):
        dom[d["domain"]][1] += 1
    elif (path, d) in unused_nontrivial or any(path==x[0] for x in unused_nontrivial):
        dom[d["domain"]][2] += 1

print("\nPER-DOMAIN (total / dead / unused):")
for k in sorted(dom):
    print(f"  {k:14} {dom[k][0]:4} / {dom[k][1]:3} / {dom[k][2]:3}")

# ---------- 7. dump detailed dead + unused lists ----------
def show(title, items):
    print(f"\n=== {title} ===")
    for path, d in sorted(items, key=lambda x: (x[1]['domain'], x[0])):
        print(f"  {path}  lines={d['n_lines']} bytes={d['n_bytes']} public={len(d['public'])} importers={d['importers']} codeLines={d.get('code_lines')}")

show("SAFE-DELETE CANDIDATES (DEAD)", dead)
show("UNUSED NON-TRIVIAL (verify before delete)", unused_nontrivial)
show("FACADE/HUB (keep - intentional re-export)", facade_hub)

# save machine-readable
out = {
  "total": len(svc_files),
  "dead": [{"path":p, **{k:v for k,v in d.items() if k not in ('module',)}} for p,d in dead],
  "unused_nontrivial": [{"path":p, **{k:v for k,v in d.items() if k not in ('module',)}} for p,d in unused_nontrivial],
  "facade_hub": [{"path":p, **{k:v for k,v in d.items() if k not in ('module',)}} for p,d in facade_hub],
  "exact_dups": list(dups.values()),
}
pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\consolidation_inventory.json").write_text(
    json.dumps(out, indent=2, default=str), encoding="utf-8")
print("\nWrote consolidation_inventory.json")
