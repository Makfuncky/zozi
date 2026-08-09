import ast, json
from pathlib import Path

B = Path("backend")
targets = {
    "services.suppliers_write_service",
    "services.promotions_write_service",
}
syms = {t: set() for t in targets}
files_scanned = 0
for p in B.rglob("*.py"):
    if "venv" in str(p) or "__pycache__" in str(p):
        continue
    files_scanned += 1
    try:
        t = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        continue
    for n in ast.walk(t):
        if isinstance(n, ast.ImportFrom) and n.module in targets:
            for x in n.names:
                syms[n.module].add(x.name)

for t in targets:
    print(f"\n### {t}  ({len(syms[t])} symbols)")
    print("   ", sorted(syms[t]))
print(f"\nfiles scanned: {files_scanned}")
json.dump(syms, open("_extra_files/need_sup_prom.json", "w"), indent=2)
