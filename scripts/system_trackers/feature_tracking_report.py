import os, ast, sys, json
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # zozi/
BACKEND = os.path.join(REPO, "backend")
FRONTEND = os.path.join(REPO, "frontend")

# ---------------------------------------------------------------------------
# Layer scanning (identity mapping: module == real directory name)
# ---------------------------------------------------------------------------
LAYERS = ["models", "db", "providers", "services", "controllers",
          "routers", "middleware", "utils", "dependencies", "events", "jobs"]

ROUTER_RULES = [
    ("admin_", "admin"), ("core_", "core"), ("store_", "commerce"),
    ("public_commerce_", "commerce"), ("public_comms_", "comms"),
    ("public_finance_", "finance"), ("public_geography_", "geography"),
    ("public_treasury_", "treasury"), ("public_suppliers_", "supplier"),
    ("public_country_", "geography"), ("public_identity_", "identity"),
    ("public_security_", "security"), ("public_effective_", "permissions"),
    ("public_permission", "permissions"), ("public_auth_", "identity"),
    ("public_", "identity"), ("supplier_", "supplier"), ("country_", "geography"),
    ("system_ai_", "ai"), ("ai_", "ai"), ("customer_", "customer"),
    ("finance_", "finance"), ("governance_", "governance"),
    ("logistics_", "logistics"), ("comms_", "comms"),
    ("internal_comms_", "comms"), ("hr_", "hr"), ("product_", "products"),
    ("security_", "security"), ("treasury_", "treasury"),
    ("ws_chat", "comms"), ("mobile_controller", "customer"),
    ("push_notifications", "comms"), ("csp_reporting", "security"),
    ("fraud_", "security"), ("cross_border", "commerce"),
    ("flash_sales", "promotions"), ("parcel_tracking", "logistics"),
    ("shift_handover", "hr"), ("expense_controller", "finance"),
    ("operational_controller", "governance"), ("batch_upload", "uploads"),
    ("upload_jobs", "uploads"), ("payout_approval", "treasury"),
    ("command_center", "admin"), ("frontend_errors", "platform"),
    ("email_controller", "comms"), ("product_moderation", "products"),
    ("product_verification", "products"), ("product_videos", "products"),
]

UTILS_RULES = [
    ("auth", "identity"), ("crypto", "security"), ("kms", "security"),
    ("vault", "security"), ("encryption", "security"), ("rls", "security"),
    ("csrf", "security"), ("country", "geography"), ("geo", "geography"),
    ("cache", "platform"), ("redis", "platform"),
]


def norm(p):
    return p.replace(os.sep, "/")


# Directories that are not feature modules (tooling / caches / VCS / venv).
EXCLUDE_DIRS = {
    "__pycache__", ".pytest_cache", ".hypothesis", ".kilo", ".git",
    "venv", "var", "tests", "alembic", "scripts",
    "_routers_clean", "_services_bak",
}
# Shared/platform layers that do NOT require a full vertical (model→service→
# controller→router) slice — they are infrastructure, not domain features.
PLATFORM_LAYERS = {
    "utils", "middleware", "events", "dependencies", "jobs", "db", "models",
    "providers", "migrations", "platform", "configuration", "provider_test",
    "root",
}


def scan_backend_py():
    """Single source of truth: every backend .py file as (rel, module_dotted, name).

    Walks the whole backend, excluding caches, venv, tests, alembic, scripts and
    temp/backup `_`-prefixed dirs, so the scan reflects the real, complete
    codebase. `collect()` and `build_module_index()` both consume this."""
    out = []
    if not os.path.isdir(BACKEND):
        return out
    for root, dirs, files in os.walk(BACKEND):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith("_")]
        for f in files:
            if not f.endswith(".py") or f == "__init__.py" or f.endswith(".bak"):
                continue
            full = os.path.join(root, f)
            rel = norm(os.path.relpath(full, BACKEND))
            out.append((rel, "backend." + rel[:-3].replace("/", "."), f))
    return sorted(out)


def module_for(layer, rel, name):
    parts = rel.split("/")
    in_subdir = len(parts) > 2
    if layer == "routers":
        n = name[:-3]
        for pref, feat in ROUTER_RULES:
            if n.startswith(pref):
                return feat
        return "platform"
    if layer == "utils":
        n = name[:-3]
        for pref, feat in UTILS_RULES:
            if n.startswith(pref) or n.endswith(pref):
                return feat
        return "utils"
    if layer == "middleware":
        return "middleware"
    if layer == "events":
        return "events"
    if layer == "dependencies":
        return "dependencies"
    if layer == "root":
        return "platform"
    if in_subdir:
        return parts[1]
    return layer


def collect():
    data = defaultdict(lambda: defaultdict(list))
    for rel, mod, name in scan_backend_py():
        layer = rel.split("/")[0] if "/" in rel else "root"
        feat = module_for(layer, rel, name)
        data[feat][layer].append((rel, mod, name))
    return data


def feature_alignment(feat, layers):
    """Return (signal, reason). signal in {GREEN, AMBER, RED, SHARED}.

    GREEN  = full vertical slice present (model/service/controller/router).
    AMBER  = logic present but not fully exposed, or a data/provider leaf whose
             completeness should be verified.
    RED    = an endpoint surface (router) exists but there is NO service or
             controller behind it — business logic is missing or bypassed.
    SHARED = platform/infra layer or provider-only leaf (no slice required).
    """
    if feat in PLATFORM_LAYERS or feat == "platform":
        return ("SHARED", "Shared platform/infrastructure layer — no full vertical slice required.")
    has_model = bool(layers.get("models") or layers.get("db"))
    has_provider = bool(layers.get("providers"))
    has_service = bool(layers.get("services"))
    has_controller = bool(layers.get("controllers"))
    has_router = bool(layers.get("routers"))
    if has_service and has_controller and has_router:
        return ("GREEN", "Full vertical slice present (model → service → controller → router).")
    if has_router and not has_service and not has_controller:
        return ("RED", "Endpoint surface (router) exists but NO service or controller — business logic "
                       "missing or bypassed.")
    if has_service:
        miss = []
        if not has_controller:
            miss.append("controller")
        if not has_router:
            miss.append("router")
        return ("AMBER", "Service present but not fully exposed: missing " + ", ".join(miss)
                + " (often dynamic importlib loading).")
    if has_controller or has_router:
        miss = [x for x in ("service", "controller", "router")
                if not (x == "service" and has_service) and not (x == "controller" and has_controller)
                and not (x == "router" and has_router)]
        return ("AMBER", "Exposed (router/controller) but missing " + ", ".join(miss) + ".")
    if has_provider:
        return ("SHARED", "Provider/integration implementation (leaf) — no service/controller required.")
    if has_model:
        return ("AMBER", "Data model present but NO service/controller/router — verify if business logic "
                         "is missing.")
    return ("SHARED", "No backend logic layers present (frontend-only or empty module).")


LAYER_LETTERS = [("models", "Mo"), ("db", "Db"), ("providers", "Pv"),
                 ("services", "Sv"), ("controllers", "Ct"), ("routers", "Rt"),
                 ("middleware", "Mw"), ("utils", "Ut"), ("events", "Ev"),
                 ("jobs", "Jb"), ("dependencies", "Dp")]


def layers_badge(layers):
    return "·".join(code for key, code in LAYER_LETTERS if layers.get(key)) or "—"


# ---------------------------------------------------------------------------
# Cross-reference engine  (feature -> feature, function -> function,
#                            operation -> operation)
# ---------------------------------------------------------------------------
def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


# First-segment names that denote an in-repo backend module (so we can turn a
# source-code import like `services.orders.orders_service` into the indexed
# `backend.services.orders.orders_service`).
INTERNAL_ROOTS = {
    "services", "controllers", "models", "providers", "routers", "utils",
    "db", "middleware", "dependencies", "events", "jobs", "scripts",
    "schemas", "core", "migrations", "tests",
}


def normalize_internal(mod_path):
    """Prefix an in-repo import target with `backend.` so it matches indexed
    module/function qualnames. External modules (fastapi, os, …) pass through."""
    if not mod_path:
        return mod_path
    first = mod_path.split(".", 1)[0]
    if first in INTERNAL_ROOTS and not mod_path.startswith("backend."):
        return "backend." + mod_path
    return mod_path


def feature_of_module(mod_dotted):
    """mod_dotted like 'backend.services.orders.orders_service' -> ('services','orders')."""
    parts = mod_dotted.split(".")
    if len(parts) < 3 or parts[0] != "backend":
        return ("platform", "platform")
    layer = parts[1]
    feat = module_for(layer, "/".join(parts[1:]) + ".py", parts[-1] + ".py")
    return (layer, feat)


def build_module_index():
    """module dotted path -> (file_rel, layer, feature). Uses the same complete
    backend scan as collect() so every file is indexed for cross-referencing."""
    idx = {}
    for rel, mod, name in scan_backend_py():
        layer = rel.split("/")[0] if "/" in rel else "root"
        _, feat = feature_of_module(mod)
        idx[mod] = (rel, layer, feat)
    return idx


def collect_calls(func_node):
    """Yield Call nodes that are directly descendants of func_node, not inside
    nested function/class definitions."""
    for child in ast.iter_child_nodes(func_node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(child, ast.Call):
            yield child
        else:
            yield from collect_calls(child)


def dotted_root(node):
    """Return (root_name, suffix_parts) for an attribute chain like a.b.c."""
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    else:
        return None
    parts.reverse()
    return parts[0], parts[1:]


def parse_py(path, mod_dotted):
    """Return dict with funcs(dict qualname->{kind,cls}), imports(dict
    alias->module_path), calls(list of (src_qualname, target_module_path_or_None,
    target_attr_or_None, raw))."""
    text = read_text(path)
    res = {"funcs": {}, "imports": {}, "calls": [], "routes": [], "syntax_error": False}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        res["syntax_error"] = True
        return res
    except Exception:
        return res

    # imports
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if base.startswith("."):
                # relative import -> resolve against file package
                pkg = ".".join(mod_dotted.split(".")[:-1])
                level = node.level
                segs = pkg.split(".")
                if level > 1:
                    segs = segs[:-(level - 1)]
                base = ".".join(segs + ([base[level:]] if base[level:] else []))
            for a in node.names:
                res["imports"][a.asname or a.name] = base  # alias -> module path
        elif isinstance(node, ast.Import):
            for a in node.names:
                res["imports"][a.asname or a.name.split(".")[-1]] = a.name

    # funcs / methods + their calls
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qn = mod_dotted + "." + node.name
            res["funcs"][qn] = {"kind": "function", "cls": None}
            for c in collect_calls(node):
                res["calls"].append(_classify_call(qn, c, res["imports"], None))
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qn = mod_dotted + "." + node.name + "." + sub.name
                    res["funcs"][qn] = {"kind": "method", "cls": node.name}
                    for c in collect_calls(sub):
                        res["calls"].append(_classify_call(qn, c, res["imports"], node.name))

    # routes (only in routers layer files)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for dec in node.decorator_list:
                m = _route_dec_method_path(dec)
                if m:
                    res["routes"].append((m[0], m[1], mod_dotted + "." + node.name))
    return res


def _route_dec_method_path(dec):
    if not isinstance(dec, ast.Call):
        return None
    f = dec.func
    method = None
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        if f.value.id in ("router", "app"):
            method = f.attr.upper()
    elif isinstance(f, ast.Attribute):  # router.something.get?
        method = f.attr.upper()
    if method not in ("GET", "POST", "PUT", "PATCH", "DELETE", "WEBSOCKET"):
        return None
    if not dec.args:
        return None
    p = dec.args[0]
    if isinstance(p, ast.Constant) and isinstance(p.value, str):
        return (method, _norm_path(p.value))
    return None


def _norm_path(p):
    return "/".join("{}" if "{" in s else s for s in p.split("/"))


def _classify_call(src_qn, call, imports, classname):
    """Return (src_qn, target_qualname, target_attr, raw_str).

    target_qualname is the resolved backend function/module (prefixed with
    `backend.`); target_attr is unused legacy (kept for call-site compat)."""
    f = call.func
    raw = ""
    try:
        raw = ast.unparse(call.func)
    except Exception:
        pass
    if isinstance(f, ast.Attribute):
        root = dotted_root(f)
        if root is None:
            return (src_qn, None, None, raw)
        root_name, rest = root
        if root_name in ("self", "cls"):
            # method call on self/cls -> same class
            if classname and rest:
                return (src_qn, ".".join(src_qn.split(".")[:-1]) + "." + classname + "." + rest[0], None, raw)
            return (src_qn, None, None, raw)
        if root_name in imports:
            mod = normalize_internal(imports[root_name])
            target = mod + ("." + ".".join(rest) if rest else "")
            return (src_qn, target, None, raw)
        # local var attribute call (self.repo.x) -> unresolved
        return (src_qn, None, None, raw)
    if isinstance(f, ast.Name):
        name = f.id
        if name in imports:
            mod = normalize_internal(imports[name])
            # `from X import foo` -> the imported symbol is X.foo
            return (src_qn, mod + "." + name, None, raw)
        # same-file call: resolve to current module + name
        src_mod = src_qn.rsplit(".", 1)[0]
        return (src_qn, src_mod + "." + name, None, raw)
    return (src_qn, None, None, raw)


def build_crossref():
    mod_index = build_module_index()
    files = {}          # mod -> parse result
    func_index = {}     # qualname -> (file_rel, layer, feature)
    for mod, (rel, layer, feat) in mod_index.items():
        path = os.path.join(BACKEND, rel)
        pr = parse_py(path, mod)
        files[mod] = pr
        for qn in pr["funcs"]:
            func_index[qn] = (rel, layer, feat)

    func_edges = []     # (src_qn, tgt_qn_or_module, src_feat, tgt_feat, src_layer, tgt_layer, kind)
    feat_deps = defaultdict(lambda: defaultdict(int))   # src_feat -> tgt_feat -> count
    import_deps = defaultdict(lambda: defaultdict(int))  # src_feat -> tgt_feat -> count
    unresolved = 0
    unresolved_by = defaultdict(int)  # category -> count (external_or_runtime / missing_internal)

    for mod, pr in files.items():
        (rel, layer, feat) = mod_index[mod]
        # import-based feature deps (coarse, always reliable)
        for alias, target_mod in pr["imports"].items():
            tmod = normalize_internal(target_mod)
            if tmod in mod_index:
                tlayer, tfeat = mod_index[tmod][1], mod_index[tmod][2]
                if tfeat != feat:
                    import_deps[feat][tfeat] += 1
        # call-based function edges
        for (src_qn, target, _attr, raw) in pr["calls"]:
            if not target:
                continue
            # exact function match
            if target in func_index:
                trel, tlayer, tfeat = func_index[target]
                func_edges.append((src_qn, target, feat, tfeat, layer, tlayer, "call"))
                if tfeat != feat:
                    feat_deps[feat][tfeat] += 1
                continue
            # module-level match (call to a function defined in target module but
            # maybe not indexed, e.g. nested) -> attribute call resolved to module
            tmod = target.rsplit(".", 1)[0] if "." in target else target
            if tmod in mod_index:
                trel, tlayer, tfeat = mod_index[tmod][0], mod_index[tmod][2], mod_index[tmod][2]
                func_edges.append((src_qn, target, feat, tfeat, layer, tlayer, "call"))
                if tfeat != feat:
                    feat_deps[feat][tfeat] += 1
            else:
                unresolved += 1
                tn = normalize_internal(target)
                if tn.startswith("backend."):
                    unresolved_by["missing_internal"] += 1
                else:
                    unresolved_by["external_or_runtime"] += 1

    return {
        "mod_index": mod_index,
        "func_index": func_index,
        "files": files,
        "func_edges": func_edges,
        "feat_deps": feat_deps,
        "import_deps": import_deps,
        "unresolved": unresolved,
        "unresolved_by": dict(unresolved_by),
    }


# ---------------------------------------------------------------------------
# Operation -> operation wiring (router operations -> handler -> backend fns)
# ---------------------------------------------------------------------------
def build_operation_wiring(cross):
    mod_index = cross["mod_index"]
    files = cross["files"]
    ops = []
    for mod, pr in files.items():
        (rel, layer, feat) = mod_index[mod]
        if layer != "routers":
            continue
        for (method, path, handler_qn) in pr["routes"]:
            called = []
            if handler_qn in cross["func_index"]:
                # find calls made by this handler
                for (src_qn, tgt, sfeat, tfeat, slayer, tlayer, kind) in cross["func_edges"]:
                    if src_qn == handler_qn:
                        called.append(tgt if tgt else src_qn)
            # also detect dynamic imports of controllers/services inside handler body.
            # parse_py stores raw import paths (e.g. "controllers.x"), so normalize first.
            nv = {normalize_internal(v) for v in pr["imports"].values()}
            dyn = sorted(d for d in nv
                         if d.startswith("backend.controllers") or d.startswith("backend.services"))
            ops.append({
                "method": method, "path": path, "router_feat": feat,
                "handler": handler_qn, "called": called, "dyn_imports": dyn,
                "wired": bool(called or dyn),
            })
    return ops


# ---------------------------------------------------------------------------
# Frontend scan  (feature->feature via cross-feature imports; op linkage)
# ---------------------------------------------------------------------------
FRONTEND_TOKENS = {
    "admin": ["admin", "command-center", "commission", "audit-fixes", "moderation"],
    "analytics": ["analytics", "dashboard", "report"],
    "audit": ["audit", "ediscovery", "worm"],
    "catalog": ["catalog", "category"],
    "commerce": ["cart", "checkout", "coupon", "flash-sale", "promotion", "package", "store"],
    "comms": ["chat", "email", "campaign", "inbox", "video", "notification", "communication", "messag"],
    "core": ["core", "hr", "employee", "hierarchy", "shift"],
    "customer": ["customer", "account", "profile", "orders", "tracking"],
    "hr": ["hr", "employee", "hierarchy", "shift", "onboarding"],
    "finance": ["finance", "commission", "ledger", "invoice"],
    "gateway": ["gateway", "integration", "webhook"],
    "geography": ["country", "geograph", "region", "tax"],
    "governance": ["governance", "policy", "operational"],
    "identity": ["auth", "login", "signin", "session", "oauth", "register"],
    "logistics": ["logistic", "parcel", "shipping", "delivery", "tracking"],
    "media": ["media", "upload", "image", "voice", "asset"],
    "orders": ["order", "returns"],
    "permissions": ["permission", "role", "access", "rbac"],
    "products": ["product", "supplier-storefront", "storefront"],
    "security": ["security", "fraud", "csp", "encrypt"],
    "supplier": ["supplier", "suppliers"],
    "treasury": ["treasury", "payout"],
    "uploads": ["upload", "batch-upload"],
    "promotions": ["promotion", "flash-sale", "promo"],
    "system": ["system", "settings", "config"],
    "users": ["user", "profile", "account"],
    "common": ["common", "shared", "utils", "lib"],
    "ai": ["ai", "assistant", "search", "ocr"],
    "delegators": ["delegator"],
}
EXCLUDE = {"node_modules", ".next", ".expo", "build", "android", "ios",
           "web-dist", "playwright-report", "playwright-out", "test-output",
           "test-results", "coverage", ".git", "__pycache__", ".expo"}


def walk_fe(root):
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE]
        for f in files:
            if f.endswith((".ts", ".tsx", ".js", ".jsx", ".vue")):
                out.append(norm(os.path.relpath(os.path.join(dirpath, f), REPO)))
    return out


def classify_fe(path):
    low = path.lower()
    for feat, toks in FRONTEND_TOKENS.items():
        for t in toks:
            if ("/" + t + "/") in low or low.endswith("/" + t) or ("-" + t + "-") in low or low.startswith(t + "/"):
                return feat
    return "platform"


def fe_imports_and_api(path):
    text = read_text(os.path.join(REPO, path))
    imps = []
    apis = []
    for m in re_imp.finditer(text):
        if m.group(1):
            imps.append(m.group(1).strip())
        elif m.group(2):
            for part in m.group(2).split(","):
                part = part.strip()
                if part:
                    imps.append(part)
    for m in re_api.finditer(text):
        apis.append(m.group(1))
    return imps, apis


import re
# `from "x" import` / `from x import` -> group(1); `import a, b, c` -> group(2) (comma list).
re_imp = re.compile(r"""from\s+['"]?([^'";]+?)['"]?\s+import|import\s+([^;]+?)(?=\s+from|$)""")
re_api = re.compile(r"""(?:fetch|apiFetch|axios\.(?:get|post|put|patch|delete)|useSWR|useQuery|ky\()\s*\(\s*[`'"]([^`'"]+)[`'"]""")


def build_frontend_xref():
    roots = {
        "web_app": os.path.join(FRONTEND, "web_app"),
        "mobile_app": os.path.join(FRONTEND, "mobile_app"),
        "shared": os.path.join(FRONTEND, "shared"),
    }
    feats = defaultdict(lambda: {"files": [], "import_deps": defaultdict(int),
                                 "api_calls": []})
    api_to_feat = defaultdict(set)
    for rname, rdir in roots.items():
        for p in walk_fe(rdir):
            f = classify_fe(p)
            feats[f]["files"].append(p)
            imps, apis = fe_imports_and_api(p)
            for spec in imps:
                # local cross-feature import: relative path that crosses feature dir
                if spec.startswith(".") or spec.startswith("/"):
                    low = spec.lower()
                    tgt = classify_fe(low)
                    if tgt != f and tgt not in ("platform",):
                        feats[f]["import_deps"][tgt] += 1
                elif spec.startswith("backend"):
                    # frontend -> backend import (rare)
                    feats[f]["import_deps"]["backend"] += 1
            for a in apis:
                if a.startswith("/"):
                    feats[f]["api_calls"].append(_norm_path(a.split("?")[0]))
                    api_to_feat[_norm_path(a.split("?")[0])].add(f)
    return feats, api_to_feat


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
SURFACE = {
    "admin": "Admin Web", "analytics": "Admin Web", "audit": "Admin Web",
    "catalog": "Admin + Store", "commerce": "Customer Web + Store", "comms": "Cross-channel",
    "communication": "Cross-channel", "core": "Internal Platform", "customer": "Customer Web + Mobile",
    "hr": "Internal Platform", "employee": "Internal Platform", "hierarchy": "Internal Platform",
    "finance": "Admin + Supplier", "gateway": "System/Integration", "gateways": "System/Integration",
    "geography": "Cross-cutting", "country": "Cross-cutting", "location_service": "Cross-cutting",
    "governance": "Admin Web", "identity": "Cross-cutting", "auth": "Cross-cutting",
    "logistics": "Supplier + Admin", "media": "Cross-cutting", "image": "Cross-cutting",
    "voice": "Cross-cutting", "orders": "Cross-cutting", "permissions": "Cross-cutting",
    "products": "Store + Supplier", "security": "Cross-cutting", "supplier": "Supplier Portal",
    "suppliers": "Supplier Portal", "treasury": "Admin + Supplier", "uploads": "Cross-cutting",
    "promotions": "Store", "system": "Internal", "users": "Cross-cutting", "common": "Shared",
    "mcp": "Internal", "legacy": "Cross-cutting", "automation": "Internal", "payments": "Cross-cutting",
    "ai": "Internal", "delegators": "Generated", "generated": "Generated", "migrations": "Database",
    "middleware": "Platform", "events": "Platform", "utils": "Platform", "dependencies": "Platform",
    "db": "Platform", "models": "Platform", "providers": "Platform", "services": "Platform",
    "jobs": "Platform/Async", "platform": "Platform", "configuration": "Cross-cutting",
    "provider_test": "Shared",
}
DOMAIN = {
    "admin": "Administration", "analytics": "Analytics", "audit": "Compliance & Audit",
    "catalog": "Catalog", "commerce": "Commerce", "comms": "Communications",
    "communication": "Communications", "core": "People / HR Platform", "customer": "Commerce",
    "hr": "HR / People", "employee": "HR / People", "hierarchy": "HR / People",
    "finance": "Finance", "gateway": "Integrations", "gateways": "Integrations",
    "geography": "Geography", "country": "Geography", "location_service": "Geography",
    "governance": "Governance", "identity": "Identity & Auth", "auth": "Identity & Auth",
    "logistics": "Logistics", "media": "Media", "image": "Media", "voice": "Communications",
    "orders": "Orders", "permissions": "Access Control", "products": "Products",
    "security": "Security", "supplier": "Suppliers", "suppliers": "Suppliers",
    "treasury": "Treasury", "uploads": "Media / Uploads", "promotions": "Promotions",
    "system": "System", "users": "Identity", "common": "Shared", "mcp": "AI / ML",
    "legacy": "Legacy", "automation": "Automation", "payments": "Payments", "ai": "AI / ML",
    "delegators": "Generated Delegation", "generated": "Generated Routers",
    "migrations": "Database", "middleware": "Platform", "events": "Platform", "utils": "Platform",
    "dependencies": "Platform", "jobs": "Async Jobs", "platform": "Platform",
    "configuration": "Configuration", "provider_test": "Shared", "db": "Database",
    "models": "Database Models", "providers": "Providers", "services": "Services",
}
DESC = {
    "admin": "Admin console, bulk ops, moderation, payouts, command center",
    "analytics": "Reporting, dashboards, admin analytics",
    "audit": "Immutable audit trail, e-discovery, WORM compliance",
    "catalog": "Category / catalog taxonomy and administration",
    "commerce": "Storefront commerce: cart, coupons, flash sales, packages",
    "comms": "Chat, email, campaigns, unified inbox, video, notifications",
    "communication": "Internal communication services (separate dir from comms)",
    "core": "Core people/HR platform, users, base schema",
    "customer": "Customer web + mobile self-service flows",
    "hr": "HR / employee / hierarchy / shift handover",
    "employee": "Employee module (services dir, related to hr)",
    "hierarchy": "Org hierarchy module (services dir, related to hr)",
    "finance": "Finance, commissions, contractor milestones, ledgers",
    "gateway": "External integrations / payment gateways (models)",
    "gateways": "External integrations / payment gateways (services)",
    "geography": "Countries, regions, tax/legal/economic country data",
    "country": "Country services (services dir, related to geography)",
    "location_service": "Location service (services dir, related to geography)",
    "governance": "Operational governance and policy enforcement",
    "identity": "Auth, identity, sessions, public auth surfaces",
    "auth": "Auth providers (providers dir, related to identity)",
    "logistics": "Logistics, parcel tracking, supplier logistics",
    "media": "Media storage, uploads, image/voice processing",
    "image": "Image processing providers (providers dir, related to media)",
    "voice": "Voice / telephony providers (providers dir, related to comms)",
    "orders": "Order lifecycle and order entities",
    "permissions": "Access control, permission entities and checks",
    "products": "Product catalog, moderation, verification, videos",
    "security": "Security: fraud, CSP, RLS, encryption",
    "supplier": "Supplier portal, supplier storefronts",
    "suppliers": "Suppliers services (services dir, related to supplier)",
    "treasury": "Treasury, payout approvals, supplier finance",
    "uploads": "Batch uploads and upload jobs",
    "promotions": "Promotions, flash sales, promo points",
    "system": "Internal system tooling and scripts",
    "users": "User accounts and profile management",
    "common": "Shared cross-cutting services and helpers",
    "mcp": "Model-context-protocol / AI tool surface",
    "legacy": "Legacy compatibility shims (providers)",
    "automation": "Internal automation providers (schedulers)",
    "payments": "Payments processing providers",
    "ai": "AI assistance, search, OCR, automation research",
    "delegators": "Auto-generated delegation controllers/routers",
    "generated": "Generated routers (routers/generated)",
    "migrations": "Database migration scripts (Alembic)",
    "middleware": "Platform HTTP middleware",
    "events": "Platform event bus / handlers",
    "utils": "Platform utilities",
    "dependencies": "Platform DI dependencies",
    "jobs": "Async / background jobs",
    "platform": "Platform-level shared concerns",
    "configuration": "Configuration models/controllers",
    "provider_test": "Provider test helpers (shared)",
    "db": "Database core: engine, session, base, init/schema bootstrap",
    "models": "Top-level ORM models at models/ root",
    "providers": "Top-level providers at providers/ root",
    "services": "Top-level services at services/ root (registry etc.)",
}
ORDER = ["admin", "analytics", "audit", "catalog", "commerce", "comms", "communication",
         "core", "customer", "hr", "employee", "hierarchy", "finance", "gateway", "gateways",
         "geography", "country", "location_service", "governance", "identity", "auth",
         "logistics", "media", "image", "voice", "orders", "permissions", "products",
         "security", "supplier", "suppliers", "treasury", "uploads", "promotions", "system",
         "users", "common", "mcp", "legacy", "automation", "payments", "ai", "delegators",
         "generated", "migrations", "middleware", "events", "utils", "dependencies", "jobs",
         "configuration", "provider_test", "platform"]


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def cell(files):
    if not files:
        return "—"
    names = sorted({(x if isinstance(x, str) else x[2]) for x in files})
    return " · ".join(names)


def main(out_dir=None, report_name="SYSTEM_TRACKING_REPORT.md",
          json_name="FEATURE_CROSS_REFERENCES.json"):
    out_dir = out_dir or BACKEND
    data = collect()
    cross = build_crossref()
    ops = build_operation_wiring(cross)
    fe, api_to_feat = build_frontend_xref()

    # backend route index (normalized path -> set of router features)
    route_index = defaultdict(set)
    for op in ops:
        route_index[op["path"]].add(op["router_feat"])

    web_files = walk_fe(os.path.join(FRONTEND, "web_app"))
    mob_files = walk_fe(os.path.join(FRONTEND, "mobile_app"))
    shared_files = walk_fe(os.path.join(FRONTEND, "shared"))

    fe_buckets = defaultdict(lambda: {"web": [], "mob": [], "shared": [], "webt": [], "mobt": [], "bt": []})
    for p in web_files:
        bn = os.path.basename(p)
        f = classify_fe(p)
        if "__tests__" in p or "__mocks__" in p or ".test." in p or ".spec." in p:
            fe_buckets[f]["webt"].append(bn)
        else:
            fe_buckets[f]["web"].append(bn)
    for p in mob_files:
        bn = os.path.basename(p)
        f = classify_fe(p)
        if "__tests__" in p or "e2e" in p or ".test." in p or ".spec." in p:
            fe_buckets[f]["mobt"].append(bn)
        else:
            fe_buckets[f]["mob"].append(bn)
    for p in shared_files:
        fe_buckets[classify_fe(p)]["shared"].append(os.path.basename(p))

    test_dir = os.path.join(BACKEND, "tests")
    for dirpath, dirs, files in os.walk(test_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                low = norm(os.path.join(dirpath, f)).lower()
                hit = "platform"
                for feat, toks in FRONTEND_TOKENS.items():
                    if any(t in low for t in toks):
                        hit = feat
                        break
                fe_buckets[hit]["bt"].append(f)

    present = set(data.keys()) | set(fe_buckets.keys())
    ordered = [m for m in ORDER if m in present] + sorted(present - set(ORDER))

    COLS = ["Sno", "Surface", "Domain", "Module", "Health", "Description of Module",
            "backend:utils", "backend:jobs", "backend:events", "backend:dependencies",
            "backend:models", "backend:db", "backend:providers", "backend:services",
            "backend:controllers", "backend:routers", "backend:middlewares",
            "backend:tests", "backend:connection report", "Layers",
            "frontend:web_app", "frontend:mobile_app", "frontend:Shared / Utils",
            "frontend: Web Tests", "frontend: Mobile Tests", "Depends on (features)",
            "Cross-func edges", "Ops wired", "Completion %", "Remaining todo", "Comments"]

    def L(feat, layer):
        return data.get(feat, {}).get(layer, [])

    align = {}
    rows = []
    for i, feat in enumerate(ordered, 1):
        layers = {l: L(feat, l) for l in LAYERS}
        signal, reason = feature_alignment(feat, layers)
        align[feat] = (signal, reason)
        deps = sorted(cross["feat_deps"].get(feat, {}).items(), key=lambda x: -x[1])
        dep_str = ", ".join(f"{d}({n})" for d, n in deps) if deps else "—"
        n_cross = sum(1 for (_, _, sf, tf, _, _, _) in cross["func_edges"] if sf == feat and tf != feat)
        n_ops = sum(1 for op in ops if op["router_feat"] == feat)
        n_ops_wired = sum(1 for op in ops if op["router_feat"] == feat and op["wired"])

        w, m, sh = fe_buckets[feat]["web"], fe_buckets[feat]["mob"], fe_buckets[feat]["shared"]
        wt, mt, bt = fe_buckets[feat]["webt"], fe_buckets[feat]["mobt"], fe_buckets[feat]["bt"]

        # Completion % is a REVIEW-ONLY heuristic (NOT a certified metric).
        # Weights: model 8 · service 15 · controller 22 · router 22 · web 10 · mobile 10
        #          · tests 5 · shared 3.
        score = 0
        if layers["models"]: score += 8
        if layers["services"]: score += 15
        if layers["controllers"]: score += 22
        if layers["routers"]: score += 22
        if w: score += 10
        if m: score += 10
        if bt or wt or mt: score += 5
        if sh: score += 3
        score = min(100, score)

        comments = []
        if feat == "permissions":
            comments.append("MODEL present, NO service layer (genuine gap).")
        if feat == "delegators":
            comments.append("Controllers loaded dynamically (importlib) - invisible to static scan.")
        if not layers["controllers"] and layers["services"]:
            comments.append("Services present but no controller here (cross-feature/dynamic exposure likely).")
        if not layers["routers"] and layers["controllers"]:
            comments.append("Controllers present but no static router import (dynamic loading).")
        if deps:
            comments.append("Depends on: " + ", ".join(d for d, _ in deps) + ".")
        if not comments:
            comments.append("Utility / cross-cutting layer.")
        todo = ""
        if "NO service" in " ".join(comments):
            todo = "Add permissions service layer or confirm logic lives elsewhere."
        elif not layers["routers"] and layers["controllers"]:
            todo = "Confirm router wiring (dynamic loader) for these controllers."

        rows.append([
            i, SURFACE.get(feat, "—"), DOMAIN.get(feat, "—"), feat, signal, DESC.get(feat, feat),
            cell(layers["utils"]), cell(layers["jobs"]), cell(layers["events"]),
            cell(layers["dependencies"]), cell(layers["models"]), cell(layers["db"]),
            cell(layers["providers"]), cell(layers["services"]), cell(layers["controllers"]),
            cell(layers["routers"]), cell(layers["middleware"]), cell(bt),
            f"R={len(layers['routers'])} · C={len(layers['controllers'])} · S={len(layers['services'])} · M={len(layers['models'])}",
            layers_badge(layers),
            cell(w), cell(m), cell(sh), cell(wt), cell(mt), dep_str, n_cross,
            f"{n_ops_wired}/{n_ops}", f"{score}%", todo, " ".join(comments),
        ])

    head = "| " + " | ".join(COLS) + " |"
    sep = "| " + " | ".join(["---"] * len(COLS)) + " |"
    body = "\n".join("| " + " | ".join(str(c) for c in r) + " |" for r in rows)

    totals = {l: sum(len(data.get(f, {}).get(l, [])) for f in data) for l in LAYERS}
    total_fe = (sum(len(fe_buckets[f]["web"]) for f in fe_buckets)
                + sum(len(fe_buckets[f]["mob"]) for f in fe_buckets)
                + sum(len(fe_buckets[f]["shared"]) for f in fe_buckets))

    # ----- Feature -> Feature dependency map -----
    # Blends two relationship types (kept separate so readers don't conflate them):
    #   * calls = backend: A's code statically calls B's code (AST, fine-grained, reliable)
    #   * feimp = frontend: A's module imports B (path-token classified, approximate)
    all_feats = sorted(present)
    feat_dep_rows = []
    for sf in all_feats:
        calls = cross["feat_deps"].get(sf, {})
        feimp = fe.get(sf, {}).get("import_deps", {})
        merged = defaultdict(int)
        for d, n in calls.items():
            merged[d] += n
        for d, n in feimp.items():
            merged[d] += n
        if sf in merged:
            del merged[sf]
        if merged:
            row = [(d, n, calls.get(d, 0), feimp.get(d, 0))
                   for d, n in sorted(merged.items(), key=lambda x: -x[1])]
            feat_dep_rows.append((sf, row))

    # ----- Function -> Function (cross-feature edges sample) -----
    cross_func_edges = [(s, t, sf, tf, sl, tl) for (s, t, sf, tf, sl, tl, k)
                        in cross["func_edges"] if sf != tf]
    # top edges by source module pair
    pair_counts = defaultdict(int)
    for s, t, sf, tf, sl, tl in cross_func_edges:
        pair_counts[(sf, tf, sl, tl)] += 1
    top_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])[:60]

    # ----- Operation -> Operation wiring -----
    wired_ops = [op for op in ops if op["wired"]]
    unwired_ops = [op for op in ops if not op["wired"]]
    # cross-stack: frontend api calls matched to backend routes
    cross_stack = []
    for path, feats_set in api_to_feat.items():
        if path in route_index:
            cross_stack.append((path, sorted(route_index[path]), sorted(feats_set)))
    cross_stack.sort()

    # ----- machine-readable JSON -----
    json_out = {
        "feature_deps": {sf: dict(deps) for sf, deps in
                         ((f, cross["feat_deps"].get(f, {})) for f in all_feats)},
        "frontend_feature_deps": {f: dict(fe[f]["import_deps"]) for f in fe},
        "func_edges_cross_feature": [
            {"src": s, "tgt": t, "src_feat": sf, "tgt_feat": tf,
             "src_layer": sl, "tgt_layer": tl}
            for (s, t, sf, tf, sl, tl) in cross_func_edges
        ],
        "operations": [
            {"method": op["method"], "path": op["path"], "router_feat": op["router_feat"],
             "handler": op["handler"], "called": op["called"], "dyn_imports": op["dyn_imports"],
             "wired": op["wired"]}
            for op in ops
        ],
        "frontend_api_to_backend_route": [
            {"path": p, "backend_feats": bf, "frontend_feats": ff} for p, bf, ff in cross_stack
        ],
        "stats": {
            "modules": len(cross["mod_index"]),
            "func_edges_total": len(cross["func_edges"]),
            "func_edges_cross_feature": len(cross_func_edges),
            "unresolved_call_targets": cross["unresolved"],
            "unresolved_by": cross["unresolved_by"],
            "operations_total": len(ops),
            "operations_wired": len(wired_ops),
            "operations_unwired": len(unwired_ops),
        },
    }
    json_path = os.path.join(out_dir, json_name)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, indent=2)

    # ----- assemble report -----
    out = []
    out.append("# ZOZI System — Comprehensive Tracking Report (with Cross-References)")
    out.append("")
    out.append(f"> **{len(rows)} modules** enumerated (real backend directories + classified "
               f"routers/utils + frontend path tokens). Backend `connection report` = module counts "
               f"(Routers/Controllers/Services/Models per module).")
    out.append("")
    out.append("> **This version adds three relationship dimensions the previous build lacked:**")
    out.append("> - **Feature → Feature** — derived from real function-call edges and import edges "
               "across module boundaries (see *Feature → Feature Dependency Map*).")
    out.append("> - **Function → Function** — AST call graph: every `module.fn()` / imported call "
               f"resolved to its target function. {len(cross_func_edges)} cross-feature edges captured "
               f"(see *Function → Function Call Graph*; full graph in FEATURE_CROSS_REFERENCES.json).")
    out.append("> - **Operation → Operation** — every FastAPI route (`@router.METHOD(path)`) traced to "
               f"its handler and the backend functions it invokes ({len(wired_ops)}/{len(ops)} router "
               "operations wired; see *Operation → Operation Wiring*).")
    out.append("")
    out.append("> **Completion %** is a heuristic weight for review only, not a certified metric.")
    out.append("")
    out.append("**Backend totals:** " + " · ".join(f"{l}={totals[l]}" for l in LAYERS)
               + f" · modules={len(data)}")
    out.append("")
    out.append(f"**Frontend totals:** web_app={sum(len(fe_buckets[f]['web']) for f in fe_buckets)} · "
                f"mobile_app={sum(len(fe_buckets[f]['mob']) for f in fe_buckets)} · "
                f"shared={sum(len(fe_buckets[f]['shared']) for f in fe_buckets)} · "
                f"web_tests={sum(len(fe_buckets[f]['webt']) for f in fe_buckets)} · "
                f"mob_tests={sum(len(fe_buckets[f]['mobt']) for f in fe_buckets)} · "
                f"backend_tests={sum(len(fe_buckets[f]['bt']) for f in fe_buckets)}")
    out.append("")

    # ---- gap register + executive summary (computed here, reused below) ----
    cross_func_edges = [(s, t, sf, tf, sl, tl) for (s, t, sf, tf, sl, tl, k)
                        in cross["func_edges"] if sf != tf]
    wired_ops = [op for op in ops if op["wired"]]
    unwired_ops = [op for op in ops if not op["wired"]]

    gaps = []  # (severity, area, finding, recommended_action)
    if not data.get("permissions", {}).get("services", []):
        gaps.append(("HIGH", "permissions",
                     "Permission **model** exists but there is **no service layer, controller, or "
                     "router** — access-control logic has no clear backend entry point.",
                     "Confirm checks live in middleware/security; otherwise add a permissions "
                     "service + router."))
    dyn_controllers = sorted(f for f, layers in data.items()
                             if layers.get("controllers") and not layers.get("routers")
                             and f not in ("delegators",))
    if dyn_controllers:
        gaps.append(("MED", "controllers",
                     "Controllers exist but have no static router import for: "
                     f"{', '.join(dyn_controllers)}. They are exposed via dynamic `importlib` loading "
                     "(main._load_routers) — invisible to a static scan.",
                     "Confirm router wiring through the dynamic loader; add a route registry for visibility."))
    gaps.append(("MED", "database",
                 "Local backend/zozi.db is **EMPTY (0 tables)** and Alembic has a **2-head branch** "
                 "(20260727_0908, 20260729_1914). The schema-audit (934 issues, ~909 index items) was "
                 "run on a **different populated DB**, so those numbers are unverified here.",
                 "Confirm the target DB, merge the two Alembic heads, then re-run the audit against the "
                 "real database before fixing any drift."))
    gaps.append(("LOW", "operations",
                 f"{len(unwired_ops)}/{len(ops)} router operations are **unwired** (stub health/status "
                 "routes with no backend call).",
                 "Expected for health checks; verify none are real endpoints masked as stubs."))
    ub = cross.get("unresolved_by", {})
    gaps.append(("INFO", "function graph",
                  f"{cross['unresolved']} call targets are unresolved: "
                  f"{ub.get('external_or_runtime', 0)} external/runtime (third-party libs, self.repo.* DI) and "
                  f"{ub.get('missing_internal', 0)} internal-but-not-found (dynamic/delegator/Generated code). "
                  "Expected for a DI-style codebase — not a defect.",
                  "Resolve by tracing repository/provider wiring, or include Generated/Delegator dirs, if "
                  "deeper precision is needed."))

    out.append("## How to read this report")
    out.append("")
    out.append("**Health legend:** `GREEN` = full vertical slice (model→service→controller→router) present · "
                "`AMBER` = logic present but not fully exposed (usually dynamic `importlib` loading) · "
                "`RED` = data model only / no business-logic wiring · `SHARED` = platform/infra layer.")
    out.append("")
    out.append("1. **System Alignment Dashboard** — every feature with its red/green health and counts.")
    out.append("2. **Master Tracking Table** — every feature with its `Health` and `Layers` (which of "
                "models/providers/services/controllers/routers/middleware exist), plus completion % and TODO.")
    out.append("3. **Feature → Feature Alignment Map** — *who calls whom* across features, with each link's "
                "health (red/green) and `BROKEN` flagged when a feature depends on an unwired (RED) feature.")
    out.append("4. **Function → Function Call Graph** — the resolved static call graph (top lanes; the full "
                "edge list lives in `FEATURE_CROSS_REFERENCES.json`).")
    out.append("5. **Operation → Operation Wiring** — every API route traced to the handler and backend "
                "functions it runs.")
    out.append("6. **Wiring Problems (what to fix)** — concrete layer-to-layer gaps (controllers without "
                "routers, services without controllers, RED features, broken dependencies).")
    out.append("7. **Gap register** — platform-level gaps with a recommended action per item.")
    out.append("")
    out.append("> **Built vs missing at a glance:** the codebase is *wide* ({len(rows)} modules, "
               f"{sum(totals.values())} backend files) but the static wiring only proves "
               f"{len(wired_ops)}/{len(ops)} routes and {len(cross_func_edges)} cross-feature calls. The "
               "rest is either dynamic (runtime `importlib`), third-party, or genuinely absent — the gap "
               "register lists the genuinely absent/risky items.")
    out.append("")
    out.append("## Executive summary — what's built and what's missing")
    out.append("")
    out.append(f"- **{len(rows)} modules** enumerated; **{sum(totals.values())} backend files** and "
               f"**{total_fe} frontend files** scanned.")
    ub = cross.get("unresolved_by", {})
    out.append(f"- **Function graph:** {len(cross['func_edges'])} total edges, "
               f"**{len(cross_func_edges)} cross-feature** resolved, **{cross['unresolved']}** unresolved "
               f"({ub.get('external_or_runtime', 0)} external/runtime, "
               f"{ub.get('missing_internal', 0)} internal-but-not-found — expected).")
    out.append(f"- **Operations:** {len(ops)} API routes — **{len(wired_ops)} wired**, "
               f"**{len(unwired_ops)} unwired** (stubs).")
    out.append(f"- **Tracked gaps:** {len(gaps)} items in the Gap register below "
               "(incl. permissions having a model but no service, and the empty local DB + Alembic branch).")
    out.append("")

    # ---- System Alignment Dashboard ----
    sig_counts = defaultdict(int)
    for f, (s, r) in align.items():
        sig_counts[s] += 1
    broken = []
    for sf in align:
        for d in cross["feat_deps"].get(sf, {}):
            if d in align and align[d][0] == "RED":
                broken.append((sf, d))
    out.append("## System Alignment Dashboard")
    out.append("")
    out.append(f"**{len(align)} features** — "
                f"**{sig_counts['GREEN']} GREEN** (fully wired), "
                f"**{sig_counts['AMBER']} AMBER** (logic present, not fully exposed), "
                f"**{sig_counts['RED']} RED** (model only / unwired), "
                f"**{sig_counts['SHARED']} SHARED** (platform/infra).")
    out.append(f"**Broken dependencies:** {len(broken)} (a feature depends on a RED/unwired feature).")
    out.append("")
    out.append("| Health | Feature | Why |")
    out.append("| --- | --- | --- |")
    for signal in ["GREEN", "AMBER", "RED", "SHARED"]:
        for f, (s, r) in sorted(align.items()):
            if s == signal:
                out.append(f"| {s} | {f} | {r} |")
    out.append("")

    # Master table
    out.append("## Master Tracking Table")
    out.append("")
    out.append(head)
    out.append(sep)
    out.append(body)
    out.append("")

    # Feature -> Feature (annotated alignment map with per-link health + edge type)
    out.append("## Feature → Feature Alignment Map")
    out.append("")
    out.append("Each edge `A --> B (n)` means feature **A** depends on feature **B**. The weight `n` is the "
               "sum of two relationship types, shown separately in the table below: `call` = backend A's code "
               "statically calls B's code (AST, fine-grained, reliable); `fe-import` = frontend A's module "
               "imports B (path-token classified, approximate). Node colour = B's health "
               "(green/amber/red/shared). A link is **BROKEN** when A depends on a RED (unwired) feature.")
    out.append("")
    mermaid = ["```mermaid", "graph LR"]
    mermaid.append("classDef green fill:#1f7a3d,stroke:#0c3,color:#fff;")
    mermaid.append("classDef amber fill:#9a6b00,stroke:#a80,color:#fff;")
    mermaid.append("classDef red fill:#9a1f1f,stroke:#a33,color:#fff;")
    mermaid.append("classDef shared fill:#555,stroke:#777,color:#fff;")
    cls_map = {"GREEN": "green", "AMBER": "amber", "RED": "red", "SHARED": "shared"}
    for f, (s, r) in align.items():
        mermaid.append(f"    {f}:::{cls_map[s]}")
    for sf, row in feat_dep_rows:
        for d, n, c, fi in row:
            mermaid.append(f"    {sf} -->|{n}| {d}")
    mermaid.append("```")
    out.append("\n".join(mermaid))
    out.append("")
    out.append("| From feature | → To feature | Edges (call / fe-import) | To-feature health | Link status |")
    out.append("| --- | --- | --- | --- | --- |")
    for sf, row in feat_dep_rows:
        for d, n, c, fi in row:
            tgt = align.get(d, ("SHARED", ""))[0]
            status = "BROKEN — target not wired" if tgt == "RED" else "ok"
            out.append(f"| {sf} | {d} | {c} call / {fi} fe-import | {tgt} | {status} |")
    out.append("")
    out.append("_Features with no inter-feature dependencies are not listed here but appear in the "
                "Alignment Dashboard and Master Table above._")
    out.append("")

    # Function -> Function
    out.append("## Function → Function Call Graph (cross-feature edges)")
    out.append("")
    out.append(f"Total function→function edges resolved: **{len(cross['func_edges'])}** "
               f"({len(cross_func_edges)} cross-feature). Unresolved call targets: "
               f"**{cross['unresolved']}** (dynamic/`self.repo.x`/runtime dispatch — expected).")
    out.append("")
    out.append("Top cross-feature call lanes (source feature → target feature, by layer):")
    out.append("")
    out.append("| Source feature | Target feature | Source layer | Target layer | Cross calls |")
    out.append("| --- | --- | --- | --- | --- |")
    for (sf, tf, sl, tl), n in top_pairs:
        out.append(f"| {sf} | {tf} | {sl} | {tl} | {n} |")
    out.append("")
    out.append("Full edge list (src → tgt, with features) is written to "
               "`backend/FEATURE_CROSS_REFERENCES.json` under `func_edges_cross_feature`.")
    out.append("")

    # Operation -> Operation
    out.append("## Operation → Operation Wiring")
    out.append("")
    out.append(f"Router operations scanned: **{len(ops)}** — "
               f"**{len(wired_ops)} wired** (handler resolves to backend functions or dynamically "
               f"imports a controller/service), **{len(unwired_ops)} not wired** (stub health/status "
               "routes with no backend call — honest gap tracking).")
    out.append("")
    out.append("### Wired operations (route → handler → backend functions invoked)")
    out.append("")
    out.append("| Method | Path | Router feature | Handler | Invokes |")
    out.append("| --- | --- | --- | --- | --- |")
    for op in wired_ops[:400]:
        invokes = ", ".join(op["called"][:6]) or ", ".join(op["dyn_imports"][:3])
        if len(op["called"]) > 6:
            invokes += ", …"
        out.append(f"| {op['method']} | {op['path']} | {op['router_feat']} | "
                   f"{op['handler'].split('.')[-1]} | {invokes} |")
    out.append("")
    if len(wired_ops) > 400:
        out.append(f"_(showing first 400 of {len(wired_ops)} wired operations; full list in JSON)_")
        out.append("")
    out.append("### Cross-stack operation links (frontend API call → backend route)")
    out.append("")
    out.append(f"{len(cross_stack)} distinct frontend API paths resolve to a scanned backend route:")
    out.append("")
    out.append("| Frontend API path | Backend feature(s) | Frontend feature(s) |")
    out.append("| --- | --- | --- |")
    for p, bf, ff in cross_stack[:200]:
        out.append(f"| {p} | {', '.join(bf)} | {', '.join(ff)} |")
    out.append("")

    # ---- Wiring Problems (concrete layer-to-layer gaps) ----
    red_features = sorted(f for f, (s, r) in align.items() if s == "RED")
    amber_features = sorted(f for f, (s, r) in align.items() if s == "AMBER")
    green_features = sorted(f for f, (s, r) in align.items() if s == "GREEN")
    shared_features = sorted(f for f, (s, r) in align.items() if s == "SHARED")
    svc_no_ctrl = sorted(f for f in data
                         if data[f].get("services") and not data[f].get("controllers"))
    ctrl_no_rt = sorted(f for f in data
                        if data[f].get("controllers") and not data[f].get("routers")
                        and f != "delegators")
    models_only = sorted(f for f in data
                         if f not in PLATFORM_LAYERS
                         and (data[f].get("models") or data[f].get("db"))
                         and not data[f].get("services")
                         and not data[f].get("controllers")
                         and not data[f].get("routers"))
    provider_features = sorted(f for f in data if data[f].get("providers"))
    middleware_features = sorted(f for f in data if data[f].get("middleware"))

    out.append("## Wiring Problems (what to fix)")
    out.append("")
    out.append("Concrete gaps between **every** backend layer (models → db → providers → services → "
               "controllers → routers → middleware → utils). Each item is something to **verify or fix** — "
               "nothing here is flagged as dead code; these are un-wired, dynamically wired via `importlib`, "
               "or data-only layers. The matrix below shows how the complete backend is wired end-to-end.")
    out.append("")

    # Layer wiring matrix — how the whole backend is wired, layer by layer.
    out.append("### Layer wiring matrix")
    out.append("")
    out.append("| Layer | Files | Features using this layer | Wired to next layer? |")
    out.append("| --- | --- | --- | --- |")
    layer_notes = {
        "models": "ORM data models.",
        "db": "engine / session / bootstrap.",
        "providers": "external integrations (leaf layer).",
        "services": "business logic.",
        "controllers": "HTTP orchestration.",
        "routers": "API surface (endpoints).",
        "middleware": "cross-cutting HTTP middleware.",
        "utils": "shared helpers.",
        "events": "event bus / handlers.",
        "jobs": "async / background jobs.",
        "dependencies": "DI wiring.",
    }
    for l in LAYERS:
        feats_with = sorted(f for f in data if data[f].get(l))
        nf = len(feats_with)
        feats_str = ", ".join(feats_with) if nf <= 12 else f"{nf} features"
        # simple "wired to next layer?" heuristic
        if l == "models":
            nxt = sum(1 for f in feats_with if data[f].get("services") or data[f].get("controllers"))
            wired = f"{nxt}/{nf} have a service/controller"
        elif l == "providers":
            nxt = sum(1 for f in feats_with if data[f].get("services"))
            wired = f"{nxt}/{nf} consumed by a service"
        elif l == "services":
            nxt = sum(1 for f in feats_with if data[f].get("controllers"))
            wired = f"{nxt}/{nf} have a controller"
        elif l == "controllers":
            nxt = sum(1 for f in feats_with if data[f].get("routers"))
            wired = f"{nxt}/{nf} have a static router (rest dynamic)"
        elif l == "routers":
            wired = "API surface"
        elif l in ("db", "middleware", "utils", "events", "jobs", "dependencies"):
            wired = "platform / cross-cutting"
        else:
            wired = "—"
        out.append(f"| {l} | {totals[l]} | {feats_str} | {wired} |")
    out.append("")

    out.append(f"### RED — endpoint surface (router) exists but no service/controller ({len(red_features)})")
    out.append("")
    if red_features:
        for f in red_features:
            out.append(f"- **{f}** — {align[f][1]}")
    else:
        out.append("- none")
    out.append("")
    out.append(f"### AMBER — services present but no controller here ({len(svc_no_ctrl)})")
    out.append("")
    if svc_no_ctrl:
        out.append("- " + ", ".join(svc_no_ctrl))
    else:
        out.append("- none")
    out.append("")
    out.append(f"### AMBER — controllers present but no static router import (dynamic importlib) ({len(ctrl_no_rt)})")
    out.append("")
    if ctrl_no_rt:
        out.append("- " + ", ".join(ctrl_no_rt))
    else:
        out.append("- none")
    out.append("")
    out.append(f"### MODELS / DB — data layer with no service, controller or router ({len(models_only)})")
    out.append("")
    out.append("These features expose a data model but no business-logic layer — verify the logic lives "
               "cross-feature (e.g. in a shared service) or is genuinely absent.")
    out.append("")
    if models_only:
        for f in models_only:
            out.append(f"- **{f}** — {align[f][1]}")
    else:
        out.append("- none")
    out.append("")
    out.append(f"### PROVIDERS — external/integration implementations ({len(provider_features)})")
    out.append("")
    out.append("Provider layers are leaves (no controller/router required). Confirm each is actually "
               "consumed by a service.")
    out.append("")
    if provider_features:
        for f in provider_features:
            consumes = sorted(x for x in data
                              if data[x].get("services") and f in cross["feat_deps"].get(x, {}))
            note = f"consumed by: {', '.join(consumes)}" if consumes else "no service dependency detected"
            out.append(f"- **{f}** ({len(data[f].get('providers', []))} providers) — {note}")
    else:
        out.append("- none")
    out.append("")
    out.append(f"### MIDDLEWARE — platform HTTP middleware ({len(middleware_features)})")
    out.append("")
    if middleware_features:
        for f in middleware_features:
            files = data[f].get("middleware", [])
            out.append(f"- **{f}** — {len(files)} middleware file(s): "
                       + (", ".join(sorted(files)) if isinstance(files[0], str) else ", ".join(sorted(x[2] for x in files))))
    else:
        out.append("- none")
    out.append("")
    out.append(f"### STUB — routers whose handlers are unwired ({len(unwired_ops)}/{len(ops)})")
    out.append("")
    out.append(f"- {len(unwired_ops)} router operations have a stub handler (health/status) with no backend "
               "call — expected, but verify none are real endpoints masked as stubs.")
    out.append("")
    out.append(f"### BROKEN DEPENDENCIES — feature depends on a RED/unwired feature ({len(broken)})")
    out.append("")
    if broken:
        for sf, d in broken:
            out.append(f"- **{sf}** depends on **{d}** (RED — {align[d][1]})")
    else:
        out.append("- none")
    out.append("")

    # Gap register
    out.append("## Gap register (what is missing / risky)")
    out.append("")
    out.append("Severity: **HIGH** = genuine absence that breaks a feature; **MED** = risky / "
               "hard-to-verify; **LOW** = expected stub, verify anyway; **INFO** = by-design, not a defect.")
    out.append("")
    out.append("| Severity | Area | Finding | Recommended action |")
    out.append("| --- | --- | --- | --- |")
    for sev, area, finding, action in gaps:
        out.append(f"| {sev} | {area} | {finding} | {action} |")
    out.append("")

    # Notes
    out.append("## Notes")
    out.append("")
    out.append("- Module = the real backend directory name (e.g. `services/employee`, `services/hierarchy`, "
               "`services/country` are distinct rows, not folded into `hr`/`geography`).")
    out.append("- **Feature→Feature** is computed from AST call edges + import edges; an edge means A's code "
               "literally calls B's code. It is a static read — runtime dispatch (dynamic `importlib` in "
               "`main._load_routers`, `delegators/`) is NOT visible and shows as fewer/no edges.")
    out.append("- **Function→Function** resolves `module.fn()` and imported-name calls to the target function "
               "via the file's import map. `self.repo.method()` and other attribute-on-instance calls are "
               "left unresolved (counted in `unresolved_call_targets`) because they need runtime types.")
    out.append("- **Operation→Operation** traces each `@router.METHOD(path)` to its handler and the backend "
               "functions that handler calls. Unwired = stub routes (health/status) with no backend call.")
    out.append("- Frontend attribution is path-based and approximate; review per-feature frontend file lists before trusting them.")
    out.append("- The empty local `zozi.db` and the Alembic 2-head branch (see DIAGNOSIS_REPORT.md) are "
               "platform-level issues affecting ALL modules and are tracked separately.")
    out.append("")

    dest = os.path.join(out_dir, report_name)
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"Wrote {dest}: {len(rows)} module rows, backend files={sum(totals.values())}, "
          f"frontend files={total_fe}")
    print(f"Wrote {json_path}: func_edges={len(cross['func_edges'])} "
          f"(cross={len(cross_func_edges)}), ops={len(ops)} wired={len(wired_ops)}, "
          f"unresolved={cross['unresolved']}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Generate the ZOZI system cross-reference tracking report.")
    ap.add_argument("--backend", default=BACKEND,
                    help="Backend source dir (default: <repo>/backend)")
    ap.add_argument("--frontend", default=FRONTEND,
                    help="Frontend source dir (default: <repo>/frontend)")
    ap.add_argument("--out-dir", default=BACKEND,
                    help="Output dir for report + json (default: <repo>/backend)")
    ap.add_argument("--report-name", default="SYSTEM_TRACKING_REPORT.md")
    ap.add_argument("--json-name", default="FEATURE_CROSS_REFERENCES.json")
    args = ap.parse_args()
    # Globals are read by the scanning helpers (scan_backend_py, build_module_index).
    BACKEND = args.backend
    FRONTEND = args.frontend
    main(args.out_dir, args.report_name, args.json_name)
