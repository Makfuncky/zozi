import re, ast, pathlib, hashlib, json

ROOT = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
REPORT = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\SYSTEM_AUDIT_REPORT.md")

def mod_to_path(mod):
    return ROOT / (mod.replace(".", "/") + ".py")

def norm_hash(src):
    try:
        tree = ast.parse(src)
        # drop docstrings (standalone string expressions)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str):
                node.value.value = ""
        return hashlib.sha1(ast.unparse(tree).encode()).hexdigest()[:12]
    except Exception as e:
        return "ERR:" + str(e)[:20]

def extract(file, line):
    src = file.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.lineno == line:
            seg = ast.get_source_segment(src, node)
            return seg
    return None

pat = re.compile(r"\| 🟡 \| SYM2 \| backend \| (.+?) \| (class|public function) '(.+?)' defined in (\d+) modules \|")
rows = []
for line in REPORT.read_text(encoding="utf-8").splitlines():
    m = pat.search(line)
    if not m:
        continue
    locs, kind, name, n = m.group(1), m.group(2), m.group(3), int(m.group(4))
    entries = re.findall(r"([\w.]+):(\d+)", locs)
    if len(rows) == 0:
        print(f"DEBUG locs={locs!r} entries={entries}", file=__import__("sys").stderr)
    rows.append((name, kind, entries))

results = []
for name, kind, entries in rows:
    seen = {}
    ok = True
    detail = []
    for mod, ln in entries:
        p = mod_to_path(mod)
        if not p.exists():
            detail.append(f"{mod}:MISSING")
            ok = False
            continue
        seg = extract(p, int(ln))
        if seg is None:
            detail.append(f"{mod}:NODEF")
            ok = False
            continue
        h = norm_hash(seg)
        seen.setdefault(h, []).append(mod)
        detail.append(f"{mod}:{h}")
    identical = ok and len(seen) == 1
    results.append((name, kind, identical, seen, detail))

# Summary
safe = [r for r in results if r[2]]
distinct = [r for r in results if not r[2]]
print(f"TOTAL SYM2 findings: {len(results)}")
print(f"IDENTICAL (safe merge candidates): {len(safe)}")
print(f"DISTINCT (defer): {len(distinct)}")
print("\n=== IDENTICAL ===")
for name, kind, _, seen, _ in safe:
    print(f"  {kind} '{name}' -> {list(seen.values())[0]}")
print("\n=== DISTINCT ===")
for name, kind, _, seen, _ in distinct:
    variants = "; ".join(f"{','.join(mods)}" for mods in seen.values())
    print(f"  {kind} '{name}' [{len(seen)} variants]: {variants}")
