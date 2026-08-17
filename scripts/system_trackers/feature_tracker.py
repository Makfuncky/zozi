#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZOZI Feature Tracker v5.3 — OLLAMA SEMANTIC VERIFICATION
==================================================================
v5.2 fixes + Ollama/NLP integration:

  F1 SEMANTIC RELEVANCE — if Ollama is running, uses embedding cosine
     similarity to score file-to-feature relevance instead of keyword
     counting. Falls back to keyword matching automatically.
  F2 LLM CAPABILITY CHECK — asks Ollama to verify if a described
     capability is actually implemented in the matched code context.
  F3 FILENAME GUARD — .md/.yaml/.json refs in specs are no longer
     treated as code identifiers.
  F4 TABLE PARSER FIX — test_categories.py no longer parsed as
     table "py" in schema "test_categories".
  F5 TEST RELEVANCE — test files must match ≥3 feature-specific terms
     (not generic) to count toward the test score.
  F6 DEDUP — duplicate file entries eliminated.
  F7 SEMANTIC THRESHOLD — files below cosine similarity 0.15 are
     excluded even if keywords match.

Usage:
    python scripts/system_trackers/feature_tracker.py
    python scripts/system_trackers/feature_tracker.py --feature SYS_007
    python scripts/system_trackers/feature_tracker.py --no-ollama
"""
from __future__ import annotations

import ast, json, math, os, re, sys, time, traceback
from collections import defaultdict
from pathlib import Path


# Canonical domain mapping from system_architecture_audit (with standalone fallback).
_DOMAIN_ALIAS_MAP: dict[str, str] = {}
try:
    from system_architecture_audit import PLACEMENT_DOMAIN_KEYWORDS as _AUDIT_KW
    for _dom, _aliases in _AUDIT_KW.items():
        _DOMAIN_ALIAS_MAP[_dom.lower()] = _dom
        for _a in _aliases:
            _DOMAIN_ALIAS_MAP[str(_a).lower()] = _dom
except Exception:
    pass


def _normalize_stem(stem: str) -> str:
    s = stem.lower()
    s = s.replace("-", "_")
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s


def _extract_domain_from_stem(stem: str) -> str:
    """Map feature stem to a canonical domain."""
    s = _normalize_stem(stem)
    if s in _DOMAIN_ALIAS_MAP:
        return _DOMAIN_ALIAS_MAP[s]
    parts = s.split("_")
    for p in parts:
        if p in _DOMAIN_ALIAS_MAP:
            return _DOMAIN_ALIAS_MAP[p]
    for i in range(len(parts)):
        for j in range(i + 1, len(parts) + 1):
            combo = "_".join(parts[i:j])
            if combo in _DOMAIN_ALIAS_MAP:
                return _DOMAIN_ALIAS_MAP[combo]
    return "other"


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================================
# PATHS & CONFIG
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent

def find_repo_root(start: Path) -> Path:
    for c in [start, *start.parents]:
        if (c / "backend").is_dir() and (c / "frontend").is_dir():
            return c
    for c in [start, *start.parents]:
        if (c / "backend").is_dir():
            return c
    return start

ROOT = find_repo_root(SCRIPT_DIR)

OUTPUT = ROOT / "documents" / "CODEBASE_STATUS_MATRIX_AUTO.md"

EXCLUDE_DIRS = {
    "node_modules", ".next", ".git", "__pycache__", "versions_archive",
    ".venv", "venv", "dist", "build", "coverage", ".expo", "artifacts",
    ".pytest_cache", ".mypy_cache", ".turbo", ".cache", ".gradle",
    "android", "ios", ".detox",
}
EXTS = {".py", ".ts", ".tsx"}
MAX_CHARS = 1_000_000
MAX_PATH_LEN = 240
MAX_CELL_FILES = 50

# Ollama config
OLLAMA_HOSTS = ["http://localhost:11434", "http://127.0.0.1:11434", "http://host.docker.internal:11434"]
OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_LLM_MODEL = "llama3.2"
COSINE_THRESHOLD = 0.15
MAX_CONTEXT_CHARS = 2000  # max chars of file content sent to LLM

WEIGHTS = {
    "db": 0.20, "api": 0.15, "state": 0.15, "capability": 0.10,
    "sections": 0.20, "tests": 0.10, "steps": 0.10,
}

SECTION_DEFS = [
    ("§I", "🌐 Section I — System & Infrastructure Features", ["Internal", "All roles"]),
    ("§II", "👤 Section II — Customer Features & Systems Status", ["Customer"]),
    ("§III", "🏭 Section III — Supplier Panel Features & Systems Status", ["Supplier"]),
    ("§IV", "🚚 Section IV — Logistor (Logistics Partner) Panel Features & Systems Status", ["Logistor", "Logistics"]),
    ("§V", "👨‍💼 Section V — Admin Panel Features & Systems Status", ["Admin"]),
    ("§VI", "👷 Section VI — Employee (EMS) Features & Systems Status", ["Employee"]),
]
SCOPE_TO_SECTION = {
    "customer": "§II", "supplier": "§III",
    "logistor": "§IV", "logistics": "§IV", "logistic": "§IV",
    "admin": "§V", "employee": "§VI", "internal": "§I", "all roles": "§I",
}

LAYER_LABEL = {
    "backend_router": "Backend Routers", "backend_controller": "Backend Controllers",
    "backend_service": "Backend Services", "backend_model": "Backend Models",
    "backend_schema": "Backend Schemas (Pydantic)",
    "backend_middleware": "Backend Middleware", "backend_util": "Backend Utils",
    "backend_provider": "Backend Providers", "backend_core": "Backend Core",
    "backend_data": "Backend Data/Seed", "backend_security": "Backend Security",
    "web_page": "Web Pages", "web_component": "Web Components",
    "web_lib": "Web Lib/Hooks", "web_app_other": "Web App Files",
    "frontend_script": "Frontend Scripts",
    "mobile_screen": "Mobile Screens", "mobile_component": "Mobile Components",
    "mobile_lib": "Mobile Lib/Hooks",
    "test_backend": "Backend Tests", "test_web": "Web Tests",
    "test_mobile": "Mobile Tests", "e2e": "E2E Tests",
    "migration": "Migrations", "backend_script": "Backend Scripts",
    "backend_other": "Backend Other", "other": "Other",
}
LAYER_ORDER = [
    "backend_router", "backend_controller", "backend_service", "backend_model",
    "backend_schema", "backend_middleware", "backend_util", "backend_provider",
    "backend_core", "backend_data", "backend_security",
    "web_page", "web_component", "web_lib", "web_app_other", "frontend_script",
    "mobile_screen", "mobile_component", "mobile_lib",
    "test_backend", "test_web", "test_mobile", "e2e",
    "migration", "backend_script", "backend_other", "other",
]

GENERIC_TERMS = {
    "product", "products", "category", "categories", "order", "orders",
    "user", "users", "cart", "checkout", "payment", "payments",
    "item", "items", "list", "detail", "create", "update", "delete",
    "get", "set", "add", "remove", "edit", "view", "page", "screen",
    "component", "app", "main", "index", "layout", "home", "dashboard",
    "api", "route", "router", "service", "controller", "model", "schema",
    "test", "tests", "spec", "config", "settings", "util", "utils",
    "helper", "helpers", "type", "types", "interface", "base", "core",
    "admin", "supplier", "customer", "logistics", "auth", "login",
    "register", "profile", "account", "search", "filter", "sort",
    "upload", "download", "import", "export", "report", "reports",
    "notification", "notifications", "message", "messages",
    "status", "state", "data", "info", "details", "form", "forms",
    "modal", "dialog", "popup", "alert", "toast", "banner",
    "loading", "error", "empty", "success", "warning",
    "button", "input", "select", "checkbox", "radio", "toggle",
    "table", "grid", "card", "tabs", "tab", "accordion",
    "header", "footer", "sidebar", "nav", "menu", "dropdown",
    "image", "icon", "avatar", "badge", "tag", "label",
    "date", "time", "datetime", "timestamp", "duration",
    "price", "amount", "total", "subtotal", "discount", "tax",
    "currency", "money", "balance", "credit", "debit",
    "address", "location", "city", "country", "region", "zone",
    "phone", "email", "name", "title", "description", "note",
    "id", "uuid", "code", "slug", "url", "link", "path",
    "chat", "file", "files", "contact", "contacts", "video", "media",
    "invoice", "invoices", "review", "reviews", "wishlist", "shipping",
    "websocket", "socket", "realtime", "real-time", "ws", "sse",
    "event", "events", "listener", "handler", "middleware", "hook",
    "store", "context", "provider", "consumer", "delivery", "delivered",
    "pending", "processing", "cancelled", "canceled", "returned",
}

# F3: file extensions that are NOT code identifiers
NON_CODE_EXTENSIONS = {".md", ".yaml", ".yml", ".json", ".txt", ".toml", ".ini", ".cfg", ".env"}

UPPER_STOP = {
    "THE", "AND", "FOR", "WITH", "FROM", "THAT", "THIS", "THESE", "THOSE",
    "ONLY", "MUST", "NEVER", "ALWAYS", "WHEN", "WHERE", "WHICH", "WHILE",
    "THEN", "THAN", "HERE", "INTO", "ONTO", "UPON", "EACH", "EVERY", "SOME",
    "ANY", "ALL", "ALSO", "JUST", "LIKE", "OVER", "UNDER", "AFTER", "BEFORE",
    "ABOUT", "ABOVE", "BELOW", "BETWEEN", "BOTH", "OTHER", "OTHERS", "SAME",
    "VIA", "PER", "NOT", "NOW", "NEW", "ONE", "TWO", "FIRST", "LAST", "MORE",
    "MOST", "DONE", "STEP", "PATH", "EXACTLY", "CANONICAL", "DETAILED",
    "BINDING", "BUILD", "SPEC", "SCOPE", "NOTE", "FULL", "CORE", "PART",
    "GOLDEN", "MATRIX", "ADDED", "RESTORED", "RESERVED", "VISIBLE", "HIDDEN",
    "COD", "CARD", "GPS", "JSON", "PDF", "HTML", "API", "URL", "ID", "QR",
    "RMA", "WS", "POST", "GET", "PUT", "PATCH", "DELETE", "DOCUMENTS",
}
LOWER_STOP = {
    "the", "and", "for", "with", "from", "that", "this", "these", "those",
    "only", "must", "never", "always", "when", "where", "which", "while",
    "then", "than", "here", "into", "onto", "upon", "each", "every", "some",
    "any", "all", "also", "just", "like", "over", "under", "after", "before",
    "about", "above", "below", "between", "both", "other", "others", "same",
    "via", "per", "not", "now", "new", "one", "two", "first", "last", "more",
    "most", "done", "step", "path", "will", "your", "their", "there", "what",
    "who", "how", "can", "may", "but", "yet", "its", "his", "her", "our",
    "you", "they", "them", "been", "have", "has", "had", "was", "were",
    "are", "is", "be", "do", "does", "did", "see", "use", "used", "using",
    "such", "well", "part", "full", "core", "every", "no", "button",
}

TABLEISH_RE = re.compile(r"(_events|_rules|_assets|_requests|_logs|_items|_lines|_settings|s)$")


# ============================================================================
# OLLAMA CLIENT — optional, graceful fallback
# ============================================================================
class OllamaClient:
    """Optional Ollama integration for semantic verification."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.host = None
        self.embed_model = None
        self.llm_model = None
        self._embeddings_cache = {}
        if enabled:
            self._detect()

    def _detect(self):
        import urllib.request
        for host in OLLAMA_HOSTS:
            try:
                req = urllib.request.Request(f"{host}/api/tags", method="GET")
                req.add_header("Content-Type", "application/json")
                with urllib.request.urlopen(req, timeout=3) as resp:
                    data = json.loads(resp.read().decode())
                    models = [m["name"] for m in data.get("models", [])]
                    self.host = host
                    # Pick best available models
                    for m in models:
                        if "embed" in m.lower():
                            self.embed_model = m
                    for m in models:
                        if any(k in m.lower() for k in ["llama", "mistral", "phi", "gemma", "qwen"]):
                            if not self.llm_model:
                                self.llm_model = m
                    if not self.embed_model and models:
                        self.embed_model = models[0]
                    if not self.llm_model and models:
                        self.llm_model = models[0]
                    if self.embed_model or self.llm_model:
                        print(f"  🦙 Ollama detected at {host}")
                        if self.embed_model:
                            print(f"     Embedding model: {self.embed_model}")
                        if self.llm_model:
                            print(f"     LLM model: {self.llm_model}")
                        return
            except Exception:
                continue
        if self.enabled:
            print("  ⚠️ Ollama not detected — falling back to keyword matching")
            self.enabled = False

    @property
    def can_embed(self):
        return self.enabled and self.host and self.embed_model

    @property
    def can_llm(self):
        return self.enabled and self.host and self.llm_model

    def _api_call(self, endpoint, payload, timeout=30):
        import urllib.request
        url = f"{self.host}/api/{endpoint}"
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def embed(self, text: str) -> list | None:
        if not self.can_embed:
            return None
        cache_key = hash(text[:500])
        if cache_key in self._embeddings_cache:
            return self._embeddings_cache[cache_key]
        try:
            result = self._api_call("embed", {
                "model": self.embed_model,
                "input": text[:4000]
            })
            emb = result.get("embedding") or result.get("embeddings", [[]])[0]
            if emb:
                self._embeddings_cache[cache_key] = emb
                return emb
        except Exception:
            pass
        return None

    def cosine_similarity(self, a: list, b: list) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def verify_capability(self, capability: str, code_context: str) -> dict:
        """Ask LLM if a capability is implemented in the given code context."""
        if not self.can_llm:
            return {"verified": None, "reason": "ollama_unavailable"}
        prompt = f"""You are a code auditor. Given a feature capability description and a code snippet, determine if the capability is actually implemented.
        CAPABILITY: {capability}
        CODE CONTEXT (first {MAX_CONTEXT_CHARS} chars of most relevant file):
        {code_context[:MAX_CONTEXT_CHARS]}

Reply with ONLY a JSON object: {{"verified": true/false, "confidence": 0.0-1.0, "reason": "brief explanation"}}"""
        try:
            result = self._api_call("generate", {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=60)
            response = result.get("response", "")
            try:
                parsed = json.loads(response)
                return {
                    "verified": parsed.get("verified"),
                    "confidence": parsed.get("confidence", 0.5),
                    "reason": parsed.get("reason", "")
                }
            except json.JSONDecodeError:
                # Try to extract JSON from response
                m = re.search(r'\{[^}]+\}', response)
                if m:
                    parsed = json.loads(m.group())
                    return {
                        "verified": parsed.get("verified"),
                        "confidence": parsed.get("confidence", 0.5),
                        "reason": parsed.get("reason", "")
                    }
        except Exception:
            pass
        return {"verified": None, "reason": "llm_error"}


# ============================================================================
# SYMBOL EXTRACTION
# ============================================================================
def extract_python_symbols(text: str, rel: str) -> dict:
    symbols = {
        "functions": set(), "classes": set(), "routes": set(),
        "route_methods": set(), "imports": set(), "models": set(),
        "tablename": set(), "has_basemodel": False, "has_sqlalchemy": False,
        "router_prefix": "",
    }
    m = re.search(r'APIRouter\([^)]*prefix\s*=\s*["\']([^"\']+)["\']', text)
    if m:
        symbols["router_prefix"] = m.group(1)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        symbols["functions"] = set(re.findall(r"def\s+(\w+)\s*\(", text))
        symbols["classes"] = set(re.findall(r"class\s+(\w+)\s*[(:]", text))
        symbols["routes"] = set(re.findall(r'["\'](/[\w/{}\-]+)["\']', text))
        symbols["imports"] = set(re.findall(r"(?:from|import)\s+([\w.]+)", text))
        symbols["has_basemodel"] = "BaseModel" in text
        symbols["has_sqlalchemy"] = "__tablename__" in text
        return symbols
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols["functions"].add(node.name)
        elif isinstance(node, ast.ClassDef):
            symbols["classes"].add(node.name)
            for base in node.bases:
                base_name = base.id if isinstance(base, ast.Name) else (
                    base.attr if isinstance(base, ast.Attribute) else "")
                if base_name == "BaseModel":
                    symbols["has_basemodel"] = True
                if base_name in ("Base", "DeclarativeBase"):
                    symbols["has_sqlalchemy"] = True
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for t in item.targets:
                        if isinstance(t, ast.Name) and t.id == "__tablename__":
                            if isinstance(item.value, ast.Constant):
                                symbols["tablename"].add(str(item.value))
                                symbols["has_sqlalchemy"] = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                symbols["imports"].add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                symbols["imports"].add(node.module)
    for m in re.finditer(
            r'@router\.(get|post|put|patch|delete|websocket)\(\s*["\']([^"\']+)["\']', text):
        method, path = m.group(1).upper(), m.group(2)
        symbols["routes"].add(path)
        symbols["route_methods"].add(f"{method} {path}")
    return symbols


def extract_ts_symbols(text: str, rel: str) -> dict:
    symbols = {
        "functions": set(), "components": set(), "imports": set(),
        "api_calls": set(), "hooks": set(), "types": set(),
    }
    for m in re.finditer(r'(?:export\s+(?:default\s+)?)?(?:function|const)\s+([A-Z]\w+)\s*(?:=\s*)?(?:\(|<)', text):
        symbols["components"].add(m.group(1))
    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(', text):
        symbols["functions"].add(m.group(1))
    for m in re.finditer(r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(', text):
        symbols["functions"].add(m.group(1))
    for m in re.finditer(r'\buse([A-Z]\w+)\s*\(', text):
        symbols["hooks"].add(f"use{m.group(1)}")
    for m in re.finditer(r'(?:fetch|apiFetch|axios\.\w+)\s*\(\s*[`"\']([^`"\']+)[`"\']', text):
        url = m.group(1)
        if url.startswith("/") or url.startswith("http"):
            symbols["api_calls"].add(url)
    for m in re.finditer(r"from\s+['\"]([^'\"]+)['\"]", text):
        symbols["imports"].add(m.group(1).split("/")[-1])
    for m in re.finditer(r'(?:interface|type)\s+(\w+)', text):
        symbols["types"].add(m.group(1))
    return symbols


def classify_by_content(rel: str, symbols: dict) -> str:
    r = rel.lower()
    fname = Path(rel).name.lower()
    if r.startswith("backend/"):
        if "alembic" in r or "/versions/" in r:
            return "migration"
        if "/scripts/" in r or fname.startswith(
                ("seed_", "generate_", "migrate_", "fix_", "check_", "lint_",
                 "update_", "safe_", "extract_", "populate_", "rebuild_")):
            return "backend_script"
        if "/tests/" in r or "/test/" in r or fname.startswith(("test_", "conftest")):
            return "test_backend"
        if symbols.get("tablename"):
            return "backend_model"
        if (symbols.get("has_sqlalchemy") and not symbols.get("route_methods")
                and ("/models/" in r or "model" in fname)):
            return "backend_model"
        if symbols.get("route_methods"):
            return "backend_router"
        if "schema" in fname or "/schemas/" in r:
            return "backend_schema"
        if "router" in fname or "routes" in fname or "/routers/" in r or "/routes/" in r:
            return "backend_router"
        if "/middleware/" in r or "middleware" in fname:
            return "backend_middleware"
        if ("/utils/" in r or "/helpers/" in r or "utils" in fname
                or "helper" in fname or fname.startswith(("constants", "pagination"))):
            return "backend_util"
        if "/providers/" in r:
            return "backend_provider"
        if fname in ("main.py", "database.py", "base.py", "__init__.py",
                     "_exports.py", "init_db.py"):
            return "backend_core"
        if "controller" in fname or "/controllers/" in r:
            return "backend_controller"
        if "service" in fname or "/services/" in r:
            return "backend_service"
        if "/security/" in r:
            return "backend_security"
        if "/data/" in r or "seed" in fname:
            return "backend_data"
        return "backend_other"
    if r.startswith("frontend/"):
        is_mobile = any(seg in r for seg in
                        ("mobile_app/", "(tabs)/", "(auth)/", ".native."))
        if "/e2e/" in r or "/playwright/" in r:
            return "e2e"
        if ("__tests__" in r or fname.startswith("conftest")
                or fname.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx"))):
            return "test_mobile" if is_mobile else "test_web"
        if fname.endswith("page.tsx"):
            return "web_page"
        if is_mobile and fname.endswith((".ts", ".tsx", ".py")):
            if "/components/" in r:
                return "mobile_component"
            if "/lib/" in r or "/hooks/" in r or "/theme/" in r or "/utils/" in r:
                return "mobile_lib"
            return "mobile_screen"
        if "/components/" in r:
            return "web_component"
        if "/hooks/" in r or "/lib/" in r or symbols.get("hooks"):
            return "web_lib"
        if "/scripts/" in r or fname.endswith(".py"):
            return "frontend_script"
        if fname.endswith((".ts", ".tsx")):
            return "web_component" if symbols.get("components") else "web_app_other"
        return "other"
    return "other"


def get_role_scope(rel: str, symbols: dict) -> str:
    r = rel.lower()
    fname = Path(rel).name.lower()
    if r.startswith("frontend/"):
        if "/admin/" in r:
            return "§V"
        if "/supplier" in r:
            return "§III"
        if "/logistic" in r:
            return "§IV"
        is_page_or_screen = (
            fname.endswith("page.tsx")
            or any(seg in r for seg in ("mobile_app/", "(tabs)/", "(auth)/")))
        is_testish = ("__tests__" in r or "/e2e/" in r or "/playwright/" in r
                      or fname.endswith((".test.ts", ".test.tsx",
                                         ".spec.ts", ".spec.tsx")))
        if is_page_or_screen and not is_testish:
            return "§II"
        return "§I"
    route_ind = set()
    for route in symbols.get("routes", set()) | symbols.get("route_methods", set()):
        rl = route.lower()
        if "/admin" in rl: route_ind.add("admin")
        if "/supplier" in rl: route_ind.add("supplier")
        if "/logistic" in rl or "/logistor" in rl: route_ind.add("logistics")
        if "/customer" in rl: route_ind.add("customer")
    if "admin" in route_ind: return "§V"
    if "supplier" in route_ind: return "§III"
    if "logistics" in route_ind: return "§IV"
    if "customer" in route_ind: return "§II"
    name_ind = set()
    for name in (symbols.get("functions", set()) | symbols.get("components", set())
                 | symbols.get("classes", set())):
        nl = name.lower()
        if "admin" in nl: name_ind.add("admin")
        elif "supplier" in nl: name_ind.add("supplier")
        elif "logistic" in nl or "logistor" in nl: name_ind.add("logistics")
        elif nl.startswith("customer") or nl in ("cart", "checkout"): name_ind.add("customer")
    if "admin" in name_ind: return "§V"
    if "supplier" in name_ind: return "§III"
    if "logistics" in name_ind: return "§IV"
    if "customer" in name_ind: return "§II"
    return "§I"


def infer_domain_from_path(rel: str) -> str | None:
    """Infer feature domain key from file path."""
    parts = rel.split("/")
    if parts[0] == "backend":
        if parts[1] in ("controllers", "services", "routers", "models", "providers"):
            if len(parts) > 2 and parts[2] not in ("__init__.py",):
                return parts[2]
        elif parts[1] == "middleware":
            return "middleware"
        elif parts[1] == "jobs":
            return "jobs"
        elif parts[1] == "events":
            return "events"
    elif parts[0] == "frontend" and parts[1] == "web_app":
        if "src/app" in rel and len(parts) > 4:
            return parts[4]
        if "src/components" in rel and len(parts) > 4:
            return parts[4]
    elif parts[0] == "frontend" and parts[1] == "mobile_app":
        if len(parts) > 2 and parts[2] in ("app", "components"):
            if len(parts) > 3:
                return parts[3]
    return None


def infer_scope_from_section(section: str) -> str:
    """Infer scope string from section marker."""
    mapping = {
        "§I": "Internal",
        "§II": "Customer",
        "§III": "Supplier",
        "§IV": "Logistics",
        "§V": "Admin",
        "§VI": "Employee",
    }
    return mapping.get(section, "Internal")


def extract_file_operations(rel: str, symbols: dict) -> list:
    """Extract function/class/route operations from file symbols."""
    operations = []
    for name in sorted(symbols.get("functions", set())):
        if name.lower() not in GENERIC_TERMS and len(name) >= 3:
            operations.append({"file": rel, "name": name, "type": "function"})
    for name in sorted(symbols.get("classes", set())):
        if name not in ("Base", "BaseModel") and len(name) >= 3:
            operations.append({"file": rel, "name": name, "type": "class"})
    for route in sorted(symbols.get("routes", set())):
        operations.append({"file": rel, "name": route, "type": "route"})
    for route in sorted(symbols.get("route_methods", set())):
        operations.append({"file": rel, "name": route, "type": "route_method"})
    return operations


def extract_feature_stem(filename: str, domain: str) -> str:
    """Extract a normalized feature stem from a filename and its domain."""
    name = filename.replace('.py', '').replace('.tsx', '').replace('.ts', '')
    tokens = name.split('_')
    stop = {
        'service', 'controller', 'write', 'read', 'admin', 'create', 'update', 'delete',
        'list', 'routes', 'router', 'engine', 'helper', 'utils', 'util', 'package',
        'management', 'worker', 'core', 'public', 'system', 'api', 'delegator',
        'test', 'tests', 'spec', 'mock', 'stub', 'fixture', 'conftest',
        'page', 'layout', 'component', 'screen', 'module',
    }
    filtered = [t for t in tokens if t.lower() not in stop]
    deduped = []
    for t in filtered:
        if not deduped or t != deduped[-1]:
            deduped.append(t)
    stem = '_'.join(deduped)
    return stem if stem else domain


def _group_files_by_feature(repo: Repo) -> dict:
    """Group all scanned files into feature_stem buckets."""
    from collections import defaultdict
    groups = defaultdict(list)

    for rel, fi in repo.files.items():
        fname = Path(rel).name
        if fname == "__init__.py":
            continue

        domain = infer_domain_from_path(rel)
        if not domain:
            domain = fi["layer"].split("_")[-1] if "_" in fi["layer"] else fi["layer"]

        stem = None

        if rel.startswith("backend/"):
            if "/services/" in rel or "/controllers/" in rel:
                parts = rel.split("/")
                if len(parts) >= 4:
                    stem = extract_feature_stem(parts[3], domain)
            elif "/routers/" in rel:
                stem = extract_feature_stem(fname, "routers")
            elif "/models/" in rel:
                parts = rel.split("/")
                if len(parts) >= 4:
                    stem = extract_feature_stem(parts[3], domain)
            elif rel.startswith("backend/middleware/"):
                stem = extract_feature_stem(fname, "middleware")
            elif rel.startswith("backend/providers/"):
                parts = rel.split("/")
                if len(parts) >= 4:
                    stem = extract_feature_stem(parts[3], domain)
            elif rel.startswith("backend/jobs/"):
                parts = rel.split("/")
                if len(parts) >= 3:
                    stem = extract_feature_stem(parts[2], "jobs")
            elif rel.startswith("backend/events/"):
                stem = extract_feature_stem(fname, "events")
            elif rel.startswith("backend/db/"):
                stem = "database"
            elif rel.startswith("backend/utils/"):
                stem = extract_feature_stem(fname, "utils")
            elif rel.startswith("backend/tests/"):
                parts = rel.split("/")
                if len(parts) >= 3:
                    stem = extract_feature_stem(parts[2], "tests")
            elif rel.startswith("backend/scripts/"):
                stem = extract_feature_stem(fname, "scripts")
            else:
                stem = domain or "backend_other"
        elif rel.startswith("frontend/web_app"):
            if "/src/app/" in rel:
                parts = rel.split("/")
                for i, p in enumerate(parts):
                    if p == "src" and i + 2 < len(parts) and parts[i + 1] == "app":
                        section_dir = parts[i + 2] if len(parts) > i + 2 else ""
                        feature_dir = parts[i + 3] if len(parts) > i + 3 else fname
                        stem = feature_dir.replace('.tsx', '').replace('.ts', '')
                        break
            elif "/src/components/" in rel:
                parts = rel.split("/")
                for i, p in enumerate(parts):
                    if p == "components" and i + 1 < len(parts):
                        comp_dir = parts[i + 1].replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')
                        if comp_dir not in ("ui", "shared"):
                            stem = comp_dir
                        else:
                            stem = "ui_components"
                        break
            elif "/src/lib/" in rel or "/src/hooks/" in rel:
                stem = extract_feature_stem(fname, "lib")
            elif "/src/__tests__/" in rel:
                parts = rel.split("/")
                if len(parts) >= 4:
                    stem = extract_feature_stem(parts[3], "tests")
            elif "/e2e/" in rel:
                stem = "e2e"
            else:
                stem = domain or "frontend_other"
        elif rel.startswith("frontend/mobile_app"):
            if "/app/" in rel:
                parts = rel.split("/")
                for i, p in enumerate(parts):
                    if p == "app" and i + 1 < len(parts):
                        feature_dir = parts[i + 2] if len(parts) > i + 2 else fname
                        stem = feature_dir.replace('.tsx', '').replace('.ts', '')
                        break
            elif "/components/" in rel:
                parts = rel.split("/")
                for i, p in enumerate(parts):
                    if p == "components" and i + 1 < len(parts):
                        stem = parts[i + 1].replace('.tsx', '').replace('.ts', '').replace('.jsx', '').replace('.js', '')
                        break
            elif "/lib/" in rel:
                stem = extract_feature_stem(fname, "lib")
            elif "/e2e/" in rel:
                stem = "e2e"
            else:
                stem = domain or "mobile_other"
        else:
            stem = domain or "other"

        if stem:
            groups[stem].append(rel)

    return groups


def _infer_section_from_files(files, repo) -> str:
    """Infer the most appropriate section for a group of files."""
    from collections import Counter
    section_counts = Counter()
    SECTION_PREFIXES = {
        "admin_": "§V", "supplier_": "§III",
        "logistics_": "§IV", "logistic_": "§IV", "logistor_": "§IV",
        "customer_": "§II", "employee_": "§VI", "hr_": "§VI",
    }
    SECTION_ORDER = {"§I": 0, "§II": 1, "§III": 2, "§IV": 3, "§V": 4, "§VI": 5}
    for rel in files:
        fi = repo.files[rel]
        r = rel.lower()
        fname = Path(rel).name.lower()
        stem_key = fname.replace('.py', '').replace('.tsx', '').replace('.ts', '')

        path_sec = None
        if "/admin/" in r or fname.endswith("_admin.py"):
            path_sec = "§V"
        elif "/supplier/" in r or "/supplier_" in r:
            path_sec = "§III"
        elif "/logistic" in r or "/logistics/" in r or "/logistics_" in r or "/logistor/" in r:
            path_sec = "§IV"
        elif "/customer/" in r or "/customer_" in r:
            path_sec = "§II"
        elif "/employee/" in r or "/employee_" in r or "/hr/" in r:
            path_sec = "§VI"
        if path_sec:
            section_counts[path_sec] += 10

        for prefix, sec in SECTION_PREFIXES.items():
            if stem_key.startswith(prefix):
                section_counts[sec] += 5
                break

        for route in fi["symbols"].get("routes", set()) | fi["symbols"].get("route_methods", set()):
            rl = route.lower()
            if "/admin" in rl: section_counts["§V"] += 3
            if "/supplier" in rl: section_counts["§III"] += 3
            if "/logistic" in rl or "/logistor" in rl: section_counts["§IV"] += 3
            if "/customer" in rl: section_counts["§II"] += 3

        for name in (fi["symbols"].get("functions", set()) | fi["symbols"].get("classes", set())):
            nl = name.lower()
            for prefix, sec in SECTION_PREFIXES.items():
                clean = prefix.rstrip("_")
                if clean in nl:
                    section_counts[sec] += 2
                    break

        role = fi["role"]
        if role != "§I" or not any(v > 0 for v in section_counts.values()):
            section_counts[role] += 1

    if not section_counts:
        return "§I"
    best_sec = max(section_counts.items(), key=lambda x: (x[1], -SECTION_ORDER.get(x[0], 99)))
    return best_sec[0]


def _merge_similar_stems(stems: dict) -> dict:
    """Merge stems that share a common prefix (e.g., orders + orders_status -> orders)."""
    sorted_stems = sorted(stems.items(), key=lambda x: -len(x[0]))
    merged = {}
    merged_map = {}

    for stem, files in sorted_stems:
        if stem in merged_map:
            continue
        target = stem
        target_files = list(files)
        for other_stem, other_files in sorted_stems:
            if other_stem == stem or other_stem in merged_map:
                continue
            if target != other_stem and (other_stem.startswith(target + "_") or target.startswith(other_stem + "_")):
                if len(target) <= len(other_stem):
                    target_files.extend(other_files)
                    merged_map[other_stem] = target
        merged[target] = target_files

    return merged



def discover_features_from_codebase(repo: Repo, matched_files: set = None) -> list:
    """Discover features from the complete codebase by grouping files into functional modules."""
    if matched_files is None:
        matched_files = set()

    DISCOVERY_GENERIC = GENERIC_TERMS | {
        "database", "db", "script", "scripts", "e2e", "migration", "migrations",
        "test", "tests", "conftest", "init", "main", "base", "core",
        "utils", "util", "helpers", "helper", "constants", "config",
        "other", "backend_other", "frontend_other", "mobile_other",
        "ui_components", "components", "shared", "lib", "hooks",
        "models", "schemas", "middleware", "providers", "jobs", "events",
        "security", "audit", "gateway", "gateways", "unknown",
        "common", "system", "api", "public", "tools",
        "auto", "comm", "layout", "bulk", "map", "fallback", "misc",
        "add", "schema", "declarations", "cross", "border", "addresses",
        "flash", "sale", "iam", "risk", "shipment", "bank",
        "logisticsPayoutInsights", "supplierPayoutsScreen",
    }

    LOW_QUALITY_TERMS = {
        "auto", "comm", "layout", "bulk", "map", "fallback", "misc",
        "add", "schema", "declarations", "cross", "border", "addresses",
        "flash", "sale", "iam", "risk", "shipment", "bank",
        "logisticsPayoutInsights", "supplierPayoutsScreen",
        "csrf", "imports", "travel", "whatsapp", "encryption",
        "unsubscribe", "code", "signaturepad", "logo", "callback",
        "cartstore", "currencystore", "toastcontainer", "recentlyviewed",
        "labels", "slug", "credibility",
        "routers", "staff", "delegators", "audit-logs", "geography audit", "media geography",
    }

    groups = _group_files_by_feature(repo)
    merged_groups = _merge_similar_stems(groups)
    discovered = []

    candidates = []
    for stem, files in sorted(merged_groups.items()):
        if stem.lower() in DISCOVERY_GENERIC or len(stem) < 3:
            continue
        if stem.lower().endswith((".tsx", ".ts", ".jsx", ".js", ".py")):
            continue
        non_test_files = [f for f in files if not any(t in f.lower() for t in ["/test", "/__tests__", ".test.", ".spec.", "conftest", "playwright"])]
        if not non_test_files:
            continue

        name = stem.replace('_', ' ').title()
        name = re.sub(r'\s+', ' ', name).strip()

        section = _infer_section_from_files(files, repo)
        section_order = {"§I": 0, "§II": 1, "§III": 2, "§IV": 3, "§V": 4, "§VI": 5}
        primary_section = section_order.get(section, 99)
        scope = infer_scope_from_section(section)

        candidates.append({
            "stem": stem,
            "name": name,
            "files": files,
            "non_test_files": non_test_files,
            "section": section,
            "primary_section": primary_section,
            "scope": scope,
            "domain": _extract_domain_from_stem(stem),
            "quality": len(non_test_files) * 2 + len([f for f in files if f.lower().endswith(('.py', '.ts', '.tsx'))]) * 0.5,
        })

    candidates.sort(key=lambda c: (c["primary_section"], c["domain"].lower(), c["stem"].lower()))
    seen_stems = set()
    for cand in candidates:
        stem_lower = cand["stem"].lower()
        if stem_lower in seen_stems:
            continue
        seen_stems.add(stem_lower)

        stem = cand["stem"]
        domain = cand["domain"]
        files = cand["files"]
        non_test_files = cand["non_test_files"]
        section = cand["section"]
        primary_section = cand["primary_section"]
        scope = cand["scope"]
        name = cand["name"]

        layer_files = defaultdict(set)
        operations = []
        tables = {}
        routes = []
        statuses = []
        caps = []
        test_layers = {"test_backend": 0, "test_web": 0, "test_mobile": 0, "e2e": 0}

        for rel in files:
            fi = repo.files[rel]
            layer_files[fi["layer"]].add(rel)
            operations.extend(extract_file_operations(rel, fi["symbols"]))

            if fi["layer"] == "backend_model":
                for tn in fi["symbols"].get("tablename", set()):
                    tables[tn] = {"schema": None, "base": tn, "found": True, "evidence": [rel], "schema_ok": False}

            for rm in fi["symbols"].get("route_methods", set()):
                parts = rm.split(" ", 1)
                if len(parts) == 2:
                    routes.append({"method": parts[0], "path": parts[1], "found": True, "evidence": [rel]})

            text_low = fi["low"]
            for st in ["pending", "processing", "completed", "cancelled", "active", "inactive",
                       "approved", "rejected", "delivered", "shipped", "packed", "confirmed",
                       "paid", "failed", "delayed", "returned", "refunded"]:
                if st in text_low:
                    norm = st.upper().replace(" ", "_")
                    if not any(s["status"] == norm for s in statuses):
                        statuses.append({"status": norm, "found": True, "evidence": [rel]})

            for func_name in fi["symbols"].get("functions", set()):
                if func_name.lower() not in GENERIC_TERMS and len(func_name) >= 3:
                    caps.append({"phrase": func_name, "found": True, "evidence": [rel]})
            for cls_name in fi["symbols"].get("classes", set()):
                if cls_name not in ("Base", "BaseModel") and len(cls_name) >= 3:
                    caps.append({"phrase": cls_name, "found": True, "evidence": [rel]})

            if fi["layer"] in test_layers:
                test_layers[fi["layer"]] += 1

        db_score = min(1.0, len(tables) / 5.0) if tables else None
        api_score = min(1.0, len(routes) / 10.0) if routes else None
        state_score = min(1.0, len(statuses) / 5.0) if statuses else None
        cap_score = min(1.0, len(caps) / 10.0) if caps else None
        has_web = bool(layer_files.get("web_page"))
        has_mobile = bool(layer_files.get("mobile_screen"))
        sec_score = (1.0 if has_web else 0.0) + (1.0 if has_mobile else 0.0)
        if has_web or has_mobile:
            sec_score = sec_score / 2.0
        else:
            sec_score = None
        test_score = sum(1 for v in test_layers.values() if v > 0) / 4.0

        comps = {
            "db": db_score, "api": api_score, "state": state_score,
            "capability": cap_score, "sections": sec_score,
            "tests": test_score, "steps": None,
        }
        present = {k: v for k, v in comps.items() if v is not None}
        wsum = sum(WEIGHTS[k] for k in present)
        overall = (sum(WEIGHTS[k] * v for k, v in present.items()) / wsum * 100.0) if wsum else 0.0

        matched = {}
        for rel in files:
            fi = repo.files[rel]
            matched[rel] = {"reasons": ["discovered"], "specific": 0, "generic": 0, "semantic": None, "layer": fi["layer"], "role": fi["role"]}

        discovered.append({
            "spec": {
                "id": f"DISCOVERED_{section}_{stem}",
                "name": name,
                "scope": scope,
                "section": section,
                "weight": 2,
                "primary_section": primary_section,
                "sections": {},
                "todo_ref": "—",
                "terms": [stem] + [w for w in name.lower().split() if w not in LOWER_STOP and len(w) >= 3],
            },
            "scores": {
                "db": db_score, "api": api_score, "state": state_score,
                "capability": cap_score, "sections": sec_score,
                "tests": test_score, "steps": None,
                "overall": round(overall, 1),
            },
            "matched": matched,
            "layer_files": {k: sorted(v) for k, v in layer_files.items()},
            "role_files": {section: sorted(files)},
            "gaps": {},
            "dead_count": 0,
            "dead_penalty": 0.0,
            "semantic_enabled": False,
            "primary_section": primary_section,
            "domain": domain,
            "stem": stem,
            "discovered": True,
            "operations": operations[:100],
            "tables": tables,
            "routes": routes,
            "statuses": statuses,
            "idents": [],
            "caps": caps[:50],
            "steps": [],
            "test_layers": test_layers,
            "test_evidence": {},
            "sections": {},
        })

    return discovered


# ============================================================================
# REPO SCAN
# ============================================================================
class Repo:
    def __init__(self, root: Path):
        self.root = root
        self.files = {}
        self._scan()

    def _walk(self, directory):
        try:
            with os.scandir(directory) as it:
                entries = list(it)
        except (PermissionError, OSError, FileNotFoundError):
            return
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in EXCLUDE_DIRS or entry.name.startswith("."):
                        continue
                    if len(entry.path) > MAX_PATH_LEN:
                        continue
                    yield from self._walk(entry.path)
                elif entry.is_file(follow_symlinks=False):
                    yield Path(entry.path)
            except (PermissionError, OSError, FileNotFoundError):
                continue

    def _scan(self):
        count = 0
        for base in ("backend", "frontend"):
            bd = self.root / base
            if not bd.exists():
                continue
            for p in self._walk(bd):
                if p.suffix not in EXTS:
                    continue
                try:
                    if p.stat().st_size > MAX_CHARS:
                        continue
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                rel = str(p.relative_to(self.root)).replace("\\", "/")
                symbols = (extract_python_symbols(text, rel) if p.suffix == ".py"
                           else extract_ts_symbols(text, rel))
                
                # OPTIMIZATION: Don't store raw `text` in memory to save RAM.
                # Only store `low` for fast keyword matching, and the path for on-demand reading.
                self.files[rel] = {
                    "low": text.lower(),
                    "symbols": symbols,
                    "layer": classify_by_content(rel, symbols),
                    "role": get_role_scope(rel, symbols),
                    "path": p,  # Keep path to read full text on-demand
                    "size": p.stat().st_size
                }
                count += 1
        print(f"  Scanned {count} source files")


# ============================================================================
# SPEC PARSER (with F3/F4 fixes)
# ============================================================================
def norm_status(tok: str) -> str:
    return re.sub(r"\s+", "_", tok.strip()).upper()

def status_ok(tok: str) -> bool:
    n = norm_status(tok)
    if len(n) < 5:
        return False
    words = n.split("_")
    return all(w not in UPPER_STOP and len(w) >= 2 for w in words)

def norm_route_path(path: str) -> str:
    return re.sub(r"\{[^}]*\}", "{}", path.strip())

def esc(s):
    return str(s).replace("|", "/")

def short_path(rel: str) -> str:
    prefixes = [
        "frontend/web_app/src/app/", "frontend/web_app/src/components/",
        "frontend/web_app/src/__tests__/", "frontend/web_app/src/",
        "frontend/mobile_app/app/", "frontend/mobile_app/lib/__tests__/",
        "frontend/mobile_app/", "frontend/shared/src/", "frontend/",
        "backend/controllers/", "backend/services/", "backend/routers/",
        "backend/models/", "backend/db/", "backend/tests/", "backend/",
    ]
    short = rel
    for pre in prefixes:
        if rel.startswith(pre):
            short = rel[len(pre):]
            break
    if short.endswith("page.tsx"):
        if "frontend/web_app" in rel:
            return "web_app/" + short
        if "frontend/mobile_app" in rel:
            return "mobile_app/" + short
    return short


def _classify_backtick(tok):
    t = tok.strip()
    if not t or len(t) < 3 or len(t) > 120:
        return None
    # F3: skip non-code file references
    _, ext = os.path.splitext(t)
    if ext.lower() in NON_CODE_EXTENSIONS:
        return None
    m = re.match(r"^(GET|POST|PUT|PATCH|DELETE)\s+(/\S+)$", t, re.I)
    if m:
        return ("route", m.group(1).upper(), m.group(2))
    if t.startswith("/") and " " not in t:
        return ("route", None, t)
    # F4: don't parse filenames as schema.table
    if re.search(r'\.\w+$', t) and re.search(r'\.(py|ts|tsx|js|yaml|yml|json|md)$', t):
        return ("ident", t)
    m = re.match(r"^([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)$", t)
    if m:
        return ("table", m.group(1), m.group(2))
    clean = t.strip("`")
    if re.match(r"^[A-Z][A-Z0-9 _]{3,}$", clean) and status_ok(clean):
        return ("status", norm_status(clean))
    if re.match(r"^[a-z][a-z0-9_]{3,}$", t):
        if "_" in t and TABLEISH_RE.search(t):
            return ("table", None, t)
        return ("ident", t)
    if re.match(r"^[A-Z][A-Za-z0-9]{3,}$", t):
        return ("ident", t)
    return None


def _extract_from_text(text):
    out = {"tables": {}, "routes": [], "statuses": set(), "idents": set(), "caps": []}
    for m in re.finditer(r"`([^`\n]+)`", text):
        c = _classify_backtick(m.group(1))
        if not c:
            continue
        if c[0] == "route":
            entry = (c[1], c[2], norm_route_path(c[2]))
            if entry not in out["routes"]:
                out["routes"].append(entry)
        elif c[0] == "table":
            out["tables"][c[2]] = {"schema": c[1], "base": c[2]}
        elif c[0] == "status":
            out["statuses"].add(c[1])
        elif c[0] == "ident":
            out["idents"].add(c[1])
    for m in re.finditer(r"([A-Z][A-Z0-9_]{3,})\s*-->", text):
        if status_ok(m.group(1)):
            out["statuses"].add(norm_status(m.group(1)))
    for m in re.finditer(r"-->\s*\|?([A-Z][A-Z0-9_]{3,})", text):
        if status_ok(m.group(1)):
            out["statuses"].add(norm_status(m.group(1)))
    for line in text.splitlines():
        if "→" in line or "-->" in line:
            for m in re.finditer(r"\b[A-Z][A-Z0-9]{2,}(?:[ _][A-Z0-9]{2,})*\b", line):
                if status_ok(m.group(0)):
                    out["statuses"].add(norm_status(m.group(0)))
    for m in re.finditer(r"\*\*([^*\n]{4,90})\*\*", text):
        phrase = m.group(1).strip().strip("`").strip()
        if re.match(r"^[A-Z][A-Z0-9 _]{3,}$", phrase) and status_ok(phrase):
            out["statuses"].add(norm_status(phrase))
            continue
        words = [w for w in re.findall(r"[a-z]{3,}", phrase.lower())
                 if len(w) >= 4 and w not in LOWER_STOP]
        if len(words) >= 2:
            out["caps"].append(phrase)
    return out


def parse_feature_spec(feat: dict) -> dict:
    desc = feat.get("description", "") or ""
    spec = _extract_from_text(desc)
    steps = []
    matches = list(re.finditer(r"\*\*Step\s+(\d+)\s*[—–\-]\s*(.+?)\*\*", desc))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(desc)
        block = desc[start:end]
        title = m.group(2).strip().rstrip(".").strip()
        done_m = re.search(r"\*Done when:\*\s*(.+?)(?:\n|$)", block)
        cps = _extract_from_text(block)
        steps.append({
            "num": int(m.group(1)), "title": title,
            "done_when": done_m.group(1).strip() if done_m else "",
            "cps": cps,
        })
    sections = {}
    raw_sections = feat.get("sections", {}) or {}
    if isinstance(raw_sections, str):
        parsed = {}
        for m in re.finditer(r'(§[IVX]+)\s*[:\-]\s*(.+?)(?=§[IVX]+\s*[:\-]|$)', raw_sections, re.DOTALL):
            key = m.group(1).strip()
            prose = m.group(2).strip()
            k = key.replace("§", "").strip()
            key_norm = "§" + k.upper() if k.upper() in ("I", "II", "III", "IV", "V") else key
            parsed[key_norm] = prose
        if not parsed:
            for line in raw_sections.splitlines():
                line = line.strip()
                if not line:
                    continue
                m2 = re.match(r'(§[IVX]+)\s*[:\-]\s*(.+)', line)
                if m2:
                    key = m2.group(1).strip()
                    prose = m2.group(2).strip()
                    k = key.replace("§", "").strip()
                    key_norm = "§" + k.upper() if k.upper() in ("I", "II", "III", "IV", "V") else key
                    parsed[key_norm] = prose
        raw_sections = parsed
    for key, prose in raw_sections.items():
        k = str(key).replace("§", "").strip()
        key_norm = "§" + k.upper() if k.upper() in ("I", "II", "III", "IV", "V") else str(key)
        cps = _extract_from_text(str(prose))
        sections[key_norm] = {"prose": str(prose).strip(), "cps": cps}
    if not sections:
        for part in str(feat.get("scope", "")).split("·"):
            tag = part.strip().lower()
            if tag in SCOPE_TO_SECTION:
                sk = SCOPE_TO_SECTION[tag]
                sections.setdefault(sk, {"prose": desc[:400], "cps": _extract_from_text(desc[:1500])})
    terms = set()
    for t in spec["idents"]:
        terms.add(t.lower())
    for s in spec["statuses"]:
        terms.add(s.lower())
    for tbl in spec["tables"].values():
        terms.add(tbl["base"].lower())
    for _m, p, _np in spec["routes"]:
        segs = [x for x in p.split("/") if x and not x.startswith("{")]
        if segs:
            terms.add(segs[-1].lower())
    for w in re.findall(r"[A-Za-z]{4,}", feat.get("name", "")):
        if w.lower() not in LOWER_STOP:
            terms.add(w.lower())
    return {
        "id": feat.get("id", "?"),
        "name": feat.get("name", "Unnamed"),
        "scope": feat.get("scope", ""),
        "section": feat.get("matrix_section", ""),
        "todo_ref": feat.get("todo_ref", "—"),
        "weight": int(feat.get("weight", 5)),
        "desc": desc,
        "tables": spec["tables"],
        "routes": spec["routes"],
        "statuses": sorted(spec["statuses"]),
        "idents": sorted(spec["idents"]),
        "caps": spec["caps"],
        "steps": steps,
        "sections": sections,
        "terms": sorted(terms),
    }


# ============================================================================
# REGISTRY
# ============================================================================
class Registry:
    def __init__(self, repo: Repo):
        self.repo = repo
        self.tablenames = defaultdict(set)
        self.model_classes = defaultdict(set)
        self.migration_tables = defaultdict(set)
        self.qualified_hits = defaultdict(set)
        self.routes = defaultdict(set)
        self.route_paths = defaultdict(set)
        self._build()

    def _build(self):
        for rel, finfo in self.repo.files.items():
            sym = finfo["symbols"]
            for tn in sym.get("tablename", set()):
                self.tablenames[tn].add(rel)
            if finfo["layer"] == "backend_model":
                for c in sym.get("classes", set()):
                    if c not in ("Base",) and not c.endswith("Mixin"):
                        self.model_classes[c].add(rel)
            if finfo["layer"] == "migration":
                # Read from disk on-demand for migrations only
                try:
                    m_text = finfo["path"].read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    m_text = ""
                for m in re.finditer(r'(?:create_table|Table)\(\s*["\']([\w.]+)["\']', m_text):
                    self.migration_tables[m.group(1).split(".")[-1]].add(rel)
                    self.qualified_hits[m.group(1)].add(rel)
            for rm in sym.get("route_methods", set()):
                parts = rm.split(" ", 1)
                if len(parts) == 2:
                    np = norm_route_path(parts[1])
                    self.routes[(parts[0], np)].add(rel)
                    self.route_paths[np].add(rel)
        for rel, finfo in self.repo.files.items():
            for m in re.finditer(r'["\']([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)["\']',
                                 finfo["low"]):
                self.qualified_hits[m.group(1)].add(rel)


    def find_table(self, schema, base):
        evidence = set()
        found = False
        schema_verified = False
        if base in self.tablenames:
            found = True
            evidence |= self.tablenames[base]
        if base in self.migration_tables:
            found = True
            evidence |= self.migration_tables[base]
        qual = f"{schema}.{base}" if schema else None
        if qual and qual in self.qualified_hits:
            found = True
            schema_verified = True
            evidence |= self.qualified_hits[qual]
        singular = base[:-1] if base.endswith("s") else base
        for cls, files in self.model_classes.items():
            if cls.lower() in (base, singular, base.replace("_", "")):
                found = True
                evidence |= files
        return found, sorted(evidence)[:3], schema_verified

    def find_route(self, method, norm_path):
        evidence = set()
        if method:
            evidence |= self.routes.get((method, norm_path), set())
        else:
            evidence |= self.route_paths.get(norm_path, set())
        if not evidence:
            segs = [s for s in norm_path.split("/") if s]
            if len(segs) >= 2:
                tail = "/" + "/".join(segs[-2:])
                for np, files in self.route_paths.items():
                    if np.endswith(tail):
                        evidence |= files
        return bool(evidence), sorted(evidence)[:3]


# ============================================================================
# VERIFICATION (with Ollama semantic layer)
# ============================================================================

# Assumes the following are defined in your global scope/constants:
# LOWER_STOP, GENERIC_TERMS, MAX_CONTEXT_CHARS, COSINE_THRESHOLD, WEIGHTS, MAX_CELL_FILES, OllamaClient

def verify_feature(repo, reg, spec, ollama: 'OllamaClient'):
    files = repo.files
    gaps = defaultdict(list)

    # --- Semantic embedding of feature description ---
    feature_emb = None
    if ollama.can_embed:
        feature_emb = ollama.embed(f"{spec['name']}: {spec['desc'][:2000]}")

    # --- DB tables ---
    table_results = {}
    for base, info in spec["tables"].items():
        found, evidence, schema_ok = reg.find_table(info.get("schema"), base)
        table_results[base] = {"found": found, "evidence": evidence,
                               "schema_ok": schema_ok, "schema": info.get("schema")}
        if not found:
            gaps["db"].append(base)
    db_score = (sum(1 for t in table_results.values() if t["found"])
                / len(table_results)) if table_results else None

    # --- API routes ---
    route_results = []
    for method, path, np in spec["routes"]:
        found, evidence = reg.find_route(method, np)
        route_results.append({"method": method, "path": path, "found": found,
                              "evidence": evidence})
        if not found:
            gaps["api"].append(f"{method or 'ANY'} {path}")
    api_score = (sum(1 for r in route_results if r["found"])
                 / len(route_results)) if route_results else None

    # --- Statuses (Use lowercase memory instead of raw text) ---
    status_results = []
    for st in spec["statuses"]:
        variant_low = st.lower().replace("_", " ")
        st_low = st.lower()
        hits = []
        for rel, fi in files.items():
            if variant_low in fi["low"] or st_low in fi["low"]:
                hits.append(rel)
            if len(hits) >= 3:
                break
        status_results.append({"status": st, "found": bool(hits), "evidence": hits[:3]})
        if not hits:
            gaps["state"].append(st)
    state_score = (sum(1 for s in status_results if s["found"])
                   / len(status_results)) if status_results else None
    
    # --- Identifiers ---
    ident_results = []
    for ident in spec["idents"]:
        hits = [rel for rel, fi in files.items() if ident.lower() in fi["low"]][:3]
        ident_results.append({"ident": ident, "found": bool(hits), "evidence": hits})
        if not hits:
            gaps["ident"].append(ident)

    # --- Capabilities (with optional LLM verification) ---
    def cap_found(phrase):
        p = phrase.lower()
        variants = {p, p.replace(" ", "_"), p.replace("-", " "), p.replace("-", "_")}
        camel = re.sub(r"[\s\-]+(\w)", lambda x: x.group(1).upper(), p)
        variants.add(camel.replace(" ", ""))
        words = [w for w in re.findall(r"[a-z]{3,}", p)
                 if len(w) >= 4 and w not in LOWER_STOP]
        for rel, fi in files.items():
            if any(v in fi["low"] for v in variants):
                return rel
            if words and all(w in fi["low"] for w in words):
                return rel
        return None

    cap_results = []
    for phrase in spec["caps"]:
        hit = cap_found(phrase)
        llm_check = None
        if hit and ollama.can_llm:
            try:
                # Read raw text on-demand instead of keeping it in RAM
                code_ctx = Path(files[hit]["path"]).read_text(encoding="utf-8", errors="ignore")[:MAX_CONTEXT_CHARS]
            except Exception:
                code_ctx = ""
            llm_check = ollama.verify_capability(phrase, code_ctx)
            if llm_check.get("verified") is False and llm_check.get("confidence", 0) > 0.7:
                hit = None  # LLM says not actually implemented
        cap_results.append({
            "phrase": phrase, "found": bool(hit),
            "evidence": [hit] if hit else [],
            "llm": llm_check
        })
        if not hit:
            gaps["capability"].append(phrase)
    cap_score = (sum(1 for c in cap_results if c["found"])
                 / len(cap_results)) if cap_results else None

    # --- File matching with semantic scoring ---
    specific_terms = set()
    generic_terms = set()
    for t in spec["idents"]:
        tl = t.lower()
        if tl in GENERIC_TERMS:
            generic_terms.add(t)
        else:
            specific_terms.add(t)
    for s in spec["statuses"]:
        if "_" in s or len(s) >= 9:
            specific_terms.add(s)
        else:
            generic_terms.add(s)
    for tbl in spec["tables"].values():
        specific_terms.add(tbl["base"])
    for w in re.findall(r"[A-Za-z]{4,}", spec["name"]):
        if w.lower() not in LOWER_STOP:
            specific_terms.add(w)
    for g in GENERIC_TERMS:
        if len(g) >= 4 and re.search(r"\b" + re.escape(g) + r"\b", spec["desc"].lower()):
            generic_terms.add(g)

    # --- File matching with semantic scoring (OPTIMIZED) ---
    file_hits = {}
    
    # PASS 1: Keyword filtering to reduce Ollama calls
    keyword_candidates = []
    for rel, fi in files.items():
        low = fi["low"]
        spec_count = sum(1 for t in specific_terms if t.lower() in low)
        gen_count = sum(1 for t in generic_terms if t.lower() in low)
        
        if spec_count >= 1 or gen_count >= 2:
            keyword_candidates.append((rel, fi, spec_count, gen_count))

    # PASS 2: Semantic scoring ONLY on candidates (Saves massive CPU time)
    for rel, fi, spec_count, gen_count in keyword_candidates:
        semantic_score = None
        if feature_emb and ollama.can_embed:
            try:
                # Read raw text on-demand instead of keeping it in RAM
                raw_text = Path(fi["path"]).read_text(encoding="utf-8", errors="ignore")
                file_summary = f"{rel}: {raw_text[:1500]}"
                file_emb = ollama.embed(file_summary)
                if file_emb:
                    semantic_score = ollama.cosine_similarity(feature_emb, file_emb)
                    if semantic_score < COSINE_THRESHOLD:
                        continue  # F7: skip irrelevant files
            except Exception:
                continue

        reasons = []
        if spec_count: reasons.append(f"specific×{spec_count}")
        if gen_count: reasons.append(f"generic×{gen_count}")
        if semantic_score is not None: reasons.append(f"semantic={semantic_score:.3f}")
        
        file_hits[rel] = {
            "reasons": reasons,
            "specific": spec_count,
            "generic": gen_count,
            "semantic": semantic_score,
            "layer": fi["layer"],
            "role": fi["role"],
        }

    matched = file_hits
    layer_files = defaultdict(set)
    role_files = defaultdict(set)
    for fpath, h in matched.items():
        layer_files[h["layer"] or "other"].add(fpath)
        role_files[h["role"] or "§I"].add(fpath)

    # --- Sections ---
    section_results = {}
    for sk, sdata in spec["sections"].items():
        cps = sdata["cps"]
        terms = set(t.lower() for t in cps["idents"])
        terms |= set(s.lower() for s in cps["statuses"])
        terms |= set(tbl["base"].lower() for tbl in cps["tables"].values())
        if not terms:
            terms = set(spec.get("terms", []))
        role_files_sk = [rel for rel, fi in files.items() if fi["role"] == sk]
        if role_files_sk:
            hit_terms = set()
            for rel in role_files_sk:
                low = files[rel]["low"]
                for t in terms:
                    if t in low:
                        hit_terms.add(t)
            term_cov = len(hit_terms) / len(terms) if terms else 0.0
        else:
            term_cov = 0.0
        ui_web = any(files[rel]["layer"] == "web_page" and
                     any(t in files[rel]["low"] for t in terms)
                     for rel in role_files_sk)
        ui_mobile = any(files[rel]["layer"] in ("mobile_screen", "mobile_component") and
                        any(t in files[rel]["low"] for t in terms)
                        for rel in role_files_sk)
        key_files = sorted(
            (rel for rel in role_files_sk if any(t in files[rel]["low"] for t in terms)),
            key=lambda r: -matched.get(r, {}).get("specific", 0))[:MAX_CELL_FILES]
        score = 0.5 * term_cov + 0.25 * (1.0 if ui_web else 0.0) + 0.25 * (1.0 if ui_mobile else 0.0)
        section_results[sk] = {
            "score": round(score * 100, 1),
            "term_cov": round(term_cov * 100, 1),
            "ui_web": ui_web, "ui_mobile": ui_mobile,
            "files": key_files,
            "prose": sdata["prose"],
            "n_files": len([r for r in role_files_sk if r in matched]),
        }
    sec_score = (sum(s["score"] for s in section_results.values())
                 / len(section_results) / 100.0) if section_results else None

    # --- Tests (F5: require ≥3 specific terms) ---
    test_layers = {"test_backend": 0, "test_web": 0, "test_mobile": 0, "e2e": 0}
    test_evidence = defaultdict(list)
    specific_lower = {t.lower() for t in specific_terms}
    for rel, fi in files.items():
        if fi["layer"] in test_layers:
            low = fi["low"]
            spec_match_count = sum(1 for t in specific_lower if t in low)
            if spec_match_count >= 3:  # F5: stricter test matching
                test_layers[fi["layer"]] += 1
                if len(test_evidence[fi["layer"]]) < 5:
                    test_evidence[fi["layer"]].append(rel)
    test_score = sum(1 for v in test_layers.values() if v > 0) / 4.0

    # --- Steps ---
    step_results = []
    for step in spec["steps"]:
        cps = step["cps"]
        checks = []
        for base, info in cps["tables"].items():
            f, _e, _s = reg.find_table(info.get("schema"), base)
            checks.append(f)
        for method, path, np in cps["routes"]:
            f, _e = reg.find_route(method, np)
            checks.append(f)
        for st in cps["statuses"]:
            checks.append(any(st.lower() in fi["low"] or st.replace("_", " ").lower() in fi["low"]
                              for fi in files.values()))
        for ident in cps["idents"]:
            checks.append(any(ident.lower() in fi["low"] for fi in files.values()))
        for phrase in cps["caps"]:
            checks.append(bool(cap_found(phrase)))
        if checks:
            sc = sum(1 for c in checks if c) / len(checks)
        else:
            words = [w.lower() for w in re.findall(r"[A-Za-z]{4,}", step["title"])
                     if w.lower() not in LOWER_STOP]
            sc = 1.0 if words and all(any(w in fi["low"] for fi in files.values())
                                      for w in words) else 0.0
        step_results.append({"num": step["num"], "title": step["title"],
                             "done_when": step["done_when"],
                             "score": round(sc * 100, 1), "n_checks": len(checks)})
    steps_score = (sum(s["score"] for s in step_results)
                   / len(step_results) / 100.0) if step_results else None

    # --- Dead file penalty ---
    import_stems = set()
    for fi in files.values():
        for imp in fi["symbols"].get("imports", set()):
            import_stems.add(imp.split(".")[-1])
    exempt_layers = {"web_page", "mobile_screen", "e2e", "migration",
                     "test_backend", "test_web", "test_mobile",
                     "backend_core", "frontend_script", "backend_script"}
    dead_count = 0
    for fpath, h in matched.items():
        if h["layer"] in exempt_layers:
            continue
        stem = Path(fpath).stem
        if stem in ("__init__", "main", "conftest"):
            continue
        if stem not in import_stems:
            dead_count += 1
    dead_penalty = min(20.0, dead_count * 0.5)

    # --- Overall ---
    comps = {
        "db": db_score, "api": api_score, "state": state_score,
        "capability": cap_score, "sections": sec_score,
        "tests": test_score, "steps": steps_score,
    }
    present = {k: v for k, v in comps.items() if v is not None}
    wsum = sum(WEIGHTS[k] for k in present)
    overall = (sum(WEIGHTS[k] * v for k, v in present.items()) / wsum
               if wsum else 0.0) * 100.0
    overall = max(0.0, overall - dead_penalty)

    return {
        "spec": spec,
        "tables": table_results,
        "routes": route_results,
        "statuses": status_results,
        "idents": ident_results,
        "caps": cap_results,
        "sections": section_results,
        "steps": step_results,
        "test_layers": test_layers,
        "test_evidence": dict(test_evidence),
        "matched": matched,
        "layer_files": {k: sorted(v) for k, v in layer_files.items()},
        "role_files": {k: sorted(v) for k, v in role_files.items()},
        "gaps": dict(gaps),
        "dead_count": dead_count,
        "dead_penalty": dead_penalty,
        "semantic_enabled": feature_emb is not None,
        "scores": {
            "db": db_score, "api": api_score, "state": state_score,
            "capability": cap_score, "sections": sec_score,
            "tests": test_score, "steps": steps_score,
            "overall": round(overall, 1),
        },
    }

# ============================================================================
# REPORT GENERATION
# ============================================================================
def pct(v):
    return "n/a" if v is None else f"{v * 100:.1f}%"

def status_emoji(p):
    if p is None: return "—"
    v = p * 100 if p <= 1 else p
    return "✅" if v >= 80 else "🟡" if v >= 50 else "❌"

def in_section(result, key, tags):
    scope_parts = [s.strip() for s in result["spec"]["scope"].split("·")]
    scope_match = any(t in scope_parts for t in tags) or key in result["spec"]["section"]
    if not scope_match and key not in result["spec"]["sections"]:
        return False
    return key in result["role_files"]

def fmt_layers(lf, keys):
    files_l = []
    for k in keys:
        files_l.extend(lf.get(k, []))
    files_l = sorted(set(files_l))
    if not files_l:
        return "❌ —"
    shown = files_l[:MAX_CELL_FILES]
    extra = (f"<br>… +{len(files_l) - MAX_CELL_FILES} more (full list in appendix)"
             if len(files_l) > MAX_CELL_FILES else "")
    return "✅ " + "<br>".join(f"`{short_path(f)}`" for f in shown) + extra


def generate_json_output(results, repo, output_path: Path, ollama):
    """Write a structured JSON with per-feature scores, gaps, matched files, and checkpoints."""
    layer_counts = defaultdict(int)

    features = []
    for r in results:
        sp = r["spec"]
        sc = r["scores"]
        feat = {
            "id": sp["id"],
            "name": sp["name"],
            "scope": sp["scope"],
            "domain": r.get("domain", ""),
            "scores": sc,
            "checkpoints": {
                "tables": [
                    {"base": base, "found": tr.get("found", False), "schema": tr.get("schema"),
                     "schema_ok": tr.get("schema_ok"), "evidence": tr.get("evidence", [])[:3]}
                    for base, tr in sorted(r["tables"].items())
                ],
                "routes": [
                    {"method": rr.get("method"), "path": rr.get("path"), "found": rr.get("found", False),
                     "evidence": rr.get("evidence", [])[:3]}
                    for rr in r.get("routes", [])
                ],
                "statuses": r["statuses"],
                "identifiers": r["idents"],
                "capabilities": r["caps"],
                "steps": r["steps"],
                "sections": {
                    sk: {
                        "score": sres["score"],
                        "term_cov": sres["term_cov"],
                        "ui_web": sres["ui_web"],
                        "ui_mobile": sres["ui_mobile"],
                        "files": sres["files"][:10],
                    }
                    for sk, sres in r["sections"].items()
                },
            },
            "gaps": r["gaps"],
            "matched_files_count": len(r["matched"]),
            "dead_count": r["dead_count"],
            "dead_penalty": r["dead_penalty"],
            "semantic_enabled": r["semantic_enabled"],
            "layer_files": r["layer_files"],
            "role_files": r["role_files"],
        }
        features.append(feat)

    data = {
        "version": 1,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "engine": "v5.3",
        "matching_mode": "ollama_semantic" if ollama.can_embed else "keyword",
        "scan_summary": {
            "total_files": len(repo.files),
            "layer_counts": dict(layer_counts),
        },
        "features": features,
        "overall": {
            "weighted_overall": round(
                sum(r["scores"]["overall"] * r["spec"]["weight"] for r in results)
                / sum(r["spec"]["weight"] for r in results), 1
            ) if results else 0.0,
        },
    }
    tmp = output_path.with_name(output_path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, output_path)
    print(f"  JSON written to {output_path}")


def generate_report(results, repo, output_path, ollama):
    L = []
    mode = "Ollama semantic" if ollama.can_embed else "keyword"
    L.append(f"# ZOZI Codebase Status Matrix — SPEC-DRIVEN (v5.3 {mode} mode)")
    L.append("")
    L.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')} · **Engine:** v5.3")
    L.append(f"**Matching mode:** {'🦙 Ollama semantic embeddings' if ollama.can_embed else '🔤 Keyword matching (Ollama not available)'}")
    if ollama.can_llm:
        L.append(f"**LLM verification:** {ollama.llm_model}")
    L.append("")

    layer_counts = defaultdict(int)
    for rel, finfo in repo.files.items():
        layer_counts[finfo["layer"]] += 1
    L.append("## 🔬 Scan Summary")
    L.append("")
    L.append("| Layer | Files |")
    L.append("|---|---|")
    for layer in LAYER_ORDER:
        if layer_counts.get(layer):
            L.append(f"| {LAYER_LABEL.get(layer, layer)} | {layer_counts[layer]} |")
    L.append(f"| **Total** | **{len(repo.files)}** |")
    L.append("")
    L.append("---")
    L.append("")

    L.append("## 📊 Executive Summary")
    L.append("")
    L.append("| # | Section | System | Scope | Files | Dead | DB | API | State | Caps | Sections | Tests | Steps | **Overall** | Status |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(results, 1):
        sc = r["scores"]
        sp = r["spec"]
        em = status_emoji(sc["overall"])
        primary_sec = r.get("primary_section", 99)
        sec_label = {0: "§I", 1: "§II", 2: "§III", 3: "§IV", 4: "§V", 5: "§VI"}.get(primary_sec, "—")
        disc = " 🔍" if r.get("discovered") else ""
        L.append(f"| {i} | {sec_label} | **{esc(sp['name'])}**{disc} | {esc(sp['scope'])} "
                 f"| {len(r['matched'])} | {r['dead_count']} "
                 f"| {pct(sc['db'])} | {pct(sc['api'])} | {pct(sc['state'])} "
                 f"| {pct(sc['capability'])} | {pct(sc['sections'])} "
                 f"| {pct(sc['tests'])} | {pct(sc['steps'])} "
                 f"| **{sc['overall']}%** | {em} |")
    tw = sum(r["spec"]["weight"] for r in results)
    ts = sum(r["scores"]["overall"] * r["spec"]["weight"] for r in results)
    L.append("")
    L.append(f"**Weighted overall: {(ts / tw if tw else 0):.1f}%**")
    L.append("")
    for key, title, tags in SECTION_DEFS:
        rows = sorted([r for r in results if in_section(r, key, tags)],
                      key=lambda r: (r.get("domain", "").lower(), r["spec"]["name"]))
        if not rows:
            continue
        w = sum(r["spec"]["weight"] for r in rows)
        s = sum(r["scores"]["overall"] * r["spec"]["weight"] for r in rows)
        L.append(f"- {title}: {len(rows)} feature(s) · **{(s / w if w else 0):.1f}%**")
    L.append("")
    L.append("---")
    L.append("")

    for key, title, tags in SECTION_DEFS:
        rows = sorted([r for r in results if in_section(r, key, tags)],
                      key=lambda r: (r.get("domain", "").lower(), r["spec"]["name"]))
        if not rows:
            continue
        L.append(f"## {title}")
        L.append("")
        L.append("| Feature | TODO Ref | Backend: Controllers | Backend: Services | Backend: Router | "
                 "Web App Pages | Mobile Screens | Shared / Utils | API Routes | DB Model(s) | "
                 "Backend Tests | Web Tests | Mobile Tests | Completion % |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            lf = defaultdict(set)
            for fpath, info in r["matched"].items():
                if info["role"] == key:
                    lf[info["layer"] or "other"].add(fpath)
            lf = {k: sorted(v) for k, v in lf.items()}
            sc = r["scores"]
            sp = r["spec"]
            em = status_emoji(sc["overall"])
            api_r = exp_routes = r["routes"]
            route_str = f"🔍 {len(exp_routes)} found" if exp_routes else "❌ —"
            model_str = f"🔍 {len(r['tables'])} tables" if r["tables"] else "❌ —"
            L.append(f"| {em} **{esc(sp['name'])}** | {esc(sp['todo_ref'])} "
                     f"| {fmt_layers(lf, ['backend_controller'])} "
                     f"| {fmt_layers(lf, ['backend_service'])} "
                     f"| {fmt_layers(lf, ['backend_router'])} "
                     f"| {fmt_layers(lf, ['web_page'])} "
                     f"| {fmt_layers(lf, ['mobile_screen'])} "
                     f"| {fmt_layers(lf, ['backend_util', 'web_lib'])} "
                     f"| {route_str} | {model_str} "
                     f"| {fmt_layers(lf, ['test_backend'])} "
                     f"| {fmt_layers(lf, ['test_web'])} "
                     f"| {fmt_layers(lf, ['test_mobile'])} "
                     f"| **{sc['overall']}%** |")
        L.append("")
        L.append("---")
        L.append("")

    for r in results:
        sp = r["spec"]
        sc = r["scores"]
        disc = " **[DISCOVERED 🔍]**" if r.get("discovered") else ""
        L.append(f"### {sp['id']} — {sp['name']}{disc}  ({sc['overall']}%)")
        L.append("")
        L.append(f"**Checkpoints:** {len(r['tables'])} tables · "
                 f"{len(r['routes'])} routes · {len(r['statuses'])} statuses · "
                 f"{len(r['idents'])} fields · {len(r['caps'])} capabilities · "
                 f"{len(r['steps'])} steps · {len(sp['terms'])} search terms")
        L.append(f"**Matched files:** {len(r['matched'])} / {len(repo.files)} "
                 f"({len(r['matched'])/len(repo.files)*100:.1f}%)")
        L.append("")

        if r.get("discovered"):
            L.append("**🔧 File Operations (discovered from codebase):**")
            L.append("")
            if r.get("operations"):
                ops_by_file = defaultdict(list)
                for op in r["operations"]:
                    ops_by_file[op.get("file", "")].append(op)
                for file_rel in sorted(ops_by_file.keys()):
                    ops = ops_by_file[file_rel]
                    L.append(f"- `{short_path(file_rel)}`:")
                    for op in ops[:15]:
                        L.append(f"  - `{op['type']}` {op['name']}")
                    if len(ops) > 15:
                        L.append(f"  - … +{len(ops) - 15} more")
            else:
                L.append("- (No operations extracted — file may be a stub/init/config)")
            L.append("")

        L.append("**Completion Breakdown:**")
        L.append("")
        L.append("| Component | Score | Weight |")
        L.append("|---|---|---|")
        L.append(f"| 🗄️ DB tables | {pct(sc['db'])} | 20% |")
        L.append(f"| 🔌 API routes | {pct(sc['api'])} | 15% |")
        L.append(f"| 🚦 Status machine | {pct(sc['state'])} | 15% |")
        L.append(f"| 💪 Capabilities | {pct(sc['capability'])} | 10% |")
        L.append(f"| 🖥️ Panel sections | {pct(sc['sections'])} | 20% |")
        L.append(f"| 🧪 Tests | {pct(sc['tests'])} | 10% |")
        L.append(f"| 🧱 Steps | {pct(sc['steps'])} | 10% |")
        L.append(f"| Dead-file penalty ({r['dead_count']} unwired) | -{r['dead_penalty']:.1f}% | — |")
        L.append(f"| **Overall** | **{sc['overall']}%** | 100% |")
        L.append("")

        if r["tables"]:
            L.append(f"**🗄️ Database tables ({pct(sc['db'])}):**")
            L.append("")
            for base, tr in sorted(r["tables"].items()):
                mark = "✅" if tr.get("found", False) else "❌"
                sch = f" ({tr['schema']})" if tr.get("schema") else ""
                ev = ", ".join(f"`{short_path(e)}`" for e in tr["evidence"]) or ""
                sv = " · schema ✓" if tr["schema_ok"] else ""
                L.append(f"- {mark} `{base}`{sch}{sv}" + (f" — {ev}" if ev else ""))
            L.append("")

        if r["routes"]:
            L.append(f"**🔌 API routes ({pct(sc['api'])}):**")
            L.append("")
            for rr in r["routes"]:
                mark = "✅" if rr.get("found", False) else "❌"
                ev = ", ".join(f"`{short_path(e)}`" for e in rr["evidence"]) or ""
                L.append(f"- {mark} `{rr['method'] or 'ANY'} {rr['path']}`"
                         + (f" — {ev}" if ev else ""))
            L.append("")

        if r["statuses"]:
            found_st = [s for s in r["statuses"] if s["found"]]
            L.append(f"**🚦 Status machine ({pct(sc['state'])}):** "
                     f"{len(found_st)}/{len(r['statuses'])} present")
            L.append("")
            missing = [s["status"] for s in r["statuses"] if not s["found"]]
            if missing:
                L.append(f"- ❌ Missing: {', '.join('`' + m + '`' for m in missing)}")
            present = ", ".join(f"`{s['status']}`" for s in r["statuses"] if s["found"])
            if present:
                L.append(f"- ✅ Present: {present}")
            L.append("")

        if r["caps"]:
            L.append(f"**💪 Capabilities ({pct(sc['capability'])}):**")
            L.append("")
            for cr in r["caps"]:
                mark = "✅" if cr["found"] else "❌"
                ev = f" — `{short_path(cr['evidence'][0])}`" if cr["evidence"] else ""
                llm_note = ""
                if cr.get("llm") and cr["llm"].get("verified") is not None:
                    llm_note = f" 🦙{'✓' if cr['llm']['verified'] else '✗'}"
                L.append(f"- {mark} {esc(cr['phrase'])}{ev}{llm_note}")
            L.append("")

        if r["steps"]:
            L.append(f"**🧱 Steps ({pct(sc['steps'])}):**")
            L.append("")
            L.append("| Step | Title | Done when | Score |")
            L.append("|---|---|---|---|")
            for s in r["steps"]:
                L.append(f"| {s['num']} | {esc(s['title'])} | {esc(s['done_when']) or '—'} "
                         f"| {status_emoji(s['score'])} **{s['score']}%** |")
            L.append("")

        if r["sections"]:
            L.append(f"**🖥️ Panel sections ({pct(sc['sections'])}):**")
            L.append("")
            for sk, sres in sorted(r["sections"].items()):
                web = "✅" if sres["ui_web"] else "❌"
                mob = "✅" if sres["ui_mobile"] else "❌"
                L.append(f"- **{sk}** — {sres['score']}% (terms {sres['term_cov']}%, "
                         f"web {web}, mobile {mob}) — {esc(sres['prose'][:160])}")
            L.append("")

        L.append(f"**🧪 Tests ({pct(sc['tests'])}):**")
        L.append("")
        for lk, label in [("test_backend", "Backend"), ("test_web", "Web"),
                          ("test_mobile", "Mobile"), ("e2e", "E2E")]:
            n = r["test_layers"][lk]
            ev = ", ".join(f"`{short_path(e)}`" for e in r["test_evidence"].get(lk, [])[:3])
            mark = "✅" if n else "❌"
            L.append(f"- {mark} {label}: {n} file(s)" + (f" — {ev}" if ev else ""))
        L.append("")

        if any(r["gaps"].values()):
            L.append("**⛔ Gap summary (what to build next):**")
            L.append("")
            for k, label in [("db", "Tables"), ("api", "Routes"), ("state", "Statuses"),
                             ("capability", "Capabilities"), ("ident", "Fields")]:
                if r["gaps"].get(k):
                    L.append(f"- **{label}:** "
                             + ", ".join(f"`{esc(g)}`" for g in r["gaps"][k][:20]))
            L.append("")

        L.append("**📁 Files by Layer (top entries):**")
        L.append("")
        for layer in LAYER_ORDER:
            files_l = r["layer_files"].get(layer, [])
            if not files_l:
                continue
            L.append(f"**{LAYER_LABEL.get(layer, layer)} ({len(files_l)}):**")
            for f in files_l[:20]:
                reasons = r["matched"].get(f, {}).get("reasons", [])
                reason_str = "; ".join(reasons[:3])
                L.append(f"- `{short_path(f)}`" + (f" — {reason_str}" if reason_str else ""))
            if len(files_l) > 20:
                L.append(f"- … +{len(files_l) - 20} more")
            L.append("")
        L.append("---")
        L.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = output_path.with_name(output_path.name + ".tmp")
    tmp.write_text("\n".join(L), encoding="utf-8")
    os.replace(tmp, output_path)
    print(f"  Report written to {output_path}")


# ============================================================================
# MAIN
# ============================================================================
def main():
    import argparse
    ap = argparse.ArgumentParser(description="ZOZI Feature Tracker — Codebase Discovery Mode")
    ap.add_argument("--output", default=str(ROOT / "documents" / "FEATURE_TRACKER.md"))
    ap.add_argument("--json-out", default=str(ROOT / "documents" / "FEATURE_TRACKER.json"))
    ap.add_argument("--no-ollama", action="store_true", help="Disable Ollama")
    args = ap.parse_args()

    print("=" * 72)
    print("  ZOZI FEATURE TRACKER — CODEBASE DISCOVERY MODE")
    print("=" * 72)
    print(f"  Repo root: {ROOT}")

    ollama = OllamaClient(enabled=not args.no_ollama)
    print()

    try:
        print("Phase 1: Scanning codebase...")
        repo = Repo(ROOT)
        print()

        print("Phase 2: Building registry...")
        reg = Registry(repo)
        print(f"  Tables: {len(reg.tablenames)} tablenames, "
              f"{len(reg.model_classes)} model classes")
        print(f"  Routes: {len(reg.route_paths)} unique paths")
        print()

        print("Phase 3: Discovering features from codebase...")
        results = discover_features_from_codebase(repo)
        print(f"  Discovered {len(results)} feature(s) from codebase")
        print()

        if not results:
            print("  ⚠️ No features discovered. Check EXCLUDE_DIRS and discovery filters.")
            return 1

        print("Phase 4: Generating report...")
        generate_report(results, repo, Path(args.output), ollama)
        if args.json_out:
            generate_json_output(results, repo, Path(args.json_out), ollama)
        print()
    except Exception:
        traceback.print_exc()
        print("\n❌ Run failed — output file left untouched.")
        return 1

    print("=" * 72)
    print("  FINAL SCORES")
    print("=" * 72)
    tw = sum(r["spec"]["weight"] for r in results)
    ts = sum(r["scores"]["overall"] * r["spec"]["weight"] for r in results)
    overall = ts / tw if tw else 0
    bar = "█" * int(overall / 5) + "░" * (20 - int(overall / 5))
    print(f"  {'Weighted overall':<28} [{bar}] {overall:5.1f}%")
    for r in results:
        p = r["scores"]["overall"]
        bar = "█" * int(p / 5) + "░" * (20 - int(p / 5))
        print(f"  {r['spec']['name'][:28]:<28} [{bar}] {p:5.1f}%")
    print("=" * 72)
    if ollama.can_embed:
        print("  🦙 Semantic matching was ACTIVE — file counts should be much lower")
    else:
        print("  🔤 Keyword matching mode — run 'ollama pull nomic-embed-text' for semantic")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⛔ Interrupted.")
        sys.exit(130)