import pathlib, re, sys

root = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\models")
pat = re.compile(r"""schema["']?\s*[:=]\s*['"]core['"]""")
hits = []
for f in sorted(root.rglob("*.py")):
    try:
        lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        continue
    for i, ln in enumerate(lines, 1):
        if pat.search(ln):
            hits.append((str(f.relative_to(root.parent.parent)), i, ln.strip()))
for h in hits:
    print(f"{h[0]}:{h[1]}  {h[2]}")
print(f"TOTAL schema='core' hits in models: {len(hits)}")
