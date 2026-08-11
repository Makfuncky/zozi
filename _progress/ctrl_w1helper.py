import os, re
BACKEND=r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
CTRL=os.path.join(BACKEND,"controllers")
EX={"__pycache__","venv",".git","_extra_files","node_modules",".mypy_cache"}
HELPER_CALLS=re.compile(r"\b(commit_and_refresh|add_and_flush|commit_only|bulk_soft_delete|bulk_restore)\s*\(")
HELPER_IMPORT=re.compile(r"from\s+(services\.common\.write_helpers|data\.services_write_helpers|utils\.soft_delete|services\.common\.db_read)\s+import")
for dp,dns,fns in os.walk(CTRL):
    dns[:]=[d for d in dns if d not in EX]
    for fn in fns:
        if not fn.endswith(".py"): continue
        fp=os.path.join(dp,fn)
        rel=os.path.relpath(fp,BACKEND).replace("\\","/")
        try: src=open(fp,encoding="utf-8",errors="ignore").read()
        except: continue
        imp="; ".join(HELPER_IMPORT.findall(src)) or ""
        calls=[(i+1,l.strip()) for i,l in enumerate(src.split("\n")) if HELPER_CALLS.search(l)]
        if calls:
            print("### %s" % rel)
            if imp: print("    imports: %s" % imp)
            for ln,l in calls: print("    L%d: %s" % (ln,l[:90]))
            print()
