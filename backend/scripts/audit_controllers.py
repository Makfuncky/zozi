"""Comprehensive controller audit — reuses auto_router's exact logic."""
import ast, os, re, sys, importlib.util
from typing import Optional

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
BACKEND = os.path.dirname(ROOT)
sys.path.insert(0, BACKEND)
import scripts.retired_auto_router as ar

KNOWN_DEPS = ar.KNOWN_DEPS
PATH_RE = re.compile(r"{([^}]+)}")

def handler_issues(meta, module):
    """Mirror assign_roles to detect injection defects."""
    issues = []
    path_names = set(PATH_RE.findall(meta["path"]))
    deps = meta["deps"]
    # dep -> required param name
    dep_to_param = {d: KNOWN_DEPS.get(d, (d, None, None))[0] for d in deps}
    param_names = {p["name"] for p in meta["params"]}
    # 1) every declared dep must have its matching param (else dependency NOT injected)
    for d, pname in dep_to_param.items():
        if pname not in param_names:
            issues.append(f"dep '{d}' declared but handler has no '{pname}' param -> dependency NOT injected")
    # 2) any param whose name matches a KNOWN_DEPS param must be declared as a dep
    #    (otherwise the generator treats it as a body/query field -> wrong value)
    for p in meta["params"]:
        n = p["name"]
        if n in ("current_user", "db", "background_tasks", "request"):
            # find which dep uses this param
            matched_dep = None
            for d, pname in dep_to_param.items():
                if pname == n:
                    matched_dep = d
                    break
            if matched_dep is None:
                issues.append(f"param '{n}' looks like an injected dependency but no matching dep declared -> treated as body/query field")
    return issues

def check_controller_source(path):
    issues = []
    text = open(path, encoding="utf-8").read()
    tree = ast.parse(text)
    # imports fastapi?
    imports_fastapi = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "fastapi":
            imports_fastapi = True
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] == "fastapi":
                    imports_fastapi = True
    # imports contract decorators from auto_router?
    imports_contract = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "infrastructure.routing.route_contract":
            if any(n.name in ("route","get","post","put","patch","delete") for n in node.names):
                imports_contract = True
    # forbidden patterns
    for pat in ar.FORBIDDEN:
        if pat in text:
            issues.append(f"FORBIDDEN pattern {pat!r}")
    if imports_fastapi:
        issues.append("controller imports fastapi directly (contract violation)")
    if not imports_contract:
        issues.append("controller does not import contract decorators from auto_router")
    return issues, imports_fastapi

def main():
    modules = ar.scan_controllers()
    total_issues = 0
    print(f"=== Scanning {len(modules)} decorated controller modules ===\n")
    for mi in modules:
        mod = mi["module"]
        file_issues, imports_fastapi = check_controller_source(os.path.join(ROOT, mi["file"]))
        route_issues = []
        for meta in mi["routes"]:
            if meta["skip"]:
                continue
            route_issues.extend(handler_issues(meta, mod))
            # flag routes whose path has no surface prefix
            if ar._surface_for_path(meta["path"]) is None:
                route_issues.append(f"path {meta['path']!r} has NO surface prefix (generator would mis-prefix / crash)")
        # compile generated router
        gen = None
        gen_compile_ok = True
        gen_err = ""
        try:
            gen = ar.generate_router_file(mi, collisions=set())
        except Exception as e:
            gen_compile_ok = False
            gen_err = f"{type(e).__name__}: {e}"
        gen_compile_ok = True
        gen_err = ""
        if gen:
            try:
                compile(gen, f"<gen {mod}>", "exec")
            except SyntaxError as e:
                gen_compile_ok = False
                gen_err = str(e)
        flags = []
        if file_issues: flags.append("FILE_ISSUES")
        if route_issues: flags.append("ROUTE_ISSUES")
        if not gen_compile_ok: flags.append("GEN_COMPILE_FAIL")
        status = "OK" if not (file_issues or route_issues or not gen_compile_ok) else "PROBLEM"
        print(f"[{status}] {mod}  routes={len(mi['routes'])} {(' '.join(flags)) if flags else ''}")
        for fi in file_issues:
            print(f"    FILE: {fi}")
        for ri in route_issues:
            print(f"    ROUTE [{meta['method']} {meta['path']} {meta['func']}]: {ri}")
        if not gen_compile_ok:
            print(f"    GEN COMPILE: {gen_err}")
        total_issues += len(file_issues) + len(route_issues) + (0 if gen_compile_ok else 1)
    print(f"\n=== TOTAL ISSUES: {total_issues} ===")
    return 1 if total_issues else 0

if __name__ == "__main__":
    raise SystemExit(main())
