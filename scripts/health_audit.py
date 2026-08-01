#!/usr/bin/env python3
"""
health_audit.py v3.0 — ZOZI Production-Ready Health, Scaling & Polyglot Auditor.

Fixes from v2.0 report review:
  1.  Grouped findings (no per-file spam for FEH402/FEH501/FEH503)
  2.  Priority tiers (P0 fix today / P1 this sprint / P2 this month / P3 when convenient)
  3.  Executive summary with quick wins
  4.  File health ranking (top 20 unhealthiest files)
  5.  Frontend findings grouped by feature domain
  6.  Actionable fix patterns (before/after code examples)
  7.  False positive fixes (tests, workers, Redis init excluded from HL401/HL602)
  8.  Python + JS polyglot contract (NOT Python vs JS)
  9.  Trend comparison (--trend-file / --update-trend)
  10. Scaling / observability / security / deployment / import health checks

Usage:
  python scripts/health_audit.py --no-fail
  python scripts/health_audit.py --base-url http://localhost:8000 --no-fail
  python scripts/health_audit.py --ci
  python scripts/health_audit.py --trend-file .governance/health_trend.json --update-trend
"""

from __future__ import annotations

import argparse
import ast
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# ============================================================================
# 1. CONSTANTS + PRIORITY SYSTEM
# ============================================================================

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"
SEV_ICON = {RED: "🔴", YEL: "🟡", GRN: "🟢"}

# Priority tiers for production governance
P0 = "P0"  # fix today — production risk / security risk
P1 = "P1"  # fix this sprint — scaling / performance risk
P2 = "P2"  # fix this month — maintainability / structure
P3 = "P3"  # fix when convenient — hygiene / style

PRIORITY_ICON = {P0: "🔴", P1: "🟠", P2: "🟡", P3: "🟢"}
PRIORITY_LABEL = {
    P0: "Fix Today",
    P1: "Fix This Sprint",
    P2: "Fix This Month",
    P3: "Fix When Convenient",
}

_DB_CALL_RE = re.compile(
    r"\b(db|session|conn|engine|cursor)\s*\.\s*"
    r"(query|execute|commit|rollback|flush|add|merge|bulk_save|bulk_insert|scalars|scalar)\s*\(",
    re.I,
)

_TOOL_FILE_KEYWORDS = {"schema_audit", "check_", "validate_", "verify_", "diag_", "smoke_", "analyze_", "probe_"}

# Map rule codes to priority tiers
RULE_PRIORITY: dict[str, str] = {
    # P0 — production / security risk
    "HL402": P0, "SEC101": P0, "SEC105": P0, "RT500": P0,
    # P1 — scaling / performance
    "HL403": P1, "HL601": P1, "HL602": P1, "SC102": P1,
    "PG102": P1, "PG103": P1, "SC501": P1, "SC101": P1,
    "HL501": P1, "OB101": P1, "OB102": P1,
    # P2 — maintainability / structure
    "HL101": P2, "HL102": P2, "FEH101": P2, "FEH501": P2,
    "HL502": P2, "API101": P2, "MR101": P2, "MR104": P2,
    "DP101": P2, "DP103": P2, "DP104": P2,
    "FEH301": P2, "FEH801": P2, "PG101": P2, "PG201": P2,
    "FEH502": P2, "FEH701": P2,
    # P3 — hygiene / style
    "HL201": P3, "HL203": P3, "HL204": P3,
    "HL301": P3, "HL302": P3, "HL303": P3,
    "HL401": P3, "HL110": P3, "HL901": P3, "HL902": P3,
    "FEH201": P3, "FEH401": P3, "FEH402": P3, "FEH503": P3,
    "FEH504": P3, "FEH601": P3, "FEH802": P3,
    "DP102": P3, "DP105": P3, "PL101": P3,
    "RT201": P1, "RT404": P2, "RT400": P2,
}

IGNORE_DIRS = {
    ".git", ".kilo", ".kilocode", "worktrees", "node_modules",
    ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".ruff_cache", ".tox", "htmlcov", ".next", ".expo", ".turbo",
    "dist", "build", "coverage", "test-results", "playwright-report",
    "playwright-out", "test-output", "web-dist", ".web-build-test",
    "static-tmp", "tmp", "uploads", "artifacts", "e2e", "__tests__",
    "__mocks__", ".storybook", ".vscode", ".idea", ".hypothesis",
    ".repo", "android", "ios",
}

PYTHON_EXT = {".py"}
FRONTEND_EXT = {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"}

HEAVY_PY_MODULES = {
    "torch", "transformers", "tensorflow", "cv2", "PIL", "pandas",
    "numpy", "sklearn", "matplotlib", "reportlab", "openpyxl",
    "weasyprint", "pdfkit", "imageio", "scipy", "xlsxwriter",
    "pdf2image", "pydub", "moviepy", "selenium", "playwright",
}

BLOCKING_CALLS = {
    "time.sleep",
    "requests.get", "requests.post", "requests.put", "requests.patch",
    "requests.delete", "requests.head", "requests.options",
    "httpx.get", "httpx.post", "httpx.put", "httpx.patch", "httpx.delete",
    "urllib.request.urlopen",
    "subprocess.run", "subprocess.call", "subprocess.check_output",
    "shutil.copy", "shutil.copy2", "shutil.copytree", "os.system",
}

SYNC_IO_CALLS = {
    "open", "os.read", "os.write", "os.listdir", "os.walk",
    "os.stat", "os.path.exists", "os.path.isfile", "os.path.isdir",
    "shutil.rmtree", "shutil.move", "glob.glob", "glob.iglob",
    "json.load", "json.dump", "csv.reader", "csv.writer",
}

EXTERNAL_CALL_PREFIXES = (
    "requests.", "httpx.", "urllib.request",
    "aiohttp.", "boto3.", "botocore.",
    "stripe.", "paypal.", "smtplib.", "imaplib.",
)

# Layers where time.sleep is LEGITIMATE (background/sync code)
SLEEP_ALLOWED_LAYERS = {"utils", "jobs", "scripts", "tasks", "monitoring", "tools"}

# Connection-init patterns that should NOT be flagged for missing timeout
CONN_INIT_PATTERNS = {"redis.Redis", "Redis", "redis_client", "StrictRedis"}

RULE_MEANING = {
    "HL101": "oversized Python file",
    "HL102": "oversized Python function",
    "HL110": "missing docstring on public service/controller function",
    "HL201": "print() used instead of structured logging",
    "HL203": "logging.basicConfig() should be configured centrally",
    "HL204": "possible secret/token value in log/print statement",
    "HL301": "bare except hides failures",
    "HL302": "swallowed exception (except + pass / no logging)",
    "HL303": "broad except Exception should be narrowed or logged",
    "HL401": "blocking sleep in request-path code",
    "HL402": "blocking call inside async function",
    "HL403": "sync file/OS I/O inside async function",
    "HL501": "heavy top-level import in web path (lazy-load recommended)",
    "HL502": "star import (from x import *) pollutes namespace",
    "HL601": "sequential external calls (concurrency opportunity)",
    "HL602": "missing timeout on external call",
    "PG101": "heavy JSON serialization (use orjson or Node.js sidecar)",
    "PG102": "WebSocket in Python (consider Node.js gateway)",
    "PG103": "CPU-bound work in request path (offload to worker)",
    "PG201": "frontend main-thread CPU work (use Web Worker)",
    "SC101": "list endpoint missing pagination",
    "SC102": "loop of individual DB operations (N+1)",
    "SC501": "heavy operation in request path (background job)",
    "API101": "endpoint missing response_model",
    "OB101": "module missing structured logger",
    "OB102": "missing request_id / correlation_id",
    "MR101": "nested list comprehension (use generator)",
    "MR104": "global mutable state (breaks scaling)",
    "SEC101": "raw SQL string concatenation (injection risk)",
    "SEC105": "hardcoded credential/secret in source",
    "FEH101": "oversized frontend file/component",
    "FEH201": "console/debugger in frontend code",
    "FEH301": "missing React error boundary",
    "FEH401": "too many inline JSX handlers",
    "FEH402": "list key uses array index",
    "FEH501": "data fetching inside useEffect",
    "FEH502": "heavy frontend import (lazy-load)",
    "FEH503": "direct DOM access in React",
    "FEH504": "large list rendering (virtualization)",
    "FEH601": "large component without memoization",
    "FEH701": "heavy client-side transformation",
    "FEH801": "missing Suspense/lazy for code splitting",
    "FEH802": "raw <img> without next/image",
    "DP101": "missing Dockerfile",
    "DP102": "missing healthcheck in Docker/compose",
    "DP103": "missing env var validation at startup",
    "DP104": "missing graceful shutdown handler",
    "DP105": "missing .dockerignore",
    "PL100": "pipeline component present",
    "PL101": "pipeline component missing",
    "RT000": "runtime probe enabled",
    "RT200": "runtime endpoint healthy",
    "RT201": "runtime endpoint slow",
    "RT400": "runtime endpoint non-success",
    "RT404": "runtime health endpoint missing",
    "RT500": "runtime endpoint unhealthy/unreachable",
}

# Rules that should be GROUPED (one finding per pattern, not per file)
GROUPABLE_RULES = {"FEH402", "FEH501", "FEH503", "FEH201", "FEH802"}

# Actionable fix patterns for the report
FIX_PATTERNS: dict[str, dict[str, str]] = {
    "FEH501": {
        "before": 'useEffect(() => { fetch("/api/data").then(r => r.json()).then(setData) }, [])',
        "after": 'const { data, isLoading, error } = useQuery({ queryKey: ["data"], queryFn: () => api.get("/data") })',
        "action": "Create shared hook: frontend/web_app/src/lib/hooks/useApiQuery.ts. Migrate all files in one PR.",
    },
    "FEH402": {
        "before": "{items.map((item, index) => <Card key={index} />)}",
        "after": "{items.map((item) => <Card key={item.id} />)}",
        "action": "Ensure API responses include stable `id` fields. Fix all files in one PR.",
    },
    "FEH503": {
        "before": "document.getElementById('modal').style.display = 'block'",
        "after": "const ref = useRef<HTMLDivElement>(null); useEffect(() => { ref.current.style.display = 'block' })",
        "action": "Isolate browser APIs in hooks (useDomEffect, useWindowSize). Prefer React state/refs.",
    },
    "HL402": {
        "before": "async def handler(): time.sleep(5)  # blocks event loop",
        "after": "async def handler(): await asyncio.sleep(5)  # or: await loop.run_in_executor(None, blocking_fn)",
        "action": "Replace sync calls with async equivalents. Use run_in_executor for unavoidable sync code.",
    },
    "HL601": {
        "before": "r1 = requests.get(url1); r2 = requests.get(url2)  # sequential",
        "after": "r1, r2 = await asyncio.gather(fetch(url1), fetch(url2))  # concurrent",
        "action": "Use asyncio.gather for async I/O. Use ThreadPoolExecutor for sync I/O. Add timeout.",
    },
    "HL602": {
        "before": "requests.get(url)  # no timeout — can hang forever",
        "after": "requests.get(url, timeout=30)  # always set timeout",
        "action": "Add timeout to ALL external calls. Add retry + circuit breaker for critical paths.",
    },
    "SC102": {
        "before": "for item in items: db.add(Order(**item)); db.flush()  # N+1",
        "after": "db.bulk_save_objects([Order(**item) for item in items])  # batch",
        "action": "Use bulk operations, joinedload, or subqueryload. Never individual DB ops in a loop.",
    },
    "PG101": {
        "before": "json.dumps(large_dict)  # stdlib json is slow",
        "after": "orjson.dumps(large_dict)  # 3-10x faster; or offload to Node.js sidecar",
        "action": "Install orjson. For very high throughput, add Node.js JSON sidecar service.",
    },
}


# ============================================================================
# 2. DATA MODEL
# ============================================================================


@dataclass
class Finding:
    sev: str
    code: str
    domain: str
    path: str
    message: str
    intended: str = ""
    line: int | None = None
    priority: str = P3
    count: int = 1
    examples: list[str] = field(default_factory=list)

    def loc(self) -> str:
        return f"{self.path}:{self.line}" if self.line else self.path


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    _seen: set[tuple] = field(default_factory=set)

    def add(
        self, sev: str, code: str, domain: str, path: str, message: str,
        intended: str = "", line: int | None = None,
        count: int = 1, examples: list[str] | None = None,
    ) -> None:
        key = (code, path, line, message)
        if key in self._seen:
            return
        self._seen.add(key)

        priority = RULE_PRIORITY.get(code, P3)

        self.findings.append(Finding(
            sev=sev, code=code, domain=domain, path=path,
            message=message, intended=intended, line=line,
            priority=priority, count=count, examples=examples or [],
        ))
        self.counters[code] += 1


# ============================================================================
# 3. GENERIC HELPERS
# ============================================================================


def rel(p: Path, repo: Path) -> str:
    try:
        return str(p.relative_to(repo))
    except ValueError:
        return str(p)


def walk_dirs(root: Path) -> Iterable[tuple[Path, list[Path]]]:
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except (PermissionError, OSError):
            continue
        yield d, entries
        for e in entries:
            if not e.is_dir():
                continue
            name = e.name.lower()
            if name in IGNORE_DIRS or name.startswith("."):
                continue
            stack.append(e)


def iter_files(root: Path, exts: set[str]) -> Iterable[Path]:
    if not root.exists():
        return
    for d, entries in walk_dirs(root):
        for e in entries:
            if e.is_file() and e.suffix.lower() in exts:
                yield e


def read_text(p: Path) -> str | None:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def parse_safe(p: Path) -> ast.Module | None:
    t = read_text(p)
    if t is None:
        return None
    try:
        return ast.parse(t)
    except (SyntaxError, ValueError):
        return None


def dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def is_public_name(name: str) -> bool:
    return bool(name) and not name.startswith("_")


def find_repo(explicit: str | None) -> Path:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).resolve())
    script_dir = Path(__file__).resolve().parent
    candidates.extend([
        script_dir, script_dir.parent, script_dir.parent.parent,
        script_dir.parent.parent.parent, Path.cwd().resolve(),
    ])
    seen: list[Path] = []
    for cand in candidates:
        try:
            cand = cand.resolve()
        except Exception:
            continue
        if cand in seen:
            continue
        seen.append(cand)
        if (cand / "backend").is_dir() and (cand / "frontend").is_dir():
            return cand
        if (cand / "backend").is_dir():
            return cand
    return Path.cwd().resolve()


def resolve_output_path(repo: Path, value: str | None, default_name: str) -> Path:
    if not value:
        return repo / default_name
    p = Path(value)
    if p.is_absolute():
        return p.resolve()
    return (repo / p).resolve()


def _lines_example(lines: list[int], limit: int = 6) -> str:
    example = ", ".join(str(x) for x in lines[:limit])
    if len(lines) > limit:
        example += f" +{len(lines) - limit} more"
    return example


def _is_request_path_layer(app_layer: str) -> bool:
    """Only flag blocking calls in request-path layers."""
    return app_layer in {"routers", "controllers", "services", "middleware", "dependencies", "providers"}


def _is_conn_init(call_name: str) -> bool:
    """Check if a call is a connection initialization (not a per-request call)."""
    return any(pat in call_name for pat in CONN_INIT_PATTERNS)


def frontend_domain(path: str) -> str:
    """Extract feature domain from a frontend file path."""
    parts = path.replace("\\", "/").split("/")
    if "app" in parts:
        idx = parts.index("app")
        remaining = parts[idx + 1:-1]
        if remaining:
            return "/".join(remaining[:2])
        return "app"
    if "components" in parts:
        idx = parts.index("components")
        remaining = parts[idx + 1:-1]
        if remaining:
            return "components/" + remaining[0]
        return "components"
    if "lib" in parts:
        return "lib"
    if "hooks" in parts:
        return "hooks"
    if "shared" in parts:
        return "shared"
    return "other"


# ============================================================================
# 4. SINGLE-PASS PYTHON FILE ANALYSIS
# ============================================================================

@dataclass
class PyFileAnalysis:
    path: str = ""
    line_count: int = 0
    app_layer: str = ""
    is_test: bool = False
    is_script: bool = False
    is_background: bool = False
    is_migration: bool = False
    is_scheduler: bool = False
    is_seed: bool = False
    is_tool: bool = False

    todo_count: int = 0
    commented_code_count: int = 0
    secret_log_lines: list[int] = field(default_factory=list)
    heavy_toplevel_imports: list[str] = field(default_factory=list)
    has_structured_logger: bool = False
    has_logging_basic_config: bool = False
    logging_basic_config_line: int | None = None
    print_lines: list[int] = field(default_factory=list)
    star_imports: list[int] = field(default_factory=list)
    global_mutables: list[str] = field(default_factory=list)
    has_request_id: bool = False
    raw_sql_lines: list[int] = field(default_factory=list)
    hardcoded_secret_lines: list[int] = field(default_factory=list)

    large_funcs: list[tuple[str, int]] = field(default_factory=list)
    missing_docs: list[str] = field(default_factory=list)
    bare_except_lines: list[int] = field(default_factory=list)
    swallowed_lines: list[int] = field(default_factory=list)
    broad_lines: list[int] = field(default_factory=list)
    blocking_sleep: list[tuple[str, int]] = field(default_factory=list)
    blocking_in_async: list[tuple[str, int, str]] = field(default_factory=list)
    sync_io_in_async: list[tuple[str, int, str]] = field(default_factory=list)
    sequential_http: list[tuple[str, int, bool]] = field(default_factory=list)
    missing_timeout: list[tuple[str, int]] = field(default_factory=list)
    cpu_bound: list[str] = field(default_factory=list)
    timing_targets: list[tuple[str, int, int]] = field(default_factory=list)
    json_heavy_funcs: list[tuple[str, int]] = field(default_factory=list)
    websocket_funcs: list[str] = field(default_factory=list)
    list_endpoints_no_pagination: list[str] = field(default_factory=list)
    loop_db_ops: list[tuple[str, int]] = field(default_factory=list)
    heavy_in_request: list[str] = field(default_factory=list)
    missing_response_model: list[str] = field(default_factory=list)
    large_list_comprehensions: list[tuple[str, int]] = field(default_factory=list)


def analyze_python_file(f: Path, text: str, tree: ast.Module | None, repo: Path) -> PyFileAnalysis:
    a = PyFileAnalysis()
    a.path = rel(f, repo)

    try:
        parts = [p.lower() for p in f.relative_to(repo).parts]
    except ValueError:
        parts = []

    a.is_test = any(x in parts for x in {"tests", "test", "e2e", "testing", "loadtests", "validation"})
    a.is_script = "scripts" in parts
    a.is_background = any(x in parts for x in SLEEP_ALLOWED_LAYERS)
    a.is_migration = "alembic" in parts and "versions" in parts
    a.is_scheduler = any(x in a.path.lower() for x in ("scheduler", "schedule", "cron", "worker"))
    a.is_seed = "seed" in a.path.lower() or "migration_helpers" in a.path.lower()
    a.is_tool = any(kw in a.path.lower() for kw in _TOOL_FILE_KEYWORDS)

    if "backend" in parts:
        idx = parts.index("backend")
        if len(parts) > idx + 1:
            a.app_layer = parts[idx + 1]

    lines = text.splitlines()
    a.line_count = len(lines)

    # ---- line-level scans ----
    todo_re = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.I)
    comment_code_re = re.compile(
        r"^#\s*(import |from |def |class |if |for |while |return |try:|except|.*=\s*[\w\[\{])"
    )
    log_secret_re = re.compile(
        r"(logger|logging|print|console).*?(password|secret|token|api_key|apikey|authorization|cookie|jwt)", re.I,
    )
    raw_sql_re = re.compile(
        r"""(execute|executemany|text)\s*\(\s*['\"].*?(%s|\{|\+\s*\w|f['\"])""", re.I,
    )
    hardcoded_secret_re = re.compile(
        r"""(password|secret|api_key|apikey|token|private_key)\s*=\s*['\"][^'\"]{8,}['\"]""", re.I,
    )

    for i, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if todo_re.search(stripped):
            a.todo_count += 1
        if stripped.startswith("#") and comment_code_re.search(stripped):
            a.commented_code_count += 1
        # HL204: skip scripts (audit scripts contain secret-detection regex)
        if not a.is_test and not a.is_script and log_secret_re.search(raw_line):
            a.secret_log_lines.append(i)
        # SEC101: skip scripts, tests, migrations
        if not a.is_script and not a.is_test and not a.is_migration:
            if raw_sql_re.search(raw_line):
                a.raw_sql_lines.append(i)
        if hardcoded_secret_re.search(raw_line):
            low = raw_line.lower()
            if not any(x in low for x in {"example", "placeholder", "changeme", "dummy", "test", "xxx", "your_"}):
                a.hardcoded_secret_lines.append(i)

    if "getLogger" in text or "structlog" in text or "loguru" in text:
        a.has_structured_logger = True
    if "request_id" in text or "correlation_id" in text or "X-Request-ID" in text:
        a.has_request_id = True

    if tree is None:
        return a

    # ---- top-level imports ----
    web_layers = {"routers", "controllers", "services", "main", "dependencies", "middleware", "providers"}
    for node in tree.body:
        module_names: list[str] = []
        if isinstance(node, ast.Import):
            module_names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_names = [node.module.split(".")[0]]
        for m in module_names:
            if m in HEAVY_PY_MODULES and a.app_layer in web_layers:
                a.heavy_toplevel_imports.append(m)
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    a.star_imports.append(node.lineno)

    # ---- global mutable state (only truly mutable, skip tests/scripts) ----
    if not a.is_test and not a.is_script:
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and is_public_name(target.id):
                        if isinstance(node.value, ast.List):
                            a.global_mutables.append(target.id)
                        elif isinstance(node.value, ast.Dict):
                            has_var = any(
                                not isinstance(v, (ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict))
                                for v in node.value.values if v is not None
                            )
                            if has_var:
                                a.global_mutables.append(target.id)

    # ---- logging.basicConfig ----
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and dotted_name(node.func) == "logging.basicConfig":
            a.has_logging_basic_config = True
            a.logging_basic_config_line = node.lineno

    # ---- print statements (skip scripts/tests) ----
    if not a.is_script and not a.is_test:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and dotted_name(node.func) == "print":
                a.print_lines.append(node.lineno)

    # ---- exception handlers (skip scripts) ----
    if not a.is_script:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.type is None:
                a.bare_except_lines.append(node.lineno)
                continue
            exception_names = []
            if isinstance(node.type, ast.Name):
                exception_names = [node.type.id]
            elif isinstance(node.type, ast.Tuple):
                exception_names = [el.id for el in node.type.elts if isinstance(el, ast.Name)]
            if "Exception" in exception_names or "BaseException" in exception_names:
                a.broad_lines.append(node.lineno)
                only_pass = all(isinstance(s, ast.Pass) for s in node.body)
                has_log = any(
                    isinstance(c, ast.Call) and "log" in dotted_name(c.func).lower()
                    for c in ast.walk(node)
                )
                if only_pass or not has_log:
                    a.swallowed_lines.append(node.lineno)

    # ---- function-level analysis ----
    for func in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        func_name = func.name
        is_async = isinstance(func, ast.AsyncFunctionDef)

        # Size: skip migrations, scripts, tests, seed, tools
        if (func.end_lineno
                and not a.is_migration and not a.is_script
                and not a.is_test and not a.is_seed and not a.is_tool):
            func_len = func.end_lineno - func.lineno + 1
            if func_len > 80:
                a.large_funcs.append((func_name, func_len))

        # Docstrings: skip scripts, tests
        if (is_public_name(func_name) and not a.is_script and not a.is_test
                and a.app_layer in {"services", "controllers", "routers", "providers", "jobs", "events"}):
            try:
                if not ast.get_docstring(func):
                    a.missing_docs.append(func_name)
            except Exception:
                pass

        # Endpoints
        is_endpoint = False
        is_write_endpoint = False
        for dec in func.decorator_list:
            dec_name = dotted_name(dec.func) if isinstance(dec, ast.Call) else dotted_name(dec)
            if any(x in dec_name for x in (".get", ".post", ".put", ".patch", ".delete")):
                is_endpoint = True
                if any(x in dec_name for x in (".post", ".put", ".patch", ".delete")):
                    is_write_endpoint = True

        if is_endpoint:
            has_rm = any(
                any(kw.arg == "response_model" for kw in dec.keywords)
                for dec in func.decorator_list if isinstance(dec, ast.Call)
            )
            if not has_rm and func_name not in a.missing_response_model:
                a.missing_response_model.append(func_name)

        # Loop ranges (correct approach)
        loop_ranges: list[tuple[int, int]] = []
        for child in ast.walk(func):
            if isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                if child.end_lineno:
                    loop_ranges.append((child.lineno, child.end_lineno))

        def _in_loop(lineno: int) -> bool:
            return any(start <= lineno <= end for start, end in loop_ranges)

        has_loop = len(loop_ranges) > 0
        http_count = 0
        has_transform = False
        has_db = False
        call_count = 0
        json_ops = 0
        db_ops_in_loop = 0

        for child in ast.walk(func):
            if isinstance(child, ast.ListComp) and len(child.generators) > 1:
                a.large_list_comprehensions.append((func_name, child.lineno))
            if not isinstance(child, ast.Call):
                continue

            call_name = dotted_name(child.func)
            call_count += 1
            child_line = getattr(child, "lineno", func.lineno)

            # Blocking sleep: exclude tests, scripts, workers, schedulers,
            # middleware, background, retry patterns
            if call_name == "time.sleep":
                func_source = ""
                try:
                    func_source = ast.get_source_segment(text, func) or ""
                except Exception:
                    pass
                is_retry = (
                    "retry" in func_name.lower()
                    or "backoff" in func_source.lower()
                    or "attempt" in func_source.lower()
                    or "max_retries" in func_source
                )
                if (_is_request_path_layer(a.app_layer)
                        and not a.is_test and not a.is_script
                        and not a.is_background and not a.is_scheduler
                        and a.app_layer not in SLEEP_ALLOWED_LAYERS
                        and a.app_layer != "middleware"
                        and not is_retry):
                    a.blocking_sleep.append((func_name, child_line))

            if call_name in BLOCKING_CALLS and is_async:
                a.blocking_in_async.append((func_name, child_line, call_name))
            if call_name in SYNC_IO_CALLS and is_async:
                a.sync_io_in_async.append((func_name, child_line, call_name))

            if call_name.startswith(EXTERNAL_CALL_PREFIXES):
                http_count += 1
                if not _is_conn_init(call_name):
                    if not any(kw.arg == "timeout" for kw in child.keywords):
                        a.missing_timeout.append((func_name, child_line))

            if call_name.startswith("json."):
                json_ops += 1
                has_transform = True
            if call_name.startswith(("re.", "hashlib.", "base64.")):
                has_transform = True

            # DB ops: module-level regex, correct loop check
            if _DB_CALL_RE.search(call_name):
                has_db = True
                if _in_loop(child_line):
                    db_ops_in_loop += 1

            # WebSocket: skip scripts (audit scripts contain "websocket" in detection code)
            if "websocket" in call_name.lower() and not a.is_script:
                if func_name not in a.websocket_funcs:
                    a.websocket_funcs.append(func_name)

        # Post-function

        # Sequential HTTP: skip scripts (setup scripts make sequential calls)
        if http_count > 1 and not a.is_script:
            a.sequential_http.append((func_name, http_count, is_async))

        if has_loop and has_transform and not has_db and http_count == 0:
            a.cpu_bound.append(func_name)
        if json_ops >= 5:
            a.json_heavy_funcs.append((func_name, json_ops))

        # Timing: skip scripts, tests, migrations, seed, utils, tools
        if (not a.is_script and not a.is_test and not a.is_migration
                and not a.is_seed and not a.is_tool
                and a.app_layer not in {"utils", "tools", "scripts", "tasks", "monitoring"}):
            if http_count >= 2 or call_count >= 25:
                a.timing_targets.append((func_name, call_count, http_count))

        # N+1: skip scripts, tests, migrations, middleware, seed, jobs
        if (not a.is_script and not a.is_test and not a.is_migration
                and a.app_layer != "middleware" and not a.is_seed
                and a.app_layer != "jobs"
                and "seed" not in a.path.lower()
                and "migration_helpers" not in a.path.lower()):
            if db_ops_in_loop >= 2:
                a.loop_db_ops.append((func_name, db_ops_in_loop))

        if is_endpoint and has_loop and has_transform and call_count > 15:
            a.heavy_in_request.append(func_name)

        # Pagination
        if is_endpoint and not is_write_endpoint:
            try:
                func_source = ast.get_source_segment(text, func) or ""
            except Exception:
                func_source = ""
            if ("skip" not in func_source and "limit" not in func_source
                    and "offset" not in func_source and "page" not in func_source):
                if ".all()" in func_source:
                    a.list_endpoints_no_pagination.append(func_name)

    return a

# ============================================================================
# 5. PYTHON HEALTH CHECKS
# ============================================================================

def check_python_health(repo: Path, rep: Report, eff: dict) -> None:
    # Grouping collectors
    ob101_by_layer: dict[str, list[str]] = defaultdict(list)
    ob102_by_layer: dict[str, list[str]] = defaultdict(list)
    hl110_all: list[tuple[str, list[str]]] = []

    for root in [repo / "backend", repo / "scripts"]:
        if not root.exists():
            continue
        for f in iter_files(root, PYTHON_EXT):
            text = read_text(f)
            if not text:
                continue
            tree = parse_safe(f)
            a = analyze_python_file(f, text, tree, repo)
            rp = a.path

            # HL101: skip scripts, tests, seed, tools
            if (a.line_count > 900 and not a.is_script
                    and not a.is_test and not a.is_seed and not a.is_tool):
                rep.add(YEL, "HL101", "python", rp,
                        f"oversized Python file ({a.line_count} lines)",
                        intended="split by responsibility/domain")

            if a.todo_count > 5:
                rep.add(YEL, "HL901", "python", rp,
                        f"{a.todo_count} TODO/FIXME/HACK markers",
                        intended="convert to tasks/ADRs; delete stale")

            # HL902: skip tests
            if a.commented_code_count > 15 and not a.is_test:
                rep.add(YEL, "HL902", "python", rp,
                        f"{a.commented_code_count} commented-out code lines",
                        intended="remove dead code; rely on git history")

            # HL204: skip scripts
            if a.secret_log_lines and not a.is_script:
                rep.add(YEL, "HL204", "security", rp,
                        f"possible secret in log (lines: {_lines_example(a.secret_log_lines)})",
                        intended="never log secrets; log only IDs/status")

            if a.hardcoded_secret_lines:
                rep.add(RED, "SEC105", "security", rp,
                        f"hardcoded credential (lines: {_lines_example(a.hardcoded_secret_lines)})",
                        intended="move to env vars / Vault / secrets manager")

            if a.raw_sql_lines:
                rep.add(RED, "SEC101", "security", rp,
                        f"raw SQL concatenation (lines: {_lines_example(a.raw_sql_lines)})",
                        intended="use parameterized queries / SQLAlchemy ORM")

            if tree is None:
                continue

            if a.heavy_toplevel_imports:
                rep.add(YEL, "HL501", "performance", rp,
                        f"heavy top-level import(s): {', '.join(sorted(set(a.heavy_toplevel_imports)))}",
                        intended="lazy-import inside the function/job that needs them")

            if a.star_imports:
                rep.add(YEL, "HL502", "python", rp,
                        f"star import(s) at lines: {_lines_example(a.star_imports)}",
                        intended="use explicit imports")

            if a.has_logging_basic_config:
                rep.add(YEL, "HL203", "logging", rp,
                        "logging.basicConfig() in module code",
                        intended="configure once in main; modules use getLogger()",
                        line=a.logging_basic_config_line)

            if a.print_lines:
                rep.add(YEL, "HL201", "logging", rp,
                        f"{len(a.print_lines)} print() (lines: {_lines_example(a.print_lines)})",
                        intended="use structured logging with request_id/domain/context")

            # OB101: COLLECT (not per-file)
            if not a.has_structured_logger and a.app_layer in {
                "services", "controllers", "routers", "middleware", "providers",
            }:
                ob101_by_layer[a.app_layer].append(rp)

            # OB102: COLLECT (not per-file)
            if not a.has_request_id and a.app_layer in {"middleware", "routers", "controllers"}:
                ob102_by_layer[a.app_layer].append(rp)

            if a.bare_except_lines:
                rep.add(YEL, "HL301", "error-handling", rp,
                        f"bare except (lines: {_lines_example(a.bare_except_lines)})",
                        intended="catch specific exceptions; log; re-raise or return safe error")

            # HL302: skip scripts
            if a.swallowed_lines and not a.is_script:
                rep.add(YEL, "HL302", "error-handling", rp,
                        f"swallowed exception (lines: {_lines_example(a.swallowed_lines)})",
                        intended="log with logger.exception(...); re-raise or return controlled error")
            elif a.broad_lines and not a.is_script:
                rep.add(YEL, "HL303", "error-handling", rp,
                        f"broad except Exception (lines: {_lines_example(a.broad_lines)})",
                        intended="narrow exception types; always log with context")

            # HL102: skip migrations, scripts, tests, seed, tools
            if (a.large_funcs and not a.is_migration and not a.is_script
                    and not a.is_test and not a.is_seed and not a.is_tool):
                examples = ", ".join(f"{n} ({l}L)" for n, l in a.large_funcs[:6])
                rep.add(YEL, "HL102", "python", rp,
                        f"oversized function(s): {examples}",
                        intended="extract smaller functions")

            # HL110: COLLECT (not per-file)
            if a.missing_docs:
                hl110_all.append((rp, a.missing_docs))

            if a.blocking_sleep:
                examples = ", ".join(f"{n}:{l}" for n, l in a.blocking_sleep[:6])
                rep.add(YEL, "HL401", "performance", rp,
                        f"blocking sleep in request path: {examples}",
                        intended="use async sleep, scheduler, or background job")

            if a.blocking_in_async:
                examples = ", ".join(f"{n}:{l} ({c})" for n, l, c in a.blocking_in_async[:6])
                rep.add(RED, "HL402", "performance", rp,
                        f"blocking call inside async: {examples}",
                        intended="use async client or run_in_executor")

            if a.sync_io_in_async:
                examples = ", ".join(f"{n}:{l} ({c})" for n, l, c in a.sync_io_in_async[:6])
                rep.add(YEL, "HL403", "performance", rp,
                        f"sync I/O inside async: {examples}",
                        intended="use aiofiles / async pathlib / run_in_executor")

            # HL601: skip scripts
            if a.sequential_http and not a.is_script:
                examples = ", ".join(f"{n} ({c} calls)" for n, c, _ in a.sequential_http[:6])
                rep.add(YEL, "HL601", "concurrency", rp,
                        f"sequential external calls: {examples}",
                        intended="use asyncio.gather or ThreadPoolExecutor; add timeout + retry")

            # HL602: skip scripts and tests
            if a.missing_timeout and not a.is_script and not a.is_test:
                examples = ", ".join(f"{n}:{l}" for n, l in a.missing_timeout[:6])
                rep.add(YEL, "HL602", "concurrency", rp,
                        f"external call(s) missing timeout: {examples}",
                        intended="always set timeout; add retry + circuit breaker")

            if a.json_heavy_funcs:
                examples = ", ".join(f"{n} ({c} json ops)" for n, c in a.json_heavy_funcs[:6])
                rep.add(YEL, "PG101", "polyglot", rp,
                        f"heavy JSON serialization: {examples}",
                        intended="use orjson (3-10x faster) or Node.js sidecar")

            if a.websocket_funcs:
                examples = ", ".join(set(a.websocket_funcs[:6]))
                rep.add(YEL, "PG102", "polyglot", rp,
                        f"WebSocket handler in Python: {examples}",
                        intended="Python for business logic; Node.js gateway for high-throughput real-time")

            if a.heavy_in_request:
                examples = ", ".join(a.heavy_in_request[:6])
                rep.add(YEL, "PG103", "polyglot", rp,
                        f"CPU-bound in request path: {examples}",
                        intended="offload to worker (Celery/arq) or Node.js worker thread")

            if a.list_endpoints_no_pagination:
                examples = ", ".join(a.list_endpoints_no_pagination[:6])
                rep.add(YEL, "SC101", "scaling", rp,
                        f"list endpoint(s) missing pagination: {examples}",
                        intended="add skip/limit or cursor pagination")

            if a.loop_db_ops:
                examples = ", ".join(f"{n} ({c} ops)" for n, c in a.loop_db_ops[:6])
                rep.add(YEL, "SC102", "scaling", rp,
                        f"N+1 DB operations in loop: {examples}",
                        intended="use bulk operations / joinedload / batch insert")

            if a.missing_response_model:
                examples = ", ".join(a.missing_response_model[:6])
                rep.add(YEL, "API101", "api-health", rp,
                        f"endpoint(s) missing response_model: {examples}",
                        intended="add response_model for type safety and docs")

            if a.large_list_comprehensions:
                examples = ", ".join(f"{n}:{l}" for n, l in a.large_list_comprehensions[:6])
                rep.add(YEL, "MR101", "memory", rp,
                        f"nested list comprehension: {examples}",
                        intended="use generator expression for large datasets")

            # MR104: skip seed, tools, scripts
            if a.global_mutables and not a.is_seed and not a.is_tool and not a.is_script:
                examples = ", ".join(a.global_mutables[:6])
                rep.add(YEL, "MR104", "memory", rp,
                        f"global mutable state: {examples}",
                        intended="use dependency injection / singleton")

            # HL801: skip scripts, tests, utils, tools
            if (a.timing_targets and not a.is_script and not a.is_test
                    and not a.is_seed and not a.is_tool
                    and a.app_layer not in {"utils", "tools", "scripts", "tasks", "monitoring"}):
                examples = ", ".join(f"{n} (calls={c})" for n, c, _ in a.timing_targets[:6])
                rep.add(YEL, "HL801", "observability", rp,
                        f"function(s) need timing/metrics: {examples}",
                        intended="add timing decorator / Prometheus histogram / duration_ms logs")

    # ================================================================
    # EMIT GROUPED FINDINGS
    # ================================================================

    for layer in sorted(ob101_by_layer.keys()):
        files = ob101_by_layer[layer]
        top = [Path(fp).name for fp in files[:5]]
        extra = f" +{len(files) - 5} more" if len(files) > 5 else ""
        rep.add(YEL, "OB101", "observability", f"backend/{layer}/",
                f"{len(files)} modules missing structured logger",
                intended=f"Add logger = logging.getLogger(__name__). Top: {', '.join(top)}{extra}")

    for layer in sorted(ob102_by_layer.keys()):
        files = ob102_by_layer[layer]
        top = [Path(fp).name for fp in files[:5]]
        extra = f" +{len(files) - 5} more" if len(files) > 5 else ""
        rep.add(YEL, "OB102", "observability", f"backend/{layer}/",
                f"{len(files)} modules missing request_id / correlation_id",
                intended=f"Add X-Request-ID middleware in main.py (fixes all {len(files)} at once). Top: {', '.join(top)}{extra}")

    if hl110_all:
        total_funcs = sum(len(funcs) for _, funcs in hl110_all)
        total_files = len(hl110_all)
        layer_counts: dict[str, int] = defaultdict(int)
        for path, funcs in hl110_all:
            parts = path.replace("\\", "/").split("/")
            if "backend" in parts:
                idx = parts.index("backend")
                ln = parts[idx + 1] if len(parts) > idx + 1 else "root"
                layer_counts[ln] += len(funcs)
        layer_summary = ", ".join(
            f"{l}/ ({c})" for l, c in sorted(layer_counts.items(), key=lambda x: -x[1])[:5]
        )
        top_files = [Path(p).name for p, _ in hl110_all[:5]]
        extra = f" +{total_files - 5} more" if total_files > 5 else ""
        rep.add(YEL, "HL110", "documentation", "backend/",
                f"{total_funcs} public functions missing docstrings across {total_files} files",
                intended=f"By layer: {layer_summary}. Top files: {', '.join(top_files)}{extra}. Add docstrings to service layer first.")
        

# ============================================================================
# 6. FRONTEND HEALTH CHECKS (WITH GROUPING)
# ============================================================================


CONSOLE_RE = re.compile(r"\bconsole\.(log|debug|info|warn|error)\b")
DEBUGGER_RE = re.compile(r"\bdebugger\b")
INLINE_HANDLER_RE = re.compile(r"\bon[A-Z]\w*=\{?\s*\(\s*\)?\s*=>")
KEY_INDEX_RE = re.compile(r"key=\{(?:index|i|idx)\}")
USEEFFECT_FETCH_RE = re.compile(
    r"useEffect\(\s*\(\s*\)\s*=>\s*\{[\s\S]*?(fetch\(|axios\.|api\.|\.get\(|\.post\()", re.I,
)
DIRECT_DOM_RE = re.compile(r"\bdocument\.getElementById|\bdocument\.querySelector|\bwindow\.")
MAP_RE = re.compile(r"\.map\(")
ERROR_BOUNDARY_RE = re.compile(r"ErrorBoundary|componentDidCatch|getDerivedStateFromError")
MEMO_RE = re.compile(r"\buseMemo\b|\buseCallback\b|\bReact\.memo\b")
SUSPENSE_RE = re.compile(r"\bSuspense\b|\bReact\.lazy\b|\bnext/dynamic\b|\blazy\(")
HEAVY_FE_IMPORT_RE = re.compile(
    r"from\s+['\"](moment|lodash|@mui/material|@mui/icons-material|chart\.js|recharts|"
    r"date-fns|dayjs|xlsx|pdfjs-dist|three|d3|monaco-editor|antd)['\"]"
)
IMG_TAG_RE = re.compile(r"<img\s")
NEXT_IMAGE_RE = re.compile(r"next/image|<Image\s")
WEB_WORKER_RE = re.compile(r"\bnew\s+Worker\b|\buseWorker\b|worker_threads")


def check_frontend_health(repo: Path, rep: Report, eff: dict) -> None:
    frontend = repo / "frontend"
    if not frontend.exists():
        return

    feh402_files: list[str] = []
    feh501_files: list[str] = []
    feh503_files: list[str] = []
    feh201_files: list[str] = []
    feh802_files: list[str] = []

    for f in iter_files(frontend, FRONTEND_EXT):
        text = read_text(f)
        if not text:
            continue
        rp = rel(f, repo)
        try:
            parts = [p.lower() for p in f.relative_to(repo).parts]
        except ValueError:
            parts = []
        is_test = any(x in parts for x in {"tests", "test", "e2e", "__tests__", "testing"})
        lines = text.splitlines()
        line_count = len(lines)
        fe_domain = frontend_domain(rp)

        if line_count > 600:
            rep.add(YEL, "FEH101", f"frontend/{fe_domain}", rp,
                    f"oversized frontend file ({line_count} lines)",
                    intended="split into smaller components/hooks/features")

        if not is_test:
            cc = len(CONSOLE_RE.findall(text))
            dc = len(DEBUGGER_RE.findall(text))
            if cc or dc:
                feh201_files.append(rp)

        inline_count = len(INLINE_HANDLER_RE.findall(text))
        if inline_count > 20:
            rep.add(YEL, "FEH401", f"frontend/{fe_domain}", rp,
                    f"{inline_count} inline JSX handler(s)",
                    intended="extract handlers; use useCallback/React.memo")

        if KEY_INDEX_RE.search(text):
            feh402_files.append(rp)

        if "useEffect" in text and USEEFFECT_FETCH_RE.search(text):
            feh501_files.append(rp)

        heavy = HEAVY_FE_IMPORT_RE.findall(text)
        if heavy:
            rep.add(YEL, "FEH502", f"frontend/{fe_domain}", rp,
                    f"heavy import(s): {', '.join(sorted(set(heavy)))}",
                    intended="use modular imports / dynamic import / next dynamic")

        if DIRECT_DOM_RE.search(text):
            feh503_files.append(rp)

        map_count = len(MAP_RE.findall(text))
        if map_count > 35:
            rep.add(YEL, "FEH504", f"frontend/{fe_domain}", rp,
                    f"large list rendering ({map_count} .map calls)",
                    intended="use virtualization, pagination, or server-driven lists")

        fname = f.name.lower()
        if fname in {"app.tsx", "layout.tsx", "_app.tsx", "main.tsx", "index.tsx"}:
            if not ERROR_BOUNDARY_RE.search(text):
                rep.add(YEL, "FEH301", f"frontend/{fe_domain}", rp,
                        "app/layout entry has no ErrorBoundary",
                        intended="wrap app/routes in ErrorBoundary")

        if line_count > 400 and inline_count > 10 and not MEMO_RE.search(text):
            rep.add(YEL, "FEH601", f"frontend/{fe_domain}", rp,
                    "large component without memoization",
                    intended="use useMemo/useCallback/React.memo where measured")

        json_heavy = text.count("JSON.parse") + text.count("JSON.stringify")
        if json_heavy > 10 and (map_count > 10 or "for " in text):
            rep.add(YEL, "FEH701", f"frontend/{fe_domain}", rp,
                    f"heavy client-side transformation ({json_heavy} JSON ops)",
                    intended="move to Web Worker / WASM / server")

        if line_count > 300 and not SUSPENSE_RE.search(text):
            if "import " in text and ("page" in fname or "screen" in fname):
                rep.add(YEL, "FEH801", f"frontend/{fe_domain}", rp,
                        "route/page without Suspense/lazy loading",
                        intended="use React.lazy + Suspense or next/dynamic")

        if IMG_TAG_RE.search(text) and not NEXT_IMAGE_RE.search(text):
            feh802_files.append(rp)

        if json_heavy > 15 and not WEB_WORKER_RE.search(text):
            rep.add(YEL, "PG201", "polyglot", rp,
                    f"heavy computation on main thread ({json_heavy} JSON ops)",
                    intended="move to Web Worker; keep main thread for rendering")

    # ================================================================
    # EMIT GROUPED FINDINGS
    # ================================================================
    if feh402_files:
        top = feh402_files[:5]
        extra = f" +{len(feh402_files) - 5} more" if len(feh402_files) > 5 else ""
        rep.add(YEL, "FEH402", "react", "frontend/",
                f"{len(feh402_files)} files use array index as list key",
                intended=f"Use item.id instead of index. Top: {', '.join(top)}{extra}",
                count=len(feh402_files), examples=top)

    if feh501_files:
        top = feh501_files[:5]
        extra = f" +{len(feh501_files) - 5} more" if len(feh501_files) > 5 else ""
        rep.add(YEL, "FEH501", "react", "frontend/",
                f"{len(feh501_files)} files fetch data inside useEffect",
                intended=f"Migrate to React Query/SWR. Create shared useApiQuery() hook. Top: {', '.join(top)}{extra}",
                count=len(feh501_files), examples=top)

    if feh503_files:
        top = feh503_files[:5]
        extra = f" +{len(feh503_files) - 5} more" if len(feh503_files) > 5 else ""
        rep.add(YEL, "FEH503", "react", "frontend/",
                f"{len(feh503_files)} files use direct DOM/window access",
                intended=f"Isolate browser APIs in hooks. Top: {', '.join(top)}{extra}",
                count=len(feh503_files), examples=top)

    if feh201_files:
        top = feh201_files[:5]
        extra = f" +{len(feh201_files) - 5} more" if len(feh201_files) > 5 else ""
        rep.add(YEL, "FEH201", "frontend", "frontend/",
                f"{len(feh201_files)} files have console/debugger statements",
                intended=f"Remove before merge; use structured logger. Top: {', '.join(top)}{extra}",
                count=len(feh201_files), examples=top)

    if feh802_files:
        top = feh802_files[:5]
        extra = f" +{len(feh802_files) - 5} more" if len(feh802_files) > 5 else ""
        rep.add(YEL, "FEH802", "frontend", "frontend/",
                f"{len(feh802_files)} files use raw <img> without next/image",
                intended=f"Use next/image for lazy loading + WebP. Top: {', '.join(top)}{extra}",
                count=len(feh802_files), examples=top)

    # ================================================================
    # EMIT GROUPED FINDINGS
    # ================================================================

    if feh402_files:
        top = feh402_files[:5]
        extra = f" +{len(feh402_files) - 5} more" if len(feh402_files) > 5 else ""
        rep.add(YEL, "FEH402", "react", "frontend/",
                f"{len(feh402_files)} files use array index as list key",
                intended=f"Use item.id instead of index. Top: {', '.join(top)}{extra}",
                count=len(feh402_files), examples=top)

    if feh501_files:
        top = feh501_files[:5]
        extra = f" +{len(feh501_files) - 5} more" if len(feh501_files) > 5 else ""
        rep.add(YEL, "FEH501", "react", "frontend/",
                f"{len(feh501_files)} files fetch data inside useEffect",
                intended=f"Migrate to React Query/SWR. Create shared useApiQuery() hook. Top: {', '.join(top)}{extra}",
                count=len(feh501_files), examples=top)

    if feh503_files:
        top = feh503_files[:5]
        extra = f" +{len(feh503_files) - 5} more" if len(feh503_files) > 5 else ""
        rep.add(YEL, "FEH503", "react", "frontend/",
                f"{len(feh503_files)} files use direct DOM/window access",
                intended=f"Isolate browser APIs in hooks. Top: {', '.join(top)}{extra}",
                count=len(feh503_files), examples=top)

    if feh201_files:
        top = feh201_files[:5]
        extra = f" +{len(feh201_files) - 5} more" if len(feh201_files) > 5 else ""
        rep.add(YEL, "FEH201", "frontend", "frontend/",
                f"{len(feh201_files)} files have console/debugger statements",
                intended=f"Remove before merge; use structured logger. Top: {', '.join(top)}{extra}",
                count=len(feh201_files), examples=top)

    if feh802_files:
        top = feh802_files[:5]
        extra = f" +{len(feh802_files) - 5} more" if len(feh802_files) > 5 else ""
        rep.add(YEL, "FEH802", "frontend", "frontend/",
                f"{len(feh802_files)} files use raw <img> without next/image",
                intended=f"Use next/image for lazy loading + WebP. Top: {', '.join(top)}{extra}",
                count=len(feh802_files), examples=top)
        
# ============================================================================
# 7. DEPLOYMENT HEALTH
# ============================================================================


def check_deployment_health(repo: Path, rep: Report, eff: dict) -> None:
    if not (repo / "Dockerfile").exists() and not (repo / "backend" / "Dockerfile").exists():
        rep.add(YEL, "DP101", "deployment", "repo",
                "no Dockerfile found",
                intended="add multi-stage Dockerfile")
    if not (repo / ".dockerignore").exists():
        rep.add(YEL, "DP105", "deployment", "repo",
                "missing .dockerignore",
                intended="exclude .git, node_modules, __pycache__, .venv, uploads")

    for compose_name in ["docker-compose.yml", "docker-compose.prod.yml"]:
        compose = repo / compose_name
        if compose.exists():
            text = read_text(compose) or ""
            if "healthcheck" not in text:
                rep.add(YEL, "DP102", "deployment", compose_name,
                        f"{compose_name} missing healthcheck",
                        intended="add healthcheck with test/interval/timeout/retries")

    backend = repo / "backend"
    if backend.exists():
        has_env = False
        for f in iter_files(backend, PYTHON_EXT):
            text = read_text(f) or ""
            if "BaseSettings" in text or "pydantic_settings" in text:
                has_env = True
                break
        if not has_env:
            rep.add(YEL, "DP103", "deployment", "backend/",
                    "no env var validation at startup",
                    intended="use pydantic BaseSettings; fail fast on missing vars")

    main_py = backend / "main.py"
    if main_py.exists():
        text = read_text(main_py) or ""
        if "SIGTERM" not in text and "graceful" not in text and "on_shutdown" not in text:
            rep.add(YEL, "DP104", "deployment", "backend/main.py",
                    "no graceful shutdown handler",
                    intended="handle SIGTERM/SIGINT; drain connections; flush logs")


# ============================================================================
# 8. PIPELINE HEALTH
# ============================================================================


def check_pipeline_health(repo: Path, rep: Report, eff: dict) -> None:
    components = [
        (".github/workflows", "GitHub Actions"),
        (".gitlab-ci.yml", "GitLab CI"),
        ("Makefile", "Makefile"),
        ("docker-compose.yml", "docker-compose"),
        ("scripts/deploy.sh", "deploy script"),
        ("scripts/health-check.sh", "health-check script"),
        ("backend/tests", "backend tests"),
        ("frontend/web_app/e2e", "frontend e2e"),
    ]
    missing = []
    present = []
    for path_value, label in components:
        if (repo / path_value).exists():
            present.append(label)
        else:
            missing.append(label)

    if present:
        rep.add(GRN, "PL100", "pipeline", "repo",
                f"present: {', '.join(present)}")
    if missing:
        rep.add(YEL, "PL101", "pipeline", "repo",
                f"missing: {', '.join(missing)}",
                intended="CI: lint → audits → tests → build → security → staging → e2e → canary")


# ============================================================================
# 9. RUNTIME PROBING
# ============================================================================


def check_runtime_health(repo: Path, rep: Report, eff: dict,
                         base_url: str | None, timeout: float) -> None:
    if not base_url:
        return
    rep.add(GRN, "RT000", "runtime", base_url, "runtime probe enabled")
    base = base_url.rstrip("/")
    for path in ["/health", "/api/health", "/api/v1/health", "/openapi.json"]:
        url = base + path
        start = time.time()
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "zozi-health-audit",
                "Accept": "application/json, text/plain, */*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as response:
                ms = int((time.time() - start) * 1000)
                status = getattr(response, "status", 200)
                if status == 200:
                    if ms > 1000:
                        rep.add(YEL, "RT201", "runtime", url, f"slow ({ms}ms)",
                                intended="add caching / query optimization")
                    else:
                        rep.add(GRN, "RT200", "runtime", url, f"healthy ({ms}ms)")
                elif status >= 500:
                    rep.add(RED, "RT500", "runtime", url, f"server error {status}")
                else:
                    rep.add(YEL, "RT400", "runtime", url, f"status {status}")
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                rep.add(YEL, "RT404", "runtime", url, "health endpoint missing",
                        intended="add /health returning db/queue/storage status")
            else:
                rep.add(RED, "RT500", "runtime", url, f"HTTP {exc.code}")
        except Exception as exc:
            rep.add(RED, "RT500", "runtime", url, f"cannot connect: {exc}")
            break


# ============================================================================
# 10. FILE HEALTH RANKING
# ============================================================================


def compute_file_health_scores(rep: Report) -> list[tuple[str, int, list[str]]]:
    """Rank files by weighted finding count. Returns top 20."""
    file_weights: dict[str, int] = defaultdict(int)
    file_codes: dict[str, set[str]] = defaultdict(set)

    weight_map = {P0: 10, P1: 5, P2: 2, P3: 1}

    for f in rep.findings:
        if f.path and f.path not in {"repo", "frontend/", "backend/", "CI/CD"}:
            w = weight_map.get(f.priority, 1) * f.count
            file_weights[f.path] += w
            file_codes[f.path].add(f.code)

    ranked = sorted(file_weights.items(), key=lambda x: -x[1])[:20]
    return [(path, score, sorted(file_codes[path])) for path, score in ranked]


# ============================================================================
# 11. EXECUTIVE SUMMARY
# ============================================================================


def generate_executive_summary(rep: Report, score: int, grade: str) -> str:
    priority_counts = {P0: 0, P1: 0, P2: 0, P3: 0}
    for f in rep.findings:
        priority_counts[f.priority] += f.count

    # Quick wins: P1 findings that affect few files
    quick_wins = []
    code_files: dict[str, int] = defaultdict(int)
    for f in rep.findings:
        if f.priority in {P0, P1}:
            code_files[f.code] += f.count

    for code, count in sorted(code_files.items(), key=lambda x: x[1]):
        meaning = RULE_MEANING.get(code, code)
        if count <= 10:
            quick_wins.append(f"- **{code}** ({count} files): {meaning}")
        if len(quick_wins) >= 5:
            break

    lines = [
        "## Executive Summary",
        "",
        f"**Health Score: {score}/100 ({grade})**",
        "",
        "| Priority | Count | Action |",
        "|---|---:|---|",
        f"| 🔴 P0 (fix today) | {priority_counts[P0]} | Production / security risk |",
        f"| 🟠 P1 (fix this sprint) | {priority_counts[P1]} | Scaling / performance risk |",
        f"| 🟡 P2 (fix this month) | {priority_counts[P2]} | Maintainability / structure |",
        f"| 🟢 P3 (fix when convenient) | {priority_counts[P3]} | Hygiene / style |",
    ]

    if quick_wins:
        lines.extend(["", "### Quick Wins (< 1 hour each)", ""])
        lines.extend(quick_wins)

    return "\n".join(lines)


# ============================================================================
# 12. AI HEALTH CONTRACT (Python + JS Polyglot)
# ============================================================================


def generate_health_contract() -> str:
    return """
## AI Health & Scaling Objective Contract

### Python + JS Polyglot Strategy (NOT Python vs JS)

Python and JS **together** are faster than either alone:

| Workload | Best Tool | Why |
|---|---|---|
| Business logic / orchestration | **Python** (FastAPI) | Readability, DB, ecosystem |
| Database operations | **Python** (SQLAlchemy) | ORM, migrations, RLS |
| ML / AI inference | **Python** (PyTorch) | Model ecosystem |
| File / media processing | **Python worker** (Celery/arq) | Background, not request path |
| High-throughput JSON | **Python + orjson** or **Node.js sidecar** | 3-10x faster than stdlib |
| Real-time WebSocket gateway | **Node.js** gateway + Python backend | Node handles 100k+ connections |
| Edge / CDN functions | **Node.js** (Cloudflare/Vercel) | Cold start < 5ms |
| Frontend rendering | **React / Next.js** | Component model, SSR/SSG |
| Client-side CPU work | **Web Worker** or **WASM** | Keep main thread free |

### Scaling Rules
- Every list endpoint must have pagination.
- Never do N individual DB ops in a loop — use bulk/batch.
- Add caching for repeated expensive reads.
- Add rate limiting on public endpoints.
- Offload heavy operations to background jobs (return 202).
- Use streaming for large responses.
- Always set timeout + retry + circuit breaker on external calls.

### Logging & Observability
- No `print()` in backend application code.
- Use structured logging with request_id, domain, duration_ms.
- Never log secrets/tokens/passwords.
- Every caught error: `logger.exception(...)` with context.

### Error Handling
- No bare `except:`. No swallowed exceptions.
- DB writes must roll back on failure.
- API endpoints return controlled errors, not stack traces.

### React Rules
- No `console.log` / `debugger` in production.
- Stable keys for lists (never index).
- React Query/SWR for data fetching.
- Error boundaries at app and route level.
- `next/image` for all images.
- `React.lazy` + `Suspense` for route-level code splitting.
- Virtualization for lists > 100 items.
- Web Workers for CPU-heavy transforms.

### Deployment Rules
- Dockerfile with multi-stage build.
- Healthcheck in docker-compose.
- Validate env vars at startup (pydantic BaseSettings).
- Handle SIGTERM for graceful shutdown.
"""


def generate_pipeline_mermaid() -> str:
    return """
```mermaid
graph TD
    PR["Pull Request"] --> LINT["Lint / Format"]
    LINT --> ARCH["architecture_audit"]
    ARCH --> DB["database_audit"]
    DB --> DESIGN["design_audit"]
    DESIGN --> HEALTH["health_audit"]
    HEALTH --> UNIT["Unit Tests"]
    UNIT --> INTEGRATION["Integration Tests"]
    INTEGRATION --> BUILD["Build BE + FE"]
    BUILD --> SECURITY["Security Scan"]
    SECURITY --> STAGE["Deploy Staging"]
    STAGE --> E2E["E2E Tests"]
    E2E --> PERF["Perf Smoke"]
    PERF --> CANARY["Canary"]
    CANARY --> PROD["Production"]
    PROD --> OBSERVE["Metrics / Logs / Traces"]
    OBSERVE --> ROLLBACK["Rollback if SLO breach"]
```
"""


def generate_fix_patterns_section() -> str:
    lines = ["## Fix Patterns (Before → After)", ""]
    for code, pattern in FIX_PATTERNS.items():
        meaning = RULE_MEANING.get(code, code)
        lines.extend([
            f"### {code}: {meaning}",
            "",
            f"**Before:**",
            f"```",
            f"{pattern['before']}",
            f"```",
            f"**After:**",
            f"```",
            f"{pattern['after']}",
            f"```",
            f"**Action:** {pattern['action']}",
            "",
        ])
    return "\n".join(lines)


# ============================================================================
# 13. TREND SUPPORT
# ============================================================================


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def update_trend(path: Path, current: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")


def print_trend(rep: Report, current: dict, baseline: dict | None) -> None:
    if not baseline:
        print("\nNo health trend baseline. Use --update-trend to create one.")
        return

    old_score = int(baseline.get("health_score", 0))
    new_score = int(current.get("health_score", 0))
    old_red = int(baseline.get("red", 0))
    new_red = int(current.get("red", 0))

    print("\n" + "=" * 78)
    print("  HEALTH TREND")
    print("=" * 78)
    print(f"  SCORE: {old_score} -> {new_score}   RED: {old_red} -> {new_red}")

    old_codes = baseline.get("by_code", {})
    new_codes = current.get("by_code", {})
    regs, imps = [], []
    for code in sorted(set(old_codes) | set(new_codes)):
        d = int(new_codes.get(code, 0)) - int(old_codes.get(code, 0))
        if d > 0:
            regs.append((code, d))
        elif d < 0:
            imps.append((code, d))
    if regs:
        print("  Regressions:  " + ", ".join(f"+{d} {c}" for c, d in regs))
    if imps:
        print("  Improvements: " + ", ".join(f"{d} {c}" for c, d in imps))


# ============================================================================
# 14. SCORE / SUMMARY / RENDERING
# ============================================================================

def compute_health_score(rep: Report) -> tuple[int, str]:
    import math

    red = sum(f.count for f in rep.findings if f.sev == RED)
    yel = sum(f.count for f in rep.findings if f.sev == YEL)

    score = 100.0
    score -= min(40, red * 3.0)
    score -= min(30, math.log2(yel + 1) * 3.0)
    score -= min(10, red * 0.5)
    score = max(0, int(score))

    if score >= 90:
        grade = "A"
    elif score >= 75:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    return score, grade

def build_summary(repo: Path, rep: Report, score: int, grade: str) -> dict:
    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": str(repo),
        "health_score": score,
        "grade": grade,
        "red": sum(f.count for f in rep.findings if f.sev == RED),
        "yellow": sum(f.count for f in rep.findings if f.sev == YEL),
        "green": sum(f.count for f in rep.findings if f.sev == GRN),
        "by_code": dict(rep.counters),
        "by_priority": {
            p: sum(f.count for f in rep.findings if f.priority == p)
            for p in [P0, P1, P2, P3]
        },
    }


def render_markdown(repo: Path, rep: Report, out: Path, summary: dict) -> None:
    score = summary["health_score"]
    grade = summary["grade"]
    red = summary["red"]
    yel = summary["yellow"]
    grn = summary["green"]

    file_ranking = compute_file_health_scores(rep)

    L = [
        "# ZOZI Health & Scaling Audit Report (GENERATED — do not hand-edit)",
        "",
        f"**Repo:** `{repo}`  ",
        f"**Health Score:** `{score}/100` ({grade})  ",
        f"**Result:** 🔴 {red} · 🟡 {yel} · 🟢 {grn}  ",
        "**Ephemeral. Add to `.gitignore`.**",
        "",
        "---",
        "",
        generate_executive_summary(rep, score, grade),
        "",
        "---",
        "",
        "## Top 20 Unhealthiest Files",
        "",
        "| # | File | Weight | Issues |",
        "|---|---|---:|---|",
    ]

    for i, (path, weight, codes) in enumerate(file_ranking, 1):
        L.append(f"| {i} | `{path}` | {weight} | {', '.join(codes)} |")

    L.extend([
        "",
        "---",
        "",
        generate_health_contract(),
        "",
        "---",
        "",
        "## Recommended Pipeline",
        "",
        generate_pipeline_mermaid(),
        "",
        "---",
        "",
        generate_fix_patterns_section(),
        "",
        "---",
        "",
        "## Scorecard",
        "",
        "| Code | Count | Priority | Sev | Meaning |",
        "|---|---:|---|---|---|",
    ])

    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        pri = RULE_PRIORITY.get(code, P3)
        L.append(
            f"| {code} | {rep.counters[code]} | {PRIORITY_ICON[pri]} {pri} "
            f"| {SEV_ICON[sev]} {sev} | {RULE_MEANING.get(code, '')} |"
        )

    # Hotlist: P0 + P1 only
    hot = sorted(
        [f for f in rep.findings if f.priority in {P0, P1}],
        key=lambda f: (f.priority, f.code),
    )

    L.extend([
        "",
        "## 🔥 Health Hotlist (P0 + P1 only)",
        "",
        "| Pri | Sev | Rule | Domain | Location | Problem | Suggestion |",
        "|---|---|---|---|---|---|---|",
    ])

    for f in hot:
        L.append(
            f"| {PRIORITY_ICON[f.priority]} {f.priority} | {SEV_ICON[f.sev]} | {f.code} "
            f"| {f.domain} | `{f.loc()}` | {f.message} | {f.intended or '-'} |"
        )

    # Frontend findings grouped by domain
    fe_findings = [f for f in rep.findings if f.domain.startswith("frontend/")]
    if fe_findings:
        fe_by_domain: dict[str, list[Finding]] = defaultdict(list)
        for f in fe_findings:
            fe_by_domain[f.domain].append(f)

        L.extend(["", "## Frontend Findings by Domain", ""])
        for dom in sorted(fe_by_domain.keys()):
            items = fe_by_domain[dom]
            L.append(f"### {dom} ({len(items)} findings)")
            L.append("")
            for f in items:
                L.append(
                    f"- {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}"
                    + (f" → *{f.intended}*" if f.intended else "")
                )
            L.append("")

    # Per-domain breakdown (non-frontend)
    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        if not f.domain.startswith("frontend/"):
            by_dom[f.domain].append(f)

    for dom in [
        "python", "performance", "concurrency", "polyglot", "scaling",
        "api-health", "logging", "error-handling", "security",
        "documentation", "observability", "memory", "deployment",
        "pipeline", "runtime", "react",
    ]:
        items = by_dom.get(dom, [])
        if not items:
            continue
        L.extend(["", f"## Domain: {dom}", ""])
        for f in items:
            L.append(
                f"- {PRIORITY_ICON[f.priority]} {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}"
                + (f" → *{f.intended}*" if f.intended else "")
            )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def render_stdout(repo: Path, rep: Report, summary: dict) -> int:
    score = summary["health_score"]
    grade = summary["grade"]
    red = summary["red"]
    yel = summary["yellow"]
    grn = summary["green"]
    by_pri = summary.get("by_priority", {})

    print("=" * 78)
    print("  ZOZI HEALTH & SCALING AUDIT v3.0")
    print("  python+js polyglot · scaling · observability · security · react · deploy")
    print("=" * 78)
    print(f"  repo: {repo}")
    print(f"  health score: {score}/100 ({grade})")
    print(f"  [RED] {red}    [YEL] {yel}    [GRN] {grn}")
    print(f"  P0={by_pri.get(P0, 0)}  P1={by_pri.get(P1, 0)}  P2={by_pri.get(P2, 0)}  P3={by_pri.get(P3, 0)}")
    print("  by rule: " + ", ".join(f"{k}={v}" for k, v in sorted(rep.counters.items())))

    # File ranking
    file_ranking = compute_file_health_scores(rep)
    if file_ranking:
        print("-" * 78)
        print("  TOP 10 UNHEALTHIEST FILES")
        print("-" * 78)
        for i, (path, weight, codes) in enumerate(file_ranking[:10], 1):
            print(f"  {i:2d}. [{weight:3d}] {path}")
            print(f"      {', '.join(codes)}")

    # Hotlist: P0 + P1
    hot = sorted(
        [f for f in rep.findings if f.priority in {P0, P1}],
        key=lambda f: (f.priority, f.code),
    )

    print("-" * 78)
    print(f"  HOTLIST: P0 + P1 ({len(hot)} items)")
    print("-" * 78)

    for f in hot[:60]:
        print(f"  {PRIORITY_ICON[f.priority]} {f.code:<7} [{f.domain:<14}] {f.loc()}")
        print(f"        {f.message}")
        if f.intended:
            print(f"        -> {f.intended}")

    if len(hot) > 60:
        print(f"  ... +{len(hot) - 60} more (see full report)")

    print("=" * 78)
    return sum(1 for f in rep.findings if f.sev == RED)


# ============================================================================
# 15. MAIN
# ============================================================================


def main() -> int:
    ap = argparse.ArgumentParser(
        description="ZOZI production-ready health, scaling & polyglot auditor v3.0."
    )
    ap.add_argument("--root", default=None, help="repo root")
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--json", default=None, help="write findings JSON")
    ap.add_argument("--no-write", action="store_true", help="do not write markdown report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--base-url", default=None, help="optional runtime base URL to probe")
    ap.add_argument("--probe-timeout", type=float, default=4.0, help="probe timeout seconds")
    ap.add_argument("--ci", action="store_true", help="CI mode")
    ap.add_argument("--trend-file", default=None, help="health trend JSON file")
    ap.add_argument("--update-trend", action="store_true", help="overwrite trend baseline")

    args = ap.parse_args()
    repo = find_repo(args.root)

    if args.ci:
        if not args.json:
            args.json = str(repo / "out" / "governance" / "health_audit.json")
        if not args.out and not args.no_write:
            args.out = str(repo / "out" / "governance" / "health_audit_report.md")
        if not args.trend_file:
            args.trend_file = str(repo / ".governance" / "health_trend.json")

    eff: dict[str, Any] = {}
    rep = Report()

    check_python_health(repo, rep, eff)
    check_deployment_health(repo, rep, eff)
    check_frontend_health(repo, rep, eff)
    check_pipeline_health(repo, rep, eff)
    check_runtime_health(repo, rep, eff, args.base_url, args.probe_timeout)

    score, grade = compute_health_score(rep)
    summary = build_summary(repo, rep, score, grade)

    # Trend
    trend_path = Path(args.trend_file).resolve() if args.trend_file else None
    if trend_path:
        if args.update_trend:
            update_trend(trend_path, summary)
            print(f"\nTrend updated: {trend_path}")
        else:
            baseline = read_json(trend_path)
            print_trend(rep, summary, baseline)

    red_count = render_stdout(repo, rep, summary)

    if not args.no_write:
        out = resolve_output_path(repo, args.out, "HEALTH_AUDIT_REPORT.md")
        render_markdown(repo, rep, out, summary)
        print(f"\nReport written: {out}")

    if args.json:
        jp = resolve_output_path(repo, args.json, "health_audit.json")
        jp.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": summary,
            "file_ranking": [
                {"file": p, "weight": w, "codes": c}
                for p, w, c in compute_file_health_scores(rep)
            ],
            "findings": [
                {
                    "sev": f.sev, "code": f.code, "domain": f.domain,
                    "path": f.path, "line": f.line, "message": f.message,
                    "intended": f.intended, "priority": f.priority,
                    "count": f.count, "examples": f.examples,
                }
                for f in rep.findings
            ],
        }
        jp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written: {jp}")

    return 1 if (red_count and not args.no_fail) else 0


if __name__ == "__main__":
    sys.exit(main())
