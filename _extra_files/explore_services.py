import ast
import os
from pathlib import Path
from collections import defaultdict

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
SERVICES = BACKEND / "services"

rows = []
for p in sorted(SERVICES.rglob("*.py")):
    if p.name == "__init__.py":
        continue
    rel = p.relative_to(BACKEND)
    parts = rel.parts
    domain = parts[1] if len(parts) >= 2 else "?"
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        nlines = len(text.splitlines())
        # try to count top-level defs/classes
        defs = 0
        try:
            tree = ast.parse(text)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defs += 1
        except Exception:
            defs = -1
    except Exception:
        nlines = -1
        defs = -1
    rows.append((domain, "/".join(parts[1:]), nlines, defs, p.stat().st_size))

# Group by domain
by_dom = defaultdict(list)
for r in rows:
    by_dom[r[0]].append(r)

print("=== DOMAIN FOLDER INVENTORY (services) ===")
print(f"{'domain':<22}{'files':>6}{'total_lines':>12}{'tiny(<15)':>10}{'empty(<=2)':>11}")
tot_files = 0
tot_lines = 0
for dom in sorted(by_dom, key=lambda d: -len(by_dom[d])):
    rs = by_dom[dom]
    tl = sum(max(r[2], 0) for r in rs)
    tiny = sum(1 for r in rs if 0 < r[2] < 15)
    empty = sum(1 for r in rs if r[2] <= 2)
    tot_files += len(rs)
    tot_lines += tl
    print(f"{dom:<22}{len(rs):>6}{tl:>12}{tiny:>10}{empty:>11}")

print(f"\nTOTAL files={tot_files}  total_lines={tot_lines}")
print(f"TOTAL empty(<=2 lines)={sum(1 for r in rows if r[2] <= 2)}")
print(f"TOTAL tiny(<15 lines)={sum(1 for r in rows if 0 < r[2] < 15)}")

print("\n=== ALL EMPTY / TINY FILES (<15 lines) ===")
for r in sorted(rows, key=lambda x: (x[2], x[1])):
    if 0 < r[2] < 15:
        print(f"{r[2]:>4} lines  defs={r[3]:>3}  {r[1]}")
