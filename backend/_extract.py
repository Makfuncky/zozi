from __future__ import annotations
import ast, os, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTROLLERS = os.path.join(ROOT, "controllers")
ROUTERS = os.path.join(ROOT, "routers")

SURFACES = {"admin":"/api/v1/admin","customer":"/api/v1/customer","supplier":"/api/v1/supplier",
            "logistics":"/api/v1/logistics","public":"/api/v1","system":"/api/v1/system","internal":"/api/v1/internal"}
def surface_for(p):
    best=None
    for n,pr in SURFACES.items():
        if p.startswith(pr) and (best is None or len(pr)>len(best[1])):
            best=(n,pr)
    return best

def router_meta(fp):
    text=open(fp,encoding="utf-8-sig").read()
    if "AUTO-GENERATED" in text:
        return None
    tree=ast.parse(text)
    prefix=""
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=="router":
                    for kw in (n.value.keywords if isinstance(n.value,ast.Call) else []):
                        if kw.arg=="prefix" and isinstance(kw.value,ast.Constant):
                            prefix=kw.value.value
    imports=defaultdict(set)
    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom) and n.module and n.module.startswith("controllers"):
            for a in n.names:
                imports[n.module].add(a.asname or a.name)
    routes=[]
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr in ("get","post","put","patch","delete"):
                path=""
                if dec.args and isinstance(dec.args[0],ast.Constant):
                    path=dec.args[0].value
                rm={}
                for kw in dec.keywords:
                    if kw.arg in ("response_model","status_code","tags","summary","description") and isinstance(kw.value,ast.Constant):
                        rm[kw.arg]=kw.value.value
                routes.append({"method":dec.func.attr.upper(),"path":prefix+path,"func":node.name,"deco_kwargs":rm})
                break
    return {"prefix":prefix,"imports":imports,"routes":routes,"file":fp}

def is_self_router(fp):
    text=open(fp,encoding="utf-8-sig").read()
    return bool(re.search(r"router\s*[:=].*APIRouter", text)) or ("router = APIRouter" in text)

# build router index
router_index={}
for fn in os.listdir(ROUTERS):
    if not fn.endswith(".py") or fn=="__init__.py":
        continue
    fp=os.path.join(ROUTERS,fn)
    m=router_meta(fp)
    if m:
        router_index[fn]=m

for dirpath,_,files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn=="__init__.py":
            continue
        fp=os.path.join(dirpath,fn)
        text=open(fp,encoding="utf-8-sig").read()
        if "from routers.generated.auto_router import" in text:
            continue
        if is_self_router(fp):
            continue
        rel=os.path.relpath(fp,ROOT)[:-3].replace(os.sep,".")
        refs=[(rf,m) for rf,m in router_index.items() if rel in m["imports"]]
        if len(refs)!=1:
            continue
        rf,m=refs[0]
        if m["imports"][rel] & {"router"}:
            continue  # imports a router symbol -> self-router style
        # router must import ONLY this controller module
        if set(m["imports"].keys())!={rel}:
            continue
        # single surface
        surfs={surface_for(r["path"]) for r in m["routes"]}
        surfs.discard(None)
        if len(surfs)!=1:
            print(f"# SKIP (multi-surface) {rel}: {sorted(x[0] for x in surfs)}")
            continue
        if re.search(r"\b(db|session)\.(commit|flush)\b", text):
            print(f"# SKIP (commit/flush) {rel}")
            continue
        print(f"ELIGIBLE {rel}  <- router {rf} surface={list(surfs)[0][0]} prefix={m['prefix']}")
        for r in m["routes"]:
            print(f"   {r['method']:7} {r['path']:50} {r['func']}  {r['deco_kwargs']}")
