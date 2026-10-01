"""ZOZI System — NEW_STRUCTURE.md Architecture & Implementation Audit.

This tracker measures the codebase *only* against the target taxonomy in
``documents/NEW_STRUCTURE.md``. It is organised around the three orthogonal
axes the document defines:

  * **Module**  (who acts)   : ``backend/modules/{m}/`` — auth + thin routers.
  * **Domain**  (what the business does) : ``backend/domains/{d}/`` —
    services / models / schemas / policies / events / features / ports /
    read_models / repositories, optionally sliced (``{d}/{slice}/...``).
  * **Feature** (what may be done) : ``backend/domains/{d}/features.py``
    aggregated by ``backend/rbac/catalog.py`` and enforced by
    ``require_feature(...)``.

What makes this tracker different from a naive file-counter:

  1. **Content-aware.** Every file is parsed with ``ast`` so the audit reports
     *what is actually written* (ORM models, Pydantic schemas, service classes,
     event classes, policy functions) — not just whether a folder exists.
  2. **LLM-reviewed.** When OLLAMA is reachable, an LLM reads the extracted
     signatures and writes a detailed, human description of what each module,
     domain and feature actually implements, and judges whether module routers
     are "thin" per Law 2. All LLM answers are cached to disk so repeat runs
     are fast and never crash when the model is offline.
  3. **Law-enforcing.** The seven laws of ``NEW_STRUCTURE.md`` are checked
     directly against the source and every breach is raised as a violation
     alert (direction of arrows, thin routers, cross-domain wiring, single-
     sourced features, country scope, schema discipline, strangler rule).

The report is organised strictly by hierarchy: **Modules → Domains →
Features**, followed by the cross-axis wiring and the violation register.
"""

import os
import ast
import re
import json
import hashlib
import urllib.request
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # zozi/
BACKEND = os.path.join(REPO, "backend")
DOCS_AUDIT = os.path.join(REPO, "docs", "audit")

# Folders that must never be treated as project source.
EXCLUDE_DIRS = {"__pycache__", ".venv", "venv", "node_modules", ".git", "var", "uploads",
                "_legacy", ".pytest_cache", ".hypothesis"}


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def norm(p):
    return p.replace(os.sep, "/")


def read_text(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception:
        return ""


def walk_py_dir(root):
    """Return .py files under ``root`` (absolute) as paths relative to BACKEND,
    excluding ``__init__.py`` and ignored dirs."""
    out = []
    if not os.path.isdir(root):
        return out
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                out.append(norm(os.path.relpath(os.path.join(dirpath, f), BACKEND)))
    return sorted(out)


def list_dirs(root):
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                 if os.path.isdir(os.path.join(root, d)) and d not in EXCLUDE_DIRS)


# ---------------------------------------------------------------------------
# OLLAMA helper (optional, cached, resilient)
# ---------------------------------------------------------------------------
class Llm:
    """Tiny OLLAMA ``/api/generate`` client. Degrades silently when offline."""

    def __init__(self, base_url="http://localhost:11434", model="qwen2.5:latest",
                 enabled=True, cache_path=None, timeout=180):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.enabled = enabled
        self.cache_path = cache_path
        self.timeout = timeout
        self._lock = threading.Lock()
        self.cache = self._load()

    def _load(self):
        if self.cache_path and os.path.isfile(self.cache_path):
            try:
                with open(self.cache_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        if self.cache_path:
            try:
                with self._lock:
                    with open(self.cache_path, "w", encoding="utf-8") as f:
                        json.dump(self.cache, f, indent=2)
            except Exception:
                pass

    def ask(self, prompt, system=None, max_tokens=700):
        if not self.enabled:
            return ""
        key = hashlib.sha256((self.model + "|" + (system or "") + "|" + prompt).encode()).hexdigest()
        if key in self.cache:
            return self.cache[key]
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or "You are a concise senior software architect.",
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.2},
        }
        text = ""
        try:
            req = urllib.request.Request(
                self.base_url + "/api/generate",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
            text = (data.get("response") or "").strip()
        except Exception:
            text = ""
        # Only cache successful, non-empty answers so failed calls can be retried.
        if text:
            self.cache[key] = text
            self._save()
        return text


# ---------------------------------------------------------------------------
# AST content extraction
# ---------------------------------------------------------------------------
def file_signatures(path):
    """Return a dict describing what is actually written in a .py file."""
    txt = read_text(path)
    if not txt.strip():
        return {"loc": 0, "classes": [], "functions": [], "models": [], "schemas": [],
               "services": [], "events": [], "policies": [], "repositories": []}
    try:
        tree = ast.parse(txt)
    except Exception:
        return {"loc": len(txt.splitlines()), "classes": [], "functions": [],
                "models": [], "schemas": [], "services": [], "events": [],
                "policies": [], "repositories": []}

    classes, functions = [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)

    models, schemas, services, events, policies, repos = [], [], [], [], [], []
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        name = cls.name
        bases = [b.id for b in cls.bases if isinstance(b, ast.Name)]
        body_src = ast.get_source_segment(txt, cls) or ""
        is_model = ("Column(" in body_src or "__tablename__" in body_src
                    or any(b in ("Base", "Model", "SQLModel") for b in bases))
        is_schema = ("BaseModel" in bases or name.endswith(("Schema", "DTO"))
                     and "Column(" not in body_src)
        is_event = name.endswith("Event") or "Event" in bases
        is_repo = name.endswith(("Repository", "Repo")) or "Repository" in bases
        if is_model:
            models.append(name)
        elif is_schema:
            schemas.append(name)
        elif is_event:
            events.append(name)
        elif is_repo:
            repos.append(name)
        elif name.endswith("Service") or name.endswith("Controller") or "Service" in name:
            services.append(name)
    for fn in functions:
        if fn.startswith("policy_") or fn.endswith("_policy") or "policy" in fn:
            policies.append(fn)

    return {
        "loc": len(txt.splitlines()),
        "classes": classes,
        "functions": functions,
        "models": models,
        "schemas": schemas,
        "services": services,
        "events": events,
        "policies": policies,
        "repositories": repos,
    }


# Cached signatures so several passes over the same file do not re-parse it.
_SIG_CACHE = {}


def sig(path):
    """``file_signatures`` wrapped in a per-run cache (path is backend-relative)."""
    if path not in _SIG_CACHE:
        _SIG_CACHE[path] = file_signatures(path)
    return _SIG_CACHE[path]


def content_line(label, paths, top=6):
    """One-line 'what is actually written' digest for a set of files.

    Returns "" (no bullet) when there is nothing meaningful to report, else a
    ready-to-print bullet: ``- content: <label> (N files, X classes, Y functions,
    Z LOC): SampleClass, sample_func, ...``
    """
    if not paths:
        return ""
    cls = funcs = loc = 0
    names = []
    for p in paths:
        s = sig(os.path.join(BACKEND, p))
        loc += s["loc"]
        cls += len(s["classes"])
        funcs += len(s["functions"])
        for n in (s["models"] + s["schemas"] + s["services"] + s["events"]):
            if len(names) < top:
                names.append(n)
    if not cls and not funcs:
        return f"- content: {label} ({len(paths)} files, {loc} LOC) — no classes/functions detected"
    return (f"- content: {label} ({len(paths)} files, {cls} classes, {funcs} functions, "
            f"{loc} LOC): {', '.join(names[:top])}")


# Layer order used everywhere a domain's anatomy is listed (hierarchy-wise).
LAYER_ORDER = ["services", "models", "schemas", "policies", "repositories",
               "read_models", "events.py", "subscribers.py", "features.py", "ports.py"]


# ---------------------------------------------------------------------------
# Three-axis taxonomy (from documents/NEW_STRUCTURE.md, verified on disk)
# ---------------------------------------------------------------------------
def discover_modules():
    mods = list_dirs(os.path.join(BACKEND, "modules"))
    return [m for m in mods if m not in EXCLUDE_DIRS]


def discover_domains():
    doms = list_dirs(os.path.join(BACKEND, "domains"))
    return [d for d in doms if d not in EXCLUDE_DIRS and d != "UNMAPPED"]


PLATFORM_LAYERS = ["infrastructure", "kernel", "providers", "jobs", "middleware",
                   "events", "dependencies", "db", "utils", "tests", "scripts"]

MODULE_DESC = {
    "admin": "Admin console (MFA/TOTP, moderation, payouts, command center, RBAC).",
    "customer": "Customer storefront (catalog, checkout, tracking, wishlist).",
    "employee": "Employee self-service (payslip, leave, expenses, attendance).",
    "logistics": "Logistics partner (pickups, shipments, settlements, COD remittance).",
    "supplier": "Supplier portal (onboarding, products, orders, payouts, finance).",
}
DOMAIN_DESC = {
    "accounts": "AR/AP sub-ledgers, invoices, reconciliation.",
    "catalog": "Products, variants, categories, coupons, reviews, moderation.",
    "comms": "Chat, email, campaigns, notifications, escalation.",
    "country": "Country configs, tax rates, staff assignments, RLS scope axis.",
    "customers": "Addresses, referrals, badge tiers, wishlists.",
    "finance": "Ledger, treasury, reporting, payouts, VAT, cash forecast.",
    "governance": "Audit logs, fraud, manual review, command center, system health.",
    "hr": "Employees, org units, attendance, shifts, leave, biometrics, payroll.",
    "logistics": "Partners, shipments, tracking, settlements, distance matrix.",
    "media": "Media assets, product videos, video rooms, AI upload jobs.",
    "orders": "Orders, items, carts, returns, disputes, lifecycle.",
    "payments": "Gateway connections, webhook events, settlement schedules.",
    "suppliers": "Profiles, documents, KYC, onboarding.",
}

# Layer anatomy a healthy domain exposes (Law-implied).
FOLDER_LAYERS = ["services", "models", "schemas", "policies", "repositories", "read_models"]
SINGLE_FILE_LAYERS = {"events.py", "subscribers.py", "features.py", "ports.py"}


def layer_of(relpath):
    """Map a backend-relative path to the domain layer it belongs to (or None)."""
    parts = relpath.split("/")
    base = parts[-1]
    for layer in FOLDER_LAYERS:
        if ("/" + layer + "/") in relpath:
            return layer
    # vertical slices: finance/ledger/service.py, finance/ledger/models.py ...
    if base in ("service.py", "services.py") or base.endswith("_service.py"):
        return "services"
    if base == "models.py":
        return "models"
    if base == "schemas.py":
        return "schemas"
    if base == "policies.py":
        return "policies"
    if base == "repositories.py":
        return "repositories"
    if base == "read_models.py":
        return "read_models"
    if base in SINGLE_FILE_LAYERS:
        return base
    return None


# ---------------------------------------------------------------------------
# Feature-atom parsing (Axis 3 seed)
# ---------------------------------------------------------------------------
def _const(node):
    if isinstance(node, ast.Constant):
        return node.value
    return ""


def _list_const(node):
    if isinstance(node, ast.List):
        return [_const(e) for e in node.elts]
    return []


def _snake(name):
    """Class name → snake_case (e.g. CountryConfigVersion → country_config_version)."""
    s = re.sub(r"(?<!^)(?=[A-Z])", "_", name)
    s = re.sub(r"[^A-Za-z0-9_]", "", s)
    return s.lower()


def _plural(word):
    """NEW_STRUCTURE.md naming lint: tables must be plural snake_case."""
    return bool(re.search(r"(ies|ses|es|s)$", word))


def parse_features(path):
    """Return [(key, label, risk, actions, description)] from a domain FEATURES dict."""
    res = []
    txt = read_text(path)
    if not txt.strip():
        return res
    try:
        tree = ast.parse(txt)
    except Exception:
        return res
    for node in ast.walk(tree):
        target = value = None
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                target, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                target, value = node.target.id, node.value
        if target != "FEATURES" or not isinstance(value, ast.Dict):
            continue
        for k, v in zip(value.keys, value.values):
            if not isinstance(k, ast.Constant):
                continue
            label = risk = desc = ""
            actions = []
            if isinstance(v, ast.Dict):
                for dk, dv in zip(v.keys, v.values):
                    if isinstance(dk, ast.Constant):
                        if dk.value == "label":
                            label = _const(dv)
                        elif dk.value == "risk":
                            risk = _const(dv)
                        elif dk.value == "description":
                            desc = _const(dv)
                        elif dk.value == "actions":
                            actions = _list_const(dv)
            res.append((str(k.value), label, risk, actions, desc))
    return res


# ---------------------------------------------------------------------------
# Import regexes (used for law enforcement)
# ---------------------------------------------------------------------------
DOMAIN_IMPORT_RE = re.compile(r"from\s+domains\.([a-z_]+)")
MODULE_IMPORT_RE = re.compile(r"from\s+modules\.([a-z_]+)")
DOMAIN_ATTR_RE = re.compile(r"domains\.([a-z_]+)\.")
REQUIRE_FEATURE_RE = re.compile(r'require_feature\(\s*["\']([a-z0-9_.]+)["\']')
RISK_RE = re.compile(r"risk", re.I)


# ---------------------------------------------------------------------------
# Axis 1 — Modules (content-aware)
# ---------------------------------------------------------------------------
def classify_module_file(relpath, sig):
    """Thin-router heuristic (Law 2). Returns (thin_score, notes)."""
    base = os.path.basename(relpath).lower()
    notes = []
    score = 0
    if "/routers/" in relpath:
        t = read_text(os.path.join(BACKEND, relpath))
        writes = len(re.findall(r"\.(commit|flush|add|merge|delete)\s*\(", t))
        model_inst = len(re.findall(r"=\s*[A-Z]\w*\([^)]*\)", t))
        direct_orm = len(re.findall(r"session\.(execute|query|add|commit)", t, re.I))
        # Law 2 (thin router): flag only genuine business logic / DB writes.
        if writes or direct_orm or model_inst > 3:
            score += writes + direct_orm + max(0, model_inst - 3)
            notes.append("contains DB writes / model instantiation (Law 2)")
        if not re.search(r"require_feature|Depends\(", t):
            notes.append("no require_feature gate detected")
    return score, notes


def scan_modules():
    out = {}
    for m in discover_modules():
        root = os.path.join(BACKEND, "modules", m)
        files = walk_py_dir(root)
        exposed = set()
        gated = set()
        residual = set()
        router_files = []
        for r in files:
            t = read_text(os.path.join(BACKEND, r))
            for mm in DOMAIN_IMPORT_RE.finditer(t):
                if discover_domains_contains(mm.group(1)):
                    exposed.add(mm.group(1))
            for mm in DOMAIN_ATTR_RE.finditer(t):
                if discover_domains_contains(mm.group(1)):
                    exposed.add(mm.group(1))
            for mm in REQUIRE_FEATURE_RE.finditer(t):
                gated.add(mm.group(1))
            if re.search(r"from\s+controllers\.|import\s+controllers", t):
                residual.add(r)
            if "/routers/" in r:
                router_files.append(r)
        # filename-token inference (supplementary)
        for r in files:
            base = os.path.basename(r).lower()
            for seg in re.split(r"[^a-z0-9]+", base):
                if discover_domains_contains(seg):
                    exposed.add(seg)
        # router thickness
        thick = []
        for r in router_files:
            score, notes = classify_module_file(r, None)
            if score >= 3 or any("controller" in n for n in notes):
                thick.append((r, notes))
        out[m] = {
            "files": files,
            "routers": router_files,
            "auth": [r for r in files if "/auth/" in r],
            "serializers": [r for r in files if "/serializers/" in r],
            "exposed": sorted(exposed),
            "gated": sorted(gated),
            "residual": sorted(residual),
            "thick_routers": thick,
            "status": "Active" if router_files else "Empty",
        }
    return out


# Digest of all domains (filled later) — placeholder for inference.
_ALL_DOMAINS = []


def discover_domains_contains(name):
    return name in _ALL_DOMAINS


# ---------------------------------------------------------------------------
# Axis 2 — Domains (slice-aware, content-aware)
# ---------------------------------------------------------------------------
def scan_domain(d):
    root = os.path.join(BACKEND, "domains", d)
    files = walk_py_dir(root)
    layers = defaultdict(list)
    for r in files:
        ly = layer_of(r)
        if ly:
            layers[ly].append(r)
    # content depth per layer
    layer_depth = {}
    for ly, fl in layers.items():
        classes = funcs = models = 0
        for r in fl:
            s = file_signatures(os.path.join(BACKEND, r))
            classes += len(s["classes"])
            funcs += len(s["functions"])
            models += len(s["models"])
        layer_depth[ly] = {"files": len(fl), "classes": classes,
                           "functions": funcs, "models": models}
    atoms = parse_features(os.path.join(root, "features.py"))
    # backing: capability token present in file/class/func names or blob
    sig_by_file = {}
    for r in files:
        sig_by_file[r] = file_signatures(os.path.join(BACKEND, r))
    blob = "\n".join(read_text(os.path.join(BACKEND, r)) for r in files)
    backed = []
    for (key, _l, _r, _a, _de) in atoms:
        cap = key.split(".")[-1]
        hit = (key in blob) or (cap in blob)
        if not hit:
            for r, s in sig_by_file.items():
                hay = " ".join(s["classes"] + s["functions"] + [os.path.basename(r)])
                if cap in hay or cap.replace("_", "") in hay.replace("_", ""):
                    hit = True
                    break
        backed.append(hit)
    # inter-domain dependencies (Law 3)
    deps = defaultdict(int)
    cross_violations = []
    for r in files:
        ly = layer_of(r)
        t = read_text(os.path.join(BACKEND, r))
        for mm in DOMAIN_IMPORT_RE.finditer(t):
            target = mm.group(1)
            if target in _ALL_DOMAINS and target != d:
                deps[target] += 1
                legal = ("/ports" in r or "/ports/" in r or "ports.py" in r
                         or "events.py" in r or "/events/" in r
                         or "/read_models" in r or "read_models.py" in r)
                if not legal:
                    cross_violations.append((r, target))
    return {
        "files": files,
        "layers": dict(layers),
        "layer_depth": layer_depth,
        "atoms": atoms,
        "backed": backed,
        "deps": dict(deps),
        "cross_violations": cross_violations,
        "total_classes": sum(v["classes"] for v in layer_depth.values()),
        "total_models": sum(v["models"] for v in layer_depth.values()),
    }


def scan_domains():
    out = {}
    for d in _ALL_DOMAINS:
        out[d] = scan_domain(d)
    return out


# ---------------------------------------------------------------------------
# Axis 3 aggregation — rbac catalog
# ---------------------------------------------------------------------------
def scan_rbac():
    atoms = []
    for d in _ALL_DOMAINS:
        for (key, label, risk, actions, desc) in parse_features(
                os.path.join(BACKEND, "domains", d, "features.py")):
            atoms.append((d, key, label, risk, actions, desc))
    gated = set()
    for m in discover_modules():
        for r in walk_py_dir(os.path.join(BACKEND, "modules", m)):
            for mm in REQUIRE_FEATURE_RE.finditer(read_text(os.path.join(BACKEND, r))):
                gated.add(mm.group(1))
    for r in walk_py_dir(os.path.join(BACKEND, "rbac")):
        for mm in REQUIRE_FEATURE_RE.finditer(read_text(os.path.join(BACKEND, r))):
            gated.add(mm.group(1))
    # unknown gates: require_feature literals not present in the catalog
    catalog_keys = {k for (_d, k, *_x) in atoms}
    unknown_gates = sorted(g for g in gated if g not in catalog_keys)
    return atoms, gated, catalog_keys, unknown_gates, \
        os.path.isfile(os.path.join(BACKEND, "rbac", "catalog.py"))


# ---------------------------------------------------------------------------
# Platform layers (context — what else is running)
# ---------------------------------------------------------------------------
def scan_platform():
    out = {}
    for layer in PLATFORM_LAYERS:
        root = os.path.join(BACKEND, layer)
        if os.path.isdir(root):
            files = walk_py_dir(root)
            out[layer] = {
                "files": len(files),
                "has_init": os.path.isfile(os.path.join(root, "__init__.py")),
            }
    return out


# ---------------------------------------------------------------------------
# Completion / status model (content-aware)
# ---------------------------------------------------------------------------
CORE_LAYERS = ["models", "services", "schemas", "events"]


def domain_completion(dom):
    """Return (status, pct, present_layers) for a domain.

    A layer counts as *present* only when it has at least one real class or
    function (content check, not just an empty folder). Core layers earn 20%
    each; features earn 20% only when atoms are defined; bonuses:
    policies(+8)/subscribers(+8)/ports(+4)/read_models(+4)/repositories(+4).
    Status: Implemented >=80 · Partial >=45 · Scaffold <45.
    """
    depth = dom["layer_depth"]
    present = []
    for ly in CORE_LAYERS:
        d = depth.get(ly)
        if d and (d["files"] > 0 and (d["classes"] + d["functions"]) > 0):
            present.append(ly)
    pct = 20 * len(present)
    if depth.get("features", {}).get("files", 0) > 0 and dom["atoms"]:
        pct += 20
        present.append("features")
    for ly, bonus in (("policies", 8), ("subscribers", 8), ("ports", 4),
                      ("read_models", 4), ("repositories", 4)):
        d = depth.get(ly)
        if d and (d["files"] > 0 and (d["classes"] + d["functions"]) > 0):
            pct += bonus
            present.append(ly)
    pct = min(100, round(pct))
    if pct >= 80:
        status = "Implemented"
    elif pct >= 45:
        status = "Partial"
    else:
        status = "Scaffold"
    return status, pct, present


def feature_status(backed, gated):
    if backed and gated:
        return "Active"
    if backed:
        return "Implemented"
    if gated:
        return "Enforced"
    return "Defined"


# ---------------------------------------------------------------------------
# Law violations (the 7 laws of NEW_STRUCTURE.md)
# ---------------------------------------------------------------------------
def detect_violations(modules, domains, rbac_atoms, unknown_gates):
    """Return list of (law, severity, area, finding, action)."""
    v = []
    domains_set = set(_ALL_DOMAINS)
    modules_set = set(discover_modules())

    # ---- Law 1: arrows point down only ----
    # domain -> module, infrastructure -> upper, domain -> rbac
    for d in domains_set:
        root = os.path.join(BACKEND, "domains", d)
        for r in walk_py_dir(root):
            t = read_text(os.path.join(BACKEND, r))
            if MODULE_IMPORT_RE.search(t):
                v.append(("Law 1", "HIGH", "direction",
                          f"domain/{d} imports a module: {r}",
                          "Remove the upward import; modules compose domains, never the reverse."))
            if re.search(r"from\s+rbac\b", t):
                v.append(("Law 1", "HIGH", "direction",
                          f"domain/{d} imports rbac: {r}",
                          "Domains enforce policies, not permissions; rbac is imported only by modules/middleware."))
    for layer in ("infrastructure", "kernel", "providers", "jobs", "middleware"):
        root = os.path.join(BACKEND, layer)
        for r in walk_py_dir(root):
            t = read_text(os.path.join(BACKEND, r))
            if DOMAIN_IMPORT_RE.search(t) or MODULE_IMPORT_RE.search(t):
                v.append(("Law 1", "MED", "direction",
                          f"platform/{layer} imports an upper layer: {r}",
                          "Platform layers must import nothing above them."))
    # residual `controllers` imports anywhere
    residual_hits = []
    for r in walk_py_dir(BACKEND):
        t = read_text(os.path.join(BACKEND, r))
        if re.search(r"from\s+controllers\.|import\s+controllers", t):
            residual_hits.append(r)
    if residual_hits:
        v.append(("Law 1", "HIGH", "residual",
                  f"{len(residual_hits)} files bypass the module→domain composition rule "
                  f"by importing from the deprecated controllers layer "
                  f"(e.g. {', '.join(residual_hits[:3])}).",
                  "Route logic must live in module routers; business logic must live in domain services."))

    # ---- Law 2: thin module routers ----
    thick_all = []
    ungated_all = []
    for m in modules_set:
        for (r, notes) in modules[m]["thick_routers"]:
            thick_all.append((m, r, notes))
        for r in modules[m]["routers"]:
            t = read_text(os.path.join(BACKEND, r))
            if not re.search(r"require_feature|Depends\(", t):
                ungated_all.append((m, r))
    if thick_all:
        sample = "; ".join(f"{m}/{os.path.basename(r)}" for m, r, _n in thick_all[:5])
        v.append(("Law 2", "HIGH", "thin-router",
                  f"{len(thick_all)} module routers carry business logic / DB writes "
                  f"(e.g. {sample}).",
                  "Push logic into domain services; routers keep only auth + require_feature + one call."))
    if ungated_all:
        sample = "; ".join(f"{m}/{os.path.basename(r)}" for m, r in ungated_all[:5])
        v.append(("Law 2", "HIGH", "thin-router",
                  f"{len(ungated_all)} module routers have no feature/auth gate at all "
                  f"(e.g. {sample}).",
                  "Every router endpoint must include require_feature(...) or equivalent auth dependency."))

    # ---- Law 3: cross-domain wiring ----
    cross_total = 0
    cross_write_violations = []
    cross_read_violations = []
    for d in domains_set:
        for (r, target) in domains[d]["cross_violations"]:
            cross_total += 1
            if len(cross_write_violations) < 3:
                cross_write_violations.append(f"{d} → {target} ({os.path.basename(r)})")
    allowlist = read_text(os.path.join(BACKEND, "DOMAIN_ALLOWLIST.yaml"))
    allowlist_entries = len(re.findall(r"-\s+\S+", allowlist)) if allowlist else 0
    if cross_total:
        v.append(("Law 3", "HIGH", "cross-domain",
                  f"{cross_total} cross-domain imports bypass the sanctioned ports/events path "
                  f"(e.g. {', '.join(cross_write_violations)}). Allowlist entries: {allowlist_entries}.",
                  "Route cross-domain reads through the target domain's ports.py or read_models/; "
                  "route cross-domain writes through events.py/subscribers.py only."))

    # ---- Law 4: features single-sourced ----
    empty_feature_domains = [d for d in domains_set if not domains[d]["atoms"]]
    if empty_feature_domains:
        v.append(("Law 4", "HIGH", "features",
                  f"{len(empty_feature_domains)}/{len(domains_set)} domains have an empty "
                  f"features.py (no atoms): {', '.join(empty_feature_domains)}.",
                  "Seed each domain's feature atoms so the rbac catalog is complete and single-sourced."))
    # duplicate feature keys across domains (single-sourced = one definition)
    key_seen = {}
    for d in domains_set:
        for (key, *_rest) in domains[d]["atoms"]:
            key_seen.setdefault(key, []).append(d)
    dups = {k: v_ for k, v_ in key_seen.items() if len(v_) > 1}
    if dups:
        sample = "; ".join(f"{k} defined in {', '.join(v_)}" for k, v_ in list(dups.items())[:5])
        v.append(("Law 4", "HIGH", "features",
                  f"{len(dups)} feature keys are defined in more than one domain (e.g. {sample}).",
                  "A feature atom must be defined in exactly one domain's features.py; merge or rename."))
    if unknown_gates:
        v.append(("Law 4", "HIGH", "features",
                  f"{len(unknown_gates)} require_feature(...) literals are NOT in any domain "
                  f"features.py (e.g. {', '.join(unknown_gates[:6])}).",
                  "Add the missing atom to the owning domain's features.py or fix the literal (CI must fail)."))
    if not os.path.isfile(os.path.join(BACKEND, "rbac", "catalog.py")):
        v.append(("Law 4", "HIGH", "rbac",
                  "backend/rbac/catalog.py missing — no single source of truth for features.",
                  "Create catalog.py that package-scans domains/*/features.py."))

    # ---- Law 5: country as orthogonal scope axis ----
    country_imports = 0
    for r in walk_py_dir(BACKEND):
        if re.search(r"country_code|country_staff_assignments|rls|row_level_security",
                     read_text(os.path.join(BACKEND, r)), re.I):
            country_imports += 1
    if country_imports == 0:
        v.append(("Law 5", "INFO", "country-axis",
                  "No RLS / country-scoped access markers detected yet.",
                  "Introduce country_code + country_staff_assignments as an independent scope axis."))

    # ---- Law 6: schema discipline (ast-based, no fragile regex) ----
    # NEW_STRUCTURE.md: every table in a domain Postgres schema; Alembic is the
    # only schema source; naming lint = snake_case, plural, <thing>_id,
    # created_at/updated_at, country_code, is_deleted.
    models_missing_schema = 0
    models_bad_name = 0
    models_missing_country = 0
    models_missing_ts = 0
    models_missing_deleted = 0
    samples = {"schema": [], "name": [], "country": [], "ts": [], "deleted": []}
    for d in domains_set:
        for r in domains[d]["layers"].get("models", []):
            raw = read_text(os.path.join(BACKEND, r))
            try:
                tree = ast.parse(raw)
            except Exception:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                body = ast.get_source_segment(raw, node) or ""
                is_model = ("Column(" in body or "__tablename__" in body
                            or any(isinstance(b, ast.Name) and b.id in ("Base", "Model", "SQLModel")
                                   for b in node.bases))
                if not is_model:
                    continue
                tag = f"{os.path.basename(r)}::{node.name}"
                # 1) explicit Postgres schema per domain
                if "__table_args__" not in body:
                    models_missing_schema += 1
                    if len(samples["schema"]) < 5:
                        samples["schema"].append(tag)
                # 2) naming lint: plural snake_case table name
                tbl = _snake(node.name)
                if not _plural(tbl):
                    models_bad_name += 1
                    if len(samples["name"]) < 5:
                        samples["name"].append(tag)
                # 3) country_code + created_at/updated_at on business tables
                if "country_code" not in body:
                    models_missing_country += 1
                    if len(samples["country"]) < 5:
                        samples["country"].append(tag)
                if "created_at" not in body or "updated_at" not in body:
                    models_missing_ts += 1
                    if len(samples["ts"]) < 5:
                        samples["ts"].append(tag)
                if "is_deleted" not in body:
                    models_missing_deleted += 1
                    if len(samples["deleted"]) < 5:
                        samples["deleted"].append(tag)
    if models_missing_schema:
        v.append(("Law 6", "MED", "schema",
                  f"{models_missing_schema} ORM model classes omit an explicit Postgres schema in "
                  f"__table_args__ (e.g. {', '.join(samples['schema'])}).",
                  "Declare __table_args__ = {'schema': '<domain>'} so each domain owns one DB schema."))
    if models_bad_name:
        v.append(("Law 6", "MED", "naming",
                  f"{models_bad_name} ORM model classes have a non-plural snake_case table name "
                  f"(e.g. {', '.join(samples['name'])}).",
                  "Rename to plural snake_case (e.g. CountryConfig → country_configs)."))
    if models_missing_country:
        v.append(("Law 6", "MED", "naming",
                  f"{models_missing_country} ORM model classes omit the country_code column "
                  f"(e.g. {', '.join(samples['country'])}).",
                  "Add country_code as an independent RLS scope axis on every business table."))
    if models_missing_ts:
        v.append(("Law 6", "MED", "naming",
                  f"{models_missing_ts} ORM model classes omit created_at/updated_at "
                  f"(e.g. {', '.join(samples['ts'])}).",
                  "Add created_at and updated_at to every business table."))
    if models_missing_deleted:
        v.append(("Law 6", "MED", "naming",
                  f"{models_missing_deleted} ORM model classes omit is_deleted "
                  f"(e.g. {', '.join(samples['deleted'])}).",
                  "Add is_deleted to every business table for soft-delete compliance."))

    # ---- Law 7: strangler rule ----
    if os.path.isdir(os.path.join(BACKEND, "_legacy")):
        v.append(("Law 7", "MED", "strangler",
                  "_legacy/ shims still present — delete when each slice is migration-ready.",
                  "Remove shims as domains reach 100% and tests go green."))
    else:
        v.append(("Law 7", "INFO", "strangler",
                  "_legacy/ folder absent — no deprecated shims tracked.",
                  "Keep DOMAIN_ALLOWLIST.yaml shrinking to zero."))

    return v


# ---------------------------------------------------------------------------
# OLLAMA descriptions (features / domains / modules)
# ---------------------------------------------------------------------------
SYS_FEATURE = ("You are a senior software architect documenting a modular "
               "monolith. Be precise, concrete, and concise (2-3 sentences).")
SYS_REVIEW = ("You are a strict architecture reviewer. Answer in 1-2 sentences, "
              "flagging whether the code follows a thin-adapter pattern.")


def ollama_domain_description(d, dom, llm):
    if not llm.enabled:
        return ""
    sig = []
    for r in dom["files"][:12]:
        s = file_signatures(os.path.join(BACKEND, r))
        if s["classes"]:
            sig.append(f"- {os.path.basename(r)}: {', '.join(s['classes'][:5])}")
    atoms = "; ".join(f"{k} ({lb or 'no label'})" for (k, lb, _r, _a, _de) in dom["atoms"]) or "none defined"
    content_snippets = []
    for r in dom["files"][:8]:
        actual = read_text(os.path.join(BACKEND, r))[:400].strip()
        if actual:
            content_snippets.append(f"- {os.path.basename(r)}: {actual[:180]}")
    content_txt = "\n".join(content_snippets[:6]) or "no readable content"
    prompt = (f"Domain '{d}' in a modular-monolith e-commerce backend.\n"
              f"Feature atoms: {atoms}.\n"
              f"Signatures:\n" + "\n".join(sig) + "\n"
              f"Code:\n{content_txt}\n\n"
              f"Describe what this domain implements (2-3 sentences). Note if feature atoms are missing.")
    return llm.ask(prompt, system=SYS_FEATURE, max_tokens=240)


def ollama_feature_description(d, key, label, risk, actions, desc, backed, gated, dom, llm):
    if not llm.enabled:
        return ""
    cap = key.split(".")[-1]
    related = [os.path.basename(r) for r in dom["files"]
               if cap in r or cap.replace("_", "") in r.replace("_", "")]
    state = ("backed by domain code" if backed else "no backing code detected") + \
            (", gated by require_feature" if gated else ", not yet gated by require_feature")
    content_snippets = []
    for r in dom["files"][:6]:
        actual = read_text(os.path.join(BACKEND, r))[:300].strip()
        hay = actual.lower()
        if cap in hay or cap.replace("_", "") in hay.replace("_", ""):
            content_snippets.append(f"- {os.path.basename(r)}: {actual[:180]}")
    content_txt = "\n".join(content_snippets[:4]) or "no directly related code snippets found"
    prompt = (f"Feature '{key}' (label: {label or 'n/a'}, risk: {risk or 'n/a'}, "
              f"actions: {', '.join(actions) or 'n/a'}).\n"
              f"State: {state}.\n"
              f"Related: {', '.join(related[:6]) or 'none'}.\n"
              f"Code:\n{content_txt}\n\n"
              f"Describe what this feature gates (2-3 sentences). Be concrete about risk and implementation.")
    return llm.ask(prompt, system=SYS_FEATURE, max_tokens=220)


def ollama_module_description(m, info, llm):
    if not llm.enabled:
        return ""
    routers = [os.path.basename(r) for r in info["routers"][:25]]
    content = []
    for r in info["routers"][:6]:
        s = sig(os.path.join(BACKEND, r))
        names = (s["models"] + s["schemas"] + s["services"] + s["events"]
                 + s["classes"] + s["functions"])
        actual = read_text(os.path.join(BACKEND, r))[:500].strip()
        if names:
            content.append(f"- {os.path.basename(r)}: {', '.join(names[:4])}\n  code: {actual[:180]}")
    content_txt = "\n".join(content[:6]) or "no service/schema/model classes in routers"
    prompt = (f"Module '{m}' is an access surface (actor) in a modular monolith.\n"
              f"Routers present: {', '.join(routers) or 'none'}.\n"
              f"Domains it composes: {', '.join(info['exposed']) or 'none'}.\n"
              f"Content:\n{content_txt}\n\n"
              f"Describe what this module exposes (2-3 sentences).")
    return llm.ask(prompt, system=SYS_FEATURE, max_tokens=220)


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------
def build_ollama_cache(modules, domains, rbac_atoms, rbac_gated, llm):
    """Generate LLM descriptions in parallel (OLLAMA queues concurrent requests)."""
    mod_desc, dom_desc, feat_desc = {}, {}, {}

    def runner(kind, key, fn):
        return kind, key, fn()

    tasks = []  # (kind, key, callable)
    for m in discover_modules():
        tasks.append(("mod", m, lambda mm=m: ollama_module_description(mm, modules[mm], llm)))
    for d in _ALL_DOMAINS:
        tasks.append(("dom", d, lambda dd=d: ollama_domain_description(dd, domains[dd], llm)))
        for (key, label, risk, actions, desc), b in zip(domains[d]["atoms"], domains[d]["backed"]):
            g = key in rbac_gated
            tasks.append(("feat", (d, key),
                          lambda dd=d, kk=key, lb=label, rk=risk, ac=actions, de=desc, bb=b, gg=g:
                          ollama_feature_description(dd, kk, lb, rk, ac, de, bb, gg, domains[dd], llm)))
    if llm.enabled and tasks:
        done = 0
        with ThreadPoolExecutor(max_workers=3) as ex:
            futs = [ex.submit(runner, kind, key, fn) for (kind, key, fn) in tasks]
            for fut in futs:
                kind, key, val = fut.result()
                done += 1
                if kind == "mod":
                    mod_desc[key] = val
                elif kind == "dom":
                    dom_desc[key] = val
                else:
                    feat_desc[key] = val
                if done % 5 == 0 or done == len(tasks):
                    print(f"  OLLAMA progress: {done}/{len(tasks)}")
    return mod_desc, dom_desc, feat_desc


def report(modules, domains, rbac_atoms, rbac_gated, rbac_keys, unknown_gates,
           rbac_exists, platform, violations, llm_descriptions):
    mod_desc, dom_desc, feat_desc = llm_descriptions
    NEW_MODS = discover_modules()
    L = []
    total_mod_files = sum(len(modules[m]["files"]) for m in NEW_MODS)
    total_dom_files = sum(len(domains[d]["files"]) for d in _ALL_DOMAINS)
    n_mod_active = sum(1 for m in NEW_MODS if modules[m]["status"] == "Active")
    n_dom_impl = sum(1 for d in _ALL_DOMAINS if domain_completion(domains[d])[0] == "Implemented")
    n_dom_part = sum(1 for d in _ALL_DOMAINS if domain_completion(domains[d])[0] == "Partial")
    n_atoms = len(rbac_atoms)
    n_backed = sum(1 for d in _ALL_DOMAINS for b in domains[d]["backed"] if b)
    n_gated = sum(1 for (d, key, *_rest) in rbac_atoms if key in rbac_gated)
    n_high = sum(1 for (_l, sev, *_x) in violations if sev == "HIGH")

    L.append("# ZOZI System — NEW_STRUCTURE.md Architecture & Implementation Audit")
    L.append("")
    L.append("> Generated by ``scripts/system_trackers/feature_tracking_report.py``. This audit "
             "measures the codebase **only** against the three-axis taxonomy in "
             "``documents/NEW_STRUCTURE.md``:")
    L.append(">")
    L.append("> - **Axis 1 — Module** (who acts): ``backend/modules/{m}/`` — auth + thin routers.")
    L.append("> - **Axis 2 — Domain** (what the business does): ``backend/domains/{d}/`` — "
             "services/models/schemas/policies/events/features (optionally sliced).")
    L.append("> - **Axis 3 — Feature** (what may be done): ``backend/domains/{d}/features.py`` "
             "aggregated by ``backend/rbac/catalog.py``.")
    L.append(">")
    L.append("> Content is parsed with ``ast`` (real classes/functions), and where OLLAMA was "
             "reachable the LLM wrote the detailed feature/module/domain descriptions. "
             "Violations of the seven NEW_STRUCTURE.md laws are raised as alerts.")
    L.append("")

    # ---------------- codebase content digest ----------------
    mod_classes = mod_funcs = mod_models = 0
    for m in NEW_MODS:
        for r in modules[m]["files"]:
            s = sig(os.path.join(BACKEND, r))
            mod_classes += len(s["classes"])
            mod_funcs += len(s["functions"])
            mod_models += len(s["models"])
    dom_classes = dom_funcs = dom_models = 0
    for d in _ALL_DOMAINS:
        for r in domains[d]["files"]:
            s = sig(os.path.join(BACKEND, r))
            dom_classes += len(s["classes"])
            dom_funcs += len(s["functions"])
            dom_models += len(s["models"])
    plat_files = sum(v["files"] for v in platform.values())

    L.append("## Codebase content digest")
    L.append("")
    L.append("What is actually written in the codebase (``ast``-parsed classes/functions, not "
             "folder counts):")
    L.append("")
    L.append(f"- **Modules** (access surfaces): {total_mod_files} files, {mod_classes} classes, "
             f"{mod_funcs} functions, {mod_models} ORM models.")
    L.append(f"- **Domains** (business logic): {total_dom_files} files, {dom_classes} classes, "
             f"{dom_funcs} functions, {dom_models} ORM models.")
    L.append(f"- **Platform layers** (infrastructure/kernel/providers/jobs/middleware/...): "
             f"{plat_files} files.")
    L.append(f"- **Features**: {n_atoms} atoms, {n_backed} backed, {n_gated} gated, "
             f"{len(unknown_gates)} unknown gates.")
    L.append("")
    L.append("> Read top-to-bottom: **Modules** (section 1) show the actor surfaces, "
             "**Domains** (section 2) show what each business capability actually implements, "
             "**Features** (section 3) show what may be done. **Violations** (section 6) flag "
             "anything that breaks the NEW_STRUCTURE.md shape.")
    L.append("")

    L.append("## Executive summary")
    L.append("")
    L.append(f"- **Modules (Axis 1):** {n_mod_active}/{len(NEW_MODS)} active "
             f"({total_mod_files} module files scanned).")
    L.append(f"- **Domains (Axis 2):** {len(_ALL_DOMAINS)} domains "
             f"({n_dom_impl} Implemented / {n_dom_part} Partial); {total_dom_files} domain files scanned.")
    L.append(f"- **Features (Axis 3):** {n_atoms} feature atoms defined across domains; "
             f"**{n_backed} backed** by domain code, **{n_gated} gated** by ``require_feature(...)``.")
    L.append(f"- **Feature catalog:** ``backend/rbac/catalog.py`` present = {rbac_exists}; "
             f"aggregates {n_atoms} atoms. Unknown gates (not in catalog): {len(unknown_gates)}.")
    L.append(f"- **Law violations:** {len(violations)} total, **{n_high} HIGH-severity**.")
    L.append("")
    L.append("> **Completion %** = content-present core layers "
             "(models/services/schemas/events × 20%) + features (20% only when atoms exist) + "
             "bonuses policies(+8)/subscribers(+8)/ports(+4)/read_models(+4)/repositories(+4), "
             "capped at 100. Status: Implemented ≥80 · Partial ≥45 · Scaffold <45. "
             "A layer counts as *present* only when it contains real classes/functions.")
    L.append("")

    # ===================== ARCHITECTURE AT A GLANCE =====================
    L.append("## Architecture at a glance")
    L.append("")
    L.append("The codebase follows the three orthogonal axes of ``documents/NEW_STRUCTURE.md``:")
    L.append("")
    L.append("- **Modules act** (section 1) — ``backend/modules/{m}/`` are entry points; each composes "
             "domains via thin routers. Think *who* uses the system.")
    L.append("- **Domains own** (section 2) — ``backend/domains/{d}/`` hold business logic in "
             "services / models / schemas / events / features. Each domain lists its **feature atoms** "
             "right below it. Think *what the business does*.")
    L.append("- **Features gate** (section 3) — atoms in each domain's ``features.py``, aggregated by "
             "``backend/rbac/catalog.py`` and enforced with ``require_feature(...)``. Think *what may be done*.")
    L.append("- **Kernel provides** shared business primitives (money, numbering, country, period) in "
             "``backend/kernel/`` — imported by domains, never the reverse.")
    L.append("")
    L.append("Read top-to-bottom: start at the modules to see the surfaces, drill into a domain to see "
             "its logic and the capabilities it exposes, then use the feature catalog to scan all "
             "permissions. Law violations (section 6) flag anything that breaks this shape.")
    L.append("")

    # ===================== 1. MODULES =====================
    L.append("## 1 — Modules (Axis 1: who acts)")
    L.append("")
    L.append("Modules are the system's entry points — each ``backend/modules/{m}/`` exposes thin "
             "routers and **composes** one or more domains (section 2). The indented list below shows, "
             "per module, which domains it acts on.")
    L.append("")
    L.append("### Hierarchy: Modules → Domains they compose")
    L.append("")
    for m in NEW_MODS:
        info = modules[m]
        exposed = ", ".join(info["exposed"]) if info["exposed"] else "—"
        L.append(f"- **{m}** — {MODULE_DESC.get(m, '—')}")
        L.append(f"  - status: **{info['status']}** · routers: {len(info['routers'])} · "
                 f"auth files: {len(info['auth'])} · serializers: {len(info['serializers'])}")
        L.append(content_line("router content", info["routers"]))
        L.append(content_line("auth content", info["auth"]))
        L.append(content_line("serializer content", info["serializers"]))
        L.append(f"  - composes domains: {exposed}")
        thin = len(info["routers"]) - len(info["thick_routers"])
        thin_pct = round(100 * thin / max(1, len(info["routers"])))
        L.append(f"  - feature gates wired: {len(info['gated'])} · "
                 f"thin routers: {thin}/{len(info['routers'])} ({thin_pct}%) · "
                 f"thick routers (Law 2): {len(info['thick_routers'])}")
        if info["thick_routers"]:
            for (r, notes) in info["thick_routers"][:5]:
                L.append(f"    - ⚠ {os.path.basename(r)}: {'; '.join(notes)}")
        if mod_desc.get(m):
            L.append(f"  - **LLM description:** {mod_desc[m]}")
    L.append("")

    # ===================== 2. DOMAINS + FEATURES =====================
    L.append("## 2 — Domains (Axis 2: what the business does) & Features (Axis 3: what may be done)")
    L.append("")
    L.append("Each **domain** owns a slice of business logic. Where a domain defines **feature atoms** "
             "(``backend/domains/{d}/features.py``), those atoms are listed directly under the domain "
             "so you can see *what the domain lets you do* alongside *how it is built*.")
    L.append("")
    L.append("### Hierarchy: Domain → Layers → Features")
    L.append("")
    L.append("| Domain | Status | Completion % | Models | Services | Schemas | Policies | "
             "Events | Subscribers | Features (atoms) | Ports | ReadModels | Repos |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for d in _ALL_DOMAINS:
        dom = domains[d]
        ld = dom["layer_depth"]
        status, pct, _p = domain_completion(dom)
        L.append(
            f"| {d} | {status} | {pct}% | {ld.get('models', {}).get('files', 0)} "
            f"({ld.get('models', {}).get('models', 0)} orm) | "
            f"{ld.get('services', {}).get('files', 0)} | {ld.get('schemas', {}).get('files', 0)} | "
            f"{ld.get('policies', {}).get('files', 0)} | {ld.get('events', {}).get('files', 0)} | "
            f"{ld.get('subscribers', {}).get('files', 0)} | "
            f"{ld.get('features', {}).get('files', 0)} ({len(dom['atoms'])}) | "
            f"{ld.get('ports', {}).get('files', 0)} | {ld.get('read_models', {}).get('files', 0)} | "
            f"{ld.get('repositories', {}).get('files', 0)} |")
    L.append("")
    for d in _ALL_DOMAINS:
        dom = domains[d]
        status, pct, _p = domain_completion(dom)
        L.append(f"### {d} — {status} ({pct}%)")
        L.append("")
        L.append(f"{DOMAIN_DESC.get(d, '—')}")
        if dom_desc.get(d):
            L.append("")
            L.append(f"**LLM implementation review:** {dom_desc[d]}")
        L.append("")
        for ly in LAYER_ORDER:
            fl = dom["layers"].get(ly, [])
            if not fl:
                continue
            L.append(content_line(f"{d}/{ly}", fl))
        L.append("")
        if dom["deps"]:
            L.append(f"- Cross-domain dependencies: " +
                     ", ".join(f"{k} ({v})" for k, v in
                               sorted(dom["deps"].items(), key=lambda x: -x[1])))
            L.append("")
        # ---- Features belonging to this domain (Axis 3 embedded) ----
        if not dom["atoms"]:
            L.append("- **Features:** none defined yet (`features.py` is empty).")
            L.append("")
        else:
            n_backed = sum(1 for b in dom["backed"] if b)
            n_gated = sum(1 for (key, *_r) in dom["atoms"] if key in rbac_gated)
            L.append(f"- **Features ({len(dom['atoms'])} atoms — {n_backed} backed, "
                     f"{n_gated} gated):**")
            L.append("")
            for (key, label, risk, actions, desc), b in zip(dom["atoms"], dom["backed"]):
                g = key in rbac_gated
                cap = key.split(".")[-1]
                related = [os.path.basename(r) for r in dom["files"]
                           if cap in r or cap.replace("_", "") in r.replace("_", "")]
                L.append(f"  - **{key}** — *{label or 'no label'}* "
                         f"· risk: {risk or '—'} · actions: {', '.join(actions) or '—'} "
                         f"· **{feature_status(b, g)}** "
                         f"(backed={'yes' if b else 'no'}, gated={'yes' if g else 'no'})")
                if related:
                    L.append(f"    - related files: {', '.join(related[:8])}")
                if desc:
                    L.append(f"    - provided description: {desc}")
                llm_d = feat_desc.get((d, key))
                if llm_d:
                    L.append(f"    - **LLM description:** {llm_d}")
            L.append("")

    # ===================== 3. FEATURE CATALOG (consolidated) =====================
    L.append("## 3 — Feature catalog (Axis 3: what may be done — consolidated across all domains)")
    L.append("")
    L.append("Quick reference of every feature atom in the system, grouped by domain. Full LLM "
             "descriptions and related files live under each domain in section 2; this table is for "
             "scanning capabilities at a glance.")
    L.append("")
    L.append("| Domain | Feature atom | Risk | Actions | Backed | Gated | Status |")
    L.append("| --- | --- | --- | --- | --- | --- | --- |")
    for d in _ALL_DOMAINS:
        dom = domains[d]
        if not dom["atoms"]:
            continue
        for (key, label, risk, actions, desc), b in zip(dom["atoms"], dom["backed"]):
            g = key in rbac_gated
            L.append(f"| {d} | {key} | {risk or '—'} | {', '.join(actions) or '—'} | "
                     f"{'yes' if b else 'no'} | {'yes' if g else 'no'} | {feature_status(b, g)} |")
    L.append("")

    # ===================== 4. CROSS-AXIS =====================
    L.append("## 4 — Cross-axis — Module → Domain composition")
    L.append("")
    L.append("| Module | # Domains | Domains composed |")
    L.append("| --- | --- | --- |")
    for m in NEW_MODS:
        exposed = modules[m]["exposed"]
        L.append(f"| {m} | {len(exposed)} | {', '.join(exposed) if exposed else '—'} |")
    L.append("")
    L.append("### Reverse — Domain exposed by which modules")
    L.append("")
    dom_modules = defaultdict(list)
    for m in NEW_MODS:
        for d in modules[m]["exposed"]:
            dom_modules[d].append(m)
    L.append("| Domain | Modules composing it |")
    L.append("| --- | --- |")
    for d in _ALL_DOMAINS:
        mods = dom_modules.get(d, [])
        L.append(f"| {d} | {', '.join(mods) if mods else '— (not composed by any module yet)'} |")
    L.append("")

    # ===================== 5. PLATFORM =====================
    L.append("## 5 — Platform layers (context — what else is running)")
    L.append("")
    L.append("| Layer | Files | Has __init__ |")
    L.append("| --- | --- | --- |")
    for layer, info in platform.items():
        L.append(f"| {layer} | {info['files']} | {'yes' if info['has_init'] else 'no'} |")
    L.append("")

    # ===================== 6. VIOLATIONS =====================
    L.append("## 6 — Violation register — NEW_STRUCTURE.md laws")
    L.append("")
    L.append("Every breach of the seven laws is raised here. Severity: **HIGH** blocks the target "
             "structure; **MED** risky / hard-to-verify; **INFO** by-design or not-yet-started.")
    L.append("")
    L.append("| Law | Severity | Area | Finding | Recommended action |")
    L.append("| --- | --- | --- | --- | --- |")
    order = {"HIGH": 0, "MED": 1, "INFO": 2}
    for law, sev, area, finding, action in sorted(violations, key=lambda x: order.get(x[1], 3)):
        L.append(f"| {law} | {sev} | {area} | {finding} | {action} |")
    L.append("")

    # ===================== 7. FILE INVENTORY =====================
    L.append("## 7 — File inventory (hierarchy-wise)")
    L.append("")
    L.append("Every file is grouped by its NEW_STRUCTURE.md layer so the anatomy of each "
             "module and domain is visible at a glance. Modules split into routers / auth / "
             "serializers; domains split by the layer each file implements.")
    L.append("")

    # --- Modules: files grouped by sub-layer ---
    L.append("### Modules — files by layer")
    L.append("")
    for m in NEW_MODS:
        info = modules[m]
        if not info["files"]:
            continue
        thin = len(info["routers"]) - len(info["thick_routers"])
        L.append(f"<details><summary><b>modules/{m}</b> — {len(info['files'])} files "
                 f"({len(info['routers'])} routers, {thin} thin, "
                 f"{len(info['thick_routers'])} thick, {len(info['auth'])} auth)</summary>")
        L.append("")
        groups = defaultdict(list)
        for r in info["files"]:
            if "/routers/" in r:
                groups["routers"].append(r)
            elif "/auth/" in r:
                groups["auth"].append(r)
            elif "/serializers/" in r:
                groups["serializers"].append(r)
            else:
                groups["other"].append(r)
        for sub in ("routers", "auth", "serializers", "other"):
            if not groups[sub]:
                continue
            L.append(f"**{sub}** ({len(groups[sub])}):")
            L.append("")
            L.append("```")
            L.append("\n".join(groups[sub]))
            L.append("```")
            L.append("")
        L.append("</details>")
        L.append("")

    # --- Domains: files grouped by layer ---
    L.append("### Domains — files by layer")
    L.append("")
    layer_order = ["services", "models", "schemas", "policies", "repositories",
                   "read_models", "events.py", "subscribers.py", "features.py",
                   "ports.py", "unclassified"]
    for d in _ALL_DOMAINS:
        dom = domains[d]
        if not dom["files"]:
            continue
        status, pct, _p = domain_completion(dom)
        L.append(f"<details><summary><b>domains/{d}</b> — {len(dom['files'])} files "
                 f"({status}, {pct}%, {dom['total_models']} ORM models)</summary>")
        L.append("")
        groups = defaultdict(list)
        for r in dom["files"]:
            groups[layer_of(r) or "unclassified"].append(r)
        for ly in layer_order:
            if not groups.get(ly):
                continue
            L.append(f"**{ly}** ({len(groups[ly])}):")
            L.append("")
            L.append("```")
            L.append("\n".join(groups[ly]))
            L.append("```")
            L.append("")
        L.append("</details>")
        L.append("")

    L.append("## Notes")
    L.append("")
    L.append("- Completion % and status measure implementation progress of each domain toward the "
             "layer anatomy in ``documents/NEW_STRUCTURE.md``, now verified by *content* "
             "(real classes/functions) rather than folder existence alone.")
    L.append("- \"Backed\" is a heuristic (atom capability token present in a domain file's names "
             "or body); it is a proxy for an implemented capability, not a certified test.")
    L.append("- LLM descriptions require a running OLLAMA server; without it the audit still runs "
             "and falls back to the machine-extracted signals above.")
    L.append("- Law violations are derived directly from imports and file content across the backend.")
    L.append("")
    return L


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------
def build_json(modules, domains, rbac_atoms, rbac_gated, rbac_keys, unknown_gates,
               rbac_exists, platform, violations, llm_descriptions):
    mod_desc, dom_desc, feat_desc = llm_descriptions
    atom_backed = {}
    for d in _ALL_DOMAINS:
        for (k, *_x), bk in zip(domains[d]["atoms"], domains[d]["backed"]):
            atom_backed[(d, k)] = bk
    return {
        "schema": "new_structure_audit_v2",
        "axes": {
            "modules": {
                m: {
                    "status": modules[m]["status"],
                    "routers": len(modules[m]["routers"]),
                    "auth_files": len(modules[m]["auth"]),
                    "serializers": len(modules[m]["serializers"]),
                    "exposed_domains": modules[m]["exposed"],
                    "gated_features": modules[m]["gated"],
                    "residual_imports": modules[m]["residual"],
                    "thick_routers": [os.path.basename(r) for r, _n in modules[m]["thick_routers"]],
                    "files": modules[m]["files"],
                    "llm_description": mod_desc.get(m, ""),
                } for m in discover_modules()
            },
            "domains": {
                d: {
                    "layers": {ly: domains[d]["layer_depth"].get(ly, {})
                               for ly in CORE_LAYERS + ["policies", "subscribers", "ports",
                                                         "read_models", "repositories", "features"]},
                    "features": [
                        {"key": k, "label": lb, "risk": rk, "actions": ac, "description": de,
                         "backed": bk, "gated": k in rbac_gated,
                         "status": feature_status(bk, k in rbac_gated),
                         "llm_description": feat_desc.get((d, k), "")}
                        for (k, lb, rk, ac, de), bk in zip(domains[d]["atoms"], domains[d]["backed"])
                    ],
                    "inter_domain_deps": domains[d]["deps"],
                    "cross_violations": domains[d]["cross_violations"],
                    "status": domain_completion(domains[d])[0],
                    "completion_pct": domain_completion(domains[d])[1],
                    "orm_models": domains[d]["total_models"],
                    "files": domains[d]["files"],
                    "llm_description": dom_desc.get(d, ""),
                } for d in _ALL_DOMAINS
            },
            "features": {
                "total_atoms": len(rbac_atoms),
                "backed_atoms": sum(1 for d in _ALL_DOMAINS for b in domains[d]["backed"] if b),
                "gated_atoms": sum(1 for (d, key, *_r) in rbac_atoms if key in rbac_gated),
                "unknown_gates": unknown_gates,
                "catalog_present": rbac_exists,
                "atoms": [
                    {"domain": d, "key": key, "label": lb, "risk": rk, "actions": ac,
                     "description": de, "backed": atom_backed.get((d, key), False),
                     "gated": key in rbac_gated,
                     "status": feature_status(atom_backed.get((d, key), False), key in rbac_gated),
                     "llm_description": feat_desc.get((d, key), "")}
                    for (d, key, lb, rk, ac, de) in rbac_atoms
                ],
            },
        },
        "platform_layers": platform,
        "violations": [
            {"law": law, "severity": sev, "area": area, "finding": finding, "action": action}
            for (law, sev, area, finding, action) in violations
        ],
        "cross_axis": {
            "module_exposes": {m: modules[m]["exposed"] for m in discover_modules()},
            "domain_exposed_by": {
                d: [m for m in discover_modules() if d in modules[m]["exposed"]] for d in _ALL_DOMAINS
            },
        },
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(out_dir=None, report_name="SYSTEM_TRACKING_REPORT.md",
         json_name="FEATURE_CROSS_REFERENCES.json", use_ollama=True,
         ollama_model="qwen2.5:latest", ollama_url="http://localhost:11434"):
    global _ALL_DOMAINS
    out_dir = out_dir or DOCS_AUDIT
    os.makedirs(out_dir, exist_ok=True)

    _ALL_DOMAINS = discover_domains()

    llm = Llm(base_url=ollama_url, model=ollama_model, enabled=use_ollama,
             cache_path=os.path.join(out_dir, "ollama_cache.json"))

    modules = scan_modules()
    domains = scan_domains()
    rbac_atoms, rbac_gated, rbac_keys, unknown_gates, rbac_exists = scan_rbac()
    platform = scan_platform()
    violations = detect_violations(modules, domains, rbac_atoms, unknown_gates)
    llm_descriptions = build_ollama_cache(modules, domains, rbac_atoms, rbac_gated, llm) if use_ollama else ({}, {}, {})

    report_lines = report(modules, domains, rbac_atoms, rbac_gated, rbac_keys,
                          unknown_gates, rbac_exists, platform, violations, llm_descriptions)
    json_out = build_json(modules, domains, rbac_atoms, rbac_gated, rbac_keys,
                          unknown_gates, rbac_exists, platform, violations, llm_descriptions)

    json_path = os.path.join(out_dir, json_name)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_out, f, indent=2)

    dest = os.path.join(out_dir, report_name)
    with open(dest, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    n_impl = sum(1 for d in _ALL_DOMAINS if domain_completion(domains[d])[0] == "Implemented")
    n_part = sum(1 for d in _ALL_DOMAINS if domain_completion(domains[d])[0] == "Partial")
    n_high = sum(1 for (_l, sev, *_x) in violations if sev == "HIGH")
    print(f"Wrote {dest}: modules={len(discover_modules())}, domains={len(_ALL_DOMAINS)} "
          f"({sum(len(domains[d]['files']) for d in _ALL_DOMAINS)} files), "
          f"implemented={n_impl}, partial={n_part}, atoms={len(rbac_atoms)}")
    print(f"Wrote {json_path}: schema=new_structure_audit_v2, "
          f"violations={len(violations)} (HIGH={n_high}), ollama={'on:'+ollama_model if use_ollama else 'off'}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(
        description="Generate the ZOZI NEW_STRUCTURE.md architecture & implementation audit.")
    ap.add_argument("--backend", default=BACKEND, help="Backend source dir")
    ap.add_argument("--out-dir", default=DOCS_AUDIT, help="Output dir for report + json")
    ap.add_argument("--report-name", default="SYSTEM_TRACKING_REPORT.md")
    ap.add_argument("--json-name", default="FEATURE_CROSS_REFERENCES.json")
    ap.add_argument("--no-ollama", action="store_true", help="Disable OLLAMA (use heuristics only)")
    ap.add_argument("--ollama-model", default="qwen2.5:latest", help="OLLAMA model name")
    ap.add_argument("--ollama-url", default="http://localhost:11434", help="OLLAMA base URL")
    args = ap.parse_args()
    BACKEND = args.backend
    main(args.out_dir, args.report_name, args.json_name,
         use_ollama=not args.no_ollama,
         ollama_model=args.ollama_model, ollama_url=args.ollama_url)
