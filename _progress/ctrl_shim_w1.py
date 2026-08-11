import os, re
BACKEND=r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
SHIM_DIRS=["admin","communication","country"]
EX={"__pycache__","venv",".git","_extra_files","node_modules",".mypy_cache"}
CALLS=re.compile(r"\b(commit_and_refresh|add_and_flush|commit_only|bulk_soft_delete|bulk_restore|db\.add|db\.commit|db\.delete|db\.merge|db\.flush)\s*\(")
for sd in SHIM_DIRS:
    d=os.path.join(BACKEND,"controllers",sd)
    if not os.path.isdir(d): continue
    hits=[]
    for dp,dns,fns in os.walk(d):
        dns[:]=[x for x in dns if x not in EX]
        for fn in fns:
            if not fn.endswith(".py"): continue
            fp=os.path.join(dp,fn)
            rel=os.path.relpath(fp,BACKEND).replace("\\","/")
            try: src=open(fp,encoding="utf-8",errors="ignore").read()
            except: continue
            for i,l in enumerate(src.split("\n"),1):
                if CALLS.search(l):
                    hits.append((rel,i,l.strip()[:90]))
    print("=== controllers/%s (GATE-EXCLUDED) write-helper / db-write hits: %d ===" % (sd,len(hits)))
    for rel,i,l in hits[:20]:
        print("  %s:%d: %s" % (rel,i,l))
