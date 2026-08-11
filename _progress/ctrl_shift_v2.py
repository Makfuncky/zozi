import os, ast, json
BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
CTRL = os.path.join(BACKEND,"controllers"); SVC = os.path.join(BACKEND,"services")
SHIM = {"admin","communication","country"}
EX = {"__pycache__","venv",".git","_extra_files","node_modules",".mypy_cache"}

def walk(r):
    o=[]
    for dp,dns,fns in os.walk(r):
        dns[:]=[d for d in dns if d not in EX]
        for fn in fns:
            if fn.endswith(".py"): o.append(os.path.join(dp,fn))
    return o

# all service file stems for correspondence
svc_files=[]
for fp in walk(SVC):
    rel=os.path.relpath(fp,BACKEND).replace("\\","/")
    svc_files.append(rel)

def svc_for(ctrl_rel):
    parts=ctrl_rel.split("/"); domain=parts[1]; stem=parts[-1][:-3]
    cand_stems=[stem+"_service", stem, stem.replace("_controller","")+"_service",
                stem.replace("_controller","")]
    for sf in svc_files:
        s=sf.split("/"); sd=s[1]; sn=s[-1][:-3]
        if sd==domain and sn in cand_stems:
            return sf
    # looser: any service file whose name contains stem keyword
    base=stem.replace("_controller","").replace("admin_","").replace("_admin","")
    for sf in svc_files:
        sn=sf.split("/")[-1][:-3]
        if domain in sf and base and (base in sn):
            return sf
    return None

ORM_SIG = ["select(","db.execute(","session.execute(",".query(",".filter(",".order_by(",
           "func.","and_(","or_(","text(","update(","delete(","insert(","bulk_save",
           "with db.begin","with session.begin"]

rows=[]
for fp in walk(CTRL):
    rel=os.path.relpath(fp,BACKEND).replace("\\","/")
    parts=rel.split("/"); domain=parts[1] if len(parts)>2 else ""; fname=parts[-1]
    try: src=open(fp,encoding="utf-8",errors="ignore").read()
    except: continue
    is_shim=(domain in SHIM) or fname=="__init__.py"
    try: tree=ast.parse(src)
    except: tree=None
    nfor=nif=nfunc=nclass=0
    has_orm=False; orm_lines=[]
    if tree:
        for n in ast.walk(tree):
            if isinstance(n,ast.For): nfor+=1
            elif isinstance(n,ast.If): nif+=1
            elif isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)): nfunc+=1
            elif isinstance(n,ast.ClassDef): nclass+=1
    for sig in ORM_SIG:
        if sig in src:
            has_orm=True
            # record first line
            for i,l in enumerate(src.split("\n"),1):
                if sig in l:
                    orm_lines.append((i,sig,l.strip()[:80])); break
    svc=svc_for(rel) if not is_shim else "(shim)"
    svc_imp = ("from services." in src) or ("import services" in src)
    rows.append({"rel":rel,"domain":domain,"is_shim":is_shim,"nfor":nfor,"nif":nif,
                 "nfunc":nfunc,"nclass":nclass,"has_orm":has_orm,"orm":orm_lines[:3],
                 "svc":svc,"svc_imp":svc_imp,"lines":src.count("\n")+1,"name":fname})

print("="*100)
print("CONTROLLERS WITH INLINE ORM / DB-LOGIC SIGNALS (potential non-shifted logic)")
print("="*100)
orm_rows=[r for r in rows if (not r["is_shim"]) and r["has_orm"]]
print("count=%d of %d non-shim controllers" % (len(orm_rows), sum(1 for r in rows if not r["is_shim"])))
for r in sorted(orm_rows, key=lambda x:-(x["nfor"]+x["nif"])):
    print("\n### %s  for=%d if=%d funcs=%d svc=%s svc_imp=%s" % (
        r["rel"],r["nfor"],r["nif"],r["nfunc"],r["svc"] or "NONE",r["svc_imp"]))
    for i,sig,l in r["orm"]:
        print("    L%-4d %-16s %s" % (i,sig,l))

print("\n\n" + "="*100)
print("CONTROLLERS WITH NO SERVICE IMPORT AND SUBSTANTIAL BODY (may not delegate)")
print("="*100)
susp=[r for r in rows if (not r["is_shim"]) and (not r["svc_imp"]) and (r["nfunc"]>=2 or r["lines"]>80)]
for r in sorted(susp,key=lambda x:-x["lines"]):
    print("  %-50s lines=%-4d funcs=%-3d svc=%s" % (r["rel"],r["lines"],r["nfunc"],r["svc"] or "NONE"))

print("\n\nDELEGATION SUMMARY (non-shim controllers):")
ns=[r for r in rows if not r["is_shim"]]
print("  total non-shim controllers : %d" % len(ns))
print("  import/call services       : %d" % sum(1 for r in ns if r["svc_imp"]))
print("  have matched service file  : %d" % sum(1 for r in ns if r["svc"]))
print("  NO matched service file    : %d" % sum(1 for r in ns if not r["svc"]))
with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_progress\ctrl_v2.json","w") as f:
    json.dump(rows,f)
print("[saved _progress/ctrl_v2.json]")
