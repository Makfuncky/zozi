import os, ast, json
BACKEND=r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
CTRL=os.path.join(BACKEND,"controllers"); SVC=os.path.join(BACKEND,"services")
SHIM={"admin","communication","country"}; EX={"__pycache__","venv",".git","_extra_files","node_modules",".mypy_cache"}
def walk(r):
    o=[]
    for dp,dns,fns in os.walk(r):
        dns[:]=[d for d in dns if d not in EX]
        for fn in fns:
            if fn.endswith(".py"): o.append(os.path.join(dp,fn))
    return o
def funcs(fp):
    try: t=ast.parse(open(fp,encoding="utf-8",errors="ignore").read())
    except: return set()
    s=set()
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and not n.name.startswith("_"):
            s.add(n.name)
    return s
ctrl_funcs={}
for fp in walk(CTRL):
    rel=os.path.relpath(fp,BACKEND).replace("\\","/")
    parts=rel.split("/"); dom=parts[1] if len(parts)>2 else ""; fn=parts[-1]
    if dom in SHIM or fn=="__init__.py": continue
    ctrl_funcs[rel]=funcs(fp)
svc_all=set()
svc_by_domain={}
for fp in walk(SVC):
    rel=os.path.relpath(fp,BACKEND).replace("\\","/")
    parts=rel.split("/"); dom=parts[1] if len(parts)>2 else ""
    f=funcs(fp)
    svc_by_domain.setdefault(dom,set()).update(f)
    svc_all.update(f)
# duplication: controller public func also defined in services (same name) -> possible leftover duplicate
print("CONTROLLER FUNCTIONS THAT ALSO EXIST IN SERVICES (potential duplicated logic):")
cnt=0
for rel,fs in ctrl_funcs.items():
    dom=rel.split("/")[1]
    svcfs=svc_by_domain.get(dom,set())
    inter=fs & svcfs
    if inter:
        cnt+=1
        print("  %s  <-> services/%s : %s" % (rel, dom, ", ".join(sorted(inter)[:8])))
print("total controllers with name overlap: %d" % cnt)
# controllers with DB/ORM logic that ALSO have same-name service func (strong duplicate signal)
ORM=["db.add","db.commit","db.delete","db.merge","db.query","db.execute",".filter(","select(","db_read_query","bulk_"]
print("\nCONTROLLERS WITH INLINE ORM THAT ALSO HAVE SAME-NAMED SERVICE FUNC (likely incomplete shift / duplication):")
for rel,fs in ctrl_funcs.items():
    try: src=open(os.path.join(BACKEND,rel),encoding="utf-8",errors="ignore").read()
    except: continue
    if not any(s in src for s in ORM): continue
    dom=rel.split("/")[1]
    inter=fs & svc_by_domain.get(dom,set())
    if inter:
        print("  %s : %s" % (rel, ", ".join(sorted(inter)[:8])))
