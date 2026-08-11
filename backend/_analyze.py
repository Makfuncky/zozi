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

def called_in_func(node):
    names=set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            names.add(n.func.id)
    return names

def controller_funcs(fp):
    try:
        tree=ast.parse(open(fp,encoding="utf-8").read())
    except SyntaxError:
        return set(), set()
    names=set(); asyncs=set()
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            names.add(n.name)
            if isinstance(n,ast.AsyncFunctionDef): asyncs.add(n.name)
    return names, asyncs

ctrl_index={}
for dirpath,_,files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn=="__init__.py": continue
        fp=os.path.join(dirpath,fn)
        text=open(fp,encoding="utf-8").read()
        if "from routers.generated.auto_router import" in text: continue
        if re.search(r"router\s*[:=].*APIRouter", text) or ("router = APIRouter" in text): continue
        rel=os.path.relpath(fp,ROOT)[:-3].replace(os.sep,".")
        funcs,asyncs=controller_funcs(fp)
        ctrl_index[rel]=(fp,funcs,asyncs,text)

def alias_map(tree):
    """Map local alias -> (controller_module, orig_func) for controllers.* imports,
    including `from controllers import X` (X becomes module controllers.X) and
    `import controllers.X`."""
    m={}  # name -> (module, func_or_None)
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("controllers"):
            for a in n.names:
                if n.module == "controllers":
                    # from controllers.catalog import banner_controller  -> module controllers.catalog.banner_controller
                    m[a.asname or a.name]=("controllers."+(a.asname or a.name), None)
                else:
                    m[a.asname or a.name]=(n.module, a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                if (a.name or "").startswith("controllers."):
                    m[a.asname or a.name]=("controllers."+(a.name.split("controllers.",1)[1]), None)
    return m

def called_attr_modules(node, amap):
    """Return set of (module, func) for Name calls + module.attr calls where module is a controllers alias."""
    out=set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in amap:
            mod,fn=amap[n.func.id]
            out.add((mod, fn))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id in amap:
            mod,fn=amap[n.func.value.id]
            out.add((mod, n.func.attr))
    return out

def router_meta(fp):
    text=open(fp,encoding="utf-8").read()
    if "AUTO-GENERATED" in text: return None
    try: tree=ast.parse(text)
    except SyntaxError: return None
    prefix=""
    for n in ast.walk(tree):
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=="router":
                    for kw in (n.value.keywords if isinstance(n.value,ast.Call) else []):
                        if kw.arg=="prefix" and isinstance(kw.value,ast.Constant):
                            prefix=kw.value.value
    amap=alias_map(tree)
    routes=[]
    for node in ast.walk(tree):
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
        for dec in node.decorator_list:
            if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr in ("get","post","put","patch","delete"):
                path=""
                if dec.args and isinstance(dec.args[0],ast.Constant): path=dec.args[0].value
                called=called_attr_modules(node, amap)
                routes.append({"method":dec.func.attr.upper(),"path":prefix+path,
                               "called":called,"func":node.name})
                break
    if not routes: return None
    return {"prefix":prefix,"routes":routes,"file":fp,"text":text}

router_index={}
for fn in os.listdir(ROUTERS):
    if not fn.endswith(".py") or fn=="__init__.py": continue
    m=router_meta(os.path.join(ROUTERS,fn))
    if m: router_index[fn]=m

def targets_of(m):
    return set(c for r in m["routes"] for c in r["called"])

clean_wrappers=defaultdict(list)
for rfn,m in router_index.items():
    all_called=targets_of(m)
    ctrl_mods={cm for (cm,fn) in all_called if cm in ctrl_index}
    if len(ctrl_mods)!=1: continue
    mod=next(iter(ctrl_mods))
    cfuncs=ctrl_index[mod][1]
    # every route call must resolve to this mod (local non-controller helpers allowed)
    ok=all(((cm in (mod,None)) for (cm,fn) in r["called"]) for r in m["routes"])
    if ok and len(all_called)>=1:
        clean_wrappers[mod].append((rfn,m))

print("DEBUG clean_wrappers count:", len(clean_wrappers))
for mod, wrappers in sorted(clean_wrappers.items()):
    print(f"  DEBUG {mod}: {len(wrappers)} wrappers -> {[w[0] for w in wrappers]}")
print()

results=[]
for mod, wrappers in sorted(clean_wrappers.items()):
    if len(wrappers)!=1: continue
    rfn,m=wrappers[0]
    fp,funcs,asyncs,text=ctrl_index[mod]
    routes=m["routes"]
    targets={(cm,fn) for r in m["routes"] for (cm,fn) in r["called"]}
    ctrl_targets={(cm,fn) for (cm,fn) in targets if cm==mod}
    reasons=[]
    if re.search(r"\.(commit|flush)\(", text): reasons.append("commit/flush in controller (#3)")
    if len(ctrl_targets)!=len(routes): reasons.append(f"1:1 mismatch (routes={len(routes)} ctrl_targets={len(ctrl_targets)})")
    surfs={surface_for(r["path"]) for r in routes}; surfs.discard(None)
    if len(surfs)!=1: reasons.append(f"multi-surface {sorted(x[0] for x in surfs)}")
    if reasons:
        print(f"# NOT ELIGIBLE {mod} <- {rfn}: {'; '.join(reasons)}")
        continue
    results.append((mod,rfn,surfs.pop(),routes))

for mod,rfn,surf,routes in sorted(results):
    print(f"ELIGIBLE {mod}  <- {rfn}  surface={surf[0]}  nroutes={len(routes)}")
    for r in routes:
        print(f"   {r['method']:7} {r['path']:55} -> {sorted(f for (_,f) in r['called'])}")
print(f"\nTOTAL ELIGIBLE: {len(results)}")
