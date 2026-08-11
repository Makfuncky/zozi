import os, ast, json

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
CTRL = os.path.join(BACKEND, "controllers")
SVC = os.path.join(BACKEND, "services")
SHIM_DIRS = {"admin", "communication", "country"}
EXCLUDE = {"__pycache__", "venv", ".git", "_extra_files", "node_modules", ".mypy_cache"}

def walk(root):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in EXCLUDE]
        for fn in fns:
            if fn.endswith(".py"):
                out.append(os.path.join(dp, fn))
    return out

WRITE_ATTRS = {"add","commit","flush","delete","merge","bulk_save_objects",
               "bulk_insert_mappings","refresh","bulk_update","bulk_delete","expire"}

def find_w1(path, src):
    hits = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return hits
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr in WRITE_ATTRS:
                v = node.value
                name = None
                if isinstance(v, ast.Name):
                    name = v.id
                elif isinstance(v, ast.Attribute) and v.attr in ("db","session"):
                    name = v.attr
                if name in ("db","session"):
                    snip = src.split("\n")[node.lineno-1].strip()
                    hits.append((node.lineno, "db.%s" % node.attr, snip))
            if node.attr == "execute":
                v = node.value
                name = v.id if isinstance(v, ast.Name) else (v.attr if isinstance(v, ast.Attribute) else None)
                if name in ("db","session"):
                    snip = src.split("\n")[node.lineno-1].strip()
                    hits.append((node.lineno, "db.execute", snip))
        if isinstance(node, ast.With):
            for item in node.items:
                ce = item.context_expr
                if isinstance(ce, ast.Call):
                    f = ce.func
                    fn = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                    arg = f.value.id if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else ""
                    if fn == "begin" and arg in ("db","session"):
                        snip = src.split("\n")[node.lineno-1].strip()
                        hits.append((node.lineno, "with db.begin", snip))
    return hits

results = []
for fpath in walk(CTRL):
    rel = os.path.relpath(fpath, BACKEND).replace("\\","/")
    parts = rel.split("/")
    domain = parts[1] if len(parts) > 2 else ""
    fname = parts[-1]
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
            src = fh.read()
    except Exception:
        continue
    is_shim = (domain in SHIM_DIRS) or fname == "__init__.py"
    w1 = find_w1(fpath, src)
    q = src.count(".query("); flt = src.count(".filter(")
    exe = src.count("db.execute") + src.count("session.execute")
    loops = src.count(" for ") + src.count("\n    for ") + src.count("\n\tfor ")
    svc_imp = src.count("from services.") + src.count("import services")
    nfuncs = src.count("def ") + src.count("async def ")
    results.append({"rel":rel,"domain":domain,"file":fname,"is_shim":is_shim,
        "w1":w1,"w1_count":len(w1),"query":q,"filter":flt,"execute":exe,
        "loops":loops,"svc_imports":svc_imp,"n_funcs":nfuncs,"lines":src.count("\n")+1})

def expected_service(rel):
    parts = rel.split("/")
    domain = parts[1]; name = parts[-1][:-3]
    if name.endswith("_controller"):
        svcname = name[:-len("_controller")] + "_service"
    else:
        svcname = name + "_service"
    for c in [os.path.join(SVC, domain, svcname+".py"),
              os.path.join(SVC, domain, name+"_service.py"),
              os.path.join(SVC, domain, name+".py")]:
        if os.path.isfile(c):
            return os.path.relpath(c, BACKEND).replace("\\","/")
    return None

for r in results:
    r["svc"] = expected_service(r["rel"]) if not r["is_shim"] else "(shim)"

print("="*100)
print("CONTROLLER DB-WRITE (W1) VIOLATIONS")
print("="*100)
viol = [r for r in results if r["w1_count"]>0]
viol_ns = [r for r in viol if not r["is_shim"]]
print("\nTotal controller files: %d" % len(results))
print("Files with >=1 W1 hit: %d (non-shim: %d, shim: %d)" % (len(viol), len(viol_ns), len(viol)-len(viol_ns)))
print("\n--- NON-SHIM controllers with direct DB writes ---")
for r in sorted(viol_ns, key=lambda x:-x["w1_count"]):
    print("\n### %s  (lines=%d funcs=%d svc_imp=%d svc=%s)" % (
        r["rel"], r["lines"], r["n_funcs"], r["svc_imports"], r["svc"]))
    for ln,kind,snip in r["w1"][:12]:
        print("   L%-4d %-12s %s" % (ln, kind, snip[:95]))

print("\n\n" + "="*100)
print("TOP CONTROLLERS BY BUSINESS-LOGIC WEIGHT")
print("="*100)
for r in sorted(results, key=lambda x:-(x["query"]+x["filter"]+x["execute"]+x["loops"]))[:25]:
    if r["is_shim"]:
        continue
    print("  %-52s q=%-3d f=%-3d e=%-3d loops=%-3d svc_imp=%-3d svc=%s" % (
        r["rel"], r["query"], r["filter"], r["execute"], r["loops"], r["svc_imports"], r["svc"] or "NONE"))

print("\n\n" + "="*100)
print("CONTROLLERS WITH NO CORRESPONDING SERVICE (logic possibly not shifted)")
print("="*100)
no_svc = [r for r in results if (not r["is_shim"]) and r["svc"] is None and (r["query"]+r["filter"]+r["execute"])>0]
for r in sorted(no_svc, key=lambda x:-(x["query"]+x["filter"]+x["execute"])):
    print("  %-52s q=%-3d f=%-3d e=%-3d funcs=%-3d" % (r["rel"], r["query"], r["filter"], r["execute"], r["n_funcs"]))

with open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_progress\ctrl_shift_analysis.json","w") as f:
    json.dump(results, f)
print("\n[saved _progress/ctrl_shift_analysis.json ; total files=%d]" % len(results))
