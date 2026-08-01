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
  ^ Read scripts\SYSTEM_ARCHTECTURE_AUDIT_USAGE.md for detail understanding of Usage and Output.
  
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
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# ============================================================================
# 1. DEFAULT EMBEDDED RULES
# ============================================================================

_ACTIVE_EFF = None
_ACTIVE_REG = None

DEFAULT_IGNORE_DIRS = {".git","node_modules",".venv","venv","__pycache__",".mypy_cache",".pytest_cache",".ruff_cache",".tox",
                       "htmlcov",".next",".expo",".kotlin","gradle","android","ios",".idea",".vscode","test-results",".playwright-artifacts-0",
                       "playwright-out","static-tmp",".web-build-test","artifacts","uploads",".turbo","dist","build","coverage",
                       "playwright-report","test-output","tmp",
                       }

DEFAULT_CACHE_DIR_NAMES = {".ruff_cache",".mypy_cache",".pytest_cache",".next",".expo","dist","build","coverage","htmlcov",".turbo","web-dist",
                           ".playwright-artifacts-0","test-results","playwright-report","test-output",
                        }

DEFAULT_TEXT_EXT = {".py",".js",".ts",".tsx",".jsx",".json",".yml",".yaml",".md",".ini",".toml",".css",".html",".sh",".bat",".ps1",".cjs",".mjs",
                    }

DEFAULT_SOURCE_EXT = {".py",".js",".ts",".tsx",".jsx",".sh",".bat",".ps1",}

DEFAULT_FRONTEND_SOURCE_EXT = {".ts",".tsx",".js",".jsx",".cjs",".mjs",}

DEFAULT_MAX_READ_BYTES = 2_000_000

DEFAULT_SCRATCH_PHRASES = ["countdivs","stackdivs","printlines","linenums","fixtailwind","patch-vars","patch_vars","verify-tmp",
                           "verify_tmp","impmain","client_tmp","reset_tmp",
                        ]

DEFAULT_SCRATCH_TOKENS = ["tmp","temp","scratch","debug","test","check","write","list","reset","verify","run","script","probe","diag","inspect",
                        ]

DEFAULT_SCRIPTS_SAFE_TOKENS = {"tmp","temp","scratch","debug","diag","inspect",}

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

# Document file extensions that are ALWAYS allowed at documents/ root
# (documents/ is the doc home — these never need listing).  A file at documents/
# root is only flagged (F8) if its extension is NOT here AND its name is not in
# allow_docs_root.  Override via governance.yaml -> policy.doc_ext if needed.
DEFAULT_DOC_EXT = {".md", ".txt", ".rst", ".adoc", ".pdf"}

DEFAULT_FORBIDDEN_ROOT = {
"backend": [
    r".*\.(log|db|db-shm|db-wal)$",
    r"^token\.tmp$",
    r"^.*\.json$",
    r"^(?!requirements\.txt$).*\.txt$",
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
    "add", "commit", "delete", "merge", "flush", "refresh",
    "execute", "bulk_insert_mappings", "bulk_save_objects",
    "begin", "rollback", "savepoint",
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

DEFAULT_FRONTEND_ROOT_ALLOW = {"package.json","package-lock.json","pnpm-lock.yaml","yarn.lock","pnpm-workspace.yaml","tsconfig.json",
                               "tsconfig.build.json","next.config.ts","next-env.d.ts","middleware.ts","eslint.config.js","jest.config.js","jest.setup.ts",
                               "playwright.config.ts","postcss.config.js","tailwind.config.js","babel.config.js","metro.config.js","app.config.js",
                               "app.json","expo-env.d.ts","README.md","ERROR_HANDLING.md","Dockerfile","sentry.config.ts","patch-logbox.js",
                                }

DEFAULT_FLAT_THRESHOLD = 30
DEFAULT_LARGE_SUBPACKAGE_THRESHOLD = 80
DEFAULT_GOD_FAN_OUT = 20
DEFAULT_GOD_FAN_IN = 30
DEFAULT_MAX_CYCLES = 80
DEFAULT_MAX_CYCLE_LENGTH = 10
DEFAULT_FRONTEND_FLAT_THRESHOLD = 40
DEFAULT_FRONTEND_LARGE_FOLDER_THRESHOLD = 120

FEATURE_STOP_NAMES = {"__init__","index","page","layout","loading","error","not-found","route","main","app","init","package","types","utils",
                      "helpers","shared","common","ui","admin","supplier","customer","public","webhooks","webhook","api","internal","external",
                      "src","components","features","hooks","lib","services","models","controllers","routers",
                    }

FEATURE_SUFFIXES = ["_service","_services","_controller","_controllers","_router","_routers","_model","_models","_provider","_providers",
                    "_event","_events","_job","_jobs","_page","_pages","_screen","_screens","_component","_components","_hook","_hooks",
                    "_store","_stores","_api","_utils","_helpers","_types","_test","_tests","_spec",
                    ]

# ============================================================================
# v3.5 AUTO-LEARNING DOMAIN PLACEMENT ENGINE
# ============================================================================

# RULE_MEANING.update({
#     "DOM1": "file should be moved into its detected domain sub-folder",
#     "DOM2": "file is inside the wrong domain sub-folder",
#     "DOM3": "domain files are scattered across surface/multiple folders",
#     "DOM6": "new domain candidate auto-detected from code patterns",
# })

# HOTLIST_RULES.update({
#     "DOM1",
#     "DOM2",
#     "DOM3",
# })

AUTO_ROUTE_PREFIX_RE = re.compile(
    r"APIRouter\([^)]*prefix\s*=\s*['\"]([^'\"]+)['\"]",
    re.I,
)

AUTO_ROUTE_DECOR_RE = re.compile(
    r"@\w+\.(?:get|post|put|patch|delete|options|head|websocket)\(\s*['\"]([^'\"]+)['\"]",
    re.I,
)


@dataclass
class AutoDomainModel:
    domains: set[str] = field(default_factory=set)
    surfaces: set[str] = field(default_factory=set)
    profiles: dict[str, dict[str, float]] = field(default_factory=dict)
    candidate_domains: set[str] = field(default_factory=set)
    token_files: dict[str, set[str]] = field(default_factory=dict)


def _auto_stop_tokens(eff: dict) -> set[str]:
    stop = {
        str(x).lower()
        for x in eff.get("feature_stop_names", FEATURE_STOP_NAMES)
    }

    stop |= {
        str(x).lower()
        for x in eff.get("surface_names", DEFAULT_SURFACE_NAMES)
    }

    stop |= {
        str(x).lower()
        for x in eff.get("placement", {}).get("stop_tokens", [])
    }

    stop.add("__init__")

    return {x for x in stop if x}


def auto_tokenize(name: str, eff: dict) -> set[str]:
    """
    Convert names, paths, imports, routes, and table names into meaningful tokens.
    This contains no hardcoded business-domain knowledge.
    """
    if not name:
        return set()

    raw = str(name)
    raw = raw.replace("\\", "/")

    # CamelCase -> snake_case
    raw = re.sub(r"(?<!^)(?=[A-Z])", "_", raw)

    # Replace punctuation/path separators
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw)

    tokens = {
        t.lower()
        for t in raw.split("_")
        if t
    }

    stop = _auto_stop_tokens(eff)

    return {
        t
        for t in tokens
        if t not in stop and len(t) >= 3
    }


def _add_auto_signals(
    signals: dict[str, float],
    tokens: set[str],
    weight: float,
) -> None:
    for token in tokens:
        signals[token] = signals.get(token, 0.0) + float(weight)


def extract_auto_signals(
    f: Path,
    backend: Path,
    text: str | None,
    tree: ast.Module | None,
    eff: dict,
) -> dict[str, float]:
    """
    Extract domain signals from one Python file.

    Signal sources:
      - file name
      - class names
      - function names
      - import paths
      - route prefixes
      - route paths
      - ORM table names
    """
    signals: dict[str, float] = {}

    # File name is a strong signal.
    _add_auto_signals(signals, auto_tokenize(f.stem, eff), 6.0)

    if tree is not None:
        function_count = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                _add_auto_signals(signals, auto_tokenize(node.name, eff), 3.0)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if function_count < 300:
                    _add_auto_signals(signals, auto_tokenize(node.name, eff), 1.0)
                    function_count += 1

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    _add_auto_signals(
                        signals,
                        auto_tokenize(alias.name.replace(".", "_"), eff),
                        4.0,
                    )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    _add_auto_signals(
                        signals,
                        auto_tokenize(node.module.replace(".", "_"), eff),
                        4.0,
                    )

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        _add_auto_signals(
                            signals,
                            auto_tokenize(str(node.value.value), eff),
                            8.0,
                        )

    if text:
        for m in AUTO_ROUTE_PREFIX_RE.finditer(text):
            _add_auto_signals(signals, auto_tokenize(m.group(1), eff), 5.0)

        for m in AUTO_ROUTE_DECOR_RE.finditer(text):
            _add_auto_signals(signals, auto_tokenize(m.group(1), eff), 5.0)

    return signals


def ensure_required_ignore_dirs(eff: dict) -> None:
    """
    Make sure editor/worktree/cache directories are always ignored,
    even if YAML config overrides ignore_dirs.
    """
    required_ignore = {
        ".git",
        ".kilo",
        "worktrees",
        ".hypothesis",
        ".repo",
        ".vscode",
        ".idea",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "htmlcov",
        ".next",
        ".expo",
        ".turbo",
        "dist",
        "build",
        "coverage",
        "test-results",
        "playwright-report",
        "playwright-out",
        ".web-build-test",
        "static-tmp",
        "tmp",
        "uploads",
        "artifacts",
    }

    current = {
        str(x).lower()
        for x in eff.get("ignore_dirs", set())
    }

    eff["ignore_dirs"] = current | required_ignore

def learn_domain_model(
    repo: Path,
    eff: dict,
    reg: FeatureRegistry,
) -> AutoDomainModel:
    """
    Learn domain profiles from the repository itself.

    No hardcoded domain dictionary is used.

    Domains are learned from:
      1. Existing domain sub-folders.
      2. FeatureRegistry domains.
      3. Explicit YAML domains.
      4. Repeated flat-file naming patterns.
    """
    model = AutoDomainModel()

    backend = repo / "backend"
    if not backend.exists():
        return model

    placement_cfg = eff.get("placement", {})

    layers = set(
        placement_cfg.get(
            "layers",
            {"services", "models", "providers", "events", "jobs", "controllers"},
        )
    )

    surfaces = {
        str(x).lower()
        for x in eff.get("surface_names", DEFAULT_SURFACE_NAMES)
    }

    model.surfaces = surfaces

    known_domains = set(reg.domains)
    known_domains |= set(eff.get("domains", {}).keys())

    stop_tokens = _auto_stop_tokens(eff)

    # Learn existing domain folders.
    for layer in layers:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            entries = list(layer_dir.iterdir())
        except OSError:
            continue

        for p in entries:
            if not p.is_dir():
                continue

            name = p.name.lower()

            if name in eff.get("ignore_dirs", set()):
                continue

            if name in surfaces:
                continue

            if name in stop_tokens:
                continue

            known_domains.add(name)

    model.domains |= known_domains

    flat_entries: list[tuple[str, str, set[str], dict[str, float]]] = []

    # Scan backend files.
    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        if f.name == "__init__.py":
            continue

        try:
            parts = [p.lower() for p in f.relative_to(backend).parts]
        except ValueError:
            continue

        if not parts:
            continue

        layer = parts[0]

        if layer not in layers:
            continue

        if any(x in eff.get("graph_exempt_layers", set()) for x in parts):
            continue

        text = read_text(f)
        if not text:
            continue

        try:
            tree = ast.parse(text)
        except Exception:
            tree = None

        signals = extract_auto_signals(f, backend, text, tree, eff)

        current_folder = parts[1] if len(parts) > 2 else None
        rp = rel(f, repo)

        # If already inside a domain folder, strengthen that domain's profile.
        if (
            current_folder
            and current_folder not in surfaces
            and current_folder not in stop_tokens
        ):
            profile = model.profiles.setdefault(current_folder, {})

            for token, weight in signals.items():
                profile[token] = profile.get(token, 0.0) + float(weight)

            # Folder name is authoritative.
            profile[current_folder] = profile.get(current_folder, 0.0) + 12.0

            model.domains.add(current_folder)

        else:
            stem_tokens = auto_tokenize(f.stem, eff)
            flat_entries.append((rp, layer, stem_tokens, signals))

            for token in stem_tokens:
                model.token_files.setdefault(token, set()).add(rp)

    # Detect new candidate domains from repeated flat-file tokens.
    min_candidate_files = int(placement_cfg.get("min_candidate_files", 2))

    for token, paths in model.token_files.items():
        if len(paths) < min_candidate_files:
            continue

        if token in model.domains:
            continue

        model.candidate_domains.add(token)
        model.domains.add(token)

        profile = model.profiles.setdefault(token, {})
        profile[token] = profile.get(token, 0.0) + 10.0

        # Build candidate profile from files that contain the token.
        for rp, layer, stem_tokens, signals in flat_entries:
            if token in stem_tokens or token in signals:
                for t, w in signals.items():
                    profile[t] = profile.get(t, 0.0) + float(w) * 0.35

    return model


def infer_auto_domain(
    signals: dict[str, float],
    model: AutoDomainModel,
    eff: dict,
) -> tuple[str | None, float, list[str], float]:
    """
    Infer the best domain for a file using learned domain profiles.

    Returns:
      domain, confidence, reasons, score
    """
    scores: dict[str, float] = {}
    reasons: dict[str, list[str]] = {}

    for domain, profile in model.profiles.items():
        score = 0.0
        matched: list[str] = []

        for token, weight in signals.items():
            if token in profile:
                score += float(weight) * (float(profile[token]) ** 0.5)

                if len(matched) < 12:
                    matched.append(token)

        if score > 0:
            scores[domain] = score
            reasons[domain] = matched

    if not scores:
        return None, 0.0, [], 0.0

    best = max(scores.items(), key=lambda kv: kv[1])[0]
    best_score = scores[best]

    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0

    min_score = float(eff.get("placement", {}).get("min_score", 6.0))

    if best_score < min_score:
        return None, 0.0, [], best_score

    confidence = best_score / (best_score + second_score + 1.0)

    reason_tokens = sorted(set(reasons.get(best, [])))[:6]

    return best, round(confidence, 3), reason_tokens, round(best_score, 3)


def detect_surface_from_name(stem: str, eff: dict) -> str | None:
    low = str(stem).lower()

    for surface in sorted(eff.get("surface_names", DEFAULT_SURFACE_NAMES)):
        surface = str(surface).lower()

        if low == surface or low.startswith(f"{surface}_"):
            return surface

    return None


def analyze_domain_placement(
    repo: Path,
    eff: dict,
    reg: FeatureRegistry,
    model: AutoDomainModel,
) -> list[dict]:
    """
    Produce file-by-file domain placement recommendations.
    """
    placements: list[dict] = []

    backend = repo / "backend"
    if not backend.exists():
        return placements

    placement_cfg = eff.get("placement", {})

    if not placement_cfg.get("enabled", True):
        return placements

    layers = set(
        placement_cfg.get(
            "layers",
            {"services", "models", "providers", "events", "jobs", "controllers"},
        )
    )

    router_layer = placement_cfg.get("router_layer", "routers")

    root_conf = float(placement_cfg.get("min_confidence_root_move", 0.45))
    wrong_conf = float(placement_cfg.get("min_confidence_wrong_folder", 0.65))
    surface_conf = float(placement_cfg.get("min_confidence_surface_to_domain", 0.60))

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        if f.name == "__init__.py":
            continue

        try:
            parts = [p.lower() for p in f.relative_to(backend).parts]
        except ValueError:
            continue

        if not parts:
            continue

        layer = parts[0]

        if layer not in layers and layer != router_layer:
            continue

        if any(x in eff.get("graph_exempt_layers", set()) for x in parts):
            continue

        text = read_text(f)
        if not text:
            continue

        try:
            tree = ast.parse(text)
        except Exception:
            tree = None

        signals = extract_auto_signals(f, backend, text, tree, eff)

        domain, confidence, reasons, score = infer_auto_domain(
            signals,
            model,
            eff,
        )

        current_folder = parts[1] if len(parts) > 2 else None
        rp = rel(f, repo)

        # ---------------- domain layers ----------------
        if layer in layers:
            if not domain:
                continue

            target_folder = domain

            if current_folder is None:
                if confidence < root_conf:
                    continue
                kind = "root_move"

            elif current_folder == target_folder:
                continue

            elif current_folder in model.surfaces:
                if confidence < surface_conf:
                    continue
                kind = "surface_to_domain"

            elif current_folder in model.domains:
                if confidence < wrong_conf:
                    continue
                kind = "wrong_folder"

            else:
                if confidence < wrong_conf:
                    continue
                kind = "wrong_folder"

        # ---------------- router layer ----------------
        else:
            if current_folder is None:
                if domain and confidence >= root_conf:
                    target_folder = domain
                    kind = "root_move"
                else:
                    surface = detect_surface_from_name(f.stem, eff)

                    if not surface:
                        continue

                    target_folder = surface
                    kind = "root_move"

            else:
                if (
                    domain
                    and current_folder != domain
                    and current_folder in model.surfaces
                    and confidence >= surface_conf
                ):
                    target_folder = domain
                    kind = "surface_to_domain"

                elif (
                    domain
                    and current_folder != domain
                    and current_folder in model.domains
                    and confidence >= wrong_conf
                ):
                    target_folder = domain
                    kind = "wrong_folder"

                else:
                    continue

        placements.append(
            {
                "path": rp,
                "layer": layer,
                "current_folder": current_folder,
                "target_folder": target_folder,
                "target_path": f"backend/{layer}/{target_folder}/{f.name}",
                "domain": domain or target_folder,
                "confidence": confidence,
                "score": score,
                "reasons": reasons,
                "kind": kind,
            }
        )

    return placements


def check_domain_placement(
    repo: Path,
    rep: Report,
    eff: dict,
    model: AutoDomainModel,
    placements: list[dict],
) -> None:
    """
    Report auto-detected domain placement recommendations.
    """
    # Report new domain candidates.
    reported_candidates = 0

    for domain in sorted(model.candidate_domains):
        files = sorted(model.token_files.get(domain, set()))[:8]

        rep.add(
            GRN,
            "DOM6",
            "backend",
            f"backend/services|models/{domain}",
            f"new domain candidate auto-detected: '{domain}'",
            intended=(
                "create backend/<layer>/" + domain + "/ and group related files; "
                "or merge into nearest existing domain if this is not a real bounded context. "
                "Examples: " + ", ".join(files)
            ),
        )

        reported_candidates += 1

        if reported_candidates >= 50:
            break

    # Group placement recommendations.
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for p in placements:
        groups[(p["layer"], p["target_folder"], p["kind"])].append(p)

    for key in sorted(groups.keys()):
        layer, target_folder, kind = key
        items = groups[key]

        files = sorted({item["path"] for item in items})
        first_reasons = items[0].get("reasons", [])

        reason_text = ", ".join(first_reasons[:4]) if first_reasons else "name/content signals"

        if kind == "root_move":
            code = "DOM1"
            message = (
                f"{len(files)} file(s) detected as domain '{target_folder}' "
                f"at backend/{layer}/ root"
            )

        elif kind == "wrong_folder":
            code = "DOM2"
            message = (
                f"{len(files)} file(s) detected as domain '{target_folder}' "
                f"but placed in wrong backend/{layer}/ sub-folder(s)"
            )

        else:
            code = "DOM3"
            message = (
                f"{len(files)} file(s) detected as domain '{target_folder}' "
                f"but grouped by surface/mixed folder in backend/{layer}/"
            )

        intended = (
            f"mkdir -p backend/{layer}/{target_folder}; move: "
            + ", ".join(files[:12])
        )

        if len(files) > 12:
            intended += f" +{len(files) - 12} more"

        intended += f" (detected from {reason_text})"

        rep.add(
            YEL,
            code,
            layer,
            f"backend/{layer}/",
            message,
            intended=intended,
        )


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
    "F8": "non-document artifact at documents/ root (docs are allowed; documents/ is the doc home)",
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

# ============================================================================
# ACTIVE CONFIGURATION GLOBALS
# Used to avoid passing eff/reg into every legacy helper.
# ============================================================================

_ACTIVE_EFF: dict | None = None
_ACTIVE_REG: FeatureRegistry | None = None


# ============================================================================
# v3.4 SELF-CONTAINED ENHANCEMENTS
# No YAML required.
# These checks make the auditor stronger without manual configuration.
# ============================================================================

RULE_MEANING.update({
    "SEC2": "possible hardcoded secret/token literal in source",
    "SEC3": "dangerous dynamic execution / deserialization / shell usage",
    "SEC4": "insecure runtime setting (debug/cors wildcard with credentials)",
    "PERF1": "blocking call inside async function",
    "PERF2": "possible DB query inside loop (N+1 risk)",
    "QUAL1": "weak exception handling (bare except / swallowed exception)",
    "QUAL2": "TODO/FIXME technical debt marker",
    "QUAL3": "oversized file or function (scaling/maintainability risk)",
    "QUAL4": "print/debug output in application code",
    "DB1": "ORM model missing __table_args__ schema declaration",
    "DB2": "multiple Alembic heads detected (migration graph fractured)",
    "CFG5": "generated governance artifacts not gitignored",
    "FE6": "frontend console/debugger statement left in source",
})

HOTLIST_RULES.update({
    "SEC2",
    "SEC3",
    "SEC4",
    "PERF1",
    "PERF2",
    "QUAL1",
    "QUAL2",
    "QUAL3",
    "QUAL4",
    "DB1",
    "DB2",
    "CFG5",
    "FE6",
})

# --- secret literals ---------------------------------------------------------
ENH_SECRET_LITERAL_RES = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk_live_[0-9A-Za-z]{24,}"),
    re.compile(r"sk_test_[0-9A-Za-z]{24,}"),
    re.compile(r"ghp_[0-9A-Za-z]{36,}"),
    re.compile(r"github_pat_[0-9A-Za-z_]{22,}"),
    re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

ENH_SECRET_ASSIGN_RE = re.compile(
    r"(?i)\b(api[_-]?key|apikey|secret|secret[_-]?key|token|auth[_-]?token|access[_-]?token|password|passwd|pwd)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"
)

ENH_SECRET_IGNORE_LINE_RE = re.compile(
    r"(?i)os\.environ|getenv|settings\.|config\.|example|placeholder|<[^>]+>|\$\{|process\.env|\bimport\b|\bfrom\b|\bdef\b|\bclass\b|BaseSettings|Field\(|get_secret|secret_manager|vault"
)

# --- dangerous calls ---------------------------------------------------------
ENH_DANGEROUS_CALLS = {
    "eval",
    "exec",
    "pickle.load",
    "pickle.loads",
    "cPickle.load",
    "cPickle.loads",
    "marshal.load",
    "marshal.loads",
    "yaml.load",
    "yaml.unsafe_load",
    "os.system",
}

ENH_SUBPROCESS_CALLS = {
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
}

# --- async blocking calls ----------------------------------------------------
ENH_BLOCKING_CALLS = {
    "time.sleep",
    "requests.get",
    "requests.post",
    "requests.put",
    "requests.delete",
    "requests.patch",
    "requests.head",
    "requests.options",
    "urllib.request.urlopen",
    "socket.recv",
    "socket.send",
    "socket.connect",
}

# --- query-in-loop -----------------------------------------------------------
ENH_QUERY_ATTRS = {
    "query",
    "execute",
    "scalar",
    "scalars",
}

# --- quality / debt ----------------------------------------------------------
ENH_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
ENH_FRONTEND_DEBUG_RE = re.compile(r"\bconsole\.(log|debug|info|warn|error)\b|\bdebugger\b")
ENH_DEBUG_TRUE_RE = re.compile(r"\bdebug\s*=\s*True\b", re.I)
ENH_CORS_WILDCARD_RE = re.compile(r"allow_origins\s*=\s*\[\s*['\"]\*['\"]\s*\]")
ENH_CORS_CREDS_RE = re.compile(r"allow_credentials\s*=\s*True\b")

ENH_FILE_LINE_LIMIT = 1200
ENH_FUNC_LINE_LIMIT = 120


def _enh_call_full_name(func: ast.AST) -> str:
    """
    Return a dotted best-effort name for a Call.func node.
    Examples:
      requests.get -> 'requests.get'
      time.sleep -> 'time.sleep'
      print -> 'print'
    """
    parts: list[str] = []
    cur = func

    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value

    if isinstance(cur, ast.Name):
        parts.append(cur.id)

    return ".".join(reversed(parts))


def _enh_call_has_attr(func: ast.AST, attrs: set[str]) -> bool:
    """
    Detect whether a call chain contains one of the given attribute names.
    Useful for chained calls like:
      session.query(...).filter(...).all()
    """
    cur = func
    depth = 0

    while cur is not None and depth < 32:
        if isinstance(cur, ast.Attribute):
            if cur.attr in attrs:
                return True
            cur = cur.value
        elif isinstance(cur, ast.Call):
            cur = cur.func
        elif isinstance(cur, ast.Name):
            return cur.id in attrs
        else:
            break

        depth += 1

    return False


def _enh_backend_parts(f: Path, backend: Path) -> list[str] | None:
    try:
        return [p.lower() for p in f.relative_to(backend).parts]
    except ValueError:
        return None


def _enh_is_excluded_backend_path(parts: list[str]) -> bool:
    excluded = {
        "tests",
        "test",
        "scripts",
        "alembic",
        "data",
        "monitoring",
        "docs",
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".next",
    }
    return any(p in excluded for p in parts)


def check_enhanced_secrets_in_code(repo: Path, rep: Report, eff: dict) -> None:
    """
    SEC2:
    Detect likely hardcoded secrets/tokens inside source files.
    """
    reported = 0

    for top in ("backend", "frontend", "scripts"):
        d = repo / top
        if not d.exists():
            continue

        for f in iter_text_files(d, eff):
            if f.suffix.lower() not in eff["source_ext"]:
                continue

            t = read_text(f)
            if not t:
                continue

            hits: list[int] = []
            strong = False

            for i, line in enumerate(t.splitlines(), 1):
                if ENH_SECRET_IGNORE_LINE_RE.search(line):
                    continue

                matched_known = False
                for rx in ENH_SECRET_LITERAL_RES:
                    if rx.search(line):
                        hits.append(i)
                        strong = True
                        matched_known = True
                        break

                if matched_known:
                    if len(hits) >= 5:
                        break
                    continue

                low = line.lower()
                if (
                    ENH_SECRET_ASSIGN_RE.search(line)
                    and not any(
                        x in low
                        for x in (
                            "example",
                            "test",
                            "dummy",
                            "changeme",
                            "placeholder",
                            "<",
                            "${",
                            "process.env",
                            "os.environ",
                        )
                    )
                ):
                    hits.append(i)

                if len(hits) >= 5:
                    break

            if hits:
                sev = RED if strong else YEL
                rep.add(
                    sev,
                    "SEC2",
                    domain_of(rel(f, repo)),
                    rel(f, repo),
                    f"possible hardcoded secret/token ({len(hits)} hit(s))",
                    intended="move secrets to env/Vault/settings; keep only placeholders in examples",
                    line=hits[0],
                )
                reported += 1

                if reported >= 150:
                    return


def check_enhanced_dangerous_calls(repo: Path, rep: Report, eff: dict) -> None:
    """
    SEC3:
    Detect dangerous execution / deserialization / shell patterns.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if parts is None or _enh_is_excluded_backend_path(parts):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _enh_call_full_name(node.func)
            if not name:
                continue

            if name in ENH_SUBPROCESS_CALLS:
                shell_true = False
                for kw in node.keywords:
                    if (
                        kw.arg == "shell"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value is True
                    ):
                        shell_true = True
                        break

                if shell_true:
                    rep.add(
                        RED,
                        "SEC3",
                        "security",
                        rel(f, repo),
                        f"dangerous subprocess call with shell=True ({name})",
                        intended="use argument list without shell=True; validate all inputs",
                        line=node.lineno,
                    )
                    reported += 1

                if reported >= 200:
                    return

                continue

            if name in ENH_DANGEROUS_CALLS:
                sev = RED if name in {
                    "eval",
                    "exec",
                    "pickle.load",
                    "pickle.loads",
                    "yaml.load",
                    "yaml.unsafe_load",
                    "marshal.load",
                    "marshal.loads",
                } else YEL

                rep.add(
                    sev,
                    "SEC3",
                    "security",
                    rel(f, repo),
                    f"dangerous dynamic execution/deserialization: {name}",
                    intended="avoid eval/exec/pickle/marshal/unsafe yaml; use safe parsers and explicit logic",
                    line=node.lineno,
                )
                reported += 1

                if reported >= 200:
                    return


def check_enhanced_runtime_security_settings(repo: Path, rep: Report, eff: dict) -> None:
    """
    SEC4:
    Detect insecure runtime settings:
    - debug=True
    - CORS wildcard + credentials
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if parts is None or _enh_is_excluded_backend_path(parts):
            continue

        t = read_text(f)
        if not t:
            continue

        if ENH_CORS_WILDCARD_RE.search(t) and ENH_CORS_CREDS_RE.search(t):
            line = 1
            for i, l in enumerate(t.splitlines(), 1):
                if ENH_CORS_WILDCARD_RE.search(l):
                    line = i
                    break

            rep.add(
                RED,
                "SEC4",
                "security",
                rel(f, repo),
                "CORS wildcard origin combined with credentials",
                intended="use explicit allowed origins when allow_credentials=True",
                line=line,
            )
            reported += 1

        if ENH_DEBUG_TRUE_RE.search(t):
            line = 1
            for i, l in enumerate(t.splitlines(), 1):
                if ENH_DEBUG_TRUE_RE.search(l):
                    line = i
                    break

            rep.add(
                YEL,
                "SEC4",
                "security",
                rel(f, repo),
                "debug=True detected in backend code",
                intended="drive debug from settings/env; never hardcode True in deployable code",
                line=line,
            )
            reported += 1

        if reported >= 150:
            return


def check_enhanced_async_blocking(repo: Path, rep: Report, eff: dict) -> None:
    """
    PERF1:
    Detect blocking calls inside async functions.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if parts is None or _enh_is_excluded_backend_path(parts):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue

                name = _enh_call_full_name(child.func)
                if not name:
                    continue

                if name in ENH_BLOCKING_CALLS or name in ENH_SUBPROCESS_CALLS:
                    rep.add(
                        YEL,
                        "PERF1",
                        "backend",
                        rel(f, repo),
                        f"blocking call '{name}' inside async function '{node.name}'",
                        intended="use async client / threadpool / background job instead of blocking the event loop",
                        line=getattr(child, "lineno", node.lineno),
                    )
                    reported += 1

                    if reported >= 200:
                        return


def check_enhanced_query_in_loop(repo: Path, rep: Report, eff: dict) -> None:
    """
    PERF2:
    Detect likely DB query calls inside loops.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if parts is None or _enh_is_excluded_backend_path(parts):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                continue

            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue

                if _enh_call_has_attr(child.func, ENH_QUERY_ATTRS):
                    rep.add(
                        YEL,
                        "PERF2",
                        "backend",
                        rel(f, repo),
                        "possible DB query inside loop (N+1 risk)",
                        intended="batch the query / use joins / preload relationships instead of querying per item",
                        line=getattr(child, "lineno", node.lineno),
                    )
                    reported += 1

                    if reported >= 200:
                        return


def check_enhanced_exception_handling(repo: Path, rep: Report, eff: dict) -> None:
    """
    QUAL1:
    Detect weak exception handling:
    - bare except
    - swallowed Exception with pass
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if parts is None or _enh_is_excluded_backend_path(parts):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            if node.type is None:
                rep.add(
                    YEL,
                    "QUAL1",
                    "backend",
                    rel(f, repo),
                    "bare except: catches everything and hides failures",
                    intended="catch specific exceptions and handle/log them explicitly",
                    line=node.lineno,
                )
                reported += 1

            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                only_pass = all(isinstance(stmt, ast.Pass) for stmt in node.body)
                if only_pass:
                    rep.add(
                        YEL,
                        "QUAL1",
                        "backend",
                        rel(f, repo),
                        "swallowed exception: 'except Exception: pass'",
                        intended="log or re-raise; silent swallowing hides bugs",
                        line=node.lineno,
                    )
                    reported += 1

            if reported >= 250:
                return


def check_enhanced_todo_debt(repo: Path, rep: Report, eff: dict) -> None:
    """
    QUAL2:
    Detect TODO/FIXME/XXX/HACK markers.
    """
    reported = 0

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

            count = len(ENH_TODO_RE.findall(t))
            if count <= 0:
                continue

            rep.add(
                YEL,
                "QUAL2",
                domain_of(rel(f, repo)),
                rel(f, repo),
                f"technical debt markers present ({count} TODO/FIXME/XXX/HACK)",
                intended="convert important markers into tasks/ADRs; delete stale ones",
            )
            reported += 1

            if reported >= 200:
                return


def check_enhanced_size_complexity(repo: Path, rep: Report, eff: dict) -> None:
    """
    QUAL3:
    Detect oversized files and functions.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if parts is None or _enh_is_excluded_backend_path(parts):
            continue

        t = read_text(f)
        if not t:
            continue

        line_count = len(t.splitlines())
        if line_count > ENH_FILE_LINE_LIMIT:
            rep.add(
                YEL,
                "QUAL3",
                "backend",
                rel(f, repo),
                f"oversized file ({line_count} lines)",
                intended="split by domain/responsibility; large files become change bottlenecks",
            )
            reported += 1

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            end_lineno = getattr(node, "end_lineno", None)
            if not end_lineno:
                continue

            func_len = end_lineno - node.lineno + 1
            if func_len > ENH_FUNC_LINE_LIMIT:
                rep.add(
                    YEL,
                    "QUAL3",
                    "backend",
                    rel(f, repo),
                    f"oversized function '{node.name}' ({func_len} lines)",
                    intended="extract smaller functions / service methods; long functions hide side effects",
                    line=node.lineno,
                )
                reported += 1

                if reported >= 250:
                    return

        if reported >= 250:
            return


def check_enhanced_print_debug(repo: Path, rep: Report, eff: dict) -> None:
    """
    QUAL4:
    Detect print() in backend application code.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    app_layers = {
        "routers",
        "controllers",
        "services",
        "middleware",
        "dependencies",
        "providers",
        "utils",
        "events",
        "jobs",
    }

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        parts = _enh_backend_parts(f, backend)
        if not parts:
            continue

        layer = parts[0]
        if layer not in app_layers:
            continue

        if _enh_is_excluded_backend_path(parts):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            name = _enh_call_full_name(node.func)
            if name == "print":
                rep.add(
                    YEL,
                    "QUAL4",
                    "backend",
                    rel(f, repo),
                    "print() statement in application code",
                    intended="use structured logging instead of print()",
                    line=node.lineno,
                )
                reported += 1

                if reported >= 200:
                    return


def check_enhanced_model_schema(repo: Path, rep: Report, eff: dict) -> None:
    """
    DB1:
    Detect ORM models that define __tablename__ but not __table_args__.
    """
    backend = repo / "backend"
    models = backend / "models"
    if not models.exists():
        return

    reported = 0

    for f in iter_text_files(models, eff):
        if f.suffix.lower() != ".py":
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            has_tablename = False
            has_tableargs = False

            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "__tablename__":
                                has_tablename = True
                            if target.id == "__table_args__":
                                has_tableargs = True

                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if stmt.target.id == "__tablename__":
                        has_tablename = True
                    if stmt.target.id == "__table_args__":
                        has_tableargs = True

            if has_tablename and not has_tableargs:
                rep.add(
                    YEL,
                    "DB1",
                    "database",
                    rel(f, repo),
                    f"model '{node.name}' has __tablename__ but no __table_args__",
                    intended="declare schema ownership with __table_args__={'schema': '<domain>'}",
                    line=node.lineno,
                )
                reported += 1

                if reported >= 200:
                    return


def check_enhanced_alembic_heads(repo: Path, rep: Report, eff: dict) -> None:
    """
    DB2:
    Detect multiple Alembic heads.
    """
    versions = repo / "backend" / "alembic" / "versions"
    if not versions.exists():
        return

    rev_re = re.compile(r"^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", re.M)
    down_re = re.compile(r"^down_revision(?:\s*:\s*[^=]+)?\s*=\s*(?:['\"]([^'\"]+)['\"]|None\b)", re.M)

    revisions: set[str] = set()
    downs: set[str] = set()

    for f in versions.glob("*.py"):
        t = read_text(f)
        if not t:
            continue

        rev_match = rev_re.search(t)
        if not rev_match:
            continue

        revisions.add(rev_match.group(1))

        down_match = down_re.search(t)
        if down_match and down_match.group(1):
            downs.add(down_match.group(1))

    heads = sorted(revisions - downs)

    if len(heads) > 1:
        rep.add(
            YEL,
            "DB2",
            "database",
            "backend/alembic/versions",
            f"multiple Alembic heads detected ({len(heads)}): " + ", ".join(heads[:5]),
            intended="merge to a single head (alembic merge heads) or add a reconciling revision",
        )


def check_enhanced_gitignore_generated(repo: Path, rep: Report, eff: dict) -> None:
    """
    CFG5:
    Ensure generated audit artifacts are gitignored, without telling you to
    ignore the entire .governance/ folder if you want to commit the registry.
    """
    gi = repo / ".gitignore"
    if not gi.exists():
        return

    t = read_text(gi) or ""

    missing = [
        item
        for item in (
            "ARCHITECTURE_AUDIT_REPORT.md",
            "out/",
            ".governance/architecture_trend.json",
            ".governance/zozi_auto_policy.json",
        )
        if item not in t
    ]

    if missing:
        rep.add(
            YEL,
            "CFG5",
            "repo",
            ".gitignore",
            f"generated governance artifacts not ignored: {', '.join(missing)}",
            intended="ignore generated local outputs; keep canonical governance files if desired",
        )

def check_enhanced_frontend_debug(repo: Path, rep: Report, eff: dict) -> None:
    """
    FE6:
    Detect console/debugger statements in frontend source.
    """
    frontend = repo / "frontend"
    if not frontend.exists():
        return

    source_ext = eff.get("frontend_source_ext", DEFAULT_FRONTEND_SOURCE_EXT)
    reported = 0

    for f in iter_text_files(frontend, eff):
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

        count = len(ENH_FRONTEND_DEBUG_RE.findall(t))
        if count <= 0:
            continue

        rep.add(
            YEL,
            "FE6",
            "frontend",
            rel(f, repo),
            f"frontend debug statements present ({count} console/debugger)",
            intended="remove console/debugger before merge; use proper logging/error reporting",
        )
        reported += 1

        if reported >= 200:
            return


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
    _seen: set[tuple] = field(default_factory=set)

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
        key = (code, path, line, message)

        if key in self._seen:
            return

        self._seen.add(key)

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
# v3.5 MOVE SUGGESTION ENGINE
# Adds concrete file-by-file relocation suggestions.
# No YAML required.
# ============================================================================

RULE_MEANING.update({
    "MV1": "flat layer file should be moved into a sub-folder",
    "MV2": "mis-housed file should be relocated to canonical layer",
    "MV3": "router file should be grouped by surface",
    "I4": "file move-map summary",
})

HOTLIST_RULES.update({
    "MV1",
    "MV2",
    "MV3",
})

# Embedded domain inference dictionary.
# This is intentionally self-contained and does not require YAML.
MOVE_DOMAIN_KEYWORDS = {
    "finance": {
        "finance", "financial", "ledger", "sub_ledger", "general_ledger",
        "journal", "invoice", "invoices", "tax", "vat", "commission",
        "billing", "accounting", "refund_posting", "posting",
        "period_close", "credit_control", "ap", "ar",
        "payments", "payment",
    },
    "treasury": {
        "treasury", "cash", "bank", "payout", "payouts",
        "settlement", "settlements", "reconciliation",
        "gateway_reconciliation", "payment_engine",
        "payment_orchestrator", "auto_payout", "payout_batch",
    },
    "orders": {
        "order", "orders", "checkout", "cart", "purchase", "purchases",
        "return", "returns", "dispute", "disputes", "refund", "refunds",
        "fulfillment",
    },
    "catalog": {
        "catalog", "product", "products", "category", "categories",
        "variant", "variants", "filter", "filters", "inventory",
        "stock", "search", "moderation", "verification",
    },
    "commerce": {
        "commerce", "promotion", "promotions", "coupon", "coupons",
        "discount", "discounts", "flash_sale", "wishlist",
        "referral", "reviews", "loyalty",
    },
    "supplier": {
        "supplier", "suppliers", "vendor", "vendors",
        "onboarding", "kyc", "badge", "storefront",
    },
    "customer": {
        "customer", "customers", "address", "addresses",
        "point", "points", "profile",
    },
    "logistics": {
        "logistics", "shipping", "shipment", "shipments",
        "dispatch", "delivery", "carrier", "fleet",
        "route", "routes", "pod", "tracking", "parcel",
    },
    "communication": {
        "communication", "comms", "comm", "chat", "email",
        "sms", "push", "notification", "notifications",
        "ticket", "tickets", "message", "messages",
        "video", "meeting", "websocket", "translation",
    },
    "hr": {
        "hr", "employee", "employees", "attendance", "shift",
        "shifts", "leave", "coi", "lms", "performance",
        "succession", "travel", "hse", "dei", "offboarding",
        "roster", "handover", "payroll", "background_check",
    },
    "ai": {
        "ai", "ml", "embedding", "embeddings", "ocr", "vision",
        "bg_removal", "removal", "chatbot", "voice",
        "recommendation", "research", "automation",
        "variant_config", "image_ai",
    },
    "audit": {
        "audit", "worm", "audit_log", "audit_trail",
        "permission_audit", "communication_audit", "auditor",
    },
    "security": {
        "security", "auth", "authentication", "authorization",
        "permission", "permissions", "rbac", "iam", "mfa",
        "otp", "fraud", "risk", "blacklist", "device_binding",
        "csrf",
    },
    "core": {
        "core", "user", "users", "role", "roles", "session",
        "device", "identity", "preferences", "banner", "banners",
        "settings", "platform", "approval_matrix", "approval",
        "workflow", "bank_transaction",
    },
    "country": {
        "country", "countries", "city", "cities", "cross_border",
        "localization", "currency", "country_detection",
        "country_research",
    },
    "media": {
        "media", "asset", "assets", "image", "images",
        "upload", "uploads", "file", "files", "storage",
        "free_image",
    },
    "analytics": {
        "analytics", "snapshot", "snapshots", "kpi", "mv",
        "report", "reports", "metrics", "insights",
    },
    "configuration": {
        "configuration", "config", "feature_flag", "feature",
        "flag", "toggles", "rules",
    },
}

def _move_normalize_stem(stem: str) -> str:
    """
    Normalize a file stem for domain inference.
    Example:
      order_service -> order
      payments_controller -> payments
    """
    low = str(stem).lower()

    for suffix in FEATURE_SUFFIXES:
        if low.endswith(suffix) and len(low) > len(suffix) + 1:
            low = low[: -len(suffix)]

    low = re.sub(r"_+", "_", low).strip("_")
    return low


def _move_known_domains_from_dirs(repo: Path, eff: dict) -> set[str]:
    """
    Discover domains already present as sub-folders in domain layers.
    """
    domains: set[str] = set()
    backend = repo / "backend"

    for layer in ("services", "models", "controllers", "providers", "events", "jobs"):
        d = backend / layer
        if not d.exists():
            continue

        try:
            entries = list(d.iterdir())
        except OSError:
            continue

        for p in entries:
            if not p.is_dir():
                continue

            name = p.name.lower()
            if name in eff["ignore_dirs"]:
                continue

            if name in eff.get("surface_names", set()):
                continue

            domains.add(name)

    return domains


def _move_infer_domain(
    stem: str,
    known_domains: set[str],
    default: str = "core",
) -> tuple[str, str]:
    """
    Infer the best domain for a flat file.

    Returns:
      (domain, reason)
    """
    norm = _move_normalize_stem(stem)
    tokens = {t for t in re.split(r"[-_.]+", norm) if t}

    # 1) Exact known-domain match
    for dom in sorted(known_domains):
        if norm == dom or norm.startswith(dom + "_") or dom in tokens:
            return dom, "known-domain"

    # 2) Keyword-based inference
    scores: dict[str, int] = defaultdict(int)

    for dom, keywords in MOVE_DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw in tokens:
                scores[dom] += 2
            elif norm.startswith(kw + "_"):
                scores[dom] += 2
            elif kw in norm:
                scores[dom] += 1

    if scores:
        best = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return best, "keyword"

    # 3) Loose substring match against known domains
    for dom in sorted(known_domains):
        if len(dom) >= 4 and dom in norm:
            return dom, "substring"

    return default, "default"


def _move_infer_surface(stem: str, eff: dict, text: str = "") -> str | None:
    """
    Infer router surface from filename and route content.
    Priority:
      1. filename prefix (admin_finance.py -> admin)
      2. route prefix/path (prefix="/admin/..." -> admin)
      3. default: internal (NOT common)
    """
    low = stem.lower()
    surfaces = sorted(eff.get("surface_names", set()))

    # Filename prefix match
    for surface in surfaces:
        if low == surface or low.startswith(f"{surface}_"):
            return surface

    # Route content match
    if text:
        route_text = text.lower()
        for surface in surfaces:
            if f"/{surface}/" in route_text or f"/{surface}\"" in route_text:
                return surface

    # Default: internal (never common)
    return "internal"

def write_move_map(path: Path, moves: list[dict]) -> None:
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "count": len(moves),
        "moves": moves,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def check_move_suggestions(repo: Path, rep: Report, eff: dict, graph: ModuleGraph, reg: FeatureRegistry,) -> list[dict]:
    """
    Generate concrete file relocation suggestions.

    This is the missing “tell me which file goes into which folder” engine.
    """
    moves: list[dict] = []
    backend = repo / "backend"

    if not backend.exists():
        return moves

    known_domains: set[str] = set()
    known_domains |= set(reg.domains)
    known_domains |= _move_known_domains_from_dirs(repo, eff)
    known_domains |= set(eff.get("domains", {}).keys())
    known_domains |= set(MOVE_DOMAIN_KEYWORDS.keys())

    reported = 0
    limit = 1500

    # ------------------------------------------------------------------
    # 1. Flat domain layers: services/ and models/
    # ------------------------------------------------------------------
    for layer in ("services", "models"):
        d = backend / layer
        if not d.exists():
            continue

        try:
            direct_files = sorted([p for p in d.glob("*.py") if p.name != "__init__.py"])
        except OSError:
            direct_files = []

        for f in direct_files:
            domain, reason = _move_infer_domain(f.stem, known_domains, default="core")
            target = f"backend/{layer}/{domain}/{f.name}"

            rep.add(
                YEL,
                "MV1",
                "backend",
                rel(f, repo),
                f"flat {layer}/ file should move into {layer}/{domain}/",
                intended=f"mkdir -p backend/{layer}/{domain}; move {rel(f, repo)} -> {target} (inferred: {reason})",
            )

            moves.append(
                {
                    "from": rel(f, repo),
                    "to": target,
                    "reason": reason,
                    "kind": f"flat-{layer}",
                }
            )

            reported += 1
            if reported >= limit:
                break

        if reported >= limit:
            break

    # ------------------------------------------------------------------
    # 2. Controllers:
    #    - known mis-housed writer/controllers -> services/ or utils/
    #    - normal flat controllers -> controllers/<domain>/
    # ------------------------------------------------------------------
    if reported < limit:
        d = backend / "controllers"
        if d.exists():
            try:
                direct_files = sorted([p for p in d.glob("*.py") if p.name != "__init__.py"])
            except OSError:
                direct_files = []

            for f in direct_files:
                stem = f.stem.lower()

                # Known mis-housed controller/util logic
                if (
                    stem in eff.get("mis_housed_controllers", set())
                    or f.name in eff.get("known_writer_controllers", set())
                ):
                    if stem == "cache_utils":
                        target = "backend/utils/cache_utils.py"
                        rep.add(
                            YEL,
                            "MV2",
                            "backend",
                            rel(f, repo),
                            "mis-housed util inside controllers/ should move to utils/",
                            intended=f"move {rel(f, repo)} -> {target}",
                        )
                        moves.append(
                            {
                                "from": rel(f, repo),
                                "to": target,
                                "reason": "mis-housed-util",
                                "kind": "controllers-mis-housed",
                            }
                        )
                    else:
                        default_dom = "audit" if "audit" in stem else "core"
                        domain, reason = _move_infer_domain(
                            f.stem,
                            known_domains,
                            default=default_dom,
                        )
                        target = f"backend/services/{domain}/{f.name}"

                        rep.add(
                            RED,
                            "MV2",
                            "backend",
                            rel(f, repo),
                            "controller appears to hold service/write logic and should move to services/",
                            intended=(
                                f"move {rel(f, repo)} -> {target}; "
                                "then rename/refactor to a *_service.py if appropriate"
                            ),
                        )
                        moves.append(
                            {
                                "from": rel(f, repo),
                                "to": target,
                                "reason": reason,
                                "kind": "controllers-mis-housed-writer",
                            }
                        )

                    reported += 1
                    if reported >= limit:
                        break

                    continue

                # Normal flat controller -> domain sub-folder
                domain, reason = _move_infer_domain(f.stem, known_domains, default="core")
                target = f"backend/controllers/{domain}/{f.name}"

                rep.add(
                    YEL,
                    "MV1",
                    "backend",
                    rel(f, repo),
                    "flat controllers/ file should move into a domain sub-folder",
                    intended=f"move {rel(f, repo)} -> {target} (inferred: {reason})",
                )

                moves.append(
                    {
                        "from": rel(f, repo),
                        "to": target,
                        "reason": reason,
                        "kind": "flat-controllers",
                    }
                )

                reported += 1
                if reported >= limit:
                    break

    # ------------------------------------------------------------------
    # 3. Routers:
    #    surface grouping is correct for routers.
    # ------------------------------------------------------------------
    if reported < limit:
        d = backend / "routers"
        if d.exists():
            try:
                direct_files = sorted([p for p in d.glob("*.py") if p.name != "__init__.py"])
            except OSError:
                direct_files = []

            for f in direct_files:
                text = read_text(f) or ""
                surface = _move_infer_surface(f.stem, eff, text)
                target = f"backend/routers/{surface}/{f.name}"

                rep.add(
                    YEL,
                    "MV3",
                    "backend",
                    rel(f, repo),
                    "flat routers/ file should move into a surface sub-folder",
                    intended=f"move {rel(f, repo)} -> {target}",
                )

                moves.append(
                    {
                        "from": rel(f, repo),
                        "to": target,
                        "reason": "surface-prefix",
                        "kind": "flat-routers",
                    }
                )

                reported += 1
                if reported >= limit:
                    break

    # ------------------------------------------------------------------
    # 4. Known structural relocations
    # ------------------------------------------------------------------
    if reported < limit:
        # employee_models.py inside db/ -> models/
        emp = backend / "db" / "employee_models.py"
        if emp.exists():
            target = "backend/models/employee_models.py"
            rep.add(
                RED,
                "MV2",
                "database",
                rel(emp, repo),
                "employee_models.py must move from db/ to models/",
                intended=f"move {rel(emp, repo)} -> {target}; add __table_args__ schema",
            )
            moves.append(
                {
                    "from": rel(emp, repo),
                    "to": target,
                    "reason": "M1",
                    "kind": "known-structural",
                }
            )
            reported += 1

        # backend/api/*.py -> routers/
        api_dir = backend / "api"
        if api_dir.exists():
            try:
                api_files = sorted([p for p in api_dir.glob("*.py") if p.name != "__init__.py"])
            except OSError:
                api_files = []

            for f in api_files:
                surface = _move_infer_surface(f.stem, eff, default="public")
                target = f"backend/routers/{surface}/{f.name}"

                rep.add(
                    RED,
                    "MV2",
                    "backend",
                    rel(f, repo),
                    "router file outside routers/ should move into routers/",
                    intended=f"move {rel(f, repo)} -> {target}",
                )

                moves.append(
                    {
                        "from": rel(f, repo),
                        "to": target,
                        "reason": "R1",
                        "kind": "known-structural",
                    }
                )

                reported += 1
                if reported >= limit:
                    break

        # alembic/_*.py diagnostics -> backend/scripts/
        alembic = backend / "alembic"
        if alembic.exists():
            try:
                diag_files = sorted([p for p in alembic.glob("_*.py") if p.is_file()])
            except OSError:
                diag_files = []

            for f in diag_files:
                target = f"backend/scripts/{f.name}"
                rep.add(
                    YEL,
                    "MV2",
                    "database",
                    rel(f, repo),
                    "alembic diagnostic script should move to backend/scripts/",
                    intended=f"move {rel(f, repo)} -> {target}",
                )

                moves.append(
                    {
                        "from": rel(f, repo),
                        "to": target,
                        "reason": "A1",
                        "kind": "known-structural",
                    }
                )

                reported += 1
                if reported >= limit:
                    break

        # backend/db/migrations/ should not exist as second migrations home
        migrations = backend / "db" / "migrations"
        if migrations.exists():
            rep.add(
                RED,
                "MV2",
                "database",
                rel(migrations, repo),
                "backend/db/migrations/ is a second migrations home and should be removed/folded into Alembic",
                intended="fold required DDL into an Alembic revision, then delete backend/db/migrations/",
            )
            moves.append(
                {
                    "from": rel(migrations, repo),
                    "to": "backend/alembic/versions/",
                    "reason": "G1",
                    "kind": "known-structural-folder",
                }
            )
            reported += 1

    # ------------------------------------------------------------------
    # 5. Backend-root modules -> proper package home
    # ------------------------------------------------------------------
    if reported < limit and backend.exists():
        try:
            root_py_files = sorted([p for p in backend.glob("*.py") if p.is_file()])
        except OSError:
            root_py_files = []

        for f in root_py_files:
            if f.name in eff.get("backend_root_allow", set()):
                continue

            if is_scratch_name(f.stem, eff, broad=True):
                target = f"backend/scripts/{f.name}"
                intended = f"move {rel(f, repo)} -> {target} or delete if it is a one-off script"
                reason = "scratch"
            else:
                domain, reason = _move_infer_domain(f.stem, known_domains, default="utils")

                if domain in {"utils", "core"}:
                    target = f"backend/utils/{f.name}"
                else:
                    target = f"backend/services/{domain}/{f.name}"

                intended = f"move {rel(f, repo)} -> {target}; backend/ root must stay clean"

            rep.add(
                YEL,
                "MV2",
                "backend",
                rel(f, repo),
                "file at backend/ root should move into a proper package",
                intended=intended,
            )

            moves.append(
                {
                    "from": rel(f, repo),
                    "to": target,
                    "reason": reason,
                    "kind": "backend-root",
                }
            )

            reported += 1
            if reported >= limit:
                break

    return moves

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
        "doc_ext",
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


def _apply_advanced_policy(eff: dict, data: dict | None) -> None:
    """
    Load advanced configurable policy values that were previously hardcoded.
    """
    if not isinstance(data, dict):
        return

    pol = data.get("policy") if isinstance(data.get("policy"), dict) else data
    if not isinstance(pol, dict):
        return

    if isinstance(pol.get("feature_stop_names"), list):
        eff["feature_stop_names"] = {str(x).lower() for x in pol["feature_stop_names"]}

    if isinstance(pol.get("feature_suffixes"), list):
        eff["feature_suffixes"] = [str(x).lower() for x in pol["feature_suffixes"]]

    for scalar_key in ("repo_root_min_top_dirs", "repo_root_min_py_files"):
        if scalar_key in pol:
            try:
                eff[scalar_key] = int(pol[scalar_key])
            except Exception:
                pass

    for list_key in ("local_path_scan_tops", "media_scan_layers", "scratch_scan_roots"):
        if isinstance(pol.get(list_key), list):
            eff[list_key] = [str(x).lower() for x in pol[list_key]]

    if isinstance(pol.get("logical_domains"), dict):
        eff["logical_domains"] = pol["logical_domains"]

    if isinstance(pol.get("frontend_flat_paths"), list):
        eff["frontend_flat_paths"] = pol["frontend_flat_paths"]

    if isinstance(pol.get("codeowners"), dict):
        eff.setdefault("codeowners", {}).update(pol["codeowners"])

    if isinstance(pol.get("placement"), dict):
        eff.setdefault("placement", {}).update(pol["placement"])

    if isinstance(pol.get("domain_layer_configs"), list):
        eff["domain_layer_configs"] = pol["domain_layer_configs"]


def _apply_structure(eff: dict, struct: dict | None) -> None:
    if not isinstance(struct, dict):
        return

    eff["forbidden_root"] = _merge_dict_of_lists(
        eff["forbidden_root"],
        struct.get("forbidden_root"),
    )
    eff["forbidden_any"] = _merge_dict_of_lists(
        eff["forbidden_any"],
        struct.get("forbidden_any"),
    )

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
            eff["forbidden_controller_to_controller"] = val.strip().lower() in {
                "1",
                "true",
                "yes",
                "on",
            }
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
                "may_import": (
                    [str(x).lower() for x in may_import]
                    if isinstance(may_import, list)
                    else []
                )
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
        "allow_root_md": set(DEFAULT_ALLOW_ROOT_MD) | {
            "REPO_LAYOUT_AUDIT_REPORT.md",
            "ARCHITECTURE_AUDIT_REPORT.md",
            "DATABASE_AUDIT_REPORT.md",
            "DESIGN_AUDIT_REPORT.md",
        },
        "allow_docs_root": set(DEFAULT_ALLOW_DOCS_ROOT),
        "doc_ext": set(DEFAULT_DOC_EXT),

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

        # v3.5 configurable policy defaults
        "feature_stop_names": set(FEATURE_STOP_NAMES),
        "feature_suffixes": list(FEATURE_SUFFIXES),

        "repo_root_min_top_dirs": 8,
        "repo_root_min_py_files": 50,

        "local_path_scan_tops": ["backend", "frontend", "scripts"],
        "media_scan_layers": [
            "controllers",
            "services",
            "routers",
            "providers",
            "models",
            "utils",
        ],
        "scratch_scan_roots": ["frontend", "scripts", "."],

        "logical_domains": {
            "database": {
                "parts": ["alembic", "db", "models"],
            },
            "security": {
                "parts": ["middleware", "dependencies"],
                "basename": ["security_config.ini"],
            },
            "frontend": {
                "first": "frontend",
            },
            "docs": {
                "first": "documents",
            },
            "infra": {
                "first": ["monitoring", "nginx", "infra"],
            },
            "backend": {
                "first": "backend",
            },
        },

        "frontend_flat_paths": [
            {
                "path": "frontend/web_app/src/components",
                "threshold_key": "frontend_flat_threshold",
            },
            {
                "path": "frontend/web_app/src/lib",
                "threshold_key": "frontend_flat_threshold",
            },
            {
                "path": "frontend/web_app/src/hooks",
                "threshold_key": "frontend_flat_threshold",
            },
            {
                "path": "frontend/mobile_app/components",
                "threshold_key": "frontend_flat_threshold",
            },
            {
                "path": "frontend/mobile_app/lib",
                "threshold_key": "frontend_flat_threshold",
            },
            {
                "path": "frontend/shared/src",
                "threshold_key": "frontend_flat_threshold",
            },
        ],

        "domain_layer_configs": [
            {
                "layer": "services",
                "flat_code": "S1",
                "surface_code": "S4",
                "large_code": "S5",
            },
            {
                "layer": "models",
                "flat_code": "M2",
                "surface_code": "M3",
                "large_code": "M4",
            },
        ],

        "codeowners": {
            "default_owner": "@zozi/platform",
            "domain_owner_template": "@zozi/{domain}",
            "domain_paths": [
                "backend/services/{domain}/",
                "backend/models/{domain}/",
            ],
            "surface_paths": [
                "backend/routers/{surface}/",
                "backend/controllers/{surface}/",
            ],
        },

        "placement": {
            "enabled": True,
            "layers": [
                "services",
                "models",
                "providers",
                "events",
                "jobs",
                "controllers",
            ],
            "router_layer": "routers",
            "min_confidence_root_move": 0.45,
            "min_confidence_wrong_folder": 0.65,
            "min_confidence_surface_to_domain": 0.60,
            "min_score": 6.0,
            "min_candidate_files": 2,
            "stop_tokens": [],
        },
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

    for cfg in (struct, layer, gov):
        _apply_advanced_policy(eff, cfg)

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

    eff["forbidden_root_c"] = {
        k: _compile(v)
        for k, v in eff["forbidden_root"].items()
    }
    eff["forbidden_any_c"] = {
        k: _compile(v)
        for k, v in eff["forbidden_any"].items()
    }
    eff["secret_file_patterns_c"] = [
        re.compile(p, re.I)
        for p in eff["secret_file_patterns"]
    ]
    eff["env_secret_keys_c"] = re.compile(eff["env_secret_keys"], re.I)
    eff["local_path_c"] = re.compile(eff["local_path"])
    eff["media_disk_write_c"] = re.compile(eff["media_disk_write"])
    eff["media_disk_url_c"] = re.compile(eff["media_disk_url"])
    eff["dead_entrypoints_c"] = [
        re.compile(p)
        for p in eff["dead_entrypoints"]
    ]

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


def _domain_of_legacy(path_rel: str) -> str:
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


def domain_of_cfg(path_rel: str, eff: dict | None) -> str:
    """
    Configurable logical-domain classifier.

    The mapping is now driven by:
      governance.yaml -> policy.logical_domains
    instead of hardcoded Python logic.
    """
    parts = [p.lower() for p in Path(path_rel).parts]
    base = parts[-1] if parts else ""

    if not eff:
        return _domain_of_legacy(path_rel)

    logical_domains = eff.get("logical_domains", {})

    for domain_name, cfg in logical_domains.items():
        if not isinstance(cfg, dict):
            continue

        match_parts = {str(x).lower() for x in cfg.get("parts", [])}
        if match_parts and any(x in parts for x in match_parts):
            return domain_name

        match_basename = {str(x).lower() for x in cfg.get("basename", [])}
        if base and base in match_basename:
            return domain_name

        first = cfg.get("first")
        if isinstance(first, str) and parts and parts[0] == first.lower():
            return domain_name

        if isinstance(first, list):
            first_set = {str(x).lower() for x in first}
            if parts and parts[0] in first_set:
                return domain_name

    return "repo"


def domain_of(path_rel: str) -> str:
    """
    Backward-compatible wrapper.
    Uses active configuration when available.
    """
    return domain_of_cfg(path_rel, _ACTIVE_EFF)


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
    """
    Normalize file/folder names into feature names.

    Stop-names and suffixes are now configurable via:
      governance.yaml -> policy.feature_stop_names
      governance.yaml -> policy.feature_suffixes
    """
    if not name:
        return ""

    eff = _ACTIVE_EFF or {}

    stop_names = {
        str(x).lower()
        for x in eff.get("feature_stop_names", FEATURE_STOP_NAMES)
    }

    suffixes = [
        str(x).lower()
        for x in eff.get("feature_suffixes", FEATURE_SUFFIXES)
    ]

    low = str(name).lower()
    low = low.replace("\\", "/")
    low = re.sub(r"[\s\-.]+", "_", low)
    low = re.sub(r"_+", "_", low).strip("_")

    if not low:
        return ""

    for _ in range(3):
        changed = False
        for suffix in suffixes:
            if low.endswith(suffix) and len(low) > len(suffix) + 1:
                low = low[: -len(suffix)].rstrip("_")
                changed = True

        if not changed:
            break

    low = re.sub(r"_+", "_", low).strip("_")

    if low in stop_names:
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
        domain_discovery_layers = set(
            eff.get("placement", {}).get(
                "layers",
                {"services", "models", "providers", "events", "jobs"},
            )
        )

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
    scan_tops = eff.get("local_path_scan_tops", ["backend", "frontend", "scripts"])

    for top in scan_tops:
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
    scan_roots = [repo]

    for sub in ("backend", "frontend", "scripts"):
        d = repo / sub
        if d.exists():
            scan_roots.append(d)

    seen: set[str] = set()

    for scan_root in scan_roots:
        for d, entries in walk_dirs(scan_root, eff["ignore_dirs"]):
            for e in entries:
                if not e.is_file():
                    continue

                rp = rel(e, repo).replace("\\", "/")
                if rp in seen:
                    continue

                for rx in eff["secret_file_patterns_c"]:
                    if rx.search("/" + rp) or rx.search(rp):
                        seen.add(rp)
                        rep.add(
                            RED,
                            "F5",
                            "security",
                            rel(e, repo),
                            "secret/credential material on disk",
                            intended="remove from VCS; load via env/Vault; keep only .env.example",
                        )
                        break


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

def _code_for_root(key: str, c: Path, eff: dict) -> str:
    if key == "." and (
        c.name.startswith("backup_")
        or c.name in {"Working_API", "provider_test", "_trash", "image", "zozi-logo-app"}
        or c.suffix == ".zip"
    ):
        return "F9"
    if (
        c.name in eff.get("artifact_names", DEFAULT_ARTIFACT_NAMES)
        or c.suffix in eff.get("artifact_exts", DEFAULT_ARTIFACT_EXTS)
        or c.suffix in {".db"}
    ):
        return "F4"
    if key == "backend/alembic":
        return "A1"
    return "F4"


def _intended_for(key: str, c: Path, eff: dict) -> str:
    if c.name.startswith("backup_") or c.suffix == ".zip":
        return "remove from VCS (backups -> object storage; design -> design/)"
    if c.name in {"Working_API", "provider_test"}:
        return "move to experiments/ and gitignore outputs"
    if c.name == "_trash":
        return "delete from repo"
    if (
        c.name in eff.get("artifact_names", DEFAULT_ARTIFACT_NAMES)
        or c.suffix in eff.get("artifact_exts", DEFAULT_ARTIFACT_EXTS)
        or c.suffix in {".db", ".db-shm", ".db-wal"}
    ):
        return "delete + add to .gitignore"
    return "relocate per scope/repo_structure.yaml or delete"


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
                    code = _code_for_root(key, c, eff)
                    if code == "F9":
                        sev = RED if (
                            c.name in {"Working_API", "provider_test", "_trash"}
                            or c.name.startswith("backup_")
                            or c.suffix == ".zip"
                        ) else YEL
                    elif c.suffix in {".db"}:
                        sev = RED
                    else:
                        sev = YEL
                    rep.add(
                        sev,
                        code,
                        dom,
                        rel(c, repo),
                        f"must not sit at {key or 'repo root'} (damages structure/scale)",
                        intended=_intended_for(key, c, eff),
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
    scratch_roots = eff.get("scratch_scan_roots", ["frontend", "scripts", "."])
    roots = [repo if r == "." else repo / r for r in scratch_roots]

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
    # POLICY: documents/ IS the authoritative doc home. Prose specs (.md/.txt/...)
    # live directly at documents/ root — there is NO required scope/ sub-folder for
    # documents.  scope/ (and governance/) remain ONLY as the OPTIONAL home for the
    # machine-readable governance YAML (repo_structure.yaml / layer_rules.yaml).
    # So F8 no longer gates documents/ by an allow-list; it only catches a genuine
    # NON-DOCUMENT artifact (a .log/.db/.png/.zip/...) dropped into the doc tree.
    # Sub-folders (archive/, snap/, scope/, ...) are organizational and always allowed.
    doc_ext = eff.get("doc_ext", DEFAULT_DOC_EXT)
    allow_names = eff.get("allow_docs_root", set())
    docs = repo / "documents"

    if docs.exists():
        for c in sorted(docs.iterdir()):
            if c.is_dir():
                # sub-folders are organizational (archive/, snap/, scope/, ...);
                # documents/ is the doc home, so we never gate directories.
                continue
            if c.suffix.lower() in doc_ext or c.name in allow_names:
                # a real document at the doc home -> always allowed
                continue
            # anything else here is a non-document artifact that doesn't belong in docs
            rep.add(
                YEL,
                "F8",
                "docs",
                rel(c, repo),
                f"non-document artifact at documents/ root (documents/ is the doc home; this is not a doc)",
                intended="move this artifact out of documents/ (e.g. archive/ or delete); .md/.txt docs are fine here",
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
                intended="move to documents/ (the doc home) or experiments/ (scratch); never commit at root",
            )

        elif c.suffix == ".md" and c.name not in allow_md:
            rep.add(
                YEL,
                "F9",
                "repo",
                rel(c, repo),
                "doc at repo root outside the allow-list",
                intended="move to documents/ (the doc home) or documents/archive/",
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

    domain_layer_configs = eff.get(
        "domain_layer_configs",
        [
            {
                "layer": "services",
                "flat_code": "S1",
                "surface_code": "S4",
                "large_code": "S5",
            },
            {
                "layer": "models",
                "flat_code": "M2",
                "surface_code": "M3",
                "large_code": "M4",
            },
        ],
    )

    for cfg in domain_layer_configs:
        if not isinstance(cfg, dict):
            continue

        layer_name = cfg.get("layer")
        flat_code = cfg.get("flat_code", "S1")
        surface_code = cfg.get("surface_code", "S4")
        large_code = cfg.get("large_code", "S5")

        if not layer_name:
            continue

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
    media_scan_layers = eff.get(
        "media_scan_layers",
        ["controllers", "services", "routers", "providers", "models", "utils"],
    )

    for layer_name in media_scan_layers:
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

def check_router_outside(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    exempt = eff.get("graph_exempt_layers", DEFAULT_GRAPH_EXEMPT_LAYERS)

    allowed_top = {
        str(x).lower()
        for x in eff.get("known_layers", set())
        if str(x).lower() not in exempt
        and str(x).lower() != "routers"
    }

    if not allowed_top:
        allowed_top = {
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

        if not parts or parts[0] not in allowed_top:
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                fn = node.func
                nm = fn.id if isinstance(fn, ast.Name) else (
                    fn.attr if isinstance(fn, ast.Attribute) else None
                )

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
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue
                v = node.func.attr
                if v == "execute":
                    raw_sql = False
                    if node.args and isinstance(node.args[0], ast.Call):
                        inner = node.args[0]
                        if isinstance(inner.func, ast.Name) and inner.func.id == "text":
                            raw_sql = True
                    if raw_sql:
                        rep.add(
                            RED, "W1", "backend", r,
                            f"{layer_name}/ executes raw SQL via session.execute(text(...))",
                            intended="move raw SQL to a service or repository layer",
                            line=node.lineno,
                        )
                    else:
                        rep.add(
                            RED, "W1", "backend", r,
                            f"{layer_name}/ must not call session .execute(); move DB work into a service",
                            intended="a services/<domain>/*_service.py method",
                            line=node.lineno,
                        )
                elif v in eff["write_verbs"]:
                    if known:
                        rep.add(
                            YEL, "W2", "backend", r,
                            f"misnamed service-helper writes here (.{v}()); relocate file to services/",
                            intended="services/<domain>/",
                            line=node.lineno,
                        )
                    else:
                        rep.add(
                            RED, "W1", "backend", r,
                            f"{layer_name}/ must not call session write .{v}(); move write into a service",
                            intended="a services/<domain>/*_service.py method",
                            line=node.lineno,
                        )
                elif v in eff["read_verbs"]:
                    rep.add(
                        YEL, "Q1", "backend", r,
                        f"{layer_name}/ reads via .{v}(); delegate to a service",
                        intended="service layer",
                        line=node.lineno,
                    )


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
            # W3: importing a mis-housed controller
            if mod == "controllers" or mod.startswith("controllers."):
                is_mis_housed = leaf in mis
                if caller_layer in {"services", "models", "providers", "events", "jobs"}:
                    is_mis_housed = True
                if is_mis_housed:
                    key = ("W3", mod)
                    if key not in reported:
                        reported.add(key)
                        rep.add(
                            RED, "W3", "backend", caller_path,
                            f"imports controller '{mod}' from {caller_layer} (controller logic belongs in services/utils)",
                            intended="move the imported logic to services/<domain>/ or utils/",
                            line=line,
                        )
                    continue
            # W4: controller -> controller internals
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
                        YEL, "W4", "backend", caller_path,
                        f"controller imports another controller ('{mod}')",
                        intended="extract shared logic into a service or util; controllers stay thin",
                        line=line,
                    )
                continue
            # DG: forbidden edge
            for pref in edges.get(caller_layer, []):
                if mod == pref or mod.startswith(pref + "."):
                    key = ("DG", mod)
                    if key not in reported:
                        reported.add(key)
                        rep.add(
                            RED, "DG", "backend", caller_path,
                            f"forbidden dependency edge: {caller_layer} -> {mod}",
                            intended=f"layer contract: {caller_layer} may not depend on {pref}; route via services/",
                            line=line,
                        )
                    break
            # DG3: cross-domain ownership
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
                                    RED, "DG3", "backend", caller_path,
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

    flat_paths = []

    for item in eff.get("frontend_flat_paths", []):
        if not isinstance(item, dict):
            continue

        path_value = item.get("path")
        if not path_value:
            continue

        threshold_key = item.get("threshold_key", "frontend_flat_threshold")
        threshold_value = eff.get(threshold_key, eff["frontend_flat_threshold"])

        flat_paths.append((path_value, threshold_value))

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

    score += by.get("SEC2", 0) * 80
    score += by.get("SEC3", 0) * 70
    score += by.get("SEC4", 0) * 60
    score += by.get("PERF1", 0) * 25
    score += by.get("PERF2", 0) * 20
    score += by.get("QUAL1", 0) * 12
    score += by.get("QUAL2", 0) * 2
    score += by.get("QUAL3", 0) * 10
    score += by.get("QUAL4", 0) * 3
    score += by.get("DB1", 0) * 12
    score += by.get("DB2", 0) * 35

    score += by.get("DOM1", 0) * 15
    score += by.get("DOM2", 0) * 20
    score += by.get("DOM3", 0) * 12
    score += by.get("DOM6", 0) * 2

    score += by.get("MV1", 0) * 8
    score += by.get("MV2", 0) * 12
    score += by.get("MV3", 0) * 6

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
        "YAML policy (documents/scope/ or governance/)"
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
    """
    Dynamic intended structure.

    This is generated from:
      - configured surfaces
      - discovered domains
      - configured ownership layers

    It is no longer a hardcoded ASCII tree.
    """
    eff = _ACTIVE_EFF or {}
    reg = _ACTIVE_REG

    surfaces = sorted(
        {
            str(x).lower()
            for x in eff.get("surface_names", DEFAULT_SURFACE_NAMES)
        }
    )

    domains = sorted(
        set(getattr(reg, "domains", set())) | set(eff.get("domains", {}).keys())
    )

    if not domains:
        domains = ["<domain>"]

    surface_preview = ", ".join(surfaces[:8])
    if len(surfaces) > 8:
        surface_preview += " ..."

    domain_preview = ", ".join(domains[:14])
    if len(domains) > 14:
        domain_preview += " ..."

    lines = [
        "# INTENDED ZOZI STRUCTURE (generated from live governance config)",
        "",
        "Logical domains `database` and `security` live INSIDE backend/ by design.",
        "",
        "Sub-folder axis:",
        f"  SURFACE in routers/ and controllers/: {surface_preview}",
        f"  DOMAIN in services/ and models/:      {domain_preview}",
        "",
        "```",
        "zozi/",
        "├── backend/",
        "│   ├── routers/        (surface grouping)",
        "│   ├── controllers/    (surface or thin orchestration)",
        "│   ├── services/       (domain grouping REQUIRED)",
        "│   ├── models/         (domain grouping REQUIRED)",
        "│   ├── providers/",
        "│   ├── events/",
        "│   ├── jobs/",
        "│   ├── middleware/",
        "│   ├── dependencies/",
        "│   ├── utils/",
        "│   ├── data/",
        "│   ├── db/             (database logical domain)",
        "│   ├── alembic/        (ONLY migrations home)",
        "│   └── tests/",
        "├── frontend/",
        "│   ├── web_app/",
        "│   ├── mobile_app/",
        "│   └── shared/",
        "├── documents/",
        "│   ├── scope/          (optional machine governance YAML)",
        "│   └── archive/",
        "├── monitoring/",
        "├── nginx/",
        "├── experiments/",
        "└── design/",
        "```",
    ]

    return "\n".join(lines)


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

def _repo_root_thresholds() -> tuple[int, int]:
    """
    Repo-root heuristic thresholds.

    Configurable by environment variables:
      ZOZI_REPO_MIN_TOP_DIRS
      ZOZI_REPO_MIN_PY_FILES

    Later these can also be loaded from governance.yaml.
    """
    try:
        min_top_dirs = int(os.environ.get("ZOZI_REPO_MIN_TOP_DIRS", "8"))
    except Exception:
        min_top_dirs = 8

    try:
        min_py_files = int(os.environ.get("ZOZI_REPO_MIN_PY_FILES", "50"))
    except Exception:
        min_py_files = 50

    return min_top_dirs, min_py_files


def _repo_root_thresholds() -> tuple[int, int]:
    """
    Repo-root heuristic thresholds.

    Configurable by environment variables:
      ZOZI_REPO_MIN_TOP_DIRS
      ZOZI_REPO_MIN_PY_FILES
    """
    try:
        min_top_dirs = int(os.environ.get("ZOZI_REPO_MIN_TOP_DIRS", "8"))
    except Exception:
        min_top_dirs = 8

    try:
        min_py_files = int(os.environ.get("ZOZI_REPO_MIN_PY_FILES", "50"))
    except Exception:
        min_py_files = 50

    return min_top_dirs, min_py_files


def _looks_like_repo_root(p: Path) -> bool:
    """
    Return True only if this directory looks like the real ZOZI repository root.

    Strongest signal:
      backend/ + frontend/

    Fallback:
      backend/main.py + non-trivial backend
    """
    if not p.is_dir():
        return False

    if (p / "backend").is_dir() and (p / "frontend").is_dir():
        return True

    be = p / "backend"
    if not (be / "main.py").is_file():
        return False

    try:
        top_dirs = sum(1 for x in be.iterdir() if x.is_dir())
        py_files = sum(1 for x in be.rglob("*.py"))
    except OSError:
        return False

    min_top_dirs, min_py_files = _repo_root_thresholds()
    return top_dirs >= min_top_dirs and py_files >= min_py_files


def find_repo(explicit: str | None) -> Path:
    """
    Find the real ZOZI repository root.

    Priority:
      1. --root argument
      2. if script is inside scripts/ or script/, use its parent if valid
      3. walk upward from script location
      4. walk upward from current working directory
      5. fail loudly
    """
    candidates: list[Path] = []

    if explicit:
        explicit_path = Path(explicit).resolve()
        if _looks_like_repo_root(explicit_path):
            return explicit_path
        candidates.append(explicit_path)

    script_dir = Path(__file__).resolve().parent

    if script_dir.name.lower() in {"scripts", "script"}:
        candidates.append(script_dir.parent)

    if (
        script_dir.parent.name.lower() == "backend"
        and script_dir.name.lower() in {"scripts", "script"}
    ):
        candidates.append(script_dir.parent.parent)

    candidates.extend(
        [
            script_dir,
            script_dir.parent,
            script_dir.parent.parent,
            script_dir.parent.parent.parent,
            Path.cwd().resolve(),
        ]
    )

    seen: list[Path] = []

    for cand in candidates:
        try:
            cand = cand.resolve()
        except Exception:
            continue

        if cand in seen:
            continue

        seen.append(cand)

        if _looks_like_repo_root(cand):
            return cand

    try:
        for parent in script_dir.parents:
            parent = parent.resolve()
            if parent in seen:
                continue
            seen.append(parent)
            if _looks_like_repo_root(parent):
                return parent
    except Exception:
        pass

    try:
        cwd = Path.cwd().resolve()
        if cwd not in seen:
            seen.append(cwd)
            if _looks_like_repo_root(cwd):
                return cwd

        for parent in cwd.parents:
            parent = parent.resolve()
            if parent in seen:
                continue
            seen.append(parent)
            if _looks_like_repo_root(parent):
                return parent
    except Exception:
        pass

    if script_dir.name.lower() in {"scripts", "script"}:
        fallback = script_dir.parent.resolve()
        print(
            "[WARN] could not fully confirm repo root markers; "
            f"using script parent as repo root: {fallback}",
            file=sys.stderr,
        )
        return fallback

    print(
        "[FATAL] could not confirm the ZOZI repository root.\n"
        f"        looked in: {[str(c) for c in seen]}\n"
        "        Run from the repository root, or pass --root <repo>.",
        file=sys.stderr,
    )
    sys.exit(2)


def resolve_repo_output_path(repo: Path, value: str | None, default_name: str) -> Path:
    """
    Resolve output paths against the repository root.

    Examples:
      --out ARCHITECTURE_AUDIT_REPORT.md
        -> <repo>/ARCHITECTURE_AUDIT_REPORT.md

      --out out/report.md
        -> <repo>/out/report.md

      --out D:/reports/report.md
        -> D:/reports/report.md
    """
    if not value:
        return repo / default_name

    p = Path(value)

    if p.is_absolute():
        return p.resolve()

    return (repo / p).resolve()

# ============================================================================
# v3.3 REGISTRY EXTENSION  (append block — generated views over the existing graph)
# The "Architecture Registry" = architecture_registry.json, written from data the
# scanner already computes.  CODEOWNERS + mermaid + report are VIEWS over it.
# Folders become a projection; the registry JSON is the canonical model.
# Semantic fields (owner/intent/notes) are READ-ONLY overlays from
#   .governance/owners.json   (human/LLM owned; this code NEVER overwrites them).
# ============================================================================

def _suggest_domain(stem: str, known_domains: set[str]) -> tuple[str, float]:
    """Deterministic confidence *hint* (no ML).  Token-overlap against the set of
    domains the scanner already discovered.  Returns (best_domain, score in {0,1}).
    Used ONLY as a suggestion string; the authoritative domain is the folder name."""
    toks = {t for t in re.split(r"[-_.]+", stem.lower()) if t}
    best, score = "", 0.0
    for dom in known_domains:
        if dom and (dom in toks or dom.replace("_", "") in "".join(toks)):
            return dom, 1.0
        # partial: domain is a prefix of some token
        if any(t.startswith(dom) or dom.startswith(t) for t in toks if len(t) >= 4):
            best, score = dom, 0.5
    return best, score


def _load_semantic_overrides(repo: Path) -> dict:
    """Read optional human/LLM semantic overlay.  Never created by this code."""
    p = repo / ".governance" / "owners.json"
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _edge_legal(caller_layer: str, callee_mod: str, eff: dict, forbid_cc: bool) -> tuple[bool, str]:
    """Return (legal, reason).  Mirrors check_dependency_graph but as a pure bool."""
    for pref in eff.get("forbidden_edges", {}).get(caller_layer, []):
        if callee_mod == pref or callee_mod.startswith(pref + "."):
            return False, f"{caller_layer} may not depend on {pref}"
    if forbid_cc and caller_layer == "controllers" and callee_mod.startswith("controllers.") \
            and callee_mod != "controllers":
        return False, "controller must not import another controller's internals"
    return True, ""


def emit_registry(repo: Path, eff: dict, graph: ModuleGraph, reg, rep: Report,
                  summary: dict) -> Path:
    """Write the canonical Architecture Registry JSON from the in-memory graph."""
    sem = _load_semantic_overrides(repo)
    known_domains = set(reg.domains) | set(eff.get("domains", {}).keys())
    forbid_cc = bool(eff.get("forbidden_controller_to_controller", True))

    # --- nodes: one per module, with layer + authoritative domain + metrics ---
    parents = set()
    for m in graph.modules:
        parts = m.split(".")
        for i in range(1, len(parts)):
            parents.add(".".join(parts[:i]))

    nodes = []
    for module in sorted(graph.modules):
        layer = layer_of_module(module)
        # authoritative domain = the sub-folder under a domain layer, else _triage
        parts = module.split(".")
        folder_domain = parts[1] if (layer in eff["ownership_layers"] and len(parts) >= 3) else None
        if folder_domain:
            domain, confidence = folder_domain, 1.0
            triage_reason = ""
        else:
            domain, confidence = "_triage", 0.0
            triage_reason = ("flat file under " + layer +
                             " (not in a domain sub-package; folder is the declaration)")
        hint, hscore = _suggest_domain(module.rsplit(".", 1)[-1], known_domains)
        fin, fout = graph.fan_in.get(module, 0), graph.fan_out.get(module, 0)
        tot = fin + fout
        nodes.append({
            "module": module,
            "layer": layer,
            "domain": domain,
            "domain_confidence": confidence,
            "domain_hint": (hint if (domain == "_triage" and hscore > 0) else ""),
            "triage_reason": triage_reason,
            "fan_in": fin, "fan_out": fout,
            "instability": round(fout / tot, 4) if tot else 0.0,
            "is_entrypoint": module in parents or any(
                rx.search(module) for rx in eff.get("dead_entrypoints_c", [])),
            "is_dead": (layer in eff.get("dead_audit_layers", set())
                        and module not in parents and fin == 0
                        and not any(rx.search(module) for rx in eff.get("dead_entrypoints_c", []))),
        })

    # --- edges: one per import edge, flagged legal/illegal ---
    edges = []
    for caller in sorted(graph.edges):
        c_layer = layer_of_module(caller)
        for callee in sorted(graph.edges[caller]):
            legal, reason = _edge_legal(c_layer, callee, eff, forbid_cc)
            edges.append({"caller": caller, "callee": callee,
                          "caller_layer": c_layer, "legal": legal,
                          "illegal_reason": ("" if legal else reason)})

    # --- features: aggregated from discovery + per-feature route/table hints ---
    features = {}
    for name, layers in reg.features.items():
        flat = {k: sorted(v) for k, v in layers.items()}
        features[name] = {
            "layers": flat,
            **({k: sem[name][k] for k in ("owner", "intent", "notes")
                if isinstance(sem.get(name), dict) and k in sem[name]}),
        }

    # --- domains: discovered + preserved semantic overlay ---
    domains = {}
    for dom in sorted(known_domains):
        domains[dom] = {
            "module_count": sum(1 for n in nodes if n["domain"] == dom),
            **({k: sem[dom][k] for k in ("owner", "intent", "notes")
                if isinstance(sem.get(dom), dict) and k in sem[dom]}),
        }

    # --- illegal edges as a first-class list (the graph view highlights these) ---
    illegal = [e for e in edges if not e["legal"]]

    registry = {
        "schema_version": 1,
        "generated_at": summary.get("timestamp"),
        "repo": str(repo),
        "debt_score": summary.get("debt_score", 0),
        "counts": {"red": summary.get("red", 0), "yellow": summary.get("yellow", 0),
                   "nodes": len(nodes), "edges": len(edges), "illegal_edges": len(illegal),
                   "features": len(features), "domains": len(domains),
                   "triage_modules": sum(1 for n in nodes if n["domain"] == "_triage")},
        "domains": domains,
        "features": features,
        "illegal_edges": illegal,
        "nodes": nodes,
        "edges": edges,
    }
    out = repo / ".governance" / "architecture_registry.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    except Exception as exc:
        rep.add(YEL, "AUTO0", "repo", str(out), f"could not write registry: {exc}",
                intended="ensure .governance/ is writable")
    return out


def emit_codeowners(repo: Path, reg, rep: Report) -> Path:
    """
    CODEOWNERS is a generated view over discovered domains.

    Owner templates are configurable via:
      governance.yaml -> policy.codeowners

    Real owners are still read from:
      .governance/owners.json
    """
    eff = _ACTIVE_EFF or {}
    cfg = eff.get("codeowners", {})

    sem = _load_semantic_overrides(repo)

    default_owner = cfg.get("default_owner", "@zozi/platform")
    domain_owner_template = cfg.get("domain_owner_template", "@zozi/{domain}")

    domain_paths = cfg.get(
        "domain_paths",
        [
            "backend/services/{domain}/",
            "backend/models/{domain}/",
        ],
    )

    surface_paths = cfg.get(
        "surface_paths",
        [
            "backend/routers/{surface}/",
            "backend/controllers/{surface}/",
        ],
    )

    known_domains = sorted(set(reg.domains) | set())

    lines = [
        "# AUTO-GENERATED by system_architecture_audit.py — DO NOT HAND-EDIT.",
        "# Regenerated every audit from the Architecture Registry.",
        "# To set a real owner, add it to .governance/owners.json under the domain key.",
        '# Example: { "finance": { "owner": "@zozi/finance" } }',
        "",
    ]

    for dom in known_domains:
        owner = (sem.get(dom, {}) or {}).get("owner")

        if not owner:
            try:
                owner = domain_owner_template.format(domain=dom)
            except Exception:
                owner = default_owner

        for path_template in domain_paths:
            try:
                path = path_template.format(domain=dom)
            except Exception:
                continue

            lines.append(f"{path}   {owner}")

    for surf in sorted(eff_surface_names_safe()):
        owner = (sem.get(surf, {}) or {}).get("owner", default_owner)

        for path_template in surface_paths:
            try:
                path = path_template.format(surface=surf)
            except Exception:
                continue

            lines.append(f"{path}   {owner}")

    out = repo / "CODEOWNERS"

    try:
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        rep.add(
            YEL,
            "AUTO0",
            "repo",
            str(out),
            f"could not write CODEOWNERS: {exc}",
            intended="ensure repo root is writable",
        )

    return out

def eff_surface_names_safe() -> set:
    """
    Return configured surface names.
    No hardcoded fallback except when no active config exists.
    """
    if _ACTIVE_EFF:
        return {
            str(x).lower()
            for x in _ACTIVE_EFF.get("surface_names", DEFAULT_SURFACE_NAMES)
        }
    return set(DEFAULT_SURFACE_NAMES)


def emit_graph_mermaid(repo: Path, reg, rep: Report, graph=None) -> Path:
    """Mermaid view. Prefer the OBSERVED domain graph; when it is empty (services/ &
    models/ still flat — no <domain>/ folders yet) fall back to the OBSERVED LAYER
    graph from real imports, so the file is NEVER a useless empty stub. The layer
    graph is non-empty even pre-regrouping and shows the real (incl. illegal) wiring."""
    lines = ["%% AUTO-GENERATED dependency graph — DO NOT HAND-EDIT.", "graph LR"]
    drawn = 0
    for s, t in sorted(reg.domain_edges):          # populated after services/<domain>/ regrouping
        lines.append(f"    {s} --> {t}")
        drawn += 1
    if drawn == 0 and graph is not None:           # graceful fallback: layer graph
        lines = ["%% AUTO-GENERATED dependency graph — DO NOT HAND-EDIT.",
                 "%% NOTE: no domain sub-packages yet (services/ & models/ are flat),",
                 "%% so this is the LAYER graph. It gains domain nodes after the",
                 "%% services/<domain>/ regrouping (see S1 / M2 findings).",
                 "graph LR"]
        layer_edges: set[tuple[str, str]] = set()
        for caller, targets in graph.edges.items():
            cl = layer_of_module(caller)
            if not cl:
                continue
            for tgt in targets:
                tl = layer_of_module(tgt)
                if tl and tl != cl:
                    layer_edges.add((cl, tl))
        for s, t in sorted(layer_edges):
            lines.append(f"    {s} --> {t}")
            drawn += 1
    out = repo / ".governance" / "architecture_graph.mmd"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception as exc:
        rep.add(YEL, "AUTO0", "repo", str(out), f"could not write mermaid: {exc}",
                intended="ensure .governance/ is writable")
    return out


# ============================================================================
# v3.6 DOMAIN PLACEMENT FIX PACK
# Paste this just before:
#
#     if __name__ == "__main__":
#
# This overrides the older move/domain suggestion logic and adds:
#   1. Proper ZOZI domain keyword map
#   2. Generic-token stop list
#   3. Router surface/domain inference
#   4. Unknown-folder detection
#   5. Wrong-folder detection
#   6. AI File Placement Contract in the report
# ============================================================================

RULE_MEANING.update({
    "DOM1": "file should be moved into its detected domain folder",
    "DOM2": "file is inside the wrong domain folder",
    "DOM3": "surface folder used where domain folder is required",
    "DOM6": "new domain candidate auto-detected",
    "DOM7": "unknown or non-canonical domain folder",
    "DOM8": "correctly placed domain files",
})

HOTLIST_RULES.update({
    "DOM1",
    "DOM2",
    "DOM3",
    "DOM7",
})

# Allow generated audit reports at repo root without F9 noise.
DEFAULT_ALLOW_ROOT_MD.update({
    "DATABASE_AUDIT_REPORT.md",
    "DESIGN_AUDIT_REPORT.md",
    "ARCHITECTURE_AUDIT_REPORT.md",
    "PROJECTSCAFFOLDING.md",
    "Features_List.md",
})

DP_DOMAIN_LAYERS = [
    "services",
    "models",
    "providers",
    "events",
    "jobs",
    "controllers",
]

DP_SKIP_PARTS = {
    "tests",
    "test",
    "scripts",
    "alembic",
    "data",
    "monitoring",
    "docs",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    "static",
    "templates",
    "e2e",
    "__tests__",
}

# Canonical ZOZI bounded-context domains.
# These are defaults. Later they can be moved into governance.yaml.
DP_DOMAIN_KEYWORDS = {
    "finance": {"finance","financial","ledger","sub_ledger","general_ledger","journal","invoice","invoices","tax","vat","commission","billing","accounting","refund_posting","posting","period_close","credit_control","ap","ar","payments","payment",},
    "treasury": {"treasury","cash","bank","payout","payouts","settlement","settlements","reconciliation","gateway_reconciliation","payment_engine","payment_orchestrator","auto_payout","payout_batch",},
    "orders": {"order","orders","checkout","cart","purchase","purchases","return","returns","dispute","disputes","refund","refunds","fulfillment",},
    "catalog": {"catalog","product","products","category","categories","variant","variants","filter","filters","inventory","stock","search","moderation","verification",},
    "commerce": {"commerce","promotion","promotions","coupon","coupons","discount","discounts","flash_sale","wishlist","referral","reviews","loyalty",},
    "supplier": {"supplier","suppliers","vendor","vendors","onboarding","kyc","badge","storefront",},
    "customer": {"customer","customers","address","addresses","point","points","profile",},
    "logistics": {"logistics","shipping","shipment","shipments","dispatch","delivery","carrier","fleet","route","routes","pod","tracking","parcel",},
    "communication": {"communication","comms","comm","chat","email","sms","push","notification","notifications","ticket","tickets","message","messages","video","meeting","websocket","translation",},
    "hr": {"hr","employee","employees","attendance","shift","shifts","leave","coi","lms","performance","succession","travel","hse","dei","offboarding","roster","handover",},
    "ai": {"ai","ml","embedding","embeddings","ocr","vision","bg_removal","chatbot","voice","recommendation","research","automation","variant_config",},
    "audit": {"audit","worm","audit_log","audit_trail","permission_audit","communication_audit","auditor",},
    "security": {"security","auth","authentication","authorization","permission","permissions","rbac","iam","mfa","otp","fraud","risk","blacklist","device_binding","csrf",},
    "core": {"core","user","users","role","roles","session","device","identity","preferences","banner","banners","settings","platform","approval_matrix","approval","workflow",},
    "country": {"country","countries","city","cities","cross_border","localization","currency","country_detection","country_research",},
    "media": {"media","asset","assets","image","images","upload","uploads","file","files","storage",},
    "analytics": {"analytics","snapshot","snapshots","kpi","mv","report","reports","metrics","insights",},
    "configuration": {"configuration","config","feature_flag","feature","flag","toggles","rules",},
}

DP_ALIAS_TO_DOMAIN = {}
for _dom, _aliases in DP_DOMAIN_KEYWORDS.items():
    DP_ALIAS_TO_DOMAIN[_dom.lower()] = _dom
    for _alias in _aliases:
        DP_ALIAS_TO_DOMAIN[_alias.lower()] = _dom

# Generic tokens that must NEVER become domains.
DP_STOP_TOKENS = {"service","services","controller","controllers","router","routers","model","models","provider","providers","event","events","job","jobs",
                  "write","read","create","update","delete","get","list","add","edit","remove","process","processor","handler","manager",
                  "management","util","utils","helper","helpers","common","shared","base","main","app","module","package","lib","src",
                  "backend","frontend","zozi","tmp","temp","test","tests","testing","debug","scratch","old","new","copy","backup","final",
                  "wip","legacy","engine","scheduler","script","scripts","task","tasks","worker","workers","middleware","dependencies","tools","data",
                  "docs","monitoring","alembic","db","web","mobile","ui","component","components","page","pages","hook","hooks","store","stores","type",
                  "types","schema","schemas","mixin","mixins","init","index",
                }


def dp_normalize_domain(token: str | None) -> str | None:
    if not token:
        return None

    t = str(token).lower()
    return DP_ALIAS_TO_DOMAIN.get(t, t)


def dp_stop_tokens(eff: dict) -> set[str]:
    stop = set(DP_STOP_TOKENS)

    # Surface names are not domains.
    stop |= {
        str(x).lower()
        for x in eff.get("surface_names", set())
    }

    # Existing feature stop names from the auditor config.
    stop |= {
        str(x).lower()
        for x in eff.get("feature_stop_names", set())
    }

    return {x for x in stop if x}


def dp_tokenize(name: str, eff: dict | None = None) -> set[str]:
    """
    Tokenize file/class/import/route names into meaningful lowercase tokens.
    """
    eff = eff or {}
    stop = dp_stop_tokens(eff)

    raw = str(name)

    # CamelCase -> snake_case
    raw = re.sub(r"(?<!^)(?=[A-Z])", "_", raw)

    # Replace punctuation/path separators with underscores
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw)

    tokens = {
        t.lower()
        for t in raw.split("_")
        if t
    }

    return {
        t
        for t in tokens
        if len(t) > 2 and t not in stop
    }


def dp_route_tokens(text: str) -> set[str]:
    """
    Extract route/path tokens from FastAPI route definitions.
    """
    if not text:
        return set()

    tokens: set[str] = set()

    # APIRouter(prefix="/admin/finance")
    for m in re.finditer(
        r"APIRouter\([^)]*prefix\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        re.I,
    ):
        # Use empty eff here because route tokens should keep surface tokens
        # like admin/supplier/customer/public/webhooks.
        tokens.update(dp_tokenize(m.group(1), {}))

    # @router.get("/admin/treasury/payouts")
    for m in re.finditer(
        r"@\w+\.(?:get|post|put|patch|delete|options|head|websocket)\(\s*['\"]([^'\"]+)['\"]",
        text,
        re.I,
    ):
        tokens.update(dp_tokenize(m.group(1), {}))

    # tags=["Admin", "Treasury"]
    for m in re.finditer(r"tags\s*=\s*\[([^\]]*)\]", text, re.I):
        tag_block = m.group(1)
        for tag in re.findall(r"['\"]([^'\"]+)['\"]", tag_block):
            tokens.update(dp_tokenize(tag, {}))

    return tokens


def dp_extract_signals(f: Path, text: str, eff: dict) -> dict[str, float]:
    """
    Extract domain signals from a Python file.

    Signal weights:
      filename   = 6
      class name = 3
      imports    = 4
      table name = 8
      routes     = 4
    """
    signals: dict[str, float] = defaultdict(float)

    def add_tokens(tokens: set[str], weight: float) -> None:
        for token in tokens:
            signals[token] += weight

    # Filename is a strong signal.
    add_tokens(dp_tokenize(f.stem, eff), 6.0)

    tree = None
    try:
        tree = ast.parse(text)
    except Exception:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                add_tokens(dp_tokenize(node.name, eff), 3.0)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    add_tokens(dp_tokenize(alias.name.replace(".", "_"), eff), 4.0)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    add_tokens(dp_tokenize(node.module.replace(".", "_"), eff), 4.0)

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        add_tokens(dp_tokenize(str(node.value.value), eff), 8.0)

    # Route paths/prefixes/tags.
    add_tokens(dp_route_tokens(text), 4.0)

    return dict(signals)


def dp_build_candidate_domains(backend: Path, eff: dict) -> set[str]:
    """
    Detect possible new domains from repeated flat-file prefixes.

    Example:
      loyalty_service.py
      loyalty_engine.py
      loyalty_jobs.py

    can become candidate domain: loyalty

    But generic words like write/event/service must not become domains.
    """
    first_counts: dict[str, set[str]] = defaultdict(set)
    stop = dp_stop_tokens(eff)

    for layer in DP_DOMAIN_LAYERS:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            flat_files = sorted(layer_dir.glob("*.py"))
        except OSError:
            flat_files = []

        for f in flat_files:
            if f.name == "__init__.py":
                continue

            stem = f.stem.lower()
            first = stem.split("_", 1)[0]

            if not first:
                continue

            if first in stop:
                continue

            if first in DP_ALIAS_TO_DOMAIN:
                continue

            if len(first) < 4:
                continue

            first_counts[first].add(f.name)

    candidates = {
        token
        for token, files in first_counts.items()
        if len(files) >= 3
    }

    return candidates


def dp_known_domains(repo: Path, eff: dict, reg, candidates: set[str]) -> set[str]:
    """
    Build the set of known canonical domains.
    """
    known: set[str] = set(DP_DOMAIN_KEYWORDS.keys())

    # Domains already discovered by the main auditor.
    try:
        known |= {
            dp_normalize_domain(d)
            for d in getattr(reg, "domains", set())
        }
    except Exception:
        pass

    # Existing domain folders.
    backend = repo / "backend"
    stop = dp_stop_tokens(eff)

    for layer in DP_DOMAIN_LAYERS:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            entries = list(layer_dir.iterdir())
        except OSError:
            continue

        for p in entries:
            if not p.is_dir():
                continue

            name = p.name.lower()

            if name in DP_SKIP_PARTS:
                continue

            if name in stop:
                continue

            normalized = dp_normalize_domain(name)
            if normalized:
                known.add(normalized)

    # New candidates.
    known |= candidates

    known.discard(None)
    return known


def dp_infer_domain(
    signals: dict[str, float],
    known_domains: set[str],
    eff: dict,
) -> tuple[str | None, float, list[str]]:
    """
    Infer the best domain from signals.
    """
    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)

    for token, weight in signals.items():
        canonical = DP_ALIAS_TO_DOMAIN.get(token)

        if canonical:
            scores[canonical] += weight
            reasons[canonical].append(token)

        elif token in known_domains:
            scores[token] += float(weight) * 0.9
            reasons[token].append(token)

    if not scores:
        return None, 0.0, []

    best = max(scores.items(), key=lambda kv: kv[1])[0]
    best_score = scores[best]

    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0

    if best_score < 4.0:
        return None, 0.0, []

    confidence = best_score / (best_score + second_score + 1.0)

    reason_tokens = sorted(set(reasons.get(best, [])))[:6]

    return best, round(confidence, 3), reason_tokens


def dp_infer_router_target(
    f: Path,
    text: str,
    inferred_domain: str | None,
    confidence: float,
    eff: dict,
) -> tuple[str | None, str]:
    """
    Infer where a router file should live.

    Priority:
      1. filename surface prefix: admin_finance.py -> admin
      2. route prefix/path/tag surface: prefix="/admin/..." -> admin
      3. inferred domain if confident
      4. internal
    """
    low = f.stem.lower()

    surfaces = {
        str(x).lower()
        for x in eff.get("surface_names", set())
    }

    if not surfaces:
        surfaces = {
            "admin",
            "supplier",
            "customer",
            "public",
            "webhooks",
            "internal",
        }

    # Filename surface prefix.
    for surface in sorted(surfaces):
        if low == surface or low.startswith(f"{surface}_"):
            return surface, "surface-filename"

    # Route/path/tag surface.
    route_tokens = dp_route_tokens(text)

    for surface in sorted(surfaces):
        if surface in route_tokens:
            return surface, "surface-route"

    # Domain-based router grouping if confident.
    if inferred_domain and confidence >= 0.55 and inferred_domain not in surfaces:
        return inferred_domain, "domain"

    # Safe default.
    return "internal", "default-surface"


def dp_check_unknown_folders(
    repo: Path,
    rep: Report,
    eff: dict,
    known_domains: set[str],
) -> None:
    """
    Detect unknown/generic/non-canonical folders inside domain layers.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    surfaces = {
        str(x).lower()
        for x in eff.get("surface_names", set())
    }

    stop = dp_stop_tokens(eff)

    for layer in DP_DOMAIN_LAYERS:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            entries = sorted(layer_dir.iterdir())
        except OSError:
            continue

        for p in entries:
            if not p.is_dir():
                continue

            name = p.name.lower()

            if name in DP_SKIP_PARTS:
                continue

            if name.startswith("."):
                continue

            # Surface folders are wrong inside domain layers.
            if name in surfaces:
                rep.add(
                    YEL,
                    "DOM3",
                    layer,
                    rel(p, repo),
                    f"surface folder '{name}' inside domain layer {layer}/",
                    intended=(
                        f"surface folders belong in routers/{name}/; "
                        f"{layer}/ must be grouped by domain"
                    ),
                )
                continue

            canonical = dp_normalize_domain(name)

            # Already canonical/known.
            if canonical in known_domains or canonical in DP_DOMAIN_KEYWORDS:
                continue

            # Generic folder like write/, event/, service/, legacy/.
            if name in stop:
                rep.add(
                    YEL,
                    "DOM7",
                    layer,
                    rel(p, repo),
                    f"generic folder '{name}/' is not a valid domain folder",
                    intended=(
                        "move its files into a real domain folder "
                        "(finance/orders/catalog/supplier/logistics/communication/...)"
                    ),
                )
                continue

            # Unknown folder.
            rep.add(
                YEL,
                "DOM7",
                layer,
                rel(p, repo),
                f"unknown domain folder '{name}/'",
                intended=(
                    f"if '{name}' is a real bounded context, add it to governance taxonomy; "
                    "otherwise move its files into the nearest canonical domain"
                ),
            )


def generate_ai_placement_contract() -> str:
    """
    Generate a prescriptive placement contract for AI agents.
    This tells AI where to put NEW files before it creates them.
    """
    lines = [
        "",
        "## AI File Placement Contract",
        "",
        "**Rule for AI:** Before creating or moving any backend file, use this contract.",
        "",
        "### Layer rules",
        "",
        "| Layer | Grouping axis | Correct examples |",
        "|---|---|---|",
        "| `backend/routers/` | Surface | `routers/admin/`, `routers/supplier/`, `routers/customer/`, `routers/public/`, `routers/webhooks/`, `routers/internal/` |",
        "| `backend/controllers/` | Domain | `controllers/finance/`, `controllers/orders/`, `controllers/catalog/` |",
        "| `backend/services/` | Domain | `services/finance/`, `services/treasury/`, `services/orders/` |",
        "| `backend/models/` | Domain | `models/finance/`, `models/orders/`, `models/catalog/` |",
        "| `backend/providers/` | Domain/adapter | `providers/ai/`, `providers/media/`, `providers/logistics/` |",
        "| `backend/events/` | Domain | `events/orders/`, `events/finance/` |",
        "| `backend/jobs/` | Domain | `jobs/finance/`, `jobs/ai/` |",
        "",
        "### Forbidden generic folders",
        "",
        "Do not create folders like:",
        "",
        "```text",
        "backend/services/write/",
        "backend/services/event/",
        "backend/services/service/",
        "backend/services/legacy/",
        "backend/services/common/",
        "backend/controllers/admin/",
        "backend/models/misc/",
        "```",
        "",
        "### Domain keyword routing",
        "",
        "| Domain | Put files here | Keywords |",
        "|---|---|---|",
    ]

    for domain in sorted(DP_DOMAIN_KEYWORDS.keys()):
        aliases = sorted(DP_DOMAIN_KEYWORDS[domain])
        examples = ", ".join(aliases[:12])
        lines.append(
            f"| `{domain}` | `backend/services/{domain}/`, `backend/models/{domain}/`, `backend/controllers/{domain}/` | {examples} |"
        )

    lines.extend([
        "",
        "### If domain is unclear",
        "",
        "If a file does not clearly belong to a domain:",
        "",
        "```text",
        "backend/_triage/<file>.py",
        "```",
        "",
        "Then ask for a domain decision before merging.",
        "",
    ])

    return "\n".join(lines)


# Inject the AI placement contract into the intended-tree/report output.
try:
    _ORIGINAL_RENDER_INTENDED_TREE = render_intended_tree

    def render_intended_tree() -> str:
        return (
            _ORIGINAL_RENDER_INTENDED_TREE()
            + "\n"
            + generate_ai_placement_contract()
        )

except Exception:
    pass


# Override the older move-suggestion engine with the corrected one.
def check_move_suggestions(
    repo: Path,
    rep: Report,
    eff: dict,
    graph,
    reg,
) -> list[dict]:
    """
    Corrected file placement engine.

    It suggests:
      - flat file -> domain folder
      - wrong domain folder -> correct domain folder
      - router file -> surface/domain folder
      - generic/unknown folder -> cleanup
      - correctly placed files -> keep summary
    """
    backend = repo / "backend"
    moves: list[dict] = []

    if not backend.exists():
        return moves

    candidates = dp_build_candidate_domains(backend, eff)
    known_domains = dp_known_domains(repo, eff, reg, candidates)

    # Report limited new-domain candidates.
    for cand in sorted(candidates)[:20]:
        rep.add(
            GRN,
            "DOM6",
            "backend",
            f"backend/services|models/{cand}/",
            f"new domain candidate auto-detected: '{cand}'",
            intended=(
                "if this is a real bounded context, create the domain folder; "
                "otherwise move related files into the nearest canonical domain"
            ),
        )

    correct_count = 0
    rename_folders: set[tuple[str, str, str]] = set()

    group_files: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    group_reasons: dict[tuple[str, str, str], list[str]] = {}

    scan_layers = DP_DOMAIN_LAYERS + ["routers"]

    for layer in scan_layers:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            files = sorted(layer_dir.rglob("*.py"))
        except OSError:
            files = []

        for f in files:
            if f.name == "__init__.py":
                continue

            try:
                rel_backend_parts = [p.lower() for p in f.relative_to(backend).parts]
            except ValueError:
                continue

            if any(x in DP_SKIP_PARTS for x in rel_backend_parts):
                continue

            try:
                rel_layer_parts = f.relative_to(layer_dir).parts
            except ValueError:
                continue

            current_folder = rel_layer_parts[0].lower() if len(rel_layer_parts) > 1 else None

            text = read_text(f) or ""
            signals = dp_extract_signals(f, text, eff)

            inferred_domain, confidence, reasons = dp_infer_domain(
                signals,
                known_domains,
                eff,
            )

            if layer == "routers":
                target_folder, inference_kind = dp_infer_router_target(
                    f,
                    text,
                    inferred_domain,
                    confidence,
                    eff,
                )

                if not target_folder:
                    continue

            else:
                if not inferred_domain:
                    continue

                if current_folder is None and confidence < 0.50:
                    continue

                if current_folder is not None and confidence < 0.65:
                    continue

                target_folder = inferred_domain
                inference_kind = "domain"

            current_norm = dp_normalize_domain(current_folder) if current_folder else None

            # Correct placement.
            if current_folder and current_norm == target_folder:
                if current_folder != target_folder:
                    rename_folders.add((layer, current_folder, target_folder))

                correct_count += 1
                continue

            kind = "root_move" if current_folder is None else "wrong_folder"

            target_path = f"backend/{layer}/{target_folder}/{f.name}"
            source_path = rel(f, repo)

            moves.append(
                {
                    "from": source_path,
                    "to": target_path,
                    "reason": inference_kind,
                    "kind": kind,
                    "domain": target_folder,
                    "layer": layer,
                    "confidence": confidence,
                }
            )

            key = (layer, target_folder, kind)
            group_files[key].append(source_path)

            if key not in group_reasons:
                group_reasons[key] = reasons

    # Emit grouped findings.
    for key in sorted(group_files.keys()):
        layer, target_folder, kind = key
        files = sorted(group_files[key])
        reasons = group_reasons.get(key, [])

        reason_text = ", ".join(reasons[:3]) if reasons else "name/content signals"

        if kind == "root_move" and layer == "routers":
            code = "MV3"
            message = (
                f"{len(files)} router file(s) should be grouped under "
                f"backend/routers/{target_folder}/"
            )

        elif kind == "root_move":
            code = "MV1"
            message = (
                f"{len(files)} '{target_folder}' domain file(s) at backend/{layer}/ root "
                f"should be moved to backend/{layer}/{target_folder}/"
            )

        else:
            code = "DOM2"
            message = (
                f"{len(files)} file(s) are in the wrong backend/{layer}/ sub-folder; "
                f"detected domain: '{target_folder}'"
            )

        intended = (
            f"mkdir -p backend/{layer}/{target_folder}; move: "
            + ", ".join(files[:12])
        )

        if len(files) > 12:
            intended += f" +{len(files) - 12} more"

        intended += f" (detected from {reason_text})"

        rep.add(
            YEL,
            code,
            layer,
            f"backend/{layer}/",
            message,
            intended=intended,
        )

    # Emit folder rename suggestions.
    for layer, old_name, new_name in sorted(rename_folders):
        rep.add(
            YEL,
            "DOM7",
            layer,
            f"backend/{layer}/{old_name}/",
            f"non-canonical domain folder '{old_name}/' should be renamed to '{new_name}/'",
            intended=f"git mv backend/{layer}/{old_name} backend/{layer}/{new_name}",
        )

        moves.append(
            {
                "from": f"backend/{layer}/{old_name}/",
                "to": f"backend/{layer}/{new_name}/",
                "reason": "rename-folder",
                "kind": "folder_rename",
                "domain": new_name,
                "layer": layer,
                "confidence": 1.0,
            }
        )

    # Unknown/generic folder detection.
    dp_check_unknown_folders(repo, rep, eff, known_domains)

    # Positive placement summary.
    if correct_count > 0:
        rep.add(
            GRN,
            "DOM8",
            "backend",
            "backend/",
            f"{correct_count} scanned file(s) are already in the correct domain folder",
            intended="keep these placements; do not move them",
        )

    return moves

# ============================================================================
# v3.7 FINAL RENDER + MOVE ENGINE FIX PACK
# ============================================================================
# This block fixes:
#   1. render_markdown duplicate sections
#   2. generate_suggested_structure_mermaid argument mismatch
#   3. main() duplicate domain placement calls
#   4. old/new move engine conflict
#   5. wrong generic domain suggestions like services/engine/, services/service/
#   6. missing AI placement contract
#   7. suggested Mermaid structure not using move-map placements
# ============================================================================

try:
    DEFAULT_ALLOW_ROOT_MD.update({
        "ARCHITECTURE_AUDIT_REPORT.md",
        "DATABASE_AUDIT_REPORT.md",
        "DESIGN_AUDIT_REPORT.md",
        "REPO_LAYOUT_AUDIT_REPORT.md",
    })
except Exception:
    pass

try:
    DEFAULT_FORBIDDEN_ROOT["backend"] = [
        r".*\.(log|db|db-shm|db-wal)$",
        r"^token\.tmp$",
        r"^.*\.json$",
        r"^(?!requirements\.txt$).*\.txt$",
    ]
except Exception:
    pass

RULE_MEANING.update({
    "MV1": "flat layer file should be moved into its detected domain folder",
    "MV2": "backend-root file should be moved into a proper package",
    "MV3": "router file should be moved into surface/domain folder",
    "DOM1": "file should be moved into its detected domain folder",
    "DOM2": "file is inside the wrong domain folder",
    "DOM3": "surface folder used where domain folder is required",
    "DOM7": "unknown, generic, or non-canonical domain folder",
    "DOM8": "correctly placed domain files",
    "I4": "file move suggestions generated",
})

HOTLIST_RULES.update({
    "MV1",
    "MV2",
    "MV3",
    "DOM1",
    "DOM2",
    "DOM3",
    "DOM7",
})

PLACEMENT_DOMAIN_LAYERS = [
    "services",
    "models",
    "controllers",
    "providers",
    "events",
    "jobs",
]

PLACEMENT_SKIP_PARTS = {
    "tests",
    "test",
    "scripts",
    "alembic",
    "data",
    "monitoring",
    "docs",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    "static",
    "templates",
    "e2e",
    "__tests__",
    "tools",
    ".hypothesis",
}

# Canonical ZOZI domain map.
# This is deterministic and avoids fake domains like:
#   engine/, service/, write/, event/, legacy/, image/, ghost/, fraud/
PLACEMENT_DOMAIN_KEYWORDS = {
    "finance": {
        "finance",
        "financial",
        "ledger",
        "sub_ledger",
        "general_ledger",
        "journal",
        "invoice",
        "invoices",
        "tax",
        "vat",
        "commission",
        "billing",
        "accounting",
        "posting",
        "refund",
        "ap",
        "ar",
        "payments",
        "payment",
        "credit_control",
        "period_close",
        "erp",
    },

    "treasury": {
        "treasury",
        "treasurer",
        "cash",
        "bank",
        "payout",
        "payouts",
        "settlement",
        "settlements",
        "reconciliation",
        "gateway_reconciliation",
        "payment_engine",
        "payment_orchestrator",
        "auto_payout",
        "payout_batch",
        "cash_flow",
    },
    "orders": {
        "order",
        "orders",
        "checkout",
        "cart",
        "purchase",
        "purchases",
        "return",
        "returns",
        "dispute",
        "disputes",
        "fulfillment",
        "ghost",
    },
    "catalog": {
        "catalog",
        "product",
        "products",
        "category",
        "categories",
        "variant",
        "variants",
        "filter",
        "filters",
        "inventory",
        "stock",
        "search",
        "moderation",
        "verification",
        "advanced_filter",
        "advanced_search",
    },
    "commerce": {
        "commerce",
        "promotion",
        "promotions",
        "coupon",
        "coupons",
        "discount",
        "discounts",
        "flash_sale",
        "wishlist",
        "referral",
        "reviews",
        "loyalty",
    },
    "supplier": {
        "supplier",
        "suppliers",
        "vendor",
        "vendors",
        "onboarding",
        "kyc",
        "badge",
        "storefront",
        "supplier_badge",
        "supplier_health",
    },
    "customer": {
        "customer",
        "customers",
        "address",
        "addresses",
        "point",
        "points",
        "profile",
    },
    "logistics": {
        "logistics",
        "shipping",
        "shipment",
        "shipments",
        "dispatch",
        "delivery",
        "carrier",
        "fleet",
        "route",
        "routes",
        "pod",
        "tracking",
        "parcel",
        "geo",
        "geofence",
        "geo_fence",
        "map",
        "live_tracking",
    },
    "communication": {
        "communication",
        "comms",
        "comm",
        "chat",
        "email",
        "sms",
        "push",
        "notification",
        "notifications",
        "ticket",
        "tickets",
        "message",
        "messages",
        "video",
        "meeting",
        "websocket",
        "translation",
        "websocket_manager",
    },
    "hr": {
        "hr",
        "employee",
        "employees",
        "attendance",
        "shift",
        "shifts",
        "leave",
        "coi",
        "lms",
        "performance",
        "succession",
        "travel",
        "hse",
        "dei",
        "offboarding",
        "roster",
        "handover",
        "payroll",
        "background",
        "shift_handover",
        "shift_roster",
        "shift_scheduling",
    },
    "ai": {
        "ai",
        "ml",
        "embedding",
        "embeddings",
        "ocr",
        "vision",
        "bg",
        "bg_removal",
        "removal",
        "chatbot",
        "voice",
        "recommendation",
        "research",
        "automation",
        "variant_config",
        "text",
        "image_ai",
    },
    "audit": {
        "audit",
        "worm",
        "audit_log",
        "audit_trail",
        "permission_audit",
        "communication_audit",
        "auditor",
    },
    "security": {
        "security",
        "auth",
        "authentication",
        "authorization",
        "permission",
        "permissions",
        "rbac",
        "iam",
        "mfa",
        "otp",
        "fraud",
        "risk",
        "blacklist",
        "device_binding",
        "csrf",
        "incident",
        "watchdog",
        "biometric",
        "ghost",
        "ghost_watchdog",
    },
    "core": {
        "core",
        "user",
        "users",
        "role",
        "roles",
        "session",
        "device",
        "identity",
        "preferences",
        "banner",
        "banners",
        "settings",
        "platform",
        "approval_matrix",
        "approval",
        "workflow",
        "workflow_engine",
        "customer_health",
    },
    "country": {
        "country",
        "countries",
        "city",
        "cities",
        "cross_border",
        "cross",
        "border",
        "localization",
        "currency",
        "country_detection",
        "country_research",
        "economics",
        "cross_border_tracker",
    },
    "media": {
        "media",
        "asset",
        "assets",
        "image",
        "images",
        "upload",
        "uploads",
        "file",
        "storage",
        "free_image",
    },
    "analytics": {
        "analytics",
        "snapshot",
        "snapshots",
        "kpi",
        "mv",
        "report",
        "reports",
        "metrics",
        "insights",
        "dashboard",
    },
    "configuration": {
        "configuration",
        "config",
        "feature_flag",
        "feature",
        "flag",
        "toggles",
        "rules",
    },
}

PLACEMENT_ALIAS_TO_DOMAIN = {}
for _dom, _aliases in PLACEMENT_DOMAIN_KEYWORDS.items():
    PLACEMENT_ALIAS_TO_DOMAIN[_dom.lower()] = _dom
    for _alias in _aliases:
        PLACEMENT_ALIAS_TO_DOMAIN[_alias.lower()] = _dom

# Additional ZOZI alias corrections.
PLACEMENT_DOMAIN_KEYWORDS.setdefault("finance", set()).update({
    "commission",
    "commission_write",
    "financial_reports",
    "financial_reporting",
    "erp",
    "finance_automation",
    "finance_erp",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("communication", set()).update({
    "chat",
    "write_chat",
    "fix_chat",
    "comm",
    "comms",
    "websocket_manager",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("catalog", set()).update({
    "verification",
    "product_verification",
    "moderation",
    "product_moderation",
    "advanced_filter",
    "advanced_search",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("supplier", set()).update({
    "supplier_profile",
    "supplier_products",
    "supplier_inventory",
    "supplier_badge",
    "supplier_health",
    "supplier_onboarding",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("security", set()).update({
    "ghost",
    "ghost_watchdog",
    "watchdog",
    "fraud",
    "incident",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("logistics", set()).update({
    "geo",
    "geo_fence",
    "geofence",
    "map",
    "parcel",
    "tracking",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("hr", set()).update({
    "shift",
    "shift_handover",
    "shift_roster",
    "shift_scheduling",
    "background",
    "background_check",
})

PLACEMENT_DOMAIN_KEYWORDS.setdefault("core", set()).update({
    "workflow",
    "workflow_engine",
    "approval",
    "approval_matrix",
    "banner",
    "banners",
})

# Rebuild alias map after adding corrections.
def _rebuild_placement_aliases() -> None:
    PLACEMENT_ALIAS_TO_DOMAIN.clear()

    for domain_name, aliases in PLACEMENT_DOMAIN_KEYWORDS.items():
        PLACEMENT_ALIAS_TO_DOMAIN[domain_name.lower()] = domain_name

        for alias in aliases:
            PLACEMENT_ALIAS_TO_DOMAIN[str(alias).lower()] = domain_name

_rebuild_placement_aliases()

PLACEMENT_STOP_TOKENS = {
    "service",
    "services",
    "controller",
    "controllers",
    "router",
    "routers",
    "model",
    "models",
    "provider",
    "providers",
    "event",
    "events",
    "job",
    "jobs",
    "write",
    "read",
    "create",
    "update",
    "delete",
    "get",
    "list",
    "add",
    "edit",
    "remove",
    "process",
    "processor",
    "handler",
    "manager",
    "management",
    "util",
    "utils",
    "helper",
    "helpers",
    "common",
    "shared",
    "base",
    "main",
    "app",
    "module",
    "package",
    "lib",
    "src",
    "backend",
    "frontend",
    "zozi",
    "tmp",
    "temp",
    "test",
    "tests",
    "testing",
    "debug",
    "scratch",
    "old",
    "new",
    "copy",
    "backup",
    "final",
    "wip",
    "legacy",
    "engine",
    "scheduler",
    "script",
    "scripts",
    "task",
    "tasks",
    "worker",
    "workers",
    "middleware",
    "dependencies",
    "tools",
    "data",
    "docs",
    "monitoring",
    "alembic",
    "db",
    "web",
    "mobile",
    "ui",
    "component",
    "components",
    "page",
    "pages",
    "hook",
    "hooks",
    "store",
    "stores",
    "type",
    "types",
    "schema",
    "schemas",
    "mixin",
    "mixins",
    "init",
    "index",
    "system",
    "api",
    "async",
    "seed",
    "all",
    "database",
    "logging",
    "logger",
    "import",
    "import_module",
    "module",
    "modules",
    "datetime",
    "uuid",
    "sqlalchemy",
    "json",
    "os",
    "sys",
    "pathlib",
    "typing",
    "asyncio",
    "boto3",
    "future",
    "exceptions",
    "error",
    "errors",
    "exception",
    "advanced",
    "fix",
    "script1",
    "script2",
    "temp",
    "tmp",
    "test",
    "debug",
    "old",
    "new",
    "copy",
    "backup",
    "final",
    "wip",
    "legacy",
    "engine",
    "manager",
    "handler",
    "helper",
    "write",
    "read",
    "create",
    "update",
    "delete",
    "get",
    "list",
    "add",
    "edit",
    "remove",
    "process",
    "processor",
    "service",
    "services",
    "controller",
    "controllers",
    "router",
    "routers",
    "model",
    "models",
    "provider",
    "providers",
    "event",
    "events",
    "job",
    "jobs",
}

PLACEMENT_FOLDER_STABLE_TOKENS = {
    "products",
    "product",
    "inventory",
    "profile",
    "reviews",
    "review",
    "orders",
    "order",
    "payments",
    "payment",
    "documents",
    "document",
    "onboarding",
    "reports",
    "report",
    "analytics",
    "dashboard",
    "settings",
    "uploads",
    "upload",
    "labels",
    "label",
    "pricing",
    "insights",
}

def _pl_normalize_domain(token: str | None) -> str | None:
    if not token:
        return None

    t = str(token).lower()
    return PLACEMENT_ALIAS_TO_DOMAIN.get(t, t)


def _pl_tokenize(name: str, eff: dict, include_surfaces: bool = False) -> set[str]:
    stop = set(PLACEMENT_STOP_TOKENS)

    if not include_surfaces:
        stop |= {
            str(x).lower()
            for x in eff.get("surface_names", set())
        }

    raw = str(name)

    # CamelCase -> snake_case
    raw = re.sub(r"(?<!^)(?=[A-Z])", "_", raw)

    # Replace punctuation/path separators
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw)

    tokens = {
        t.lower()
        for t in raw.split("_")
        if t
    }

    return {
        t
        for t in tokens
        if len(t) > 2 and t not in stop
    }


def _pl_route_tokens(text: str) -> set[str]:
    """
    Extract route/path tokens from FastAPI route definitions.
    Surface tokens are intentionally kept here.
    """
    if not text:
        return set()

    tokens: set[str] = set()

    # APIRouter(prefix="/admin/finance")
    for m in re.finditer(
        r"APIRouter\([^)]*prefix\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        re.I,
    ):
        tokens.update(_pl_tokenize(m.group(1), {}, include_surfaces=True))

    # @router.get("/admin/treasury/payouts")
    for m in re.finditer(
        r"@\w+\.(?:get|post|put|patch|delete|options|head|websocket)\(\s*['\"]([^'\"]+)['\"]",
        text,
        re.I,
    ):
        tokens.update(_pl_tokenize(m.group(1), {}, include_surfaces=True))

    # tags=["Admin", "Treasury"]
    for m in re.finditer(r"tags\s*=\s*\[([^\]]*)\]", text, re.I):
        tag_block = m.group(1)
        for tag in re.findall(r"['\"]([^'\"]+)['\"]", tag_block):
            tokens.update(_pl_tokenize(tag, {}, include_surfaces=True))

    return tokens


def _pl_extract_signals(f: Path, text: str, eff: dict) -> dict[str, float]:
    signals: dict[str, float] = defaultdict(float)

    def add_tokens(tokens: set[str], weight: float) -> None:
        for token in tokens:
            signals[token] += weight

    # Filename is the strongest signal.
    add_tokens(_pl_tokenize(f.stem, eff), 6.0)

    tree = None
    try:
        tree = ast.parse(text)
    except Exception:
        tree = None

    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                add_tokens(_pl_tokenize(node.name, eff), 3.0)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    add_tokens(
                        _pl_tokenize(alias.name.replace(".", "_"), eff),
                        4.0,
                    )

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    add_tokens(
                        _pl_tokenize(node.module.replace(".", "_"), eff),
                        4.0,
                    )

            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        add_tokens(
                            _pl_tokenize(str(node.value.value), eff),
                            8.0,
                        )

    # Route tokens help routers and controllers.
    for token in _pl_route_tokens(text):
        signals[token] += 4.0

    return dict(signals)


def _pl_known_domains(repo: Path, eff: dict, reg) -> set[str]:
    known: set[str] = set(PLACEMENT_DOMAIN_KEYWORDS.keys())

    surfaces = {
        str(x).lower()
        for x in eff.get("surface_names", set())
    }

    stop = set(PLACEMENT_STOP_TOKENS) | surfaces

    # Add safe discovered domains from registry.
    try:
        for d in getattr(reg, "domains", set()):
            norm = _pl_normalize_domain(d)
            if not norm or norm in stop:
                continue

            if norm in PLACEMENT_DOMAIN_KEYWORDS or len(norm) >= 4:
                known.add(norm)
    except Exception:
        pass

    # Add existing domain folders, normalized.
    backend = repo / "backend"

    for layer in PLACEMENT_DOMAIN_LAYERS:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            entries = list(layer_dir.iterdir())
        except OSError:
            continue

        for p in entries:
            if not p.is_dir():
                continue

            name = p.name.lower()

            if name.startswith("."):
                continue

            if name in PLACEMENT_SKIP_PARTS:
                continue

            if name in stop:
                continue

            norm = _pl_normalize_domain(name)

            if not norm:
                continue

            if norm in PLACEMENT_DOMAIN_KEYWORDS or len(norm) >= 4:
                known.add(norm)

    return known


def _pl_infer_domain(
    signals: dict[str, float],
    known_domains: set[str],
    eff: dict,
) -> tuple[str | None, float, list[str]]:
    scores: dict[str, float] = defaultdict(float)
    reasons: dict[str, list[str]] = defaultdict(list)

    for token, weight in signals.items():
        canonical = PLACEMENT_ALIAS_TO_DOMAIN.get(token)

        if canonical:
            scores[canonical] += float(weight)
            reasons[canonical].append(token)

        elif token in known_domains:
            scores[token] += float(weight) * 0.8
            reasons[token].append(token)

    if not scores:
        return None, 0.0, []

    best = max(scores.items(), key=lambda kv: kv[1])[0]
    best_score = scores[best]

    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0

    if best_score < 5.0:
        return None, 0.0, []

    confidence = best_score / (best_score + second_score + 1.0)

    reason_tokens = sorted(set(reasons.get(best, [])))[:6]

    return best, round(confidence, 3), reason_tokens


def _pl_infer_router_target(
    f: Path,
    text: str,
    inferred_domain: str | None,
    confidence: float,
    eff: dict,
) -> tuple[str, str]:
    low = f.stem.lower()

    surfaces = {
        str(x).lower()
        for x in eff.get("surface_names", set())
    }

    if not surfaces:
        surfaces = {
            "admin",
            "supplier",
            "customer",
            "public",
            "webhooks",
            "internal",
        }

    # 1. Filename surface prefix: admin_finance.py -> admin
    for surface in sorted(surfaces):
        if low == surface or low.startswith(f"{surface}_"):
            return surface, "surface-filename"

    # 2. Route prefix/path/tag surface: prefix="/admin/..." -> admin
    route_tokens = _pl_route_tokens(text)

    for surface in sorted(surfaces):
        if surface in route_tokens:
            return surface, "surface-route"

    # 3. Domain grouping if confident.
    if inferred_domain and confidence >= 0.55:
        return inferred_domain, "domain"

    # 4. Safe default.
    return "internal", "default-surface"


def _pl_check_unknown_folders(
    repo: Path,
    rep: Report,
    eff: dict,
    known_domains: set[str],
) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return

    surfaces = {
        str(x).lower()
        for x in eff.get("surface_names", set())
    }

    stop = set(PLACEMENT_STOP_TOKENS) | surfaces

    for layer in PLACEMENT_DOMAIN_LAYERS:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            entries = sorted(layer_dir.iterdir())
        except OSError:
            continue

        for p in entries:
            if not p.is_dir():
                continue

            name = p.name.lower()

            if name.startswith("."):
                continue

            if name in PLACEMENT_SKIP_PARTS:
                continue

            # Surface folders are not allowed inside domain layers.
            if name in surfaces:
                rep.add(
                    YEL,
                    "DOM3",
                    layer,
                    rel(p, repo),
                    f"surface folder '{name}/' inside domain layer {layer}/",
                    intended=(
                        f"surface folders belong in routers/{name}/; "
                        f"{layer}/ must be grouped by domain"
                    ),
                )
                continue

            canonical = _pl_normalize_domain(name)

            # Alias folder: chat/ -> communication/, payments/ -> finance/
            if canonical and canonical != name and canonical in PLACEMENT_DOMAIN_KEYWORDS:
                rep.add(
                    YEL,
                    "DOM7",
                    layer,
                    rel(p, repo),
                    f"non-canonical domain folder '{name}/' should be '{canonical}/'",
                    intended=f"git mv backend/{layer}/{name} backend/{layer}/{canonical}",
                )
                continue

            # Known/canonical folder is okay.
            if canonical in known_domains or canonical in PLACEMENT_DOMAIN_KEYWORDS:
                continue

            # Generic folder like write/, event/, service/, legacy/.
            if name in stop:
                rep.add(
                    YEL,
                    "DOM7",
                    layer,
                    rel(p, repo),
                    f"generic folder '{name}/' is not a valid domain folder",
                    intended=(
                        "move its files into a real domain folder "
                        "(finance/orders/catalog/supplier/logistics/communication/...)"
                    ),
                )
                continue

            # Unknown folder.
            rep.add(
                YEL,
                "DOM7",
                layer,
                rel(p, repo),
                f"unknown domain folder '{name}/'",
                intended=(
                    f"if '{name}' is a real bounded context, add it to governance taxonomy; "
                    "otherwise move its files into the nearest canonical domain"
                ),
            )


def check_move_suggestions(
    repo: Path,
    rep: Report,
    eff: dict,
    graph,
    reg,
) -> list[dict]:
    """
    Corrected deterministic move-suggestion engine.

    It suggests:
      - flat domain-layer file -> domain folder
      - wrong domain folder -> correct domain folder
      - router file -> surface/domain folder
      - backend-root file -> proper package
      - generic/unknown folder cleanup
      - correctly placed files summary
    """
    backend = repo / "backend"
    moves: list[dict] = []

    if not backend.exists():
        return moves

    known_domains = _pl_known_domains(repo, eff, reg)

    correct_count = 0
    rename_folders: set[tuple[str, str, str]] = set()

    group_files: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    group_reasons: dict[tuple[str, str, str], list[str]] = {}

    scan_layers = PLACEMENT_DOMAIN_LAYERS + ["routers"]

    for layer in scan_layers:
        layer_dir = backend / layer
        if not layer_dir.exists():
            continue

        try:
            files = sorted(layer_dir.rglob("*.py"))
        except OSError:
            files = []

        for f in files:
            if f.name == "__init__.py":
                continue

            try:
                rel_backend_parts = [p.lower() for p in f.relative_to(backend).parts]
            except ValueError:
                continue

            if any(x in PLACEMENT_SKIP_PARTS for x in rel_backend_parts):
                continue

            try:
                rel_layer_parts = f.relative_to(layer_dir).parts
            except ValueError:
                continue

            current_folder = rel_layer_parts[0].lower() if len(rel_layer_parts) > 1 else None

            text = read_text(f) or ""
            signals = _pl_extract_signals(f, text, eff)

            inferred_domain, confidence, reasons = _pl_infer_domain(
                signals,
                known_domains,
                eff,
            )

            if layer == "routers":
                target_folder, inference_kind = _pl_infer_router_target(
                    f,
                    text,
                    inferred_domain,
                    confidence,
                    eff,
                )
            else:
                if not inferred_domain:
                    continue

                if current_folder is None and confidence < 0.50:
                    continue

                if current_folder is not None and confidence < 0.65:
                    continue

                target_folder = inferred_domain
                inference_kind = "domain"

            current_norm = _pl_normalize_domain(current_folder) if current_folder else None

            # Folder-stability override.
            #
            # Prevent false positives like:
            #   controllers/supplier/products.py  -> controllers/catalog/
            #   controllers/supplier/inventory.py -> controllers/catalog/
            #   controllers/supplier/profile.py   -> controllers/customer/
            #
            # If the file is already inside a known domain folder and the
            # filename uses a shared token, keep the current folder.
            if (
                layer != "routers"
                and current_folder
                and current_norm
                and current_norm in known_domains
                and current_norm != target_folder
            ):
                filename_tokens = _pl_tokenize(f.stem, eff)

                # If filename explicitly contains the current domain token, keep it.
                if current_norm in filename_tokens:
                    target_folder = current_norm
                    inference_kind = "folder-name-match"

                # For controllers/providers, shared tokens stay in the current domain.
                elif (
                    layer in {"controllers", "providers"}
                    and filename_tokens & PLACEMENT_FOLDER_STABLE_TOKENS
                ):
                    target_folder = current_norm
                    inference_kind = "folder-stable"

            # Correct placement.
            if current_folder and current_norm == target_folder:
                if current_folder != target_folder:
                    rename_folders.add((layer, current_folder, target_folder))

                correct_count += 1
                continue

            kind = "root_move" if current_folder is None else "wrong_folder"

            source_path = rel(f, repo)
            target_path = f"backend/{layer}/{target_folder}/{f.name}"

            moves.append(
                {
                    "from": source_path,
                    "to": target_path,
                    "reason": inference_kind,
                    "kind": kind,
                    "domain": target_folder,
                    "target_folder": target_folder,
                    "layer": layer,
                    "confidence": confidence,
                }
            )

            key = (layer, target_folder, kind)
            group_files[key].append(source_path)

            if key not in group_reasons:
                group_reasons[key] = reasons

    # Backend-root file placement.
    try:
        root_py_files = sorted([p for p in backend.glob("*.py") if p.is_file()])
    except OSError:
        root_py_files = []

    for f in root_py_files:
        if f.name in eff.get("backend_root_allow", set()):
            continue

        source_path = rel(f, repo)
        canonical = eff.get("canonical_home", {}).get(f.name)

        if canonical:
            canonical_path = Path(canonical)
            target_folder = canonical_path.parent.as_posix()
            target_path = f"backend/{canonical}"
            reasons = ["canonical_home"]
        else:
            text = read_text(f) or ""
            signals = _pl_extract_signals(f, text, eff)
            inferred_domain, confidence, reasons = _pl_infer_domain(
                signals,
                known_domains,
                eff,
            )

            if inferred_domain and confidence >= 0.50:
                if inferred_domain in {"core", "configuration"}:
                    target_folder = "utils"
                    target_path = f"backend/utils/{f.name}"
                else:
                    target_folder = f"services/{inferred_domain}"
                    target_path = f"backend/services/{inferred_domain}/{f.name}"
            else:
                target_folder = "utils"
                target_path = f"backend/utils/{f.name}"

        moves.append(
            {
                "from": source_path,
                "to": target_path,
                "reason": "backend-root",
                "kind": "backend_root",
                "domain": target_folder,
                "target_folder": target_folder,
                "layer": "backend",
                "confidence": 1.0 if canonical else 0.6,
            }
        )

        key = ("backend", target_folder, "backend_root")
        group_files[key].append(source_path)

        if key not in group_reasons:
            group_reasons[key] = reasons

    # Emit grouped findings.
    for key in sorted(group_files.keys()):
        layer, target_folder, kind = key
        files = sorted(group_files[key])
        reasons = group_reasons.get(key, [])

        reason_text = ", ".join(reasons[:3]) if reasons else "name/content signals"

        if kind == "root_move" and layer == "routers":
            code = "MV3"
            message = (
                f"{len(files)} router file(s) should be grouped under "
                f"backend/routers/{target_folder}/"
            )

        elif kind == "root_move":
            code = "MV1"
            message = (
                f"{len(files)} '{target_folder}' domain file(s) at backend/{layer}/ root "
                f"should be moved to backend/{layer}/{target_folder}/"
            )

        elif kind == "backend_root":
            code = "MV2"
            message = (
                f"{len(files)} backend-root file(s) should be moved to backend/{target_folder}/"
            )

        else:
            code = "DOM2"
            message = (
                f"{len(files)} file(s) are in the wrong backend/{layer}/ sub-folder; "
                f"detected domain: '{target_folder}'"
            )

    # Emit grouped findings.
    for key in sorted(group_files.keys()):
        layer, target_folder, kind = key
        files = sorted(group_files[key])
        reasons = group_reasons.get(key, [])

        reason_text = ", ".join(reasons[:3]) if reasons else "name/content signals"

        if kind == "root_move" and layer == "routers":
            code = "MV3"
            message = (
                f"{len(files)} router file(s) should be grouped under "
                f"backend/routers/{target_folder}/"
            )
            mkdir_path = f"backend/routers/{target_folder}"

        elif kind == "root_move":
            code = "MV1"
            message = (
                f"{len(files)} '{target_folder}' domain file(s) at backend/{layer}/ root "
                f"should be moved to backend/{layer}/{target_folder}/"
            )
            mkdir_path = f"backend/{layer}/{target_folder}"

        elif kind == "backend_root":
            code = "MV2"
            message = (
                f"{len(files)} backend-root file(s) should be moved to backend/{target_folder}/"
            )
            # FIX: target_folder already contains the full relative path (e.g. "db" or "utils")
            # Do NOT prepend "backend/" again
            mkdir_path = f"backend/{target_folder}"

        else:
            code = "DOM2"
            message = (
                f"{len(files)} file(s) are in the wrong backend/{layer}/ sub-folder; "
                f"detected domain: '{target_folder}'"
            )
            mkdir_path = f"backend/{layer}/{target_folder}"

        intended = f"mkdir -p {mkdir_path}; move: " + ", ".join(files[:12])

        if len(files) > 12:
            intended += f" +{len(files) - 12} more"

        intended += f" (detected from {reason_text})"

        rep.add(
            YEL,
            code,
            layer,
            f"backend/{layer}/" if layer != "backend" else "backend/",
            message,
            intended=intended,
        )

        if len(files) > 12:
            intended += f" +{len(files) - 12} more"

        intended += f" (detected from {reason_text})"

        rep.add(
            YEL,
            code,
            layer,
            f"backend/{layer}/" if layer != "backend" else "backend/",
            message,
            intended=intended,
        )

    # Emit folder rename suggestions.
    for layer, old_name, new_name in sorted(rename_folders):
        rep.add(
            YEL,
            "DOM7",
            layer,
            f"backend/{layer}/{old_name}/",
            f"non-canonical domain folder '{old_name}/' should be renamed to '{new_name}/'",
            intended=f"git mv backend/{layer}/{old_name} backend/{layer}/{new_name}",
        )

        moves.append(
            {
                "from": f"backend/{layer}/{old_name}/",
                "to": f"backend/{layer}/{new_name}/",
                "reason": "rename-folder",
                "kind": "folder_rename",
                "domain": new_name,
                "target_folder": new_name,
                "layer": layer,
                "confidence": 1.0,
            }
        )

    # Unknown/generic folder detection.
    _pl_check_unknown_folders(repo, rep, eff, known_domains)

    # Positive placement summary.
    if correct_count > 0:
        rep.add(
            GRN,
            "DOM8",
            "backend",
            "backend/",
            f"{correct_count} scanned file(s) are already in the correct domain folder",
            intended="keep these placements; do not move them",
        )

    return moves


def resolve_repo_output_path(repo: Path, value: str | None, default_name: str) -> Path:
    if not value:
        return repo / default_name

    p = Path(value)

    if p.is_absolute():
        return p.resolve()

    return (repo / p).resolve()


def generate_current_structure_mermaid(repo: Path, eff: dict) -> str:
    """Generate Mermaid graph of the CURRENT backend folder structure."""
    backend = repo / "backend"
    if not backend.exists():
        return ""

    ignore_dirs = {str(x).lower() for x in eff.get("ignore_dirs", set())}
    # Always filter these from structure diagrams
    extra_skip = {
        ".hypothesis", "__pycache__", ".pytest_cache", ".mypy_cache",
        ".ruff_cache", "node_modules", ".git", ".venv", "venv",
        "provider_test", ".tox", "htmlcov",
    }
    skip = ignore_dirs | extra_skip

    lines = ["```mermaid", "graph TD", '    ROOT["backend/"]']

    try:
        top_dirs = sorted(
            [
                d.name for d in backend.iterdir()
                if d.is_dir()
                and not d.name.startswith(".")
                and d.name.lower() not in skip
            ],
            key=str.lower,
        )
    except OSError:
        top_dirs = []

    for td in top_dirs:
        safe_id = td.replace("-", "_").replace(".", "_")
        lines.append(f'    {safe_id}["{td}/"]')
        lines.append(f"    ROOT --> {safe_id}")

        try:
            sub_dirs = sorted(
                [
                    sd.name for sd in (backend / td).iterdir()
                    if sd.is_dir()
                    and not sd.name.startswith(".")
                    and sd.name != "__pycache__"
                    and sd.name.lower() not in skip
                ],
                key=str.lower,
            )[:12]
        except OSError:
            sub_dirs = []

        for sd in sub_dirs:
            sd_id = f"{safe_id}_{sd.replace('-', '_').replace('.', '_')}"
            lines.append(f'    {sd_id}["{sd}/"]')
            lines.append(f"    {safe_id} --> {sd_id}")

        try:
            flat_py = sum(
                1 for f in (backend / td).iterdir()
                if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"
            )
        except OSError:
            flat_py = 0

        if flat_py > 0:
            flat_id = f"{safe_id}_flat"
            lines.append(f'    {flat_id}["{flat_py} flat .py files"]')
            lines.append(f"    {safe_id} --> {flat_id}")

    lines.append("```")
    return "\n".join(lines)


def generate_suggested_structure_mermaid(
    repo: Path,
    eff: dict,
    placements: list[dict] | None = None,
) -> str:
    """Generate Mermaid graph of the SUGGESTED backend folder structure."""
    backend = repo / "backend"
    if not backend.exists():
        return ""

    placements = placements or []

    ignore_dirs = {str(x).lower() for x in eff.get("ignore_dirs", set())}
    extra_skip = {
        ".hypothesis", "__pycache__", ".pytest_cache", ".mypy_cache",
        ".ruff_cache", "node_modules", ".git", ".venv", "venv",
        "provider_test", ".tox", "htmlcov",
    }
    skip = ignore_dirs | extra_skip

    # Collect suggested targets from placements
    suggested: dict[str, set[str]] = defaultdict(set)

    for p in placements:
        layer = p.get("layer", "")
        target = p.get("target_folder") or p.get("domain", "")

        if not layer or not target:
            to_path = str(p.get("to", "")).replace("\\", "/")
            parts = to_path.split("/")
            if len(parts) >= 3 and parts[0] == "backend":
                layer = parts[1]
                target = parts[2]

        if layer and target:
            # Filter out generic/wrong targets
            target_final = str(target).replace("\\", "/").split("/")[-1]
            bad_targets = {
                "service", "services", "controller", "controllers",
                "engine", "write", "manager", "handler", "helper",
                "common", "shared", "utils", "util", "legacy",
                "advanced", "shift", "badge", "geo", "ghost",
                "border", "ledger", "financial", "chat", "email",
                "event", "config", "commission", "employee", "incident",
                "management", "cross",
            }
            if target_final.lower() not in bad_targets:
                suggested[layer].add(target_final)

    lines = ["```mermaid", "graph TD", '    ROOT["backend/ (suggested)"]']

    domain_like_layers = {
        "services", "models", "controllers", "providers", "events", "jobs", "routers",
    }

    try:
        top_dirs = sorted(
            [
                d.name for d in backend.iterdir()
                if d.is_dir()
                and not d.name.startswith(".")
                and d.name.lower() not in skip
            ],
            key=str.lower,
        )
    except OSError:
        top_dirs = []

    # Add suggested layers that may not exist yet
    for layer in sorted(suggested.keys()):
        if layer not in top_dirs and layer in domain_like_layers:
            top_dirs.append(layer)

    top_dirs = sorted(top_dirs, key=str.lower)

    for td in top_dirs:
        safe_id = td.replace("-", "_").replace(".", "_")
        lines.append(f'    {safe_id}["{td}/"]')
        lines.append(f"    ROOT --> {safe_id}")

        if td in domain_like_layers:
            try:
                existing_subs = sorted(
                    [
                        sd.name for sd in (backend / td).iterdir()
                        if sd.is_dir()
                        and not sd.name.startswith(".")
                        and sd.name != "__pycache__"
                        and sd.name.lower() not in skip
                    ],
                    key=str.lower,
                )
            except OSError:
                existing_subs = []

            suggested_subs = sorted(suggested.get(td, set()))
            all_subs = sorted(set(existing_subs) | set(suggested_subs))

            for sub in all_subs[:20]:
                sub_id = f"{safe_id}_{sub.replace('-', '_').replace('.', '_')}"
                is_new = sub in suggested_subs and sub not in existing_subs
                label = f"{sub}/ ✨" if is_new else f"{sub}/"
                lines.append(f'    {sub_id}["{label}"]')
                lines.append(f"    {safe_id} --> {sub_id}")

            try:
                flat_py = sum(
                    1 for f in (backend / td).iterdir()
                    if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"
                )
            except OSError:
                flat_py = 0

            placed_count = sum(
                1 for p in placements
                if p.get("layer") == td and p.get("kind") in {"root_move", "wrong_folder"}
            )

            remaining = max(0, flat_py - placed_count)

            if remaining > 0:
                remaining_id = f"{safe_id}_remaining"
                lines.append(f'    {remaining_id}["{remaining} files still to place"]')
                lines.append(f"    {safe_id} --> {remaining_id}")
        else:
            try:
                sub_dirs = sorted(
                    [
                        sd.name for sd in (backend / td).iterdir()
                        if sd.is_dir()
                        and not sd.name.startswith(".")
                        and sd.name != "__pycache__"
                        and sd.name.lower() not in skip
                    ],
                    key=str.lower,
                )[:10]
            except OSError:
                sub_dirs = []

            for sd in sub_dirs:
                sd_id = f"{safe_id}_{sd.replace('-', '_').replace('.', '_')}"
                lines.append(f'    {sd_id}["{sd}/"]')
                lines.append(f"    {safe_id} --> {sd_id}")

    lines.append("```")
    return "\n".join(lines)

def _mermaid_safe_id(prefix: str, name: str, used_ids: set[str]) -> str:
    """
    Create a Mermaid-safe unique node ID.
    """
    clean = re.sub(r"[^A-Za-z0-9_]", "_", str(name))
    clean = re.sub(r"_+", "_", clean).strip("_") or "node"

    base = f"{prefix}_{clean}"
    candidate = base
    counter = 2

    while candidate in used_ids:
        candidate = f"{base}_{counter}"
        counter += 1

    used_ids.add(candidate)
    return candidate


def _mermaid_label(name: str, file_count: int = 0) -> str:
    """
    Create a Mermaid-safe quoted label.
    """
    label = str(name).replace('"', "'").replace("\n", " ")

    if file_count > 0:
        label += f" ({file_count} files)"

    return label


def generate_current_frontend_mermaid(repo: Path, eff: dict) -> str:
    """
    Generate Mermaid graph of the CURRENT frontend folder structure.

    Shows:
      - frontend workspaces
      - important sub-folders
      - deeper folders for src/app/components/lib/hooks/features
      - direct source-file counts
      - safe Mermaid IDs and labels
    """
    frontend = repo / "frontend"

    if not frontend.exists():
        return ""

    ignore_dirs = {
        str(x).lower()
        for x in eff.get("ignore_dirs", set())
    }

    extra_skip = {
        "node_modules",
        ".next",
        "dist",
        "build",
        "coverage",
        ".expo",
        ".turbo",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "test-results",
        "playwright-report",
        "playwright-out",
        "test-output",
        "web-dist",
        ".web-build-test",
        "static-tmp",
        "tmp",
        "e2e",
        ".hypothesis",
        ".kilo",
        ".kilocode",
        "worktrees",
        "__tests__",
        "tests",
        "test",
        "__mocks__",
        ".storybook",
        ".vscode",
        ".idea",
        ".git",
        ".venv",
        "venv",
    }

    skip = ignore_dirs | extra_skip

    raw_source_ext = eff.get(
        "frontend_source_ext",
        {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"},
    )

    source_ext = set()

    for ext in raw_source_ext:
        ext = str(ext).lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        source_ext.add(ext)

    def allowed_dir(p: Path) -> bool:
        return (
            p.is_dir()
            and not p.name.startswith(".")
            and p.name.lower() not in skip
        )

    def count_direct_source_files(d: Path) -> int:
        try:
            return sum(
                1
                for f in d.iterdir()
                if f.is_file() and f.suffix.lower() in source_ext
            )
        except OSError:
            return 0

    used_ids: set[str] = set()

    lines = [
        "```mermaid",
        "graph TD",
    ]

    root_id = _mermaid_safe_id("fe", "frontend", used_ids)
    lines.append(f'    {root_id}["{_mermaid_label("frontend/")}"]')

    # Optional: count flat source files directly under frontend/
    root_flat = count_direct_source_files(frontend)
    if root_flat > 0:
        root_flat_id = _mermaid_safe_id(root_id, "flat_files", used_ids)
        lines.append(
            f'    {root_flat_id}["{_mermaid_label("flat source files", root_flat)}"]'
        )
        lines.append(f"    {root_id} --> {root_flat_id}")

    try:
        top_dirs = sorted(
            [d.name for d in frontend.iterdir() if allowed_dir(d)],
            key=str.lower,
        )[:20]
    except OSError:
        top_dirs = []

    deep_folder_names = {
        "src",
        "app",
        "components",
        "lib",
        "hooks",
        "features",
        "pages",
        "screens",
        "services",
        "store",
        "stores",
        "utils",
        "types",
        "styles",
    }

    for td in top_dirs:
        td_path = frontend / td
        td_id = _mermaid_safe_id("fe", td, used_ids)

        td_file_count = count_direct_source_files(td_path)
        td_label = _mermaid_label(f"{td}/", td_file_count)

        lines.append(f'    {td_id}["{td_label}"]')
        lines.append(f"    {root_id} --> {td_id}")

        try:
            sub_dirs = sorted(
                [sd.name for sd in td_path.iterdir() if allowed_dir(sd)],
                key=str.lower,
            )[:12]
        except OSError:
            sub_dirs = []

        for sd in sub_dirs:
            sd_path = td_path / sd
            sd_id = _mermaid_safe_id(td_id, sd, used_ids)

            sd_file_count = count_direct_source_files(sd_path)
            sd_label = _mermaid_label(f"{sd}/", sd_file_count)

            lines.append(f'    {sd_id}["{sd_label}"]')
            lines.append(f"    {td_id} --> {sd_id}")

            # Show one more level for important source folders.
            if sd in deep_folder_names:
                try:
                    deep_dirs = sorted(
                        [dd.name for dd in sd_path.iterdir() if allowed_dir(dd)],
                        key=str.lower,
                    )[:10]
                except OSError:
                    deep_dirs = []

                for dd in deep_dirs:
                    dd_path = sd_path / dd
                    dd_id = _mermaid_safe_id(sd_id, dd, used_ids)

                    dd_file_count = count_direct_source_files(dd_path)
                    dd_label = _mermaid_label(f"{dd}/", dd_file_count)

                    lines.append(f'    {dd_id}["{dd_label}"]')
                    lines.append(f"    {sd_id} --> {dd_id}")

    lines.append("```")
    return "\n".join(lines)

def generate_suggested_frontend_mermaid(repo: Path, eff: dict) -> str:
    """Generate Mermaid graph of the SUGGESTED frontend folder structure."""
    frontend = repo / "frontend"
    if not frontend.exists():
        return ""

    ignore_dirs = {str(x).lower() for x in eff.get("ignore_dirs", set())}
    extra_skip = {
        "node_modules", ".next", "dist", "build", "coverage",
        ".expo", ".turbo", "__pycache__", ".pytest_cache",
        "test-results", "playwright-report", "e2e", ".hypothesis",
    }
    skip = ignore_dirs | extra_skip

    lines = ["```mermaid", "graph TD", '    ROOT["frontend/ (suggested)"]']

    # Expected workspace structure
    workspaces = sorted(eff.get("frontend_workspaces", {"web_app", "mobile_app", "shared"}))

    for ws in workspaces:
        ws_id = f"fe_{ws.replace('-', '_').replace('.', '_')}"
        ws_path = frontend / ws

        if ws_path.exists():
            lines.append(f'    {ws_id}["{ws}/ ✅"]')
        else:
            lines.append(f'    {ws_id}["{ws}/ ⚠️ missing"]')

        lines.append(f"    ROOT --> {ws_id}")

        if ws == "web_app":
            # Suggested web_app structure
            web_dirs = [
                "src/app/", "src/components/", "src/lib/",
                "src/hooks/", "src/features/", "src/styles/",
            ]
            for wd in web_dirs:
                wd_clean = wd.rstrip("/")
                wd_id = f"{ws_id}_{wd_clean.replace('/', '_').replace('-', '_')}"
                lines.append(f'    {wd_id}["{wd}"]')
                lines.append(f"    {ws_id} --> {wd_id}")

            # Show feature sub-folders if they exist
            features_path = ws_path / "src" / "features"
            if features_path.exists():
                try:
                    feature_dirs = sorted(
                        [d.name for d in features_path.iterdir() if d.is_dir() and d.name.lower() not in skip],
                        key=str.lower,
                    )[:10]
                except OSError:
                    feature_dirs = []

                features_id = f"{ws_id}_src_features"
                for fd in feature_dirs:
                    fd_id = f"{features_id}_{fd.replace('-', '_').replace('.', '_')}"
                    lines.append(f'    {fd_id}["{fd}/"]')
                    lines.append(f"    {features_id} --> {fd_id}")

        elif ws == "mobile_app":
            mobile_dirs = [
                "app/", "components/", "lib/",
                "hooks/", "features/", "assets/",
            ]
            for md in mobile_dirs:
                md_clean = md.rstrip("/")
                md_id = f"{ws_id}_{md_clean.replace('/', '_').replace('-', '_')}"
                lines.append(f'    {md_id}["{md}"]')
                lines.append(f"    {ws_id} --> {md_id}")

        elif ws == "shared":
            shared_dirs = ["src/components/", "src/lib/", "src/types/", "src/hooks/"]
            for sd in shared_dirs:
                sd_clean = sd.rstrip("/")
                sd_id = f"{ws_id}_{sd_clean.replace('/', '_').replace('-', '_')}"
                lines.append(f'    {sd_id}["{sd}"]')
                lines.append(f"    {ws_id} --> {sd_id}")

    lines.append("```")
    return "\n".join(lines)

def generate_ai_placement_contract() -> str:
    lines = [
        "## AI File Placement Contract",
        "",
        "**Rule for AI:** Before creating or moving any backend file, use this contract.",
        "",
        "### Layer rules",
        "",
        "| Layer | Grouping axis | Correct examples |",
        "|---|---|---|",
        "| `backend/routers/` | Surface | `routers/admin/`, `routers/supplier/`, `routers/customer/`, `routers/public/`, `routers/webhooks/`, `routers/internal/` |",
        "| `backend/controllers/` | Domain | `controllers/finance/`, `controllers/orders/`, `controllers/catalog/` |",
        "| `backend/services/` | Domain | `services/finance/`, `services/treasury/`, `services/orders/` |",
        "| `backend/models/` | Domain | `models/finance/`, `models/orders/`, `models/catalog/` |",
        "| `backend/providers/` | Domain/adapter | `providers/ai/`, `providers/media/`, `providers/logistics/` |",
        "| `backend/events/` | Domain | `events/orders/`, `events/finance/` |",
        "| `backend/jobs/` | Domain | `jobs/finance/`, `jobs/ai/` |",
        "",
        "### Forbidden generic folders",
        "",
        "Do not create folders like:",
        "",
        "```text",
        "backend/services/write/",
        "backend/services/event/",
        "backend/services/service/",
        "backend/services/legacy/",
        "backend/services/common/",
        "backend/services/engine/",
        "backend/controllers/admin/",
        "backend/models/misc/",
        "```",
        "",
        "### Domain keyword routing",
        "",
        "| Domain | Put files here | Keywords |",
        "|---|---|---|",
    ]

    for domain in sorted(PLACEMENT_DOMAIN_KEYWORDS.keys()):
        aliases = sorted(PLACEMENT_DOMAIN_KEYWORDS[domain])
        examples = ", ".join(aliases[:14])
        lines.append(
            f"| `{domain}` | `backend/services/{domain}/`, `backend/models/{domain}/`, `backend/controllers/{domain}/` | {examples} |"
        )

    lines.extend([
        "",
        "### If domain is unclear",
        "",
        "If a file does not clearly belong to a domain:",
        "",
        "```text",
        "backend/_triage/<file>.py",
        "```",
        "",
        "Then ask for a domain decision before merging.",
        "",
    ])

    return "\n".join(lines)


def render_markdown(
    repo: Path,
    rep: Report,
    out: Path,
    summary: dict,
    placements: list[dict] | None = None,
) -> None:
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary.get("debt_score", 0)

    eff = _ACTIVE_EFF or {}

    current_backend_mmd = generate_current_structure_mermaid(repo, eff)
    suggested_backend_mmd = generate_suggested_structure_mermaid(repo, eff, placements or [])
    current_frontend_mmd = generate_current_frontend_mermaid(repo, eff)
    suggested_frontend_mmd = generate_suggested_frontend_mermaid(repo, eff)

    L = [
        "# Architecture Governance Audit Report (GENERATED — do not hand-edit)",
        "",
        f"**Repo:** `{repo}`  ",
        f"**Result:** 🔴 {n_red} · 🟡 {n_yel} · 🟢 {n_grn}  ",
        f"**Architecture Debt Score:** `{debt}`  ",
        "**Ephemeral. Add to `.gitignore`. NOT an authoritative spec (those live in `documents/scope/`).**",
        "",
        "---",
        "",
        "## Current Backend Structure",
        "",
        current_backend_mmd,
        "",
        "## Suggested Backend Structure",
        "",
        suggested_backend_mmd,
        "",
        "---",
        "",
        "## Current Frontend Structure",
        "",
        current_frontend_mmd,
        "",
        "## Suggested Frontend Structure",
        "",
        suggested_frontend_mmd,
        "",
        "---",
        "",
        render_intended_tree(),
        "",
        generate_ai_placement_contract() if "generate_ai_placement_contract" in globals() else "",
        "",
        "## Scorecard",
        "",
        "| Code | Count | Sev | Meaning |",
        "|---|---:|---|---|",
    ]

    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        L.append(
            f"| {code} | {rep.counters[code]} | {SEV_ICON[sev]} {sev} | {RULE_MEANING.get(code, '')} |"
        )

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
        L.append(
            "- layer counts: "
            + ", ".join(f"`{k}={v}`" for k, v in sorted(summary["layer_counts"].items()))
        )

    if summary.get("top_fan_in"):
        L += ["", "### Top fan-in", "", "| Module | Fan-in |", "|---|---:|"]
        for module, count in summary["top_fan_in"]:
            L.append(f"| `{module}` | {count} |")

    if summary.get("top_fan_out"):
        L += ["", "### Top fan-out", "", "| Module | Fan-out |", "|---|---:|"]
        for module, count in summary["top_fan_out"]:
            L.append(f"| `{module}` | {count} |")

    if summary.get("frontend_metrics"):
        L += [
            "",
            "### Frontend workspace metrics",
            "",
            "| Workspace | Source files | Dirs |",
            "|---|---:|---:|",
        ]
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

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")


def collapse_noisy_findings(rep: Report) -> None:
    """
    Collapse high-volume line-level findings into one file-level finding.

    This makes the report production-readable.

    Example:
      80 individual Q1 findings in one controller
      becomes:
      1 Q1 finding saying "80 DB read(s) in this file"
    """
    noisy_codes = {
        "Q1",
        "W1",
        "W2",
        "PERF2",
        "QUAL1",
        "QUAL4",
    }

    old_findings = rep.findings
    kept: list[Finding] = []
    grouped: dict[tuple, list[Finding]] = defaultdict(list)

    for f in old_findings:
        if f.code in noisy_codes:
            key = (f.sev, f.code, f.domain, f.path, f.intended)
            grouped[key].append(f)
        else:
            kept.append(f)

    for key, items in grouped.items():
        sev, code, domain, path, intended = key

        lines = sorted({f.line for f in items if f.line is not None})
        count = len(items)

        if code == "Q1":
            base_message = (
                f"{count} DB read(s) via .query() in this file; "
                "delegate reads to a service"
            )

        elif code == "W1":
            base_message = (
                f"{count} session write(s) in this file; "
                "move writes into services/<domain>/"
            )

        elif code == "W2":
            base_message = (
                f"{count} misnamed service-helper write location(s) in this file; "
                "relocate logic to services/"
            )

        elif code == "PERF2":
            base_message = (
                f"{count} possible DB query inside loop (N+1 risk) in this file; "
                "batch queries / use joins / preload relationships"
            )

        elif code == "QUAL1":
            base_message = (
                f"{count} weak exception handling location(s) in this file; "
                "log or re-raise instead of swallowing exceptions"
            )

        elif code == "QUAL4":
            base_message = (
                f"{count} print/debug output location(s) in this file; "
                "use structured logging instead of print()"
            )

        else:
            base_message = (
                f"{count} {RULE_MEANING.get(code, code)} location(s) in this file"
            )

        if lines:
            example_lines = ", ".join(str(x) for x in lines[:10])

            if len(lines) > 10:
                example_lines += f" +{len(lines) - 10} more"

            message = f"{base_message} (lines: {example_lines})"
        else:
            message = base_message

        kept.append(
            Finding(
                sev=sev,
                code=code,
                domain=domain,
                path=path,
                message=message,
                intended=intended,
                line=None,
            )
        )

    rep.findings = kept

    rep.counters = defaultdict(int)
    for f in rep.findings:
        rep.counters[f.code] += 1


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Read-only repo-wide ZOZI architecture governance auditor v3.7."
    )

    ap.add_argument("--root", default=None, help="repo root (default: auto-detect)")
    ap.add_argument(
        "--rules-dir",
        default=None,
        help="dir holding repo_structure.yaml + layer_rules.yaml + governance.yaml",
    )
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--json", default=None, help="write findings + summary JSON")
    ap.add_argument("--metrics-json", default=None, help="write module metrics JSON")
    ap.add_argument("--move-map", default=None, help="write file relocation suggestions JSON")
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
    ap.add_argument(
        "--no-registry",
        action="store_true",
        help="skip emitting architecture_registry.json / CODEOWNERS / mermaid",
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

        if not args.move_map:
            args.move_map = str(repo / "out" / "governance" / "move_map.json")

    try:
        DEFAULT_ALLOW_ROOT_MD.update({
            "ARCHITECTURE_AUDIT_REPORT.md",
            "REPO_LAYOUT_AUDIT_REPORT.md",
            "DATABASE_AUDIT_REPORT.md",
            "DESIGN_AUDIT_REPORT.md",
        })
    except Exception:
        pass

    eff = load_rules(repo, Path(args.rules_dir) if args.rules_dir else None)
    ensure_required_ignore_dirs(eff)

    global _ACTIVE_EFF, _ACTIVE_REG
    _ACTIVE_EFF = eff

    print(
        f"Scanning {repo} ...  "
        f"(rules: {'YAML' if eff['from_yaml'] else 'embedded fallback'})"
    )

    rep = Report()
    graph = build_module_graph(repo, eff)
    reg = discover_features(repo, eff, graph)

    _ACTIVE_REG = reg

    # Single unified placement engine.
    placement_suggestions: list[dict] = []

    if "check_move_suggestions" in globals():
        placement_suggestions = check_move_suggestions(repo, rep, eff, graph, reg)

        if placement_suggestions:
            rep.add(
                GRN,
                "I4",
                "repo",
                "move-map",
                f"{len(placement_suggestions)} file move suggestions generated",
                intended="run with --move-map to get exact from/to relocation JSON",
            )

    # Auto-policy learning.
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

    # v3.4 self-contained enhancements.
    enhanced_simple_checks = [
        "check_enhanced_secrets_in_code",
        "check_enhanced_dangerous_calls",
        "check_enhanced_runtime_security_settings",
        "check_enhanced_async_blocking",
        "check_enhanced_query_in_loop",
        "check_enhanced_exception_handling",
        "check_enhanced_todo_debt",
        "check_enhanced_size_complexity",
        "check_enhanced_print_debug",
        "check_enhanced_model_schema",
        "check_enhanced_alembic_heads",
        "check_enhanced_gitignore_generated",
        "check_enhanced_frontend_debug",
    ]

    for fn_name in enhanced_simple_checks:
        fn = globals().get(fn_name)
        if fn:
            fn(repo, rep, eff)

    # v3.8 production readability:
    # collapse noisy line-level findings into file-level findings.
    collapse_noisy_findings(rep)

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

    # Registry / CODEOWNERS / graph.
    if not args.no_registry and "emit_registry" in globals():
        rpath = emit_registry(repo, eff, graph, reg, rep, summary)
        print(f"Registry written: {rpath}")

        try:
            cpath = emit_codeowners(repo, reg, rep)
        except TypeError:
            cpath = emit_codeowners(repo, eff, reg, rep)

        print(f"CODEOWNERS written: {cpath}")

        mpath = emit_graph_mermaid(repo, reg, rep, graph)
        print(f"Graph written: {mpath}")

    # Trend.
    trend_path = Path(args.trend_file).resolve() if args.trend_file else None

    if trend_path:
        if args.update_trend:
            update_trend(trend_path, summary)
            print(f"\nTrend file updated: {trend_path}")
        else:
            baseline = read_json(trend_path)
            print_trend(rep, summary, baseline)

    # Console output.
    n_red = render_stdout(repo, rep, args.show_intended, summary)

    # Markdown report.
    if not args.no_write:
        out = resolve_repo_output_path(
            repo,
            args.out,
            "ARCHITECTURE_AUDIT_REPORT.md",
        )
        render_markdown(repo, rep, out, summary, placements=placement_suggestions)
        print(f"\nReport written: {out}")

    # JSON report.
    if args.json:
        jp = resolve_repo_output_path(
            repo,
            args.json,
            "audit.json",
        )
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
        print(f"JSON written: {jp}")

    # Metrics JSON.
    if args.metrics_json:
        mp = resolve_repo_output_path(
            repo,
            args.metrics_json,
            "metrics.json",
        )
        write_metrics_json(mp, summary, graph)
        print(f"Metrics written: {mp}")

    # Move-map JSON.
    if args.move_map and placement_suggestions and "write_move_map" in globals():
        mm = resolve_repo_output_path(
            repo,
            args.move_map,
            "move_map.json",
        )
        write_move_map(mm, placement_suggestions)
        print(f"Move map written: {mm}")

    return 1 if (n_red and not args.no_fail) else 0

#===========================================================================

if __name__ == "__main__":
    sys.exit(main())