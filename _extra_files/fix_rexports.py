"""
Safe wiring repair: for each module that fails to import because it does
`from TARGET import SYMBOL` but TARGET no longer defines SYMBOL, add a
re-export into TARGET:  `from CANONICAL import SYMBOL`
where CANONICAL is a module that defines SYMBOL.

This is ADDITIVE (a re-export shim) - it never deletes or duplicates logic,
and never changes call sites. It avoids circular imports by only picking a
CANONICAL that does not itself import TARGET.
"""
import importlib, os, sys, ast, threading, re

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, ROOT)
EXCLUDE = {"venv", "__pycache__", ".git", "node_modules", "tests", "alembic", "_migration_trash"}

# ---- 1) find all live definitions of every name ----
defs = {}  # name -> list of module dotted names that define it
for dirpath, dirs, files in os.walk(ROOT):
    relparts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
    if relparts & EXCLUDE:
        dirs[:] = []
        continue
    for f in files:
        if not f.endswith(".py"):
            continue
        full = os.path.join(dirpath, f)
        mod = os.path.relpath(full, ROOT)[:-3].replace(os.sep, ".")
        if mod.endswith(".__init__"):
            mod = mod[:-9]
        try:
            src = open(full, encoding="utf-8", errors="ignore").read()
            tree = ast.parse(src, filename=full)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defs.setdefault(node.name, set()).add(mod)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        defs.setdefault(t.id, set()).add(mod)

# modules that import TARGET (to avoid creating a cycle via canonical)
def imports_of(mod):
    path = None
    cand = os.path.join(ROOT, *mod.split(".")) + ".py"
    if os.path.isfile(cand):
        path = cand
    else:
        cand2 = os.path.join(ROOT, *mod.split("."), "__init__.py")
        if os.path.isfile(cand2):
            path = cand2
    if not path:
        return set()
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
        tree = ast.parse(src)
    except Exception:
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
        elif isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[0])
    return out

# ---- 2) find broken modules ----
re_imp = re.compile(r"cannot import name '([^']+)' from '([^']+)'")

def worker(mod, out):
    try:
        importlib.import_module(mod)
        out.append(("OK", ""))
    except ImportError as e:
        out.append(("IMP", str(e)))
    except Exception as e:
        out.append(("OTHER", type(e).__name__))

breaks = {}  # importer_mod -> (target_mod, symbol)
for dirpath, dirs, files in os.walk(ROOT):
    relparts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
    if relparts & EXCLUDE:
        dirs[:] = []
        continue
    for f in files:
        if not f.endswith(".py") or f == "__init__.py":
            continue
        mod = os.path.relpath(os.path.join(dirpath, f), ROOT)[:-3].replace(os.sep, ".")
        out = []
        t = threading.Thread(target=worker, args=(mod, out), daemon=True)
        t.start(); t.join(3.0)
        if out and out[0][0] == "IMP":
            m = re_imp.search(out[0][1])
            if m:
                breaks[mod] = (m.group(2), m.group(1))

# ---- 3) choose canonical + plan re-export ----
plan = []  # (target_mod, symbol, canonical)
skipped = []
for importer, (target, symbol) in sorted(breaks.items()):
    cands = [c for c in defs.get(symbol, set()) if c != target and c != importer and not c.startswith("_migration_trash")]
    # prefer services, prefer same domain as target, avoid cycle
    tparts = target.split(".")
    def score(c):
        cp = c.split(".")
        s = 0
        if cp[0] == "services":
            s += 10
        if cp[-1].endswith("_service"):
            s += 5
        # shared leading path components
        shared = 0
        for a, b in zip(tparts, cp):
            if a == b:
                shared += 1
            else:
                break
        s += shared * 2
        return s
    cands.sort(key=score, reverse=True)
    chosen = None
    for c in cands:
        if target not in imports_of(c):
            chosen = c
            break
    if chosen:
        plan.append((target, symbol, chosen))
    else:
        skipped.append((importer, target, symbol, cands))

print(f"BROKEN MODULES: {len(breaks)}")
print(f"PLAN (will add re-export): {len(plan)}")
print(f"SKIPPED (no safe canonical): {len(skipped)}")
print("=" * 90)
for target, symbol, canonical in plan:
    print(f"  RE-EXPORT: {symbol}  INTO {target}  FROM {canonical}")
print("=" * 90)
for importer, target, symbol, cands in skipped:
    print(f"  SKIP: {symbol} ({importer} <- {target}) cands={list(cands)[:3]}")
