#!/usr/bin/env python3
"""
system_architecture_audit.py — READ-ONLY, repo-wide architecture governance auditor.

Version:
  v3.2 — Auto-Discovery Governance Edition

Purpose:
  ZOZI architecture governance engine.

This is a single complete script.

It validates:
  1. Repository structure
  2. Backend layer boundaries
  3. Forbidden dependency edges
  4. Circular dependencies
  5. Domain ownership / bounded-context leakage when explicit YAML policy exists
  6. Dead / orphan modules
  7. Architecture hotspots via fan-in / fan-out
  8. Duplicate module and class names
  9. Package shape (__init__.py, missing packages, flat-layer disease)
 10. Surface-vs-domain sub-folder rules
 11. Repository hygiene (cache, logs, lockfiles, secrets, artifacts)
 12. Documentation allow-lists
 13. Trend reporting over time
 14. Dynamic import / eval / exec detection
 15. YAML policy self-validation
 16. Architecture debt score
 17. Frontend workspace scaling checks
 18. Automatic feature/domain discovery
 19. Safe self-learning auto-policy

Design principles:
  * READ-ONLY with respect to source code.
  * Does NOT import application code.
  * Uses stdlib `ast` for Python static analysis.
  * YAML is optional and preferred when present.
  * Embedded rules are fallback.
  * Auto-policy is safe recognition only.
  * RED is reserved for high-confidence architectural violations.
  * Auto-discovery does not aggressively recommend refactors.
  * Logical domains `database` and `security` live INSIDE backend/.
  * Sub-folder axis:
      - SURFACE in routers/ and controllers/  (admin/supplier/customer/...)
      - DOMAIN in services/ and models/       (finance/orders/catalog/...)

Severity:
  [RED] VIOLATION   high-confidence architectural / structural / security problem
  [YEL] ADVISORY    likely drift / maintainability / scaling warning
  [GRN] INFO        summary / metric / healthy signal / discovered feature

Output:
  * stdout scorecard + damage hotlist + domain sections + metrics
  * optional Markdown report
  * optional JSON report for CI/tooling
  * optional metrics JSON
  * optional trend file comparison / update
  * auto-policy file for safe feature/domain learning

Auto-policy:
  .governance/zozi_auto_policy.json

Usage:
  python backend/scripts/system_architecture_audit.py --no-fail --show-intended

  # first baseline
  python backend/scripts/system_architecture_audit.py --ci --update-trend --show-intended

  # regular CI gate
  python backend/scripts/system_architecture_audit.py --ci

  # reset learned auto-policy
  python backend/scripts/system_architecture_audit.py --reset-auto-policy --ci
"""

from __future__ import annotations

import argparse
import ast
import datetime
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# ============================================================================
# 1. DEFAULT EMBEDDED RULES
# ============================================================================

DEFAULT_IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "htmlcov",
    ".next",
    ".expo",
    ".kotlin",
    "gradle",
    "android",
    "ios",
    ".idea",
    ".vscode",
    "test-results",
    ".playwright-artifacts-0",
    "playwright-out",
    "static-tmp",
    ".web-build-test",
    "artifacts",
    "uploads",
    ".turbo",
    "dist",
    "build",
    "coverage",
    "playwright-report",
    "test-output",
    "tmp",
}

DEFAULT_CACHE_DIR_NAMES = {
    ".ruff_cache",
    ".mypy_cache",
    ".pytest_cache",
    ".next",
    ".expo",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".turbo",
    "web-dist",
    ".playwright-artifacts-0",
    "test-results",
    "playwright-report",
    "test-output",
}

DEFAULT_TEXT_EXT = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".ini",
    ".toml",
    ".css",
    ".html",
    ".sh",
    ".bat",
    ".ps1",
    ".cjs",
    ".mjs",
}

DEFAULT_SOURCE_EXT = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".sh",
    ".bat",
    ".ps1",
}

DEFAULT_FRONTEND_SOURCE_EXT = {
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".cjs",
    ".mjs",
}

DEFAULT_MAX_READ_BYTES = 2_000_000

DEFAULT_SCRATCH_PHRASES = [
    "countdivs",
    "stackdivs",
    "printlines",
    "linenums",
    "fixtailwind",
    "patch-vars",
    "patch_vars",
    "verify-tmp",
    "verify_tmp",
    "impmain",
    "client_tmp",
    "reset_tmp",
]

DEFAULT_SCRATCH_TOKENS = [
    "tmp",
    "temp",
    "scratch",
    "debug",
    "test",
    "check",
    "write",
    "list",
    "reset",
    "verify",
    "run",
    "script",
    "probe",
    "diag",
    "inspect",
]

DEFAULT_SCRIPTS_SAFE_TOKENS = {
    "tmp",
    "temp",
    "scratch",
    "debug",
    "diag",
    "inspect",
}

DEFAULT_BACKEND_ROOT_ALLOW = {
    "__init__.py",
    "main.py",
    "lifespan.py",
    "run_server.py",
    "start_server.py",
}

DEFAULT_ALLOW_ROOT_MD = {
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "LICENSE.md",
    "LICENSE",
}

DEFAULT_ALLOW_DOCS_ROOT = {
    "scope",
    "archive",
    "README.md",
    "DOCUMENTATION_INDEX.md",
    "INDEX.md",
}

DEFAULT_FORBIDDEN_ROOT = {
    "backend": [
        r".*\.(log|db|db-shm|db-wal)$",
        r"^token\.tmp$",
        r"^.*\.(json|txt)$",
    ],
    "backend/alembic": [
        r"^_.*\.py$",
    ],
    "frontend": [
        r".*\.(log|tsbuildinfo)$",
    ],
    "frontend/web_app": [
        r".*\.bak$",
        r"\.tsbuildinfo$",
        r"^build_final.*$",
        r"^build_out.*$",
        r"^build_log\.txt$",
        r"^_audit_.*\.cjs$",
        r"^verify_.*\.cjs$",
        r"^debug.*\.spec\.ts$",
        r"^diag.*\.spec\.ts$",
        r"^inspect-playwright\.cjs$",
        r"^playwright-results\.txt$",
        r".*_test(_output|_verbose)?\.txt$",
        r".*\.(png|jpe?g)$",
        r"^-w$",
        r".*\.log$",
    ],
    "frontend/mobile_app": [
        r".*\.log$",
        r"^expo-err\.log$",
        r"^expo-start\.log$",
    ],
    ".": [
        r"^Working_API$",
        r"^provider_test$",
        r"^_trash$",
        r"^backup_\d+",
        r"^image$",
        r"^zozi-logo-app$",
        r".*\.zip$",
        r"^login_form\.yml$",
        r"^login_rsp\.json$",
        r"^zozi\.db(-shm|-wal)?$",
        r"^dev\.db$",
        r"^.*\.log$",
        r"^_orchestrator_read\.py$",
        r"^fix_.*\.py$",
        r"^generate_.*\.py$",
        r"^problems\.txt$",
        r"^mobile_app\.html$",
    ],
    "documents": [],
}

DEFAULT_FORBIDDEN_ANY = {
    "backend": [
        r"/db/migrations/",
        r"(^|/)employee_models\.py$",
        r"/log/.*\.(log|txt)$",
    ],
    "backend/db": [
        r"/migrations/",
        r"(^|/)employee_models\.py$",
    ],
    "backend/alembic": [
        r"/versions/.*stub.*\.py$",
    ],
    "frontend/mobile_app/scripts": [
        r".*\.(log|err)$",
    ],
}

DEFAULT_FORBIDDEN_EDGES = {
    "controllers": [
        "db.database",
        "db.create_tables",
        "db.init_db",
    ],
    "services": [
        "routers",
        "controllers",
    ],
    "models": [
        "routers",
        "controllers",
        "services",
    ],
    "providers": [
        "routers",
        "controllers",
        "services",
    ],
}

DEFAULT_MIS_HOUSED_CONTROLLERS = [
    "audit_controller",
    "payments_controller",
    "cache_utils",
]

DEFAULT_WRITE_VERBS = {
    "add",
    "commit",
    "delete",
    "merge",
    "flush",
    "refresh",
}

DEFAULT_READ_VERBS = {
    "query",
}

DEFAULT_KNOWN_WRITER_CONTROLLERS = {
    "audit_controller.py",
}

DEFAULT_SECRET_FILE_PATTERNS = [
    r"(^|/)token\.tmp$",
    r"(^|/)\.env$",
    r"(^|/).*\.(key|pem|p12|pfx|secret)$",
    r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$",
    r"(^|/).*credentials.*\.(json|ya?ml)$",
]

DEFAULT_ENV_SECRET_KEYS = r"""os\.environ\.(?:get\(\s*|[\[])\s*["'](APP_ENV|SECRET_KEY|JWT_SECRET|DATABASE_URL|DB_PASSWORD|REDIS_URL|HF_API_TOKEN|STRIPE_SECRET|AWS_SECRET|ENCRYPTION_KEY|TOKEN|PASSWORD)"""

DEFAULT_LOCAL_PATH = r"""[A-Za-z]:[\\/](?:Users|Projects|home|Documents|Desktop|recovery_recuva)[\\/]|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/"""

DEFAULT_MEDIA_DISK_WRITE = r"""open\(\s*(?:f?["'][^"']*uploads/|.*upload_dir)"""

DEFAULT_MEDIA_DISK_URL = r"""image_url\s*=\s*f?["']\{?\s*upload_dir"""

DEFAULT_LOCKFILES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}

DEFAULT_ARTIFACT_EXTS = {
    ".log",
    ".db-shm",
    ".db-wal",
    ".tsbuildinfo",
}

DEFAULT_ARTIFACT_NAMES = {
    "schema-audit-report.json",
    "vision_cache.json",
    "alembic_test.json",
    "_import_test_out.txt",
    "playwright-results.txt",
    "backend.log",
    "server_stderr.log",
    "server_stdout.log",
    "run_log.txt",
}

DEFAULT_DUP_IGNORE_BASENAMES = {
    "__init__",
    "conftest",
}

DEFAULT_CANONICAL_HOME = {
    "database.py": "db/database.py",
    "schemas.py": "db/schemas.py",
    "config.py": "utils/config.py",
    "auth.py": "utils/auth.py",
    "email_service.py": "utils/email_service.py",
}

DEFAULT_SURFACE_NAMES = {
    "admin",
    "supplier",
    "customer",
    "public",
    "webhooks",
    "webhook",
    "api",
    "internal",
    "external",
}

DEFAULT_DOMAIN_LAYERS = {
    "services",
    "models",
}

DEFAULT_OWNERSHIP_LAYERS = {
    "services",
    "models",
}

DEFAULT_GRAPH_EXEMPT_LAYERS = {
    "tests",
    "scripts",
    "alembic",
    "monitoring",
    "docs",
    "data",
}

DEFAULT_DEAD_EXEMPT_LAYERS = {
    "tests",
    "scripts",
    "alembic",
    "middleware",
    "dependencies",
    "providers",
    "events",
    "jobs",
    "data",
    "monitoring",
    "docs",
}

DEFAULT_DEAD_AUDIT_LAYERS = {
    "services",
    "models",
    "controllers",
    "routers",
    "providers",
    "utils",
    "events",
    "jobs",
}

DEFAULT_DEAD_ENTRYPOINTS = [
    r"^main$",
    r"^lifespan$",
    r"^run_server$",
    r"^start_server$",
    r"^routers(\.|$)",
    r"^alembic\.env$",
    r"^scripts(\.|$)",
    r"^tests(\.|$)",
    r"^middleware(\.|$)",
    r"^dependencies(\.|$)",
    r"^providers(\.|$)",
    r"^events(\.|$)",
    r"^jobs(\.|$)",
    r"^data(\.|$)",
    r"^db\.base$",
    r"^db\.database$",
]

DEFAULT_DUP_CLASS_IGNORE = {
    "Base",
    "Metadata",
    "Config",
    "Enum",
    "Schema",
    "Model",
    "Table",
    "Mixin",
    "Settings",
    "Exception",
    "Error",
}

DEFAULT_EXPECTED_BACKEND_PACKAGES = [
    "routers",
    "controllers",
    "services",
    "models",
    "middleware",
    "dependencies",
    "providers",
    "utils",
    "db",
    "alembic",
    "tests",
    "scripts",
    "events",
    "jobs",
    "data",
]

DEFAULT_NO_INIT_DIRS = {
    "scripts",
    "tests",
    "alembic",
    "data",
    "monitoring",
    "docs",
}

DEFAULT_FRONTEND_WORKSPACES = {
    "web_app",
    "mobile_app",
    "shared",
}

DEFAULT_FRONTEND_ROOT_ALLOW = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pnpm-workspace.yaml",
    "tsconfig.json",
    "tsconfig.build.json",
    "next.config.ts",
    "next-env.d.ts",
    "middleware.ts",
    "eslint.config.js",
    "jest.config.js",
    "jest.setup.ts",
    "playwright.config.ts",
    "postcss.config.js",
    "tailwind.config.js",
    "babel.config.js",
    "metro.config.js",
    "app.config.js",
    "app.json",
    "expo-env.d.ts",
    "README.md",
    "ERROR_HANDLING.md",
    "Dockerfile",
    "sentry.config.ts",
    "patch-logbox.js",
}

DEFAULT_FLAT_THRESHOLD = 30
DEFAULT_LARGE_SUBPACKAGE_THRESHOLD = 80
DEFAULT_GOD_FAN_OUT = 20
DEFAULT_GOD_FAN_IN = 30
DEFAULT_MAX_CYCLES = 80
DEFAULT_MAX_CYCLE_LENGTH = 10
DEFAULT_FRONTEND_FLAT_THRESHOLD = 40
DEFAULT_FRONTEND_LARGE_FOLDER_THRESHOLD = 120

FEATURE_STOP_NAMES = {
    "__init__",
    "index",
    "page",
    "layout",
    "loading",
    "error",
    "not-found",
    "route",
    "main",
    "app",
    "init",
    "package",
    "types",
    "utils",
    "helpers",
    "shared",
    "common",
    "ui",
    "admin",
    "supplier",
    "customer",
    "public",
    "webhooks",
    "webhook",
    "api",
    "internal",
    "external",
    "src",
    "components",
    "features",
    "hooks",
    "lib",
    "services",
    "models",
    "controllers",
    "routers",
}

FEATURE_SUFFIXES = [
    "_service",
    "_services",
    "_controller",
    "_controllers",
    "_router",
    "_routers",
    "_model",
    "_models",
    "_provider",
    "_providers",
    "_event",
    "_events",
    "_job",
    "_jobs",
    "_page",
    "_pages",
    "_screen",
    "_screens",
    "_component",
    "_components",
    "_hook",
    "_hooks",
    "_store",
    "_stores",
    "_api",
    "_utils",
    "_helpers",
    "_types",
    "_test",
    "_tests",
    "_spec",
]


# ============================================================================
# 2. FINDING MODEL + RULE DICTIONARY
# ============================================================================

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"

SEV_ICON = {
    RED: "🔴",
    YEL: "🟡",
    GRN: "🟢",
}

SEV_TAG = {
    RED: "[RED]",
    YEL: "[YEL]",
    GRN: "[GRN]",
}

HOTLIST_RULES = {
    "W1",
    "W2",
    "W3",
    "W4",
    "Q1",
    "M1",
    "R1",
    "G1",
    "X1",
    "D1",
    "D2",
    "D3",
    "S1",
    "S2",
    "S3",
    "S4",
    "S5",
    "M2",
    "M3",
    "M4",
    "L1",
    "A1",
    "A2",
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "H1",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "G0",
    "DG",
    "DG2",
    "DG3",
    "DG4",
    "DG5",
    "CFG1",
    "CFG2",
    "CFG3",
    "CFG4",
    "MET1",
    "FE1",
    "FE2",
    "FE3",
    "FE4",
    "FE5",
    "AUTO0",
    "AUTO3",
    "AUTO6",
    "AUTO8",
    "AUTO10",
    "NM",
}

RULE_MEANING = {
    "W1": "controller/router writes to DB (must be a service)",
    "W2": "misnamed writer-controller -> relocate to services/",
    "W3": "imports a mis-housed controller (logic belongs in services/utils)",
    "W4": "controller imports another controller (shared logic -> service/util)",
    "Q1": "controller/router reads via db.query (delegate)",
    "M1": "ORM model outside models/ package",
    "R1": "APIRouter instantiated outside routers/",
    "G1": "second migrations home / dual schema-creator",
    "X1": "ghost/duplicate backend skeleton",
    "D1": "duplicate module basename within backend (import-shadow)",
    "D2": "duplicate module basename across top dirs",
    "D3": "duplicate class name across modules",
    "S1": "services/ is flat (needs domain sub-packages)",
    "S2": "overlapping service stems (ownership ambiguity)",
    "S3": "routers/controllers flat (group by surface)",
    "S4": "surface sub-folder in services/ (must be domain)",
    "S5": "service domain sub-package too large (split bounded context)",
    "M2": "models/ is flat (group by domain)",
    "M3": "surface sub-folder in models/ (must be domain)",
    "M4": "models domain sub-package too large",
    "L1": "multiple RLS enforcers (fail-open risk)",
    "A1": "architecture hotspot (high coupling / instability)",
    "A2": "possibly dead/orphan module (no inbound imports; not an entrypoint)",
    "P1": "scratch script at backend root (delete / scripts/)",
    "P2": "controller file outside controllers/",
    "P3": "module at backend root (belongs in a layer package)",
    "P4": "missing expected backend package",
    "P5": "python package missing __init__.py",
    "H1": "sys.path.insert/append (import-resolution footgun)",
    "F1": "scratch/debug script (delete; ops scripts -> scripts/maintenance|validation)",
    "F2": "hardcoded developer-local absolute path in source",
    "F3": "dual/triple lockfiles (drift)",
    "F4": "committed cache/build/artifact present (bloat)",
    "F5": "secret material on disk (security)",
    "F6": "media written to / served from local disk (scale killer)",
    "F7": "raw os.environ secret read in middleware (use settings)",
    "F8": "documents/ root entry outside allow-list (only scope/ is authoritative)",
    "F9": "repo-root note outside allow-list / banned dir",
    "G0": "missing/weak root .gitignore (root cause of committed artifacts)",
    "DG": "forbidden dependency-graph edge (layer contract violated)",
    "DG2": "circular dependency detected",
    "DG3": "cross-domain import violates explicit bounded-context ownership",
    "DG4": "dynamic import edge detected",
    "DG5": "dynamic execution obscures dependency graph",
    "CFG1": "unknown layer referenced in policy",
    "CFG2": "unknown domain referenced in policy",
    "CFG3": "malformed or contradictory policy rule",
    "CFG4": "policy-level domain cycle",
    "MET1": "architecture debt score",
    "FE1": "missing expected frontend workspace/package file",
    "FE2": "frontend scratch/artifact script at package root",
    "FE3": "frontend flat folder scaling warning",
    "FE4": "frontend cross-workspace relative import",
    "FE5": "frontend folder too large (split by feature/domain)",
    "AUTO0": "auto-discovery baseline created",
    "AUTO3": "new backend domain detected",
    "AUTO6": "new cross-domain dependency learned",
    "AUTO8": "new top-level backend package detected",
    "AUTO10": "new feature detected",
    "NM": "node_modules present (confirm gitignored; #1 context-bloat source)",
    "I1": "structure summary",
    "I2": "rules source (yaml vs embedded fallback)",
    "I3": "architecture metric summary",
    "T1": "architecture trend delta",
}


@dataclass
class Finding:
    sev: str
    code: str
    domain: str
    path: str
    message: str
    intended: str = ""
    line: int | None = None

    def loc(self) -> str:
        return f"{self.path}:{self.line}" if self.line else self.path


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    def add(
        self,
        sev: str,
        code: str,
        domain: str,
        path: str,
        message: str,
        intended: str = "",
        line: int | None = None,
    ) -> None:
        self.findings.append(
            Finding(
                sev=sev,
                code=code,
                domain=domain,
                path=path,
                message=message,
                intended=intended,
                line=line,
            )
        )
        self.counters[code] += 1


@dataclass
class ModuleGraph:
    modules: dict[str, Path] = field(default_factory=dict)
    imports: dict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
    edges: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    edge_lines: dict[tuple[str, str], int] = field(default_factory=dict)
    fan_in: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    fan_out: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    classes: dict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
    packages: set[str] = field(default_factory=set)
    dynamic_imports: list[tuple[str, str, int]] = field(default_factory=list)
    dynamic_calls: list[tuple[str, str, int]] = field(default_factory=list)

    def finalize(self) -> None:
        self.fan_in = defaultdict(int)
        self.fan_out = defaultdict(int)

        for caller, targets in self.edges.items():
            self.fan_out[caller] = len(targets)
            for target in targets:
                self.fan_in[target] += 1

        self.packages = set()
        for module in self.modules:
            parts = module.split(".")
            if len(parts) >= 2:
                self.packages.add(".".join(parts[:2]))


@dataclass
class FeatureRegistry:
    domains: set[str] = field(default_factory=set)
    top_dirs: set[str] = field(default_factory=set)
    frontend_features: set[str] = field(default_factory=set)
    domain_edges: set[tuple[str, str]] = field(default_factory=set)
    features: dict[str, dict[str, set[str]]] = field(
        default_factory=lambda: defaultdict(lambda: defaultdict(set))
    )

    def to_json(self) -> dict:
        features = {}

        for name, layers in self.features.items():
            features[name] = {
                layer: sorted(values)
                for layer, values in layers.items()
            }

        return {
            "domains": sorted(self.domains),
            "backend_top_dirs": sorted(self.top_dirs),
            "frontend_features": sorted(self.frontend_features),
            "allowed_domain_edges": sorted([list(x) for x in self.domain_edges]),
            "features": features,
        }


# ============================================================================
# 3. RULE LOADING
# ============================================================================

def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p) for p in (patterns or [])]


def _merge_dict_of_lists(base: dict[str, list[str]], overlay: dict[str, Any] | None) -> dict[str, list[str]]:
    out = {k: list(v) for k, v in base.items()}
    for k, v in (overlay or {}).items():
        if v is None:
            continue
        out[k] = [str(x) for x in v]
    return out


def _read_cfg(path: Path) -> dict | None:
    if not path or not path.exists():
        return None

    try:
        txt = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    if path.suffix.lower() == ".json":
        try:
            data = json.loads(txt)
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    try:
        import yaml  # soft dependency
        data = yaml.safe_load(txt)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _apply_policy(eff: dict, data: dict | None) -> None:
    if not isinstance(data, dict):
        return

    pol = data.get("policy") if isinstance(data.get("policy"), dict) else data
    if not isinstance(pol, dict):
        return

    list_keys = {
        "scratch_phrases",
        "scratch_tokens",
        "scripts_safe_tokens",
        "dead_entrypoints",
        "secret_file_patterns",
    }

    set_lower_keys = {
        "ignore_dirs",
        "cache_dir_names",
        "text_ext",
        "source_ext",
        "surface_names",
        "write_verbs",
        "read_verbs",
        "lockfiles",
        "artifact_exts",
        "dup_ignore_basenames",
        "domain_layers",
        "ownership_layers",
        "graph_exempt_layers",
        "dead_exempt_layers",
        "dead_audit_layers",
        "no_init_dirs",
        "frontend_workspaces",
        "frontend_source_ext",
    }

    set_exact_keys = {
        "backend_root_allow",
        "allow_root_md",
        "allow_docs_root",
        "artifact_names",
        "known_writer_controllers",
        "dup_class_ignore",
        "expected_backend_packages",
        "frontend_root_allow",
    }

    scalar_keys = {
        "max_read_bytes",
        "flat_threshold",
        "large_subpackage_threshold",
        "god_fan_out",
        "god_fan_in",
        "max_cycles",
        "max_cycle_length",
        "frontend_flat_threshold",
        "frontend_large_folder_threshold",
        "forbidden_controller_to_controller",
        "detect_module_cycles",
        "detect_domain_cycles",
        "detect_dead_modules",
        "detect_metrics",
        "detect_duplicate_classes",
        "detect_dynamic_imports",
        "detect_policy_config",
        "detect_frontend",
        "detect_auto_discovery",
    }

    for key in list_keys:
        if key in pol and isinstance(pol[key], list):
            eff[key] = [str(x) for x in pol[key]]

    for key in set_lower_keys:
        if key in pol and isinstance(pol[key], list):
            eff[key] = {str(x).lower() for x in pol[key]}

    for key in set_exact_keys:
        if key in pol and isinstance(pol[key], list):
            eff[key] = {str(x) for x in pol[key]}

    for key in scalar_keys:
        if key not in pol:
            continue

        val = pol[key]

        if isinstance(val, bool):
            eff[key] = val
        elif isinstance(val, (int, float)):
            eff[key] = val
        elif isinstance(val, str):
            low = val.strip().lower()
            if low in {"1", "true", "yes", "on"}:
                eff[key] = True
            elif low in {"0", "false", "no", "off"}:
                eff[key] = False
            elif val.strip().isdigit():
                eff[key] = int(val.strip())
            else:
                eff[key] = val

    if isinstance(pol.get("canonical_home"), dict):
        for k, v in pol["canonical_home"].items():
            eff["canonical_home"][str(k)] = str(v)

    if isinstance(pol.get("env_secret_keys"), str):
        eff["env_secret_keys"] = pol["env_secret_keys"]

    if isinstance(pol.get("local_path"), str):
        eff["local_path"] = pol["local_path"]

    if isinstance(pol.get("media_disk_write"), str):
        eff["media_disk_write"] = pol["media_disk_write"]

    if isinstance(pol.get("media_disk_url"), str):
        eff["media_disk_url"] = pol["media_disk_url"]

    eff["scratch_phrases"] = [str(x).lower() for x in eff.get("scratch_phrases", [])]
    eff["scratch_tokens"] = {str(x).lower() for x in eff.get("scratch_tokens", set())}
    eff["scripts_safe_tokens"] = {str(x).lower() for x in eff.get("scripts_safe_tokens", set())}


def _apply_structure(eff: dict, struct: dict | None) -> None:
    if not isinstance(struct, dict):
        return

    eff["forbidden_root"] = _merge_dict_of_lists(eff["forbidden_root"], struct.get("forbidden_root"))
    eff["forbidden_any"] = _merge_dict_of_lists(eff["forbidden_any"], struct.get("forbidden_any"))

    if isinstance(struct.get("allow_root_md"), list):
        eff["allow_root_md"] = {str(x) for x in struct["allow_root_md"]}

    if isinstance(struct.get("allow_docs_root"), list):
        eff["allow_docs_root"] = {str(x) for x in struct["allow_docs_root"]}

    if isinstance(struct.get("scratch_phrases"), list):
        eff["scratch_phrases"] = [str(x).lower() for x in struct["scratch_phrases"]]

    if isinstance(struct.get("scratch_tokens"), list):
        eff["scratch_tokens"] = {str(x).lower() for x in struct["scratch_tokens"]}

    _apply_policy(eff, struct)


def _apply_layer(eff: dict, layer: dict | None) -> None:
    if not isinstance(layer, dict):
        return

    if isinstance(layer.get("forbidden_edges"), dict):
        eff["forbidden_edges"] = {
            str(k): [str(x) for x in v]
            for k, v in layer["forbidden_edges"].items()
            if isinstance(v, list)
        }

    if isinstance(layer.get("mis_housed_controllers"), list):
        eff["mis_housed_controllers"] = {str(x) for x in layer["mis_housed_controllers"]}

    if "forbidden_controller_to_controller" in layer:
        val = layer["forbidden_controller_to_controller"]
        if isinstance(val, str):
            eff["forbidden_controller_to_controller"] = val.strip().lower() in {"1", "true", "yes", "on"}
        else:
            eff["forbidden_controller_to_controller"] = bool(val)

    if isinstance(layer.get("domains"), dict):
        normalized: dict[str, dict[str, list[str]]] = {}
        for domain, cfg in layer["domains"].items():
            dom = str(domain).lower()
            if not isinstance(cfg, dict):
                normalized[dom] = {"may_import": []}
                continue

            may_import = cfg.get("may_import", [])
            normalized[dom] = {
                "may_import": [str(x).lower() for x in may_import] if isinstance(may_import, list) else []
            }

        eff["domains"] = normalized

    if isinstance(layer.get("ownership_layers"), list):
        eff["ownership_layers"] = {str(x).lower() for x in layer["ownership_layers"]}

    _apply_policy(eff, layer)


def load_rules(repo: Path, rules_dir: Path | None) -> dict:
    eff = {
        # structure
        "forbidden_root": _merge_dict_of_lists(DEFAULT_FORBIDDEN_ROOT, {}),
        "forbidden_any": _merge_dict_of_lists(DEFAULT_FORBIDDEN_ANY, {}),
        "allow_root_md": set(DEFAULT_ALLOW_ROOT_MD),
        "allow_docs_root": set(DEFAULT_ALLOW_DOCS_ROOT),

        # scratch
        "scratch_phrases": list(DEFAULT_SCRATCH_PHRASES),
        "scratch_tokens": set(DEFAULT_SCRATCH_TOKENS),
        "scripts_safe_tokens": set(DEFAULT_SCRIPTS_SAFE_TOKENS),

        # layers / dependencies
        "forbidden_edges": {k: list(v) for k, v in DEFAULT_FORBIDDEN_EDGES.items()},
        "mis_housed_controllers": set(DEFAULT_MIS_HOUSED_CONTROLLERS),
        "forbidden_controller_to_controller": True,
        "domains": {},
        "ownership_layers": set(DEFAULT_OWNERSHIP_LAYERS),
        "domain_layers": set(DEFAULT_DOMAIN_LAYERS),
        "graph_exempt_layers": set(DEFAULT_GRAPH_EXEMPT_LAYERS),
        "dead_exempt_layers": set(DEFAULT_DEAD_EXEMPT_LAYERS),
        "dead_audit_layers": set(DEFAULT_DEAD_AUDIT_LAYERS),
        "dead_entrypoints": list(DEFAULT_DEAD_ENTRYPOINTS),

        # policy / hygiene
        "ignore_dirs": set(DEFAULT_IGNORE_DIRS),
        "cache_dir_names": set(DEFAULT_CACHE_DIR_NAMES),
        "text_ext": set(DEFAULT_TEXT_EXT),
        "source_ext": set(DEFAULT_SOURCE_EXT),
        "max_read_bytes": DEFAULT_MAX_READ_BYTES,
        "backend_root_allow": set(DEFAULT_BACKEND_ROOT_ALLOW),
        "write_verbs": set(DEFAULT_WRITE_VERBS),
        "read_verbs": set(DEFAULT_READ_VERBS),
        "known_writer_controllers": set(DEFAULT_KNOWN_WRITER_CONTROLLERS),
        "secret_file_patterns": list(DEFAULT_SECRET_FILE_PATTERNS),
        "env_secret_keys": DEFAULT_ENV_SECRET_KEYS,
        "local_path": DEFAULT_LOCAL_PATH,
        "media_disk_write": DEFAULT_MEDIA_DISK_WRITE,
        "media_disk_url": DEFAULT_MEDIA_DISK_URL,
        "lockfiles": set(DEFAULT_LOCKFILES),
        "artifact_exts": set(DEFAULT_ARTIFACT_EXTS),
        "artifact_names": set(DEFAULT_ARTIFACT_NAMES),
        "dup_ignore_basenames": set(DEFAULT_DUP_IGNORE_BASENAMES),
        "canonical_home": dict(DEFAULT_CANONICAL_HOME),
        "surface_names": set(DEFAULT_SURFACE_NAMES),
        "expected_backend_packages": list(DEFAULT_EXPECTED_BACKEND_PACKAGES),
        "no_init_dirs": set(DEFAULT_NO_INIT_DIRS),
        "dup_class_ignore": set(DEFAULT_DUP_CLASS_IGNORE),

        # frontend
        "frontend_workspaces": set(DEFAULT_FRONTEND_WORKSPACES),
        "frontend_source_ext": set(DEFAULT_FRONTEND_SOURCE_EXT),
        "frontend_root_allow": set(DEFAULT_FRONTEND_ROOT_ALLOW),
        "frontend_flat_threshold": DEFAULT_FRONTEND_FLAT_THRESHOLD,
        "frontend_large_folder_threshold": DEFAULT_FRONTEND_LARGE_FOLDER_THRESHOLD,

        # scaling thresholds
        "flat_threshold": DEFAULT_FLAT_THRESHOLD,
        "large_subpackage_threshold": DEFAULT_LARGE_SUBPACKAGE_THRESHOLD,
        "god_fan_out": DEFAULT_GOD_FAN_OUT,
        "god_fan_in": DEFAULT_GOD_FAN_IN,
        "max_cycles": DEFAULT_MAX_CYCLES,
        "max_cycle_length": DEFAULT_MAX_CYCLE_LENGTH,

        # feature toggles
        "detect_module_cycles": True,
        "detect_domain_cycles": True,
        "detect_dead_modules": True,
        "detect_metrics": True,
        "detect_duplicate_classes": True,
        "detect_dynamic_imports": True,
        "detect_policy_config": True,
        "detect_frontend": True,
        "detect_auto_discovery": True,

        # meta
        "from_yaml": False,
        "known_layers": set(),
    }

    candidates: list[Path] = []
    if rules_dir:
        candidates.append(Path(rules_dir))
    candidates.append(repo / "documents" / "scope")
    candidates.append(repo / "governance")

    struct = None
    layer = None
    gov = None

    for d in candidates:
        if not d or not d.is_dir():
            continue

        if struct is None:
            struct = _read_cfg(d / "repo_structure.yaml") or _read_cfg(d / "repo_structure.json")

        if layer is None:
            layer = _read_cfg(d / "layer_rules.yaml") or _read_cfg(d / "layer_rules.json")

        if gov is None:
            gov = _read_cfg(d / "governance.yaml") or _read_cfg(d / "governance.json")

        if struct and layer and gov:
            break

    if struct:
        eff["from_yaml"] = True
        _apply_structure(eff, struct)

    if layer:
        eff["from_yaml"] = True
        _apply_layer(eff, layer)

    if gov:
        eff["from_yaml"] = True
        _apply_policy(eff, gov)

    eff["text_ext"] = {str(x).lower() for x in eff["text_ext"]}
    eff["source_ext"] = {str(x).lower() for x in eff["source_ext"]}
    eff["frontend_source_ext"] = {str(x).lower() for x in eff["frontend_source_ext"]}
    eff["ignore_dirs"] = {str(x).lower() for x in eff["ignore_dirs"]}
    eff["cache_dir_names"] = {str(x).lower() for x in eff["cache_dir_names"]}

    eff["scratch_phrases"] = [str(x).lower() for x in eff.get("scratch_phrases", [])]
    eff["scratch_tokens"] = {str(x).lower() for x in eff.get("scratch_tokens", set())}
    eff["scripts_safe_tokens"] = {str(x).lower() for x in eff.get("scripts_safe_tokens", set())}

    known_layers = {str(x).lower() for x in eff["expected_backend_packages"]}
    backend = repo / "backend"
    if backend.exists():
        try:
            for p in backend.iterdir():
                if p.is_dir() and p.name.lower() not in eff["ignore_dirs"]:
                    known_layers.add(p.name.lower())
        except OSError:
            pass

    eff["known_layers"] = known_layers

    eff["forbidden_root_c"] = {k: _compile(v) for k, v in eff["forbidden_root"].items()}
    eff["forbidden_any_c"] = {k: _compile(v) for k, v in eff["forbidden_any"].items()}
    eff["secret_file_patterns_c"] = [re.compile(p, re.I) for p in eff["secret_file_patterns"]]
    eff["env_secret_keys_c"] = re.compile(eff["env_secret_keys"], re.I)
    eff["local_path_c"] = re.compile(eff["local_path"])
    eff["media_disk_write_c"] = re.compile(eff["media_disk_write"])
    eff["media_disk_url_c"] = re.compile(eff["media_disk_url"])
    eff["dead_entrypoints_c"] = [re.compile(p) for p in eff["dead_entrypoints"]]

    return eff


# ============================================================================
# 4. GENERIC HELPERS
# ============================================================================

def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
    except ValueError:
        return str(p)


def walk_dirs(root: Path, ignore_dirs: set[str]):
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(d.iterdir())
        except (PermissionError, OSError):
            continue

        yield d, entries

        for e in entries:
            if e.is_dir() and e.name.lower() not in ignore_dirs:
                stack.append(e)


def iter_text_files(root: Path, eff: dict) -> Iterable[Path]:
    for d, entries in walk_dirs(root, eff["ignore_dirs"]):
        for e in entries:
            if e.is_file() and e.suffix.lower() in eff["text_ext"]:
                try:
                    if e.stat().st_size <= eff["max_read_bytes"]:
                        yield e
                except OSError:
                    pass


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


def in_parts(path: Path, *names: str) -> bool:
    parts = {x.lower() for x in path.parts}
    return any(n.lower() in parts for n in names)


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def domain_of(path_rel: str) -> str:
    parts = [p.lower() for p in Path(path_rel).parts]
    base = parts[-1] if parts else ""

    if "alembic" in parts or "db" in parts or "models" in parts:
        return "database"

    if "middleware" in parts or "dependencies" in parts or base == "security_config.ini":
        return "security"

    if parts and parts[0] == "frontend":
        return "frontend"

    if parts and parts[0] == "documents":
        return "docs"

    if parts and parts[0] in {"monitoring", "nginx", "infra"}:
        return "infra"

    if parts and parts[0] == "backend":
        return "backend"

    return "repo"


def is_scratch_name(stem: str, eff: dict, broad: bool) -> bool:
    low = stem.lower()

    for ph in eff.get("scratch_phrases", []):
        ph = str(ph).lower()
        if ph and ph in low:
            return True

    tokens = {t.lower() for t in re.split(r"[-_.]+", low) if t}

    if broad:
        token_set = {str(t).lower() for t in eff.get("scratch_tokens", set())}
    else:
        token_set = {str(t).lower() for t in eff.get("scripts_safe_tokens", set())}

    return bool(tokens & token_set)


def layer_of(path_rel: str) -> str:
    parts = [p.lower() for p in Path(path_rel).parts]
    if not parts or parts[0] != "backend":
        return ""
    if len(parts) < 2:
        return ""
    return parts[1]


def layer_of_module(module: str) -> str:
    if not module:
        return ""
    return module.split(".", 1)[0]


def module_path_rel(module: str, graph: ModuleGraph, repo: Path) -> str:
    p = graph.modules.get(module)
    return rel(p, repo) if p else module


def backend_module_name(pyfile: Path, backend_dir: Path) -> str | None:
    try:
        rel_path = pyfile.relative_to(backend_dir).with_suffix("")
    except ValueError:
        return None

    parts = list(rel_path.parts)
    if not parts:
        return None

    if parts[-1] == "__init__":
        parts = parts[:-1]

    if not parts:
        return None

    return ".".join(parts)


def normalize_import(raw: str | None, known_top: set[str]) -> str | None:
    if not raw:
        return None

    raw = raw.strip().strip(".")
    if not raw:
        return None

    if raw.startswith("backend."):
        raw = raw[len("backend."):]

    first = raw.split(".", 1)[0]
    if first in known_top:
        return raw

    return None


def resolve_relative_import(level: int, module: str | None, pkg: list[str]) -> str | None:
    if level == 0:
        return module

    if level - 1 > len(pkg):
        return None

    base = pkg[: len(pkg) - (level - 1)]
    parts = base + ([module] if module else [])
    return ".".join(parts) if parts else None


def resolve_target_module(mod: str, modules: dict[str, Path]) -> str | None:
    parts = mod.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in modules:
            return cand
    return None


def domain_of_module(module: str, eff: dict, graph: ModuleGraph | None = None) -> str | None:
    parts = module.split(".")
    if not parts:
        return None

    layer = parts[0]
    if layer not in eff["ownership_layers"]:
        return None

    if len(parts) >= 3:
        return parts[1].lower()

    if len(parts) == 2:
        if graph and module in graph.packages:
            return parts[1].lower()

    return None


def normalize_cycle(cycle: list[str]) -> list[str]:
    if not cycle:
        return []

    core = list(cycle)
    if len(core) > 1 and core[0] == core[-1]:
        core = core[:-1]

    if not core:
        return []

    min_i = min(range(len(core)), key=lambda i: core[i])
    return core[min_i:] + core[:min_i]


# ============================================================================
# 5. FEATURE AUTO-DISCOVERY HELPERS
# ============================================================================

def normalize_feature_name(name: str) -> str:
    if not name:
        return ""

    low = str(name).lower()
    low = low.replace("\\", "/")
    low = re.sub(r"[\s\-.]+", "_", low)
    low = re.sub(r"_+", "_", low).strip("_")

    if not low:
        return ""

    for _ in range(3):
        changed = False
        for suffix in FEATURE_SUFFIXES:
            if low.endswith(suffix) and len(low) > len(suffix) + 1:
                low = low[: -len(suffix)].rstrip("_")
                changed = True

        if not changed:
            break

    low = re.sub(r"_+", "_", low).strip("_")

    if low in FEATURE_STOP_NAMES:
        return ""

    if len(low) <= 2:
        return ""

    return low


def discover_features(repo: Path, eff: dict, graph: ModuleGraph) -> FeatureRegistry:
    reg = FeatureRegistry()

    backend = repo / "backend"
    frontend = repo / "frontend"

    # Backend top-level packages.
    if backend.exists():
        try:
            for p in backend.iterdir():
                if p.is_dir() and p.name.lower() not in eff["ignore_dirs"]:
                    reg.top_dirs.add(p.name.lower())
        except OSError:
            pass

    # Backend domains/features from files.
    if backend.exists():
        domain_discovery_layers = {"services", "models", "providers", "events", "jobs"}

        for f in iter_text_files(backend, eff):
            if f.suffix.lower() != ".py":
                continue

            try:
                parts = [p.lower() for p in f.relative_to(backend).parts]
            except ValueError:
                continue

            if len(parts) < 2:
                continue

            layer = parts[0]
            stem = f.stem.lower()

            # Domain discovery from sub-packages.
            if layer in domain_discovery_layers and len(parts) >= 3:
                candidate_domain = parts[1]
                if candidate_domain not in eff["surface_names"]:
                    reg.domains.add(candidate_domain)

            if stem == "__init__":
                continue

            feature = ""
            surface = ""

            if layer in {"routers", "controllers"}:
                if len(parts) >= 3:
                    sub = parts[1]
                    if sub in eff["surface_names"]:
                        surface = sub

                feature = normalize_feature_name(stem)

                for s in eff["surface_names"]:
                    prefix = f"{s}_"
                    if feature.startswith(prefix):
                        surface = s
                        feature = feature[len(prefix):]
                        break

            elif layer in domain_discovery_layers:
                feature = normalize_feature_name(stem)

            else:
                feature = normalize_feature_name(stem)

            if feature:
                reg.features[feature]["backend"].add(layer)
                reg.features[feature]["paths"].add(rel(f, repo))

                if surface:
                    reg.features[feature]["surfaces"].add(surface)

    # Domain edges from module graph.
    for caller, targets in graph.edges.items():
        cd = domain_of_module(caller, eff, graph)
        if not cd:
            continue

        for target in targets:
            td = domain_of_module(target, eff, graph)
            if td and td != cd:
                reg.domain_edges.add((cd, td))

    # Frontend feature discovery.
    if frontend.exists():
        workspaces = sorted(eff.get("frontend_workspaces", set()))

        for ws in workspaces:
            wsdir = frontend / ws
            if not wsdir.exists():
                continue

            bases = []

            if ws == "shared":
                bases.extend(
                    [
                        wsdir / "src" / "features",
                        wsdir / "src" / "components",
                        wsdir / "src" / "logo",
                    ]
                )
            else:
                bases.extend(
                    [
                        wsdir / "src" / "features",
                        wsdir / "features",
                        wsdir / "src" / "components",
                        wsdir / "components",
                    ]
                )

            for base in bases:
                if not base.exists():
                    continue

                try:
                    entries = list(base.iterdir())
                except OSError:
                    entries = []

                for e in entries:
                    if not e.is_dir():
                        continue

                    if e.name.lower() in eff["ignore_dirs"]:
                        continue

                    name = normalize_feature_name(e.name)
                    if not name:
                        continue

                    reg.frontend_features.add(name)
                    reg.features[name]["frontend"].add(rel(e, repo))

    return reg


# ============================================================================
# 6. MODULE GRAPH BUILDER
# ============================================================================

def build_module_graph(repo: Path, eff: dict) -> ModuleGraph:
    graph = ModuleGraph()
    backend = repo / "backend"

    if not backend.exists():
        return graph

    known_top = {str(x).lower() for x in eff["expected_backend_packages"]}

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        module = backend_module_name(f, backend)
        if not module:
            continue

        graph.modules[module] = f
        known_top.add(module.split(".", 1)[0])

    for module, f in graph.modules.items():
        tree = parse_safe(f)
        if tree is None:
            continue

        try:
            pkg = list(f.relative_to(backend).parent.parts)
        except ValueError:
            pkg = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not node.name.startswith("_"):
                    graph.classes[node.name].append((module, node.lineno))

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    raw = alias.name
                    norm = normalize_import(raw, known_top)
                    if not norm:
                        continue

                    graph.imports[module].append((norm, node.lineno))
                    target = resolve_target_module(norm, graph.modules)
                    if target and target != module:
                        if target not in graph.edges[module]:
                            graph.edge_lines[(module, target)] = node.lineno
                        graph.edges[module].add(target)

            elif isinstance(node, ast.ImportFrom):
                raw = resolve_relative_import(node.level, node.module, pkg)
                norm = normalize_import(raw, known_top)
                if not norm:
                    continue

                graph.imports[module].append((norm, node.lineno))
                target = resolve_target_module(norm, graph.modules)
                if target and target != module:
                    if target not in graph.edges[module]:
                        graph.edge_lines[(module, target)] = node.lineno
                    graph.edges[module].add(target)

            if isinstance(node, ast.Call):
                fname = None
                if isinstance(node.func, ast.Name):
                    fname = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    fname = node.func.attr

                if fname in {"import_module", "__import__"}:
                    raw = None

                    if (
                        node.args
                        and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                    ):
                        raw = node.args[0].value

                    if raw:
                        norm = normalize_import(raw, known_top)
                        if norm:
                            graph.imports[module].append((norm, node.lineno))
                            graph.dynamic_imports.append((module, norm, node.lineno))

                            target = resolve_target_module(norm, graph.modules)
                            if target and target != module:
                                if target not in graph.edges[module]:
                                    graph.edge_lines[(module, target)] = node.lineno
                                graph.edges[module].add(target)
                        else:
                            graph.dynamic_calls.append((module, f"{fname}:{raw}", node.lineno))
                    else:
                        graph.dynamic_calls.append((module, fname or "dynamic_import", node.lineno))

                elif fname in {"eval", "exec"}:
                    graph.dynamic_calls.append((module, fname, node.lineno))

    graph.finalize()
    return graph


# ============================================================================
# 7. STRUCTURE / HYGIENE CHECKS
# ============================================================================

def check_gitignore(repo: Path, rep: Report, eff: dict) -> None:
    gi = repo / ".gitignore"

    if not gi.exists():
        rep.add(
            RED,
            "G0",
            "repo",
            ".gitignore",
            "no root .gitignore -> artifacts/caches/secrets get committed",
            intended="add strict root .gitignore (logs, *.db*, caches, node_modules, .env, backups)",
        )
        return

    t = read_text(gi) or ""
    missing = [m for m in ["*.db", "node_modules", "__pycache__", ".env", "*.log"] if m not in t]

    if missing:
        rep.add(
            YEL,
            "G0",
            "repo",
            ".gitignore",
            f".gitignore missing key patterns: {', '.join(missing)}",
            intended="add the missing patterns so artifacts stop being committed",
        )


def check_lockfiles(repo: Path, rep: Report, eff: dict) -> None:
    for top in (".", "frontend", "frontend/web_app", "frontend/mobile_app", "frontend/shared"):
        d = repo if top == "." else repo / top
        if not d.exists():
            continue

        present = [lf for lf in eff["lockfiles"] if (d / lf).exists()]
        if len(present) >= 2:
            rep.add(
                YEL,
                "F3",
                "repo" if top == "." else "frontend",
                rel(d, repo),
                f"multiple lockfiles ({', '.join(sorted(present))}) -> install drift",
                intended="keep ONE package manager / one lockfile per workspace",
            )


def check_cache_dirs(repo: Path, rep: Report, eff: dict) -> None:
    seen: set[str] = set()

    for d, entries in walk_dirs(repo, eff["ignore_dirs"]):
        for e in entries:
            if e.is_dir() and e.name.lower() in eff["cache_dir_names"] and e.name not in seen:
                seen.add(e.name)
                rep.add(
                    YEL,
                    "F4",
                    domain_of(rel(e, repo)),
                    rel(e, repo),
                    f"cache/build dir '{e.name}' present in tree (bloats repo & context)",
                    intended="delete + ensure in .gitignore",
                )


def check_node_modules(repo: Path, rep: Report, eff: dict) -> None:
    for d, entries in walk_dirs(repo, eff["ignore_dirs"]):
        for e in entries:
            if e.is_dir() and e.name == "node_modules":
                rep.add(
                    GRN,
                    "NM",
                    domain_of(rel(e, repo)),
                    rel(e, repo),
                    "node_modules present (local-only is fine)",
                    intended="CONFIRM gitignored; a COMMITTED node_modules is the #1 bloat source",
                )


def check_hardcoded_local_paths(repo: Path, rep: Report, eff: dict) -> None:
    for top in ("backend", "frontend"):
        d = repo / top
        if not d.exists():
            continue

        for f in iter_text_files(d, eff):
            if f.suffix.lower() not in eff["source_ext"]:
                continue

            t = read_text(f)
            if not t:
                continue

            for i, line in enumerate(t.splitlines(), 1):
                if eff["local_path_c"].search(line):
                    rep.add(
                        YEL,
                        "F2",
                        domain_of(rel(f, repo)),
                        rel(f, repo),
                        "hardcoded developer-local absolute path (portability + leak)",
                        intended="use repo-relative paths / config; never commit C:/d:/F:/home paths",
                        line=i,
                    )
                    break


def check_ghost_backend(repo: Path, rep: Report) -> None:
    for cand in ("scripts/backend", "Working_API"):
        c = repo / cand
        if (c / "main.py").exists() or (c / "db" / "database.py").exists():
            rep.add(
                RED,
                "X1",
                "repo",
                cand,
                "ghost backend (own main.py / db/database.py) -> two main.py & two database.py",
                intended="delete, or scripts/templates/ renamed so it can't import",
            )


def check_duplicate_basenames(repo: Path, rep: Report, eff: dict) -> None:
    ignore = {str(x).lower() for x in eff["dup_ignore_basenames"]}

    by: dict[str, list[str]] = defaultdict(list)
    backend = repo / "backend"

    if backend.exists():
        for f in iter_text_files(backend, eff):
            if f.suffix.lower() != ".py" or f.stem.lower() in ignore:
                continue
            by[f.name].append(rel(f, repo))

    for name, paths in by.items():
        dirs = {Path(p).parent for p in paths}
        if len(dirs) > 1:
            home = eff["canonical_home"].get(name, "one canonical package")
            rep.add(
                YEL,
                "D1",
                "backend",
                name,
                f"same module name in {len(dirs)} dirs (import-shadow): " + ", ".join(paths[:5]),
                intended=f"keep the canonical copy ({home}); delete the shadows",
            )

    cross: dict[str, list[str]] = defaultdict(list)
    for top in ("backend", "monitoring", "scripts"):
        d = repo / top
        if not d.exists():
            continue

        for f in iter_text_files(d, eff):
            if f.suffix.lower() != ".py" or f.stem.lower() in ignore:
                continue
            cross[f.name].append(rel(f, repo))

    for name, paths in cross.items():
        tops = {Path(p).parts[0] for p in paths if Path(p).parts}
        if len(tops) > 1:
            rep.add(
                YEL,
                "D2",
                "repo",
                name,
                f"same module name across {sorted(tops)} (duplicated detector / ghost backend): "
                + ", ".join(paths[:5]),
                intended="keep ONE owner; the other is drift",
            )


def check_secrets_on_disk(repo: Path, rep: Report, eff: dict) -> None:
    for d, entries in walk_dirs(repo, eff["ignore_dirs"]):
        for e in entries:
            if not e.is_file():
                continue

            rp = rel(e, repo).replace("\\", "/")
            for rx in eff["secret_file_patterns_c"]:
                if rx.search("/" + rp) or rx.search(rp):
                    rep.add(
                        RED,
                        "F5",
                        "security",
                        rel(e, repo),
                        "secret/credential material on disk",
                        intended="remove from VCS; load via env/Vault; keep only .env.example",
                    )
                    break


def _code_for_root(key: str, c: Path) -> str:
    if key == "." and (
        c.name.startswith("backup_")
        or c.name in {"Working_API", "provider_test", "_trash", "image", "zozi-logo-app"}
        or c.suffix == ".zip"
    ):
        return "F9"

    if c.name in DEFAULT_ARTIFACT_NAMES or c.suffix in DEFAULT_ARTIFACT_EXTS or c.suffix in {".db"}:
        return "F4"

    if key == "backend/alembic":
        return "A1"

    return "F4"


def _intended_for(key: str, c: Path) -> str:
    if c.name.startswith("backup_") or c.suffix == ".zip":
        return "remove from VCS (backups -> object storage; design -> design/)"

    if c.name in {"Working_API", "provider_test"}:
        return "move to experiments/ and gitignore outputs (remove Working_API fallback first)"

    if c.name == "_trash":
        return "delete from repo"

    if c.name in DEFAULT_ARTIFACT_NAMES or c.suffix in DEFAULT_ARTIFACT_EXTS or c.suffix in {
        ".db",
        ".db-shm",
        ".db-wal",
    }:
        return "delete + add to .gitignore"

    return "relocate per scope/repo_structure.yaml or delete"


def _code_for_any(f: Path) -> str:
    if "migrations" in f.parts and "alembic" not in f.parts:
        return "G1"

    if f.name == "employee_models.py":
        return "M1"

    if "stub" in f.name:
        return "A1"

    return "G1"


def _intended_for_any(f: Path) -> str:
    if "migrations" in f.parts and "alembic" not in f.parts:
        return "fold into an Alembic revision or delete (no second migrations home)"

    if f.name == "employee_models.py":
        return "move into backend/models/ and add __table_args__ schema"

    return "relocate per scope/repo_structure.yaml"


def check_intended_violations(repo: Path, rep: Report, eff: dict) -> None:
    for key, frx in eff["forbidden_root_c"].items():
        base = repo if key == "." else repo / key
        if not base.exists() or not frx:
            continue

        dom = "repo" if key == "." else domain_of(key)

        try:
            children = list(base.iterdir())
        except OSError:
            children = []

        for c in children:
            for rx in frx:
                if rx.search(c.name):
                    sev = RED if c.suffix in {".db"} else YEL
                    rep.add(
                        sev,
                        _code_for_root(key, c),
                        dom,
                        rel(c, repo),
                        f"must not sit at {key or 'repo root'} (damages structure/scale)",
                        intended=_intended_for(key, c),
                    )
                    break

    for key, fax in eff["forbidden_any_c"].items():
        base = repo if key == "." else repo / key
        if not base.exists() or not fax:
            continue

        for f in iter_text_files(base, eff):
            rp = rel(f, repo).replace("\\", "/")
            for rx in fax:
                if rx.search("/" + rp) or rx.search(rp):
                    rep.add(
                        YEL,
                        _code_for_any(f),
                        domain_of(rp),
                        rel(f, repo),
                        f"forbidden under {key}",
                        intended=_intended_for_any(f),
                    )
                    break


def check_backend_root_modules(repo: Path, rep: Report, eff: dict) -> None:
    be = repo / "backend"
    if not be.exists():
        return

    for c in sorted(be.iterdir()):
        if not c.is_file() or c.suffix != ".py":
            continue

        if c.name in eff["backend_root_allow"]:
            continue

        rp = rel(c, repo)

        if is_scratch_name(c.stem, eff, broad=True):
            rep.add(
                YEL,
                "P1",
                "backend",
                rp,
                "scratch/one-off script at backend root",
                intended="delete, or move to scripts/ (ops) / tests/",
            )
        else:
            home = eff["canonical_home"].get(
                c.name,
                "a layer package (routers/controllers/services/utils/db)",
            )
            rep.add(
                YEL,
                "P3",
                "backend",
                rp,
                "module at backend root (shadows the canonical home or is mis-placed)",
                intended=f"move to {home}; backend/ root holds only main/lifespan/run_server",
            )


def check_scratch_scripts(repo: Path, rep: Report, eff: dict) -> None:
    roots = [repo / "frontend", repo / "scripts", repo]
    seen: set[str] = set()

    for r in roots:
        if not r.exists():
            continue

        for f in iter_text_files(r, eff):
            if f.suffix.lower() not in {".js", ".cjs", ".mjs"}:
                continue

            rp = rel(f, repo)
            if rp in seen:
                continue

            if is_scratch_name(f.stem, eff, broad=False):
                seen.add(rp)
                rep.add(
                    YEL,
                    "F1",
                    domain_of(rp),
                    rp,
                    "scratch/debug script (one-off; not an ops/maintenance script)",
                    intended="delete; ops scripts live in scripts/maintenance or scripts/validation",
                )


def check_doc_and_root_allowlists(repo: Path, rep: Report, eff: dict) -> None:
    docs = repo / "documents"

    if docs.exists():
        allow = eff["allow_docs_root"]
        for c in sorted(docs.iterdir()):
            if c.name in allow:
                continue

            kind = "dir" if c.is_dir() else "file"
            rep.add(
                YEL,
                "F8",
                "docs",
                rel(c, repo),
                f"{kind} at documents/ root outside the allow-list",
                intended="documents/scope/ is authoritative; move this to documents/archive/ (or delete)",
            )

    allow_md = eff["allow_root_md"]

    for c in sorted(repo.iterdir()):
        if not c.is_file():
            continue

        if c.suffix == ".txt":
            rep.add(
                YEL,
                "F9",
                "repo",
                rel(c, repo),
                "design/plan note (.txt) at repo root",
                intended="move to documents/ (spec) or experiments/ (scratch); never commit at root",
            )

        elif c.suffix == ".md" and c.name not in allow_md:
            rep.add(
                YEL,
                "F9",
                "repo",
                rel(c, repo),
                "doc at repo root outside the allow-list",
                intended="move to documents/scope/ (authoritative) or documents/archive/",
            )


def check_expected_packages(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    no_init = {str(x).lower() for x in eff["no_init_dirs"]}

    for pkg in eff["expected_backend_packages"]:
        d = backend / pkg
        if not d.exists():
            rep.add(
                YEL,
                "P4",
                "backend",
                rel(d, repo),
                f"expected backend package '{pkg}' is missing",
                intended="create the package if this layer is part of the target architecture",
            )
            continue

        if pkg.lower() not in no_init and not (d / "__init__.py").exists():
            rep.add(
                YEL,
                "P5",
                "backend",
                rel(d, repo),
                f"expected package '{pkg}' has no __init__.py",
                intended="add __init__.py so imports/package boundaries are explicit",
            )


def check_package_init_shape(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    no_init = {str(x).lower() for x in eff["no_init_dirs"]}
    reported = 0

    for d, entries in walk_dirs(backend, eff["ignore_dirs"]):
        if d == backend:
            continue

        try:
            parts = [p.lower() for p in d.relative_to(backend).parts]
        except ValueError:
            continue

        if any(p in no_init for p in parts):
            continue

        has_py = any(e.is_file() and e.suffix.lower() == ".py" for e in entries)
        if has_py and not (d / "__init__.py").exists():
            rep.add(
                YEL,
                "P5",
                "backend",
                rel(d, repo),
                "folder contains Python files but no __init__.py",
                intended="make it an explicit package or move the script to scripts/tests",
            )
            reported += 1

        if reported >= 200:
            break


def check_subfolder_axis_and_shape(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    def count_py_dir(d: Path) -> int:
        return sum(1 for f in iter_text_files(d, eff) if f.suffix.lower() == ".py")

    for layer_name, flat_code, surface_code, large_code in [
        ("services", "S1", "S4", "S5"),
        ("models", "M2", "M3", "M4"),
    ]:
        d = backend / layer_name
        if not d.exists():
            continue

        direct = [p for p in d.glob("*.py") if p.name != "__init__.py"]
        if len(direct) > eff["flat_threshold"]:
            rep.add(
                YEL,
                flat_code,
                "backend",
                rel(d, repo),
                f"{layer_name}/ FLAT ({len(direct)} files, too many at layer root)",
                intended=f"{layer_name}/<domain>/ per bounded contexts (finance/orders/catalog/...)",
            )

        try:
            subdirs = [
                p
                for p in d.iterdir()
                if p.is_dir() and p.name.lower() not in eff["ignore_dirs"]
            ]
        except OSError:
            subdirs = []

        for sd in subdirs:
            if sd.name.lower() in eff["surface_names"]:
                rep.add(
                    YEL,
                    surface_code,
                    "backend",
                    rel(sd, repo),
                    f"surface sub-folder '{sd.name}' inside domain layer {layer_name}/",
                    intended=f"{layer_name}/ must be grouped by DOMAIN, not by surface (admin/supplier/...)",
                )

            py_count = count_py_dir(sd)
            if py_count > eff["large_subpackage_threshold"]:
                rep.add(
                    YEL,
                    large_code,
                    "backend",
                    rel(sd, repo),
                    f"domain sub-package '{sd.name}' is very large ({py_count} .py files)",
                    intended="split this bounded context into sub-domains or feature packages",
                )

        if layer_name == "services":
            stems = sorted({p.stem for p in direct})
            used: set[str] = set()

            for i, a in enumerate(stems):
                if a in used:
                    continue

                grp = [a]
                for b in stems[i + 1:]:
                    if b in used:
                        continue

                    n = 0
                    while n < len(a) and n < len(b) and a[n] == b[n]:
                        n += 1

                    if n >= 6:
                        grp.append(b)

                if len(grp) >= 2:
                    used.update(grp)
                    rep.add(
                        YEL,
                        "S2",
                        "backend",
                        rel(d, repo),
                        f"overlapping service stems '{a[:6].rstrip('_')}*' ({len(grp)}) -> ambiguous ownership",
                        intended="merge or document each role in an ADR: " + ", ".join(grp[:6]),
                    )

    for layer_name in ("routers", "controllers"):
        d = backend / layer_name
        if not d.exists():
            continue

        direct = [p for p in d.glob("*.py") if p.name != "__init__.py"]
        if len(direct) > eff["flat_threshold"]:
            rep.add(
                YEL,
                "S3",
                "backend",
                rel(d, repo),
                f"{layer_name}/ FLAT ({len(direct)} files at layer root)",
                intended=f"group {layer_name}/ by surface (admin/supplier/customer/public/webhooks)",
            )


def check_rls_cluster(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    hits = [
        rel(f, repo)
        for f in iter_text_files(backend, eff)
        if f.suffix.lower() == ".py" and (f.stem.startswith("rls_") or f.stem == "country_rls")
    ]

    if len(hits) >= 2:
        rep.add(
            YEL,
            "L1",
            "security",
            "middleware/ + dependencies/",
            f"{len(hits)} RLS modules -> two enforcers = fail-open risk",
            intended="pick ONE canonical enforcer (ADR); alias/delete rest: " + ", ".join(hits),
        )


def check_raw_env_in_middleware(repo: Path, rep: Report, eff: dict) -> None:
    mw = repo / "backend" / "middleware"
    if not mw.exists():
        return

    for f in iter_text_files(mw, eff):
        if f.suffix.lower() != ".py":
            continue

        t = read_text(f)
        if not t:
            continue

        for i, line in enumerate(t.splitlines(), 1):
            if eff["env_secret_keys_c"].search(line):
                rep.add(
                    YEL,
                    "F7",
                    "security",
                    rel(f, repo),
                    "raw os.environ secret read in middleware",
                    intended="read via utils/config settings (single source of truth)",
                    line=i,
                )
                break


def check_media_on_disk(repo: Path, rep: Report, eff: dict) -> None:
    for layer_name in ("controllers", "services", "routers"):
        d = repo / "backend" / layer_name
        if not d.exists():
            continue

        for f in iter_text_files(d, eff):
            if f.suffix.lower() != ".py":
                continue

            t = read_text(f)
            if not t:
                continue

            for i, line in enumerate(t.splitlines(), 1):
                if eff["media_disk_write_c"].search(line) or eff["media_disk_url_c"].search(line):
                    rep.add(
                        YEL,
                        "F6",
                        "backend",
                        rel(f, repo),
                        "media written to / referenced from local disk",
                        intended="storage abstraction -> object storage + CDN; DB stores metadata only",
                        line=i,
                    )
                    break


# ============================================================================
# 8. LAYER / DEPENDENCY CHECKS
# ============================================================================

def check_layer_writes(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"

    for layer_name in ("controllers", "routers"):
        d = backend / layer_name
        if not d.exists():
            continue

        for f in iter_text_files(d, eff):
            if f.suffix.lower() != ".py" or in_parts(f, "tests"):
                continue

            tree = parse_safe(f)
            if tree is None:
                continue

            r = rel(f, repo)
            known = f.name in eff["known_writer_controllers"]

            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                    continue

                v = node.func.attr

                if v in eff["write_verbs"]:
                    if known:
                        rep.add(
                            YEL,
                            "W2",
                            "backend",
                            r,
                            f"misnamed service-helper writes here (.{v}()); relocate file to services/",
                            intended="services/<domain>/",
                            line=node.lineno,
                        )
                    else:
                        rep.add(
                            RED,
                            "W1",
                            "backend",
                            r,
                            f"{layer_name}/ must not call session write .{v}(); move write into a service",
                            intended="a services/<domain>/*_service.py method",
                            line=node.lineno,
                        )

                elif v in eff["read_verbs"]:
                    rep.add(
                        YEL,
                        "Q1",
                        "backend",
                        r,
                        f"{layer_name}/ reads via .{v}(); delegate to a service",
                        intended="service layer",
                        line=node.lineno,
                    )


def check_router_outside(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    allowed_top_for_router_check = {
        "controllers",
        "services",
        "middleware",
        "dependencies",
        "providers",
        "utils",
        "events",
        "jobs",
        "tasks",
        "api",
    }

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        try:
            parts = [p.lower() for p in f.relative_to(backend).parts]
        except ValueError:
            continue

        if not parts:
            continue

        if parts[0] not in allowed_top_for_router_check:
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                nm = fn.id if isinstance(fn, ast.Name) else (fn.attr if isinstance(fn, ast.Attribute) else None)

                if nm == "APIRouter":
                    rep.add(
                        RED,
                        "R1",
                        "backend",
                        rel(f, repo),
                        "APIRouter outside routers/ -> endpoint mis-registered/shadowed",
                        intended="backend/routers/",
                        line=node.lineno,
                    )
                    break


def check_dependency_graph(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    edges = eff["forbidden_edges"]
    mis = eff["mis_housed_controllers"]
    forbid_cc = eff["forbidden_controller_to_controller"]

    for caller in sorted(graph.imports.keys()):
        caller_layer = layer_of_module(caller)
        if caller_layer in eff["graph_exempt_layers"]:
            continue

        reported: set[tuple[str, str]] = set()
        caller_path = module_path_rel(caller, graph, repo)

        for mod, line in graph.imports[caller]:
            if not mod:
                continue

            leaf = mod.rsplit(".", 1)[-1]

            if leaf in mis and (mod == "controllers" or mod.startswith("controllers.")):
                key = ("W3", mod)
                if key not in reported:
                    reported.add(key)
                    rep.add(
                        RED,
                        "W3",
                        "backend",
                        caller_path,
                        f"imports mis-housed controller '{mod}' (it holds service/util logic)",
                        intended="import from its services/<domain>/ (or utils/) home once relocated",
                        line=line,
                    )
                continue

            if (
                forbid_cc
                and caller_layer == "controllers"
                and mod.startswith("controllers.")
                and mod != "controllers"
            ):
                key = ("W4", mod)
                if key not in reported:
                    reported.add(key)
                    rep.add(
                        YEL,
                        "W4",
                        "backend",
                        caller_path,
                        f"controller imports another controller ('{mod}')",
                        intended="extract shared logic into a service or util; controllers stay thin",
                        line=line,
                    )
                continue

            for pref in edges.get(caller_layer, []):
                if mod == pref or mod.startswith(pref + "."):
                    key = ("DG", mod)
                    if key not in reported:
                        reported.add(key)
                        rep.add(
                            RED,
                            "DG",
                            "backend",
                            caller_path,
                            f"forbidden dependency edge: {caller_layer} -> {mod}",
                            intended=f"layer contract: {caller_layer} may not depend on {pref}; route via services/",
                            line=line,
                        )
                    break

            if eff.get("domains"):
                target_layer = layer_of_module(mod)
                if target_layer in eff["ownership_layers"]:
                    sd = domain_of_module(caller, eff, graph)
                    td = domain_of_module(mod, eff, graph)

                    if sd and td and sd != td and sd in eff["domains"]:
                        allowed = eff["domains"][sd].get("may_import", [])
                        if td not in allowed:
                            key = ("DG3", mod)
                            if key not in reported:
                                reported.add(key)
                                rep.add(
                                    RED,
                                    "DG3",
                                    "backend",
                                    caller_path,
                                    f"cross-domain import {sd} -> {td} violates explicit ownership rules",
                                    intended=f"declare allowed imports in layer_rules.yaml or route via {td} service facade",
                                    line=line,
                                )


def detect_cycles(edges: dict[str, set[str]], max_len: int, max_cycles: int) -> list[list[str]]:
    nodes = set(edges.keys())
    for targets in edges.values():
        nodes.update(targets)

    color: dict[str, int] = {}
    stack: list[str] = []
    cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    sys.setrecursionlimit(max(10000, len(nodes) * 5 + 1000))

    def dfs(u: str) -> None:
        color[u] = 1
        stack.append(u)

        for v in edges.get(u, set()):
            if v not in nodes:
                continue

            state = color.get(v, 0)

            if state == 0:
                if len(stack) < max_len:
                    dfs(v)
            elif state == 1:
                try:
                    idx = stack.index(v)
                except ValueError:
                    continue

                cyc = stack[idx:]
                if len(cyc) <= max_len:
                    norm = normalize_cycle(cyc)
                    key = tuple(norm)
                    if key not in seen:
                        seen.add(key)
                        cycles.append(norm)

                        if len(cycles) >= max_cycles:
                            break

        stack.pop()
        color[u] = 2

    for n in sorted(nodes):
        if color.get(n, 0) == 0:
            dfs(n)

        if len(cycles) >= max_cycles:
            break

    return cycles


def check_dependency_cycles(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    if not eff.get("detect_module_cycles") and not eff.get("detect_domain_cycles"):
        return

    filtered_edges: dict[str, set[str]] = defaultdict(set)

    for caller, targets in graph.edges.items():
        caller_layer = layer_of_module(caller)
        if caller_layer in eff["graph_exempt_layers"]:
            continue

        for target in targets:
            target_layer = layer_of_module(target)
            if target_layer in eff["graph_exempt_layers"]:
                continue

            filtered_edges[caller].add(target)

    if eff.get("detect_module_cycles"):
        cycles = detect_cycles(
            filtered_edges,
            int(eff["max_cycle_length"]),
            int(eff["max_cycles"]),
        )

        for cyc in cycles:
            path = " -> ".join(cyc + [cyc[0]])
            first = cyc[0]
            rep.add(
                YEL,
                "DG2",
                "backend",
                module_path_rel(first, graph, repo),
                f"circular module dependency: {path}",
                intended="break the cycle by extracting shared logic into a lower layer (utils/service interface)",
            )

    if eff.get("detect_domain_cycles"):
        domain_edges: dict[str, set[str]] = defaultdict(set)

        for caller, targets in filtered_edges.items():
            sd = domain_of_module(caller, eff, graph)
            if not sd:
                continue

            for target in targets:
                td = domain_of_module(target, eff, graph)
                if td and td != sd:
                    domain_edges[sd].add(td)

        domain_cycles = detect_cycles(
            domain_edges,
            int(eff["max_cycle_length"]),
            int(eff["max_cycles"]),
        )

        for cyc in domain_cycles:
            path = " -> ".join(cyc + [cyc[0]])
            rep.add(
                RED,
                "DG2",
                "backend",
                "domain-graph",
                f"circular domain dependency: {path}",
                intended="redefine bounded-context boundaries; introduce explicit service contracts / events",
            )


def check_dead_modules(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    if not eff.get("detect_dead_modules"):
        return

    parents: set[str] = set()
    for module in graph.modules:
        parts = module.split(".")
        for i in range(1, len(parts)):
            parents.add(".".join(parts[:i]))

    reported = 0
    audit_layers = eff.get("dead_audit_layers", set())

    for module in sorted(graph.modules.keys()):
        layer_name = layer_of_module(module)

        if audit_layers and layer_name not in audit_layers:
            continue

        if layer_name in eff["dead_exempt_layers"]:
            continue

        if module in parents:
            continue

        if graph.fan_in.get(module, 0) > 0:
            continue

        if any(rx.search(module) for rx in eff["dead_entrypoints_c"]):
            continue

        rep.add(
            YEL,
            "A2",
            "backend",
            module_path_rel(module, graph, repo),
            "module has no inbound imports and is not an obvious entrypoint",
            intended="verify usage; delete if unused, or wire it through the correct layer",
        )

        reported += 1
        if reported >= 150:
            break


def check_metrics(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    if not eff.get("detect_metrics"):
        return

    god_fan_out = int(eff["god_fan_out"])
    god_fan_in = int(eff["god_fan_in"])

    reported = 0

    for module in sorted(graph.modules.keys()):
        fin = graph.fan_in.get(module, 0)
        fout = graph.fan_out.get(module, 0)
        total = fin + fout

        if total == 0:
            continue

        instability = fout / total

        if fout >= god_fan_out or fin >= god_fan_in:
            rep.add(
                YEL,
                "A1",
                "backend",
                module_path_rel(module, graph, repo),
                f"architecture hotspot: fan_in={fin}, fan_out={fout}, instability={instability:.2f}",
                intended="reduce coupling; split responsibilities or introduce an abstraction layer",
            )

            reported += 1
            if reported >= 150:
                break


def check_duplicate_classes(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    if not eff.get("detect_duplicate_classes"):
        return

    ignore = {str(x) for x in eff["dup_class_ignore"]}
    reported = 0

    for name, locs in sorted(graph.classes.items()):
        if name in ignore:
            continue

        if len(name) <= 3:
            continue

        mods = sorted({m for m, _ in locs})
        if len(mods) <= 1:
            continue

        first_line = locs[0][1] if locs else None

        rep.add(
            YEL,
            "D3",
            "backend",
            ", ".join(mods[:5]),
            f"class name '{name}' is defined in {len(mods)} modules",
            intended="rename or consolidate; duplicate class names create import/confusion drift",
            line=first_line,
        )

        reported += 1
        if reported >= 150:
            break


# ============================================================================
# 9. DYNAMIC IMPORTS, POLICY VALIDATION, FRONTEND, AUTO-POLICY
# ============================================================================

def check_dynamic_dependency_signals(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    if not eff.get("detect_dynamic_imports"):
        return

    reported = 0

    for caller, mod, line in graph.dynamic_imports:
        caller_layer = layer_of_module(caller)
        if caller_layer in eff["graph_exempt_layers"]:
            continue

        rep.add(
            YEL,
            "DG4",
            "backend",
            module_path_rel(caller, graph, repo),
            f"dynamic import resolves to '{mod}' (hidden dependency)",
            intended="prefer explicit static imports for auditable architecture",
            line=line,
        )

        reported += 1
        if reported >= 100:
            break

    reported = 0

    for caller, name, line in graph.dynamic_calls:
        caller_layer = layer_of_module(caller)
        if caller_layer in eff["graph_exempt_layers"]:
            continue

        rep.add(
            YEL,
            "DG5",
            "backend",
            module_path_rel(caller, graph, repo),
            f"dynamic execution/import obscures dependency graph ({name})",
            intended="avoid eval/exec/dynamic import_module for layer-critical code paths",
            line=line,
        )

        reported += 1
        if reported >= 100:
            break


def check_policy_config(repo: Path, rep: Report, eff: dict) -> None:
    if not eff.get("detect_policy_config"):
        return

    known_layers = eff.get("known_layers", set())

    for caller, targets in eff.get("forbidden_edges", {}).items():
        if known_layers and caller.lower() not in known_layers:
            rep.add(
                YEL,
                "CFG1",
                "repo",
                "layer_rules.yaml",
                f"forbidden_edges references unknown caller layer '{caller}'",
                intended="fix the layer name or add it to expected_backend_packages",
            )

        for target in targets:
            top = str(target).split(".", 1)[0].lower()
            if known_layers and top not in known_layers:
                rep.add(
                    YEL,
                    "CFG1",
                    "repo",
                    "layer_rules.yaml",
                    f"forbidden_edges references unknown target layer '{top}' from '{target}'",
                    intended="fix the layer name or add it to expected_backend_packages",
                )

    for key in ("ownership_layers", "graph_exempt_layers", "dead_exempt_layers", "no_init_dirs"):
        for layer_name in eff.get(key, set()):
            if known_layers and layer_name.lower() not in known_layers:
                rep.add(
                    YEL,
                    "CFG3",
                    "repo",
                    "governance.yaml",
                    f"{key} references unknown backend folder '{layer_name}'",
                    intended="remove it or create the expected backend package",
                )

    domains = eff.get("domains", {})

    if domains:
        for dom, cfg in domains.items():
            for imp in cfg.get("may_import", []):
                if imp not in domains:
                    rep.add(
                        YEL,
                        "CFG2",
                        "repo",
                        "layer_rules.yaml",
                        f"domain '{dom}' may_import references unknown domain '{imp}'",
                        intended="define the missing domain or fix the typo",
                    )

        policy_edges: dict[str, set[str]] = defaultdict(set)
        for dom, cfg in domains.items():
            for imp in cfg.get("may_import", []):
                if imp in domains and imp != dom:
                    policy_edges[dom].add(imp)

        policy_cycles = detect_cycles(policy_edges, 12, 30)
        for cyc in policy_cycles:
            path = " -> ".join(cyc + [cyc[0]])
            rep.add(
                YEL,
                "CFG4",
                "repo",
                "layer_rules.yaml",
                f"explicit domain policy contains a cycle: {path}",
                intended="bounded-context rules should be acyclic; introduce explicit contracts/events",
            )


def check_frontend_structure(repo: Path, rep: Report, eff: dict) -> None:
    if not eff.get("detect_frontend"):
        return

    frontend = repo / "frontend"
    if not frontend.exists():
        return

    workspaces = sorted(eff.get("frontend_workspaces", set()))
    source_ext = eff.get("frontend_source_ext", set())
    allow_root = eff.get("frontend_root_allow", set())

    if not (frontend / "package.json").exists():
        rep.add(
            YEL,
            "FE1",
            "frontend",
            rel(frontend, repo),
            "frontend root package.json missing",
            intended="add workspace root package.json for monorepo scripts",
        )

    for ws in workspaces:
        d = frontend / ws
        if not d.exists():
            rep.add(
                YEL,
                "FE1",
                "frontend",
                rel(d, repo),
                f"expected frontend workspace '{ws}' missing",
                intended="create/maintain workspace or update governance.yaml",
            )
            continue

        if not (d / "package.json").exists():
            rep.add(
                YEL,
                "FE1",
                "frontend",
                rel(d, repo),
                f"workspace '{ws}' missing package.json",
                intended="add package.json for this workspace",
            )

    roots = [frontend] + [frontend / ws for ws in workspaces if (frontend / ws).exists()]

    for root in roots:
        try:
            entries = list(root.iterdir())
        except OSError:
            entries = []

        for f in entries:
            if not f.is_file():
                continue

            if f.suffix.lower() not in source_ext:
                continue

            if f.name in allow_root:
                continue

            low = f.name.lower()
            scratchy = (
                is_scratch_name(f.stem, eff, broad=False)
                or low.startswith("_audit_")
                or low.startswith("verify_")
                or low.startswith("debug")
                or low.startswith("diag")
                or low.startswith("build_final")
                or low.startswith("build_out")
                or low.startswith("build_log")
                or low.startswith("inspect-")
                or low.endswith("_test.txt")
                or low.endswith("_test_output.txt")
                or low.endswith("_test_verbose.txt")
            )

            if scratchy:
                rep.add(
                    YEL,
                    "FE2",
                    "frontend",
                    rel(f, repo),
                    "frontend scratch/artifact script at package root",
                    intended="delete; keep only workspace config/package files at root",
                )

    flat_paths = [
        ("frontend/web_app/src/components", eff["frontend_flat_threshold"]),
        ("frontend/web_app/src/lib", eff["frontend_flat_threshold"]),
        ("frontend/web_app/src/hooks", eff["frontend_flat_threshold"]),
        ("frontend/mobile_app/components", eff["frontend_flat_threshold"]),
        ("frontend/mobile_app/lib", eff["frontend_flat_threshold"]),
        ("frontend/shared/src", eff["frontend_flat_threshold"]),
    ]

    for p, threshold in flat_paths:
        d = repo / p
        if not d.exists():
            continue

        try:
            direct = [
                x
                for x in d.iterdir()
                if x.is_file() and x.suffix.lower() in source_ext
            ]
        except OSError:
            direct = []

        if len(direct) > int(threshold):
            rep.add(
                YEL,
                "FE3",
                "frontend",
                rel(d, repo),
                f"frontend folder is flat ({len(direct)} direct source files)",
                intended="group by feature/domain (e.g. orders/, finance/, supplier/, ui/)",
            )

    reported = 0
    skip_parts = {
        "e2e",
        "__tests__",
        "tests",
        "test-output",
        "playwright-report",
        "coverage",
        ".next",
        "dist",
        "build",
        "tmp",
        "assets",
    }

    for ws in workspaces:
        wsdir = frontend / ws
        if not wsdir.exists():
            continue

        for d, entries in walk_dirs(wsdir, eff["ignore_dirs"]):
            if d == wsdir:
                continue

            try:
                parts = [x.lower() for x in d.relative_to(wsdir).parts]
            except ValueError:
                continue

            if any(x in skip_parts for x in parts):
                continue

            count = sum(
                1
                for e in entries
                if e.is_file() and e.suffix.lower() in source_ext
            )

            if count > int(eff["frontend_large_folder_threshold"]):
                rep.add(
                    YEL,
                    "FE5",
                    "frontend",
                    rel(d, repo),
                    f"frontend folder has {count} direct source files (scaling risk)",
                    intended="split into feature/domain sub-folders",
                )

                reported += 1
                if reported >= 100:
                    break

        if reported >= 100:
            break

    import_re = re.compile(
        r"""(?:import\s+[^'"]*?\s+from\s+|export\s+[^'"]*?\s+from\s+|require\(\s*|import\(\s*)['"]([^'"]+)['"]"""
    )

    for ws in workspaces:
        wsdir = frontend / ws
        if not wsdir.exists():
            continue

        reported_ws = 0

        for f in iter_text_files(wsdir, eff):
            if f.suffix.lower() not in source_ext:
                continue

            if in_parts(
                f,
                "node_modules",
                ".next",
                "dist",
                "build",
                "coverage",
                "test-results",
                "playwright-report",
                "e2e",
                "__tests__",
            ):
                continue

            t = read_text(f)
            if not t:
                continue

            for i, line in enumerate(t.splitlines(), 1):
                m = import_re.search(line)
                if not m:
                    continue

                imp = m.group(1)
                if not imp.startswith("."):
                    continue

                try:
                    resolved = (f.parent / imp).resolve()
                except Exception:
                    continue

                if is_relative_to(resolved, wsdir):
                    continue

                crosses = False

                if is_relative_to(resolved, frontend / "shared"):
                    crosses = True
                else:
                    for other in workspaces:
                        if other == ws:
                            continue
                        if is_relative_to(resolved, frontend / other):
                            crosses = True
                            break

                if crosses:
                    rep.add(
                        YEL,
                        "FE4",
                        "frontend",
                        rel(f, repo),
                        f"relative import crosses workspace boundary: {imp}",
                        intended="import shared via workspace package name, not relative path",
                        line=i,
                    )

                    reported_ws += 1
                    break

            if reported_ws >= 50:
                break


def collect_frontend_metrics(repo: Path, eff: dict) -> dict:
    frontend = repo / "frontend"
    metrics: dict[str, Any] = {}

    if not frontend.exists():
        return metrics

    workspaces = sorted(eff.get("frontend_workspaces", set()))
    source_ext = eff.get("frontend_source_ext", set())

    for ws in workspaces:
        d = frontend / ws
        if not d.exists():
            continue

        source_files = sum(
            1
            for f in iter_text_files(d, eff)
            if f.suffix.lower() in source_ext
        )

        dirs = sum(1 for _ in walk_dirs(d, eff["ignore_dirs"]))

        metrics[ws] = {
            "source_files": source_files,
            "dirs": dirs,
        }

    return metrics


def _merge_features(base: dict, current: dict) -> dict:
    out: dict[str, dict[str, list[str]]] = {}

    keys = set(base.keys()) | set(current.keys())

    for key in keys:
        base_layers = base.get(key, {})
        cur_layers = current.get(key, {})
        layer_keys = set(base_layers.keys()) | set(cur_layers.keys())

        out[key] = {}

        for layer in layer_keys:
            base_vals = set(base_layers.get(layer, []))
            cur_vals = set(cur_layers.get(layer, []))
            out[key][layer] = sorted(base_vals | cur_vals)

    return out


def reconcile_auto_policy(
    repo: Path,
    rep: Report,
    eff: dict,
    reg: FeatureRegistry,
    auto_policy_path: Path,
) -> None:
    if not eff.get("detect_auto_discovery"):
        return

    current = reg.to_json()

    try:
        auto_policy_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        rep.add(
            YEL,
            "AUTO0",
            "repo",
            rel(auto_policy_path, repo),
            "could not create .governance directory for auto-policy",
            intended="ensure the repository workspace is writable",
        )
        return

    data = None
    if auto_policy_path.exists():
        try:
            data = json.loads(auto_policy_path.read_text(encoding="utf-8"))
        except Exception:
            data = None

    if not isinstance(data, dict):
        payload = {
            "version": 1,
            "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            **current,
        }

        try:
            auto_policy_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            rep.add(
                GRN,
                "AUTO0",
                "repo",
                rel(auto_policy_path, repo),
                "auto-discovery baseline created (safe recognition only)",
                intended="run normally; the auditor learns conventional domains/features automatically",
            )
        except Exception:
            rep.add(
                YEL,
                "AUTO0",
                "repo",
                rel(auto_policy_path, repo),
                "could not write auto-policy baseline",
                intended="ensure .governance/ is writable or use --no-auto-policy",
            )

        return

    baseline_top = set(data.get("backend_top_dirs", []))
    current_top = set(reg.top_dirs)
    new_top = sorted(current_top - baseline_top)

    for d in new_top:
        rep.add(
            YEL,
            "AUTO8",
            "backend",
            f"backend/{d}",
            "new top-level backend package detected",
            intended="prefer placing features inside routers/controllers/services/models/providers/events/jobs/utils; add a new layer only with an ADR",
        )

    baseline_domains = set(data.get("domains", []))
    new_domains = sorted(reg.domains - baseline_domains)

    for d in new_domains:
        rep.add(
            GRN,
            "AUTO3",
            "backend",
            f"backend/services|models/{d}",
            f"new domain detected: {d}",
            intended="auto-recognized; keep domain grouped in services/models/providers",
        )

    baseline_fe = set(data.get("frontend_features", []))
    new_fe = sorted(reg.frontend_features - baseline_fe)

    for f in new_fe[:100]:
        rep.add(
            GRN,
            "AUTO10",
            "frontend",
            f"frontend feature: {f}",
            f"new frontend feature detected: {f}",
            intended="keep feature isolated under features/<feature>/ or components/<feature>/",
        )

    baseline_features = set(data.get("features", {}).keys())
    new_features = sorted(set(reg.features.keys()) - baseline_features)

    for f in new_features[:100]:
        rep.add(
            GRN,
            "AUTO10",
            "repo",
            f"feature: {f}",
            f"new feature detected: {f}",
            intended="auto-recognized from naming/location; no manual registration required",
        )

    baseline_edges = {tuple(x) for x in data.get("allowed_domain_edges", [])}
    new_edges = sorted(reg.domain_edges - baseline_edges)

    for s, t in new_edges[:100]:
        rep.add(
            GRN,
            "AUTO6",
            "backend",
            f"{s} -> {t}",
            "new cross-domain dependency learned",
            intended="allowed by auto-learning because no explicit domain policy forbids it; add domains in layer_rules.yaml to enforce ownership",
        )

    merged = dict(data)
    merged["version"] = 1
    merged["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Safe auto-add: domains, features, frontend features, learned domain edges.
    # Top-level backend dirs are NOT auto-added, so unknown layers keep surfacing.
    merged["backend_top_dirs"] = sorted(baseline_top)
    merged["domains"] = sorted(baseline_domains | reg.domains)
    merged["frontend_features"] = sorted(baseline_fe | reg.frontend_features)
    merged["features"] = _merge_features(data.get("features", {}), current.get("features", {}))
    merged["allowed_domain_edges"] = sorted({tuple(x) for x in baseline_edges} | reg.domain_edges)

    try:
        auto_policy_path.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    except Exception:
        rep.add(
            YEL,
            "AUTO0",
            "repo",
            rel(auto_policy_path, repo),
            "could not update auto-policy",
            intended="ensure .governance/ is writable or use --no-auto-policy",
        )


def compute_debt_score(rep: Report, eff: dict) -> int:
    red = sum(1 for f in rep.findings if f.sev == RED)
    yel = sum(1 for f in rep.findings if f.sev == YEL)

    by = rep.counters

    score = red * 100 + yel * 15
    score += by.get("DG2", 0) * 35
    score += by.get("DG3", 0) * 50
    score += by.get("DG4", 0) * 10
    score += by.get("DG5", 0) * 8
    score += by.get("A1", 0) * 12
    score += by.get("A2", 0) * 4
    score += by.get("D1", 0) * 10
    score += by.get("D2", 0) * 8
    score += by.get("D3", 0) * 5
    score += sum(v for k, v in by.items() if k.startswith("CFG")) * 40
    score += sum(v for k, v in by.items() if k.startswith("FE")) * 8
    score += by.get("AUTO8", 0) * 20

    return int(score)


# ============================================================================
# 10. SUMMARY / METRICS / TREND
# ============================================================================

def collect_info(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    def n(sub: str) -> int:
        d = repo / "backend" / sub
        if not d.exists():
            return 0
        return sum(1 for x in d.rglob("*.py") if x.is_file())

    rep.add(
        GRN,
        "I1",
        "repo",
        rel(repo, repo),
        f"backend models={n('models')} routers={n('routers')} controllers={n('controllers')} "
        f"services={n('services')} middleware={n('middleware')}",
    )

    src = (
        "scope YAML (single source of truth)"
        if eff["from_yaml"]
        else "EMBEDDED FALLBACK (create documents/scope/*.yaml to make scope authoritative)"
    )

    rep.add(
        GRN,
        "I2",
        "repo",
        "documents/scope/",
        f"rules loaded from: {src}",
    )

    rep.add(
        GRN,
        "I3",
        "repo",
        "backend/",
        f"module graph: modules={len(graph.modules)}, edges={sum(len(v) for v in graph.edges.values())}, "
        f"classes={len(graph.classes)}",
    )


def build_summary(
    repo: Path,
    rep: Report,
    graph: ModuleGraph,
    debt_score: int,
    frontend_metrics: dict,
    reg: FeatureRegistry,
) -> dict:
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)

    layer_counts: dict[str, int] = defaultdict(int)
    for module in graph.modules:
        layer_counts[layer_of_module(module)] += 1

    top_fan_in = sorted(graph.fan_in.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_fan_out = sorted(graph.fan_out.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": str(repo),
        "red": n_red,
        "yellow": n_yel,
        "green": n_grn,
        "debt_score": debt_score,
        "by_code": dict(rep.counters),
        "modules": len(graph.modules),
        "edges": sum(len(v) for v in graph.edges.values()),
        "classes": len(graph.classes),
        "layer_counts": dict(layer_counts),
        "top_fan_in": top_fan_in,
        "top_fan_out": top_fan_out,
        "frontend_metrics": frontend_metrics,
        "auto_discovery": {
            "domains": len(reg.domains),
            "features": len(reg.features),
            "frontend_features": len(reg.frontend_features),
            "backend_top_dirs": len(reg.top_dirs),
            "domain_edges": len(reg.domain_edges),
        },
    }


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def print_trend(rep: Report, current: dict, baseline: dict | None) -> None:
    if not baseline:
        print("\nNo trend baseline found. Use --update-trend to create one.")
        return

    old_red = int(baseline.get("red", 0))
    old_yel = int(baseline.get("yellow", 0))
    old_score = int(baseline.get("debt_score", 0))

    new_red = int(current.get("red", 0))
    new_yel = int(current.get("yellow", 0))
    new_score = int(current.get("debt_score", 0))

    print("\n" + "=" * 76)
    print("  ARCHITECTURE TREND")
    print("=" * 76)
    print(f"  RED: {old_red} -> {new_red}   YEL: {old_yel} -> {new_yel}")
    print(f"  DEBT SCORE: {old_score} -> {new_score}")

    old_codes = baseline.get("by_code", {})
    new_codes = current.get("by_code", {})
    all_codes = sorted(set(old_codes.keys()) | set(new_codes.keys()))

    regressions = []
    improvements = []

    for code in all_codes:
        old = int(old_codes.get(code, 0))
        new = int(new_codes.get(code, 0))
        delta = new - old

        if delta > 0:
            regressions.append((code, old, new, delta))
        elif delta < 0:
            improvements.append((code, old, new, delta))

    if regressions:
        print("\n  Regressions:")
        for code, old, new, delta in regressions:
            print(f"    +{delta:<2} {code:<4} {old} -> {new}")

    if improvements:
        print("\n  Improvements:")
        for code, old, new, delta in improvements:
            print(f"    {delta:<3} {code:<4} {old} -> {new}")

    if not regressions and not improvements:
        print("\n  No rule-count changes since baseline.")

    rep.add(
        GRN,
        "T1",
        "repo",
        "trend",
        f"RED {old_red}->{new_red}, YEL {old_yel}->{new_yel}, DEBT {old_score}->{new_score}",
        intended="use trend reporting to drive architecture debt down continuously",
    )


def update_trend(path: Path, current: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(current, indent=2), encoding="utf-8")


# ============================================================================
# 11. RENDERING
# ============================================================================

def render_intended_tree() -> str:
    return "\n".join(
        [
            "# INTENDED ZOZI STRUCTURE (target — derived from governance model)",
            "Logical domains `database` & `security` live INSIDE backend/ by design.",
            "Sub-folder axis: SURFACE in routers/ & controllers/ (admin/supplier/...);",
            "                 DOMAIN  in services/ & models/ (finance/orders/...).",
            "```",
            "zozi/",
            "├── backend/",
            "│   ├── routers/        (admin/ supplier/ customer/ public/ webhooks/ = surface OK)",
            "│   ├── controllers/    (admin/ supplier/ ... surface OK; thin orchestration)",
            "│   ├── services/       (finance/ orders/ catalog/ supplier/ logistics/ comms/ hr/ ai/ = domain REQUIRED)",
            "│   ├── models/         (same domain sub-packages; each file declares __table_args__ schema)",
            "│   ├── middleware/  dependencies/  providers/  utils/  events/  jobs/  data/",
            "│   ├── db/  alembic/   (= the 'database' logical domain; ONLY migrations home)",
            "│   └── tests/  scripts/",
            "├── frontend/   (web_app · mobile_app · shared)",
            "├── documents/",
            "│   ├── scope/          (AUTHORITATIVE specs + optional YAML policy)",
            "│   └── archive/        (everything else)",
            "├── monitoring/  nginx/  (infra)",
            "├── experiments/  design/   (gitignored outputs / logo source)",
            "└── .gitignore  .env.example  README.md  docker-compose.yml  railway.toml",
            "```",
        ]
    )


def render_stdout(repo: Path, rep: Report, show_intended: bool, summary: dict) -> int:
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary.get("debt_score", 0)

    print("=" * 76)
    print("  ZOZI ARCHITECTURE GOVERNANCE AUDIT v3.2")
    print("  structure · layers · dependency graph · cycles · ownership · metrics")
    print("  dynamic imports · policy validation · frontend scaling · auto-discovery")
    print("=" * 76)
    print(f"  repo: {repo}")
    print(f"  [RED] VIOLATIONS : {n_red}    [YEL] ADVISORIES : {n_yel}    [GRN] INFO : {n_grn}")
    print(f"  ARCHITECTURE DEBT SCORE: {debt}")
    print("  by rule: " + ", ".join(f"{k}={v}" for k, v in sorted(rep.counters.items())))

    hot = [f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED]
    hot.sort(key=lambda f: (0 if f.sev == RED else 1, f.code, f.path))

    print("-" * 76)
    print(f"  DAMAGE HOTLIST  ({len(hot)} items actively harming structure/scale)")
    print("-" * 76)

    for f in hot[:90]:
        print(f"  {SEV_ICON[f.sev]} {f.code:<5} [{f.domain:<8}] {f.loc()}")
        print(f"        {f.message}")
        if f.intended:
            print(f"        -> intended: {f.intended}")

    if len(hot) > 90:
        print(f"  ... +{len(hot) - 90} more (see report)")

    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)

    for dom in ["repo", "backend", "database", "frontend", "security", "docs", "infra"]:
        items = by_dom.get(dom, [])
        if not items:
            continue

        print("\n" + "=" * 76)
        print(f"  DOMAIN: {dom.upper()}  ({len(items)} finding(s))")
        print("=" * 76)

        for sev in (RED, YEL, GRN):
            for f in [x for x in items if x.sev == sev]:
                print(f"  {SEV_TAG[sev]} {f.code}  {f.loc()}")
                print(f"        {f.message}")
                if f.intended:
                    print(f"        -> {f.intended}")

    print("\n" + "=" * 76)
    print("  ARCHITECTURE METRICS")
    print("=" * 76)
    print(f"  modules: {summary['modules']}   edges: {summary['edges']}   classes: {summary['classes']}")

    if summary.get("layer_counts"):
        print("  layer counts: " + ", ".join(f"{k}={v}" for k, v in sorted(summary["layer_counts"].items())))

    if summary.get("top_fan_in"):
        print("\n  Top fan-in:")
        for module, count in summary["top_fan_in"]:
            print(f"    {count:>3}  {module}")

    if summary.get("top_fan_out"):
        print("\n  Top fan-out:")
        for module, count in summary["top_fan_out"]:
            print(f"    {count:>3}  {module}")

    if summary.get("frontend_metrics"):
        print("\n  Frontend workspace metrics:")
        for ws, m in sorted(summary["frontend_metrics"].items()):
            print(f"    {ws}: source_files={m.get('source_files', 0)}, dirs={m.get('dirs', 0)}")

    if summary.get("auto_discovery"):
        ad = summary["auto_discovery"]
        print("\n  Auto-discovery:")
        print(f"    domains={ad.get('domains', 0)}")
        print(f"    features={ad.get('features', 0)}")
        print(f"    frontend_features={ad.get('frontend_features', 0)}")
        print(f"    backend_top_dirs={ad.get('backend_top_dirs', 0)}")
        print(f"    learned_domain_edges={ad.get('domain_edges', 0)}")

    if show_intended:
        print("\n" + render_intended_tree())

    print("\n" + "=" * 76)
    return n_red


def render_markdown(repo: Path, rep: Report, out: Path, summary: dict) -> None:
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary.get("debt_score", 0)

    L = [
        "# Architecture Governance Audit Report v3.2 (GENERATED — do not hand-edit)",
        "",
        f"**Repo:** `{repo}`  ",
        f"**Result:** 🔴 {n_red} · 🟡 {n_yel} · 🟢 {n_grn}  ",
        f"**Architecture Debt Score:** `{debt}`  ",
        "**Ephemeral. Add to `.gitignore`. NOT an authoritative spec (those live in `documents/scope/`).**",
        "",
        render_intended_tree(),
        "",
        "## Scorecard",
        "",
        "| Code | Count | Sev | Meaning |",
        "|---|---:|---|---|",
    ]

    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        L.append(f"| {code} | {rep.counters[code]} | {SEV_ICON[sev]} {sev} | {RULE_MEANING.get(code, '')} |")

    hot = sorted(
        [f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED],
        key=lambda f: (0 if f.sev == RED else 1, f.code),
    )

    L += [
        "",
        "## 🔥 Damage Hotlist (fix these first)",
        "",
        "| Sev | Rule | Domain | Location | Problem | Intended home / action |",
        "|---|---|---|---|---|---|",
    ]

    for f in hot:
        L.append(
            f"| {SEV_ICON[f.sev]} | {f.code} | {f.domain} | `{f.loc()}` | {f.message} | {f.intended or '-'} |"
        )

    L += [
        "",
        "## Architecture Metrics",
        "",
        f"- architecture debt score: **{debt}**",
        f"- modules: **{summary['modules']}**",
        f"- dependency edges: **{summary['edges']}**",
        f"- classes: **{summary['classes']}**",
    ]

    if summary.get("layer_counts"):
        L.append("- layer counts: " + ", ".join(f"`{k}={v}`" for k, v in sorted(summary["layer_counts"].items())))

    if summary.get("top_fan_in"):
        L += ["", "### Top fan-in", "", "| Module | Fan-in |", "|---|---:|"]
        for module, count in summary["top_fan_in"]:
            L.append(f"| `{module}` | {count} |")

    if summary.get("top_fan_out"):
        L += ["", "### Top fan-out", "", "| Module | Fan-out |", "|---|---:|"]
        for module, count in summary["top_fan_out"]:
            L.append(f"| `{module}` | {count} |")

    if summary.get("frontend_metrics"):
        L += ["", "### Frontend workspace metrics", "", "| Workspace | Source files | Dirs |", "|---|---:|---:|"]
        for ws, m in sorted(summary["frontend_metrics"].items()):
            L.append(f"| `{ws}` | {m.get('source_files', 0)} | {m.get('dirs', 0)} |")

    if summary.get("auto_discovery"):
        ad = summary["auto_discovery"]
        L += [
            "",
            "### Auto-discovery",
            "",
            f"- domains: **{ad.get('domains', 0)}**",
            f"- features: **{ad.get('features', 0)}**",
            f"- frontend features: **{ad.get('frontend_features', 0)}**",
            f"- backend top dirs: **{ad.get('backend_top_dirs', 0)}**",
            f"- learned domain edges: **{ad.get('domain_edges', 0)}**",
        ]

    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)

    for dom in ["repo", "backend", "database", "frontend", "security", "docs", "infra"]:
        items = by_dom.get(dom, [])
        if not items:
            continue

        L += ["", f"## Domain: {dom}", ""]

        for f in items:
            L.append(
                f"- {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}"
                + (f" → *{f.intended}*" if f.intended else "")
            )

    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_metrics_json(path: Path, summary: dict, graph: ModuleGraph) -> None:
    modules = []

    for module in sorted(graph.modules.keys()):
        fin = graph.fan_in.get(module, 0)
        fout = graph.fan_out.get(module, 0)
        total = fin + fout
        instability = (fout / total) if total else 0.0

        modules.append(
            {
                "module": module,
                "fan_in": fin,
                "fan_out": fout,
                "instability": round(instability, 4),
            }
        )

    modules.sort(key=lambda m: (m["fan_in"] + m["fan_out"]), reverse=True)

    payload = {
        "summary": summary,
        "modules": modules[:2000],
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ============================================================================
# 12. MAIN
# ============================================================================

def find_repo(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()

    cur = Path(__file__).resolve().parent

    for cand in (cur, cur.parent, cur.parent.parent, cur.parent.parent.parent):
        if (cand / "backend").is_dir() and (cand / "frontend").is_dir():
            return cand

    return Path.cwd().resolve()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Read-only repo-wide ZOZI architecture governance auditor v3.2."
    )

    ap.add_argument("--root", default=None, help="repo root (default: auto-detect)")
    ap.add_argument(
        "--rules-dir",
        default=None,
        help="dir holding repo_structure.yaml + layer_rules.yaml + governance.yaml (default: documents/scope)",
    )
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--json", default=None, help="write findings + summary JSON here (tooling/CI)")
    ap.add_argument("--metrics-json", default=None, help="write module metrics JSON here")
    ap.add_argument("--no-write", action="store_true", help="do not write the .md report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--show-intended", action="store_true", help="also print the target tree")
    ap.add_argument("--trend-file", default=None, help="JSON file used for trend comparison")
    ap.add_argument(
        "--update-trend",
        action="store_true",
        help="overwrite the trend file with the current summary",
    )
    ap.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: default JSON/metrics artifacts and trend file if not provided",
    )
    ap.add_argument(
        "--auto-policy",
        default=None,
        help="path to auto-discovery policy JSON (default: .governance/zozi_auto_policy.json)",
    )
    ap.add_argument(
        "--no-auto-policy",
        action="store_true",
        help="disable auto-discovery policy learning",
    )
    ap.add_argument(
        "--reset-auto-policy",
        action="store_true",
        help="delete existing auto-policy and create a fresh baseline",
    )

    args = ap.parse_args()

    repo = find_repo(args.root)
    if not repo.is_dir():
        print(f"[FATAL] repo root not found: {repo}", file=sys.stderr)
        return 2

    if args.ci:
        if not args.json:
            args.json = str(repo / "out" / "governance" / "audit.json")
        if not args.metrics_json:
            args.metrics_json = str(repo / "out" / "governance" / "metrics.json")
        if not args.trend_file:
            args.trend_file = str(repo / ".governance" / "architecture_trend.json")

    eff = load_rules(repo, Path(args.rules_dir) if args.rules_dir else None)

    print(
        f"Scanning {repo} ...  (rules: {'YAML' if eff['from_yaml'] else 'embedded fallback'})"
    )

    rep = Report()
    graph = build_module_graph(repo, eff)
    reg = discover_features(repo, eff, graph)

    auto_policy_path = None
    if not args.no_auto_policy:
        auto_policy_path = (
            Path(args.auto_policy).resolve()
            if args.auto_policy
            else repo / ".governance" / "zozi_auto_policy.json"
        )

        if args.reset_auto_policy and auto_policy_path.exists():
            try:
                auto_policy_path.unlink()
            except Exception:
                pass

        reconcile_auto_policy(repo, rep, eff, reg, auto_policy_path)

    # Repository hygiene / structure.
    check_gitignore(repo, rep, eff)
    check_lockfiles(repo, rep, eff)
    check_cache_dirs(repo, rep, eff)
    check_node_modules(repo, rep, eff)
    check_hardcoded_local_paths(repo, rep, eff)
    check_ghost_backend(repo, rep)
    check_duplicate_basenames(repo, rep, eff)
    check_secrets_on_disk(repo, rep, eff)
    check_intended_violations(repo, rep, eff)
    check_backend_root_modules(repo, rep, eff)
    check_scratch_scripts(repo, rep, eff)
    check_doc_and_root_allowlists(repo, rep, eff)
    check_expected_packages(repo, rep, eff)
    check_package_init_shape(repo, rep, eff)
    check_subfolder_axis_and_shape(repo, rep, eff)

    # Backend layer / dependency architecture.
    check_layer_writes(repo, rep, eff)
    check_router_outside(repo, rep, eff)
    check_dependency_graph(repo, rep, eff, graph)
    check_dependency_cycles(repo, rep, eff, graph)
    check_dead_modules(repo, rep, eff, graph)
    check_metrics(repo, rep, eff, graph)
    check_duplicate_classes(repo, rep, eff, graph)

    # v3.1/v3.2 additions.
    check_dynamic_dependency_signals(repo, rep, eff, graph)
    check_policy_config(repo, rep, eff)
    check_frontend_structure(repo, rep, eff)

    # Security / scale smells.
    check_rls_cluster(repo, rep, eff)
    check_raw_env_in_middleware(repo, rep, eff)
    check_media_on_disk(repo, rep, eff)

    # Summary.
    collect_info(repo, rep, eff, graph)
    frontend_metrics = collect_frontend_metrics(repo, eff)
    debt_score = compute_debt_score(rep, eff)

    rep.add(
        GRN,
        "MET1",
        "repo",
        "architecture-debt",
        f"architecture debt score = {debt_score}",
        intended="track this number down over time; lower is healthier",
    )

    summary = build_summary(repo, rep, graph, debt_score, frontend_metrics, reg)

    # Trend.
    trend_path = Path(args.trend_file).resolve() if args.trend_file else None

    if trend_path:
        if args.update_trend:
            update_trend(trend_path, summary)
            print(f"\nTrend file updated: {trend_path}")
        else:
            baseline = read_json(trend_path)
            print_trend(rep, summary, baseline)

    n_red = render_stdout(repo, rep, args.show_intended, summary)

    if not args.no_write:
        out = Path(args.out).resolve() if args.out else (repo / "REPO_LAYOUT_AUDIT_REPORT.md")
        render_markdown(repo, rep, out, summary)
        print(f"\nReport written: {out}  (generated -> .gitignore it; NOT under documents/scope/)")

    if args.json:
        jp = Path(args.json).resolve()
        jp.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "summary": summary,
            "findings": [
                {
                    "sev": f.sev,
                    "code": f.code,
                    "domain": f.domain,
                    "path": f.path,
                    "line": f.line,
                    "message": f.message,
                    "intended": f.intended,
                }
                for f in rep.findings
            ],
        }

        jp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"JSON written:   {jp}")

    if args.metrics_json:
        mp = Path(args.metrics_json).resolve()
        write_metrics_json(mp, summary, graph)
        print(f"Metrics written: {mp}")

    return 1 if (n_red and not args.no_fail) else 0


if __name__ == "__main__":
    sys.exit(main())