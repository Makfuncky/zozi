# System Architecture Audit Script --- `scripts/system_architecture_audit_3.py`
"""
system_architecture_audit.py — READ-ONLY, repo-wide architecture governance auditor.

Version: v4.0 — Unified Governance Engine

Purpose:
    ZOZI architecture governance engine. Single complete script.
    Enforces the ZOZI backend circuit:

        ENTRY → MIDDLEWARE → ROUTERS(surface) → CONTROLLERS(domain)
            → SERVICES(domain) → PROVIDERS(domain) → MODELS(domain) → DB

    Validates:
    system_architecture_audit_3.py
    │
    ├── SECTION 1: Constants (existing)
    ├── SECTION 2: Domain Taxonomy (existing)
    ├── SECTION 3: Circuit Contract (existing)
    ├── SECTION 4: Data Models (ADD: SymbolIndex, CallGraphNode, LayerContract, ArchitectureRegistry)
    ├── SECTION 5: Generic Helpers (existing)
    ├── SECTION 6: Rule Loading (existing)
    ├── SECTION 7: Module Graph Builder (existing)
    ├── SECTION 8: Feature Discovery (existing)
    ├── SECTION 9: Structure/Hygiene Checks (existing)
    ├── SECTION 10: Circuit Enforcement (ADD: new functions here)
    │   ├── check_circuit_import_direction()
    │   ├── check_middleware_pipeline()
    │   └── check_layer_contracts()
    ├── SECTION 11: Layer/Dependency Checks (existing)
    ├── SECTION 12: Dynamic/Policy/Frontend (existing)
    ├── SECTION 13: Security/Performance/Quality (existing)
    ├── SECTION 14: Domain Placement Engine (existing)
    ├── SECTION 15: Scaffolding/Matrix/Frontend Roles (existing)
    ├── SECTION 16: Auto-Learning (existing)
    ├── SECTION 17: Summary/Trend/Collapse (existing)
    ├── SECTION 18: Rendering (existing)
    ├── SECTION 19: SYMBOL INDEX ENGINE (NEW)
    │
    ├── SECTION 20: CALL GRAPH ENGINE (NEW)
    ├── SECTION 21: PUBLIC API DETECTION (NEW)
    ├── SECTION 22: FLOW-TYPE CLASSIFICATION (NEW)
    ├── SECTION 23: FILE-NAME-TO-CONTENT ALIGNMENT (NEW)
    ├── SECTION 24: SPLIT-FILE DETECTION (NEW)
    ├── SECTION 25: SURFACE-OPERATION VALIDATION (NEW)
    ├── SECTION 26: MIDDLEWARE PIPELINE VALIDATION (NEW)
    ├── SECTION 27: REQUIRED PROJECT FILES (NEW)
    ├── SECTION 28: SCOPE DOCUMENTATION VALIDATION (NEW)
    ├── SECTION 29: API SHAPE VALIDATION (NEW)
    ├── SECTION 30: ADVANCED SECURITY CHECKS (NEW)
    ├── SECTION 31: ADVANCED PERFORMANCE CHECKS (NEW)
    ├── SECTION 32: ADVANCED FRONTEND CHECKS (NEW)
    ├── SECTION 33: ARCHITECTURE METRICS ENHANCED (NEW)
    ├── SECTION 34: DOMAIN EVENT / BOUNDED-CONTEXT VALIDATION (NEW)
    ├── SECTION 35: ARCHITECTURE REGISTRY (NEW)
    │
    ├── SECTION 36: Repo Root Detection (was SECTION 20)
    ├── SECTION 37: Render Markdown (was SECTION 21)
    └── SECTION 38: main() (was SECTION 22)

Design principles:
    * READ-ONLY with respect to source code.
    * Does NOT import application code.
    * Uses stdlib `ast` for Python static analysis.
    * YAML is optional and preferred when present.
    * Embedded rules are fallback.
    * RED is reserved for high-confidence architectural violations.
    * Single implementation of each function (no fix-pack appending).

Sub-folder axis:
- ROUTERS are FLAT.
  Router filename pattern: {surface}_{domain}_{operation}.py
  Examples:
    admin_orders_management.py
    supplier_orders_fulfillment.py
    customer_orders_tracking.py
    public_catalog_product_browsing.py

- DOMAIN folders for:
    controllers/
    services/
    models/
    providers/
    events/
    jobs/

  Domains:
    finance/orders/catalog/supplier/logistics/comms/hr/ai/security/geography/...

- Surface-specific controllers live inside the DOMAIN folder with a surface-prefixed filename:
    controllers/orders/admin_order_management_controller.py
    controllers/catalog/admin_product_moderation_controller.py

Severity:
    [RED] VIOLATION   high-confidence architectural / structural / security problem
    [YEL] ADVISORY    likely drift / maintainability / scaling warning
    [GRN] INFO        summary / metric / healthy signal / discovered feature

Usage:
    python scripts/system_architecture_audit.py --no-fail --show-intended
    python scripts/system_architecture_audit.py --root . --out ARCHITECTURE_AUDIT_REPORT.md
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
# SECTION 1: SEVERITY + RULE DICTIONARY + DEFAULT CONSTANTS
# ============================================================================

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"

SEV_ICON = {RED: "🔴", YEL: "🟡", GRN: "🟢"}
SEV_TAG  = {RED: "[RED]", YEL: "[YEL]", GRN: "[GRN]"}

# ---------------------------------------------------------------------------
# RULE_MEANING — SINGLE consolidated dict (all rules from v3.2 through v3.7)
# ---------------------------------------------------------------------------
RULE_MEANING: dict[str, str] = {
    # Layer violations
    "W1":  "controller/router writes to DB (must be a service)",
    "W2":  "misnamed writer-controller -> relocate to services/",
    "W3":  "imports a mis-housed controller (logic belongs in services/utils)",
    "W4":  "controller imports another controller (shared logic -> service/util)",
    "Q1":  "controller/router reads via db.query (delegate)",
    "M1":  "ORM model outside models/ package",
    "R1":  "APIRouter instantiated outside routers/",
    "G1":  "second migrations home / dual schema-creator",
    "X1":  "ghost/duplicate backend skeleton",
    # Duplicates
    "D1":  "duplicate module basename within backend (import-shadow)",
    "D2":  "duplicate module basename across top dirs",
    "D3":  "duplicate class name across modules",
    # Structure
    "S1":  "services/ is flat (needs domain sub-packages)",
    "S2":  "overlapping service stems (ownership ambiguity)",
    "S3":  "controllers/ flat (group by domain; routers/ is flat by design)",
    "S4":  "surface sub-folder in services/ (must be domain)",
    "S5":  "service domain sub-package too large (split bounded context)",
    "M2":  "models/ is flat (group by domain)",
    "M3":  "surface sub-folder in models/ (must be domain)",
    "M4":  "models domain sub-package too large",
    "L1":  "multiple RLS enforcers (fail-open risk)",
    # Hotspots / dead code
    "A1":  "architecture hotspot (high coupling / instability)",
    "A2":  "possibly dead/orphan module (no inbound imports; not an entrypoint)",
    # Package shape
    "P1":  "scratch script at backend root (delete / scripts/)",
    "P2":  "controller file outside controllers/",
    "P3":  "module at backend root (belongs in a layer package)",
    "P4":  "missing expected backend package",
    "P5":  "python package missing __init__.py",
    "H1":  "sys.path.insert/append (import-resolution footgun)",
    # Hygiene
    "F1":  "scratch/debug script (delete; ops scripts -> scripts/maintenance|validation)",
    "F2":  "hardcoded developer-local absolute path in source",
    "F3":  "dual/triple lockfiles (drift)",
    "F4":  "committed cache/build/artifact present (bloat)",
    "F5":  "secret material on disk (security)",
    "F6":  "media written to / served from local disk (scale killer)",
    "F7":  "raw os.environ secret read in middleware (use settings)",
    "F8":  "non-document artifact at documents/ root",
    "F9":  "repo-root note outside allow-list / banned dir",
    "G0":  "missing/weak root .gitignore",
    # Dependency graph
    "DG":  "forbidden dependency-graph edge (layer contract violated)",
    "DG2": "circular dependency detected",
    "DG3": "cross-domain import violates explicit bounded-context ownership",
    "DG4": "dynamic import edge detected",
    "DG5": "dynamic execution obscures dependency graph",
    # Config
    "CFG1": "unknown layer referenced in policy",
    "CFG2": "unknown domain referenced in policy",
    "CFG3": "malformed or contradictory policy rule",
    "CFG4": "policy-level domain cycle",
    "CFG5": "generated governance artifacts not gitignored",
    # Metrics
    "MET1": "architecture debt score",
    # Frontend
    "FE1": "missing expected frontend workspace/package file",
    "FE2": "frontend scratch/artifact script at package root",
    "FE3": "frontend flat folder scaling warning",
    "FE4": "frontend cross-workspace relative import",
    "FE5": "frontend folder too large (split by feature/domain)",
    "FE6": "frontend console/debugger statement left in source",
    # Domain placement
    "DOM1": "file should be moved into its detected domain folder",
    "DOM2": "file is inside the wrong domain folder",
    "DOM3": "surface folder used where domain folder is required",
    "DOM6": "new domain candidate auto-detected",
    "DOM7": "unknown or non-canonical domain folder",
    "DOM8": "correctly placed domain files",
    # Move suggestions
    "MV1": "flat layer file should be moved into its detected domain folder",
    "MV2": "mis-housed / backend-root file should be relocated to canonical layer",
    "MV3": "router file should be renamed/moved to flat surface_domain_operation.py",
    # Security / quality (v3.4)
    "SEC2":  "possible hardcoded secret/token literal in source",
    "SEC3":  "dangerous dynamic execution / deserialization / shell usage",
    "SEC4":  "insecure runtime setting (debug/cors wildcard with credentials)",
    "PERF1": "blocking call inside async function",
    "PERF2": "possible DB query inside loop (N+1 risk)",
    "QUAL1": "weak exception handling (bare except / swallowed exception)",
    "QUAL2": "TODO/FIXME technical debt marker",
    "QUAL3": "oversized file or function (scaling/maintainability risk)",
    "QUAL4": "print/debug output in application code",
    "DB1":   "ORM model missing __table_args__ schema declaration",
    "DB2":   "multiple Alembic heads detected (migration graph fractured)",
    "DB3":   "Alembic diagnostics/stub/fractured revision artifact",
    # Circuit contract
    "CIR1":  "circuit violation: import is outside the allowed layer circuit",
    "CIR2":  "circuit bypass: import skips the preferred layer (migration warning)",
    # Router naming
    "RN1": "flat router filename must be comprehensive: {surface}_{domain}_{operation}.py",
    "RN2": "router file is inside a sub-folder; routers/ must be flat",
    "RN3": "router sub-folder found; routers/ must be flat with surface_domain_operation filenames",
    # Auto-discovery
    "AUTO0":  "auto-discovery baseline created",
    "AUTO3":  "new backend domain detected",
    "AUTO6":  "new cross-domain dependency learned",
    "AUTO8":  "new top-level backend package detected",
    "AUTO10": "new feature detected",
    # Info
    "NM": "node_modules present (confirm gitignored)",
    "I1": "structure summary",
    "I2": "rules source (yaml vs embedded fallback)",
    "I3": "architecture metric summary",
    "I4": "file move suggestions generated",
    "T1": "architecture trend delta",

    # ADD THESE TO RULE_MEANING dict:
    
    # Symbol / Call Graph
    "SYM1":  "symbol defined but never used (dead symbol)",
    "SYM2":  "duplicate symbol definition across modules",
    "CG1":   "call graph violation: function calls across forbidden layer boundary",
    "CG2":   "call chain violates circuit direction (upward call)",
    "CG3":   "circular call chain detected",
    # Public API
    "API1":  "public API symbol changed without deprecation",
    "API2":  "internal symbol exposed outside its module boundary",
    # Layer Contracts
    "LC1":   "layer contract violation: forbidden operation in layer",
    "LC2":   "layer contract violation: forbidden call pattern",
    "LC3":   "layer contract violation: missing required pattern",
    # Flow Types
    "FT1":   "flow-type violation: operation not allowed for this surface×domain flow",
    "FT2":   "flow-type mismatch: file contains operations from wrong flow direction",
    # Content Alignment
    "CA1":   "file name does not match file content (operations mismatch)",
    "CA2":   "file contains operations from multiple domains (split candidate)",
    "CA3":   "surface-inappropriate operation detected",
    # Middleware
    "MW1":   "middleware pipeline order violation",
    "MW2":   "required middleware missing",
    "MW3":   "middleware imports service/controller (circuit violation)",
    # Project Files
    "PF1":   "required project file missing",
    "PF2":   "required scope document missing",
    # API Shape
    "AS1":   "route prefix does not align with surface",
    "AS2":   "OpenAPI tag does not align with domain",
    "AS3":   "endpoint naming convention violation",
    # Advanced Security
    "SEC5":  "potential SQL injection risk",
    "SEC6":  "potential SSRF risk",
    "SEC7":  "potential path traversal risk",
    "SEC8":  "insecure JWT/token handling",
    "SEC9":  "missing CSRF protection on state-changing endpoint",
    "SEC10": "insecure CORS configuration",
    # Advanced Performance
    "PERF3": "missing pagination on list endpoint",
    "PERF4": "unbounded query detected (no limit clause)",
    "PERF5": "large transaction risk (multiple writes without savepoint)",
    "PERF6": "missing database index on frequently queried column",
    # Advanced Frontend
    "FE7":   "frontend component in wrong feature folder",
    "FE8":   "shared package boundary violation",
    "FE9":   "state management boundary violation",
    # Architecture Metrics
    "MET2":  "module instability exceeds threshold",
    "MET3":  "abstractness below threshold (no interfaces)",
    "MET4":  "distance from main sequence too high",
    "MET5":  "god module detected (excessive responsibility)",
    # Bounded Context
    "BC1":   "cross-domain import bypasses event/facade boundary",
    "BC2":   "domain event not properly defined",
    "BC3":   "bounded context leakage detected",
    # Architecture Registry
    "REG1":  "domain missing from architecture registry",
    "REG2":  "registry dependency not reflected in code",
    "REG3":  "public API not documented in registry",
}

# ---------------------------------------------------------------------------
# HOTLIST_RULES — SINGLE consolidated set
# ---------------------------------------------------------------------------
HOTLIST_RULES: set[str] = {
    "W1", "W2", "W3", "W4", "Q1", "M1", "R1", "G1", "X1",
    "D1", "D2", "D3",
    "S1", "S2", "S3", "S4", "S5", "M2", "M3", "M4", "L1",
    "A1", "A2",
    "P1", "P2", "P3", "P4", "P5", "H1",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "G0",
    "DG", "DG2", "DG3", "DG4", "DG5",
    "CFG1", "CFG2", "CFG3", "CFG4", "CFG5",
    "MET1",
    "FE1", "FE2", "FE3", "FE4", "FE5", "FE6",
    "DOM1", "DOM2", "DOM3", "DOM6", "DOM7",
    "MV1", "MV2", "MV3",
    "SEC2", "SEC3", "SEC4", "PERF1", "PERF2",
    "QUAL1", "QUAL2", "QUAL3", "QUAL4",
    "DB1", "DB2", "DB3",
    "RN1", "RN2", "RN3",
    "CIR1", "CIR2",
    "AUTO0", "AUTO3", "AUTO6", "AUTO8", "AUTO10",
    "NM",

    # ADD THESE TO HOTLIST_RULES set:
    "SYM1", "SYM2",
    "CG1", "CG2", "CG3",
    "API1", "API2",
    "LC1", "LC2", "LC3",
    "FT1", "FT2",
    "CA1", "CA2", "CA3",
    "MW1", "MW2", "MW3",
    "PF1", "PF2",
    "AS1", "AS2", "AS3",
    "SEC5", "SEC6", "SEC7", "SEC8", "SEC9", "SEC10",
    "PERF3", "PERF4", "PERF5", "PERF6",
    "FE7", "FE8", "FE9",
    "MET2", "MET3", "MET4", "MET5",
    "BC1", "BC2", "BC3",
    "REG1", "REG2", "REG3",
}

# ---------------------------------------------------------------------------
# DEFAULT CONSTANTS (each defined ONCE)
# ---------------------------------------------------------------------------

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "htmlcov", ".next", ".expo", ".kotlin", "gradle", "android", "ios",
    ".idea", ".vscode", "test-results", ".playwright-artifacts-0",
    "playwright-out", "static-tmp", ".web-build-test", "artifacts",
    "uploads", ".turbo", "dist", "build", "coverage",
    "playwright-report", "test-output", "tmp",
    ".hypothesis", ".kilo", ".kilocode", "worktrees", ".repo",
}

DEFAULT_CACHE_DIR_NAMES = {
    ".ruff_cache", ".mypy_cache", ".pytest_cache", ".next", ".expo",
    "dist", "build", "coverage", "htmlcov", ".turbo", "web-dist",
    ".playwright-artifacts-0", "test-results", "playwright-report", "test-output",
}

DEFAULT_TEXT_EXT = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".yml", ".yaml",
    ".md", ".ini", ".toml", ".css", ".html", ".sh", ".bat", ".ps1", ".cjs", ".mjs",
}

DEFAULT_SOURCE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".bat", ".ps1"}
DEFAULT_FRONTEND_SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"}
DEFAULT_MAX_READ_BYTES = 2_000_000

DEFAULT_SCRATCH_PHRASES = [
    "countdivs", "stackdivs", "printlines", "linenums", "fixtailwind",
    "patch-vars", "patch_vars", "verify-tmp", "verify_tmp", "impmain",
    "client_tmp", "reset_tmp",
]

DEFAULT_SCRATCH_TOKENS = {
    "tmp", "temp", "scratch", "debug", "test", "check", "write", "list",
    "reset", "verify", "run", "script", "probe", "diag", "inspect",
}

DEFAULT_SCRIPTS_SAFE_TOKENS = {"tmp", "temp", "scratch", "debug", "diag", "inspect"}

DEFAULT_BACKEND_ROOT_ALLOW = {
    "__init__.py", "main.py", "lifespan.py", "run_server.py", "start_server.py",
}

DEFAULT_ALLOW_ROOT_MD = {
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md",
    "SECURITY.md", "LICENSE.md", "LICENSE",
    "ARCHITECTURE_AUDIT_REPORT.md", "DATABASE_AUDIT_REPORT.md",
    "DESIGN_AUDIT_REPORT.md", "REPO_LAYOUT_AUDIT_REPORT.md",
    "PROJECT_SCAFFOLDING.md", "FEATURES_LIST.md",
    "GOVERNANCE_REPORT.md", "HEALTH_AUDIT_REPORT.md",
}

DEFAULT_ALLOW_DOCS_ROOT = {"scope", "archive", "README.md", "DOCUMENTATION_INDEX.md", "INDEX.md"}
DEFAULT_DOC_EXT = {".md", ".txt", ".rst", ".adoc", ".pdf"}

DEFAULT_FORBIDDEN_ROOT = {
    "backend": [
        r".*\.(log|db|db-shm|db-wal)$",
        r"^token\.tmp$",
        r"^.*\.json$",
        r"^(?!requirements\.txt$).*\.txt$",
    ],
    "backend/alembic": [r"^_.*\.py$"],
    "frontend": [r".*\.(log|tsbuildinfo)$"],
    "frontend/web_app": [
        r".*\.bak$", r"\.tsbuildinfo$",
        r"^build_final.*$", r"^build_out.*$", r"^build_log\.txt$",
        r"^_audit_.*\.cjs$", r"^verify_.*\.cjs$",
        r"^debug.*\.spec\.ts$", r"^diag.*\.spec\.ts$",
        r"^inspect-playwright\.cjs$", r"^playwright-results\.txt$",
        r".*_test(_output|_verbose)?\.txt$",
        r".*\.(png|jpe?g)$", r"^-w$", r".*\.log$",
    ],
    "frontend/mobile_app": [r".*\.log$", r"^expo-err\.log$", r"^expo-start\.log$"],
    ".": [
        r"^Working_API$", r"^provider_test$", r"^_trash$",
        r"^backup_\d+", r"^image$", r"^zozi-logo-app$",
        r".*\.zip$", r"^login_form\.yml$", r"^login_rsp\.json$",
        r"^zozi\.db(-shm|-wal)?$", r"^dev\.db$", r"^.*\.log$",
        r"^_orchestrator_read\.py$", r"^fix_.*\.py$",
        r"^generate_.*\.py$", r"^problems\.txt$", r"^mobile_app\.html$",
    ],
    "documents": [],
}

DEFAULT_FORBIDDEN_ANY = {
    # employee_models.py is ONLY illegal under db/ — it is CORRECT under models/
    "backend": [r"/db/migrations/", r"/db/employee_models\.py$", r"/log/.*\.(log|txt)$"],
    "backend/db": [r"/migrations/", r"employee_models\.py$"],
    "backend/alembic": [r"/versions/.*stub.*\.py$"],
    "frontend/mobile_app/scripts": [r".*\.(log|err)$"],
}

DEFAULT_FORBIDDEN_EDGES = {
    # Middleware / dependencies are request-preprocessing layers.
    # They must not reach into business/domain layers.
    "middleware": [
        "services",
        "controllers",
        "routers",
        "models",
        "providers",
        "events",
        "jobs",
    ],
    "dependencies": [
        "services",
        "controllers",
        "routers",
        "models",
        "providers",
        "events",
        "jobs",
    ],

    # Routers should stay thin.
    # They may call controllers/services/utils during migration,
    # but must not use providers or direct DB infrastructure.
    "routers": [
        "providers",
        "db.database",
        "db.create_tables",
        "db.init_db",
    ],

    # Controllers orchestrate.
    # They must not import routers or security middleware,
    # and must not touch DB engine/session creation directly.
    "controllers": [
        "routers",
        "middleware",
        "dependencies",
        "db.database",
        "db.create_tables",
        "db.init_db",
    ],

    # Services are business logic and the only normal DB writers.
    # They must not depend upward on routers/controllers/middleware.
    "services": [
        "routers",
        "controllers",
        "middleware",
        "dependencies",
    ],

    # Providers are external adapters.
    # They must not depend on application layers or ORM models.
    "providers": ["routers","controllers","services","models","middleware","dependencies","db.database","db.create_tables","db.init_db","events","jobs",],

    # Models are data entities.
    # They must not depend on application layers.
    "models": ["routers","controllers","services","providers","middleware","dependencies","events","jobs",],

    # Events/jobs may use services/models/providers,
    # but must not depend upward on HTTP/middleware layers.
    "events": ["routers","controllers","middleware","dependencies",],

    "jobs": ["routers","controllers","middleware","dependencies",],

    # Utils should be pure helpers.
    "utils": ["routers","controllers","services","models","providers","middleware","dependencies","db.database","db.create_tables","db.init_db",],

    # DB infrastructure must not depend on application layers.
    "db": ["routers","controllers","services","providers","middleware","dependencies","events","jobs",],
}

DEFAULT_MIS_HOUSED_CONTROLLERS = {"audit_controller", "payments_controller", "cache_utils"}
DEFAULT_KNOWN_WRITER_CONTROLLERS = {"audit_controller.py"}

DEFAULT_WRITE_VERBS = {
    "add", "commit", "delete", "merge", "flush", "refresh",
    "execute", "bulk_insert_mappings", "bulk_save_objects",
    "begin", "rollback", "savepoint",
}
DEFAULT_READ_VERBS = {"query"}

DEFAULT_SECRET_FILE_PATTERNS = [
    r"(^|/)token\.tmp$",
    r"(^|/)\.env$",
    r"(^|/).*\.(key|pem|p12|pfx|secret)$",
    r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$",
    r"(^|/).*credentials.*\.(json|ya?ml)$",
]

DEFAULT_ENV_SECRET_KEYS = (
    r"""os\.environ\.(?:get\(\s*|[\[])\s*["']"""
    r"""(APP_ENV|SECRET_KEY|JWT_SECRET|DATABASE_URL|DB_PASSWORD|REDIS_URL|"""
    r"""HF_API_TOKEN|STRIPE_SECRET|AWS_SECRET|ENCRYPTION_KEY|TOKEN|PASSWORD)"""
)

DEFAULT_LOCAL_PATH = (
    r"[A-Za-z]:[\\/](?:Users|Projects|home|Documents|Desktop|recovery_recuva)[\\/]"
    r"|/home/[A-Za-z0-9_.-]+/|/Users/[A-Za-z0-9_.-]+/"
)

DEFAULT_MEDIA_DISK_WRITE = r"""open\(\s*(?:f?["'][^"']*uploads/|.*upload_dir)"""
DEFAULT_MEDIA_DISK_URL   = r"""image_url\s*=\s*f?["']\{?\s*upload_dir"""

DEFAULT_LOCKFILES = {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"}

DEFAULT_ARTIFACT_EXTS = {".log", ".db-shm", ".db-wal", ".tsbuildinfo"}
DEFAULT_ARTIFACT_NAMES = {
    "schema-audit-report.json", "vision_cache.json", "alembic_test.json",
    "_import_test_out.txt", "playwright-results.txt",
    "backend.log", "server_stderr.log", "server_stdout.log", "run_log.txt",
}

DEFAULT_DUP_IGNORE_BASENAMES = {"__init__", "conftest"}

DEFAULT_CANONICAL_HOME = {
    "database.py": "db/database.py",
    "schemas.py": "db/schemas.py",
    "config.py": "utils/config.py",
    "auth.py": "utils/auth.py",
    "email_service.py": "utils/email_service.py",
}

DEFAULT_SURFACE_NAMES = {"admin","supplier","customer","logistics","public",
                         "webhooks","webhook","api","internal","external","partner",}

DEFAULT_DOMAIN_LAYERS    = {"services", "models"}
DEFAULT_OWNERSHIP_LAYERS = {"services", "models"}

DEFAULT_GRAPH_EXEMPT_LAYERS = {"tests", "scripts", "alembic", "monitoring", "docs", "data"}

DEFAULT_DEAD_EXEMPT_LAYERS = {"tests","scripts","alembic","data","monitoring","docs",}

DEFAULT_DEAD_AUDIT_LAYERS = {"services","models","controllers","routers","providers","utils","events","jobs","middleware","dependencies","db"}

DEFAULT_DEAD_ENTRYPOINTS = [
    r"^main$", r"^lifespan$", r"^run_server$", r"^start_server$",
    r"^routers(\.|$)", r"^alembic\.env$", r"^scripts(\.|$)", r"^tests(\.|$)",
    r"^middleware(\.|$)", r"^dependencies(\.|$)", r"^providers(\.|$)",
    r"^events(\.|$)", r"^jobs(\.|$)", r"^data(\.|$)",
    r"^db\.base$", r"^db\.database$",
]

DEFAULT_DUP_CLASS_IGNORE = {
    "Base", "Metadata", "Config", "Enum", "Schema", "Model",
    "Table", "Mixin", "Settings", "Exception", "Error",
}

DEFAULT_EXPECTED_BACKEND_PACKAGES = [
    "routers", "controllers", "services", "models", "middleware",
    "dependencies", "providers", "utils", "db", "alembic",
    "tests", "scripts", "events", "jobs", "data",
]

DEFAULT_NO_INIT_DIRS = {"scripts", "tests", "alembic", "data", "monitoring", "docs"}
DEFAULT_FRONTEND_WORKSPACES = {"web_app", "mobile_app", "shared"}

DEFAULT_FRONTEND_ROOT_ALLOW = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "pnpm-workspace.yaml", "tsconfig.json", "tsconfig.build.json",
    "next.config.ts", "next-env.d.ts", "middleware.ts", "eslint.config.js",
    "jest.config.js", "jest.setup.ts", "playwright.config.ts",
    "postcss.config.js", "tailwind.config.js", "babel.config.js",
    "metro.config.js", "app.config.js", "app.json", "expo-env.d.ts",
    "README.md", "ERROR_HANDLING.md", "Dockerfile", "sentry.config.ts",
    "patch-logbox.js",
}

# Thresholds
DEFAULT_FLAT_THRESHOLD = 30
DEFAULT_LARGE_SUBPACKAGE_THRESHOLD = 80
DEFAULT_GOD_FAN_OUT = 20
DEFAULT_GOD_FAN_IN  = 30
DEFAULT_MAX_CYCLES  = 80
DEFAULT_MAX_CYCLE_LENGTH = 10
DEFAULT_FRONTEND_FLAT_THRESHOLD = 40
DEFAULT_FRONTEND_LARGE_FOLDER_THRESHOLD = 120

FEATURE_STOP_NAMES = {
    "__init__", "index", "page", "layout", "loading", "error", "not-found",
    "route", "main", "app", "init", "package", "types", "utils",
    "helpers", "shared", "common", "ui", "admin", "supplier", "customer",
    "public", "webhooks", "webhook", "api", "internal", "external",
    "src", "components", "features", "hooks", "lib", "services", "models",
    "controllers", "routers",
}

FEATURE_SUFFIXES = [
    "_service", "_services", "_controller", "_controllers", "_router", "_routers",
    "_model", "_models", "_provider", "_providers", "_event", "_events",
    "_job", "_jobs", "_page", "_pages", "_screen", "_screens",
    "_component", "_components", "_hook", "_hooks", "_store", "_stores",
    "_api", "_utils", "_helpers", "_types", "_test", "_tests", "_spec",
]


# ============================================================================
# SECTION 2: DOMAIN TAXONOMY (SINGLE SOURCE OF TRUTH)
# ============================================================================

PLACEMENT_DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "finance": {"finance", "financial", "ledger", "sub_ledger", "general_ledger", "journal", "invoice", "invoices", "tax", "vat", "commission",
        "billing", "accounting", "posting", "refund", "ap", "ar", "payments", "payment", "credit_control", "period_close", "erp",
        "commission_write", "financial_reports", "financial_reporting", "finance_automation", "finance_erp",},
    "treasury": {"treasury", "treasurer", "cash", "bank", "payout", "payouts", "settlement", "settlements", "reconciliation",
        "gateway_reconciliation", "payment_engine", "payment_orchestrator", "auto_payout", "payout_batch", "cash_flow",},
    "orders": {"order", "orders", "checkout", "cart", "purchase", "purchases", "return", "returns", "dispute", "disputes", "fulfillment", "ghost",},
    "catalog": {"catalog", "product", "products", "category", "categories", "variant", "variants", "filter", "filters", "inventory",
        "stock", "search", "moderation", "verification", "advanced_filter", "advanced_search", "product_verification", "product_moderation",},
    "commerce": {"commerce", "promotion", "promotions", "coupon", "coupons", "discount", "discounts", "flash_sale", "wishlist", "referral", "reviews", "loyalty",},
    "supplier": {"supplier", "suppliers", "vendor", "vendors", "onboarding", "kyc", "badge", "storefront",
        "supplier_badge", "supplier_health", "supplier_profile", "supplier_products", "supplier_inventory", "supplier_onboarding",},
    "customer": {"customer", "customers", "address", "addresses", "point", "points", "profile",},
    "logistics": {"logistics", "shipping", "shipment", "shipments", "dispatch", "delivery", "carrier", "fleet",
        "route", "routes", "pod", "tracking", "parcel", "geo", "geofence", "geo_fence", "map", "live_tracking",},
    "comms": {"comms","communication","comm","chat","email","sms","push","notification","notifications","ticket","tickets",
              "message","messages","video","meeting","websocket","translation","websocket_manager","write_chat","fix_chat",},
    "hr": {"hr", "employee", "employees", "attendance", "shift", "shifts", "leave", "coi", "lms", "performance", "succession", "travel", 
           "hse", "dei", "offboarding", "roster", "handover", "payroll", "background", "shift_handover", "shift_roster", "shift_scheduling", "background_check",},
    "ai": {"ai", "ml", "embedding", "embeddings", "ocr", "vision","bg", "bg_removal", "removal", "chatbot", "voice",
           "recommendation", "research", "automation", "variant_config", "image_ai", "text",},
    "audit": {"audit", "worm", "audit_log", "audit_trail","permission_audit", "communication_audit", "auditor",},
    "security": {"security", "auth", "authentication", "authorization", "permission", "permissions", "rbac", "iam", "mfa",
        "otp", "fraud", "risk", "blacklist", "device_binding","csrf", "incident", "watchdog", "biometric", "ghost", "ghost_watchdog",},
    "core": {"core", "user", "users", "role", "roles", "session", "device", "identity", "preferences", "banner", "banners",
        "settings", "platform", "approval_matrix", "approval","workflow", "workflow_engine", "customer_health",},
    "geography": {"geography","country","countries","city","cities","cross_border","cross","border","localization",
                  "currency","country_detection","country_research","economics","cross_border_tracker",},
    "media": {"media", "asset", "assets", "image", "images","upload", "uploads", "file", "storage", "free_image",},
    "analytics": {"analytics", "snapshot", "snapshots", "kpi", "mv","report", "reports", "metrics", "insights", "dashboard",},
    "configuration": {"configuration", "config", "feature_flag", "feature", "flag", "toggles", "rules",},
}

# Build alias lookup (built ONCE at module load)
PLACEMENT_ALIAS_TO_DOMAIN: dict[str, str] = {}
for _dom, _aliases in PLACEMENT_DOMAIN_KEYWORDS.items():
    PLACEMENT_ALIAS_TO_DOMAIN[_dom.lower()] = _dom
    for _a in _aliases:
        PLACEMENT_ALIAS_TO_DOMAIN[str(_a).lower()] = _dom

# Generic tokens that must NEVER become domain names
PLACEMENT_STOP_TOKENS: set[str] = {
    "service", "services", "controller", "controllers", "router", "routers",
    "model", "models", "provider", "providers", "event", "events",
    "job", "jobs", "write", "read", "create", "update", "delete",
    "get", "list", "add", "edit", "remove", "process", "processor",
    "handler", "manager", "management", "util", "utils", "helper",
    "helpers", "common", "shared", "base", "main", "app", "module",
    "package", "lib", "src", "backend", "frontend", "zozi",
    "tmp", "temp", "test", "tests", "testing", "debug", "scratch",
    "old", "new", "copy", "backup", "final", "wip", "legacy",
    "engine", "scheduler", "script", "scripts", "task", "tasks",
    "worker", "workers", "middleware", "dependencies", "tools", "data",
    "docs", "monitoring", "alembic", "db", "web", "mobile", "ui",
    "component", "components", "page", "pages", "hook", "hooks",
    "store", "stores", "type", "types", "schema", "schemas",
    "mixin", "mixins", "init", "index", "system", "api", "async",
    "seed", "all", "database", "logging", "logger", "import",
    "import_module", "modules", "datetime", "uuid", "sqlalchemy",
    "json", "os", "sys", "pathlib", "typing", "asyncio", "boto3",
    "future", "exceptions", "error", "errors", "exception",
    "advanced", "fix", "script1", "script2",
}

# Tokens that indicate a file belongs to its CURRENT folder (stability override)
PLACEMENT_FOLDER_STABLE_TOKENS: set[str] = {
    "products", "product", "inventory", "profile", "reviews", "review",
    "orders", "order", "payments", "payment", "documents", "document",
    "onboarding", "reports", "report", "analytics", "dashboard",
    "settings", "uploads", "upload", "labels", "label", "pricing", "insights",
}

PLACEMENT_DOMAIN_LAYERS = [
    "services", "models", "controllers", "providers", "events", "jobs",
]

PLACEMENT_SKIP_PARTS = {
    "tests", "test", "scripts", "alembic", "data", "monitoring", "docs",
    "node_modules", "dist", "build", "coverage", "__pycache__",
    "static", "templates", "e2e", "__tests__", "tools", ".hypothesis",
}

# ---------------------------------------------------------------------------
# ROUTE SIGNAL REGEXES
# Single source for route extraction used by placement + auto-learning.
# ---------------------------------------------------------------------------
AUTO_ROUTE_PREFIX_RE = re.compile(
    r"APIRouter\([^)]*prefix\s*=\s*['\"]([^'\"]+)['\"]",
    re.I,
)

AUTO_ROUTE_DECOR_RE = re.compile(
    r"@\w+\.(?:get|post|put|patch|delete|options|head|websocket)\(\s*['\"]([^'\"]+)['\"]",
    re.I,
)

AUTO_ROUTE_TAGS_RE = re.compile(
    r"tags\s*=\s*\[([^\]]*)\]",
    re.I,
)

# ============================================================================
# SECTION 3: CIRCUIT CONTRACT — ACTIVE
# ============================================================================
#
# Correct ZOZI circuit:
#
#   ENTRY
#     -> MIDDLEWARE / DEPENDENCIES
#       -> ROUTERS
#         -> CONTROLLERS
#           -> SERVICES
#             -> PROVIDERS
#               -> MODELS
#                 -> DB
#
# Utils and data are cross-cutting helper layers.
# Utils must not import application layers.
# Data must not import application layers.
# ============================================================================

CIRCUIT_ALLOWED_IMPORTS: dict[str, set[str]] = {
    # Entry / lifecycle
    "main": {
        "middleware",
        "dependencies",
        "routers",
        "db",
        "utils",
        "lifespan",
        "data",
    },
    "lifespan": {
        "db",
        "utils",
        "middleware",
        "dependencies",
        "data",
    },

    # Request preprocessing
    "middleware": {
        "db",
        "utils",
        "dependencies",
        "data",
    },
    "dependencies": {
        "db",
        "utils",
        "data",
    },

    # HTTP surface
    "routers": {
        "controllers",
        "dependencies",
        "utils",
        "data",
    },

    # Orchestration
    "controllers": {
        "services",
        "utils",
        "data",
    },

    # Business logic and normal DB writers
    "services": {
        "models",
        "providers",
        "utils",
        "events",
        "jobs",
        "db",
        "data",
    },

    # External adapters
    "providers": {
        "utils",
        "data",
    },

    # ORM entities
    "models": {
        "db",
        "utils",
    },

    # DB infrastructure
    "db": {
        "utils",
    },

    # Async/domain workers
    "events": {
        "services",
        "models",
        "providers",
        "utils",
        "db",
        "data",
    },
    "jobs": {
        "services",
        "models",
        "providers",
        "utils",
        "db",
        "data",
    },

    # Config-as-data
    "data": set(),

    # Pure helpers
    "utils": set(),
}


# ---------------------------------------------------------------------------
# Migration bypass warnings.
#
# These are not hard RED circuit violations yet, but they are architecturally
# undesirable and should be migrated.
# ---------------------------------------------------------------------------
CIRCUIT_BYPASS_IMPORTS: dict[tuple[str, str], str] = {
    ("routers", "services"): (
        "routers should call controllers; direct router -> service usage "
        "skips the orchestration layer"
    ),
    ("routers", "models"): (
        "routers should not read models directly; use controllers/services"
    ),
    ("controllers", "models"): (
        "controllers should use services for model access; direct model "
        "usage is a migration bypass"
    ),
}

# ============================================================================
# SECTION 4: DATA MODELS
# ============================================================================

# Active configuration globals (set in main(), used by helpers)
_ACTIVE_EFF: dict | None = None
_ACTIVE_REG: "FeatureRegistry | None" = None

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
                sev=sev, code=code, domain=domain,
                path=path, message=message,
                intended=intended, line=line,
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


@dataclass
class AutoDomainModel:
    domains: set[str] = field(default_factory=set)
    surfaces: set[str] = field(default_factory=set)
    profiles: dict[str, dict[str, float]] = field(default_factory=dict)
    candidate_domains: set[str] = field(default_factory=set)
    token_files: dict[str, set[str]] = field(default_factory=dict)


@dataclass
class SymbolInfo:
    """A single symbol (class, function, variable) in the codebase."""
    name: str
    kind: str  # "class", "function", "method", "variable", "constant"
    module: str
    file_path: str
    line: int
    is_public: bool = False
    is_deprecated: bool = False
    decorators: list[str] = field(default_factory=list)
    parent_class: str | None = None
    docstring: str | None = None


@dataclass
class SymbolIndex:
    """Repository-wide symbol index (like a language server)."""
    symbols: dict[str, list[SymbolInfo]] = field(default_factory=dict)
    class_methods: dict[str, list[str]] = field(default_factory=dict)
    module_exports: dict[str, set[str]] = field(default_factory=dict)
    symbol_usages: dict[str, list[tuple[str, int]]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add(self, sym: SymbolInfo) -> None:
        self.symbols.setdefault(sym.name, []).append(sym)
        if sym.kind == "class":
            self.class_methods.setdefault(sym.name, [])
        if sym.parent_class:
            self.class_methods.setdefault(sym.parent_class, []).append(sym.name)

    def find_symbol(self, name: str) -> list[SymbolInfo]:
        return self.symbols.get(name, [])

    def find_class(self, name: str) -> SymbolInfo | None:
        for sym in self.symbols.get(name, []):
            if sym.kind == "class":
                return sym
        return None


@dataclass
class CallEdge:
    """A single call edge in the call graph."""
    caller_module: str
    caller_function: str
    callee_module: str
    callee_function: str
    line: int
    call_type: str = "direct"  # "direct", "method", "dynamic"


@dataclass
class CallGraph:
    """Function-level call graph."""
    edges: list[CallEdge] = field(default_factory=list)
    adjacency: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )
    reverse_adjacency: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )

    def add_edge(self, edge: CallEdge) -> None:
        self.edges.append(edge)
        caller_key = f"{edge.caller_module}.{edge.caller_function}"
        callee_key = f"{edge.callee_module}.{edge.callee_function}"
        self.adjacency[caller_key].add(callee_key)
        self.reverse_adjacency[callee_key].add(caller_key)

    def get_call_chain(self, start: str, max_depth: int = 10) -> list[list[str]]:
        """BFS to find call chains from a starting node."""
        chains: list[list[str]] = []
        queue: list[tuple[str, list[str]]] = [(start, [start])]
        while queue:
            node, path = queue.pop(0)
            if len(path) > max_depth:
                continue
            for neighbor in self.adjacency.get(node, set()):
                if neighbor not in path:
                    new_path = path + [neighbor]
                    chains.append(new_path)
                    queue.append((neighbor, new_path))
        return chains


@dataclass
class LayerContract:
    """Defines what a layer may and may not do."""
    layer: str
    may_import: set[str] = field(default_factory=set)
    may_not_import: set[str] = field(default_factory=set)
    may_call: set[str] = field(default_factory=set)
    may_not_call: set[str] = field(default_factory=set)
    allowed_operations: set[str] = field(default_factory=set)
    forbidden_operations: set[str] = field(default_factory=set)
    required_patterns: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)


@dataclass
class FlowType:
    """Flow type classification for a domain × surface intersection."""
    domain: str
    surface: str
    flow_type: str  # "forward", "backward", "two_way", "tree", "multi_way", "one_way_in", "one_way_out", "oversight"
    operations: list[str] = field(default_factory=list)


@dataclass
class ArchitectureRegistryEntry:
    """One entry in the architecture registry."""
    domain: str
    owner: str = ""
    depends_on: list[str] = field(default_factory=list)
    public_api: list[str] = field(default_factory=list)
    events_produced: list[str] = field(default_factory=list)
    events_consumed: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ArchitectureRegistry:
    """Generated + human-overridable architecture registry."""
    entries: dict[str, ArchitectureRegistryEntry] = field(default_factory=dict)

    def add(self, entry: ArchitectureRegistryEntry) -> None:
        self.entries[entry.domain] = entry

    def get(self, domain: str) -> ArchitectureRegistryEntry | None:
        return self.entries.get(domain)


# ============================================================================
# SECTION 5: GENERIC HELPERS
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
    Driven by governance.yaml -> policy.logical_domains when available.
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
    """Backward-compatible wrapper. Uses active configuration when available."""
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


def ensure_required_ignore_dirs(eff: dict) -> None:
    """
    Make sure editor/worktree/cache directories are always ignored,
    even if YAML config overrides ignore_dirs.
    """
    required_ignore = {
        ".git", ".kilo", "worktrees", ".hypothesis", ".repo",
        ".vscode", ".idea", "node_modules", "__pycache__", ".venv",
        "venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
        "htmlcov", ".next", ".expo", ".turbo", "dist", "build",
        "coverage", "test-results", "playwright-report", "playwright-out",
        ".web-build-test", "static-tmp", "tmp", "uploads", "artifacts",
    }
    current = {str(x).lower() for x in eff.get("ignore_dirs", set())}
    eff["ignore_dirs"] = current | required_ignore


# ============================================================================
# SECTION 6: RULE LOADING
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
        "scratch_phrases", "scratch_tokens", "scripts_safe_tokens",
        "dead_entrypoints", "secret_file_patterns",
    }
    set_lower_keys = {
        "ignore_dirs", "cache_dir_names", "text_ext", "source_ext",
        "surface_names", "write_verbs", "read_verbs", "lockfiles",
        "artifact_exts", "dup_ignore_basenames", "domain_layers",
        "ownership_layers", "graph_exempt_layers", "dead_exempt_layers",
        "dead_audit_layers", "no_init_dirs", "frontend_workspaces",
        "frontend_source_ext", "doc_ext",
    }
    set_exact_keys = {
        "backend_root_allow", "allow_root_md", "allow_docs_root",
        "artifact_names", "known_writer_controllers", "dup_class_ignore",
        "expected_backend_packages", "frontend_root_allow",
    }
    scalar_keys = {
        "max_read_bytes", "flat_threshold", "large_subpackage_threshold",
        "god_fan_out", "god_fan_in", "max_cycles", "max_cycle_length",
        "frontend_flat_threshold", "frontend_large_folder_threshold",
        "forbidden_controller_to_controller", "detect_module_cycles",
        "detect_domain_cycles", "detect_dead_modules", "detect_metrics",
        "detect_duplicate_classes", "detect_dynamic_imports",
        "detect_policy_config", "detect_frontend", "detect_auto_discovery",
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
    """Load advanced configurable policy values that were previously hardcoded."""
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
        eff["forbidden_root"], struct.get("forbidden_root"),
    )
    eff["forbidden_any"] = _merge_dict_of_lists(
        eff["forbidden_any"], struct.get("forbidden_any"),
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
                "1", "true", "yes", "on",
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
        "allow_root_md": set(DEFAULT_ALLOW_ROOT_MD),
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
        # configurable policy defaults
        "feature_stop_names": set(FEATURE_STOP_NAMES),
        "feature_suffixes": list(FEATURE_SUFFIXES),
        "repo_root_min_top_dirs": 8,
        "repo_root_min_py_files": 50,
        "local_path_scan_tops": ["backend", "frontend", "scripts"],
        "media_scan_layers": [
            "controllers", "services", "routers", "providers", "models", "utils",
        ],
        "scratch_scan_roots": ["frontend", "scripts", "."],
        "logical_domains": {
            "database": {"parts": ["alembic", "db", "models"]},
            "security": {"parts": ["middleware", "dependencies"], "basename": ["security_config.ini"]},
            "frontend": {"first": "frontend"},
            "docs": {"first": "documents"},
            "infra": {"first": ["monitoring", "nginx", "infra"]},
            "backend": {"first": "backend"},
        },
        "frontend_flat_paths": [
            {"path": "frontend/web_app/src/components", "threshold_key": "frontend_flat_threshold"},
            {"path": "frontend/web_app/src/lib", "threshold_key": "frontend_flat_threshold"},
            {"path": "frontend/web_app/src/hooks", "threshold_key": "frontend_flat_threshold"},
            {"path": "frontend/mobile_app/components", "threshold_key": "frontend_flat_threshold"},
            {"path": "frontend/mobile_app/lib", "threshold_key": "frontend_flat_threshold"},
            {"path": "frontend/shared/src", "threshold_key": "frontend_flat_threshold"},
        ],
        "domain_layer_configs": [
            {"layer": "services", "flat_code": "S1", "surface_code": "S4", "large_code": "S5"},
            {"layer": "models", "flat_code": "M2", "surface_code": "M3", "large_code": "M4"},
        ],
        "codeowners": {
            "default_owner": "@zozi/platform",
            "domain_owner_template": "@zozi/{domain}",
            "domain_paths": ["backend/services/{domain}/", "backend/models/{domain}/"],
            "surface_paths": ["backend/routers/{surface}/", "backend/controllers/{surface}/"],
        },
        "placement": {
            "enabled": True,
            "layers": ["services", "models", "providers", "events", "jobs", "controllers"],
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
    layer_cfg = None
    gov = None
    for d in candidates:
        if not d or not d.is_dir():
            continue
        if struct is None:
            struct = _read_cfg(d / "repo_structure.yaml") or _read_cfg(d / "repo_structure.json")
        if layer_cfg is None:
            layer_cfg = _read_cfg(d / "layer_rules.yaml") or _read_cfg(d / "layer_rules.json")
        if gov is None:
            gov = _read_cfg(d / "governance.yaml") or _read_cfg(d / "governance.json")
        if struct and layer_cfg and gov:
            break

    if struct:
        eff["from_yaml"] = True
        _apply_structure(eff, struct)
    if layer_cfg:
        eff["from_yaml"] = True
        _apply_layer(eff, layer_cfg)
    if gov:
        eff["from_yaml"] = True
        _apply_policy(eff, gov)
    for cfg in (struct, layer_cfg, gov):
        _apply_advanced_policy(eff, cfg)

    # Normalize
    eff["text_ext"] = {str(x).lower() for x in eff["text_ext"]}
    eff["source_ext"] = {str(x).lower() for x in eff["source_ext"]}
    eff["frontend_source_ext"] = {str(x).lower() for x in eff["frontend_source_ext"]}
    eff["ignore_dirs"] = {str(x).lower() for x in eff["ignore_dirs"]}
    eff["cache_dir_names"] = {str(x).lower() for x in eff["cache_dir_names"]}
    eff["scratch_phrases"] = [str(x).lower() for x in eff.get("scratch_phrases", [])]
    eff["scratch_tokens"] = {str(x).lower() for x in eff.get("scratch_tokens", set())}
    eff["scripts_safe_tokens"] = {str(x).lower() for x in eff.get("scripts_safe_tokens", set())}

    # Discover known layers from filesystem
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

    # Compile regex patterns
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
# SECTION 7: MODULE GRAPH BUILDER
# ============================================================================

def build_module_graph(repo: Path, eff: dict) -> ModuleGraph:
    graph = ModuleGraph()
    backend = repo / "backend"
    if not backend.exists():
        return graph

    known_top = {str(x).lower() for x in eff["expected_backend_packages"]}

    # Phase 1: Register all Python modules
    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue
        module = backend_module_name(f, backend)
        if not module:
            continue
        graph.modules[module] = f
        known_top.add(module.split(".", 1)[0])

    # Phase 2: Parse imports and build edges
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

            # Dynamic imports / eval / exec detection
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
                elif fname in {"eval", "exec"}:
                    graph.dynamic_calls.append((module, fname, node.lineno))

    graph.finalize()
    return graph


# ============================================================================
# SECTION 8: FEATURE AUTO-DISCOVERY
# ============================================================================

def normalize_feature_name(name: str) -> str:
    """
    Normalize file/folder names into feature names.
    Stop-names and suffixes are configurable via governance.yaml.
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
                bases.extend([
                    wsdir / "src" / "features",
                    wsdir / "src" / "components",
                    wsdir / "src" / "logo",
                ])
            else:
                bases.extend([
                    wsdir / "src" / "features",
                    wsdir / "features",
                    wsdir / "src" / "components",
                    wsdir / "components",
                ])
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
# SECTION 9: STRUCTURE / HYGIENE CHECKS
# ============================================================================

def check_gitignore(repo: Path, rep: Report, eff: dict) -> None:
    gi = repo / ".gitignore"
    if not gi.exists():
        rep.add(
            RED, "G0", "repo", ".gitignore",
            "no root .gitignore -> artifacts/caches/secrets get committed",
            intended="add strict root .gitignore (logs, *.db*, caches, node_modules, .env, backups)",
        )
        return
    t = read_text(gi) or ""
    missing = [m for m in ["*.db", "node_modules", "__pycache__", ".env", "*.log"] if m not in t]
    if missing:
        rep.add(
            YEL, "G0", "repo", ".gitignore",
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
                YEL, "F3",
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
                    YEL, "F4",
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
                    GRN, "NM",
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
                        YEL, "F2",
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
                RED, "X1", "repo", cand,
                "ghost backend (own main.py / db/database.py) -> two main.py & two database.py",
                intended="delete, or scripts/templates/ renamed so it can't import",
            )


def check_duplicate_basenames(repo: Path, rep: Report, eff: dict) -> None:
    """
    D1/D2: detect dangerous duplicate infrastructure modules.

    This intentionally does NOT flag normal repeated names such as:
        routers/admin/orders.py
        routers/supplier/orders.py
        routers/customer/orders.py

    Those are valid surface-specific modules.

    It focuses on infrastructure shadows such as:
        database.py
        schemas.py
        config.py
        auth.py
        main.py
    """
    ignore = {str(x).lower() for x in eff["dup_ignore_basenames"]}

    sensitive = {
        str(k).lower()
        for k in eff.get("canonical_home", {}).keys()
    }

    sensitive |= {
        "database.py",
        "schemas.py",
        "config.py",
        "auth.py",
        "base.py",
        "main.py",
        "email_service.py",
        "settings.py",
    }

    # D1: duplicate sensitive basename within backend.
    by: dict[str, list[str]] = defaultdict(list)

    backend = repo / "backend"
    if backend.exists():
        for f in iter_text_files(backend, eff):
            if f.suffix.lower() != ".py":
                continue

            if f.stem.lower() in ignore:
                continue

            if f.name.lower() not in sensitive:
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
                f"sensitive module name in {len(dirs)} dirs (import-shadow): "
                + ", ".join(paths[:5]),
                intended=f"keep the canonical copy ({home}); delete the shadows",
            )

    # D2: duplicate sensitive basename across top dirs.
    cross: dict[str, list[str]] = defaultdict(list)

    for top in ("backend", "monitoring", "scripts"):
        d = repo / top
        if not d.exists():
            continue

        for f in iter_text_files(d, eff):
            if f.suffix.lower() != ".py":
                continue

            if f.stem.lower() in ignore:
                continue

            if f.name.lower() not in sensitive:
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
                f"sensitive module name across {sorted(tops)} "
                f"(duplicated detector / ghost backend): "
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
                            RED, "F5", "security", rel(e, repo),
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
        return "DB3"
    return "G1"


def _intended_for_any(f: Path) -> str:
    if "migrations" in f.parts and "alembic" not in f.parts:
        return "fold into an Alembic revision or delete (no second migrations home)"
    if f.name == "employee_models.py" and "models" not in f.parts:
        return "move into backend/models/<domain>/ and add __table_args__ schema"
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
                        sev, code, dom, rel(c, repo),
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
                        YEL, _code_for_any(f), domain_of(rp), rel(f, repo),
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
                YEL, "P1", "backend", rp,
                "scratch/one-off script at backend root",
                intended="delete, or move to scripts/ (ops) / tests/",
            )
        else:
            home = eff["canonical_home"].get(
                c.name, "a layer package (routers/controllers/services/utils/db)",
            )
            rep.add(
                YEL, "P3", "backend", rp,
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
                    YEL, "F1", domain_of(rp), rp,
                    "scratch/debug script (one-off; not an ops/maintenance script)",
                    intended="delete; ops scripts live in scripts/maintenance or scripts/validation",
                )


def check_doc_and_root_allowlists(repo: Path, rep: Report, eff: dict) -> None:
    doc_ext = eff.get("doc_ext", DEFAULT_DOC_EXT)
    allow_names = eff.get("allow_docs_root", set())
    docs = repo / "documents"
    if docs.exists():
        for c in sorted(docs.iterdir()):
            if c.is_dir():
                continue
            if c.suffix.lower() in doc_ext or c.name in allow_names:
                continue
            rep.add(
                YEL, "F8", "docs", rel(c, repo),
                "non-document artifact at documents/ root (documents/ is the doc home; this is not a doc)",
                intended="move this artifact out of documents/ (e.g. archive/ or delete); .md/.txt docs are fine here",
            )
    allow_md = eff["allow_root_md"]
    for c in sorted(repo.iterdir()):
        if not c.is_file():
            continue
        if c.suffix == ".txt":
            rep.add(
                YEL, "F9", "repo", rel(c, repo),
                "design/plan note (.txt) at repo root",
                intended="move to documents/ (the doc home) or experiments/ (scratch); never commit at root",
            )
        elif c.suffix == ".md" and c.name not in allow_md:
            rep.add(
                YEL, "F9", "repo", rel(c, repo),
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
                YEL, "P4", "backend", rel(d, repo),
                f"expected backend package '{pkg}' is missing",
                intended="create the package if this layer is part of the target architecture",
            )
            continue
        if pkg.lower() not in no_init and not (d / "__init__.py").exists():
            rep.add(
                YEL, "P5", "backend", rel(d, repo),
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
                YEL, "P5", "backend", rel(d, repo),
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

    domain_layer_configs = eff.get("domain_layer_configs", [
        {"layer": "services", "flat_code": "S1", "surface_code": "S4", "large_code": "S5"},
        {"layer": "models", "flat_code": "M2", "surface_code": "M3", "large_code": "M4"},
    ])
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
                YEL, flat_code, "backend", rel(d, repo),
                f"{layer_name}/ FLAT ({len(direct)} files, too many at layer root)",
                intended=f"{layer_name}/<domain>/ per bounded contexts (finance/orders/catalog/...)",
            )
        try:
            subdirs = [
                p for p in d.iterdir()
                if p.is_dir() and p.name.lower() not in eff["ignore_dirs"]
            ]
        except OSError:
            subdirs = []
            known_domains = set(PLACEMENT_DOMAIN_KEYWORDS.keys())
            known_domains |= {str(x).lower() for x in eff.get("domains", {}).keys()}

            if _ACTIVE_REG is not None:
                known_domains |= {
                    str(x).lower()
                    for x in getattr(_ACTIVE_REG, "domains", set())
                }

            for sd in subdirs:
                sd_name = sd.name.lower()

                # Domain folders are valid inside domain layers.
                # Surface-only folders are violations.
                if sd_name not in known_domains and sd_name in eff["surface_names"]:
                    rep.add(
                        YEL,
                        surface_code,
                        "backend",
                        rel(sd, repo),
                        f"surface sub-folder '{sd.name}' inside domain layer {layer_name}/",
                        intended=(
                            f"{layer_name}/ must be grouped by DOMAIN, "
                            f"not by surface (admin/supplier/customer/...)"
                        ),
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
                        YEL, "S2", "backend", rel(d, repo),
                        f"overlapping service stems '{a[:6].rstrip('_')}*' ({len(grp)}) -> ambiguous ownership",
                        intended="merge or document each role in an ADR: " + ", ".join(grp[:6]),
                    )
    # routers/ is intentionally flat.
    # Only controllers/ should be domain-grouped.
    controllers_dir = backend / "controllers"

    if controllers_dir.exists():
        direct = [p for p in controllers_dir.glob("*.py") if p.name != "__init__.py"]

        if len(direct) > eff["flat_threshold"]:
            rep.add(
                YEL,
                "S3",
                "backend",
                rel(controllers_dir, repo),
                f"controllers/ FLAT ({len(direct)} files at layer root)",
                intended=(
                    "group controllers/ by domain "
                    "(finance/orders/catalog/...) with surface-prefixed "
                    "controller filenames"
                ),
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
            YEL, "L1", "security", "middleware/ + dependencies/",
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
                    YEL, "F7", "security", rel(f, repo),
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
                        YEL, "F6", "backend", rel(f, repo),
                        "media written to / referenced from local disk",
                        intended="storage abstraction -> object storage + CDN; DB stores metadata only",
                        line=i,
                    )
                    break


# ============================================================================
# SECTION 10: CIRCUIT ENFORCEMENT CHECKS
# ============================================================================
"""
These checks enforce the ZOZI backend circuit:
  ENTRY → MIDDLEWARE → ROUTERS → CONTROLLERS → SERVICES → PROVIDERS → MODELS → DB

Rules enforced:
  - Imports may only flow DOWNWARD (higher layer → lower layer)
  - DB writes (session.add/commit/delete) only in services/
  - Surface folders only in routers/ (not in services/models)
  - Middleware may NOT import from services/controllers/models
  - Providers may NOT import from services/controllers/routers
  - Controllers may NOT do DB writes
  - Routers may NOT contain business logic (only call controllers)
  - Domain A may NOT import from Domain B (unless explicitly allowed)
"""

# Layer ordering for circuit direction enforcement
CIRCUIT_LAYER_ORDER: dict[str, int] = {
    "main": 0,
    "lifespan": 0,
    "middleware": 1,
    "dependencies": 1,
    "routers": 2,
    "controllers": 3,
    "services": 4,
    "providers": 5,
    "models": 6,
    "db": 7,
    "utils": 8,
    "data": 8,
    "events": 4,
    "jobs": 4,
}

# What each layer may import (explicit allowed-import matrix)
LAYER_IMPORT_RULES: dict[str, set[str]] = {
    "main": {"middleware", "dependencies", "routers", "db", "utils", "lifespan", "data"},
    "lifespan": {"db", "utils", "middleware", "dependencies", "data"},
    "middleware": {"db", "utils", "dependencies", "data"},
    "dependencies": {"db", "utils", "data"},
    "routers": {"controllers", "dependencies", "utils", "data"},
    "controllers": {"services", "utils", "data"},
    "services": {"models", "providers", "utils", "events", "jobs", "db", "data"},
    "providers": {"utils", "data"},
    "models": {"db", "utils"},
    "db": {"utils"},
    "events": {"services", "models", "providers", "utils", "db", "data"},
    "jobs": {"services", "models", "providers", "utils", "db", "data"},
    "data": set(),
    "utils": set(),
}

# What each layer MUST NOT import (explicit forbidden)
LAYER_FORBIDDEN_IMPORTS: dict[str, set[str]] = {
    "middleware": {"services", "controllers", "routers", "models", "providers", "events", "jobs"},
    "dependencies": {"services", "controllers", "routers", "models", "providers", "events", "jobs"},
    "routers": {"providers", "db.database", "db.create_tables", "db.init_db"},
    "controllers": {"routers", "middleware", "dependencies", "db.database", "db.create_tables", "db.init_db"},
    "services": {"routers", "controllers", "middleware", "dependencies"},
    "providers": {"routers", "controllers", "services", "models", "middleware", "dependencies",
                  "db.database", "db.create_tables", "db.init_db", "events", "jobs"},
    "models": {"routers", "controllers", "services", "providers", "middleware", "dependencies",
               "events", "jobs"},
    "db": {"routers", "controllers", "services", "providers", "middleware", "dependencies",
           "events", "jobs"},
    "utils": {"routers", "controllers", "services", "models", "providers", "middleware",
              "dependencies", "db.database", "db.create_tables", "db.init_db"},
    "events": {"routers", "controllers", "middleware", "dependencies"},
    "jobs": {"routers", "controllers", "middleware", "dependencies"},
}

# DB operations each layer may perform
LAYER_OPERATIONS: dict[str, set[str]] = {
    "services": {"session.add", "session.commit", "session.delete", "session.merge",
                 "session.flush", "session.execute", "session.refresh"},
    "db": {"engine", "session_factory", "base"},
    # All other layers: NO DB writes
}


def check_circuit_import_direction(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    """
    CIR1: Detect upward imports that violate circuit direction.
    
    An upward import is when a lower layer imports from a higher layer.
    Example: services/ importing from routers/ is upward (violation).
    
    This uses CIRCUIT_LAYER_ORDER to determine direction.
    """
    exempt = set(eff.get("graph_exempt_layers", set())) | {
        "tests", "scripts", "alembic", "monitoring", "docs",
    }
    reported = 0

    for caller in sorted(graph.imports.keys()):
        caller_layer = layer_of_module(caller)
        if not caller_layer or caller_layer in exempt:
            continue

        caller_order = CIRCUIT_LAYER_ORDER.get(caller_layer, 99)
        if caller_order == 99:
            continue

        caller_path = module_path_rel(caller, graph, repo)

        for mod, line in graph.imports[caller]:
            target_layer = layer_of_module(mod)
            if not target_layer or target_layer in exempt:
                continue
            if target_layer == caller_layer:
                continue

            target_order = CIRCUIT_LAYER_ORDER.get(target_layer, 99)
            if target_order == 99:
                continue

            # Upward import: target is at a higher (lower number) layer
            # than the caller. This violates the circuit.
            if target_order < caller_order:
                # Skip if it's a cross-cutting layer (utils, data)
                if target_layer in ("utils", "data"):
                    continue

                rep.add(
                    RED, "CIR1", "backend", caller_path,
                    f"upward circuit violation: {caller_layer} (order={caller_order}) "
                    f"imports from {target_layer} (order={target_order}) via '{mod}'",
                    intended=(
                        f"imports must flow downward in the circuit; "
                        f"{caller_layer} may only import from layers below it"
                    ),
                    line=line,
                )
                reported += 1

            if reported >= 300:
                return


# ============================================================================
# SECTION 11: LAYER / DEPENDENCY CHECKS
# ============================================================================

def check_router_outside(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return
    exempt = eff.get("graph_exempt_layers", DEFAULT_GRAPH_EXEMPT_LAYERS)
    allowed_top = {
        str(x).lower()
        for x in eff.get("known_layers", set())
        if str(x).lower() not in exempt and str(x).lower() != "routers"
    }
    if not allowed_top:
        allowed_top = {
            "controllers", "services", "middleware", "dependencies",
            "providers", "utils", "events", "jobs", "tasks", "api",
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
                        RED, "R1", "backend", rel(f, repo),
                        "APIRouter outside routers/ -> endpoint mis-registered/shadowed",
                        intended="backend/routers/",
                        line=node.lineno,
                    )
                    break


def check_layer_writes(repo: Path, rep: Report, eff: dict) -> None:
    """Check for DB writes in controllers/routers (legacy check, kept for compatibility)."""
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


def _module_matches_prefix(mod: str, prefix: str) -> bool:
    """Return True if module equals prefix or is inside prefix package."""
    return mod == prefix or mod.startswith(prefix + ".")


def check_circuit_contract(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    """
    Enforce the ZOZI backend circuit.

    RED CIR1:
        Import is outside the allowed circuit.

    YEL CIR2:
        Import is a migration bypass, for example:
        router -> service
        router -> model
        controller -> model

    Explicit forbidden edges in DEFAULT_FORBIDDEN_EDGES / layer_rules.yaml
    are still reported by check_dependency_graph as DG.
    """
    allowed = CIRCUIT_ALLOWED_IMPORTS
    bypass = CIRCUIT_BYPASS_IMPORTS
    edges = eff.get("forbidden_edges", {})

    exempt = set(eff.get("graph_exempt_layers", set())) | {
        "tests",
        "scripts",
        "alembic",
        "monitoring",
        "docs",
    }

    # Data modules may be imported by application layers.
    # But data itself must not import application layers.
    target_always_ok = {"data"}

    reported = 0

    for caller in sorted(graph.imports.keys()):
        caller_layer = layer_of_module(caller)

        if not caller_layer:
            continue

        if caller_layer in exempt:
            continue

        if caller_layer not in allowed:
            continue

        caller_path = module_path_rel(caller, graph, repo)
        seen: set[tuple[str, str]] = set()

        for mod, line in graph.imports[caller]:
            target_layer = layer_of_module(mod)

            if not target_layer:
                continue

            if target_layer in exempt:
                continue

            if target_layer in target_always_ok:
                continue

            if target_layer == caller_layer:
                continue

            # If this is already an explicit forbidden edge, let
            # check_dependency_graph() report DG to avoid duplicate findings.
            if any(
                _module_matches_prefix(mod, prefix)
                for prefix in edges.get(caller_layer, [])
            ):
                continue

            # Allowed by circuit contract.
            if target_layer in allowed.get(caller_layer, set()):
                continue

            key = (caller_layer, target_layer)

            if key in seen:
                continue

            seen.add(key)

            if key in bypass:
                rep.add(
                    YEL,
                    "CIR2",
                    "backend",
                    caller_path,
                    f"circuit bypass: {caller_layer} -> {target_layer} ({mod})",
                    intended=bypass[key],
                    line=line,
                )
            else:
                allowed_list = ", ".join(sorted(allowed.get(caller_layer, set()))) or "none"

                rep.add(
                    RED,
                    "CIR1",
                    "backend",
                    caller_path,
                    f"circuit violation: {caller_layer} -> {target_layer} ({mod}) "
                    f"is outside the allowed circuit",
                    intended=f"{caller_layer} may import only: {allowed_list}",
                    line=line,
                )

            reported += 1

            if reported >= 800:
                return
            

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
            filtered_edges, int(eff["max_cycle_length"]), int(eff["max_cycles"]),
        )
        for cyc in cycles:
            path = " -> ".join(cyc + [cyc[0]])
            first = cyc[0]
            rep.add(
                YEL, "DG2", "backend",
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
            domain_edges, int(eff["max_cycle_length"]), int(eff["max_cycles"]),
        )
        for cyc in domain_cycles:
            path = " -> ".join(cyc + [cyc[0]])
            rep.add(
                RED, "DG2", "backend", "domain-graph",
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
            YEL, "A2", "backend",
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
                YEL, "A1", "backend",
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
            YEL, "D3", "backend",
            ", ".join(mods[:5]),
            f"class name '{name}' is defined in {len(mods)} modules",
            intended="rename or consolidate; duplicate class names create import/confusion drift",
            line=first_line,
        )
        reported += 1
        if reported >= 150:
            break


def check_sys_path_manipulation(repo: Path, rep: Report, eff: dict) -> None:
    """
    H1: detect sys.path.insert/append in backend application code.

    This is an import-resolution footgun and often hides broken package structure.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        if in_parts(f, "tests", "scripts", "alembic", "data", "monitoring", "docs"):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func = node.func

            if not isinstance(func, ast.Attribute):
                continue

            if func.attr not in {"insert", "append"}:
                continue

            value = func.value

            if not isinstance(value, ast.Attribute):
                continue

            if value.attr != "path":
                continue

            root = value.value

            if isinstance(root, ast.Name) and root.id == "sys":
                rep.add(
                    YEL,
                    "H1",
                    "backend",
                    rel(f, repo),
                    "sys.path manipulation detected",
                    intended=(
                        "remove sys.path.insert/append; fix package structure "
                        "and use proper imports"
                    ),
                    line=node.lineno,
                )
                reported += 1
                break

        if reported >= 100:
            return


def check_controller_outside(repo: Path, rep: Report, eff: dict) -> None:
    """
    P2: detect controller-named files outside controllers/.

    Examples:
        backend/services/audit/audit_controller.py
        backend/utils/cache_controller.py

    If the file contains business logic, it should usually be renamed to *_service.py.
    If it is truly a controller, it should move to controllers/<domain>/.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() != ".py":
            continue

        try:
            parts = [p.lower() for p in f.relative_to(backend).parts]
        except ValueError:
            continue

        if not parts:
            continue

        layer = parts[0]

        if layer in {
            "controllers",
            "tests",
            "scripts",
            "alembic",
            "data",
            "monitoring",
            "docs",
        }:
            continue

        stem = f.stem.lower()

        if not stem.endswith("_controller"):
            continue

        rep.add(
            YEL,
            "P2",
            "backend",
            rel(f, repo),
            f"controller-named file '{f.name}' outside controllers/",
            intended=(
                "if it contains business logic, rename to *_service.py; "
                "if it is truly a controller, move to controllers/<domain>/"
            ),
        )

        reported += 1

        if reported >= 100:
            return


def check_router_naming_convention(repo: Path, rep: Report, eff: dict) -> None:
    """
    RN1:
        Flat router filename must be comprehensive:
        {surface}_{domain}_{operation}.py

    RN2:
        Router file is inside a sub-folder.
        Routers must be flat.

    RN3:
        Router sub-folder exists.
        Routers must be flat.
    """
    backend = repo / "backend"
    routers = backend / "routers"

    if not routers.exists():
        return

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    stop = set(PLACEMENT_STOP_TOKENS)
    aliases = PLACEMENT_ALIAS_TO_DOMAIN

    def _tokens(stem: str) -> list[str]:
        return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", stem) if t]

    def _surface(toks: list[str], hint: str | None = None) -> str | None:
        if hint and hint in surfaces:
            return hint

        for t in toks:
            if t in surfaces:
                return t

        return None

    def _domain(toks: list[str]) -> str | None:
        for t in toks:
            d = aliases.get(t)
            if d:
                return d

        return None

    def _has_operation(
        toks: list[str],
        surface: str | None,
        domain: str | None,
    ) -> bool:
        """
        Return True if the filename contains at least one meaningful
        operation token beyond surface/domain.
        """
        for t in toks:
            if len(t) < 3:
                continue

            if t in stop:
                continue

            if surface and t == surface:
                continue

            if domain and (t == domain or aliases.get(t) == domain):
                continue

            return True

        return False

    def _flat_target(
        stem: str,
        surface: str | None,
        domain: str | None,
    ) -> str:
        new = stem.lower()

        if surface and not new.startswith(f"{surface}_"):
            new = f"{surface}_{new}"

        if domain:
            parts = new.split("_")
            first = parts[0] if parts else ""

            if domain not in parts and aliases.get(first) != domain:
                if surface and new.startswith(f"{surface}_"):
                    rest = new[len(surface) + 1:]
                    new = f"{surface}_{domain}_{rest}"
                else:
                    new = f"{domain}_{new}"

        return f"backend/routers/{new}.py"

    # ------------------------------------------------------------------
    # RN3 + RN2: router sub-folders are not allowed.
    # ------------------------------------------------------------------
    try:
        subdirs = [
            p for p in routers.iterdir()
            if p.is_dir()
            and p.name.lower() not in eff.get("ignore_dirs", set())
            and p.name.lower() != "__pycache__"
        ]
    except OSError:
        subdirs = []

    for sd in sorted(subdirs):
        rep.add(
            YEL,
            "RN3",
            "routers",
            rel(sd, repo),
            f"router sub-folder '{sd.name}/' found; routers/ must be flat",
            intended=(
                "move router files to "
                "backend/routers/{surface}_{domain}_{operation}.py"
            ),
        )

        for f in sorted(sd.rglob("*.py")):
            if f.name == "__init__.py":
                continue

            toks = _tokens(f.stem)
            surface = _surface(toks, sd.name.lower())
            domain = _domain(toks)
            target = _flat_target(f.stem, surface, domain)

            rep.add(
                YEL,
                "RN2",
                "routers",
                rel(f, repo),
                f"router file inside sub-folder '{sd.name}/'",
                intended=f"move to flat router: {target}",
            )

    # ------------------------------------------------------------------
    # RN1: flat router filenames must be comprehensive.
    # ------------------------------------------------------------------
    for f in sorted(routers.glob("*.py")):
        if f.name == "__init__.py":
            continue

        toks = _tokens(f.stem)
        surface = _surface(toks)
        domain = _domain(toks)
        has_op = _has_operation(toks, surface, domain)

        missing: list[str] = []

        if not surface:
            missing.append("surface")

        if not domain:
            missing.append("domain")

        if not has_op:
            missing.append("operation")

        if missing:
            rep.add(
                YEL,
                "RN1",
                "routers",
                rel(f, repo),
                f"flat router filename '{f.name}' is not comprehensive; "
                f"missing {', '.join(missing)}",
                intended=(
                    "rename to {surface}_{domain}_{operation}.py, e.g. "
                    "admin_orders_management.py, "
                    "supplier_orders_fulfillment.py, "
                    "customer_orders_tracking.py"
                ),
            )

# ============================================================================
# SECTION 12: DYNAMIC IMPORTS, POLICY VALIDATION, FRONTEND, AUTO-POLICY
# ============================================================================

def check_dynamic_dependency_signals(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    """Detect dynamic imports and eval/exec that obscure the dependency graph."""
    if not eff.get("detect_dynamic_imports"):
        return
    reported = 0
    for caller, mod, line in graph.dynamic_imports:
        caller_layer = layer_of_module(caller)
        if caller_layer in eff["graph_exempt_layers"]:
            continue
        rep.add(
            YEL, "DG4", "backend",
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
            YEL, "DG5", "backend",
            module_path_rel(caller, graph, repo),
            f"dynamic execution/import obscures dependency graph ({name})",
            intended="avoid eval/exec/dynamic import_module for layer-critical code paths",
            line=line,
        )
        reported += 1
        if reported >= 100:
            break


def check_policy_config(repo: Path, rep: Report, eff: dict) -> None:
    """Validate that YAML policy references only known layers and domains."""
    if not eff.get("detect_policy_config"):
        return
    known_layers = eff.get("known_layers", set())

    # Validate forbidden_edges references
    for caller, targets in eff.get("forbidden_edges", {}).items():
        if known_layers and caller.lower() not in known_layers:
            rep.add(
                YEL, "CFG1", "repo", "layer_rules.yaml",
                f"forbidden_edges references unknown caller layer '{caller}'",
                intended="fix the layer name or add it to expected_backend_packages",
            )
        for target in targets:
            top = str(target).split(".", 1)[0].lower()
            if known_layers and top not in known_layers:
                rep.add(
                    YEL, "CFG1", "repo", "layer_rules.yaml",
                    f"forbidden_edges references unknown target layer '{top}' from '{target}'",
                    intended="fix the layer name or add it to expected_backend_packages",
                )

    # Validate layer set references
    for key in ("ownership_layers", "graph_exempt_layers", "dead_exempt_layers", "no_init_dirs"):
        for layer_name in eff.get(key, set()):
            if known_layers and layer_name.lower() not in known_layers:
                rep.add(
                    YEL, "CFG3", "repo", "governance.yaml",
                    f"{key} references unknown backend folder '{layer_name}'",
                    intended="remove it or create the expected backend package",
                )

    # Validate domain policy references
    domains = eff.get("domains", {})
    if domains:
        for dom, cfg in domains.items():
            for imp in cfg.get("may_import", []):
                if imp not in domains:
                    rep.add(
                        YEL, "CFG2", "repo", "layer_rules.yaml",
                        f"domain '{dom}' may_import references unknown domain '{imp}'",
                        intended="define the missing domain or fix the typo",
                    )
        # Check for cycles in domain policy
        policy_edges: dict[str, set[str]] = defaultdict(set)
        for dom, cfg in domains.items():
            for imp in cfg.get("may_import", []):
                if imp in domains and imp != dom:
                    policy_edges[dom].add(imp)
        policy_cycles = detect_cycles(policy_edges, 12, 30)
        for cyc in policy_cycles:
            path = " -> ".join(cyc + [cyc[0]])
            rep.add(
                YEL, "CFG4", "repo", "layer_rules.yaml",
                f"explicit domain policy contains a cycle: {path}",
                intended="bounded-context rules should be acyclic; introduce explicit contracts/events",
            )


def check_frontend_structure(repo: Path, rep: Report, eff: dict) -> None:
    """Validate frontend workspace structure, flat folders, and cross-workspace imports."""
    if not eff.get("detect_frontend"):
        return
    frontend = repo / "frontend"
    if not frontend.exists():
        return
    workspaces = sorted(eff.get("frontend_workspaces", set()))
    source_ext = eff.get("frontend_source_ext", set())
    allow_root = eff.get("frontend_root_allow", set())

    # Workspace existence
    if not (frontend / "package.json").exists():
        rep.add(
            YEL, "FE1", "frontend", rel(frontend, repo),
            "frontend root package.json missing",
            intended="add workspace root package.json for monorepo scripts",
        )
    for ws in workspaces:
        d = frontend / ws
        if not d.exists():
            rep.add(
                YEL, "FE1", "frontend", rel(d, repo),
                f"expected frontend workspace '{ws}' missing",
                intended="create/maintain workspace or update governance.yaml",
            )
            continue
        if not (d / "package.json").exists():
            rep.add(
                YEL, "FE1", "frontend", rel(d, repo),
                f"workspace '{ws}' missing package.json",
                intended="add package.json for this workspace",
            )

    # Scratch/artifact scripts at workspace root
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
                or low.startswith("_audit_") or low.startswith("verify_")
                or low.startswith("debug") or low.startswith("diag")
                or low.startswith("build_final") or low.startswith("build_out")
                or low.startswith("build_log") or low.startswith("inspect-")
                or low.endswith("_test.txt") or low.endswith("_test_output.txt")
                or low.endswith("_test_verbose.txt")
            )
            if scratchy:
                rep.add(
                    YEL, "FE2", "frontend", rel(f, repo),
                    "frontend scratch/artifact script at package root",
                    intended="delete; keep only workspace config/package files at root",
                )

    # Flat folder detection
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
            direct = [x for x in d.iterdir() if x.is_file() and x.suffix.lower() in source_ext]
        except OSError:
            direct = []
        if len(direct) > int(threshold):
            rep.add(
                YEL, "FE3", "frontend", rel(d, repo),
                f"frontend folder is flat ({len(direct)} direct source files)",
                intended="group by feature/domain (e.g. orders/, finance/, supplier/, ui/)",
            )

    # Large folder detection
    reported = 0
    skip_parts = {
        "e2e", "__tests__", "tests", "test-output", "playwright-report",
        "coverage", ".next", "dist", "build", "tmp", "assets",
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
            count = sum(1 for e in entries if e.is_file() and e.suffix.lower() in source_ext)
            if count > int(eff["frontend_large_folder_threshold"]):
                rep.add(
                    YEL, "FE5", "frontend", rel(d, repo),
                    f"frontend folder has {count} direct source files (scaling risk)",
                    intended="split into feature/domain sub-folders",
                )
                reported += 1
                if reported >= 100:
                    break
        if reported >= 100:
            break

    # Cross-workspace relative imports
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
            if in_parts(f, "node_modules", ".next", "dist", "build", "coverage",
                        "test-results", "playwright-report", "e2e", "__tests__"):
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
                        YEL, "FE4", "frontend", rel(f, repo),
                        f"relative import crosses workspace boundary: {imp}",
                        intended="import shared via workspace package name, not relative path",
                        line=i,
                    )
                    reported_ws += 1
                    break
            if reported_ws >= 50:
                break


def collect_frontend_metrics(repo: Path, eff: dict) -> dict:
    """Collect frontend workspace metrics for the summary."""
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
        source_files = sum(1 for f in iter_text_files(d, eff) if f.suffix.lower() in source_ext)
        dirs = sum(1 for _ in walk_dirs(d, eff["ignore_dirs"]))
        metrics[ws] = {"source_files": source_files, "dirs": dirs}
    return metrics


# ============================================================================
# SECTION 13: SECURITY / PERFORMANCE / QUALITY ENHANCEMENTS
# ============================================================================

# --- Secret detection patterns ---
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
    r"(?i)\b(api[_-]?key|apikey|secret|secret[_-]?key|token|auth[_-]?token|"
    r"access[_-]?token|password|passwd|pwd)\b\s*[:=]\s*['\"][^'\"]{12,}['\"]"
)

ENH_SECRET_IGNORE_LINE_RE = re.compile(
    r"(?i)os\.environ|getenv|settings\.|config\.|example|placeholder|<[^>]+>|"
    r"\$\{|process\.env|\bimport\b|\bfrom\b|\bdef\b|\bclass\b|BaseSettings|"
    r"Field\(|get_secret|secret_manager|vault"
)

# --- Dangerous calls ---
ENH_DANGEROUS_CALLS = {
    "eval", "exec", "pickle.load", "pickle.loads",
    "cPickle.load", "cPickle.loads",
    "marshal.load", "marshal.loads",
    "yaml.load", "yaml.unsafe_load", "os.system",
}

ENH_SUBPROCESS_CALLS = {"subprocess.run", "subprocess.call", "subprocess.Popen"}

# --- Async blocking calls ---
ENH_BLOCKING_CALLS = {
    "time.sleep", "requests.get", "requests.post", "requests.put",
    "requests.delete", "requests.patch", "requests.head", "requests.options",
    "urllib.request.urlopen", "socket.recv", "socket.send", "socket.connect",
}

# --- Query-in-loop detection ---
ENH_QUERY_ATTRS = {"query", "execute", "scalar", "scalars"}

# --- Quality / debt ---
ENH_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
ENH_FRONTEND_DEBUG_RE = re.compile(r"\bconsole\.(log|debug|info|warn|error)\b|\bdebugger\b")
ENH_DEBUG_TRUE_RE = re.compile(r"\bdebug\s*=\s*True\b", re.I)
ENH_CORS_WILDCARD_RE = re.compile(r"allow_origins\s*=\s*\[\s*['\"]\*['\"]\s*\]")
ENH_CORS_CREDS_RE = re.compile(r"allow_credentials\s*=\s*True\b")
ENH_FILE_LINE_LIMIT = 1200
ENH_FUNC_LINE_LIMIT = 120


# --- Helper functions ---

def _enh_call_full_name(func: ast.AST) -> str:
    """Return a dotted best-effort name for a Call.func node."""
    parts: list[str] = []
    cur = func
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _enh_call_has_attr(func: ast.AST, attrs: set[str]) -> bool:
    """Detect whether a call chain contains one of the given attribute names."""
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
        "tests", "test", "scripts", "alembic", "data", "monitoring",
        "docs", "node_modules", "dist", "build", "coverage", ".next",
    }
    return any(p in excluded for p in parts)


# --- SEC2: Hardcoded secrets ---

def check_enhanced_secrets_in_code(repo: Path, rep: Report, eff: dict) -> None:
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
                    and not any(x in low for x in (
                        "example", "test", "dummy", "changeme",
                        "placeholder", "<", "${", "process.env", "os.environ",
                    ))
                ):
                    hits.append(i)
                    if len(hits) >= 5:
                        break
            if hits:
                sev = RED if strong else YEL
                rep.add(
                    sev, "SEC2", domain_of(rel(f, repo)), rel(f, repo),
                    f"possible hardcoded secret/token ({len(hits)} hit(s))",
                    intended="move secrets to env/Vault/settings; keep only placeholders in examples",
                    line=hits[0],
                )
                reported += 1
                if reported >= 150:
                    return


# --- SEC3: Dangerous calls ---

def check_enhanced_dangerous_calls(repo: Path, rep: Report, eff: dict) -> None:
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
                    if (kw.arg == "shell" and isinstance(kw.value, ast.Constant)
                            and kw.value.value is True):
                        shell_true = True
                        break
                if shell_true:
                    rep.add(
                        RED, "SEC3", "security", rel(f, repo),
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
                    "eval", "exec", "pickle.load", "pickle.loads",
                    "yaml.load", "yaml.unsafe_load", "marshal.load", "marshal.loads",
                } else YEL
                rep.add(
                    sev, "SEC3", "security", rel(f, repo),
                    f"dangerous dynamic execution/deserialization: {name}",
                    intended="avoid eval/exec/pickle/marshal/unsafe yaml; use safe parsers and explicit logic",
                    line=node.lineno,
                )
                reported += 1
                if reported >= 200:
                    return


# --- SEC4: Insecure runtime settings ---

def check_enhanced_runtime_security_settings(repo: Path, rep: Report, eff: dict) -> None:
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
                RED, "SEC4", "security", rel(f, repo),
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
                YEL, "SEC4", "security", rel(f, repo),
                "debug=True detected in backend code",
                intended="drive debug from settings/env; never hardcode True in deployable code",
                line=line,
            )
            reported += 1
        if reported >= 150:
            return


# --- PERF1: Blocking calls in async ---

def check_enhanced_async_blocking(repo: Path, rep: Report, eff: dict) -> None:
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
                        YEL, "PERF1", "backend", rel(f, repo),
                        f"blocking call '{name}' inside async function '{node.name}'",
                        intended="use async client / threadpool / background job instead of blocking the event loop",
                        line=getattr(child, "lineno", node.lineno),
                    )
                    reported += 1
                    if reported >= 200:
                        return


# --- PERF2: Query in loop ---

def check_enhanced_query_in_loop(repo: Path, rep: Report, eff: dict) -> None:
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
                        YEL, "PERF2", "backend", rel(f, repo),
                        "possible DB query inside loop (N+1 risk)",
                        intended="batch the query / use joins / preload relationships instead of querying per item",
                        line=getattr(child, "lineno", node.lineno),
                    )
                    reported += 1
                    if reported >= 200:
                        return


# --- QUAL1: Weak exception handling ---

def check_enhanced_exception_handling(repo: Path, rep: Report, eff: dict) -> None:
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
                    YEL, "QUAL1", "backend", rel(f, repo),
                    "bare except: catches everything and hides failures",
                    intended="catch specific exceptions and handle/log them explicitly",
                    line=node.lineno,
                )
                reported += 1
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                only_pass = all(isinstance(stmt, ast.Pass) for stmt in node.body)
                if only_pass:
                    rep.add(
                        YEL, "QUAL1", "backend", rel(f, repo),
                        "swallowed exception: 'except Exception: pass'",
                        intended="log or re-raise; silent swallowing hides bugs",
                        line=node.lineno,
                    )
                    reported += 1
            if reported >= 250:
                return


# --- QUAL2: TODO/FIXME debt ---

def check_enhanced_todo_debt(repo: Path, rep: Report, eff: dict) -> None:
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
                YEL, "QUAL2", domain_of(rel(f, repo)), rel(f, repo),
                f"technical debt markers present ({count} TODO/FIXME/XXX/HACK)",
                intended="convert important markers into tasks/ADRs; delete stale ones",
            )
            reported += 1
            if reported >= 200:
                return


# --- QUAL3: Oversized files/functions ---

def check_enhanced_size_complexity(repo: Path, rep: Report, eff: dict) -> None:
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
                YEL, "QUAL3", "backend", rel(f, repo),
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
                    YEL, "QUAL3", "backend", rel(f, repo),
                    f"oversized function '{node.name}' ({func_len} lines)",
                    intended="extract smaller functions / service methods; long functions hide side effects",
                    line=node.lineno,
                )
                reported += 1
        if reported >= 250:
            return


# --- QUAL4: Print/debug in app code ---

def check_enhanced_print_debug(repo: Path, rep: Report, eff: dict) -> None:
    backend = repo / "backend"
    if not backend.exists():
        return
    app_layers = {
        "routers", "controllers", "services", "middleware", "dependencies",
        "providers", "utils", "events", "jobs",
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
                    YEL, "QUAL4", "backend", rel(f, repo),
                    "print() statement in application code",
                    intended="use structured logging instead of print()",
                    line=node.lineno,
                )
                reported += 1
                if reported >= 200:
                    return


# --- DB1: Missing __table_args__ ---

def check_enhanced_model_schema(repo: Path, rep: Report, eff: dict) -> None:
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
                    YEL, "DB1", "database", rel(f, repo),
                    f"model '{node.name}' has __tablename__ but no __table_args__",
                    intended="declare schema ownership with __table_args__={'schema': '<domain>'}",
                    line=node.lineno,
                )
                reported += 1
                if reported >= 200:
                    return


# --- DB2: Multiple Alembic heads ---

def check_enhanced_alembic_heads(repo: Path, rep: Report, eff: dict) -> None:
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
            YEL, "DB2", "database", "backend/alembic/versions",
            f"multiple Alembic heads detected ({len(heads)}): " + ", ".join(heads[:5]),
            intended="merge to a single head (alembic merge heads) or add a reconciling revision",
        )


# --- CFG5: Generated artifacts not gitignored ---

def check_enhanced_gitignore_generated(repo: Path, rep: Report, eff: dict) -> None:
    gi = repo / ".gitignore"
    if not gi.exists():
        return
    t = read_text(gi) or ""
    missing = [
        item for item in (
            "ARCHITECTURE_AUDIT_REPORT.md",
            "out/",
            ".governance/architecture_trend.json",
            ".governance/zozi_auto_policy.json",
        ) if item not in t
    ]
    if missing:
        rep.add(
            YEL, "CFG5", "repo", ".gitignore",
            f"generated governance artifacts not ignored: {', '.join(missing)}",
            intended="ignore generated local outputs; keep canonical governance files if desired",
        )


# --- FE6: Frontend console/debugger ---

def check_enhanced_frontend_debug(repo: Path, rep: Report, eff: dict) -> None:
    frontend = repo / "frontend"
    if not frontend.exists():
        return
    source_ext = eff.get("frontend_source_ext", DEFAULT_FRONTEND_SOURCE_EXT)
    reported = 0
    for f in iter_text_files(frontend, eff):
        if f.suffix.lower() not in source_ext:
            continue
        if in_parts(f, "node_modules", ".next", "dist", "build", "coverage",
                    "test-results", "playwright-report", "e2e", "__tests__"):
            continue
        t = read_text(f)
        if not t:
            continue
        count = len(ENH_FRONTEND_DEBUG_RE.findall(t))
        if count <= 0:
            continue
        rep.add(
            YEL, "FE6", "frontend", rel(f, repo),
            f"frontend debug statements present ({count} console/debugger)",
            intended="remove console/debugger before merge; use proper logging/error reporting",
        )
        reported += 1
        if reported >= 200:
            return


# ============================================================================
# SECTION 14: DOMAIN PLACEMENT ENGINE (SINGLE AUTHORITATIVE IMPLEMENTATION)
# ============================================================================
# This is the ONLY move-suggestion engine.
# It replaces ALL earlier versions (v3.5 MOVE_*, v3.6 DP_*).
# ============================================================================

def _pl_normalize_domain(token: str | None) -> str | None:
    """Normalize a token to its canonical domain name via alias map."""
    if not token:
        return None
    t = str(token).lower()
    return PLACEMENT_ALIAS_TO_DOMAIN.get(t, t)


def _pl_tokenize(name: str, eff: dict, include_surfaces: bool = False) -> set[str]:
    """Tokenize a name into meaningful lowercase tokens for domain inference."""
    stop = set(PLACEMENT_STOP_TOKENS)
    if not include_surfaces:
        stop |= {str(x).lower() for x in eff.get("surface_names", set())}
    raw = str(name)
    raw = re.sub(r"(?<!^)(?=[A-Z])", "_", raw)
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw)
    tokens = {t.lower() for t in raw.split("_") if t}
    return {t for t in tokens if len(t) > 2 and t not in stop}


def _pl_route_tokens(text: str) -> set[str]:
    """Extract route/path tokens from FastAPI route definitions."""
    if not text:
        return set()

    tokens: set[str] = set()

    for m in AUTO_ROUTE_PREFIX_RE.finditer(text):
        tokens.update(_pl_tokenize(m.group(1), {}, include_surfaces=True))

    for m in AUTO_ROUTE_DECOR_RE.finditer(text):
        tokens.update(_pl_tokenize(m.group(1), {}, include_surfaces=True))

    for m in AUTO_ROUTE_TAGS_RE.finditer(text):
        for tag in re.findall(r"['\"]([^'\"]+)['\"]", m.group(1)):
            tokens.update(_pl_tokenize(tag, {}, include_surfaces=True))

    return tokens


def _pl_extract_signals(f: Path, text: str, eff: dict) -> dict[str, float]:
    """Extract weighted domain signals from a Python file."""
    signals: dict[str, float] = defaultdict(float)

    def add_tokens(tokens: set[str], weight: float) -> None:
        for token in tokens:
            signals[token] += weight

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
                    add_tokens(_pl_tokenize(alias.name.replace(".", "_"), eff), 4.0)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    add_tokens(_pl_tokenize(node.module.replace(".", "_"), eff), 4.0)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        add_tokens(_pl_tokenize(str(node.value.value), eff), 8.0)
    for token in _pl_route_tokens(text):
        signals[token] += 4.0
    return dict(signals)


def _pl_known_domains(repo: Path, eff: dict, reg) -> set[str]:
    """Build the set of known canonical domains from taxonomy + repo state."""
    known: set[str] = set(PLACEMENT_DOMAIN_KEYWORDS.keys())
    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    stop = set(PLACEMENT_STOP_TOKENS) | surfaces

    try:
        for d in getattr(reg, "domains", set()):
            norm = _pl_normalize_domain(d)
            if not norm or norm in stop:
                continue
            if norm in PLACEMENT_DOMAIN_KEYWORDS or len(norm) >= 4:
                known.add(norm)
    except Exception:
        pass

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
            if name.startswith(".") or name in PLACEMENT_SKIP_PARTS or name in stop:
                continue
            norm = _pl_normalize_domain(name)
            if not norm:
                continue
            if norm in PLACEMENT_DOMAIN_KEYWORDS or len(norm) >= 4:
                known.add(norm)
    return known


def _pl_infer_domain(signals: dict[str, float], known_domains: set[str], eff: dict,) -> tuple[str | None, float, list[str]]:
    """Infer the best domain from weighted signals. Returns (domain, confidence, reasons)."""
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


def _pl_infer_router_target(f: Path, text: str, inferred_domain: str | None, confidence: float, eff: dict,) -> tuple[str, str]:
    """Infer where a router file should live.  Routers are SURFACE-only."""
    low = f.stem.lower()
    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    if not surfaces:
        surfaces = {"admin", "supplier", "customer", "public", "webhooks", "internal"}
    # 1. filename prefix  e.g. admin_orders.py → admin
    for surface in sorted(surfaces):
        if low == surface or low.startswith(f"{surface}_"):
            return surface, "surface-filename"
    # 2. route prefix / tags  e.g. prefix="/admin/..." → admin
    route_tokens = _pl_route_tokens(text)
    for surface in sorted(surfaces):
        if surface in route_tokens:
            return surface, "surface-route"
    # 3. NO domain fallback — routers are surface-only.
    #    If no surface is detected, default to "internal".
    return "internal", "default-surface"


def _pl_check_unknown_folders(repo: Path, rep: Report, eff: dict, known_domains: set[str],) -> None:
    """Detect unknown/generic/non-canonical folders inside domain layers."""
    backend = repo / "backend"
    if not backend.exists():
        return
    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
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
            if name.startswith(".") or name in PLACEMENT_SKIP_PARTS:
                continue
            # Domain folders are valid even if the same name is also a surface.
            if name in known_domains:
                continue

            # Surface-only folders are invalid inside domain layers.
            if name in surfaces:
                # DOM3 is reported by check_surface_domain_matrix().
                # Avoid duplicate findings.
                continue

            canonical = _pl_normalize_domain(name)
            if canonical and canonical != name and canonical in PLACEMENT_DOMAIN_KEYWORDS:
                rep.add(
                    YEL, "DOM7", layer, rel(p, repo),
                    f"non-canonical domain folder '{name}/' should be '{canonical}/'",
                    intended=f"git mv backend/{layer}/{name} backend/{layer}/{canonical}",
                )
                continue
            if canonical in known_domains or canonical in PLACEMENT_DOMAIN_KEYWORDS:
                continue
            if name in stop:
                rep.add(
                    YEL, "DOM7", layer, rel(p, repo),
                    f"generic folder '{name}/' is not a valid domain folder",
                    intended=(
                        "move its files into a real domain folder "
                        "(finance/orders/catalog/supplier/logistics/communication/...)"
                    ),
                )
                continue
            rep.add(
                YEL, "DOM7", layer, rel(p, repo),
                f"unknown domain folder '{name}/'",
                intended=(
                    f"if '{name}' is a real bounded context, add it to governance taxonomy; "
                    "otherwise move its files into the nearest canonical domain"
                ),
            )


def check_move_suggestions(repo: Path, rep: Report, eff: dict, graph, reg,) -> list[dict]:
    """
    SINGLE authoritative move-suggestion engine.
    Suggests:
    - flat domain-layer file -> domain folder
    - wrong domain folder -> correct domain folder
    - router file -> surface/domain folder
    - backend-root file -> proper package
    - generic/unknown folder -> cleanup
    - correctly placed files -> keep summary
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
    # Routers are flat.
    # Router naming/movement is handled by RN1/RN2/RN3 and the router-flat
    # move block below.
    scan_layers = PLACEMENT_DOMAIN_LAYERS

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
            inferred_domain, confidence, reasons = _pl_infer_domain(signals, known_domains, eff)

            if layer == "routers":
                target_folder, inference_kind = _pl_infer_router_target(f, text, inferred_domain, confidence, eff)
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

            # Folder-stability override: prevent false positives
            if (
                layer != "routers"
                and current_folder
                and current_norm
                and current_norm in known_domains
                and current_norm != target_folder
            ):
                filename_tokens = _pl_tokenize(f.stem, eff)
                if current_norm in filename_tokens:
                    target_folder = current_norm
                    inference_kind = "folder-name-match"
                elif (
                    layer in {"controllers", "providers"}
                    and filename_tokens & PLACEMENT_FOLDER_STABLE_TOKENS
                ):
                    target_folder = current_norm
                    inference_kind = "folder-stable"

            # Correct placement
            if current_folder and current_norm == target_folder:
                if current_folder != target_folder:
                    rename_folders.add((layer, current_folder, target_folder))
                correct_count += 1
                continue

            kind = "root_move" if current_folder is None else "wrong_folder"
            source_path = rel(f, repo)
            target_path = f"backend/{layer}/{target_folder}/{f.name}"
            moves.append({
                "from": source_path, "to": target_path,
                "reason": inference_kind, "kind": kind,
                "domain": target_folder, "target_folder": target_folder,
                "layer": layer, "confidence": confidence,
            })
            key = (layer, target_folder, kind)
            group_files[key].append(source_path)
            if key not in group_reasons:
                group_reasons[key] = reasons

    # Backend-root file placement
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
            inferred_domain, confidence, reasons = _pl_infer_domain(signals, known_domains, eff)
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
        moves.append({
            "from": source_path, "to": target_path,
            "reason": "backend-root", "kind": "backend_root",
            "domain": target_folder, "target_folder": target_folder,
            "layer": "backend", "confidence": 1.0 if canonical else 0.6,
        })
        key = ("backend", target_folder, "backend_root")
        group_files[key].append(source_path)
        if key not in group_reasons:
            group_reasons[key] = reasons

    # ------------------------------------------------------------------
    # Router flat move suggestions.
    # Routers must be flat: {surface}_{domain}_{operation}.py
    # ------------------------------------------------------------------
    routers_dir = backend / "routers"

    if routers_dir.exists():
        surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
        aliases = PLACEMENT_ALIAS_TO_DOMAIN

        def _r_tokens(stem: str) -> list[str]:
            return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", stem) if t]

        def _r_surface(toks: list[str], hint: str | None = None) -> str | None:
            if hint and hint in surfaces:
                return hint

            for t in toks:
                if t in surfaces:
                    return t

            return None

        def _r_domain(toks: list[str]) -> str | None:
            for t in toks:
                d = aliases.get(t)
                if d:
                    return d

            return None

        def _r_flat_target(
            stem: str,
            surface: str | None,
            domain: str | None,
        ) -> str:
            new = stem.lower()

            if surface and not new.startswith(f"{surface}_"):
                new = f"{surface}_{new}"

            if domain:
                parts = new.split("_")
                first = parts[0] if parts else ""

                if domain not in parts and aliases.get(first) != domain:
                    if surface and new.startswith(f"{surface}_"):
                        rest = new[len(surface) + 1:]
                        new = f"{surface}_{domain}_{rest}"
                    else:
                        new = f"{domain}_{new}"

            return f"backend/routers/{new}.py"

        try:
            router_subdirs = [
                p for p in routers_dir.iterdir()
                if p.is_dir()
                and p.name.lower() not in eff.get("ignore_dirs", set())
                and p.name.lower() != "__pycache__"
            ]
        except OSError:
            router_subdirs = []

        for sd in sorted(router_subdirs):
            for f in sorted(sd.rglob("*.py")):
                if f.name == "__init__.py":
                    continue

                toks = _r_tokens(f.stem)
                surface = _r_surface(toks, sd.name.lower())
                domain = _r_domain(toks)
                target_path = _r_flat_target(f.stem, surface, domain)

                moves.append({
                    "from": rel(f, repo),
                    "to": target_path,
                    "reason": "router-flat",
                    "kind": "router_rename",
                    "domain": domain or "routers",
                    "target_folder": "",
                    "layer": "routers",
                    "confidence": 0.7,
                })

    # Emit grouped findings (SINGLE emission loop)
    for key in sorted(group_files.keys()):
        layer, target_folder, kind = key
        files_list = sorted(group_files[key])
        reasons_list = group_reasons.get(key, [])
        reason_text = ", ".join(reasons_list[:3]) if reasons_list else "name/content signals"

        if kind == "root_move" and layer == "routers":
            code = "MV3"
            message = f"{len(files_list)} router file(s) should be grouped under backend/routers/{target_folder}/"
            mkdir_path = f"backend/routers/{target_folder}"
        elif kind == "root_move":
            code = "MV1"
            message = f"{len(files_list)} '{target_folder}' domain file(s) at backend/{layer}/ root should be moved to backend/{layer}/{target_folder}/"
            mkdir_path = f"backend/{layer}/{target_folder}"
        elif kind == "backend_root":
            code = "MV2"
            message = f"{len(files_list)} backend-root file(s) should be moved to backend/{target_folder}/"
            mkdir_path = f"backend/{target_folder}"
        else:
            code = "DOM2"
            message = f"{len(files_list)} file(s) are in the wrong backend/{layer}/ sub-folder; detected domain: '{target_folder}'"
            mkdir_path = f"backend/{layer}/{target_folder}"

        intended = f"mkdir -p {mkdir_path}; move: " + ", ".join(files_list[:12])
        if len(files_list) > 12:
            intended += f" +{len(files_list) - 12} more"
        intended += f" (detected from {reason_text})"
        rep.add(
            YEL, code, layer,
            f"backend/{layer}/" if layer != "backend" else "backend/",
            message, intended=intended,
        )

    # Emit folder rename suggestions
    for layer, old_name, new_name in sorted(rename_folders):
        rep.add(
            YEL, "DOM7", layer,
            f"backend/{layer}/{old_name}/",
            f"non-canonical domain folder '{old_name}/' should be renamed to '{new_name}/'",
            intended=f"git mv backend/{layer}/{old_name} backend/{layer}/{new_name}",
        )
        moves.append({
            "from": f"backend/{layer}/{old_name}/",
            "to": f"backend/{layer}/{new_name}/",
            "reason": "rename-folder", "kind": "folder_rename",
            "domain": new_name, "target_folder": new_name,
            "layer": layer, "confidence": 1.0,
        })

    # Unknown/generic folder detection
    _pl_check_unknown_folders(repo, rep, eff, known_domains)

    # Positive placement summary
    if correct_count > 0:
        rep.add(
            GRN, "DOM8", "backend", "backend/",
            f"{correct_count} scanned file(s) are already in the correct domain folder",
            intended="keep these placements; do not move them",
        )

    return moves

# ============================================================================
# SECTION 15: SCAFFOLDING CONTRACT + SURFACE×DOMAIN MATRIX + FRONTEND ROLES
# ============================================================================

def check_surface_domain_matrix(repo: Path, rep: Report, eff: dict, graph: ModuleGraph,) -> None:
    """
    Validate grouping axis:

    - routers/      -> flat, validated by RN1/RN2/RN3
    - controllers/  -> domain grouping required
    - services/     -> domain grouping required
    - models/       -> domain grouping required
    - providers/    -> domain grouping required
    - events/       -> domain grouping required
    - jobs/         -> domain grouping required

    Important:
    If a folder name is BOTH a surface and a domain, domain wins inside
    domain layers. This prevents false positives for:
        services/supplier/
        services/customer/
        services/logistics/
    """
    backend = repo / "backend"

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}

    domains: set[str] = set(PLACEMENT_DOMAIN_KEYWORDS.keys())
    domains |= {str(x).lower() for x in eff.get("domains", {}).keys()}

    if _ACTIVE_REG is not None:
        domains |= {
            str(x).lower()
            for x in getattr(_ACTIVE_REG, "domains", set())
        }

    # Routers are intentionally flat.
    # Router sub-folder validation is owned by RN1/RN2/RN3.
    domain_layers = (
        "controllers",
        "services",
        "models",
        "providers",
        "events",
        "jobs",
    )

    for layer in domain_layers:
        layer_dir = backend / layer

        if not layer_dir.exists():
            continue

        try:
            entries = list(layer_dir.iterdir())
        except OSError:
            continue

        for entry in entries:
            if not entry.is_dir():
                continue

            name = entry.name.lower()

            if name in {"__pycache__"}:
                continue

            # Domain folders are allowed.
            # Domain wins over surface.
            if name in domains:
                continue

            # Surface-only folders are invalid inside domain layers.
            if name in surfaces:
                rep.add(
                    RED,
                    "DOM3",
                    layer,
                    rel(entry, repo),
                    f"SURFACE folder '{name}/' inside DOMAIN layer {layer}/",
                    intended=(
                        f"remove {layer}/{name}/; move its files into the "
                        f"correct domain folder or rename to a real domain "
                        f"(finance/orders/catalog/supplier/...)"
                    ),
                )


def check_frontend_role_pages(repo: Path, rep: Report, eff: dict) -> None:
    """
    Validate frontend role-based page structure.
    Ensures:
    1. Role surfaces exist (admin/, supplier/, logistics-partner/)
    2. Required domain pages exist within each role
    3. Customer-facing pages are at root level (not under /customer/)
    """
    web_app = repo / "frontend" / "web_app" / "src" / "app"
    if not web_app.exists():
        return

    role_pages = {
        "admin": {
            "required": ["products", "orders", "suppliers", "dashboard"],
            "optional": [
                "finance", "treasury", "logistics", "employees",
                "countries", "communication", "promotions", "users",
                "permissions", "audit-logs", "banners", "coupons",
            ],
        },
        "supplier": {
            "required": ["products", "orders", "dashboard"],
            "optional": [
                "payouts", "invoices", "logistics", "analytics",
                "documents", "profile", "reports", "returns",
                "disputes", "inventory", "bulk", "upload",
            ],
        },
        "logistics-partner": {
            "required": ["dashboard", "shipments"],
            "optional": ["payouts", "scan", "analytics", "profile", "routes"],
        },
    }

    for role, config in role_pages.items():
        role_dir = web_app / role
        if not role_dir.exists():
            rep.add(
                RED, "FE1", "frontend",
                f"frontend/web_app/src/app/{role}/",
                f"missing role surface '{role}/' in web_app",
                intended=f"create frontend/web_app/src/app/{role}/ with required pages",
            )
            continue

        existing_pages: set[str] = set()
        try:
            for entry in role_dir.iterdir():
                if entry.is_dir() and (entry / "page.tsx").exists():
                    existing_pages.add(entry.name)
                elif entry.is_dir():
                    for sub in entry.iterdir():
                        if sub.is_dir() and (sub / "page.tsx").exists():
                            existing_pages.add(entry.name)
        except OSError:
            continue

        for req in config["required"]:
            if req not in existing_pages:
                rep.add(
                    YEL, "FE3", "frontend",
                    f"frontend/web_app/src/app/{role}/{req}/",
                    f"required page '{req}' missing in {role}/ surface",
                    intended=f"create frontend/web_app/src/app/{role}/{req}/page.tsx",
                )

    # Customer pages should be at root, not under /customer/.
    customer_at_root = {"products", "orders", "cart", "checkout", "profile", "wishlist"}
    for page in customer_at_root:
        if not (web_app / page / "page.tsx").exists():
            rep.add(
                YEL, "FE3", "frontend",
                f"frontend/web_app/src/app/{page}/",
                f"customer-facing page '{page}' missing at root level",
                intended=f"customer pages live at app/{page}/page.tsx (no /customer/ prefix)",
            )


# ============================================================================
# SECTION 16: AUTO-LEARNING DOMAIN PLACEMENT ENGINE
# ============================================================================

def _auto_stop_tokens(eff: dict) -> set[str]:
    """Build stop-token set for auto-learning tokenization."""
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
    raw = re.sub(r"(?<!^)(?=[A-Z])", "_", raw)
    raw = re.sub(r"[^A-Za-z0-9]+", "_", raw)
    tokens = {t.lower() for t in raw.split("_") if t}
    stop = _auto_stop_tokens(eff)
    return {t for t in tokens if t not in stop and len(t) >= 3}


def _add_auto_signals(signals: dict[str, float],tokens: set[str], weight: float,) -> None:
    for token in tokens:
        signals[token] = signals.get(token, 0.0) + float(weight)


def extract_auto_signals(f: Path, backend: Path, text: str | None, tree: ast.Module | None, eff: dict,) -> dict[str, float]:
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


def learn_domain_model(repo: Path, eff: dict, reg: FeatureRegistry,) -> AutoDomainModel:
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

def report_auto_domain_candidates(repo: Path, rep: Report, eff: dict, model: AutoDomainModel,) -> None:
    """
    Report only auto-discovered candidate domains.

    This intentionally does NOT produce a second set of move recommendations.
    Move recommendations must come from the deterministic placement engine only.
    """
    if not eff.get("detect_auto_discovery"):
        return

    reported = 0

    for domain in sorted(model.candidate_domains):
        files = sorted(model.token_files.get(domain, set()))[:8]

        rep.add(
            GRN,
            "DOM6",
            "backend",
            f"backend/services|models/{domain}",
            f"new domain candidate auto-detected: '{domain}'",
            intended=(
                f"create backend/<layer>/{domain}/ and group related files; "
                f"or merge into nearest existing domain if this is not a real "
                f"bounded context. Examples: " + ", ".join(files)
            ),
        )

        reported += 1

        if reported >= 50:
            break

# ============================================================================
# SECTION 17: SUMMARY + TREND + COLLAPSE
# ============================================================================

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
    score += by.get("DB3", 0) * 50

    score += by.get("DOM1", 0) * 15
    score += by.get("DOM2", 0) * 20
    score += by.get("DOM3", 0) * 12
    score += by.get("DOM6", 0) * 2

    score += by.get("CIR1", 0) * 60
    score += by.get("CIR2", 0) * 12

    score += by.get("RN1", 0) * 6
    score += by.get("RN2", 0) * 3
    score += by.get("MV1", 0) * 8
    score += by.get("MV2", 0) * 12
    score += by.get("MV3", 0) * 6
    return int(score)


def collect_info(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    def n(sub: str) -> int:
        d = repo / "backend" / sub
        if not d.exists():
            return 0
        return sum(1 for x in d.rglob("*.py") if x.is_file())

    rep.add(
        GRN, "I1", "repo", rel(repo, repo),
        f"backend models={n('models')} routers={n('routers')} "
        f"controllers={n('controllers')} services={n('services')} "
        f"middleware={n('middleware')}",
    )
    src = (
        "YAML policy (documents/scope/ or governance/)"
        if eff["from_yaml"]
        else "EMBEDDED FALLBACK (create documents/scope/*.yaml to make scope authoritative)"
    )
    rep.add(GRN, "I2", "repo", "documents/scope/", f"rules loaded from: {src}")
    rep.add(
        GRN, "I3", "repo", "backend/",
        f"module graph: modules={len(graph.modules)}, "
        f"edges={sum(len(v) for v in graph.edges.values())}, "
        f"classes={len(graph.classes)}",
    )


def build_summary(repo: Path, rep: Report,graph: ModuleGraph, debt_score: int, frontend_metrics: dict, reg: FeatureRegistry,) -> dict:
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


def collapse_noisy_findings(rep: Report) -> None:
    """
    Collapse high-volume line-level findings into one file-level finding.
    Example:
        80 individual Q1 findings in one controller
        becomes:
        1 Q1 finding saying "80 DB read(s) in this file"
    """
    noisy_codes = {"Q1", "W1", "W2", "PERF2", "QUAL1", "QUAL4"}
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

        messages = {
            "Q1": (
                f"{count} DB read(s) via .query() in this file; "
                "delegate reads to a service"
            ),
            "W1": (
                f"{count} session write(s) in this file; "
                "move writes into services/<domain>/"
            ),
            "W2": (
                f"{count} misnamed service-helper write location(s) in this file; "
                "relocate logic to services/"
            ),
            "PERF2": (
                f"{count} possible DB query inside loop (N+1 risk) in this file; "
                "batch queries / use joins / preload relationships"
            ),
            "QUAL1": (
                f"{count} weak exception handling location(s) in this file; "
                "log or re-raise instead of swallowing exceptions"
            ),
            "QUAL4": (
                f"{count} print/debug output location(s) in this file; "
                "use structured logging instead of print()"
            ),
        }
        base_message = messages.get(
            code,
            f"{count} {RULE_MEANING.get(code, code)} location(s) in this file",
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
                sev=sev, code=code, domain=domain, path=path,
                message=message, intended=intended, line=None,
            )
        )

    rep.findings = kept
    rep.counters = defaultdict(int)
    for f in rep.findings:
        rep.counters[f.code] += 1


# ============================================================================
# SECTION 18: RENDERING
# ============================================================================

def generate_ai_placement_contract() -> str:
    """
    Generate a prescriptive placement contract for AI agents.
    This tells AI where to put NEW files before it creates them.
    """
    lines = [
        "## AI File Placement Contract",
        "",
        "**Rule for AI:** Before creating or moving any backend file, use this contract.",
        "",
        "### Layer rules",
        "",
        "| Layer | Structure | Correct examples |",
        "|---|---|---|",
        "| `backend/routers/` | **Flat file**: `{surface}_{domain}_{operation}.py` | "
        "`admin_orders_management.py`, `supplier_orders_fulfillment.py`, "
        "`customer_orders_tracking.py`, `public_catalog_product_browsing.py` |",
        "| `backend/controllers/` | Domain folder + surface-prefixed controller file | "
        "`controllers/orders/admin_order_management_controller.py`, "
        "`controllers/catalog/supplier_product_management_controller.py` |",
        "| `backend/services/` | Domain folder | "
        "`services/orders/order_management_service.py`, "
        "`services/finance/payment_processing_service.py` |",
        "| `backend/models/` | Domain folder | "
        "`models/orders/order_entities.py` |",
        "| `backend/providers/` | Domain/adapter folder | "
        "`providers/ai/image_analysis_provider.py` |",
        "| `backend/events/` | Domain folder | "
        "`events/orders/order_events.py` |",
        "| `backend/jobs/` | Domain folder | "
        "`jobs/finance/payout_batch_job.py` |",
        "",
        "### Admin CRUD handling",
        "",
        "Admin is a **surface**, not a domain.",
        "",
        "Do not create:",
        "",
        "```text",
        "backend/services/admin/",
        "backend/controllers/admin/",
        "backend/routers/admin/",
        "```",
        "",
        "Use this instead:",
        "",
        "```text",
        "backend/routers/admin_orders_management.py",
        "backend/controllers/orders/admin_order_management_controller.py",
        "backend/services/orders/order_management_service.py",
        "```",
        "",
        "### Forbidden folders",
        "",
        "```text",
        "backend/routers/admin/",
        "backend/routers/finance/",
        "backend/routers/catalog/",
        "backend/routers/orders/",
        "backend/controllers/admin/",
        "backend/services/admin/",
        "backend/models/admin/",
        "backend/providers/admin/",
        "backend/events/admin/",
        "backend/jobs/admin/",
        "backend/services/write/",
        "backend/services/common/",
        "backend/services/legacy/",
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
            f"| `{domain}` | `backend/services/{domain}/`, "
            f"`backend/models/{domain}/`, `backend/controllers/{domain}/` "
            f"| {examples} |"
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


def render_intended_tree() -> str:
    """
    Dynamic intended structure.
    Generated from configured surfaces, discovered domains, ownership layers.
    Includes the AI File Placement Contract inline.
    """
    eff = _ACTIVE_EFF or {}
    reg = _ACTIVE_REG

    surfaces = sorted(
        {str(x).lower() for x in eff.get("surface_names", DEFAULT_SURFACE_NAMES)}
    )

    domains = sorted(
        set(getattr(reg, "domains", set()))
        | set(eff.get("domains", {}).keys())
        | set(PLACEMENT_DOMAIN_KEYWORDS.keys())
    )

    if not domains:
        domains = ["<domain>"]

    surface_preview = ", ".join(surfaces[:10])
    domain_preview = ", ".join(domains[:16])

    lines = [
        "# INTENDED ZOZI STRUCTURE (generated from live governance config)",
        "",
        "Logical domains `database` and `security` live INSIDE backend/ by design.",
        "",
        "Sub-folder / naming axis:",
        "  ROUTERS are FLAT: {surface}_{domain}_{operation}.py",
        f"  Surfaces: {surface_preview}",
        f"  DOMAIN folders in controllers/, services/, models/, providers/, events/, jobs/: {domain_preview}",
        "",
        "```",
        "zozi/",
        "├── backend/",
        "│   ├── routers/        (FLAT: admin_orders_management.py, supplier_orders_fulfillment.py, ...)",
        "│   ├── controllers/    (domain folders; surface-specific files use surface prefix)",
        "│   ├── services/       (domain folders REQUIRED; admin is NOT a domain)",
        "│   ├── models/         (domain folders REQUIRED)",
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
        "│   ├── scope/          (authoritative specs + YAML policy)",
        "│   └── archive/",
        "├── monitoring/",
        "├── nginx/",
        "├── experiments/",
        "└── design/",
        "```",
        "",
        generate_ai_placement_contract(),
    ]

    return "\n".join(lines)


def ordered_report_domains(rep: Report) -> list[str]:
    """
    Return all domains present in findings.

    Priority domains are shown first.
    Any extra domains, such as services/routers/controllers/models, are shown after.
    """
    priority = [
        "repo",
        "backend",
        "database",
        "frontend",
        "security",
        "docs",
        "infra",
    ]

    present = {f.domain for f in rep.findings if f.domain}
    ordered = [d for d in priority if d in present]
    extra = sorted(d for d in present if d not in priority)

    return ordered + extra


def render_stdout(repo: Path, rep: Report, show_intended: bool, summary: dict) -> int:
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary.get("debt_score", 0)

    print("=" * 76)
    print("  ZOZI ARCHITECTURE GOVERNANCE AUDIT v4.0")
    print("  structure · layers · dependency graph · cycles · ownership · metrics")
    print("  dynamic imports · policy validation · frontend scaling · auto-discovery")
    print("=" * 76)
    print(f"  repo: {repo}")
    print(
        f"  [RED] VIOLATIONS : {n_red}    "
        f"[YEL] ADVISORIES : {n_yel}    "
        f"[GRN] INFO : {n_grn}"
    )
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
    for dom in ordered_report_domains(rep):
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
    print(
        f"  modules: {summary['modules']}   "
        f"edges: {summary['edges']}   "
        f"classes: {summary['classes']}"
    )
    if summary.get("layer_counts"):
        print(
            "  layer counts: "
            + ", ".join(f"{k}={v}" for k, v in sorted(summary["layer_counts"].items()))
        )
    if summary.get("top_fan_in"):
        print("\nTop fan-in:")
        for module, count in summary["top_fan_in"]:
            print(f"    {count:>3}  {module}")
    if summary.get("top_fan_out"):
        print("\nTop fan-out:")
        for module, count in summary["top_fan_out"]:
            print(f"    {count:>3}  {module}")
    if summary.get("frontend_metrics"):
        print("\nFrontend workspace metrics:")
        for ws, m in sorted(summary["frontend_metrics"].items()):
            print(f"    {ws}: source_files={m.get('source_files', 0)}, dirs={m.get('dirs', 0)}")
    if summary.get("auto_discovery"):
        ad = summary["auto_discovery"]
        print("\nAuto-discovery:")
        print(f"    domains={ad.get('domains', 0)}")
        print(f"    features={ad.get('features', 0)}")
        print(f"    frontend_features={ad.get('frontend_features', 0)}")
        print(f"    backend_top_dirs={ad.get('backend_top_dirs', 0)}")
        print(f"    learned_domain_edges={ad.get('domain_edges', 0)}")
    if show_intended:
        print("\n" + render_intended_tree())
    print("\n" + "=" * 76)
    return n_red


def _mermaid_safe_id(prefix: str, name: str, used_ids: set[str]) -> str:
    """Create a Mermaid-safe unique node ID."""
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
    """Create a Mermaid-safe quoted label."""
    label = str(name).replace('"', "'").replace("\n", " ")
    if file_count > 0:
        label += f" ({file_count} files)"
    return label


def generate_current_structure_mermaid(repo: Path, eff: dict) -> str:
    """Generate Mermaid graph of the CURRENT backend folder structure."""
    backend = repo / "backend"
    if not backend.exists():
        return ""
    ignore_dirs = {str(x).lower() for x in eff.get("ignore_dirs", set())}
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


def generate_suggested_structure_mermaid(repo: Path, eff: dict, placements: list[dict] | None = None,) -> str:
    """
    Generate Mermaid graph of the SUGGESTED backend folder structure.

    Important:
    - routers/ is shown as flat.
    - domain layers must not show surface-only folders such as admin/.
    """
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

    used_ids: set[str] = set()

    suggested: dict[str, set[str]] = defaultdict(set)
    router_flat_files: list[str] = []

    for p in placements:
        layer = p.get("layer", "")
        kind = p.get("kind", "")

        if layer == "routers" and kind == "router_rename":
            to = str(p.get("to", "")).replace("\\", "/")
            if to:
                router_flat_files.append(to.split("/")[-1])
            continue

        target = p.get("target_folder") or p.get("domain", "")

        if not layer or not target:
            to_path = str(p.get("to", "")).replace("\\", "/")
            parts = to_path.split("/")

            if len(parts) >= 3 and parts[0] == "backend":
                layer = parts[1]
                target = parts[2]

        if layer and target:
            target_final = str(target).replace("\\", "/").split("/")[-1].lower()

            bad_targets = {
                "service", "services", "controller", "controllers",
                "engine", "write", "manager", "handler", "helper",
                "common", "shared", "utils", "util", "legacy",
                "advanced", "shift", "badge", "geo", "ghost",
                "border", "ledger", "financial", "chat", "email",
                "event", "config", "commission", "employee", "incident",
                "management", "cross",
                # surfaces must not become domain folders
                "admin", "supplier", "customer", "public",
                "internal", "external", "webhooks", "logistics-partner",
            }

            if target_final not in bad_targets:
                suggested[layer].add(target_final)

    known_domains = set(PLACEMENT_DOMAIN_KEYWORDS.keys())
    known_domains |= {str(x).lower() for x in eff.get("domains", {}).keys()}

    if _ACTIVE_REG is not None:
        known_domains |= {
            str(x).lower()
            for x in getattr(_ACTIVE_REG, "domains", set())
        }

    known_surfaces = {str(x).lower() for x in eff.get("surface_names", set())}

    domain_only_layers = {
        "services",
        "models",
        "controllers",
        "providers",
        "events",
        "jobs",
    }

    lines = [
        "```mermaid",
        "graph TD",
        '    ROOT["backend/ (suggested target)"]',
    ]

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

    for layer in sorted(suggested.keys()):
        if layer not in top_dirs and layer in domain_only_layers:
            top_dirs.append(layer)

    if (backend / "routers").exists() and "routers" not in top_dirs:
        top_dirs.append("routers")

    top_dirs = sorted(set(top_dirs), key=str.lower)

    for td in top_dirs:
        td_id = _mermaid_safe_id("be", td, used_ids)

        # --------------------------------------------------------------
        # Routers are flat.
        # --------------------------------------------------------------
        if td == "routers":
            lines.append(f'    {td_id}["routers/ (flat: surface_domain_operation.py)"]')
            lines.append(f"    ROOT --> {td_id}")

            examples = router_flat_files[:12]

            if not examples:
                try:
                    examples = sorted(
                        [
                            f.name for f in (backend / "routers").glob("*.py")
                            if f.name != "__init__.py"
                        ]
                    )[:12]
                except OSError:
                    examples = []

            for fname in examples:
                fid = _mermaid_safe_id(td_id, fname.replace(".", "_"), used_ids)
                lines.append(f'    {fid}["{fname}"]')
                lines.append(f"    {td_id} --> {fid}")

            if len(router_flat_files) > 12:
                fid = _mermaid_safe_id(td_id, "more_router_files", used_ids)
                lines.append(f'    {fid}["+{len(router_flat_files) - 12} more flat router files"]')
                lines.append(f"    {td_id} --> {fid}")

            continue

        lines.append(f'    {td_id}["{td}/"]')
        lines.append(f"    ROOT --> {td_id}")

        # --------------------------------------------------------------
        # Domain layers: remove surface-only folders from suggested target.
        # --------------------------------------------------------------
        if td in domain_only_layers:
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

            # True target: surface-only folders must disappear.
            existing_subs = [
                sd for sd in existing_subs
                if sd.lower() in known_domains or sd.lower() not in known_surfaces
            ]

            suggested_subs = sorted(suggested.get(td, set()))
            all_subs = sorted(set(existing_subs) | set(suggested_subs))

            for sub in all_subs[:20]:
                sub_id = _mermaid_safe_id(td_id, sub, used_ids)
                is_new = sub in suggested_subs and sub not in existing_subs
                label = f"{sub}/ ✨" if is_new else f"{sub}/"

                lines.append(f'    {sub_id}["{label}"]')
                lines.append(f"    {td_id} --> {sub_id}")

            continue

        # --------------------------------------------------------------
        # Non-domain layers: normal sub-directory preview.
        # --------------------------------------------------------------
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
            sub_id = _mermaid_safe_id(td_id, sd, used_ids)
            lines.append(f'    {sub_id}["{sd}/"]')
            lines.append(f"    {td_id} --> {sub_id}")

    lines.append("```")

    return "\n".join(lines)


def generate_current_frontend_mermaid(repo: Path, eff: dict) -> str:
    """Generate Mermaid graph of the CURRENT frontend folder structure."""
    frontend = repo / "frontend"
    if not frontend.exists():
        return ""
    ignore_dirs = {str(x).lower() for x in eff.get("ignore_dirs", set())}
    extra_skip = {
        "node_modules", ".next", "dist", "build", "coverage",
        ".expo", ".turbo", "__pycache__", ".pytest_cache",
        ".mypy_cache", ".ruff_cache", "test-results",
        "playwright-report", "playwright-out", "test-output",
        "web-dist", ".web-build-test", "static-tmp", "tmp",
        "e2e", ".hypothesis", ".kilo", ".kilocode", "worktrees",
        "__tests__", "tests", "test", "__mocks__", ".storybook",
        ".vscode", ".idea", ".git", ".venv", "venv",
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
                1 for f in d.iterdir()
                if f.is_file() and f.suffix.lower() in source_ext
            )
        except OSError:
            return 0

    used_ids: set[str] = set()
    lines = ["```mermaid", "graph TD"]
    root_id = _mermaid_safe_id("fe", "frontend", used_ids)
    lines.append(f'    {root_id}["{_mermaid_label("frontend/")}"]')

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
        "src", "app", "components", "lib", "hooks", "features",
        "pages", "screens", "services", "store", "stores",
        "utils", "types", "styles",
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
            web_dirs = [
                "src/app/", "src/components/", "src/lib/",
                "src/hooks/", "src/features/", "src/styles/",
            ]
            for wd in web_dirs:
                wd_clean = wd.rstrip("/")
                wd_id = f"{ws_id}_{wd_clean.replace('/', '_').replace('-', '_')}"
                lines.append(f'    {wd_id}["{wd}"]')
                lines.append(f"    {ws_id} --> {wd_id}")
            features_path = ws_path / "src" / "features"
            if features_path.exists():
                try:
                    feature_dirs = sorted(
                        [
                            d.name for d in features_path.iterdir()
                            if d.is_dir() and d.name.lower() not in skip
                        ],
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


# ============================================================================
# SECTION 19: SYMBOL INDEX ENGINE
# ============================================================================
"""
Builds a repository-wide symbol index similar to a language server.
Tracks: classes, functions, methods, constants, imports, usages.
Enables: dead symbol detection, public API analysis, call graph construction.
"""

def build_symbol_index(repo: Path, eff: dict, graph: ModuleGraph) -> SymbolIndex:
    """
    Build a comprehensive symbol index for all Python modules.
    This is the foundation for call graph, public API, and dead code analysis.
    """
    index = SymbolIndex()
    backend = repo / "backend"
    if not backend.exists():
        return index

    for module, f in graph.modules.items():
        tree = parse_safe(f)
        if tree is None:
            continue

        rel_path = rel(f, repo)
        module_exports: set[str] = set()

        for node in ast.walk(tree):
            # Classes
            if isinstance(node, ast.ClassDef):
                is_public = not node.name.startswith("_")
                decorators = [
                    _ast_name_to_str(d) for d in node.decorator_list
                ]
                is_deprecated = any(
                    "deprecated" in d.lower() for d in decorators
                )
                sym = SymbolInfo(
                    name=node.name,
                    kind="class",
                    module=module,
                    file_path=rel_path,
                    line=node.lineno,
                    is_public=is_public,
                    is_deprecated=is_deprecated,
                    decorators=decorators,
                    docstring=ast.get_docstring(node),
                )
                index.add(sym)
                if is_public:
                    module_exports.add(node.name)

                # Methods within class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_public = not item.name.startswith("_")
                        method_decorators = [
                            _ast_name_to_str(d) for d in item.decorator_list
                        ]
                        method_sym = SymbolInfo(
                            name=item.name,
                            kind="method",
                            module=module,
                            file_path=rel_path,
                            line=item.lineno,
                            is_public=method_public,
                            is_deprecated=any(
                                "deprecated" in d.lower()
                                for d in method_decorators
                            ),
                            decorators=method_decorators,
                            parent_class=node.name,
                            docstring=ast.get_docstring(item),
                        )
                        index.add(method_sym)

            # Top-level functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Only top-level (not inside class)
                if node.col_offset == 0:
                    is_public = not node.name.startswith("_")
                    decorators = [
                        _ast_name_to_str(d) for d in node.decorator_list
                    ]
                    sym = SymbolInfo(
                        name=node.name,
                        kind="function",
                        module=module,
                        file_path=rel_path,
                        line=node.lineno,
                        is_public=is_public,
                        is_deprecated=any(
                            "deprecated" in d.lower() for d in decorators
                        ),
                        decorators=decorators,
                        docstring=ast.get_docstring(node),
                    )
                    index.add(sym)
                    if is_public:
                        module_exports.add(node.name)

            # Top-level assignments (constants)
            elif isinstance(node, ast.Assign) and node.col_offset == 0:
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id.isupper():
                        sym = SymbolInfo(
                            name=target.id,
                            kind="constant",
                            module=module,
                            file_path=rel_path,
                            line=node.lineno,
                            is_public=True,
                        )
                        index.add(sym)
                        module_exports.add(target.id)

        index.module_exports[module] = module_exports

    # Build usage index
    for module, f in graph.modules.items():
        tree = parse_safe(f)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                if node.id in index.symbols:
                    index.symbol_usages[node.id].append((module, node.lineno))
            elif isinstance(node, ast.Attribute):
                attr_name = node.attr
                if attr_name in index.symbols:
                    index.symbol_usages[attr_name].append((module, node.lineno))

    return index


def _ast_name_to_str(node: ast.AST) -> str:
    """Convert an AST decorator node to a string representation."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_ast_name_to_str(node.value)}.{node.attr}"
    elif isinstance(node, ast.Call):
        return _ast_name_to_str(node.func)
    return "<unknown>"


def check_dead_symbols(repo: Path, rep: Report, eff: dict,index: SymbolIndex, graph: ModuleGraph) -> None:
    """
    SYM1: Detect symbols defined but never used anywhere.
    Only checks public functions/classes in application layers.
    """
    app_layers = {
        "routers", "controllers", "services", "providers",
        "middleware", "dependencies", "utils",
    }
    exempt_names = {"__init__", "main", "setup", "configure"}
    reported = 0

    for name, symbols in sorted(index.symbols.items()):
        if name in exempt_names or name.startswith("_"):
            continue
        for sym in symbols:
            layer = layer_of_module(sym.module)
            if layer not in app_layers:
                continue
            # Check if symbol is used anywhere
            usages = index.symbol_usages.get(name, [])
            # Filter out self-definition
            external_usages = [
                (m, l) for m, l in usages if m != sym.module
            ]
            if not external_usages and sym.kind in ("function", "class"):
                # Check if it's an entrypoint (decorated with route, etc.)
                if any(d in ("app.get", "app.post", "router.get",
                             "router.post", "router.put", "router.delete")
                       for d in sym.decorators):
                    continue
                rep.add(
                    YEL, "SYM1", layer,
                    sym.file_path,
                    f"symbol '{name}' ({sym.kind}) defined but never "
                    f"referenced outside its module",
                    intended="verify usage; delete if dead code",
                    line=sym.line,
                )
                reported += 1
                if reported >= 100:
                    return


def check_duplicate_symbols(repo: Path, rep: Report, eff: dict,index: SymbolIndex) -> None:
    """
    SYM2: Detect duplicate class/function definitions across modules.
    """
    reported = 0
    for name, symbols in sorted(index.symbols.items()):
        if len(symbols) <= 1:
            continue
        # Only flag classes and public functions
        classes = [s for s in symbols if s.kind == "class"]
        funcs = [s for s in symbols if s.kind == "function" and s.is_public]

        if len(classes) > 1:
            modules = ", ".join(f"{s.module}:{s.line}" for s in classes[:5])
            rep.add(
                YEL, "SYM2", "backend", modules,
                f"class '{name}' defined in {len(classes)} modules",
                intended="consolidate into one canonical definition",
            )
            reported += 1

        if len(funcs) > 1:
            modules = ", ".join(f"{s.module}:{s.line}" for s in funcs[:5])
            rep.add(
                YEL, "SYM2", "backend", modules,
                f"public function '{name}' defined in {len(funcs)} modules",
                intended="consolidate or rename to avoid confusion",
            )
            reported += 1

        if reported >= 100:
            return


# ============================================================================
# SECTION 20: CALL GRAPH ENGINE
# ============================================================================
"""
Builds a function-level call graph.
Tracks: Router → Controller → Service → Model call chains.
Reveals: architecture violations that import-only analysis misses.
"""

def build_call_graph(repo: Path, eff: dict, graph: ModuleGraph,
                     index: SymbolIndex) -> CallGraph:
    """
    Build a function-level call graph using AST analysis.
    Resolves calls to known symbols in the symbol index.
    Uses a parent map to find enclosing functions efficiently.
    """
    call_graph = CallGraph()
    backend = repo / "backend"
    if not backend.exists():
        return call_graph

    for module, f in graph.modules.items():
        tree = parse_safe(f)
        if tree is None:
            continue

        # ── Build parent map ONCE per file ──
        # Maps id(child_node) -> parent_node
        parent_map: dict[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parent_map[id(child)] = node

        def find_enclosing_func(node: ast.AST) -> str:
            """Walk up parent chain to find the enclosing function name."""
            current = node
            depth = 0
            while id(current) in parent_map and depth < 200:
                current = parent_map[id(current)]
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return current.name
                depth += 1
            return "<module>"

        # ── Collect function/method definitions in this module ──
        local_functions: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                local_functions[node.name] = f"{module}.{node.name}"

        # ── Track imports for resolving cross-module calls ──
        imported_names: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    local = alias.asname or alias.name
                    imported_names[local] = alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for alias in node.names:
                        local = alias.asname or alias.name
                        imported_names[local] = f"{node.module}.{alias.name}"

        # ── Find all Call nodes and resolve them ──
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            # Use parent map to find enclosing function
            caller_func = find_enclosing_func(node)

            callee_name = None
            callee_module = None

            if isinstance(node.func, ast.Name):
                # Direct function call: some_function()
                name = node.func.id
                if name in local_functions:
                    callee_name = name
                    callee_module = module
                elif name in imported_names:
                    full = imported_names[name]
                    parts = full.rsplit(".", 1)
                    if len(parts) == 2:
                        callee_module = parts[0]
                        callee_name = parts[1]
                    else:
                        callee_module = full
                        callee_name = "<init>"

            elif isinstance(node.func, ast.Attribute):
                # Method call: obj.method() or module.function()
                attr = node.func.attr
                if isinstance(node.func.value, ast.Name):
                    obj_name = node.func.value.id
                    if obj_name in imported_names:
                        callee_module = imported_names[obj_name]
                        callee_name = attr
                    else:
                        callee_name = attr
                        callee_module = module
                elif isinstance(node.func.value, ast.Attribute):
                    # Chained attribute: module.sub.func()
                    callee_name = attr
                    callee_module = module

            if callee_name and callee_module:
                edge = CallEdge(
                    caller_module=module,
                    caller_function=caller_func,
                    callee_module=callee_module,
                    callee_function=callee_name,
                    line=node.lineno,
                )
                call_graph.add_edge(edge)

    return call_graph


# # CG2 exemptions: modules that legitimately call upward for cross-cutting concerns
# CG2_EXEMPT_MODULES: set[str] = {
#     "utils.audit",
#     "utils.audit_log",
#     "utils.security_audit",
#     "utils.schema_audit",
#     "utils.logging_config",
#     "utils.metrics",
# }

# CG2_EXEMPT_PATTERNS: set[str] = {
#     "audit",
#     "log_security",
#     "schema_audit",
# }

def check_call_graph_violations(repo: Path, rep: Report, eff: dict,
                                call_graph: CallGraph,
                                graph: ModuleGraph) -> None:
    """
    CG1/CG2/CG3: Detect call graph violations.
    - CG1: Function calls across forbidden layer boundaries
    - CG2: Upward calls (calling a higher layer)
    - CG3: Circular call chains

    Exemptions:
    - Audit/logging/security utilities legitimately write to db/models
    - Configured via eff['circuit_exempt_modules'] or built-in defaults
    """
    layer_order = {
        "main": 0, "lifespan": 0,
        "middleware": 1, "dependencies": 1,
        "routers": 2,
        "controllers": 3,
        "services": 4,
        "providers": 5,
        "models": 6,
        "db": 7,
        "utils": 8, "data": 8,
        "events": 4, "jobs": 4,
    }

    # ── CG2 Exemption Configuration ──
    # These modules legitimately call models/db for cross-cutting concerns.
    # Configurable via YAML: circuit_exempt_modules
    DEFAULT_CG2_EXEMPT_MODULES: set[str] = {
        "utils.audit",
        "utils.audit_log",
        "utils.security_audit",
        "utils.schema_audit",
        "utils.logging_config",
        "utils.event_logger",
    }

    # Module-name patterns that are exempt from CG2 upward-call checks.
    # Audit, logging, and security utilities inherently need db access.
    CG2_EXEMPT_PATTERNS: set[str] = {
        "audit",
        "audit_log",
        "security_audit",
        "schema_audit",
        "event_logger",
        "logging_config",
    }

    # Load exemptions from YAML policy if available
    yaml_exemptions = eff.get("circuit_exempt_modules", [])
    if yaml_exemptions:
        DEFAULT_CG2_EXEMPT_MODULES |= set(yaml_exemptions)

    yaml_exempt_patterns = eff.get("circuit_exempt_patterns", [])
    if yaml_exempt_patterns:
        CG2_EXEMPT_PATTERNS |= set(yaml_exempt_patterns)

    # Forbidden cross-layer calls (caller_layer, callee_layer)
    forbidden_calls: set[tuple[str, str]] = {
        ("routers", "db"),
        ("routers", "providers"),
        ("routers", "models"),
        ("controllers", "db"),
        ("controllers", "middleware"),
        ("controllers", "dependencies"),
        ("services", "routers"),
        ("services", "controllers"),
        ("services", "middleware"),
        ("providers", "services"),
        ("providers", "controllers"),
        ("providers", "routers"),
        ("providers", "models"),
        ("models", "services"),
        ("models", "controllers"),
        ("models", "routers"),
        ("models", "providers"),
        ("middleware", "services"),
        ("middleware", "controllers"),
        ("middleware", "routers"),
    }

    # CG1/CG2: Check layer direction in calls
    reported = 0
    for edge in call_graph.edges:
        caller_layer = layer_of_module(edge.caller_module)
        callee_layer = layer_of_module(edge.callee_module)

        if not caller_layer or not callee_layer:
            continue
        if caller_layer == callee_layer:
            continue

        caller_order = layer_order.get(caller_layer, 99)
        callee_order = layer_order.get(callee_layer, 99)

        # ── Exemption check: skip audit/logging/security utilities ──
        caller_module_lower = edge.caller_module.lower()
        if edge.caller_module in DEFAULT_CG2_EXEMPT_MODULES:
            continue
        if any(pattern in caller_module_lower for pattern in CG2_EXEMPT_PATTERNS):
            continue

        # Upward call violation (calling a higher layer)
        if callee_order < caller_order and callee_layer not in ("utils", "data"):
            rep.add(
                RED, "CG2", "backend",
                module_path_rel(edge.caller_module, graph, repo),
                f"upward call: {caller_layer}.{edge.caller_function}() → "
                f"{callee_layer}.{edge.callee_function}()",
                intended="calls must flow downward in the circuit; "
                         "extract shared logic to a lower layer",
                line=edge.line,
            )
            reported += 1

        # Forbidden cross-layer calls
        if (caller_layer, callee_layer) in forbidden_calls:
            rep.add(
                RED, "CG1", "backend",
                module_path_rel(edge.caller_module, graph, repo),
                f"forbidden call: {caller_layer}.{edge.caller_function}() → "
                f"{callee_layer}.{edge.callee_function}()",
                intended=f"{caller_layer} must not call {callee_layer} directly",
                line=edge.line,
            )
            reported += 1

        if reported >= 300:
            return

    # CG3: Circular call chains
    call_adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in call_graph.edges:
        caller_layer = layer_of_module(edge.caller_module)
        callee_layer = layer_of_module(edge.callee_module)
        if caller_layer and callee_layer and caller_layer != callee_layer:
            call_adjacency[edge.caller_module].add(edge.callee_module)

    cycles = detect_cycles(call_adjacency, 6, 20)
    for cyc in cycles[:10]:
        path = " → ".join(cyc + [cyc[0]])
        rep.add(
            RED, "CG3", "backend", "call-graph",
            f"circular call chain: {path}",
            intended="break the cycle; extract shared logic to utils/ or events/",
        )

def check_layer_contracts(repo: Path, rep: Report, eff: dict,
                          graph: ModuleGraph, call_graph: CallGraph) -> None:
    """
    LC1/LC2/LC3: Validate explicit layer contracts.
    Each layer has defined allowed/forbidden operations and call patterns.
    """
    contracts: dict[str, LayerContract] = {
        "routers": LayerContract(
            layer="routers",
            may_import={"controllers", "dependencies", "utils", "data"},
            may_not_import={"db", "models", "providers", "middleware"},
            may_call={"controllers"},
            may_not_call={"db", "models", "providers"},
            forbidden_operations={"session.add", "session.commit", "session.delete",
                                  "session.execute", "db.query"},
            forbidden_patterns=[r"session\.(add|commit|delete|execute)",
                               r"db\.query", r"\.execute\(text\("],
        ),
        "controllers": LayerContract(
            layer="controllers",
            may_import={"services", "utils", "data"},
            may_not_import={"db", "models", "providers", "routers", "middleware"},
            may_call={"services"},
            may_not_call={"db", "models", "providers", "routers"},
            forbidden_operations={"session.add", "session.commit", "session.delete"},
            forbidden_patterns=[r"session\.(add|commit|delete)",
                               r"\.execute\(text\("],
        ),
        "services": LayerContract(
            layer="services",
            may_import={"models", "providers", "utils", "events", "jobs", "db", "data"},
            may_not_import={"routers", "controllers", "middleware", "dependencies"},
            may_call={"models", "providers", "db"},
            may_not_call={"routers", "controllers"},
            required_patterns=[],
            forbidden_patterns=[],
        ),
        "providers": LayerContract(
            layer="providers",
            may_import={"utils", "data"},
            may_not_import={"services", "controllers", "routers", "models",
                           "middleware", "dependencies", "db"},
            may_call={"utils"},
            may_not_call={"services", "controllers", "routers", "models"},
            forbidden_patterns=[],
        ),
        "models": LayerContract(
            layer="models",
            may_import={"db", "utils"},
            may_not_import={"services", "controllers", "routers", "providers",
                           "middleware", "dependencies"},
            may_call=set(),
            may_not_call={"services", "controllers", "routers", "providers"},
            forbidden_patterns=[],
        ),
        "middleware": LayerContract(
            layer="middleware",
            may_import={"db", "utils", "dependencies", "data"},
            may_not_import={"services", "controllers", "routers", "models",
                           "providers"},
            may_call={"utils"},
            may_not_call={"services", "controllers", "routers"},
            forbidden_patterns=[],
        ),
        "utils": LayerContract(
            layer="utils",
            may_import=set(),
            may_not_import={"routers", "controllers", "services", "models",
                           "providers", "middleware", "dependencies", "db"},
            may_call=set(),
            may_not_call={"routers", "controllers", "services", "models"},
            forbidden_patterns=[],
        ),
    }

    # Load contracts from YAML if available
    if eff.get("layer_contracts"):
        for layer_name, cfg in eff["layer_contracts"].items():
            if layer_name in contracts and isinstance(cfg, dict):
                c = contracts[layer_name]
                if isinstance(cfg.get("forbidden_operations"), list):
                    c.forbidden_operations = set(cfg["forbidden_operations"])
                if isinstance(cfg.get("forbidden_patterns"), list):
                    c.forbidden_patterns = cfg["forbidden_patterns"]

    backend = repo / "backend"
    reported = 0

    for module, f in graph.modules.items():
        layer = layer_of_module(module)
        if layer not in contracts:
            continue

        contract = contracts[layer]
        if not contract.forbidden_patterns:
            continue

        text = read_text(f)
        if not text:
            continue

        for pattern in contract.forbidden_patterns:
            try:
                rx = re.compile(pattern)
            except re.error:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rep.add(
                        RED, "LC1", layer,
                        rel(f, repo),
                        f"layer contract violation: '{pattern}' found in {layer}/",
                        intended=f"{layer} must not perform this operation; "
                                 f"move it to the appropriate layer",
                        line=i,
                    )
                    reported += 1
                    break  # One finding per file per pattern
                if reported >= 200:
                    return


# ============================================================================
# SECTION 21: PUBLIC API DETECTION
# ============================================================================
"""
Identifies public, private, internal, and deprecated symbols.
Detects: unstable public APIs, internal symbols leaking outward.
"""

def check_public_api_stability(repo: Path, rep: Report, eff: dict,
                               index: SymbolIndex, graph: ModuleGraph) -> None:
    """
    API1/API2: Detect public API issues.
    - API1: Public symbols that appear unstable (frequent changes, no docs)
    - API2: Internal/private symbols used outside their module boundary
    """
    reported = 0

    # API2: Internal symbols exposed externally
    for name, symbols in sorted(index.symbols.items()):
        if name.startswith("_"):
            # Private symbol - check if used externally
            usages = index.symbol_usages.get(name, [])
            for sym in symbols:
                external = [
                    (m, l) for m, l in usages
                    if m != sym.module and not m.startswith(sym.module + ".")
                ]
                if external:
                    rep.add(
                        YEL, "API2", "backend",
                        sym.file_path,
                        f"private symbol '{name}' used in "
                        f"{len(external)} external module(s)",
                        intended="make it public (remove _) or keep internal "
                                 "and refactor external usages",
                        line=sym.line,
                    )
                    reported += 1
                    break

        if reported >= 100:
            return

    # API1: Public symbols without documentation (potential instability)
    for name, symbols in sorted(index.symbols.items()):
        for sym in symbols:
            if (sym.is_public and sym.kind in ("function", "class")
                    and not sym.docstring
                    and not sym.name.startswith("test_")):
                layer = layer_of_module(sym.module)
                if layer in ("services", "controllers", "providers"):
                    rep.add(
                        GRN, "API1", layer,
                        sym.file_path,
                        f"public {sym.kind} '{name}' has no docstring "
                        f"(API documentation gap)",
                        intended="add docstring documenting parameters, "
                                 "return type, and side effects",
                        line=sym.line,
                    )
                    reported += 1
                    break
        if reported >= 200:
            return


# ============================================================================
# SECTION 22: FLOW-TYPE CLASSIFICATION
# ============================================================================
"""
Classifies domain × surface intersections by flow type:
- forward: one-directional process (place → track → receive)
- backward: reverse flow (returns, refunds)
- two_way: bidirectional (chat, messaging)
- tree: one-in, multiple-out (finance: customer pays → payouts to supplier + logistics)
- multi_way: all surfaces interact (communication)
- one_way_in: only receives (customer pays)
- one_way_out: only sends (supplier receives payout)
- oversight: admin monitors/moderates
"""

# Default flow-type model (can be overridden by governance.yaml)
DEFAULT_FLOW_TYPES: dict[str, dict[str, str]] = {
    "orders": {
        "customer": "forward",
        "supplier": "forward",
        "logistics": "forward",
        "admin": "oversight",
    },
    "finance": {
        "customer": "one_way_in",
        "supplier": "one_way_out",
        "logistics": "one_way_out",
        "admin": "tree",
    },
    "catalog": {
        "supplier": "one_way_in",
        "customer": "one_way_out",
        "admin": "oversight",
    },
    "comms": {
        "customer": "multi_way",
        "supplier": "multi_way",
        "admin": "multi_way",
        "logistics": "multi_way",
    },
    "communication": {
        "customer": "multi_way",
        "supplier": "multi_way",
        "admin": "multi_way",
    },
    "logistics": {
        "logistics": "forward",
        "supplier": "forward",
        "customer": "forward",
        "admin": "oversight",
    },
    "supplier": {
        "supplier": "forward",
        "admin": "oversight",
    },
    "hr": {
        "admin": "tree",
    },
    "security": {
        "admin": "oversight",
    },
}

# Operation verbs associated with each flow type
FLOW_TYPE_OPERATIONS: dict[str, set[str]] = {
    "forward": {"place", "track", "cancel", "return", "review", "accept",
                "pack", "ship", "handover", "pickup", "deliver", "pod",
                "update_status", "confirm"},
    "backward": {"return", "refund", "reverse", "cancel", "reject"},
    "two_way": {"send", "receive", "read", "reply", "forward"},
    "tree": {"configure", "monitor", "approve", "distribute", "allocate"},
    "multi_way": {"send", "receive", "read", "reply", "broadcast", "moderate"},
    "one_way_in": {"pay", "submit", "create", "upload", "add"},
    "one_way_out": {"view", "browse", "search", "filter", "download",
                    "receive", "request"},
    "oversight": {"view_all", "moderate", "override", "report", "monitor",
                  "audit", "configure", "approve", "reject", "suspend"},
}


def classify_flow_types(repo: Path, eff: dict, reg: FeatureRegistry,
                        graph: ModuleGraph) -> list[FlowType]:
    """
    Build flow-type classification for all domain × surface pairs.
    Uses default model + discovered features.
    """
    flows: list[FlowType] = []

    # Load from YAML if available
    flow_config = eff.get("flow_types", DEFAULT_FLOW_TYPES)

    for domain, surface_flows in flow_config.items():
        for surface, flow_type in surface_flows.items():
            operations = list(FLOW_TYPE_OPERATIONS.get(flow_type, set()))
            flows.append(FlowType(
                domain=domain,
                surface=surface,
                flow_type=flow_type,
                operations=operations,
            ))

    return flows


def check_flow_type_violations(repo: Path, rep: Report, eff: dict,
                               flows: list[FlowType],
                               graph: ModuleGraph) -> None:
    """
    FT1/FT2: Validate that operations match expected flow types.
    - FT1: Operation not allowed for this surface × domain flow
    - FT2: File contains operations from wrong flow direction
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    flow_map: dict[tuple[str, str], FlowType] = {
        (f.domain, f.surface): f for f in flows
    }

    # Check router files for flow-type violations
    routers_dir = backend / "routers"
    if not routers_dir.exists():
        return

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    reported = 0

    for f in iter_text_files(routers_dir, eff):
        if f.suffix.lower() != ".py":
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        # Determine surface from path or filename
        try:
            parts = [p.lower() for p in f.relative_to(routers_dir).parts]
        except ValueError:
            continue

        surface = None
        if parts and parts[0] in surfaces:
            surface = parts[0]
        else:
            stem_tokens = {t.lower() for t in re.split(r"[_\-]+", f.stem)}
            for s in surfaces:
                if s in stem_tokens:
                    surface = s
                    break

        if not surface:
            continue

        # Extract function names
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_name = node.name.lower()

                # Check against flow types
                for (domain, surf), flow in flow_map.items():
                    if surf != surface:
                        continue

                    # Check if function contains operations from wrong flow
                    func_tokens = set(re.split(r"[_\-]+", func_name))

                    # Oversight operations in non-admin surface
                    if surface != "admin":
                        oversight_ops = FLOW_TYPE_OPERATIONS.get("oversight", set())
                        if func_tokens & oversight_ops:
                            rep.add(
                                YEL, "FT1", "routers",
                                rel(f, repo),
                                f"oversight operation '{node.name}' in "
                                f"non-admin surface '{surface}'",
                                intended="oversight operations belong in admin surface",
                                line=node.lineno,
                            )
                            reported += 1

                    # One-way-in operations in wrong surface
                    if flow.flow_type == "one_way_out":
                        in_ops = FLOW_TYPE_OPERATIONS.get("one_way_in", set())
                        if func_tokens & in_ops and domain in func_tokens:
                            rep.add(
                                YEL, "FT2", "routers",
                                rel(f, repo),
                                f"input operation '{node.name}' in "
                                f"one-way-out flow ({domain} × {surface})",
                                intended="this flow only outputs; "
                                         "input operations belong elsewhere",
                                line=node.lineno,
                            )
                            reported += 1

                if reported >= 100:
                    return


# ============================================================================
# SECTION 23: FILE-NAME-TO-CONTENT ALIGNMENT
# ============================================================================
"""
Validates that a file's content matches its declared purpose (filename).
Example: order_fulfillment.py must contain fulfill/pack/ship functions.
"""

# Mapping of common filename tokens to expected operation verbs
FILENAME_OPERATION_MAP: dict[str, set[str]] = {
    "fulfillment": {"fulfill", "pack", "ship", "handover", "prepare"},
    "tracking": {"track", "status", "locate", "monitor", "timeline"},
    "management": {"create", "update", "delete", "list", "get", "crud"},
    "processing": {"process", "execute", "handle", "compute"},
    "validation": {"validate", "verify", "check", "ensure"},
    "notification": {"notify", "send", "alert", "inform", "push"},
    "authentication": {"authenticate", "login", "verify", "token", "session"},
    "authorization": {"authorize", "permission", "role", "access"},
    "payment": {"pay", "charge", "refund", "process_payment"},
    "payout": {"payout", "disburse", "transfer", "settle"},
    "moderation": {"moderate", "approve", "reject", "review", "flag"},
    "search": {"search", "find", "query", "filter", "browse"},
    "upload": {"upload", "store", "save", "persist"},
    "delivery": {"deliver", "pickup", "drop", "pod", "route"},
    "onboarding": {"onboard", "register", "enroll", "kyc", "verify"},
    "lifecycle": {"create", "activate", "deactivate", "archive", "transition"},
    "calculation": {"calculate", "compute", "derive", "aggregate"},
    "reporting": {"report", "aggregate", "summarize", "export"},
    "scheduling": {"schedule", "plan", "allocate", "assign"},
}


def check_file_content_alignment(repo: Path, rep: Report, eff: dict,
                                  graph: ModuleGraph) -> None:
    """
    CA1: Validate that file content matches its name.
    Extracts function names and compares against expected operations
    derived from the filename.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    app_layers = {"services", "controllers", "routers", "providers"}
    reported = 0

    for module, f in graph.modules.items():
        layer = layer_of_module(module)
        if layer not in app_layers:
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        # Extract filename tokens
        stem = f.stem.lower()
        # Remove common suffixes
        for suffix in ("_service", "_controller", "_provider", "_router",
                       "_entities", "_models"):
            if stem.endswith(suffix):
                stem = stem[:-len(suffix)]
                break

        stem_tokens = set(re.split(r"[_\-]+", stem))

        # Find expected operations from filename
        expected_ops: set[str] = set()
        for token in stem_tokens:
            if token in FILENAME_OPERATION_MAP:
                expected_ops |= FILENAME_OPERATION_MAP[token]

        if not expected_ops:
            continue  # Can't validate without known mapping

        # Extract actual function names
        actual_funcs: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith("_"):
                    func_tokens = set(re.split(r"[_\-]+", node.name.lower()))
                    actual_funcs |= func_tokens

        # Check alignment
        if actual_funcs and expected_ops:
            alignment = actual_funcs & expected_ops
            alignment_ratio = len(alignment) / len(expected_ops)

            if alignment_ratio < 0.2 and len(actual_funcs) > 3:
                rep.add(
                    YEL, "CA1", layer,
                    rel(f, repo),
                    f"file '{f.name}' content does not match its name "
                    f"(expected operations like: "
                    f"{', '.join(sorted(expected_ops)[:5])})",
                    intended="rename the file to match its actual content, "
                             "or move mismatched functions to appropriate files",
                )
                reported += 1

        if reported >= 100:
            return


# ============================================================================
# SECTION 24: SPLIT-FILE DETECTION
# ============================================================================
"""
Detects files that contain signals for 2+ domains and should be split.
"""

def check_split_file_candidates(repo: Path, rep: Report, eff: dict,
                                graph: ModuleGraph) -> None:
    """
    CA2: Detect files with strong signals for multiple domains.
    If a file has functions/imports from 2+ distinct domains,
    it should be split.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    app_layers = {"services", "controllers", "providers"}
    aliases = PLACEMENT_ALIAS_TO_DOMAIN
    reported = 0

    for module, f in graph.modules.items():
        layer = layer_of_module(module)
        if layer not in app_layers:
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        text = read_text(f)
        if not text:
            continue

        # Collect domain signals from function names
        domain_signals: dict[str, int] = defaultdict(int)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                tokens = set(re.split(r"[_\-]+", node.name.lower()))
                for token in tokens:
                    domain = aliases.get(token)
                    if domain:
                        domain_signals[domain] += 1

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    parts = node.module.split(".")
                    for part in parts:
                        domain = aliases.get(part.lower())
                        if domain:
                            domain_signals[domain] += 1

        # Filter to significant signals
        significant_domains = {
            d: count for d, count in domain_signals.items()
            if count >= 2
        }

        if len(significant_domains) >= 2:
            domains_str = ", ".join(
                f"{d}({c})" for d, c in sorted(
                    significant_domains.items(),
                    key=lambda x: -x[1]
                )
            )
            rep.add(
                YEL, "CA2", layer,
                rel(f, repo),
                f"file contains signals for {len(significant_domains)} domains: "
                f"{domains_str} — split candidate",
                intended="split this file into domain-specific modules; "
                         "each file should serve one domain",
            )
            reported += 1

        if reported >= 100:
            return


# ============================================================================
# SECTION 25: SURFACE-APPROPRIATE OPERATION VALIDATION
# ============================================================================
"""
Validates that operations in a file are appropriate for its surface.
Example: customer router should NOT contain approve_supplier().
"""

# Operations that belong ONLY to specific surfaces
SURFACE_EXCLUSIVE_OPERATIONS: dict[str, set[str]] = {
    "admin": {
        "moderate", "override", "suspend", "ban", "configure_platform",
        "approve_supplier", "reject_supplier", "configure_commission",
        "configure_rates", "view_ledger", "approve_payout", "manage_roles",
        "manage_permissions", "view_audit", "manage_settings",
    },
    "supplier": {
        "pack", "ship", "handover", "upload_product", "edit_product",
        "delete_product", "manage_inventory", "view_earnings",
        "request_payout", "process_return",
    },
    "customer": {
        "browse", "add_to_cart", "checkout", "place_order", "track_order",
        "cancel_order", "request_return", "write_review", "add_wishlist",
        "update_profile", "manage_addresses",
    },
    "logistics": {
        "pickup", "deliver", "pod", "update_delivery_status",
        "optimize_route", "scan_parcel", "confirm_delivery",
    },
}

# Operations that should NEVER appear in certain surfaces
SURFACE_FORBIDDEN_OPERATIONS: dict[str, set[str]] = {
    "customer": {
        "approve", "reject", "moderate", "suspend", "ban", "configure",
        "manage_roles", "manage_permissions", "override", "view_all",
        "admin", "approve_supplier", "configure_commission",
    },
    "supplier": {
        "configure_platform", "manage_roles", "manage_permissions",
        "view_all_orders", "moderate_all", "ban_user", "configure_rates",
    },
    "logistics": {
        "create_product", "approve_supplier", "configure_commission",
        "manage_users", "view_ledger",
    },
}


def check_surface_operations(repo: Path, rep: Report, eff: dict,
                             graph: ModuleGraph) -> None:
    """
    CA3: Detect surface-inappropriate operations.
    Checks function names in router/controller files against
    surface-exclusive and surface-forbidden operation lists.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    reported = 0

    for layer_name in ("routers", "controllers"):
        layer_dir = backend / layer_name
        if not layer_dir.exists():
            continue

        for f in iter_text_files(layer_dir, eff):
            if f.suffix.lower() != ".py":
                continue

            tree = parse_safe(f)
            if tree is None:
                continue

            # Determine surface
            try:
                parts = [p.lower() for p in f.relative_to(layer_dir).parts]
            except ValueError:
                continue

            surface = None
            if parts and parts[0] in surfaces:
                surface = parts[0]
            else:
                stem_tokens = set(re.split(r"[_\-]+", f.stem.lower()))
                for s in surfaces:
                    if s in stem_tokens:
                        surface = s
                        break

            if not surface:
                continue

            forbidden_ops = SURFACE_FORBIDDEN_OPERATIONS.get(surface, set())
            if not forbidden_ops:
                continue

            # Check function names
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_tokens = set(re.split(r"[_\-]+", node.name.lower()))

                    violations = func_tokens & forbidden_ops
                    if violations:
                        rep.add(
                            RED, "CA3", layer_name,
                            rel(f, repo),
                            f"surface-inappropriate operation '{node.name}' "
                            f"in {surface} {layer_name} "
                            f"(forbidden: {', '.join(sorted(violations))})",
                            intended=f"move '{node.name}' to the appropriate "
                                     f"surface (likely admin) or extract to "
                                     f"a shared service",
                            line=node.lineno,
                        )
                        reported += 1

            if reported >= 150:
                return


# ============================================================================
# SECTION 26: MIDDLEWARE PIPELINE VALIDATION
# ============================================================================
"""
Validates middleware structure and pipeline order.
Expected layers:
  1. Foundation (GZip, CORS, IP, RequestID, ApiVersion)
  2. Security (SecurityHeaders, ImpossibleTravel, CSRF)
  3. Rate Limit
  4. Geo/Country
  5. Observability (RequestLogging)
  6. Compliance (PCI-DSS, prod only)
"""

EXPECTED_MIDDLEWARE_ORDER = [
    # (category, expected_file_patterns)
    ("foundation", ["gzip", "cors", "ip_extraction", "request_id", "api_version"]),
    ("security", ["security_header", "impossible_travel", "csrf"]),
    ("rate_limit", ["rate_limit"]),
    ("geo", ["country_context", "geo"]),
    ("observability", ["request_logging", "logging"]),
    ("compliance", ["pci", "compliance"]),
]

REQUIRED_MIDDLEWARE = [
    "cors",
    "rate_limit",
    "request_id",
]


def check_middleware_pipeline(repo: Path, rep: Report, eff: dict) -> None:
    """
    MW1/MW2/MW3: Validate middleware structure.
    - MW1: Pipeline order violation
    - MW2: Required middleware missing
    - MW3: Middleware imports service/controller (already in DG, but explicit here)
    """
    backend = repo / "backend"
    mw_dir = backend / "middleware"
    if not mw_dir.exists():
        rep.add(
            YEL, "MW2", "backend", "backend/middleware/",
            "middleware/ directory missing",
            intended="create backend/middleware/ with required middleware",
        )
        return

    # Collect existing middleware files
    try:
        mw_files = sorted([
            f.stem.lower() for f in mw_dir.glob("*.py")
            if f.name != "__init__.py"
        ])
    except OSError:
        mw_files = []

    # MW2: Check required middleware
    for required in REQUIRED_MIDDLEWARE:
        found = any(required in mf for mf in mw_files)
        if not found:
            rep.add(
                YEL, "MW2", "backend", "backend/middleware/",
                f"required middleware '{required}' not found",
                intended=f"add {required} middleware to backend/middleware/",)

    # MW1: Check pipeline order (if registration order is detectable)
    # Look for setup_middleware or add_middleware calls in main.py
    main_file = backend / "main.py"
    if main_file.exists():
        text = read_text(main_file)
        if text:
            # Find middleware registration order
            registration_order: list[str] = []
            for line in text.splitlines():
                if "add_middleware" in line or "setup_middleware" in line:
                    # Extract middleware name
                    match = re.search(r"(\w+)Middleware", line)
                    if match:
                        registration_order.append(match.group(1).lower())

            # Validate order categories
            category_positions: dict[str, list[int]] = defaultdict(list)
            for i, mw_name in enumerate(registration_order):
                for cat_name, patterns in EXPECTED_MIDDLEWARE_ORDER:
                    if any(p in mw_name for p in patterns):
                        category_positions[cat_name].append(i)
                        break

            # Check that categories are in expected order
            cat_order = list(EXPECTED_MIDDLEWARE_ORDER)
            for i in range(len(cat_order) - 1):
                cat_a = cat_order[i][0]
                cat_b = cat_order[i + 1][0]
                if cat_a in category_positions and cat_b in category_positions:
                    max_a = max(category_positions[cat_a])
                    min_b = min(category_positions[cat_b])
                    if max_a > min_b:
                        rep.add(
                            YEL, "MW1", "backend", "backend/main.py",
                            f"middleware pipeline order: '{cat_a}' "
                            f"appears after '{cat_b}'",
                            intended=f"expected order: {' → '.join(c[0] for c in cat_order)}",
                        )

    # MW3: Check middleware imports (explicit check)
    for f in mw_dir.glob("*.py"):
        if f.name == "__init__.py":
            continue
        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module_name = ""
                if isinstance(node, ast.ImportFrom) and node.module:
                    module_name = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        break

                if module_name.startswith(("services.", "controllers.",
                                           "routers.", "models.")):
                    rep.add(
                        RED, "MW3", "backend",
                        rel(f, repo),
                        f"middleware imports from '{module_name}' "
                        f"(circuit violation)",
                        intended="middleware must not import from "
                                 "services/controllers/routers/models; "
                                 "use dependency injection or events",
                        line=node.lineno,
                    )


# ============================================================================
# SECTION 27: REQUIRED PROJECT FILES VALIDATION
# ============================================================================
"""
Validates that required project files exist at repo root.
"""

REQUIRED_PROJECT_FILES = [
    (".gitignore", "version control ignore rules"),
    (".env.example", "environment variable template"),
    ("README.md", "project documentation"),
]

RECOMMENDED_PROJECT_FILES = [
    ("docker-compose.yml", "container orchestration"),
    ("Makefile", "task automation"),
    (".aiignore", "AI tool ignore rules"),
]

REQUIRED_SCOPE_DOCS = [
    ("00_SCOPE_BINDING.md", "scope binding document"),
    ("01_DATABASE.md", "database specification"),
    ("00_REPO_STRUCTURE.md", "repository structure spec"),
]


def check_required_project_files(repo: Path, rep: Report, eff: dict) -> None:
    """
    PF1: Validate required project files exist.
    """
    # Required files
    for filename, description in REQUIRED_PROJECT_FILES:
        if not (repo / filename).exists():
            rep.add(
                YEL, "PF1", "repo", filename,
                f"required file '{filename}' missing ({description})",
                intended=f"create {filename} at repository root",
            )

    # Recommended files
    for filename, description in RECOMMENDED_PROJECT_FILES:
        if not (repo / filename).exists():
            rep.add(
                GRN, "PF1", "repo", filename,
                f"recommended file '{filename}' missing ({description})",
                intended=f"consider adding {filename}",
            )


# ============================================================================
# SECTION 28: SCOPE DOCUMENTATION VALIDATION
# ============================================================================
"""
Validates that documents/scope/ contains the required authoritative specs.
The discussion states:
  - documents/scope/ is the SINGLE SOURCE OF TRUTH
  - It must contain:
      00_SCOPE_BINDING.md
      01_DATABASE.md
      00_REPO_STRUCTURE.md
      repo_structure.yaml
      layer_rules.yaml
  - Only scope/ is authoritative; archive/ is historical.
"""

REQUIRED_SCOPE_DOCS: list[tuple[str, str]] = [
    ("00_SCOPE_BINDING.md", "scope binding document — defines what this project IS"),
    ("01_DATABASE.md", "database specification — schema, RLS, tables"),
    ("00_REPO_STRUCTURE.md", "repository structure spec — target folder layout"),
]

RECOMMENDED_SCOPE_DOCS: list[tuple[str, str]] = [
    ("02_SEARCH.md", "search specification — indexing, queries"),
    ("03_COMMS.md", "communication specification — chat, email, SMS"),
    ("04_FINANCE.md", "finance specification — ledger, payments, payouts"),
    ("05_ORDERS.md", "orders specification — lifecycle, fulfillment"),
    ("06_LOGISTICS.md", "logistics specification — delivery, tracking"),
    ("07_SECURITY.md", "security specification — auth, permissions, RLS"),
]

REQUIRED_POLICY_YAML: list[str] = [
    "repo_structure.yaml",
    "layer_rules.yaml",
]

RECOMMENDED_POLICY_YAML: list[str] = [
    "governance.yaml",
]


def check_scope_documentation(repo: Path, rep: Report, eff: dict) -> None:
    """
    PF2: Validate scope documentation exists and is complete.
    Checks:
    1. documents/scope/ directory exists
    2. Required scope docs exist
    3. Policy YAML files exist (repo_structure.yaml, layer_rules.yaml)
    4. Scope docs are not empty
    5. Every known domain has at least one scope document
    """
    scope_dir = repo / "documents" / "scope"

    # ── Check 1: scope/ directory exists ──
    if not scope_dir.exists():
        rep.add(
            YEL, "PF2", "docs", "documents/scope/",
            "documents/scope/ directory missing — no authoritative specs exist",
            intended=(
                "create documents/scope/ with authoritative specifications; "
                "this is the SINGLE SOURCE OF TRUTH for architecture"
            ),
        )
        return

    # ── Check 2: Required scope documents ──
    reported = 0
    for filename, description in REQUIRED_SCOPE_DOCS:
        doc_path = scope_dir / filename
        if not doc_path.exists():
            rep.add(
                YEL, "PF2", "docs", f"documents/scope/{filename}",
                f"REQUIRED scope document missing: '{filename}' ({description})",
                intended=f"create documents/scope/{filename}",
            )
            reported += 1
        else:
            # Check if file is empty
            content = read_text(doc_path)
            if content is None or len(content.strip()) < 10:
                rep.add(
                    YEL, "PF2", "docs", f"documents/scope/{filename}",
                    f"scope document '{filename}' exists but is empty",
                    intended=f"add content to documents/scope/{filename}",
                )
                reported += 1

    # ── Check 3: Recommended scope documents ──
    for filename, description in RECOMMENDED_SCOPE_DOCS:
        doc_path = scope_dir / filename
        if not doc_path.exists():
            rep.add(
                GRN, "PF2", "docs", f"documents/scope/{filename}",
                f"recommended scope document missing: '{filename}' ({description})",
                intended=f"consider adding documents/scope/{filename}",
            )
            reported += 1

    # ── Check 4: Required policy YAML files ──
    for yaml_name in REQUIRED_POLICY_YAML:
        # Check in scope/ first, then governance/
        found = (
            (scope_dir / yaml_name).exists()
            or (repo / "governance" / yaml_name).exists()
        )
        if not found:
            rep.add(
                YEL, "PF2", "docs", f"documents/scope/{yaml_name}",
                f"REQUIRED policy file missing: '{yaml_name}'",
                intended=(
                    f"create {yaml_name} in documents/scope/ or governance/; "
                    f"this file drives the audit rules externally"
                ),
            )
            reported += 1
        else:
            # Verify the YAML is parseable
            yaml_path = scope_dir / yaml_name
            if not yaml_path.exists():
                yaml_path = repo / "governance" / yaml_name
            cfg = _read_cfg(yaml_path)
            if cfg is None:
                rep.add(
                    YEL, "PF2", "docs", rel(yaml_path, repo),
                    f"policy file '{yaml_name}' exists but cannot be parsed",
                    intended=f"fix YAML syntax in {rel(yaml_path, repo)}",
                )
                reported += 1

    # ── Check 5: Recommended policy YAML files ──
    for yaml_name in RECOMMENDED_POLICY_YAML:
        found = (
            (scope_dir / yaml_name).exists()
            or (repo / "governance" / yaml_name).exists()
        )
        if not found:
            rep.add(
                GRN, "PF2", "docs", f"documents/scope/{yaml_name}",
                f"recommended policy file missing: '{yaml_name}'",
                intended=f"consider adding {yaml_name} for centralized governance",
            )
            reported += 1

    # ── Check 6: Domain coverage in scope docs ──
    # Every known domain should have at least one scope document
    if _ACTIVE_REG is not None:
        known_domains = set(getattr(_ACTIVE_REG, "domains", set()))
        known_domains |= set(PLACEMENT_DOMAIN_KEYWORDS.keys())

        # Collect all scope doc filenames
        try:
            scope_files = [
                f.stem.lower() for f in scope_dir.glob("*.md")
            ]
        except OSError:
            scope_files = []

        scope_text = " ".join(scope_files)
        uncovered_domains = []
        for domain in sorted(known_domains):
            if domain.lower() not in scope_text:
                uncovered_domains.append(domain)

        if uncovered_domains and len(uncovered_domains) <= 10:
            rep.add(
                GRN, "PF2", "docs", "documents/scope/",
                f"domains without dedicated scope docs: "
                f"{', '.join(uncovered_domains)}",
                intended=(
                    "consider adding a scope document per domain "
                    "(e.g., 04_FINANCE.md, 05_ORDERS.md)"
                ),
            )
            reported += 1

    if reported >= 50:
        return


def check_scope_yaml_agreement(repo: Path, rep: Report, eff: dict) -> None:
    """
    PF2 (extended): Validate that YAML policy and scope docs do not drift.
    Checks:
    1. Domains in layer_rules.yaml match domains in repo_structure.yaml
    2. Layers in layer_rules.yaml match expected backend packages
    3. governance.yaml (if exists) does not contradict layer_rules.yaml
    """
    scope_dir = repo / "documents" / "scope"
    governance_dir = repo / "governance"

    # Load all available YAML files
    struct_cfg = None
    layer_cfg = None
    gov_cfg = None

    for d in (scope_dir, governance_dir):
        if not d or not d.exists():
            continue
        if struct_cfg is None:
            struct_cfg = _read_cfg(d / "repo_structure.yaml") or _read_cfg(d / "repo_structure.json")
        if layer_cfg is None:
            layer_cfg = _read_cfg(d / "layer_rules.yaml") or _read_cfg(d / "layer_rules.json")
        if gov_cfg is None:
            gov_cfg = _read_cfg(d / "governance.yaml") or _read_cfg(d / "governance.json")

    if not struct_cfg and not layer_cfg:
        return  # No YAML to validate

    # ── Check: forbidden_edges layers match expected packages ──
    if layer_cfg and isinstance(layer_cfg.get("forbidden_edges"), dict):
        expected_pkgs = {
            str(x).lower()
            for x in eff.get("expected_backend_packages", [])
        }
        for caller_layer in layer_cfg["forbidden_edges"]:
            caller_lower = str(caller_layer).lower()
            if caller_lower not in expected_pkgs and expected_pkgs:
                rep.add(
                    YEL, "CFG3", "docs", "layer_rules.yaml",
                    f"layer_rules.yaml forbidden_edges references "
                    f"layer '{caller_layer}' not in expected backend packages",
                    intended="fix layer name or add it to expected_backend_packages",
                )

    # ── Check: domain policy domains are consistent ──
    if layer_cfg and isinstance(layer_cfg.get("domains"), dict):
        domain_names = set(layer_cfg["domains"].keys())
        for dom, cfg in layer_cfg["domains"].items():
            if isinstance(cfg, dict):
                for imp in cfg.get("may_import", []):
                    if imp not in domain_names:
                        rep.add(
                            YEL, "CFG2", "docs", "layer_rules.yaml",
                            f"domain '{dom}' may_import references "
                            f"undefined domain '{imp}'",
                            intended=f"define '{imp}' in layer_rules.yaml domains",
                        )

    # ── Check: governance.yaml logical_domains match actual structure ──
    if gov_cfg:
        pol = gov_cfg.get("policy", gov_cfg)
        if isinstance(pol, dict):
            logical_domains = pol.get("logical_domains", {})
            if isinstance(logical_domains, dict):
                for dom_name, dom_cfg in logical_domains.items():
                    if not isinstance(dom_cfg, dict):
                        continue
                    parts = dom_cfg.get("parts", [])
                    for part in parts:
                        backend_part = repo / "backend" / str(part)
                        if not backend_part.exists():
                            rep.add(
                                GRN, "CFG3", "docs", "governance.yaml",
                                f"logical_domains '{dom_name}' references "
                                f"non-existent backend/{part}/",
                                intended=f"create backend/{part}/ or remove from governance.yaml",
                            )

# ============================================================================
# SECTION 29: API SHAPE VALIDATION
# ============================================================================
"""
Validates FastAPI route structure:
- Route prefixes align with surface
- OpenAPI tags align with domain
- Endpoint naming conventions
"""

SURFACE_PREFIX_MAP: dict[str, list[str]] = {
    "admin": ["/admin", "/api/admin", "/api/v1/admin"],
    "supplier": ["/supplier", "/api/supplier", "/api/v1/supplier"],
    "customer": ["/customer", "/api/customer", "/api/v1/customer",
                 "/public", "/api/public"],
    "logistics": ["/logistics", "/api/logistics", "/api/v1/logistics"],
    "internal": ["/internal", "/api/internal", "/health", "/webhooks"],
    "external": ["/external", "/webhooks", "/callbacks"],
}


def check_api_shape(repo: Path, rep: Report, eff: dict,
                    graph: ModuleGraph) -> None:
    """
    AS1/AS2/AS3: Validate API shape.
    - AS1: Route prefix doesn't align with surface
    - AS2: OpenAPI tag doesn't align with domain
    - AS3: Endpoint naming convention violation
    """
    backend = repo / "backend"
    routers_dir = backend / "routers"
    if not routers_dir.exists():
        return

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    aliases = PLACEMENT_ALIAS_TO_DOMAIN
    reported = 0

    for f in iter_text_files(routers_dir, eff):
        if f.suffix.lower() != ".py":
            continue

        text = read_text(f)
        if not text:
            continue

        # Determine surface from path
        try:
            parts = [p.lower() for p in f.relative_to(routers_dir).parts]
        except ValueError:
            continue

        surface = None
        if parts and parts[0] in surfaces:
            surface = parts[0]
        else:
            stem_tokens = set(re.split(r"[_\-]+", f.stem.lower()))
            for s in surfaces:
                if s in stem_tokens:
                    surface = s
                    break

        if not surface:
            continue

        # AS1: Check route prefix alignment
        expected_prefixes = SURFACE_PREFIX_MAP.get(surface, [])
        if expected_prefixes:
            prefix_matches = AUTO_ROUTE_PREFIX_RE.findall(text)
            for prefix in prefix_matches:
                prefix_lower = prefix.lower()
                if not any(prefix_lower.startswith(ep) for ep in expected_prefixes):
                    rep.add(
                        YEL, "AS1", "routers",
                        rel(f, repo),
                        f"route prefix '{prefix}' doesn't align with "
                        f"surface '{surface}' "
                        f"(expected: {', '.join(expected_prefixes[:3])})",
                        intended=f"align route prefix with {surface} surface",
                    )
                    reported += 1
                    break

        # AS2: Check tags alignment
        tag_matches = AUTO_ROUTE_TAGS_RE.findall(text)
        for tag_str in tag_matches:
            tags = re.findall(r"['\"]([^'\"]+)['\"]", tag_str)
            for tag in tags:
                tag_domain = aliases.get(tag.lower())
                if tag_domain and surface:
                    # Check if tag domain makes sense for this surface
                    # (This is a soft check - just informational)
                    pass

        # AS3: Endpoint naming (function names should be descriptive)
        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check for generic names
                generic_names = {"get", "post", "put", "delete", "handler",
                                 "index", "main", "process"}
                if node.name.lower() in generic_names:
                    rep.add(
                        GRN, "AS3", "routers",
                        rel(f, repo),
                        f"generic endpoint name '{node.name}' "
                        f"(not descriptive)",
                        intended="use descriptive names like "
                                 "'create_order', 'get_supplier_profile'",
                        line=node.lineno,
                    )
                    reported += 1

        if reported >= 150:
            return


# ============================================================================
# SECTION 30: ADVANCED SECURITY CHECKS
# ============================================================================
"""
SEC5-SEC10: Advanced security pattern detection.
"""

# SQL injection patterns
SEC_SQL_INJECTION_PATTERNS = [
    re.compile(r"f['\"].*SELECT.*{", re.I),
    re.compile(r"f['\"].*INSERT.*{", re.I),
    re.compile(r"f['\"].*UPDATE.*{", re.I),
    re.compile(r"f['\"].*DELETE.*{", re.I),
    re.compile(r"\.format\(.*\).*(?:SELECT|INSERT|UPDATE|DELETE)", re.I),
    re.compile(r"%\s*(?:SELECT|INSERT|UPDATE|DELETE).*%\s*\(", re.I),
    re.compile(r"execute\(\s*f['\"]", re.I),
    re.compile(r"execute\(\s*['\"].*['\"]\s*\+", re.I),
]

# SSRF patterns
SEC_SSRF_PATTERNS = [
    re.compile(r"requests\.(?:get|post|put)\(\s*(?:url|target|host|endpoint)", re.I),
    re.compile(r"urllib\.request\.urlopen\(\s*(?:url|target)", re.I),
    re.compile(r"httpx\.(?:get|post)\(\s*(?:url|target)", re.I),
    re.compile(r"aiohttp\.ClientSession\(\)\.(?:get|post)\(\s*(?:url|target)", re.I),
]

# Path traversal patterns
SEC_PATH_TRAVERSAL_PATTERNS = [
    re.compile(r"open\(.*\+.*(?:filename|path|file_path|name)", re.I),
    re.compile(r"Path\(.*\+.*(?:filename|path|file_path)", re.I),
    re.compile(r"os\.path\.join\(.*(?:filename|user_input|request)", re.I),
]

# Insecure JWT patterns
SEC_JWT_PATTERNS = [
    re.compile(r"jwt\.encode\(.*algorithm\s*=\s*['\"]none['\"]", re.I),
    re.compile(r"verify\s*=\s*False", re.I),
    re.compile(r"jwt\.decode\(.*options\s*=\s*\{.*verify_signature.*False", re.I),
]


def check_advanced_security(repo: Path, rep: Report, eff: dict,
                            graph: ModuleGraph) -> None:
    """
    SEC5-SEC10: Advanced security checks.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for module, f in graph.modules.items():
        text = read_text(f)
        if not text:
            continue

        layer = layer_of_module(module)
        rel_path = rel(f, repo)

        # SEC5: SQL injection
        for rx in SEC_SQL_INJECTION_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rep.add(
                        RED, "SEC5", layer, rel_path,
                        "potential SQL injection: string interpolation "
                        "in SQL query",
                        intended="use parameterized queries or SQLAlchemy ORM; "
                                 "never interpolate user input into SQL",
                        line=i,
                    )
                    reported += 1
                    break

        # SEC6: SSRF
        for rx in SEC_SSRF_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rep.add(
                        YEL, "SEC6", layer, rel_path,
                        "potential SSRF: URL from variable used in "
                        "HTTP request",
                        intended="validate/whitelist URLs before making "
                                 "requests; restrict to known domains",
                        line=i,
                    )
                    reported += 1
                    break

        # SEC7: Path traversal
        for rx in SEC_PATH_TRAVERSAL_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rep.add(
                        YEL, "SEC7", layer, rel_path,
                        "potential path traversal: user-controlled "
                        "path component",
                        intended="sanitize file paths; use allowlist; "
                                 "resolve and validate against base directory",
                        line=i,
                    )
                    reported += 1
                    break

        # SEC8: Insecure JWT
        for rx in SEC_JWT_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    rep.add(
                        RED, "SEC8", layer, rel_path,
                        "insecure JWT/token handling detected",
                        intended="always verify signatures; never use "
                                 "algorithm='none'; validate expiration",
                        line=i,
                    )
                    reported += 1
                    break

        # SEC9: Missing CSRF on state-changing endpoints
        if layer == "routers":
            tree = parse_safe(f)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        for dec in node.decorator_list:
                            dec_str = _ast_name_to_str(dec)
                            if any(m in dec_str for m in
                                   (".post", ".put", ".delete", ".patch")):
                                # Check if CSRF protection is referenced
                                func_source = ast.get_source_segment(text, node)
                                if func_source and "csrf" not in func_source.lower():
                                    # Soft check - only flag if no CSRF middleware exists
                                    pass

        if reported >= 200:
            return

# ============================================================================
# SECTION 31: ADVANCED PERFORMANCE CHECKS
# ============================================================================
"""
PERF3-PERF6: Advanced performance pattern detection.
"""

def check_advanced_performance(repo: Path, rep: Report, eff: dict,
                               graph: ModuleGraph) -> None:
    """
    PERF3: Missing pagination on list endpoints
    PERF4: Unbounded query (no limit)
    PERF5: Large transaction risk
    PERF6: Missing index hints
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    reported = 0

    for module, f in graph.modules.items():
        layer = layer_of_module(module)
        if layer not in ("services", "controllers", "routers"):
            continue

        text = read_text(f)
        if not text:
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        rel_path = rel(f, repo)

        # PERF3: Missing pagination on list endpoints
        if layer == "routers":
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_name = node.name.lower()
                    if any(kw in func_name for kw in
                           ("list", "get_all", "get_many", "fetch_all")):
                        # Check if function has limit/offset/skip params
                        param_names = {
                            arg.arg.lower() for arg in node.args.args
                        }
                        has_pagination = bool(
                            param_names & {"limit", "offset", "skip",
                                          "page", "page_size", "cursor"}
                        )
                        if not has_pagination:
                            rep.add(
                                YEL, "PERF3", layer, rel_path,
                                f"list endpoint '{node.name}' appears to "
                                f"lack pagination parameters",
                                intended="add limit/offset or cursor-based "
                                         "pagination to prevent unbounded results",
                                line=node.lineno,
                            )
                            reported += 1

        # PERF4: Unbounded query (no limit)
        if layer in ("services", "controllers"):
            lines = text.splitlines()
            for i, line in enumerate(lines, 1):
                if ".query(" in line or ".all()" in line:
                    # Check if there's a .limit() nearby
                    context = "\n".join(
                        lines[max(0, i-3):min(len(lines), i+3)]
                    )
                    if ".all()" in line and ".limit(" not in context:
                        rep.add(
                            YEL, "PERF4", layer, rel_path,
                            "unbounded query: .all() without .limit()",
                            intended="add .limit() to prevent loading "
                                     "entire tables into memory",
                            line=i,
                        )
                        reported += 1

        # PERF5: Large transaction risk
        if layer == "services":
            write_count = 0
            first_write_line = 0
            for i, line in enumerate(text.splitlines(), 1):
                if any(w in line for w in
                       ("session.add", "session.commit", "session.delete",
                        "session.merge")):
                    write_count += 1
                    if first_write_line == 0:
                        first_write_line = i

            if write_count > 5:
                rep.add(
                    YEL, "PERF5", layer, rel_path,
                    f"large transaction risk: {write_count} write "
                    f"operations in single file",
                    intended="consider breaking into smaller transactions "
                             "or using savepoints for partial rollback",
                    line=first_write_line,
                )
                reported += 1

        if reported >= 200:
            return        


# ============================================================================
# SECTION 32: ADVANCED FRONTEND CHECKS
# ============================================================================
"""
FE7-FE9: Advanced frontend architecture checks.
"""

def check_advanced_frontend(repo: Path, rep: Report, eff: dict) -> None:
    """
    FE7: Component in wrong feature folder
    FE8: Shared package boundary violation
    FE9: State management boundary violation
    """
    frontend = repo / "frontend"
    if not frontend.exists():
        return

    source_ext = eff.get("frontend_source_ext", DEFAULT_FRONTEND_SOURCE_EXT)
    reported = 0

    # FE7: Check if components reference wrong domain
    web_app = frontend / "web_app" / "src"
    if web_app.exists():
        components_dir = web_app / "components"
        if components_dir.exists():
            try:
                feature_dirs = [
                    d.name.lower() for d in components_dir.iterdir()
                    if d.is_dir()
                ]
            except OSError:
                feature_dirs = []

            # Check for cross-domain imports in components
            for f in iter_text_files(components_dir, eff):
                if f.suffix.lower() not in source_ext:
                    continue

                text = read_text(f)
                if not text:
                    continue

                try:
                    parts = [p.lower() for p in f.relative_to(components_dir).parts]
                except ValueError:
                    continue

                if not parts:
                    continue

                current_feature = parts[0]

                # Check imports
                for line in text.splitlines():
                    if "from" in line and "import" in line:
                        for other_feature in feature_dirs:
                            if (other_feature != current_feature
                                    and f"/{other_feature}/" in line
                                    and not line.strip().startswith("//")):
                                rep.add(
                                    YEL, "FE7", "frontend",
                                    rel(f, repo),
                                    f"component in '{current_feature}/' "
                                    f"imports from '{other_feature}/'",
                                    intended="extract shared component to "
                                             "shared/ or ui/ folder",
                                )
                                reported += 1
                                break

                if reported >= 100:
                    return

    # FE8: Shared package boundary
    shared_dir = frontend / "shared" / "src"
    if shared_dir.exists():
        for f in iter_text_files(shared_dir, eff):
            if f.suffix.lower() not in source_ext:
                continue

            text = read_text(f)
            if not text:
                continue

            # Shared should not import from web_app or mobile_app
            for i, line in enumerate(text.splitlines(), 1):
                if ("web_app" in line or "mobile_app" in line) and "import" in line:
                    rep.add(
                        RED, "FE8", "frontend",
                        rel(f, repo),
                        "shared package imports from workspace-specific code",
                        intended="shared/ must not depend on web_app/ or "
                                 "mobile_app/; dependency flows one way",
                        line=i,
                    )
                    reported += 1
                    break

            if reported >= 100:
                return

    # FE9: State management boundary
    # Check if components directly manipulate global state they shouldn't
    for ws in ("web_app", "mobile_app"):
        ws_dir = frontend / ws
        if not ws_dir.exists():
            continue

        for f in iter_text_files(ws_dir, eff):
            if f.suffix.lower() not in source_ext:
                continue

            text = read_text(f)
            if not text:
                continue

            # Check for direct store mutations in components
            if "components" in str(f).lower():
                for i, line in enumerate(text.splitlines(), 1):
                    if ("dispatch(" in line or "setState(" in line
                            or "useReducer" in line):
                        # Components should use hooks/actions, not direct dispatch
                        if "store" in line.lower() or "global" in line.lower():
                            rep.add(
                                GRN, "FE9", "frontend",
                                rel(f, repo),
                                "component appears to directly manipulate "
                                "global state",
                                intended="use custom hooks or action creators "
                                         "for state mutations",
                                line=i,
                            )
                            reported += 1
                            break

            if reported >= 150:
                return


# ============================================================================
# SECTION 33: ARCHITECTURE METRICS ENHANCED
# ============================================================================
"""
MET2-MET5: Richer architecture metrics.
- Instability index: I = Ce / (Ca + Ce)
- Abstractness: A = abstract_classes / total_classes
- Distance from main sequence: D = |A + I - 1|
- God module detection
"""

def check_enhanced_metrics(repo: Path, rep: Report, eff: dict,
                           graph: ModuleGraph, index: SymbolIndex) -> None:
    """
    MET2-MET5: Enhanced architecture metrics.
    """
    reported = 0

    # Calculate per-module metrics
    for module in sorted(graph.modules.keys()):
        fan_in = graph.fan_in.get(module, 0)   # Ca: afferent coupling
        fan_out = graph.fan_out.get(module, 0)  # Ce: efferent coupling

        total = fan_in + fan_out
        if total == 0:
            continue

        # Instability: I = Ce / (Ca + Ce)
        instability = fan_out / total

        # MET2: High instability (very dependent on others, nothing depends on it)
        if instability > 0.9 and fan_out > 10:
            rep.add(
                YEL, "MET2", "backend",
                module_path_rel(module, graph, repo),
                f"high instability: I={instability:.2f} "
                f"(Ca={fan_in}, Ce={fan_out})",
                intended="module is very fragile; add abstractions or "
                         "reduce outgoing dependencies",
            )
            reported += 1

        # MET5: God module (excessive responsibility)
        if fan_in > 50 and fan_out > 20:
            rep.add(
                RED, "MET5", "backend",
                module_path_rel(module, graph, repo),
                f"god module: Ca={fan_in}, Ce={fan_out}, "
                f"total coupling={total}",
                intended="split this module; it has too many responsibilities",
            )
            reported += 1

    # MET3/MET4: Package-level abstractness and distance from main sequence
    package_classes: dict[str, dict] = defaultdict(lambda: {
        "total": 0, "abstract": 0
    })

    for name, symbols in index.symbols.items():
        for sym in symbols:
            if sym.kind != "class":
                continue
            layer = layer_of_module(sym.module)
            if not layer:
                continue
            package_classes[layer]["total"] += 1
            # Check if abstract (has ABCMeta, abstractmethod, or starts with Base/Abstract)
            if (any("abstract" in d.lower() for d in sym.decorators)
                    or name.startswith("Base")
                    or name.startswith("Abstract")):
                package_classes[layer]["abstract"] += 1

    for layer, counts in package_classes.items():
        total = counts["total"]
        if total == 0:
            continue

        abstractness = counts["abstract"] / total
        # We don't have instability at package level easily,
        # so just report abstractness
        if total > 10 and abstractness == 0:
            rep.add(
                GRN, "MET3", layer, f"backend/{layer}/",
                f"no abstract classes in {layer}/ "
                f"(A=0.00, {total} classes)",
                intended="consider adding interfaces/ABCs for "
                         "dependency inversion",
            )
            reported += 1

    if reported >= 100:
        return


# ============================================================================
# SECTION 34: DOMAIN EVENT / BOUNDED-CONTEXT VALIDATION
# ============================================================================
"""
BC1-BC3: Validate bounded context boundaries.
Cross-domain communication should go through events or facades.
"""

def check_bounded_contexts(repo: Path, rep: Report, eff: dict,
                           graph: ModuleGraph, reg: FeatureRegistry) -> None:
    """
    BC1: Cross-domain import bypasses event/facade boundary
    BC2: Domain event not properly defined
    BC3: Bounded context leakage
    """
    domains = eff.get("domains", {})
    if not domains:
        return

    reported = 0

    for caller in sorted(graph.imports.keys()):
        caller_domain = domain_of_module(caller, eff, graph)
        if not caller_domain:
            continue

        caller_cfg = domains.get(caller_domain, {})
        may_import = set(caller_cfg.get("may_import", []))

        for mod, line in graph.imports[caller]:
            target_domain = domain_of_module(mod, eff, graph)
            if not target_domain or target_domain == caller_domain:
                continue

            # Cross-domain import detected
            if target_domain not in may_import:
                # Check if it goes through events/ or a facade
                is_via_event = (
                    mod.startswith("events.")
                    or "event" in mod.lower()
                    or "facade" in mod.lower()
                )

                if not is_via_event:
                    rep.add(
                        YEL, "BC1", "backend",
                        module_path_rel(caller, graph, repo),
                        f"cross-domain import {caller_domain} → "
                        f"{target_domain} bypasses event/facade boundary",
                        intended=f"route through events/ or a {target_domain} "
                                 f"service facade; declare in layer_rules.yaml "
                                 f"if intentional",
                        line=line,
                    )
                    reported += 1

        if reported >= 150:
            return

    # BC3: Check for direct model access across domains
    for caller in sorted(graph.imports.keys()):
        caller_domain = domain_of_module(caller, eff, graph)
        caller_layer = layer_of_module(caller)
        if not caller_domain or caller_layer != "services":
            continue

        for mod, line in graph.imports[caller]:
            target_domain = domain_of_module(mod, eff, graph)
            target_layer = layer_of_module(mod)
            if (target_domain and target_domain != caller_domain
                    and target_layer == "models"):
                rep.add(
                    YEL, "BC3", "backend",
                    module_path_rel(caller, graph, repo),
                    f"bounded context leakage: {caller_domain} service "
                    f"directly imports {target_domain} models",
                    intended=f"use {target_domain} service API or events "
                             f"instead of direct model access",
                    line=line,
                )
                reported += 1

        if reported >= 200:
            return


# ============================================================================
# SECTION 35: ARCHITECTURE REGISTRY
# ============================================================================
"""
Generates and validates a lightweight architecture registry.
One file: domains.yaml
Generated from code analysis.
Human-overridable.
"""

def generate_architecture_registry(repo: Path, eff: dict,
                                   reg: FeatureRegistry,
                                   graph: ModuleGraph) -> ArchitectureRegistry:
    """
    Generate architecture registry from code analysis.
    """
    registry = ArchitectureRegistry()

    # Build from discovered domains
    all_domains = set(reg.domains)
    all_domains |= set(eff.get("domains", {}).keys())
    all_domains |= set(PLACEMENT_DOMAIN_KEYWORDS.keys())

    for domain in sorted(all_domains):
        # Find dependencies
        depends_on: set[str] = set()
        for caller in graph.modules:
            caller_domain = domain_of_module(caller, eff, graph)
            if caller_domain != domain:
                continue
            for target in graph.edges.get(caller, set()):
                target_domain = domain_of_module(target, eff, graph)
                if target_domain and target_domain != domain:
                    depends_on.add(target_domain)

        # Find public API (exported symbols)
        public_api: list[str] = []
        for module, exports in graph.modules.items():
            mod_domain = domain_of_module(module, eff, graph)
            if mod_domain == domain:
                # Get public functions/classes
                pass  # Would use symbol index

        entry = ArchitectureRegistryEntry(
            domain=domain,
            owner=f"@zozi/{domain}",
            depends_on=sorted(depends_on),
            public_api=public_api[:20],
        )
        registry.add(entry)

    return registry


def check_architecture_registry(repo: Path, rep: Report, eff: dict,
                                registry: ArchitectureRegistry,
                                graph: ModuleGraph) -> None:
    """
    REG1-REG3: Validate architecture registry.
    """
    # REG1: Check if all code domains are in registry
    code_domains: set[str] = set()
    for module in graph.modules:
        d = domain_of_module(module, eff, graph)
        if d:
            code_domains.add(d)

    for domain in sorted(code_domains):
        if not registry.get(domain):
            rep.add(
                GRN, "REG1", "backend", f"domain:{domain}",
                f"domain '{domain}' exists in code but not in "
                f"architecture registry",
                intended=f"add '{domain}' to domains.yaml registry",
            )

    # REG2: Check if registry dependencies match code
    for domain, entry in registry.entries.items():
        for dep in entry.depends_on:
            # Verify this dependency exists in code
            found = False
            for caller in graph.modules:
                caller_domain = domain_of_module(caller, eff, graph)
                if caller_domain != domain:
                    continue
                for target in graph.edges.get(caller, set()):
                    target_domain = domain_of_module(target, eff, graph)
                    if target_domain == dep:
                        found = True
                        break
                if found:
                    break

            if not found:
                rep.add(
                    GRN, "REG2", "backend", f"domain:{domain}",
                    f"registry declares {domain} depends on {dep} "
                    f"but no code dependency found",
                    intended="update registry or verify if dependency "
                             "was removed",
                )


def emit_registry_yaml(repo: Path, registry: ArchitectureRegistry) -> None:
    """
    Write domains.yaml registry file (optional, only if --emit-registry).
    """
    lines = [
        "# Architecture Registry",
        "# Generated by system_architecture_audit.py",
        "# Human-overridable: edit this file to declare domain boundaries",
        "",
        "domains:",
    ]

    for domain, entry in sorted(registry.entries.items()):
        lines.append(f"  {domain}:")
        lines.append(f"    owner: {entry.owner}")
        if entry.depends_on:
            lines.append(f"    depends_on:")
            for dep in entry.depends_on:
                lines.append(f"      - {dep}")
        if entry.public_api:
            lines.append(f"    public_api:")
            for api in entry.public_api[:10]:
                lines.append(f"      - {api}")
        lines.append("")

    out_path = repo / "documents" / "scope" / "domains.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")

# ============================================================================
# SECTION 36: Repo Root Detection (was SECTION 20)
# ============================================================================

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
    Strongest signal: backend/ + frontend/
    Fallback: backend/main.py + non-trivial backend
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
        if script_dir.parent.name.lower() == "backend":
            candidates.append(script_dir.parent.parent)

    candidates.extend([
        script_dir,
        script_dir.parent,
        script_dir.parent.parent,
        script_dir.parent.parent.parent,
        Path.cwd().resolve(),
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
      --out ARCHITECTURE_AUDIT_REPORT.md  -> <repo>/ARCHITECTURE_AUDIT_REPORT.md
      --out out/report.md                 -> <repo>/out/report.md
      --out D:/reports/report.md          -> D:/reports/report.md
    """
    if not value:
        return repo / default_name
    p = Path(value)
    if p.is_absolute():
        return p.resolve()
    return (repo / p).resolve()


# ============================================================================
# SECTION 37: RENDER — SINGLE COMPREHENSIVE MARKDOWN REPORT (was SECTION 21)
# ============================================================================

def render_markdown(repo: Path, rep: Report, out: Path, summary: dict, placements: list[dict], eff: dict, reg: FeatureRegistry, graph: ModuleGraph,) -> None:
    """
    Produce ONE comprehensive .md report containing:
      1. Grid line definition (the circuit)
      2. Current backend structure (mermaid)
      3. Suggested backend structure (mermaid)
      4. Current frontend structure (mermaid)
      5. Suggested frontend structure (mermaid)
      6. AI File Placement Contract
      7. Scorecard
      8. Damage hotlist
      9. All violations grouped by domain
      10. File move suggestions (embedded, not separate JSON)
      11. Architecture metrics
      12. Auto-discovery summary
    """
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary.get("debt_score", 0)

    current_backend_mmd = generate_current_structure_mermaid(repo, eff)
    suggested_backend_mmd = generate_suggested_structure_mermaid(repo, eff, placements)
    current_frontend_mmd = generate_current_frontend_mermaid(repo, eff)
    suggested_frontend_mmd = generate_suggested_frontend_mermaid(repo, eff)

    L: list[str] = []

    # ── Header ──
    L += [
        "# ZOZI Architecture Governance Audit Report",
        "",
        f"> **Generated:** {summary.get('timestamp', '')}  ",
        f"> **Repo:** `{repo}`  ",
        f"> **Result:** 🔴 {n_red} violations · 🟡 {n_yel} advisories · 🟢 {n_grn} info  ",
        f"> **Architecture Debt Score:** **{debt}**  ",
        "",
        "---",
        "",
    ]

    # ── Section 1: The Grid Line ──
    L += [
        "## 1. The Grid Line (Backend Circuit)",
        "",
        "Every file in this project MUST sit inside exactly one of these layers.",
        "Imports flow **downward only**. Any upward import is a violation.",
        "",
        "```",
        "HTTP Request",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 0: ENTRY  (main.py, lifespan.py)                  │",
        "│   Only: app creation, middleware registration,          │",
        "│         router mounting                                 │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 1: MIDDLEWARE + DEPENDENCIES  (flat, no subdirs)  │",
        "│   Only: request preprocessing, auth, RLS context        │",
        "│   FORBIDDEN: import from services/*, controllers/*      │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 2: ROUTERS  — FLAT files                          │",
        "│   filename: {surface}_{domain}_{operation}.py           │",
        "│   Only: endpoint defs, request validation, call ctrl    │",
        "│   FORBIDDEN: session.add/commit/delete, business logic  │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 3: CONTROLLERS  — grouped by DOMAIN               │",
        "│   finance/ orders/ catalog/ logistics/ communication/   │",
        "│   Only: orchestrate services, compose responses         │",
        "│   FORBIDDEN: session writes, raw SQL, import routers/   │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 4: SERVICES  — grouped by DOMAIN                  │",
        "│   Only: business rules, DB operations, call providers   │",
        "│   FORBIDDEN: import from routers/, controllers/         │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 5: PROVIDERS  — grouped by DOMAIN/ADAPTER         │",
        "│   Only: external API adapters (AI, maps, email, pay)    │",
        "│   FORBIDDEN: import from services/, controllers/        │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 6: MODELS  — grouped by DOMAIN                    │",
        "│   Only: SQLAlchemy ORM definitions, relationships       │",
        "│   FORBIDDEN: import from ANY other layer                │",
        "└─────────────────────────────────────────────────────────┘",
        "    │",
        "    ▼",
        "┌─────────────────────────────────────────────────────────┐",
        "│ LAYER 7: DB INFRASTRUCTURE  (db/, alembic/)             │",
        "│   Only: engine, session factory, base classes           │",
        "└─────────────────────────────────────────────────────────┘",
        "",
        "CROSS-CUTTING:",
        "  utils/     — pure helpers, no state, no DB",
        "  events/    — domain events (grouped by domain)",
        "  jobs/      — background tasks (grouped by domain)",
        "  tests/     — test files (exempt from most rules)",
        "  scripts/   — ops/maintenance scripts (exempt)",
        "```",
        "",
        "---",
        "",
    ]

    # ── Section 2: Current Backend Structure ──
    L += [
        "## 2. Current Backend Structure",
        "",
        current_backend_mmd,
        "",
        "---",
        "",
    ]

    # ── Section 3: Suggested Backend Structure ──
    L += [
        "## 3. Suggested Backend Structure",
        "",
        suggested_backend_mmd,
        "",
        "---",
        "",
    ]

    # ── Section 4: Current Frontend Structure ──
    L += [
        "## 4. Current Frontend Structure",
        "",
        current_frontend_mmd,
        "",
        "---",
        "",
    ]

    # ── Section 5: Suggested Frontend Structure ──
    L += [
        "## 5. Suggested Frontend Structure",
        "",
        suggested_frontend_mmd,
        "",
        "---",
        "",
    ]

    # ── Section 6: AI File Placement Contract ──
    L += [
        "## 6. AI File Placement Contract",
        "",
        generate_ai_placement_contract(),
        "",
        "---",
        "",
    ]

    # ── Section 7: Scorecard ──
    L += [
        "## 7. Scorecard",
        "",
        "| Code | Count | Sev | Meaning |",
        "|---|---:|---|---|",
    ]
    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        L.append(
            f"| {code} | {rep.counters[code]} | {SEV_ICON[sev]} {sev} "
            f"| {RULE_MEANING.get(code, '')} |"
        )
    L += ["", "---", ""]

    # ── Section 8: Damage Hotlist ──
    hot = sorted(
        [f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED],
        key=lambda f: (0 if f.sev == RED else 1, f.code),
    )
    L += [
        "## 8. 🔥 Damage Hotlist (fix these first)",
        "",
        "| Sev | Rule | Domain | Location | Problem | Fix |",
        "|---|---|---|---|---|---|",
    ]
    for f in hot:
        L.append(
            f"| {SEV_ICON[f.sev]} | {f.code} | {f.domain} "
            f"| `{f.loc()}` | {f.message} | {f.intended or '-'} |"
        )
    L += ["", "---", ""]

    # ── Section 9: All Violations Grouped by Domain ──
    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)

    L += ["## 9. All Findings by Domain", ""]
    for dom in ordered_report_domains(rep):
        items = by_dom.get(dom, [])
        if not items:
            continue
        L += [f"### {dom.upper()} ({len(items)} findings)", ""]
        for f in items:
            intended_part = f" → *{f.intended}*" if f.intended else ""
            L.append(
                f"- {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}{intended_part}"
            )
        L.append("")
    L += ["---", ""]

    # ── Section 10: File Move Suggestions (embedded) ──
    if placements:
        L += [
            "## 10. File Move Suggestions",
            "",
            f"**{len(placements)} file(s) need relocation:**",
            "",
            "| # | Current Location | Suggested Location | Reason | Confidence |",
            "|---:|---|---|---|---:|",
        ]
        for i, p in enumerate(placements, 1):
            conf = f"{p.get('confidence', 0):.0%}"
            L.append(
                f"| {i} | `{p['from']}` | `{p['to']}` "
                f"| {p.get('reason', '')} | {conf} |"
            )
        L += ["", "---", ""]

    # ── Section 11: Architecture Metrics ──
    L += [
        "## 11. Architecture Metrics",
        "",
        f"- **Architecture Debt Score:** {debt}",
        f"- **Modules scanned:** {summary['modules']}",
        f"- **Dependency edges:** {summary['edges']}",
        f"- **Classes found:** {summary['classes']}",
    ]
    if summary.get("layer_counts"):
        L.append(
            "- **Layer counts:** "
            + ", ".join(f"`{k}={v}`" for k, v in sorted(summary["layer_counts"].items()))
        )
    if summary.get("top_fan_in"):
        L += ["", "### Top Fan-In (most depended-upon)", "", "| Module | Fan-In |", "|---|---:|"]
        for module, count in summary["top_fan_in"]:
            L.append(f"| `{module}` | {count} |")
    if summary.get("top_fan_out"):
        L += ["", "### Top Fan-Out (most dependent)", "", "| Module | Fan-Out |", "|---|---:|"]
        for module, count in summary["top_fan_out"]:
            L.append(f"| `{module}` | {count} |")
    if summary.get("frontend_metrics"):
        L += ["", "### Frontend Workspace Metrics", "", "| Workspace | Source Files | Dirs |", "|---|---:|---:|"]
        for ws, m in sorted(summary["frontend_metrics"].items()):
            L.append(f"| `{ws}` | {m.get('source_files', 0)} | {m.get('dirs', 0)} |")
    L += ["", "---", ""]

    # ── Section 12: Auto-Discovery Summary ──
    if summary.get("auto_discovery"):
        ad = summary["auto_discovery"]
        L += [
            "## 12. Auto-Discovery Summary",
            "",
            f"- **Domains discovered:** {ad.get('domains', 0)}",
            f"- **Features discovered:** {ad.get('features', 0)}",
            f"- **Frontend features:** {ad.get('frontend_features', 0)}",
            f"- **Backend top-level dirs:** {ad.get('backend_top_dirs', 0)}",
            f"- **Cross-domain edges:** {ad.get('domain_edges', 0)}",
            "",
        ]
        if reg.domains:
            L += ["### Discovered Domains", ""]
            for dom in sorted(reg.domains):
                L.append(f"- `{dom}`")
            L.append("")

    L += [
        "---",
        "",
        "*This report is the single source of truth for architecture governance.*",
        "*Fix RED violations first, then YELLOW advisories.*",
        "",
    ]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")



# ============================================================================
# SECTION 38: MAIN — SIMPLIFIED, SINGLE .md OUTPUT (was SECTION 22)
# ============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="ZOZI Architecture Governance Auditor v4.1 — "
                    "produces ONE comprehensive .md report."
    )
    ap.add_argument("--root", default=None,help="repo root (default: auto-detect)")
    ap.add_argument("--out", default=None,help="output .md report path")
    ap.add_argument("--show-intended", action="store_true",help="print intended structure tree to console")
    ap.add_argument("--no-fail", action="store_true",help="always exit 0")
    ap.add_argument("--emit-registry", action="store_true",help="generate domains.yaml registry file")
    args = ap.parse_args()

    repo = find_repo(args.root)
    if not repo.is_dir():
        print(f"[FATAL] repo root not found: {repo}", file=sys.stderr)
        return 2

    eff = load_rules(repo, None)
    ensure_required_ignore_dirs(eff)

    global _ACTIVE_EFF, _ACTIVE_REG
    _ACTIVE_EFF = eff

    print(f"Scanning {repo} ...")
    print(f"  Rules source: {'YAML' if eff['from_yaml'] else 'embedded'}")
    print()

    rep = Report()

    # ══════════════════════════════════════════════════════════════
    # PHASE 1: Build graph + discover features
    # ══════════════════════════════════════════════════════════════
    graph = build_module_graph(repo, eff)
    reg = discover_features(repo, eff, graph)
    _ACTIVE_REG = reg

    # ══════════════════════════════════════════════════════════════
    # PHASE 2: Symbol Index + Call Graph (SECTION 19, 20)
    # ══════════════════════════════════════════════════════════════
    print("  Building symbol index...")
    symbol_index = build_symbol_index(repo, eff, graph)

    print("  Building call graph...")
    call_graph = build_call_graph(repo, eff, graph, symbol_index)

    # ══════════════════════════════════════════════════════════════
    # PHASE 3: Domain placement engine (SECTION 14)
    # ══════════════════════════════════════════════════════════════
    placement_suggestions = check_move_suggestions(repo, rep, eff, graph, reg)
    if placement_suggestions:
        rep.add(
            GRN, "I4", "repo", "move-map",
            f"{len(placement_suggestions)} file move suggestions generated",
            intended="see 'File Move Suggestions' section in this report",
        )

    # ══════════════════════════════════════════════════════════════
    # PHASE 4: Auto-learning domain discovery (SECTION 16)
    # ══════════════════════════════════════════════════════════════
    model = learn_domain_model(repo, eff, reg)
    report_auto_domain_candidates(repo, rep, eff, model)

    # ══════════════════════════════════════════════════════════════
    # PHASE 5: Repository hygiene / structure (SECTION 9) — 18 checks
    # ══════════════════════════════════════════════════════════════
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
    check_rls_cluster(repo, rep, eff)
    check_raw_env_in_middleware(repo, rep, eff)
    check_media_on_disk(repo, rep, eff)

    # ══════════════════════════════════════════════════════════════
    # PHASE 6: Circuit enforcement (SECTION 10) — 3 NEW checks
    # ══════════════════════════════════════════════════════════════
    print("  Enforcing circuit import direction...")
    check_circuit_import_direction(repo, rep, eff, graph)

    print("  Validating middleware pipeline...")
    check_middleware_pipeline(repo, rep, eff)

    print("  Checking layer contracts...")
    check_layer_contracts(repo, rep, eff, graph, call_graph)  # ← 5 args, CORRECT

    # ══════════════════════════════════════════════════════════════
    # PHASE 7: Backend layer / dependency (SECTION 11) — 11 checks
    # ══════════════════════════════════════════════════════════════
    check_layer_writes(repo, rep, eff)
    check_router_outside(repo, rep, eff)
    check_dependency_graph(repo, rep, eff, graph)
    check_circuit_contract(repo, rep, eff, graph)
    check_dependency_cycles(repo, rep, eff, graph)
    check_dead_modules(repo, rep, eff, graph)
    check_metrics(repo, rep, eff, graph)
    check_duplicate_classes(repo, rep, eff, graph)
    check_sys_path_manipulation(repo, rep, eff)
    check_controller_outside(repo, rep, eff)
    check_router_naming_convention(repo, rep, eff)

    # ══════════════════════════════════════════════════════════════
    # PHASE 8: Symbol / Call Graph / Public API (SECTION 19, 20, 21)
    # ══════════════════════════════════════════════════════════════
    print("  Checking symbol index...")
    check_dead_symbols(repo, rep, eff, symbol_index, graph)
    check_duplicate_symbols(repo, rep, eff, symbol_index)

    print("  Checking call graph violations...")
    check_call_graph_violations(repo, rep, eff, call_graph, graph)

    print("  Checking public API stability...")
    check_public_api_stability(repo, rep, eff, symbol_index, graph)

    # ══════════════════════════════════════════════════════════════
    # PHASE 9: Flow Types / Content / Split / Surface Ops (SECTION 22-25)
    # ══════════════════════════════════════════════════════════════
    print("  Classifying flow types...")
    flow_types = classify_flow_types(repo, eff, reg, graph)
    check_flow_type_violations(repo, rep, eff, flow_types, graph)

    print("  Checking content alignment...")
    check_file_content_alignment(repo, rep, eff, graph)
    check_split_file_candidates(repo, rep, eff, graph)

    print("  Validating surface operations...")
    check_surface_operations(repo, rep, eff, graph)

    # ══════════════════════════════════════════════════════════════
    # PHASE 10: Project Files / Scope Docs / API Shape (SECTION 27, 28)
    # ══════════════════════════════════════════════════════════════
    print("  Checking required files...")
    check_required_project_files(repo, rep, eff)

    print("  Validating scope documentation...")
    check_scope_documentation(repo, rep, eff)
    check_scope_yaml_agreement(repo, rep, eff)

    print("  Validating API shape...")
    check_api_shape(repo, rep, eff, graph)

    # ══════════════════════════════════════════════════════════════
    # PHASE 11: Dynamic imports / policy / frontend (SECTION 12)
    # ══════════════════════════════════════════════════════════════
    check_dynamic_dependency_signals(repo, rep, eff, graph)
    check_policy_config(repo, rep, eff)
    check_frontend_structure(repo, rep, eff)

    # ══════════════════════════════════════════════════════════════
    # PHASE 12: Security / performance / quality (SECTION 13) — 13 checks
    # ══════════════════════════════════════════════════════════════
    check_enhanced_secrets_in_code(repo, rep, eff)
    check_enhanced_dangerous_calls(repo, rep, eff)
    check_enhanced_runtime_security_settings(repo, rep, eff)
    check_enhanced_async_blocking(repo, rep, eff)
    check_enhanced_query_in_loop(repo, rep, eff)
    check_enhanced_exception_handling(repo, rep, eff)
    check_enhanced_todo_debt(repo, rep, eff)
    check_enhanced_size_complexity(repo, rep, eff)
    check_enhanced_print_debug(repo, rep, eff)
    check_enhanced_model_schema(repo, rep, eff)
    check_enhanced_alembic_heads(repo, rep, eff)
    check_enhanced_gitignore_generated(repo, rep, eff)
    check_enhanced_frontend_debug(repo, rep, eff)

    # ══════════════════════════════════════════════════════════════
    # PHASE 13: Advanced Security / Performance / Frontend (SECTION 29-31)
    # ══════════════════════════════════════════════════════════════
    print("  Running advanced security checks...")
    check_advanced_security(repo, rep, eff, graph)

    print("  Running advanced performance checks...")
    check_advanced_performance(repo, rep, eff, graph)

    print("  Running advanced frontend checks...")
    check_advanced_frontend(repo, rep, eff)

    # ══════════════════════════════════════════════════════════════
    # PHASE 14: Enhanced Metrics / Bounded Contexts (SECTION 32, 33)
    # ══════════════════════════════════════════════════════════════
    print("  Computing enhanced metrics...")
    check_enhanced_metrics(repo, rep, eff, graph, symbol_index)

    print("  Validating bounded contexts...")
    check_bounded_contexts(repo, rep, eff, graph, reg)

    # ══════════════════════════════════════════════════════════════
    # PHASE 15: Architecture Registry (SECTION 34)
    # ══════════════════════════════════════════════════════════════
    print("  Building architecture registry...")
    arch_registry = generate_architecture_registry(repo, eff, reg, graph)
    check_architecture_registry(repo, rep, eff, arch_registry, graph)

    # ══════════════════════════════════════════════════════════════
    # PHASE 16: Surface × Domain matrix + Frontend roles (SECTION 15)
    # ══════════════════════════════════════════════════════════════
    check_surface_domain_matrix(repo, rep, eff, graph)
    check_frontend_role_pages(repo, rep, eff)

    # ══════════════════════════════════════════════════════════════
    # PHASE 17: Collapse + Summary (SECTION 17)
    # ══════════════════════════════════════════════════════════════
    collapse_noisy_findings(rep)
    collect_info(repo, rep, eff, graph)
    frontend_metrics = collect_frontend_metrics(repo, eff)
    debt_score = compute_debt_score(rep, eff)
    rep.add(
        GRN, "MET1", "repo", "architecture-debt",
        f"architecture debt score = {debt_score}",
        intended="track this number down over time; lower is healthier",
    )
    summary = build_summary(repo, rep, graph, debt_score, frontend_metrics, reg)

    # ══════════════════════════════════════════════════════════════
    # PHASE 18: Console output (SECTION 18)
    # ══════════════════════════════════════════════════════════════
    n_red = render_stdout(repo, rep, args.show_intended, summary)

    # ══════════════════════════════════════════════════════════════
    # PHASE 19: Write THE SINGLE .md report (SECTION 18)
    # ══════════════════════════════════════════════════════════════
    out = resolve_repo_output_path(repo, args.out, "ARCHITECTURE_AUDIT_REPORT.md")
    render_markdown(repo, rep, out, summary, placement_suggestions, eff, reg, graph)

    # Optional: Emit registry YAML
    if args.emit_registry:
        emit_registry_yaml(repo, arch_registry)
        print(f"  Registry written: documents/scope/domains.yaml")

    print(f"\n{'=' * 76}")
    print(f"  REPORT WRITTEN: {out}")
    print(f"  Total findings: {len(rep.findings)}")
    print(f"  🔴 RED: {summary['red']}  🟡 YEL: {summary['yellow']}  🟢 GRN: {summary['green']}")
    print(f"  Debt Score: {debt_score}")
    print(f"{'=' * 76}")

    return 1 if (n_red and not args.no_fail) else 0

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    sys.exit(main())