import os, re
ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
ctrl=[]
for dp,_,fs in os.walk(os.path.join(ROOT,"controllers")):
    for f in fs:
        if f.endswith(".py"):
            ctrl.append(os.path.join(dp,f))

real=[p for p in ctrl if os.path.basename(p)!="__init__.py"]
init=[p for p in ctrl if os.path.basename(p)=="__init__.py"]
print("raw controller .py:", len(ctrl), "| __init__.py:", len(init), "| real modules:", len(real))

empty_real=[p for p in real if len([l for l in open(p,encoding="utf-8",errors="ignore").read().splitlines() if l.strip()])==0]
print("truly empty REAL controller modules (non-__init__):", len(empty_real))

no_dec=[p for p in real if not re.search(r"@(get|post|put|patch|delete)\b", open(p,encoding="utf-8",errors="ignore").read())]
print("real modules WITHOUT @route decorator:", len(no_dec))
print("\n-- what do a few 'no-decorator' controllers actually contain? --")
for p in no_dec[:6]:
    src=open(p,encoding="utf-8",errors="ignore").read()
    print(f"\n### {os.path.relpath(p,ROOT)} ({len([l for l in src.splitlines() if l.strip()])} non-blank lines)")
    print("\n".join(src.splitlines()[:12]))
