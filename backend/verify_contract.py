import ast, os, sys, importlib.util
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from routers.generated import auto_router as ar

CONTROLLERS = os.path.join(ROOT, "controllers")
PATH_RE = ar.PATH_RE
KNOWN_DEPS = ar.KNOWN_DEPS  # dep -> (canonical_param, type, wiring)
# reverse: dep -> canonical param name used in handler
DEP_PARAM = {d: KNOWN_DEPS[d][0] for d in KNOWN_DEPS}

def _const_list(v):
    if isinstance(v, ast.List): return [e.value for e in v.elts if isinstance(e, ast.Constant)]
    return []
def _const_str(v):
    return v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else None
def _const_bool(v):
    return bool(v.value) if isinstance(v, ast.Constant) and isinstance(v.value, bool) else False

issues=[]
for dp,_,files in os.walk(CONTROLLERS):
    for fn in files:
        if not fn.endswith(".py") or fn=="__init__.py": continue
        full=os.path.join(dp,fn)
        rel=os.path.relpath(full,ROOT).replace(os.sep,".")
        mod=rel[:-3]
        tree=ast.parse(open(full,encoding="utf-8").read(),filename=full)
        for node in ast.walk(tree):
            if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
            for dec in node.decorator_list:
                m=ar.parse_decorator(dec)
                if not m: continue
                params=[a.arg for a in node.args.args]+[a.arg for a in node.args.kwonlyargs]
                if node.args.kwarg: params.append(node.args.kwarg.arg)
                path_names=set(PATH_RE.findall(m["path"]))
                deps=set(m["deps"]); query=set(m["query"])
                # path params must be handler params
                for pn in path_names:
                    if pn not in params:
                        issues.append((mod,node.name,m["method"],m["path"],f"path param '{{{pn}}}' NOT a handler param"))
                # deps must bind to a handler param (canonical name)
                for d in deps:
                    cp=DEP_PARAM.get(d)
                    if cp and cp not in params:
                        issues.append((mod,node.name,m["method"],m["path"],f"dep '{d}' declared but handler has no '{cp}' param -> auth/dep NOT injected"))
                # query names must be handler params
                for q in query:
                    if q not in params:
                        issues.append((mod,node.name,m["method"],m["path"],f"query '{q}' NOT a handler param"))
                # body set -> exactly one non-path/non-dep leftover
                if m["body"] is not None:
                    left=[p for p in params if p not in path_names and p not in {DEP_PARAM.get(d) for d in deps} and p not in query]
                    if len(left)!=1:
                        issues.append((mod,node.name,m["method"],m["path"],f"body= set but {len(left)} candidate args {left}"))
                # handler params must each be accounted for (path/dep/query/body/leftover)
                accounted=set(path_names)|{DEP_PARAM.get(d) for d in deps if DEP_PARAM.get(d)}|set(query)
                for p in params:
                    if p in accounted: continue
                    # leftovers are fine (become bodyfield/query/body)
                if m.get("permissions") and "current_user" not in params:
                    issues.append((mod,node.name,m["method"],m["path"],"permissions set but no current_user param -> RBAC not injected"))

print("=== Contract-conformance issues across decorated routes ===")
print("count:", len(issues))
for i in issues: print("  ", i)
