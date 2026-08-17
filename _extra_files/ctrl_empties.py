import os, re

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

ctrl=[]
for dp,_,fs in os.walk(os.path.join(ROOT,"controllers")):
    for f in fs:
        if f.endswith(".py"):
            ctrl.append(os.path.join(dp,f))

rows=[]
for p in ctrl:
    src=open(p,encoding="utf-8",errors="ignore").read()
    nlines=len([l for l in src.splitlines() if l.strip()])
    has_dec=bool(re.search(r"@(get|post|put|patch|delete)\b", src))
    rows.append((nlines, has_dec, os.path.relpath(p, ROOT)))

rows.sort()
print("total controllers:", len(rows))
empty=[r for r in rows if r[0]==0]
tiny=[r for r in rows if 1<=r[0]<=5]
no_dec=[r for r in rows if not r[1]]
print("truly empty (0 non-blank lines):", len(empty))
print("tiny (1-5 non-blank lines):", len(tiny))
print("no route decorator:", len(no_dec))
print("\n-- sample of NO-decorator controllers (non-blank line count) --")
for n,dec,rel in [r for r in rows if not r[1]][:25]:
    print(f"  {n:3} lines  {rel}")
print("\n-- 15 smallest controllers by non-blank lines --")
for n,dec,rel in rows[:15]:
    print(f"  {n:3} lines  dec={dec}  {rel}")
