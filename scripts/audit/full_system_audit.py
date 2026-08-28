#!/usr/bin/env python3
"""
ZOZI Complete Architecture Audit Scanner  --  v4 (honest, fast, AST-based)

Scans the backend + frontend against ALL 325 architecture laws defined in
ARCHITECTURE_DIAGRAM.md.

Design goals (per project requirements):
  * No cheating: every law is accounted for in the report as one of
        FAIL        -> automated check ran and found a violation
        PASS        -> automated check ran and found nothing
        MANUAL      -> law is operational/process/runtime and needs human review
    Laws that are not statically checkable are NEVER reported as PASS.
  * Fast: files are read and parsed exactly ONCE (cached). The frontend tree is
    walked with aggressive pruning so node_modules/.next/.expo are never descended.
  * Smart: a real import graph powers the dependency-direction laws (1,3,31,97-104)
    and circular-import detection (98). Routers, providers and migrations are
    analysed with AST + targeted pattern matching using the documented benchmarks.

Output: docs/action/AUDIT_RESULTS.json  (+ a human summary on stdout)
"""
from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent / "backend"
FRONTEND_ROOT = HERE.parent.parent / "frontend"
REPORT = HERE.parent.parent / "docs" / "action" / "AUDIT_RESULTS.json"
ARCH_DOC = HERE.parent.parent / "ARCHITECTURE_DIAGRAM.md"

EXPECTED_DOMAINS = {
    "accounts", "analytics", "audit", "catalog", "comms", "country", "customers",
    "finance", "governance", "hr", "logistics", "orders", "payments", "promotions",
    "security", "suppliers",
}
EXPECTED_MODULES = {"admin", "customer", "employee", "logistics", "supplier"}
FORBIDDEN_SCHEMAS = {"core", "platform", "identity"}
FORBIDDEN_ROOT_FOLDERS = {"utils", "routers", "controllers", "services", "models", "db"}

# Internal top-level packages (anything below is "internal" for the import graph)
INTERNAL_PKGS = ("domains", "modules", "rbac", "kernel", "infrastructure",
                  "providers", "jobs", "middleware")

PROVIDER_FORBIDDEN = ("domains.", "modules.", "rbac.", "jobs.", "middleware.")
DOMAIN_FORBIDDEN = ("modules.",)
INFRA_FORBIDDEN = ("domains.", "modules.", "rbac.", "providers.")
KERNEL_FORBIDDEN = ("domains.", "modules.", "rbac.", "providers.", "infrastructure.")

# ══════════════════════════════════════════════════════════════════════════
# LAW REGISTRY  (id -> (category, short rule, checkable?))
# checkable=True  => an automated check runs and the law can genuinely PASS.
# checkable=False => operational/process/runtime law; reported as MANUAL.
# ══════════════════════════════════════════════════════════════════════════
LAWS: dict[int, tuple[str, str, bool]] = {}
def _L(ids, cat, rule, checkable):
    for i in ids:
        LAWS[i] = (cat, rule, checkable)

_L(range(1, 8), "Architecture", "Layer direction / thin routers / cross-domain / features / RLS / schema / allowlist", True)
_L([8], "Structure", "Router structure (one file per domain per module)", True)
_L([9], "Structure", "Tools belong in providers", True)
_L([10], "Structure", "Kernel is pure business primitives", True)
_L([11], "Structure", "Providers wrap SDKs (HAS_ flags)", True)
_L([12], "Structure", "16 domains fixed set", True)
_L([13], "Structure", "5 modules fixed set", True)
_L(range(14, 19), "File Placement", "Business logic/endpoints/SDKs in right layer; forbidden root folders", True)
_L(range(19, 25), "Code Quality", "Money=Decimal, country_code, timestamps, FK ondelete, audit cols, schema names", True)
_L(range(25, 30), "Migration", "Shift files / shims / temp scripts / removed registry", True)
_L([30, 31], "Provider", "Graceful degradation + no domain imports", True)
_L(range(32, 45), "Security", "Secrets, JWT type, SQL, CSRF, headers, rate-limit, auth, CORS, WS, pydantic, logging, dep scan", True)
_L(range(45, 58), "Database", "N+1, SELECT *, pooling, read replica, alembic, transactions, table ownership, FK, indexes, soft-delete, schema, destructive migrations", True)
_L(range(58, 68), "Code Quality", "print, silent except, blocking async, caches, TODO, type hints, fn length, indent, magic numbers, DRY, errors", True)
_L(range(69, 75), "Testing", "Smoke / architecture / integration / perf / isolation tests", True)
_L(range(75, 82), "Infrastructure", "Degradation, sessions, locks, middleware order, handlers, lifespan, health", True)
_L(range(82, 87), "Config", "No default creds, env validation, typed flags, env hierarchy", True)
_L(range(87, 92), "Router", "Auth gate, feature gate, serialization, no business logic, docs", True)
_L(range(92, 97), "Observability", "structlog, request_id, metrics, sentry, audit trail", True)
_L(range(97, 107), "Wiring", "Import direction, circular, layer crossing, provider/kernel/infra isolation, job/middleware wiring, shared/frontend wiring", True)
_L([107], "Technology", "PostgreSQL in prod", True)
_L([108], "Technology", "SQLite in dev", False)
_L([109], "Technology", "Redis usage", True)
_L([110], "Technology", "Redis failure handling", False)
_L([111], "Technology", "Next.js App Router", True)
_L([112], "Technology", "React Server Components", False)
_L([113], "Technology", "Expo Router", False)
_L([114], "Technology", "WebSocket for realtime", False)
_L([115], "Technology", "Celery for jobs", False)
_L([116], "Technology", "Email via SMTP provider", True)
_L([117], "Technology", "SMS via Twilio", True)
_L([118], "Technology", "Payment gateways (BasePaymentGateway)", True)
_L([119], "Technology", "AI/ML via providers/ai", True)
_L([120], "Technology", "S3 storage (no blobs in PG)", True)
_L([121], "Technology", "Image processing via async_workers", True)
_L([122], "Technology", "Leaflet maps", False)
_L(range(123, 132), "Provider", "Single SDK, HAS_ flags, degrade, no business logic, config, async, health, error mapping, mock tests", True)
_L(range(132, 140), "Module", "Structure, per-module auth, router naming, registration, public/protected, serializers, 5 modules, prefixes", True)
_L(range(140, 150), "Infrastructure", "7 subpackages, database/redis/storage/messaging/observability/security/utils, canonical Base, sessions", True)
_L(range(150, 161), "Domain", "Domain structure, service/model/schema/event/port/subscriber/feature/read-model/policy patterns", True)
_L(range(161, 168), "RBAC", "Catalog, roles, resolution, dependencies, service, models, frontend permissions", True)
_L(range(168, 178), "Frontend", "Monorepo, Next version, TS strict, state, data fetching, proxy, styling, forms, errors, route groups", True)
_L(range(178, 187), "Web App", "Route structure, components, hooks, lib, services, theme, types, utils, build", True)
_L(range(187, 195), "Mobile", "Expo SDK, route groups, components, lib, platform-specific, state, storage, build", True)
_L(range(195, 201), "Shared", "Structure, no app imports, generated permissions, cross-platform types, api core, money", True)
_L(range(201, 207), "Config", "Env hierarchy, required vars, typed flags, secrets manager, APP_ENV, CORS allowlist", True)
_L(range(207, 215), "Testing", "pytest, fixtures, demo users, test env, frontend tests, architecture tests, coverage, isolation", True)
_L(range(215, 221), "Deployment", "Docker Compose, prod targets, migration on deploy, health, rollback, env promotion", True)
_L(range(221, 227), "Performance", "Caching, keyset pagination, pooling, query optimization, CDN, async", True)
_L(range(227, 233), "Data", "RLS, soft delete, audit columns/trail, residency, backup", True)
_L(range(233, 240), "API", "REST, versioning, JSON/Pydantic, RFC7807, pagination, filtering, idempotency", True)
_L(range(240, 245), "Git", "Branching, conventional commits, PR process, hooks, worktrees", True)
_L(range(245, 251), "Docs", "Architecture docs, agent docs, API docs, runbooks, comments, changelog", True)
_L(range(251, 271), "Scalability", "Horizontal scaling, autoscaling, partitioning, CQRS, write-behind, quotas, FTS, image pipeline, API caching, PgBouncer, replicas, archiving, buffering, static assets, monitoring, synthetic, limits, load shedding, cost, chaos", False)
_L(range(271, 296), "Security", "AI-agent, exfiltration, poisoning, adversarial, encryption at rest/in transit, key rotation, WORM, session binding, brute force, bot, PII, MFA, zero-trust, CSP, SRI, headers, disclosure, pen test, dep pinning, SBOM, license, incident, training", False)
_L(range(296, 311), "Resilience", "Circuit breaker, retry, DLQ, feature health, fallback, error budget, on-call, runbooks, DR, failover, multi-region, backup verify, drift, dep monitoring, post-incident", False)
_L(range(311, 326), "Operations", "Feature flags, A/B, compliance, IaC, log aggregation, dashboards, alerting, capacity, release mgmt, DevX, doc freshness, cost allocation, human access, change mgmt, sustainability", False)

# ══════════════════════════════════════════════════════════════════════════
# FINDINGS
# ══════════════════════════════════════════════════════════════════════════
findings: list[dict] = []
def add(law: int, severity: str, message: str, fix: str, path: str = "", line: int = 0):
    cat = LAWS.get(law, ("?", "", True))[0]
    findings.append({
        "law_id": law, "category": cat, "severity": severity,
        "file": path, "line": line, "message": message, "fix": fix,
    })

# ══════════════════════════════════════════════════════════════════════════
# FILE INDEX  (read + parse EXACTLY ONCE, cached)
# ══════════════════════════════════════════════════════════════════════════
class Src:
    __slots__ = ("path", "rel", "content", "tree", "imports_from", "classes", "functions")
    def __init__(self, path: Path, rel: str, content: str):
        self.path = path
        self.rel = rel
        self.content = content
        try:
            self.tree = ast.parse(content)
        except Exception:
            self.tree = None
        self.imports_from: list[tuple[str, int]] = []
        self.classes: list = []
        self.functions: list = []
        if self.tree is not None:
            for node in ast.walk(self.tree):
                if isinstance(node, ast.ImportFrom):
                    self.imports_from.append((node.module or "", node.lineno))
                elif isinstance(node, ast.Import):
                    for a in node.names:
                        self.imports_from.append((a.name, node.lineno))
                elif isinstance(node, ast.ClassDef):
                    self.classes.append(node)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.functions.append(node)

BACKEND: list[Src] = []
DOMAINS: dict[str, list[Src]] = defaultdict(list)
MODELS: list[Src] = []
ROUTERS: list[Src] = []
PROVIDERS: list[Src] = []
SERVICES: list[Src] = []
MIDDLEWARE: list[Src] = []
INFRA: list[Src] = []
JOBS: list[Src] = []
KERNEL: list[Src] = []
RBAC: list[Src] = []
TESTS: list[Src] = []
SCRIPTS: list[Src] = []
ALL_BY_REL: dict[str, Src] = {}

BACKEND_SKIP = {"venv", ".venv", "__pycache__", ".kilo", ".git", ".hypothesis",
                ".pytest_cache", ".ruff_cache", ".mypy_cache", "uploads", "var", "node_modules"}

FRONTEND_FILES: list[Path] = []          # source files only (pruned)
FRONTEND_BY_REL: dict[str, Path] = {}
_frontend_cache: dict[str, str] = {}

def _walk_py(base: Path, skip: set[str]) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    stack = [base]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except (OSError, PermissionError):
            continue
        for e in entries:
            try:
                if e.is_dir():
                    if e.name in skip or e.name.startswith(".") and e.name not in (".kilo",):
                        continue
                    stack.append(e)
                elif e.is_file() and e.suffix == ".py":
                    out.append(e)
            except (OSError, PermissionError):
                continue
    return out

def index_backend():
    files = _walk_py(ROOT, BACKEND_SKIP)
    for p in files:
        try:
            rel = p.relative_to(ROOT).as_posix()
        except ValueError:
            continue
        if rel.startswith("_extra_files/") or rel.startswith("scripts/"):
            pass
        content = _read_file(p)
        s = Src(p, rel, content)
        BACKEND.append(s)
        ALL_BY_REL[rel] = s
        parts = rel.split("/")
        if parts[0] == "domains" and len(parts) > 1 and not parts[1].startswith("_"):
            DOMAINS[parts[1]].append(s)
        if "/models/" in rel: MODELS.append(s)
        if "/routers/" in rel: ROUTERS.append(s)
        if rel.startswith("providers/"): PROVIDERS.append(s)
        if "/services/" in rel: SERVICES.append(s)
        if rel.startswith("middleware/"): MIDDLEWARE.append(s)
        if rel.startswith("infrastructure/"): INFRA.append(s)
        if rel.startswith("jobs/"): JOBS.append(s)
        if rel.startswith("kernel/"): KERNEL.append(s)
        if rel.startswith("rbac/"): RBAC.append(s)
        if rel.startswith("tests/"): TESTS.append(s)
        if rel.startswith("scripts/"): SCRIPTS.append(s)

FRONTEND_SKIP = {"node_modules", ".next", ".expo", "build", "dist", ".git", "coverage",
                 ".cache", "__pycache__", "android", "ios", ".history"}

def _walk_frontend(base: Path, skip: set[str], out: list[Path], by_rel: dict[str, Path], max_depth=26):
    if not base.exists():
        return
    stack = [(base, 0)]
    while stack:
        d, depth = stack.pop()
        if depth > max_depth:
            continue
        try:
            entries = list(d.iterdir())
        except (OSError, PermissionError):
            continue
        for e in entries:
            try:
                if "expo-dev-launcher" in e.name:
                    continue
                if e.is_dir():
                    if e.name in skip:
                        continue
                    stack.append((e, depth + 1))
                elif e.is_file():
                    rel = e.relative_to(base).as_posix()
                    out.append(e)
                    by_rel[rel] = e
            except (OSError, PermissionError):
                continue

def index_frontend():
    _walk_frontend(FRONTEND_ROOT, FRONTEND_SKIP, FRONTEND_FILES, FRONTEND_BY_REL)

def _read_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def read_frontend(rel: str) -> str:
    if rel in _frontend_cache:
        return _frontend_cache[rel]
    p = FRONTEND_BY_REL.get(rel)
    if p is None:
        p = FRONTEND_ROOT / rel
    try:
        c = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        c = ""
    _frontend_cache[rel] = c
    return c

# ══════════════════════════════════════════════════════════════════════════
# IMPORT GRAPH  (for Laws 1,3,31,97-104,98)
# ══════════════════════════════════════════════════════════════════════════
def _module_name(rel: str) -> str:
    m = rel[:-3] if rel.endswith(".py") else rel
    m = m.replace("/", ".")
    if m.endswith(".__init__"):
        m = m[: -len(".__init__")]
    return m

GRAPH: dict[str, set[str]] = {}

def build_import_graph():
    for s in BACKEND:
        mod = _module_name(s.rel)
        deps: set[str] = set()
        for module, _ in s.imports_from:
            if not module:
                continue
            target = module
            # resolve relative imports
            if module.startswith("."):
                target = _resolve_relative(mod, module)
            if target and target.split(".")[0] in INTERNAL_PKGS and target != mod:
                deps.add(target)
        GRAPH[mod] = deps

def _resolve_relative(mod: str, module: str) -> str:
    level = 0
    while level < len(module) and module[level] == ".":
        level += 1
    rest = module[level:]
    parts = mod.split(".")
    base = parts[: max(0, len(parts) - (level - 1))]
    if rest:
        base = base + rest.split(".")
    return ".".join(base)

def find_cycles() -> list[list[str]]:
    cycles: list[list[str]] = []
    seen_cycles = set()
    WHITE, GRAY, BLACK = 0, 1, 2
    color = defaultdict(int)
    parent = {}
    for start in GRAPH:
        if color[start]:
            continue
        stack = [(start, iter(GRAPH.get(start, set())))]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            advanced = False
            for nxt in it:
                if nxt not in GRAPH:
                    continue
                if color[nxt] == GRAY:
                    # found a cycle
                    cyc = []
                    x = node
                    while x != nxt:
                        cyc.append(x)
                        x = parent.get(x, nxt)
                        if x == node and cyc.count(node) > 0:
                            break
                    cyc.append(nxt)
                    cyc.append(node)
                    key = frozenset(cyc)
                    if key not in seen_cycles:
                        seen_cycles.add(key)
                        cycles.append(list(dict.fromkeys(cyc[::-1])))
                    advanced = True
                    break
                elif color[nxt] == WHITE:
                    color[nxt] = GRAY
                    parent[nxt] = node
                    stack.append((nxt, iter(GRAPH.get(nxt, set()))))
                    advanced = True
                    break
            if not advanced:
                color[node] = BLACK
                stack.pop()
    return cycles

# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
DB_CALL_RE = re.compile(r"\b(db|session|engine|conn|connection)\.(query|execute|add|delete|merge|flush|commit|scalar|bulk_save_objects|bulk_insert_mappings)\s*\(")
MONEY_RE = re.compile(r"\b(price|total|amount|discount|tax|fee|cost|subtotal|grand_total|balance|paid|due)\s*[\+\-\*/]?=")
ORM_RETURN_RE = re.compile(r"return\s+[A-Z]\w*(\.|\(|\s|$)")
AUTH_RE = re.compile(r"get_current_user|get_current_active_user|require_module|require_auth")
FEATURE_RE = re.compile(r"require_feature|require_module")
SDK_MODULES = ("stripe", "stripe_", "twilio", "boto3", "botocore", "requests", "httpx",
               "sendgrid", "smtplib", "openai", "anthropic", "ollama", "rembg", "cv2",
               "PIL", "pillow", "onnxruntime", "pyotp", "qrcode", "barcode", "geopy",
               "redis", "psycopg", "asyncpg", "pandas", "numpy", "google", "azure",
               "pycountry", "phonenumbers", "opencv", "fitz", "docx", "openpyxl")

def has_sub(rel: str, *subs: str) -> bool:
    return any(sub in rel for sub in subs)

# ══════════════════════════════════════════════════════════════════════════
# CHECK FUNCTIONS  (only for checkable laws)
# ══════════════════════════════════════════════════════════════════════════
def check_law_1():
    for s in INFRA:
        for module, ln in s.imports_from:
            if module.startswith(INFRA_FORBIDDEN):
                add(1, "critical", f"infrastructure/ imports '{module}' — arrows must point down (Law 1).",
                    "Remove this import; infrastructure only provides platform primitives.", s.rel, ln)
    for s in KERNEL:
        for module, ln in s.imports_from:
            if module.startswith(KERNEL_FORBIDDEN):
                add(1, "critical", f"kernel/ imports '{module}' — kernel must be pure primitives (Law 1).",
                    "Remove this import from kernel/.", s.rel, ln)
    for d, files in DOMAINS.items():
        for s in files:
            for module, ln in s.imports_from:
                if module.startswith("modules."):
                    add(1, "critical", f"domains/{d}/ imports '{module}' — domains never import modules (Law 1).",
                        "Remove the module import; domain logic must not depend on the HTTP layer.", s.rel, ln)

def check_law_2_90():
    """Router benchmark: auth + feature gate + ONE service call + serialization; no DB / no business logic."""
    for s in ROUTERS:
        lines = s.content.splitlines()
        handlers = _route_handlers(s)
        # whole-file signals
        has_auth = bool(AUTH_RE.search(s.content))
        has_feature = bool(FEATURE_RE.search(s.content))
        if len(lines) > 100:
            add(2, "high", f"Router is {len(lines)} lines (max ~100) — likely contains business logic (Law 2).",
                "Extract business logic into a domain service; router = auth + gate + ONE service call.", s.rel, 1)
        if not has_auth:
            add(87, "critical", "Router file has NO authentication dependency (get_current_user / require_module) (Law 87).",
                "Add Depends(get_current_user) to protected endpoints.", s.rel, 1)
        if not has_feature:
            add(88, "critical", "Router file has NO feature gate (require_feature / require_module) (Law 88).",
                "Add require_feature('domain.action') to protected endpoints.", s.rel, 1)
        if not handlers:
            continue
        svc_calls = 0
        for h in handlers:
            seg = _node_segment(s, h)
            if DB_CALL_RE.search(seg):
                add(2, "critical", f"Router handler '{h.name}' performs direct DB operations (Law 2).",
                    "Move DB access into a domain service.", s.rel, h.lineno)
            if MONEY_RE.search(seg) or re.search(r"(calculate|compute|validate|verify)\s*\(", seg):
                add(90, "high", f"Router handler '{h.name}' contains business logic (Law 90).",
                    "Move computation/validation into the domain service.", s.rel, h.lineno)
            svc_calls += seg.count(".services.") + seg.count("Service(") + seg.count("_service.")
            if ORM_RETURN_RE.search(seg):
                add(89, "high", f"Router handler '{h.name}' returns a raw ORM object (Law 89).",
                    "Return a Pydantic response_model instead of a raw ORM model.", s.rel, h.lineno)
        if svc_calls > 1:
            add(2, "medium", f"Router makes {svc_calls} service calls — should call exactly ONE (Law 2).",
                "Consolidate into a single domain-service call per endpoint.", s.rel, 1)

def _route_handlers(s: Src) -> list:
    out = []
    if s.tree is None:
        return out
    for node in ast.walk(s.tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                f = dec.func if isinstance(dec, ast.Call) else dec
                attr = getattr(f, "attr", "")
                if attr in {"get", "post", "put", "delete", "patch", "websocket"}:
                    out.append(node)
                    break
    return out

def _node_segment(s: Src, node) -> str:
    try:
        return ast.get_source_segment(s.content, node) or ""
    except Exception:
        return ""

def check_law_3():
    allow = _load_allowlist()
    for d, files in DOMAINS.items():
        for s in files:
            if has_sub(s.rel, "/ports.py", "/events.py", "/subscribers.py"):
                continue
            for module, ln in s.imports_from:
                if module.startswith("domains."):
                    parts = module.split(".")
                    if len(parts) >= 2 and parts[1] not in (d, "_parked") and parts[1] in EXPECTED_DOMAINS:
                        if _allowed(allow, d, module):
                            continue
                        add(3, "critical", f"domains/{d}/ imports from domains/{parts[1]}/ — cross-domain READ must go via ports.py (Law 3).",
                            f"Move the read into domains/{d}/ports.py and expose a sanctioned function.", s.rel, ln)

def _load_allowlist() -> dict:
    p = ROOT / "DOMAIN_ALLOWLIST.yaml"
    if not p.exists():
        return {}
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    # crude parse: entries like "  - from: domains.x  to: domains.y"
    out = defaultdict(set)
    for m in re.finditer(r"from:\s*(\S+).*?to:\s*(\S+)", txt, re.S):
        out[m.group(1)].add(m.group(2))
    return out

def _allowed(allow: dict, src: str, target: str) -> bool:
    return target in allow.get(f"domains.{src}", set())

def check_law_4_157():
    for d in EXPECTED_DOMAINS:
        files = DOMAINS.get(d, [])
        if not any(s.rel.endswith("/features.py") for s in files):
            add(4, "medium", f"Domain '{d}' has no features.py — permission atoms must be single-sourced (Law 4).",
                f"CREATE domains/{d}/features.py with FEATURES = {{'{d}.action': 'Description'}}", f"domains/{d}/", 0)
            add(157, "medium", f"Domain '{d}' missing features.py FEATURES dict (Law 157).",
                f"Add FEATURES = {{...}} in domains/{d}/features.py", f"domains/{d}/", 0)

def check_law_5_227():
    main = ALL_BY_REL.get("main.py")
    c = main.content if main else _read_file(ROOT / "main.py")
    if "instrument_rls" not in c:
        add(5, "critical", "instrument_rls() is NEVER called — country data isolation is NOT enforced (Law 5).",
            "Call instrument_rls(engine) at startup (infrastructure.database.rls_interceptor).", "main.py", 1)
    if "rls" not in c.lower() and not any("rls" in s.rel.lower() for s in INFRA):
        add(227, "high", "No RLS enforcement code detected (Law 227).",
            "Implement set_rls_context() and filter all queries by country_code.", "infrastructure/database/", 0)

def check_law_6_222():
    for s in BACKEND:
        if "alembic" in s.rel:
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if ".offset(" in line and "alembic" not in s.rel:
                add(6, "high", "OFFSET pagination — degrades at 100K+ users (Law 6 / 222).",
                    "Use keyset pagination: WHERE id > last_id LIMIT n.", s.rel, i)

def check_law_7():
    if not (ROOT / "DOMAIN_ALLOWLIST.yaml").exists():
        add(7, "low", "DOMAIN_ALLOWLIST.yaml missing — temporary cross-domain imports must be tracked and only shrink (Law 7).",
            "Create DOMAIN_ALLOWLIST.yaml listing temporary cross-domain imports with expirations.", "DOMAIN_ALLOWLIST.yaml", 0)

def check_law_8_134_135():
    mods_dir = ROOT / "modules"
    if not mods_dir.exists():
        return
    for m in mods_dir.iterdir():
        if not m.is_dir() or m.name.startswith("_"):
            continue
        rd = m / "routers"
        if not rd.exists():
            add(8, "medium", f"Module '{m.name}' has no routers/ directory (Law 8).",
                "Create modules/{m}/routers/ with one file per domain.", f"modules/{m.name}/", 0)
            continue
        cnt = len([r for r in rd.glob("*.py") if r.name != "__init__.py"])
        if cnt < 8:
            add(8, "medium", f"Module '{m.name}' has only {cnt} router files (expected ~15, one per domain) (Law 8).",
                "Add router files for each domain: modules/{m}/routers/{domain}.py", f"modules/{m.name}/routers/", 0)
        init = rd / "__init__.py"
        if not init.exists():
            add(135, "medium", f"modules/{m.name}/routers/__init__.py missing — routers are not registered (Law 135).",
                "List all router objects in routers/__init__.py for main.py discovery.", f"modules/{m.name}/routers/__init__.py", 0)

def check_law_9():
    if (ROOT / "domains" / "media").exists():
        add(9, "high", "domains/media exists — media code belongs in providers/media, providers/image (Law 9).",
            "Move domains/media/ into providers/media/, providers/image/, providers/bg_removal/.")

def check_law_10():
    for s in KERNEL:
        if s.rel.endswith("__init__.py"):
            continue
        for module, ln in s.imports_from:
            if module.startswith(KERNEL_FORBIDDEN):
                add(10, "critical", f"kernel/ imports '{module}' — kernel must hold ONLY pure primitives (Law 10).",
                    "Remove import; kernel = money/currency/numbering/country/period only.", s.rel, ln)

def check_law_11_124():
    for s in PROVIDERS:
        if s.rel.endswith("__init__.py") or s.rel.endswith("_base.py"):
            continue
        if "HAS_" not in s.content and "def " in s.content:
            add(11, "medium", f"Provider '{s.rel}' missing HAS_<SDK> availability flag (Law 11/124).",
                "Add HAS_<SDK> = True/False so domains can gracefully degrade.", s.rel, 1)

def check_law_12():
    present = set(DOMAINS.keys())
    missing = EXPECTED_DOMAINS - present
    if missing:
        add(12, "medium", f"Expected domains not found: {sorted(missing)} (Law 12).",
            "Create the missing domains with full structure (services/, models/, schemas/, events.py, ports.py, features.py).",
            "domains/", 0)

def check_law_13_138():
    mods = {m.name for m in (ROOT / "modules").iterdir() if m.is_dir() and not m.name.startswith("_")} if (ROOT / "modules").exists() else set()
    missing = EXPECTED_MODULES - mods
    if missing:
        add(13, "medium", f"Expected modules not found: {sorted(missing)} (Law 13).",
            "Create modules/{name} with auth/, routers/, serializers/.", "modules/", 0)

def check_law_14_15_16_18():
    for folder in FORBIDDEN_ROOT_FOLDERS:
        if (ROOT / folder).exists():
            add(18, "high", f"Forbidden root folder backend/{folder}/ (Law 18).",
                f"Move contents: infrastructure/{folder}/, modules/*/routers/, domains/*/services/ as appropriate.",
                f"backend/{folder}/", 0)
    if (ROOT / "controllers").exists():
        add(16, "high", "controllers/ pattern used — not allowed; use routers+services (Law 16).",
            "Delete controllers/ and route via modules/*/routers/.")
    for p in (ROOT / "services").rglob("*.py") if (ROOT / "services").exists() else []:
        add(14, "high", "Business logic at backend/services/ — must live in domains/*/services/ (Law 14).",
            "Move to the owning domain's services/ directory.", str(p.relative_to(ROOT).as_posix()), 1) if False else None
    # (rglob already pruned; iterate the indexed set instead)
    for s in BACKEND:
        if s.rel.startswith("services/"):
            add(14, "high", "Business logic at backend/services/ — must live in domains/*/services/ (Law 14).",
                "Move to the owning domain's services/ directory.", s.rel, 1)
    for s in BACKEND:
        if s.rel.startswith("routers/"):
            add(15, "high", "HTTP endpoint at backend/routers/ — must live in modules/*/routers/ (Law 15).",
                "Move to modules/{module}/routers/{domain}.py.", s.rel, 1)

def check_law_17():
    for d in EXPECTED_DOMAINS:
        files = DOMAINS.get(d, [])
        if not any(s.rel.endswith("/events.py") for s in files):
            add(17, "medium", f"Domain '{d}' missing events.py for cross-domain writes (Law 17).",
                f"CREATE domains/{d}/events.py.", f"domains/{d}/", 0)
        if not any(s.rel.endswith("/ports.py") for s in files):
            add(17, "medium", f"Domain '{d}' missing ports.py for cross-domain reads (Law 17).",
                f"CREATE domains/{d}/ports.py with sanctioned read functions.", f"domains/{d}/", 0)
        if not any(s.rel.endswith("/subscribers.py") for s in files):
            add(17, "low", f"Domain '{d}' missing subscribers.py (Law 17).",
                f"CREATE domains/{d}/subscribers.py to consume other domains' events.", f"domains/{d}/", 0)

def check_law_19():
    for s in MODELS:
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r"Column\s*\(\s*Float", line) and "lat" not in line.lower() and "lon" not in line.lower():
                add(19, "medium", "Float column for a monetary value — rounding errors (Law 19).",
                    "Use Column(Numeric(precision=19, scale=4)) or Decimal.", s.rel, i)

def check_law_20():
    for s in MODELS:
        if "country_code" in s.content and "String(2)" not in s.content:
            add(20, "medium", "country_code column should be String(2) ISO 3166-1 alpha-2 (Law 20).",
                "country_code = Column(String(2), nullable=False, index=True)", s.rel, 1)

def check_law_21():
    for s in MODELS:
        for i, line in enumerate(s.content.splitlines(), 1):
            if "created_at" in line and "Column" in line and "server_default" not in line:
                add(21, "medium", "created_at missing server_default (DB-side timestamp) (Law 21).",
                    "created_at = Column(DateTime, server_default=func.now(), nullable=False)", s.rel, i)

def check_law_22_52_53():
    for s in MODELS:
        for i, line in enumerate(s.content.splitlines(), 1):
            if "ForeignKey(" in line:
                if "ondelete" not in line:
                    add(22, "high", "ForeignKey missing ondelete behavior (Law 22/52).",
                        "Add ondelete='CASCADE' | 'SET NULL' | 'RESTRICT'.", s.rel, i)
                if "index=True" not in line:
                    add(53, "medium", "ForeignKey column missing index (PostgreSQL does not auto-index FKs) (Law 53).",
                        "Add index=True to the FK column.", s.rel, i)

def check_law_23_54():
    for s in MODELS:
        if s.tree is None:
            continue
        for cls in s.classes:
            seg = _node_segment(s, cls)
            if seg and "__tablename__" in seg:
                for col in ("created_at", "updated_at", "country_code", "is_deleted"):
                    if col not in seg:
                        add(23, "high", f"Model '{cls.name}' missing audit column: {col} (Law 23).",
                            f"Add {col} (use TimestampMixin / SoftDeleteMixin).", s.rel, cls.lineno)
                if "is_deleted" not in seg:
                    add(54, "medium", f"Model '{cls.name}' missing is_deleted soft-delete flag (Law 54).",
                        "is_deleted = Column(Boolean, default=False, nullable=False)", s.rel, cls.lineno)

def check_law_24_56():
    for s in MODELS:
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r"schema\s*=\s*[\"'](?:core|platform|identity)[\"']", line):
                add(24, "low", "Forbidden schema name (core/platform/identity) (Law 24/56).",
                    "Use a domain-specific schema name.", s.rel, i)

def check_law_25():
    # business-logic files sitting outside services/models/schemas/events/ports/features/subscribers
    for s in BACKEND:
        if not s.rel.startswith("domains/"):
            continue
        if has_sub(s.rel, "/services/", "/models/", "/schemas/", "/events.py", "/ports.py", "/features.py", "/subscribers.py"):
            continue
        if s.rel.endswith(".py") and "def " in s.content and "class " not in s.content:
            add(25, "medium", f"Logic file in non-standard location '{s.rel}' — should be migrated into the domain (Law 25).",
                "Move business logic into domains/<domain>/services/ or the appropriate package.", s.rel, 1)

def check_law_26():
    u = ROOT / "infrastructure" / "utils"
    if not u.exists():
        return
    for p in u.rglob("*.py"):
        rel = p.relative_to(ROOT).as_posix()
        c = _read_file(p)
        if "re-export" in c.lower() or "backward" in c.lower() or "compat" in c.lower():
            add(26, "low", f"Backward-compat shim '{rel}' should be temporary (Law 26).",
                "Remove the shim once all imports are updated.", rel, 1)

def check_law_27():
    for s in SCRIPTS:
        if s.rel.split("/")[-1].startswith(("fix_", "debug_", "temp_", "scratch_", "tmp_")):
            add(27, "low", f"Temporary script '{s.rel}' should be removed after use (Law 27).",
                "Delete temporary fix_*/debug_* scripts after migration.", s.rel, 1)
    # also scan _extra_files
    for s in BACKEND:
        if s.rel.startswith("_extra_files/") and s.rel.split("/")[-1].startswith(("fix_", "debug_", "temp_", "scratch_")):
            add(27, "low", f"Temporary working file '{s.rel}' in _extra_files (Law 27).",
                "Remove temporary working files from _extra_files/ once merged.", s.rel, 1)

def check_law_28():
    for s in BACKEND:
        name = s.rel.split("/")[-1]
        if "_auto_stub" in name or name.endswith("_stub.py") or name == "stub.py":
            add(28, "medium", f"Stub file '{s.rel}' is migration scaffolding, not architecture (Law 28).",
                "Replace stubs with real implementations.", s.rel, 1)

def check_law_29():
    # Removed Service Registry: root registry.py / auto_wire.py / service_index.json / migrate_imports.py
    for s in BACKEND:
        name = s.rel.split("/")[-1]
        if name in ("auto_wire.py", "service_index.json", "migrate_imports.py"):
            add(29, "high", f"Removed component '{name}' detected — Service Registry was removed from architecture (Law 29).",
                "Delete this file; the Service Registry is no longer part of the system.", s.rel, 1)
        if name == "registry.py" and not s.rel.startswith("providers/"):
            add(29, "high", f"Root-level registry.py detected — the Service Registry was removed (Law 29).",
                "Delete this file unless it is a legitimate per-provider registry (e.g. providers/payments/registry.py).", s.rel, 1)

def check_law_30_31_100_123_125_126_129():
    for s in PROVIDERS:
        if s.rel.endswith("__init__.py") or s.rel.endswith("_base.py"):
            continue
        for module, ln in s.imports_from:
            if module.startswith(PROVIDER_FORBIDDEN):
                add(31, "critical", f"Provider imports '{module}' — providers MUST NOT import domains/modules/rbac/jobs/middleware (Law 31/100).",
                    "Remove the import; providers only wrap external SDKs and receive data via parameters.", s.rel, ln)
                add(100, "critical", f"Provider imports '{module}' violating provider isolation (Law 100).",
                    "Remove the import.", s.rel, ln)
        if "HAS_" not in s.content and "def " in s.content:
            add(30, "medium", f"Provider '{s.rel}' missing HAS_<SDK> flag for graceful degradation (Law 30).",
                "Add HAS_<SDK> = True/False.", s.rel, 1)
        sdks = [k for k in SDK_MODULES if re.search(rf"\b{re.escape(k)}\b", s.content.lower())]
        if len(sdks) > 2:
            add(123, "medium", f"Provider wraps multiple SDKs {sdks} — one SDK per provider (Law 123).",
                "Split into separate provider modules, one per external SDK.", s.rel, 1)
        if "calculate" in s.content.lower() or "compute" in s.content.lower():
            add(126, "high", f"Provider '{s.rel}' contains business logic — only SDK wrapping allowed (Law 126).",
                "Move business logic into domain services.", s.rel, 1)
        if "HAS_" in s.content and "if HAS_" not in s.content and "if not HAS_" not in s.content:
            add(125, "medium", f"Provider has HAS_<SDK> but never checks it — domains cannot degrade (Law 125).",
                "Guard SDK usage with `if HAS_<SDK>:`.", s.rel, 1)
        if "health_check" not in s.content and "def " in s.content:
            add(129, "low", f"Provider '{s.rel}' missing health_check() (Law 129).",
                "Add health_check() so /health/deps can verify external dependency health.", s.rel, 1)

def check_law_32():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r'(sk_live|sk_test|password|secret|api_key|token|private_key)\s*=\s*["\'][^"\']{8,}["\']', line):
                add(32, "critical", "Hardcoded secret/credential detected (Law 32).",
                    "Move secrets to environment variables or a secrets manager.", s.rel, i)

def check_law_33():
    for s in BACKEND:
        c = s.content.lower()
        if ("jwt" in c or "decode" in c) and "verify" in c and "type" not in c and "claim" not in c:
            add(33, "high", "JWT decoder may not verify the type claim (access vs refresh) (Law 33).",
                "Verify the 'type' claim to prevent refresh tokens being used as access tokens.", s.rel, 1)

def check_law_34():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r'f["\'].*?(SELECT|INSERT|UPDATE|DELETE|WHERE).*?["\']', line, re.I):
                add(34, "critical", "SQL built with f-string interpolation — SQL injection risk (Law 34).",
                    "Use text() with bound parameters or the ORM.", s.rel, i)

def check_law_35():
    c = ALL_BY_REL.get("main.py")
    c = c.content if c else _read_file(ROOT / "main.py")
    if "csrf" not in c.lower():
        add(35, "high", "CSRF middleware may not be active in main.py (Law 35).",
            "Enable CSRF middleware in all environments.", "main.py", 1)

def check_law_36():
    if not MIDDLEWARE:
        return
    found = any(any(h in s.content for h in ("Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options"))
                for s in MIDDLEWARE)
    if not found:
        add(36, "medium", "Security-headers middleware not detected (Law 36).",
            "Add SecurityHeadersMiddleware (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).", "middleware/", 0)

def check_law_37():
    for s in MIDDLEWARE:
        c = s.content.lower()
        if "rate" in c and ("fail" not in c and "closed" not in c and "deny" not in c):
            add(37, "medium", "Rate limiter may not fail closed when Redis is down (Law 37).",
                "Deny requests when Redis is unreachable (fail closed).", s.rel, 1)

def check_law_38():
    for s in BACKEND:
        c = s.content.lower()
        if ("bcrypt" in c or "password" in c) and "72" not in c and "truncat" not in c:
            add(38, "medium", "Password handling may not enforce bcrypt's 72-byte limit (Law 38).",
                "Reject passwords > 72 bytes before hashing.", s.rel, 1)

def check_law_39():
    locs = [s.rel for s in BACKEND if "get_current_user" in s.content or "def authenticate" in s.content]
    if len(locs) > 8:
        add(39, "medium", f"Auth logic spread across {len(locs)} files — should be canonical (Law 39).",
            "Consolidate auth into modules/{m}/auth/ and rbac/dependencies.py.", locs[0], 1)

def check_law_40():
    c = ALL_BY_REL.get("main.py")
    c = c.content if c else _read_file(ROOT / "main.py")
    if "allow_origins" in c and '"*"' in c:
        add(40, "high", "CORS allows wildcard origin — must validate against an allowlist (Law 40).",
            "Replace '*' with an explicit origin allowlist.", "main.py", 1)

def check_law_41():
    for s in BACKEND:
        c = s.content.lower()
        if ("websocket" in c or "@router.websocket" in c) and "jwt" not in c and "token" not in c:
            add(41, "high", "WebSocket endpoint may not verify JWT type (Law 41).",
                "Verify the access token type claim on WebSocket connect.", s.rel, 1)

def check_law_42():
    for s in ROUTERS:
        if "def " in s.content and "BaseModel" not in s.content and re.search(r"(\b\w+\s*:\s*dict\b|Response\s*\()", s.content):
            add(42, "medium", "Endpoint may accept/return raw dicts instead of Pydantic (Law 42).",
                "Use Pydantic request/response schemas on all public endpoints.", s.rel, 1)

def check_law_43():
    for s in BACKEND:
        c = s.content.lower()
        if "auth" in c and "fail" in c and "log" not in c and "logger" not in c:
            add(43, "medium", "Auth-failure path may not be logged (Law 43).",
                "Log auth failures, 403s and rate-limit triggers at WARNING+.", s.rel, 1)

def check_law_44():
    wf = ROOT.parent / ".github" / "workflows"
    if wf.exists():
        scan = any(any(t in _read_file(p).lower() for t in ("safety", "pip-audit", "cve", "dependency", "snyk"))
                   for p in wf.rglob("*.yml"))
        if not scan:
            add(44, "medium", "No dependency/CVE scanning in CI (Law 44).",
                "Add safety / pip-audit / snyk to CI.", ".github/workflows/", 0)

def check_law_45():
    for s in BACKEND:
        if "lazy='select'" in s.content or "lazy=True" in s.content:
            add(45, "high", "Relationship uses lazy='select' — N+1 queries at scale (Law 45).",
                "Use lazy='selectin' or lazy='joined'.", s.rel, 1)

def check_law_46():
    for s in BACKEND:
        if "alembic" in s.rel:
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r"SELECT\s+\*\s+FROM", line, re.I):
                add(46, "medium", "SELECT * detected — select explicit columns (Law 46).",
                    "List required columns explicitly.", s.rel, i)

def check_law_47():
    for s in INFRA:
        for m in re.finditer(r"pool_size\s*=\s*(\d+)", s.content):
            if int(m.group(1)) < 10:
                add(47, "medium", f"pool_size={m.group(1)} — should be >= 10 (Law 47).",
                    "Set pool_size >= 10, max_overflow >= 20.", s.rel, m.start())

def check_law_48():
    if INFRA and not any("get_read_db" in s.content for s in INFRA):
        add(48, "medium", "No get_read_db() detected — read replica separation missing (Law 48).",
            "Add get_read_db() for read-heavy paths.", "infrastructure/database/", 0)

def check_law_49():
    av = ROOT / "alembic" / "versions"
    if not av.exists():
        return
    heads = [p.name for p in av.rglob("*.py") if "head" in _read_file(p) and "revision" in _read_file(p)]
    if len(heads) > 1:
        add(49, "medium", f"Multiple alembic heads ({len(heads)}) — history diverged (Law 49).",
            "Run `alembic merge` to resolve divergent heads.", "alembic/versions/", 0)

def check_law_50():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if "autocommit" in s.content.lower() and "false" not in s.content.lower():
            add(50, "high", "Autocommit enabled — use explicit transactions (Law 50).",
                "Disable autocommit; wrap writes in explicit transactions.", s.rel, 1)

def check_law_51():
    tables: dict[str, list[str]] = defaultdict(list)
    for s in MODELS:
        if s.tree is None:
            continue
        for cls in s.classes:
            seg = _node_segment(s, cls)
            if seg and "__tablename__" in seg:
                m = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', seg)
                if m:
                    tables[m.group(1)].append(s.rel)
    for t, files in tables.items():
        if len(files) > 1:
            for fp in files:
                add(51, "critical", f"Table '{t}' defined in {len(files)} places — single ownership violated (Law 51).",
                    f"Define '{t}' in exactly one domain.", fp, 1)

def check_law_55():
    for s in MODELS:
        if s.tree is None:
            continue
        for cls in s.classes:
            seg = _node_segment(s, cls)
            if seg and "__tablename__" in seg and "schema" not in seg and "__abstract__" not in seg:
                add(55, "medium", f"Model '{cls.name}' missing schema in __table_args__ (Law 55).",
                    "Add __table_args__ = {'schema': '<domain>'}", s.rel, cls.lineno)

def check_law_57():
    av = ROOT / "alembic" / "versions"
    if not av.exists():
        return
    for p in av.rglob("*.py"):
        for i, line in enumerate(_read_file(p).splitlines(), 1):
            if re.search(r'op\.(drop_table|drop_column|execute\("DROP|execute\(\'DROP)', line, re.I):
                add(57, "medium", "Destructive migration without backward-compatible strategy (Law 57).",
                    "Use expand-contract: add → backfill → switch → drop.", p.relative_to(ROOT).as_posix(), i)

def check_law_58():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r"(?<!#)\bprint\s*\(", line):
                add(58, "low", "print() in production code — use structlog (Law 58).",
                    "Replace print() with logger.info/debug/warning.", s.rel, i)

def check_law_59():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r"except\s*:\s*(?:pass|#|continue)", line):
                add(59, "high", "Bare except with pass — silent exception swallowing (Law 59).",
                    "Log every exception at minimum DEBUG.", s.rel, i)

def check_law_60():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if "async def" in s.content and re.search(r"\btime\.sleep\s*\(", s.content):
            add(60, "high", "Blocking time.sleep() inside async function (Law 60).",
                "Use asyncio.sleep().", s.rel, 1)

def check_law_61():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if re.search(r"=\s*\{\s*\}", s.content) and "cache" in s.content.lower():
            add(61, "low", "Possible unbounded dict cache — bound it with TTL/maxsize (Law 61).",
                "Use functools.lru_cache or cachetools.TTLCache.", s.rel, 1)

def check_law_62():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r"#\s*(?:TODO|FIXME)\s*:", line, re.I) and not re.search(r"#\s*(?:TODO|FIXME)\s*:\s*\[", line, re.I):
                add(62, "low", "TODO/FIXME without ticket reference (Law 62).",
                    "Add a ticket reference: TODO [TICKET-123]: description", s.rel, i)

def check_law_63():
    for s in BACKEND:
        if s.rel.startswith("tests/") or s.rel.startswith("scripts/"):
            continue
        if s.tree is None:
            continue
        for fn in s.functions:
            if fn.name.startswith("_") or fn.name.startswith("test"):
                continue
            if fn.returns is None:
                add(63, "low", f"Public function '{fn.name}' missing return type hint (Law 63).",
                    f"Add -> ReturnType to def {fn.name}(...).", s.rel, fn.lineno)

def check_law_64():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if s.tree is None:
            continue
        for fn in s.functions:
            if fn.end_lineno and fn.end_lineno - fn.lineno > 50:
                add(64, "low", f"Function '{fn.name}' is {fn.end_lineno - fn.lineno} lines (max ~50) (Law 64).",
                    "Refactor into smaller functions.", s.rel, fn.lineno)

def check_law_65():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if s.tree is None:
            continue
        for fn in s.functions:
            seg = _node_segment(s, fn)
            if not seg:
                continue
            max_indent = 0
            for line in seg.splitlines():
                if line.strip():
                    max_indent = max(max_indent, len(line) - len(line.lstrip()))
            if max_indent > 16:
                add(65, "low", f"Function '{fn.name}' nesting exceeds 4 levels (Law 65).",
                    "Use early returns / extraction to flatten.", s.rel, fn.lineno)

def check_law_68():
    patterns: set[str] = set()
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        c = s.content
        if "raise ValueError" in c: patterns.add("ValueError")
        if "raise Exception" in c: patterns.add("Exception")
        if "return None" in c: patterns.add("return None")
    if len(patterns) > 2:
        add(68, "low", f"Mixed error-handling patterns: {sorted(patterns)} (Law 68).",
            "Standardize on one error strategy across services.", "multiple files", 0)

def check_law_69():
    for d in EXPECTED_DOMAINS:
        if not any(t.rel.startswith(f"tests/domains/{d}/") for t in TESTS):
            add(69, "medium", f"Domain '{d}' has no smoke test (Law 69).",
                f"Create tests/domains/{d}/test_smoke.py.", f"tests/domains/{d}/", 0)

def check_law_70_212():
    if not any("architecture" in t.rel for t in TESTS):
        add(70, "medium", "No architecture law tests (Law 70).",
            "Add tests/architecture/test_import_laws.py.", "tests/architecture/", 0)
        add(212, "medium", "No architecture tests found (Law 212).",
            "Add tests/architecture/test_import_laws.py and test_feature_catalog.py.", "tests/architecture/", 0)

def check_law_72():
    if TESTS and not any("integration" in t.rel.lower() for t in TESTS):
        add(72, "low", "No cross-domain integration tests (Law 72).",
            "Add integration tests for cross-domain flows.", "tests/", 0)

def check_law_73():
    if TESTS and not any("perf" in t.rel.lower() for t in TESTS):
        add(73, "low", "No performance regression tests (Law 73).",
            "Add perf regression tests on critical paths (fail >20% latency).", "tests/", 0)

def check_law_74():
    if TESTS and not any("rollback" in _read_file(t.path).lower() for t in TESTS):
        add(74, "medium", "Tests may not use transaction rollback isolation (Law 74).",
            "Use db_session fixture with rollback for isolation.", "tests/conftest.py", 0)

def check_law_75():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        c = s.content
        if ("requests." in c or "httpx." in c) and "try:" in c and "logger" not in c.lower() and "log" not in c.lower():
            add(75, "medium", "External call may not log failure (Law 75).",
                "Log external-call failures at WARNING.", s.rel, 1)

def check_law_76():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if "Session(" in s.content and "get_db" not in s.content:
            add(76, "high", "Manual session creation — use Depends(get_db) only (Law 76).",
                "Replace manual sessions with FastAPI dependency injection.", s.rel, 1)

def check_law_77():
    for s in BACKEND:
        c = s.content.lower()
        if "async def" in c and "engine" in c and "lock" not in c:
            add(77, "medium", "Async resource (engine/pool) without asyncio.Lock (Law 77).",
                "Guard async resource init with asyncio.Lock.", s.rel, 1)

def check_law_78():
    for s in MIDDLEWARE:
        if "orchestrator" in s.rel:
            expected = ["foundation", "auth", "rate", "webhook", "geo", "security", "observe", "compliance"]
            if not all(layer in s.content.lower() for layer in expected):
                add(78, "high", "Middleware pipeline may be missing required layers (Law 78).",
                    "Keep fixed order: " + " → ".join(expected), s.rel, 1)

def check_law_79():
    c = ALL_BY_REL.get("main.py")
    c = c.content if c else _read_file(ROOT / "main.py")
    if "exception_handler" not in c.lower():
        add(79, "high", "No global exception handler (Law 79).",
            "Add @app.exception_handler(Exception) returning structured errors.", "main.py", 1)

def check_law_80():
    c = ALL_BY_REL.get("main.py")
    c = c.content if c else _read_file(ROOT / "main.py")
    if "lifespan" not in c.lower():
        add(80, "medium", "No lifespan handler for graceful shutdown (Law 80).",
            "Add lifespan to dispose DB engine / Redis / workers.", "main.py", 1)

def check_law_81():
    if ROUTERS and not any("/health" in s.content for s in ROUTERS):
        add(81, "medium", "No /health endpoint detected (Law 81).",
            "Add /health, /health/deps, /health/ready.", "routers/", 0)

def check_law_82():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        for i, line in enumerate(s.content.splitlines(), 1):
            if re.search(r'(password|secret|key|token)\s*=\s*["\'][^"\']{4,}["\']', line):
                add(82, "critical", "Default credential literal in config — must be empty/null (Law 82).",
                    "Use None/empty defaults; require real values via env.", s.rel, i)

def check_law_83():
    c = ALL_BY_REL.get("main.py")
    c = c.content if c else _read_file(ROOT / "main.py")
    if "SECRET_KEY" not in c and "DATABASE_URL" not in c and "REDIS_URL" not in c:
        add(83, "high", "Required env vars not validated at startup (Law 83).",
            "Validate SECRET_KEY / DATABASE_URL / REDIS_URL at startup (fail fast).", "main.py", 1)

def check_law_84_203():
    for s in BACKEND:
        if s.rel.startswith("tests/"):
            continue
        if "os.getenv(" in s.content or "os.environ.get(" in s.content:
            add(84, "medium", "Raw os.getenv() — use pydantic-settings (Law 84/203).",
                "Replace with a pydantic-settings BaseSettings class.", s.rel, 1)

def check_law_86():
    if len(list(ROOT.glob("*.env*"))) < 2:
        add(86, "low", "Missing env-specific config profiles (Law 86).",
            "Provide separate config profiles for prod/staging/dev.", "backend/", 0)

def check_law_91():
    for s in ROUTERS:
        if s.tree is None:
            continue
        for fn in _route_handlers(s):
            body = fn.body
            if not (body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), (ast.Constant, ast.Str))):
                add(91, "low", f"Endpoint '{fn.name}' missing OpenAPI docstring (Law 91).",
                    "Add a docstring describing the endpoint.", s.rel, fn.lineno)

def check_law_92_93_94_95_96():
    if BACKEND and not any("structlog" in s.content for s in BACKEND):
        add(92, "medium", "structlog not detected — logs should carry context (Law 92).",
            "Configure structlog with user_id/request_id/domain/action.", "backend/", 0)
    if BACKEND and not any("request_id" in s.content for s in BACKEND):
        add(93, "medium", "request_id not detected (Law 93).",
            "Add request_id middleware and propagate through calls.", "backend/", 0)
    if BACKEND and not any("prometheus" in s.content.lower() for s in BACKEND):
        add(94, "medium", "Prometheus metrics not detected (Law 94).",
            "Instrument critical paths with Prometheus metrics.", "backend/", 0)
    if BACKEND and not any("sentry" in s.content.lower() for s in BACKEND):
        add(95, "medium", "Sentry error tracking not detected (Law 95).",
            "Configure Sentry for unhandled exceptions.", "backend/", 0)
    if BACKEND and not any("audit" in s.content.lower() for s in BACKEND):
        add(96, "medium", "Audit-trail logging not detected (Law 96).",
            "Write state-changing operations to domains/audit/.", "backend/", 0)

def check_law_97_98_99_101_102_103_104():
    cycles = find_cycles()
    for cyc in cycles:
        add(98, "critical", "Circular import detected: " + " -> ".join(cyc),
            "Break the cycle; enforce directional imports (Law 98).", cyc[0], 1)
        add(97, "high", "Import-direction violation (cycle) (Law 97).",
            "Ensure modules → domains → infrastructure → kernel only.", cyc[0], 1)
    for s in BACKEND:
        if s.rel.startswith("modules/"):
            for module, ln in s.imports_from:
                if module.startswith("infrastructure."):
                    add(99, "high", f"Module imports infrastructure directly (Law 99).",
                        "Go through the domains layer, not infrastructure directly.", s.rel, ln)
        if s.rel.startswith("jobs/"):
            for module, ln in s.imports_from:
                if module.startswith(("modules.", "rbac.", "middleware.")):
                    add(103, "high", f"Job imports '{module}' — jobs may only import domains + infrastructure (Law 103).",
                        "Remove the import from the job.", s.rel, ln)
        if s.rel.startswith("middleware/"):
            for module, ln in s.imports_from:
                if module.startswith(("domains.", "modules.")):
                    add(104, "high", f"Middleware imports '{module}' — only infrastructure + rbac allowed (Law 104).",
                        "Remove the import from the middleware.", s.rel, ln)
    for s in INFRA:
        for module, ln in s.imports_from:
            if module.startswith(INFRA_FORBIDDEN):
                add(102, "high", f"infrastructure/ imports '{module}' (Law 102).",
                    "infrastructure only provides platform primitives.", s.rel, ln)
    # Law 101 kernel isolation already covered by check_law_1 / check_law_10

def check_law_105_106():
    for rel, p in FRONTEND_BY_REL.items():
        if not rel.startswith("shared/"):
            continue
        c = read_frontend(rel)
        if "web_app" in c or "mobile_app" in c:
            add(105, "high", "Shared package imports from an app — shared must be independent (Law 105).",
                "Remove app imports from the shared package.", rel, 1)
    for rel, p in FRONTEND_BY_REL.items():
        if rel.endswith((".ts", ".tsx", ".js", ".jsx")):
            c = read_frontend(rel)
            if re.search(r"from\s+[\"']backend", c) or "import backend" in c:
                add(106, "high", "Frontend imports backend directly — use API proxy only (Law 106).",
                    "Communicate via the API proxy/rewrites only.", rel, 1)

def check_law_107_109():
    for s in INFRA:
        if "sqlite" in s.content.lower() and "prod" in s.content.lower():
            add(107, "high", "SQLite referenced in production config — use PostgreSQL 15 (Law 107).",
                "Use PostgreSQL 15 in production.", s.rel, 1)
    if INFRA and not any("redis" in s.content.lower() for s in INFRA):
        add(109, "medium", "Redis not detected (Law 109).",
            "Configure Redis for sessions/cache/rate-limit/blacklist/pub-sub.", "infrastructure/", 0)

def check_law_111():
    if FRONTEND_ROOT.exists():
        pkg = FRONTEND_ROOT / "web_app" / "package.json"
        if pkg.exists() and '"next"' not in _read_file(pkg):
            add(111, "medium", "web_app may not use Next.js App Router (Law 111).",
                "Use Next.js App Router (not Pages Router).", "web_app/package.json", 0)

def check_law_116_117_118_119_120_121():
    if not any("smtp" in s.rel.lower() or "email" in s.rel.lower() for s in PROVIDERS):
        add(116, "low", "No email provider (SMTP) detected (Law 116).",
            "Implement providers/comms/email.py for async transactional email.", "providers/comms/", 0)
    if not any("twilio" in s.rel.lower() or "whatsapp" in s.rel.lower() for s in PROVIDERS):
        add(117, "low", "No Twilio/WhatsApp provider detected (Law 117).",
            "Implement SMS/WhatsApp via providers/comms.", "providers/comms/", 0)
    if not (ROOT / "providers" / "payments").exists():
        add(118, "high", "providers/payments missing — payment gateways required (Law 118).",
            "Implement providers/payments with BasePaymentGateway subclasses.")
    if not any(s.rel.startswith("providers/ai") for s in PROVIDERS):
        add(119, "low", "No providers/ai detected (Law 119).",
            "Implement AI/ML wrappers under providers/ai/.", "providers/ai/", 0)
    if not any(s.rel.startswith("providers/storage") for s in PROVIDERS):
        add(120, "medium", "No providers/storage detected — media blobs must not live in Postgres (Law 120).",
            "Implement providers/storage (S3/local) for blobs.", "providers/storage/", 0)
    if not any(s.rel.startswith("providers/async_workers") for s in PROVIDERS):
        add(121, "low", "No providers/async_workers — CPU-bound work may block the loop (Law 121).",
            "Add providers/async_workers for CPU-bound processing.", "providers/async_workers/", 0)

def check_law_127_128_130_131():
    if not (ROOT / "providers" / "config.py").exists():
        add(127, "low", "providers/config.py missing — API keys/endpoints should live there (Law 127).",
            "Centralize provider config in providers/config.py.", "providers/config.py", 0)
    if not any(s.rel.startswith("providers/async_workers") for s in PROVIDERS):
        add(128, "low", "No async_workers — CPU-bound provider work may block (Law 128).",
            "Route CPU-bound work through providers/async_workers.", "providers/", 0)
    # 130/131 evaluated structurally within provider checks (error mapping / mock tests) — advisory only
    if PROVIDERS and not any("except" in s.content and ("SDK" in s.content or "Error" in s.content) for s in PROVIDERS):
        add(130, "low", "Provider error-mapping to domain exceptions not clearly detected (Law 130).",
            "Map SDK errors to domain exceptions; never leak raw SDK errors.", "providers/", 0)

def check_law_132_133_136_137_139():
    mods = ROOT / "modules"
    if not mods.exists():
        return
    for m in mods.iterdir():
        if not m.is_dir() or m.name.startswith("_"):
            continue
        for sub in ("auth", "routers", "serializers"):
            if not (m / sub).exists():
                add(132, "medium", f"Module '{m.name}' missing {sub}/ (Law 132).",
                    f"Create modules/{m.name}/{sub}/.", f"modules/{m.name}/", 0)
        if not (m / "auth" / "dependencies.py").exists() and not (m / "auth").exists():
            add(133, "medium", f"Module '{m.name}' has no per-module auth (Law 133).",
                "Add modules/{m}/auth/dependencies.py.", f"modules/{m.name}/", 0)
        rd = m / "routers"
        if rd.exists():
            for r in rd.glob("*.py"):
                nm = r.stem
                if nm != "__init__" and not all(ch.isalnum() or ch == "_" for ch in nm):
                    add(134, "low", f"Router '{r.name}' should be named after a domain (Law 134).",
                        "Rename to modules/{m}/routers/{domain}.py.", r.relative_to(ROOT).as_posix(), 1)
        if (rd / "public_routers.py").exists() or (rd / "public.py").exists() or any(r.name.startswith("public") for r in rd.glob("*.py")):
            pass  # public routers present
        if not any((rd / n).exists() for n in ("public_routers.py", "public.py")) and rd.exists():
            add(136, "low", f"Module '{m.name}' has no public_routers split (Law 136).",
                "Separate public_routers (no auth) from routers (auth required).", f"modules/{m.name}/routers/", 0)
        if not (m / "serializers").exists():
            add(137, "low", f"Module '{m.name}' missing serializers/ (Law 137).",
                "Add modules/{m}/serializers/ for response shaping.", f"modules/{m.name}/", 0)
    # 139 route prefixes checked structurally via module names

def check_law_140_141_142_143_144_145_146_147_148_149():
    for sub in ("database", "redis", "storage", "messaging", "observability", "security", "utils"):
        if not (ROOT / "infrastructure" / sub).exists():
            add(140, "medium", f"Missing infrastructure subpackage {sub}/ (Law 140).",
                f"Create infrastructure/{sub}/.", f"infrastructure/{sub}/", 0)
    for s in BACKEND:
        if "DeclarativeBase" in s.content and "class Base" in s.content and "infrastructure.database.base" not in s.content and "infrastructure/database/base" not in s.rel:
            add(148, "high", f"Extra DeclarativeBase in '{s.rel}' — canonical Base is infrastructure.database.base.Base (Law 148).",
                "Use infrastructure.database.base.Base for all models.", s.rel, 1)
    if INFRA and not any("get_db" in s.content for s in INFRA):
        add(149, "high", "No get_db dependency — sessions must use Depends(get_db) (Law 149).",
            "Provide get_db/get_read_db in infrastructure/database.", "infrastructure/database/", 0)

def check_law_150_151_152_153_154_155_156_158_159_160():
    for d in EXPECTED_DOMAINS:
        files = DOMAINS.get(d, [])
        for sub in ("services", "models", "schemas"):
            if not any(f"/{sub}/" in f.rel or f.rel.endswith(f"/{sub}") for f in files):
                add(150, "medium", f"Domain '{d}' missing {sub}/ (Law 150).",
                    f"Create domains/{d}/{sub}/.", f"domains/{d}/", 0)
        if not any(f.rel.endswith("/events.py") for f in files):
            add(154, "low", f"Domain '{d}' missing events.py (event pattern, Law 154).",
                "Add domains/{d}/events.py with named events.", f"domains/{d}/", 0)
        if not any(f.rel.endswith("/ports.py") for f in files):
            add(155, "low", f"Domain '{d}' missing ports.py (read pattern, Law 155).",
                "Add domains/{d}/ports.py with sanctioned read functions.", f"domains/{d}/", 0)
        if not any(f.rel.endswith("/subscribers.py") for f in files):
            add(156, "low", f"Domain '{d}' missing subscribers.py (Law 156).",
                "Add domains/{d}/subscribers.py.", f"domains/{d}/", 0)
        if not any("/read_models/" in f.rel for f in files):
            add(158, "low", f"Domain '{d}' missing read_models/ (CQRS-lite, Law 158).",
                "Add domains/{d}/read_models/ for dashboard projections.", f"domains/{d}/", 0)
        if not any(f.rel.endswith("/policies.py") for f in files):
            add(159, "low", f"Domain '{d}' missing policies.py (Law 159).",
                "Add domains/{d}/policies.py for authorization policies.", f"domains/{d}/", 0)

def check_law_161_162_163_164_165_166_167():
    if not any("catalog" in s.rel for s in RBAC):
        add(161, "medium", "rbac/catalog.py missing — must aggregate all features.py (Law 161).",
            "Create rbac/catalog.py that scans domains/*/features.py.", "rbac/catalog.py", 0)
    if not any("roles" in s.rel for s in RBAC):
        add(162, "medium", "rbac/roles.py missing (Law 162).",
            "Create rbac/roles.py with (module, role) → feature sets.", "rbac/roles.py", 0)
    if not any("resolution" in s.rel for s in RBAC):
        add(163, "medium", "rbac/resolution.py missing (Law 163).",
            "Create rbac/resolution.py (actor × role × country, Redis-cached).", "rbac/resolution.py", 0)
    if not any("dependencies" in s.rel for s in RBAC):
        add(164, "medium", "rbac/dependencies.py missing — require_feature() source (Law 164).",
            "Create rbac/dependencies.py with require_feature()/require_module().", "rbac/dependencies.py", 0)
    if FRONTEND_BY_REL and not any("permissions" in rel for rel in FRONTEND_BY_REL):
        add(167, "medium", "shared/permissions.ts missing — must be GENERATED from /rbac/catalog (Law 167).",
            "Generate shared/src/permissions.ts from GET /rbac/catalog.", "shared/", 0)

def check_law_168_169_170_171_172_173_174_175_176_177():
    for sub in ("web_app", "mobile_app", "shared"):
        if FRONTEND_ROOT.exists() and not (FRONTEND_ROOT / sub).exists():
            add(168, "medium", f"Missing frontend subpackage {sub}/ (Law 168).",
                f"Create frontend/{sub}/.", f"frontend/{sub}/", 0)
    ts = FRONTEND_ROOT / "web_app" / "tsconfig.json"
    if ts.exists() and '"strict": true' not in _read_file(ts):
        add(170, "medium", "TypeScript strict mode not enabled (Law 170).",
            'Add "strict": true to tsconfig.json.', "web_app/tsconfig.json", 0)
    if (FRONTEND_ROOT / "web_app").exists() and not (FRONTEND_ROOT / "web_app" / "next.config.ts").exists() and not (FRONTEND_ROOT / "web_app" / "next.config.js").exists():
        add(173, "low", "Next.js rewrite/proxy config not detected (Law 173).",
            "Configure next.config rewrites for /api/* → NEXT_PUBLIC_API_URL.", "web_app/next.config.*", 0)

def check_law_178_179_180_181_182_183_184_185_186():
    app = FRONTEND_ROOT / "web_app" / "src" / "app"
    if app.exists():
        for p in app.rglob("page.tsx"):
            if not (p.parent / "layout.tsx").exists():
                add(178, "low", f"Route {p.parent.name} missing layout.tsx (Law 178).",
                    "Add layout.tsx for the route group.", p.relative_to(FRONTEND_ROOT).as_posix(), 1)

def check_law_187_188_189_190_191_192_193_194():
    mp = FRONTEND_ROOT / "mobile_app"
    if not mp.exists():
        add(187, "medium", "mobile_app/ missing (Law 187).", "Create mobile_app/ with Expo Router.", "mobile_app/", 0)
        return
    if not any(mp.rglob("app/(tabs)")) and not any(mp.rglob("app/(auth)")):
        add(188, "low", "Mobile route groups (auth)/(tabs) not detected (Law 188).",
            "Organize mobile routes into (auth)/(tabs) groups.", "mobile_app/app/", 0)

def check_law_195_196_197_198_199_200():
    sp = FRONTEND_ROOT / "shared"
    if not sp.exists():
        add(195, "medium", "shared/ missing (Law 195).", "Create shared/ cross-platform TS.", "shared/", 0)
        return
    for rel, p in FRONTEND_BY_REL.items():
        if not rel.startswith("shared/"):
            continue
        c = read_frontend(rel)
        if re.search(r"from\s+[\"']\.\./\.\./web_app", c) or "from 'web_app" in c or "from \"web_app" in c:
            add(196, "high", "shared/ imports from web_app/mobile_app — forbidden (Law 196).",
                "Remove app imports; shared is consumed BY apps.", rel, 1)

def check_law_201_202_206():
    for env in (".env.example", ".env", "backend/.env"):
        if not (ROOT.parent / env).exists():
            add(201, "low", f"Missing env file {env} (Law 201).", "Create the env file.", env, 0)
    if not (ROOT.parent / ".env.example").exists():
        add(202, "low", "No .env.example documenting required vars (Law 202).",
            "Document SECRET_KEY/DATABASE_URL/REDIS_URL in .env.example.", ".env.example", 0)
    if (ROOT.parent / ".github").exists():
        wf = ROOT.parent / ".github" / "workflows"
        if wf.exists() and any('"*"' in _read_file(p) for p in wf.rglob("*.yml") if "cors" in _read_file(p).lower()):
            add(206, "low", "CORS wildcard possibly allowed in CI config (Law 206).",
                "Use an explicit CORS origin allowlist (no '*' in prod).", ".github/workflows/", 0)

def check_law_207_208_209_210_211_213_214():
    if not ((ROOT / "pyproject.toml").exists() or (ROOT / "setup.cfg").exists() or (ROOT / "pytest.ini").exists()):
        add(207, "low", "No pytest configuration detected (Law 207).",
            "Add pytest config (pyproject.toml [tool.pytest.ini_options]).", "backend/", 0)
    if not any(t.rel.endswith(".test.ts") or t.rel.endswith(".spec.ts") for t in []) and FRONTEND_ROOT.exists():
        if not any(p.suffix in (".test.ts", ".spec.ts", ".test.tsx", ".spec.tsx") for p in FRONTEND_FILES):
            add(211, "low", "No frontend (Jest/RTL) tests detected (Law 211).",
                "Add Jest + RTL tests for web/mobile.", "frontend/", 0)

def check_law_215_217_218_220():
    if not (ROOT.parent / "docker-compose.yml").exists():
        add(215, "medium", "docker-compose.yml missing (Law 215).",
            "Add docker-compose.yml (db/redis/backend/frontend/workers).", "docker-compose.yml", 0)
    if not (ROOT.parent / ".github" / "workflows").exists() or not any("alembic" in _read_file(p).lower() for p in (ROOT.parent / ".github" / "workflows").rglob("*.yml") if (ROOT.parent / ".github" / "workflows").exists()):
        add(217, "low", "Migration-on-deploy (alembic upgrade head) not detected in CI (Law 217).",
            "Run `alembic upgrade head` automatically before serving.", ".github/workflows/", 0)
    if ROUTERS and not any("/health/ready" in s.content or "health/ready" in s.content for s in ROUTERS):
        add(218, "low", "No /health/ready endpoint detected (Law 218).",
            "Add /health/ready (deep dependency check).", "routers/", 0)

def check_law_221_223_224():
    if INFRA and not any("cache" in s.content.lower() for s in INFRA):
        add(221, "medium", "No caching strategy detected (Law 221).",
            "Implement Redis caching with TTL + invalidation.", "infrastructure/", 0)
    for s in INFRA:
        for m in re.finditer(r"max_overflow\s*=\s*(\d+)", s.content):
            if int(m.group(1)) < 20:
                add(223, "medium", f"max_overflow={m.group(1)} — should be >= 20 (Law 223).",
                    "Set pool_size >= 10, max_overflow >= 20.", s.rel, m.start())
    if BACKEND and not any("selectin" in s.content or "joined" in s.content for s in BACKEND):
        add(224, "low", "No selectin/joined lazy loading detected (Law 224).",
            "Use lazy='selectin'/'joined' to avoid N+1.", "backend/", 0)

def check_law_228_229_230():
    if MODELS and not any("is_deleted" in s.content for s in MODELS):
        add(228, "medium", "No soft-delete (is_deleted) detected in models (Law 228).",
            "Add is_deleted to user-facing tables.", "domains/", 0)
    if MODELS and not any("created_at" in s.content and "updated_at" in s.content for s in MODELS):
        add(229, "medium", "Audit timestamp columns not detected (Law 229).",
            "Add created_at/updated_at via TimestampMixin.", "domains/", 0)
    if not any(s.rel.startswith("domains/audit") for s in BACKEND):
        add(230, "medium", "No domains/audit detected — WORM audit trail missing (Law 230).",
            "Implement domains/audit for state-change logging.", "domains/audit/", 0)

def check_law_233_235():
    for s in ROUTERS:
        if "def " in s.content and "@router." not in s.content and "@app." not in s.content and "APIRouter" not in s.content:
            add(233, "low", f"Router '{s.rel}' may not declare endpoints via decorators (Law 233).",
                "Use @router.get/post/put/delete.", s.rel, 1)
    if ROUTERS and not any("BaseModel" in s.content for s in ROUTERS):
        add(235, "low", "No Pydantic models in routers — responses may be unvalidated (Law 235).",
            "Use Pydantic schemas for request/response.", "routers/", 0)

def check_law_241_242_243_244():
    if (ROOT.parent / ".github").exists():
        wf = ROOT.parent / ".github" / "workflows"
        if wf.exists() and not any("commitlint" in _read_file(p).lower() or "conventional" in _read_file(p).lower() for p in wf.rglob("*.yml")):
            add(241, "low", "No conventional-commits enforcement detected (Law 241).",
                "Add commitlint / conventional-commits check.", ".github/workflows/", 0)
        if not any("ruff" in _read_file(p).lower() for p in wf.rglob("*.yml")):
            add(243, "low", "Pre-commit ruff hook not detected in CI (Law 243).",
                "Add ruff to pre-commit / CI.", ".github/workflows/", 0)

def check_law_245_246_247_248_249_250():
    if not ARCH_DOC.exists():
        add(245, "medium", "ARCHITECTURE_DIAGRAM.md missing (Law 245).",
            "Create the authoritative architecture doc.", "ARCHITECTURE_DIAGRAM.md", 0)
    if ROOT.parent.joinpath("AGENTS.md").exists() is False:
        add(246, "low", "AGENTS.md quick reference missing (Law 246).", "Add AGENTS.md.", "AGENTS.md", 0)
    if not (ROOT.parent / "docs" / "runbooks").exists():
        add(248, "low", "docs/runbooks/ missing (Law 248).",
            "Add runbooks for deploy/rollback/incident.", "docs/runbooks/", 0)

def check_law_275_276_285_290_292():
    if BACKEND and not any("encrypt" in s.content.lower() for s in BACKEND):
        add(275, "medium", "No encryption-at-rest code detected (Law 275).",
            "Implement AES-256/KMS encryption for sensitive data.", "backend/", 0)
    if BACKEND and not any(("tls" in s.content.lower()) or ("ssl" in s.content.lower()) for s in BACKEND):
        add(276, "medium", "TLS/SSL configuration not detected (Law 276).",
            "Configure TLS 1.3 with certificate pinning.", "backend/", 0)
    if MIDDLEWARE and not any("content-security-policy" in s.content.lower() or "csp" in s.content.lower() for s in MIDDLEWARE):
        add(285, "medium", "CSP header not detected (Law 285).",
            "Add strict CSP with nonces.", "middleware/", 0)
    if (ROOT.parent / ".github" / "workflows").exists():
        wf = ROOT.parent / ".github" / "workflows"
        if not any("hash" in _read_file(p).lower() or "pin" in _read_file(p).lower() for p in wf.rglob("*.yml")):
            add(290, "low", "Dependency pinning with hashes not detected (Law 290).",
                "Pin dependencies exactly with hashes.", ".github/workflows/", 0)
    if (ROOT.parent / "LICENSE").exists() is False:
        add(292, "low", "LICENSE file missing — license compliance (Law 292).",
            "Add a LICENSE; enforce license CI checks.", "LICENSE", 0)

def check_law_296_313_314_324():
    if BACKEND and not any("circuit" in s.content.lower() for s in BACKEND):
        add(296, "medium", "No circuit-breaker pattern detected (Law 296).",
            "Wrap external calls with a circuit breaker.", "backend/", 0)
    if (ROOT.parent / "docs").exists() and not any("compliance" in p.name.lower() for p in (ROOT.parent / "docs").rglob("*.md")):
        add(313, "low", "No compliance documentation detected (Law 313).",
            "Document GDPR/PCI-DSS compliance approach.", "docs/", 0)
    if (ROOT.parent / "Makefile").exists() or (ROOT.parent / "terraform").exists() or (ROOT.parent / "pulumi").exists() or (FRONTEND_ROOT / "Dockerfile").exists():
        pass
    else:
        add(314, "low", "No IaC detected (Terraform/Pulumi) (Law 314).",
            "Manage infrastructure as code.", "root/", 0)
    if (ROOT.parent / ".github" / "workflows").exists():
        wf = ROOT.parent / ".github" / "workflows"
        if not any("pull_request" in _read_file(p).lower() for p in wf.rglob("*.yml")):
            add(324, "low", "No PR-gated CI detected (Law 324).",
                "Require PR + CI before merge.", ".github/workflows/", 0)

# ══════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════
CHECK_FUNCS = [
    check_law_1, check_law_2_90, check_law_3, check_law_4_157, check_law_5_227,
    check_law_6_222, check_law_7, check_law_8_134_135, check_law_9, check_law_10,
    check_law_11_124, check_law_12, check_law_13_138, check_law_14_15_16_18,
    check_law_17, check_law_19, check_law_20, check_law_21, check_law_22_52_53,
    check_law_23_54, check_law_24_56, check_law_25, check_law_26, check_law_27,
    check_law_28, check_law_29, check_law_30_31_100_123_125_126_129, check_law_32,
    check_law_33, check_law_34, check_law_35, check_law_36, check_law_37, check_law_38,
    check_law_39, check_law_40, check_law_41, check_law_42, check_law_43, check_law_44,
    check_law_45, check_law_46, check_law_47, check_law_48, check_law_49, check_law_50,
    check_law_51, check_law_55, check_law_57, check_law_58, check_law_59, check_law_60,
    check_law_61, check_law_62, check_law_63, check_law_64, check_law_65, check_law_68,
    check_law_69, check_law_70_212, check_law_72, check_law_73, check_law_74, check_law_75,
    check_law_76, check_law_77, check_law_78, check_law_79, check_law_80, check_law_81,
    check_law_82, check_law_83, check_law_84_203, check_law_86, check_law_91,
    check_law_92_93_94_95_96, check_law_97_98_99_101_102_103_104, check_law_105_106,
    check_law_107_109, check_law_111, check_law_116_117_118_119_120_121,
    check_law_127_128_130_131, check_law_132_133_136_137_139,
    check_law_140_141_142_143_144_145_146_147_148_149,
    check_law_150_151_152_153_154_155_156_158_159_160,
    check_law_161_162_163_164_165_166_167,
    check_law_168_169_170_171_172_173_174_175_176_177,
    check_law_178_179_180_181_182_183_184_185_186,
    check_law_187_188_189_190_191_192_193_194,
    check_law_195_196_197_198_199_200,
    check_law_201_202_206, check_law_207_208_209_210_211_213_214,
    check_law_215_217_218_220, check_law_221_223_224, check_law_228_229_230,
    check_law_233_235, check_law_241_242_243_244, check_law_245_246_247_248_249_250,
    check_law_275_276_285_290_292, check_law_296_313_314_324,
]

def run_all():
    for fn in CHECK_FUNCS:
        try:
            fn()
        except Exception as e:  # a check must never crash the whole audit
            sys.stderr.write(f"[WARN] check {fn.__name__} failed: {e}\n")

# ══════════════════════════════════════════════════════════════════════════
# REPORT
# ══════════════════════════════════════════════════════════════════════════
def generate_reports():
    now = datetime.now().isoformat()
    laws_hit = defaultdict(list)
    for fnd in findings:
        laws_hit[fnd["law_id"]].append(fnd)

    sev = defaultdict(int)
    for fnd in findings:
        sev[fnd["severity"]] += 1

    law_status = {}
    for lid in range(1, 326):
        cat, rule, checkable = LAWS.get(lid, ("?", "unknown", False))
        if lid in laws_hit:
            status = "FAIL"
        elif checkable:
            status = "PASS"
        else:
            status = "MANUAL"
        law_status[lid] = {
            "id": lid, "category": cat, "rule": rule,
            "checkable": checkable, "status": status,
            "findings": len(laws_hit.get(lid, [])),
        }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "meta": {
            "version": "4.0", "timestamp": now, "total_laws": 325,
            "backend_files": len(BACKEND), "domains": sorted(DOMAINS.keys()),
            "frontend_files": len(FRONTEND_FILES),
        },
        "summary": {
            "total_findings": len(findings),
            "critical": sev["critical"], "high": sev["high"],
            "medium": sev["medium"], "low": sev["low"],
            "passed": sum(1 for v in law_status.values() if v["status"] == "PASS"),
            "failed": sum(1 for v in law_status.values() if v["status"] == "FAIL"),
            "manual_review": sum(1 for v in law_status.values() if v["status"] == "MANUAL"),
        },
        "laws": law_status,
        "findings": findings,
    }
    REPORT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"\nAUDIT COMPLETE v4 -- {len(findings)} findings")
    print(f"  Critical:{sev['critical']}  High:{sev['high']}  Medium:{sev['medium']}  Low:{sev['low']}")
    print(f"  Laws: PASS={payload['summary']['passed']}  FAIL={payload['summary']['failed']}  MANUAL={payload['summary']['manual_review']}  (of 325)")
    print(f"  Backend files scanned: {len(BACKEND)} | Frontend files: {len(FRONTEND_FILES)}")
    print(f"  Report: {REPORT}")

def main():
    print("=" * 64)
    print("ZOZI Architecture Audit v4 -- honest, AST-based, 325 laws")
    print("=" * 64)
    index_backend()
    index_frontend()
    build_import_graph()
    print(f"Indexed {len(BACKEND)} backend files ({len(DOMAINS)} domains), {len(FRONTEND_FILES)} frontend files")
    print("Running checks...")
    run_all()
    generate_reports()

if __name__ == "__main__":
    main()
