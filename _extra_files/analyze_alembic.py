import os, re, ast

versions = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions"
revs = {}
down = {}
missing_imports = {}
for fn in os.listdir(versions):
    if not fn.endswith(".py") or fn == "__init__.py":
        continue
    p = os.path.join(versions, fn)
    try:
        src = open(p, encoding="utf-8", errors="ignore").read()
    except Exception as e:
        print("UNREADABLE", fn, e); continue
    m_r = re.search(r"^revision\b[^=]*=\s*([\"'])(.*?)\1", src, re.M)
    m_d = re.search(r"^down_revision\b[^=]*=\s*(.+)$", src, re.M)
    rev = m_r.group(2) if m_r else None
    d = None
    if m_d:
        try:
            d = ast.literal_eval(m_d.group(1).strip())
        except Exception:
            d = m_d.group(1).strip()
    if rev is None:
        print("NO REVISION:", fn); continue
    revs[rev] = fn
    down[rev] = d
    # detect custom imports
    for m in re.finditer(r"^\s*(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))", src, re.M):
        mod = m.group(1) or m.group(2)
        if mod in ("alembic", "sqlalchemy", "sa", "op", "typing", "os", "re", "datetime", "uuid", "json", "decimal", "enum"):
            continue
        if mod.startswith("sqlalchemy") or mod.startswith("alembic"):
            continue
        missing_imports.setdefault(fn, []).append(mod)

referenced = set()
for rev, d in down.items():
    targets = d if isinstance(d, (tuple, list)) else ([d] if d else [])
    for t in targets:
        if t: referenced.add(t)

heads = [r for r in revs if r not in referenced]
print("TOTAL revisions:", len(revs))
print("HEADS:", sorted(heads))
allrevs = set(revs.keys())
for rev, d in down.items():
    targets = d if isinstance(d, (tuple, list)) else ([d] if d else [])
    for t in targets:
        if t and t not in allrevs:
            print("BROKEN down_revision:", revs[rev], "->", t)
print("--- sorted chain ---")
for r in sorted(revs):
    print(r, "->", down[r])
print("--- custom (non-stdlib, non-alembic) imports ---")
for fn, mods in sorted(missing_imports.items()):
    print(fn, "=>", mods)
