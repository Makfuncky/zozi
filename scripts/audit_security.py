#!/usr/bin/env python3
"""Generate _generated/SECURITY_POSTURE.md from static code analysis."""
from __future__ import annotations

import ast
import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
GENERATED_DIR = REPO_ROOT / "_generated"
OUTPUT_FILE = GENERATED_DIR / "SECURITY_POSTURE.md"

MIDDLEWARE_FILE = BACKEND_DIR / "middleware" / "orchestrator.py"
ROOT_ROUTERS_DIR = BACKEND_DIR / "modules"
ROLES_FILE = BACKEND_DIR / "rbac" / "roles.py"
CATALOG_FILE = BACKEND_DIR / "rbac" / "catalog.py"
SECRETS_SCRIPT = REPO_ROOT / "scripts" / "audit_secrets.py"

CANONICAL_SCHEMAS = [
    "accounts", "analytics", "audit", "catalog", "comms", "country",
    "customers", "finance", "governance", "hr", "logistics", "orders",
    "promotions", "security", "suppliers",
]

HTTP_METHODS = {"get", "post", "put", "delete", "patch"}


def get_git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError("git rev-parse HEAD failed")
    return result.stdout.strip()


def extract_middleware_pipeline() -> list[dict]:
    source = MIDDLEWARE_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    pipeline: list[dict] = []

    layer_lists = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    if name.startswith("_") and name.isupper():
                        layer_lists.append((name, node.value))
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name):
                name = target.id
                if name.startswith("_") and name.isupper() and node.value is not None:
                    layer_lists.append((name, node.value))

    for layer_name, list_node in sorted(layer_lists, key=lambda x: x[0]):
        if not isinstance(list_node, ast.List):
            continue
        for elt in list_node.elts:
            if isinstance(elt, ast.Name):
                cls_name = elt.id
                lineno = elt.lineno
                pipeline.append({
                    "class": cls_name,
                    "file": f"backend/middleware/orchestrator.py",
                    "line": lineno,
                    "layer": layer_name,
                })

    pipeline.sort(key=lambda x: (x["layer"], x["line"]))
    return pipeline


def _find_router_decorators(func_node) -> list[dict]:
    endpoints = []
    for decorator in func_node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name):
            continue
        if func.value.id != "router":
            continue
        method = func.attr
        if method not in HTTP_METHODS:
            continue
        if not decorator.args:
            continue
        path_arg = decorator.args[0]
        if isinstance(path_arg, ast.Constant):
            path = path_arg.value
        else:
            continue
        endpoints.append({
            "method": method.upper(),
            "path": path,
            "decorator": decorator,
        })
    return endpoints


def _get_arg_defaults(func_node) -> list[ast.AST | None]:
    defaults = list(func_node.args.defaults)
    while len(defaults) < len(func_node.args.args):
        defaults.insert(0, None)
    return defaults


def _is_auth_call(default: ast.AST) -> tuple[bool, str]:
    if not isinstance(default, ast.Call):
        return False, ""
    func = default.func
    if isinstance(func, ast.Name):
        if func.id == "Depends":
            if default.args and isinstance(default.args[0], ast.Name):
                inner = default.args[0].id
                if inner in ("get_current_user", "require_admin", "require_super_admin", "get_current_user_optional"):
                    return True, inner
            if default.args and isinstance(default.args[0], ast.Attribute):
                inner_attr = default.args[0].attr
                if inner_attr in ("get_current_user", "require_admin", "get_current_user_optional"):
                    return True, inner_attr
        elif func.id in ("get_current_user", "require_admin", "require_super_admin", "get_current_user_optional"):
            return True, func.id
    elif isinstance(func, ast.Attribute):
        if func.attr == "Depends":
            if default.args and isinstance(default.args[0], ast.Name):
                inner = default.args[0].id
                if inner in ("get_current_user", "require_admin", "require_super_admin", "get_current_user_optional"):
                    return True, inner
        elif func.attr in ("get_current_user", "require_admin", "get_current_user_optional"):
            return True, func.attr
    return False, ""


def _has_auth_dependency(func_node) -> tuple[bool, str]:
    defaults = _get_arg_defaults(func_node)
    for arg, default in zip(func_node.args.args, defaults):
        ann = arg.annotation
        if ann is not None:
            ann_str = ast.unparse(ann) if hasattr(ast, "unparse") else ""
            if "get_current_user" in ann_str or "require_admin" in ann_str:
                return True, ann_str
        is_auth, name = _is_auth_call(default)
        if is_auth:
            return True, name
    return False, ""


def _find_rbac_gates(func_node) -> tuple[str, str]:
    rbac_gate = "NONE"
    auth_dep = "no"
    defaults = _get_arg_defaults(func_node)
    for arg, default in zip(func_node.args.args, defaults):
        if not isinstance(default, ast.Call):
            continue
        func = default.func
        if isinstance(func, ast.Name):
            if func.id == "require_feature":
                if default.args and isinstance(default.args[0], ast.Constant):
                    rbac_gate = default.args[0].value
            elif func.id == "require_module":
                if default.args and isinstance(default.args[0], ast.Constant):
                    rbac_gate = f"module:{default.args[0].value}"
            elif func.id == "Depends":
                is_auth, _ = _is_auth_call(default)
                if is_auth:
                    auth_dep = "yes"
                if default.args and isinstance(default.args[0], ast.Call):
                    inner = default.args[0]
                    inner_func = inner.func
                    if isinstance(inner_func, ast.Name) and inner_func.id == "require_feature":
                        if inner.args and isinstance(inner.args[0], ast.Constant):
                            rbac_gate = inner.args[0].value
                    elif isinstance(inner_func, ast.Attribute) and inner_func.attr == "require_feature":
                        if inner.args and isinstance(inner.args[0], ast.Constant):
                            rbac_gate = inner.args[0].value
        elif isinstance(func, ast.Attribute):
            if func.attr == "require_feature":
                if default.args and isinstance(default.args[0], ast.Constant):
                    rbac_gate = default.args[0].value
            elif func.attr == "require_module":
                if default.args and isinstance(default.args[0], ast.Constant):
                    rbac_gate = f"module:{default.args[0].value}"
    if rbac_gate == "NONE":
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "require_feature":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        rbac_gate = node.args[0].value
                elif isinstance(func, ast.Attribute) and func.attr == "require_feature":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        rbac_gate = node.args[0].value
    return rbac_gate, auth_dep


def extract_endpoints() -> list[dict]:
    endpoints = []
    router_files = sorted(ROOT_ROUTERS_DIR.glob("*/routers/*.py"))

    for router_file in router_files:
        if router_file.name == "__init__.py":
            continue
        module_path = (
            str(router_file.relative_to(BACKEND_DIR))
            .replace(os.sep, ".")
            .removesuffix(".py")
        )
        module_name = router_file.parent.parent.name

        source = router_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            route_decorators = _find_router_decorators(node)
            if not route_decorators:
                continue

            rbac_gate, auth_dep = _find_rbac_gates(node)
            for dec in route_decorators:
                endpoints.append({
                    "method": dec["method"],
                    "path": dec["path"],
                    "module": module_name,
                    "file": module_path,
                    "line": node.lineno,
                    "rbac_gate": rbac_gate,
                    "auth_dep": auth_dep,
                })

    endpoints.sort(key=lambda e: (e["module"], e["path"]))
    return endpoints


def extract_features() -> dict[str, dict]:
    features_by_domain: dict[str, dict] = {}
    features_dirs = sorted((BACKEND_DIR / "domains").glob("*/"))
    for domain_dir in features_dirs:
        features_file = domain_dir / "features.py"
        if not features_file.exists():
            continue
        source = features_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "FEATURES":
                        if isinstance(node.value, ast.Dict):
                            keys = []
                            for key_node in node.value.keys:
                                if isinstance(key_node, ast.Constant):
                                    keys.append(key_node.value)
                            features_by_domain[domain_dir.name] = {
                                "keys": sorted(keys),
                                "file": f"backend/domains/{domain_dir.name}/features.py",
                                "line": node.lineno,
                            }
                        break
    return features_by_domain


def extract_rbac_roles() -> dict[tuple[str, str], list[str]]:
    source = ROLES_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    role_map: dict[tuple[str, str], list[str]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "ROLE_FEATURES":
                    if isinstance(node.value, ast.Dict):
                        for key_node, val_node in zip(node.value.keys, node.value.values):
                            if isinstance(key_node, ast.Tuple):
                                module = None
                                role = None
                                for elt in key_node.elts:
                                    if isinstance(elt, ast.Constant):
                                        if module is None:
                                            module = elt.value
                                        else:
                                            role = elt.value
                                if module and role and isinstance(val_node, ast.Set):
                                    features = []
                                    for elt in val_node.elts:
                                        if isinstance(elt, ast.Constant):
                                            features.append(elt.value)
                                    role_map[(module, role)] = sorted(features)
    return role_map


def extract_catalog_info() -> dict:
    source = CATALOG_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)

    catalog_keys = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "FEATURE_CATALOG":
                    if isinstance(node.value, ast.Dict):
                        for key_node in node.value.keys:
                            if isinstance(key_node, ast.Constant):
                                catalog_keys.append(key_node.value)
                    break

    return {
        "catalog_keys": sorted(catalog_keys),
        "file": "backend/rbac/catalog.py",
        "line": 1,
    }


def run_secret_scanner() -> str:
    try:
        result = subprocess.run(
            [sys.executable, str(SECRETS_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        output = result.stdout.strip()
        if "FINDINGS:" in output:
            for line in output.splitlines():
                if line.startswith("FINDINGS:"):
                    return line.strip()
        return "No secrets found."
    except Exception as exc:
        return f"Secret scanner error: {exc}"


def find_rls_enforcement() -> list[dict]:
    locations = []
    patterns = ["SET LOCAL app.country_code", "set_rls_context"]
    for py_file in sorted(BACKEND_DIR.rglob("*.py")):
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = str(py_file.relative_to(REPO_ROOT)).replace(os.sep, "/")
        for i, line in enumerate(text.splitlines(), 1):
            for pattern in patterns:
                if pattern in line:
                    locations.append({
                        "file": rel,
                        "line": i,
                        "pattern": pattern,
                    })
    return locations


def build_security_posture(
    middleware: list[dict],
    endpoints: list[dict],
    features: dict[str, dict],
    roles: dict[tuple[str, str], list[str]],
    catalog: dict,
    secret_summary: str,
    rls_locations: list[dict],
) -> str:
    sha = get_git_sha()

    total_endpoints = len(endpoints)
    with_auth = sum(1 for e in endpoints if e["auth_dep"] == "yes")
    with_rbac = sum(1 for e in endpoints if e["rbac_gate"] != "NONE")
    with_both = sum(1 for e in endpoints if e["auth_dep"] == "yes" and e["rbac_gate"] != "NONE")
    neither = sum(1 for e in endpoints if e["auth_dep"] != "yes" and e["rbac_gate"] == "NONE")
    unauthenticated = sum(1 for e in endpoints if e["auth_dep"] != "yes")

    feature_keys_defined = set()
    for domain_info in features.values():
        feature_keys_defined.update(domain_info["keys"])

    feature_keys_referenced = set()
    for e in endpoints:
        if e["rbac_gate"] != "NONE":
            feature_keys_referenced.add(e["rbac_gate"])

    orphan_keys = sorted(feature_keys_defined - feature_keys_referenced)

    module_counts: dict[str, dict] = {}
    for e in endpoints:
        mod = e["module"]
        if mod not in module_counts:
            module_counts[mod] = {"total": 0, "auth": 0, "rbac": 0, "both": 0, "neither": 0}
        module_counts[mod]["total"] += 1
        if e["auth_dep"] == "yes":
            module_counts[mod]["auth"] += 1
        if e["rbac_gate"] != "NONE":
            module_counts[mod]["rbac"] += 1
        if e["auth_dep"] == "yes" and e["rbac_gate"] != "NONE":
            module_counts[mod]["both"] += 1
        if e["auth_dep"] != "yes" and e["rbac_gate"] == "NONE":
            module_counts[mod]["neither"] += 1

    lines: list[str] = []
    lines.append("# Security Posture")
    lines.append("")
    lines.append(f"> Generated by `scripts/audit_security.py`. Do not edit by hand.")
    lines.append(f"> Commit: {sha}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| Middleware classes in pipeline | {len(middleware)} |")
    lines.append(f"| Total endpoints | {total_endpoints} |")
    lines.append(f"| Endpoints with auth dependency | {with_auth} |")
    lines.append(f"| Endpoints with RBAC gate | {with_rbac} |")
    lines.append(f"| Endpoints with both | {with_both} |")
    lines.append(f"| Ungated endpoints (no RBAC) | {total_endpoints - with_rbac} |")
    lines.append(f"| Unauthenticated endpoints (no auth) | {unauthenticated} |")
    lines.append(f"| RBAC feature keys defined | {len(feature_keys_defined)} |")
    lines.append(f"| RBAC feature keys referenced by at least one endpoint | {len(feature_keys_referenced)} |")
    lines.append(f"| Orphan feature keys (defined, unreferenced) | {len(orphan_keys)} |")
    lines.append(f"| Secret scanner findings | {secret_summary.split(':')[1].strip().split()[0] if ':' in secret_summary else 'N/A'} |")
    lines.append("")

    lines.append("## Middleware pipeline")
    lines.append("")
    lines.append("| Order | Class | File:line | Docstring (first line) |")
    lines.append("|---|---|---|---|")
    for i, mw in enumerate(middleware, 1):
        docstring = ""
        cls_file = BACKEND_DIR / mw["file"].replace("backend/", "")
        if cls_file.exists():
            cls_source = cls_file.read_text(encoding="utf-8", errors="ignore")
            cls_match = re.search(rf"class {mw['class']}.*?(?::\n.*?)((?:\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'))", cls_source, re.DOTALL)
            if cls_match:
                docstring = cls_match.group(1).strip("\"' \n")
                first_line = docstring.splitlines()[0].strip() if docstring else ""
                docstring = first_line[:80]
        lines.append(f"| {i} | {mw['class']} | {mw['file']}:{mw['line']} | {docstring} |")
    lines.append("")

    lines.append("## Endpoint gating coverage")
    lines.append("")
    lines.append("| Module | Total | Auth | RBAC | Both | Neither |")
    lines.append("|---|---|---|---|---|---|")
    for mod in sorted(module_counts.keys()):
        c = module_counts[mod]
        lines.append(f"| {mod} | {c['total']} | {c['auth']} | {c['rbac']} | {c['both']} | {c['neither']} |")
    lines.append("")

    lines.append("## Gated endpoints")
    lines.append("")
    lines.append("| Method | Path | Module | File:line | Feature gate literal | Auth dep |")
    lines.append("|---|---|---|---|---|---|")
    gated = [e for e in endpoints if e["rbac_gate"] != "NONE"]
    if gated:
        for e in gated:
            lines.append(f"| {e['method']} | {e['path']} | {e['module']} | {e['file']}:{e['line']} | {e['rbac_gate']} | {e['auth_dep']} |")
    else:
        lines.append("| _(none)_ | | | | | |")
    lines.append("")

    lines.append("## Ungated endpoints")
    lines.append("")
    lines.append("| Method | Path | Module | File:line | Auth dep |")
    lines.append("|---|---|---|---|---|")
    ungated = [e for e in endpoints if e["rbac_gate"] == "NONE"]
    if ungated:
        for e in ungated:
            lines.append(f"| {e['method']} | {e['path']} | {e['module']} | {e['file']}:{e['line']} | {e['auth_dep']} |")
    else:
        lines.append("| _(none)_ | | | | |")
    lines.append("")

    lines.append("## Unauthenticated endpoints")
    lines.append("")
    lines.append("| Method | Path | Module | File:line | RBAC gate |")
    lines.append("|---|---|---|---|---|")
    unauth = [e for e in endpoints if e["auth_dep"] != "yes"]
    if unauth:
        for e in unauth:
            lines.append(f"| {e['method']} | {e['path']} | {e['module']} | {e['file']}:{e['line']} | {e['rbac_gate']} |")
    else:
        lines.append("| _(none)_ | | | | |")
    lines.append("")

    lines.append("## Feature catalog")
    lines.append("")
    lines.append("| Domain | Feature key | Referenced by N endpoints | File:line |")
    lines.append("|---|---|---|---|")
    for domain in sorted(features.keys()):
        info = features[domain]
        for key in info["keys"]:
            count = sum(1 for e in endpoints if e["rbac_gate"] == key)
            lines.append(f"| {domain} | {key} | {count} | {info['file']}:{info['line']} |")
    lines.append("")

    lines.append("## Orphan feature keys")
    lines.append("")
    lines.append("| Domain | Feature key | Defined in file:line |")
    lines.append("|---|---|---|")
    if orphan_keys:
        for domain in sorted(features.keys()):
            info = features[domain]
            for key in info["keys"]:
                if key in orphan_keys:
                    lines.append(f"| {domain} | {key} | {info['file']}:{info['line']} |")
    else:
        lines.append("| _(none)_ | | |")
    lines.append("")

    lines.append("## Role → feature mapping")
    lines.append("")
    lines.append("| Module | Role | Feature keys granted | File:line |")
    lines.append("|---|---|---|---|")
    for (module, role) in sorted(roles.keys()):
        feats = roles[(module, role)]
        lines.append(f"| {module} | {role} | {', '.join(feats)} | backend/rbac/roles.py:1 |")
    lines.append("")

    lines.append("## Secret scanner summary")
    lines.append("")
    lines.append(f"Output of `scripts/audit_secrets.py`:")
    lines.append("")
    lines.append(f"<{secret_summary}>")
    lines.append("")

    lines.append("## RLS enforcement")
    lines.append("")
    if rls_locations:
        lines.append("| Where RLS is enforced | File:line |")
        lines.append("|---|---|")
        for loc in rls_locations:
            lines.append(f"| {loc['pattern']} | {loc['file']}:{loc['line']} |")
    else:
        lines.append("_(none found)_")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    middleware = extract_middleware_pipeline()
    endpoints = extract_endpoints()
    features = extract_features()
    roles = extract_rbac_roles()
    catalog = extract_catalog_info()
    secret_summary = run_secret_scanner()
    rls_locations = find_rls_enforcement()

    markdown = build_security_posture(
        middleware, endpoints, features, roles, catalog, secret_summary, rls_locations
    )

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
