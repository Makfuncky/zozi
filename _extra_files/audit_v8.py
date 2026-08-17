"""ZOZI Architecture Audit v8 — verifies ARCHITECTURE_MIGRATION_REPORT.md claims.

Pure-AST, never imports application code. Emits JSON + markdown summary.

Run:  python _extra_files/audit_v8.py
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

BACKEND = os.environ.get(
    "ZOZI_BACKEND_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"),
)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

LAYERS = ("routers", "controllers", "services", "models", "providers", "middleware")
ROUTE_DECORATORS = {"get", "post", "put", "patch", "delete", "route"}

# Provider-ish third-party SDKs that must NOT be imported by services/controllers
PROVIDER_SDKS = {
    "openai", "anthropic", "stripe", "paypalrestsdk", "paypalhttp", "twilio",
    "boto3", "botocore", "sendgrid", "smtplib", "httpx", "requests", "aiohttp",
    "ollama", "transformers", "torch", "sentence_transformers", "cv2",
    "rembg", "pytesseract", "easyocr", "PIL", "googlemaps", "geopy",
    "google", "jwt", "passlib", "pyotp", "qrcode", "faiss", "chromadb",
    "pinecone", "weaviate", "redis", "celery", "apscheduler", "paddleocr",
}

DB_WRITE_RE = re.compile(r"\b(?:db|session|_db|s)\.(?:commit|flush|add|add_all|delete|merge|refresh|execute)\s*\(")
DB_QUERY_RE = re.compile(r"\b(?:db|session|_db|s)\.(?:query|get|scalars|scalar)\s*\(")


def rel(p: str) -> str:
    return os.path.relpath(p, BACKEND).replace("/", "\\")


def iter_py(layer: str):
    root = os.path.join(BACKEND, layer)
    if not os.path.isdir(root):
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"__pycache__", "venv", ".pytest_cache"}]
        for fn in sorted(filenames):
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def load(path: str):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            src = fh.read()
    except Exception as exc:  # pragma: no cover
        return None, None, f"read-error: {exc}"
    try:
        return src, ast.parse(src), None
    except SyntaxError as exc:
        return src, None, f"syntax-error: line {exc.lineno}: {exc.msg}"


def imported_modules(tree: ast.AST):
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                mods.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                mods.add(node.module)
    return mods


def decorator_names(fn: ast.AST):
    out = []
    for dec in getattr(fn, "decorator_list", []) or []:
        node = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(node, ast.Name):
            out.append(node.id)
        elif isinstance(node, ast.Attribute):
            out.append(node.attr)
    return out


def body_hash(fn: ast.AST) -> str:
    try:
        dump = ast.dump(ast.Module(body=list(fn.body), type_ignores=[]), annotate_fields=False)
    except Exception:
        return ""
    return hashlib.sha256(dump.encode()).hexdigest()


def main() -> int:
    result = {
        "backend": BACKEND,
        "counts": {},
        "syntax_errors": [],
        "routers": {"total": 0, "with_business_logic": [], "import_models": [], "import_services": [],
                    "db_writes": [], "db_queries": [], "generated": []},
        "controllers": {"total": 0, "with_route_decorators": [], "without_route_decorators": [],
                        "reexport_shims": [],
                        "import_models": [], "import_fastapi": [], "db_writes": [], "db_queries": [],
                        "import_provider_sdk": [], "empty_or_stub": []},
        "services": {"total": 0, "import_provider_sdk": [], "import_fastapi": [], "import_routers": []},
        "models": {"total": 0, "tables": {}},
        "providers": {"total": 0},
        "duplicates": [],
        "decorated_routes": [],
        "route_collisions": [],
    }

    # ---------------- routers ----------------
    for path in iter_py("routers"):
        if os.path.basename(path) == "__init__.py":
            continue
        result["routers"]["total"] += 1
        r = rel(path)
        src, tree, err = load(path)
        if err:
            result["syntax_errors"].append({"file": r, "error": err})
            continue
        mods = imported_modules(tree)
        if "AUTO-GENERATED" in src:
            result["routers"]["generated"].append(r)
        if any(m == "models" or m.startswith("models.") or m.startswith("data.models") for m in mods):
            result["routers"]["import_models"].append(r)
        if any(m == "services" or m.startswith("services.") for m in mods):
            result["routers"]["import_services"].append(r)
        w = len(DB_WRITE_RE.findall(src))
        q = len(DB_QUERY_RE.findall(src))
        if w:
            result["routers"]["db_writes"].append({"file": r, "count": w})
        if q:
            result["routers"]["db_queries"].append({"file": r, "count": q})
        if w or q:
            result["routers"]["with_business_logic"].append({"file": r, "writes": w, "queries": q})

    # ---------------- controllers ----------------
    fn_index = defaultdict(list)  # (name, hash) -> [file]
    for path in iter_py("controllers"):
        if os.path.basename(path) == "__init__.py":
            continue
        result["controllers"]["total"] += 1
        r = rel(path)
        src, tree, err = load(path)
        if err:
            result["syntax_errors"].append({"file": r, "error": err})
            continue
        mods = imported_modules(tree)
        funcs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        decorated = []
        for fn in funcs:
            names = set(decorator_names(fn))
            if names & ROUTE_DECORATORS:
                decorated.append(fn.name)
        # A "re-export shim" is a module that defines no real functions/classes of
        # its own (only imports) — e.g. controllers/delegators/*.py forward names
        # from services. These are not route targets and are intentionally skipped.
        has_real_body = bool(funcs) or any(isinstance(n, ast.ClassDef) for n in tree.body)
        if decorated:
            result["controllers"]["with_route_decorators"].append({"file": r, "routes": len(decorated)})
        elif not has_real_body:
            result["controllers"]["reexport_shims"].append(r)
        else:
            result["controllers"]["without_route_decorators"].append(
                {"file": r, "public_funcs": len([f for f in funcs if not f.name.startswith("_")])}
            )
        if any(m == "models" or m.startswith("models.") or m.startswith("data.models") for m in mods):
            result["controllers"]["import_models"].append(r)
        if any(m == "fastapi" or m.startswith("fastapi.") for m in mods):
            result["controllers"]["import_fastapi"].append(r)
        sdk = sorted({m.split(".")[0] for m in mods if m.split(".")[0] in PROVIDER_SDKS})
        if sdk:
            result["controllers"]["import_provider_sdk"].append({"file": r, "sdk": sdk})
        w = len(DB_WRITE_RE.findall(src))
        q = len(DB_QUERY_RE.findall(src))
        if w:
            result["controllers"]["db_writes"].append({"file": r, "count": w})
        if q:
            result["controllers"]["db_queries"].append({"file": r, "count": q})
        if not funcs and not [n for n in tree.body if isinstance(n, ast.ClassDef)]:
            result["controllers"]["empty_or_stub"].append(r)
        for fn in funcs:
            h = body_hash(fn)
            if h and len(fn.body) > 2:
                fn_index[(fn.name, h)].append(r)

    # ---------------- services ----------------
    for path in iter_py("services"):
        if os.path.basename(path) == "__init__.py":
            continue
        result["services"]["total"] += 1
        r = rel(path)
        src, tree, err = load(path)
        if err:
            result["syntax_errors"].append({"file": r, "error": err})
            continue
        mods = imported_modules(tree)
        sdk = sorted({m.split(".")[0] for m in mods if m.split(".")[0] in PROVIDER_SDKS})
        if sdk:
            result["services"]["import_provider_sdk"].append({"file": r, "sdk": sdk})
        if any(m == "fastapi" or m.startswith("fastapi.") for m in mods):
            result["services"]["import_fastapi"].append(r)
        if any(m == "routers" or m.startswith("routers.") for m in mods):
            result["services"]["import_routers"].append(r)
        for fn in [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            h = body_hash(fn)
            if h and len(fn.body) > 2:
                fn_index[(fn.name, h)].append(r)

    # ---------------- models ----------------
    for path in iter_py("models"):
        if os.path.basename(path) == "__init__.py":
            continue
        result["models"]["total"] += 1
        r = rel(path)
        src, tree, err = load(path)
        if err:
            result["syntax_errors"].append({"file": r, "error": err})
            continue
        tables = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for stmt in node.body:
                    if isinstance(stmt, ast.Assign):
                        for t in stmt.targets:
                            if isinstance(t, ast.Name) and t.id == "__tablename__":
                                if isinstance(stmt.value, ast.Constant):
                                    tables.append(stmt.value.value)
        if tables:
            result["models"]["tables"][r] = sorted(tables)

    # ---------------- providers ----------------
    for path in iter_py("providers"):
        if os.path.basename(path) == "__init__.py":
            continue
        result["providers"]["total"] += 1
        r = rel(path)
        _src, tree, err = load(path)
        if err:
            result["syntax_errors"].append({"file": r, "error": err})

    # ---------------- middleware ----------------
    for path in iter_py("middleware"):
        _src, tree, err = load(path)
        if err:
            result["syntax_errors"].append({"file": rel(path), "error": err})

    # ---------------- duplicates ----------------
    for (name, _h), files in sorted(fn_index.items()):
        uniq = sorted(set(files))
        if len(uniq) > 1:
            result["duplicates"].append({"function": name, "files": uniq})

    # ---------------- decorated route inventory + collisions ----------------
    seen = defaultdict(list)
    for path in iter_py("controllers"):
        if os.path.basename(path) == "__init__.py":
            continue
        src, tree, err = load(path)
        if err:
            continue
        r = rel(path)
        for fn in [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            for dec in getattr(fn, "decorator_list", []) or []:
                if not isinstance(dec, ast.Call):
                    continue
                node = dec.func
                nm = node.id if isinstance(node, ast.Name) else getattr(node, "attr", None)
                if nm not in ROUTE_DECORATORS:
                    continue
                args = list(dec.args)
                if nm == "route":
                    method = args[0].value if args and isinstance(args[0], ast.Constant) else "?"
                    p = args[1].value if len(args) > 1 and isinstance(args[1], ast.Constant) else "?"
                else:
                    method = nm.upper()
                    p = args[0].value if args and isinstance(args[0], ast.Constant) else "?"
                skip = False
                for kw in dec.keywords or []:
                    if kw.arg == "skip" and isinstance(kw.value, ast.Constant):
                        skip = bool(kw.value.value)
                entry = {"file": r, "func": fn.name, "method": str(method).upper(), "path": p, "skip": skip}
                result["decorated_routes"].append(entry)
                if not skip:
                    seen[(str(method).upper(), p)].append(f"{r}::{fn.name}")
    for key, owners in sorted(seen.items()):
        if len(owners) > 1:
            result["route_collisions"].append({"method": key[0], "path": key[1], "owners": owners})

    result["counts"] = {
        "routers": result["routers"]["total"],
        "controllers": result["controllers"]["total"],
        "services": result["services"]["total"],
        "models": result["models"]["total"],
        "providers": result["providers"]["total"],
        "routers_with_business_logic": len(result["routers"]["with_business_logic"]),
        "routers_import_models": len(result["routers"]["import_models"]),
        "controllers_with_decorators": len(result["controllers"]["with_route_decorators"]),
        "controllers_without_decorators": len(result["controllers"]["without_route_decorators"]),
        "controllers_import_models": len(result["controllers"]["import_models"]),
        "controllers_db_ops": len(result["controllers"]["db_writes"]) + len(result["controllers"]["db_queries"]),
        "services_import_provider_sdk": len(result["services"]["import_provider_sdk"]),
        "duplicate_function_groups": len(result["duplicates"]),
        "decorated_routes": len(result["decorated_routes"]),
        "route_collisions": len(result["route_collisions"]),
        "syntax_errors": len(result["syntax_errors"]),
    }

    out = os.path.join(OUT_DIR, "audit_v8.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, default=str)

    print(json.dumps(result["counts"], indent=2))
    print("\nwrote", out)
    if result["syntax_errors"]:
        print("\nSYNTAX ERRORS:")
        for e in result["syntax_errors"][:40]:
            print("  ", e["file"], "->", e["error"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
