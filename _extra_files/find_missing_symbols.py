import ast, pathlib

def top_names(modpath):
    src = pathlib.Path(modpath).read_text()
    tree = ast.parse(src)
    names = set()
    for n in tree.body:
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                names.add(a.asname or a.name)
        elif isinstance(n, ast.Import):
            for a in n.names:
                names.add((a.asname or a.name).split('.')[0])
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    names.add(t.id)
    return names

def needed_from_controller(ctrlpath):
    src = pathlib.Path(ctrlpath).read_text()
    tree = ast.parse(src)
    res = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("services."):
            for a in n.names:
                res.append((n.module, a.name))
    return res

pairs = {
 "routers/logistics_logistics_status.py": "services/logistics/logistics_logistics_status_service.py",
 "routers/logistics_partner_verify.py": "services/logistics/logistics_partner_verify_service.py",
}
for router, svc in pairs.items():
    rsrc = pathlib.Path(router).read_text()
    rtree = ast.parse(rsrc)
    ctrl = None
    for n in ast.walk(rtree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.startswith("controllers."):
            ctrl = n.module
    print("ROUTER", router, "-> CTRL", ctrl, "-> SVC", svc)
    ctrlpath = ctrl.replace(".", "/") + ".py"
    need = needed_from_controller(ctrlpath)
    svcnames = top_names(svc)
    missing = [(m, name) for (m, name) in need if name not in svcnames]
    print("  missing count:", len(missing))
    for m, name in missing:
        print("    ", name, "   (ctrl imports from", m + ")")
