# System Architecture Audit Script --- `scripts/system_trackers/system_architecture_audit.py`
"""
system_architecture_audit.py — READ-ONLY, repo-wide architecture governance auditor.

Architecture Audit Script — aligned with ARCHITECTURE_DIAGRAM.md

Purpose:
    ZOZI architecture governance engine. Single complete script.
    AUTHORITATIVE TARGET SPEC: documents/ARCHITECTURE_DIAGRAM.md (three orthogonal axes
    + seven laws). This auditor ENFORCES that target so a migration can be
    VERIFIED, not trusted. It detects abolished layers that still exist,
    missing ARCHITECTURE_DIAGRAM axis packages, inverted dependency arrows, and
    "claimed-but-not-done" migrations (compliance check: stops false migration claims from
    100% placement while old layers persist).

    Enforces the ARCHITECTURE_DIAGRAM.md backend circuit (arrows point DOWN only):

        modules/{actor}/routers  ->  domains/{domain}/services  ->  infrastructure
        rbac/*  (feature axis; imported by modules + middleware ONLY)
        providers/*  (imported by services/jobs ONLY)
        jobs/*  ->  domains/*  ->  infrastructure
        kernel/*  ->  domains/*  ->  infrastructure

    Validates:
    system_architecture_audit.py
    │
    ├── SECTION 1:  Constants (ENHANCED - unified domains, fixed IGNORE_DIRS)
    ├── SECTION 2:  Domain Taxonomy (ENHANCED - unified)
    ├── SECTION 3:  Circuit Contract (KEEP)
    ├── SECTION 4:  Data Models (ENHANCED - add DB/Design/Health models)
    ├── SECTION 5:  Generic Helpers (ENHANCED - add color math, AST helpers)
    ├── SECTION 6:  Rule Loading (KEEP)
    ├── SECTION 7:  Module Graph Builder (KEEP)
    ├── SECTION 8:  Feature Discovery (KEEP)
    ├── SECTION 9:  Structure/Hygiene (KEEP)
    ├── SECTION 10: Circuit Enforcement (KEEP)
    ├── SECTION 11: Layer/Dependency (KEEP)
    ├── SECTION 12: Dynamic/Policy/Frontend (KEEP)
    ├── SECTION 13: Security/Performance/Quality (KEEP)
    ├── SECTION 14: Domain Placement Engine (KEEP)
    ├── SECTION 15: Scaffolding/Matrix/Frontend Roles (KEEP)
    ├── SECTION 16: Auto-Learning (KEEP)
    ├── SECTION 17: Summary/Trend/Collapse (ENHANCED)
    ├── SECTION 18: Rendering (ENHANCED)
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
    ├── SECTION 37: Render Markdown (ENHANCED)
    │
    ├── ═══ NEW: DATABASE AUDIT ENGINE ═══
    ├── SECTION 40: Database Constants & Models
    ├── SECTION 41: Database Model Parser
    ├── SECTION 42: Database Migration Parser
    ├── SECTION 43: Database RLS Parser
    ├── SECTION 44: Database Static Checks (DB01-DB37)
    ├── SECTION 45: Database Production Checklist
    ├── SECTION 46: Database Live Checks
    ├── SECTION 47: Database Scoring
    │
    ├── ═══ NEW: DESIGN AUDIT ENGINE ═══
    ├── SECTION 50: Design Constants & Models
    ├── SECTION 51: Color Math Engine
    ├── SECTION 52: Palette Discovery
    ├── SECTION 53: Design File Scanners
    ├── SECTION 54: Design Aggregate Checks (DS01-DS18)
    ├── SECTION 55: Design Scoring
    │
    ├── ═══ NEW: HEALTH AUDIT ENGINE ═══
    ├── SECTION 60: Health Constants & Models
    ├── SECTION 61: Python File Analyzer
    ├── SECTION 62: Python Health Checks
    ├── SECTION 63: Frontend Health Checks
    ├── SECTION 64: Deployment/Pipeline/Runtime
    ├── SECTION 65: Health Scoring & Ranking
    │
    ├── SECTION 70: Unified Orchestrator (main)
    └── SECTION 71: Unified Rendering

Design principles:
    * READ-ONLY with respect to source code.
    * Does NOT import application code.
    * Uses stdlib `ast` for Python static analysis.
    * YAML is optional and preferred when present.
    * Embedded rules are fallback.
    * RED is reserved for high-confidence architectural violations.
    * Single implementation of each function (no fix-pack appending).

Sub-folder axis (per documents/ARCHITECTURE_DIAGRAM.md - the AUTHORITATIVE target):
- AXIS 1 MODULE = modules/{actor}/  where actor in {customer, supplier, logistics, admin, employee}
    modules/{actor}/auth/        # login/OTP/session for that actor
    modules/{actor}/routers/     # THIN per-actor routers (auth + require_feature + one service call)
  Routers are NO LONGER flat at backend root, and controllers/ is ABOLISHED.

- AXIS 2 DOMAIN = domains/{domain}/  where domain in {finance, accounts, catalog, orders,
  payments, logistics, suppliers, customers, hr, comms, media, country, governance}
    domains/{d}/services/  models/  schemas/  policies/  events.py  subscribers.py  features.py
  Models are ORM-only and live UNDER domains/{d}/models/ (flat per domain), NOT at backend root.

- AXIS 3 FEATURE = rbac/ + domains/*/features.py
    rbac/catalog.py aggregates domains/*/features.py (single source of truth)
    require_feature("domain.action") gates live in rbac/dependencies.py

- PLATFORM = infrastructure/ (database, redis, storage, messaging, security, observability, utils)
  plus providers/ (3rd-party/AI adapters), jobs/ (background workers), middleware/, alembic/,
  scripts/, tests/, and kernel/ (money/numbering/country/period business primitives).

- backend/ root is a CLOSED set (documents/ARCHITECTURE_DIAGRAM.md §1): main.py, config.py,
  DOMAIN_ALLOWLIST.yaml, modules/, domains/, rbac/, infrastructure/, providers/, jobs/,
  middleware/, alembic/, scripts/, tests/. Any other top-level package at backend root is a
  stray that the audit must flag; there is no prescribed re-export/_legacy shim layer.

SEVEN LAWS (enforced by check_architecture_diagram_compliance — compliance gate):
  1. Arrows point down: modules -> domains -> infrastructure. Domains NEVER import modules.
     rbac imported by modules + middleware only. infrastructure imports nothing above it.
  2. Module routers stay thin (auth + require_feature + one service call; no DB writes/rules).
  3. Cross-domain writes only via events; cross-domain reads only via ports.py / events.py.
  4. Features single-sourced in domains/*/features.py; CI fails on literal not in catalog.
  5. Country is the orthogonal scope axis (RLS + country_staff_assignments).
  6. Schema discipline: every table in a domain Postgres schema; Alembic is sole schema source.

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
import math
import re
import sys
import os
import time
import urllib.request
import urllib.error
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# Reconfigure stdout/stderr to UTF-8 so emoji severity icons render correctly
# on Windows (default cp1252) and when stdout is redirected to a pipe.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
del _stream


# ============================================================================
# SECTION 1: SEVERITY + RULE DICTIONARY + DEFAULT CONSTANTS
# ============================================================================

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"

SEV_ICON = {RED: "🔴", YEL: "🟡", GRN: "🟢"}
SEV_TAG  = {RED: "[RED]", YEL: "[YEL]", GRN: "[GRN]"}

# ---------------------------------------------------------------------------
# RULE_MEANING — SINGLE consolidated dict (all architecture rules)
# ---------------------------------------------------------------------------
RULE_MEANING: dict[str, str] = {
    # ── Layer violations (ARCHITECTURE_DIAGRAM.md: Modules=who, Domains=what, Features=may) ──
    "W1":  "module router writes to DB (must be a domain service)",
    "W2":  "business logic inside a module router -> relocate to domains/*/services/",
    "W3":  "imports a mis-housed controller (logic belongs in domains/*/services, infrastructure/utils, or kernel/)",  # FIXED
    "W4":  "controller imports another controller (controllers abolished; shared logic -> domain service/util)",
    "Q1":  "module router reads via db.query (delegate to domain service)",
    "M1":  "ORM model outside its domain models/ package (must be domains/*/models/)",
    "R1":  "APIRouter instantiated outside modules/*/routers/",
    "G1":  "second migrations home / dual schema-creator (Alembic is the only schema source)",
    "X1":  "ghost/duplicate backend skeleton",
    # ── Duplicates ──
    "D1":  "duplicate module basename within backend (import-shadow)",
    "D2":  "duplicate module basename across top dirs",
    "D3":  "duplicate class name across modules",
    # ── Structure ──
    "S1":  "service not under a domain (must be domains/*/services/)",
    "S2":  "overlapping service stems (ownership ambiguity)",
    "S3":  "abolished flat controllers/ still present (split into modules/*/routers + domains/*/services)",
    "S4":  "surface sub-folder in domains/*/services/ (must be domain)",
    "S5":  "domain service package too large (slice bounded context)",
    "M2":  "ORM model not under a domain models/ (must be domains/*/models/)",
    "M3":  "surface sub-folder in domains/*/models/ (must be domain)",
    "M4":  "domain models package too large",
    "L1":  "multiple RLS enforcers (fail-open risk) — consolidate to ONE canonical enforcer at infrastructure/database/security.py",  # FIXED
    # ── Hotspots / dead code ──
    "A1":  "architecture hotspot (high coupling / instability)",
    "A2":  "possibly dead/orphan module (no inbound imports; not an entrypoint)",
    # ── Package shape ──
    "P1":  "scratch script at backend root (delete / scripts/)",
    "P2":  "controller-named file present (controllers/ abolished -> split into modules/*/routers + domains/*/services)",
    "P3":  "abolished flat root layer package present (controllers/ routers/ services/ models/ db/ utils/ core/ dependencies/)",
    "P4":  "missing expected backend package",
    "P5":  "python package missing __init__.py",
    "H1":  "sys.path.insert/append (import-resolution footgun)",
    # ── Hygiene ──
    "F1":  "scratch/debug script (delete; ops scripts -> scripts/maintenance|validation)",
    "F2":  "hardcoded developer-local absolute path in source",
    "F3":  "dual/triple lockfiles (drift)",
    "F4":  "committed cache/build/artifact present (bloat)",
    "F5":  "secret material on disk (security)",
    "F6":  "media written to / served from local disk (scale killer)",
    "F7":  "raw os.environ secret read in middleware (use config.py settings)",  # FIXED
    "F8":  "non-document artifact at documents/ root",
    "F9":  "repo-root note outside allow-list / banned dir",
    "G0":  "missing/weak root .gitignore",
    # ── Dependency graph ──
    "DG":  "forbidden dependency-graph edge (layer contract violated)",
    "DG2": "circular dependency detected",
    "DG3": "cross-domain import violates explicit bounded-context ownership",
    "DG4": "dynamic import edge detected",
    "DG5": "dynamic execution obscures dependency graph",
    # ── Config ──
    "CFG1": "unknown layer referenced in policy",
    "CFG2": "unknown domain referenced in policy",
    "CFG3": "malformed or contradictory policy rule",
    "CFG4": "policy-level domain cycle",
    "CFG5": "generated governance artifacts not gitignored (incl. SYSTEM_AUDIT_REPORT.md)",  # FIXED
    # ── Metrics ──
    "MET1": "architecture debt score",
    # ── Frontend ──
    "FE1": "missing expected frontend workspace/package file",
    "FE2": "frontend scratch/artifact script at package root",
    "FE3": "frontend flat folder scaling warning",
    "FE4": "frontend cross-workspace relative import",
    "FE5": "frontend folder too large (split by feature/domain)",
    "FE6": "frontend console/debugger statement left in source",
    # ── Domain placement ──
    "DOM1": "file should be moved into its detected domain folder",
    "DOM2": "file is inside the wrong domain folder",
    "DOM3": "surface/flat folder used where a domain-scoped home is required (incl. abolished root layers controllers/ services/ models/ events/)",
    "DOM6": "new domain candidate auto-detected",
    "DOM7": "unknown or non-canonical domain folder (canonical set = the 13 domains of ARCHITECTURE_DIAGRAM.md §3)",  # FIXED
    "DOM8": "correctly placed domain files",
    # ── Move suggestions ──
    "MV1": "flat layer file should be moved into its detected domain folder",
    "MV2": "mis-housed / backend-root file should be relocated to canonical layer",
    "MV3": "router file should be moved to the configured router contract",
    # ── Security / quality ──
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
    # ── Circuit contract ──
    "CIR1":  "circuit violation: import is outside the allowed layer circuit",
    "CIR2":  "circuit bypass: import skips the preferred layer (migration warning)",
    # ── Router naming ──
    "RN1": "module router name does not match the ARCHITECTURE_DIAGRAM.md pattern: modules/{module}/routers/{domain}[_{operation}]_router.py",  # FIXED
    "RN2": "router file is nested deeper than the configured router contract allows",
    "RN3": "router sub-folder does not match the configured surface contract",
    "RN4": "router still lives under abolished root backend/routers/ (pre-ARCHITECTURE_DIAGRAM flat layer)",
    "SCF1": "folder is explicitly forbidden by the scaffolding contract",
    # ── Auto-discovery ──
    "AUTO0":  "auto-discovery baseline created",
    "AUTO3":  "new backend domain detected",
    "AUTO6":  "new cross-domain dependency learned",
    "AUTO8":  "new top-level backend package detected",
    "AUTO10": "new feature detected",
    # ── Info ──
    "NM": "node_modules present (confirm gitignored)",
    "I1": "structure summary",
    "I2": "rules source (yaml vs embedded fallback)",
    "I3": "architecture metric summary",
    "I4": "file move suggestions generated",
    "T1": "architecture trend delta",
    # ── Symbol / Call Graph ──
    "SYM1":  "symbol defined but never used (dead symbol)",
    "SYM2":  "duplicate symbol definition across modules",
    "CG1":   "call graph violation: function calls across forbidden layer boundary",
    "CG2":   "call chain violates circuit direction (upward call)",
    "CG3":   "circular call chain detected",
    # ── Public API ──
    "API1":  "public API symbol changed without deprecation",
    "API2":  "internal symbol exposed outside its module boundary",
    # ── Layer Contracts ──
    "LC1":   "layer contract violation: forbidden operation in layer",
    "LC2":   "layer contract violation: forbidden call pattern",
    "LC3":   "layer contract violation: missing required pattern",
    # ── Flow Types ──
    "FT1":   "flow-type violation: operation not allowed for this surface×domain flow",
    "FT2":   "flow-type mismatch: file contains operations from wrong flow direction",
    # ── Content Alignment ──
    "CA1":   "file name does not match file content (operations mismatch)",
    "CA2":   "file contains operations from multiple domains (split candidate)",
    "CA3":   "surface-inappropriate operation detected",
    # ── Middleware ──
    "MW1":   "middleware pipeline order violation (expected: Foundation → Security → Rate Limit → Geo → Observability → Compliance)",  # FIXED
    "MW2":   "required middleware missing (diagram §3 list: api_version · country_context · csrf · database_security · device_binding · impossible_travel · ip_extraction · logging · pci_dss_compliance · rate_limit · request_id · rls_dependency · security_headers · webhook_ip_whitelist · webhook_verification · zero_trust_auth)",  # FIXED
    "MW3":   "middleware imports an application layer (modules/domains/providers) — circuit violation; middleware may import infrastructure + kernel + rbac only",  # FIXED
    # ── Project Files ──
    "PF1":   "required project file missing",
    "PF2":   "required scope document missing",
    # ── API Shape ──
    "AS1":   "route prefix does not align with surface",
    "AS2":   "OpenAPI tag does not align with domain",
    "AS3":   "endpoint naming convention violation",
    # ── Advanced Security ──
    "SEC5":  "potential SQL injection risk",
    "SEC6":  "potential SSRF risk",
    "SEC7":  "potential path traversal risk",
    "SEC8":  "insecure JWT/token handling",
    "SEC9":  "missing CSRF protection on state-changing endpoint",
    "SEC10": "insecure CORS configuration",
    # ═══ ARCHITECTURE_DIAGRAM §1 security / scaling ═══
    "SEC11": "multiple independent RLS enforcers — fail-open risk; exactly ONE canonical enforcer at infrastructure/database/security.py",  # FIXED
    "SC1":   "DB pool_size exceeds PgBouncer-safe limit (pool_size=5, max_overflow=10 behind PgBouncer)",  # FIXED
    "SC2":   "hot path uses sync-only SQLAlchemy — blocks the event loop at scale (stack target: SQLAlchemy 2.0 async + asyncpg)",  # FIXED
    "SC3":   "in-process WebSocket fan-out won't scale past one replica (move to Redis pub/sub — infrastructure/messaging/)",
    "SC5":   "oversized schemas module (split domain models into sub-packages)",  # FIXED
    # ── Advanced Performance ──
    "PERF3": "missing pagination on list endpoint",
    "PERF4": "unbounded query detected (no limit clause)",
    "PERF5": "large transaction risk (multiple writes without savepoint)",
    "PERF6": "missing database index on frequently queried column",
    # ── Advanced Frontend ──
    "FE7":   "frontend component in wrong feature folder",
    "FE8":   "shared package boundary violation",
    "FE9":   "state management boundary violation",
    "FE10":  "raw fetch()/XMLHttpRequest bypasses typed API client",
    "FE11":  "frontend/shared/src/adminPermissions.ts must be deleted (replaced by generated permissions.ts from /rbac/catalog)",
    "FE12":  "frontend/web_app/src/lib/rbac.ts missing — must fetch /rbac/catalog so UI gating and backend gating share one source",
    "FE13":  "frontend/shared/src/permissions.ts missing — must be generated from backend /rbac/catalog",
    "FE14":  "employee/* route group missing in web_app (module actor 'employee' has no UI shell — diagram §3 route tree)",  # NEW
    # ── Architecture Metrics ──
    "MET2":  "module instability exceeds threshold",
    "MET3":  "abstractness below threshold (no interfaces)",
    "MET4":  "distance from main sequence too high",
    "MET5":  "god module detected (excessive responsibility)",
    # ── Bounded Context ──
    "BC1":   "cross-domain import bypasses ports.py/events.py boundary (Law 3)",  # FIXED
    "BC2":   "domain event not properly defined (must be typed @dataclass/model with id + serialization)",
    "BC3":   "bounded context leakage detected (direct cross-domain model access)",
    # ── Architecture Registry ──
    "REG1":  "domain missing from architecture registry",
    "REG2":  "registry dependency not reflected in code",
    "REG3":  "public API not documented in registry",
    # ═══════════════════════════════════════════════════════════
    # ARCHITECTURE_DIAGRAM.md COMPLIANCE GATE (NS prefix)
    # ═══════════════════════════════════════════════════════════
    "NS0":  "ARCHITECTURE_DIAGRAM.md compliance gate active (authoritative target)",
    "NS1":  "abolished controllers/ layer still present at backend root",
    "NS2":  "flat routers/ package still present at backend root (must be modules/*/routers)",
    "NS3":  "flat services/ package still present at backend root (must be domains/*/services)",
    "NS4":  "flat models/ package still present at backend root (must be domains/*/models)",
    "NS5":  "required ARCHITECTURE_DIAGRAM.md package missing (modules/domains/rbac/infrastructure required; kernel/middleware/alembic advisory)",  # FIXED
    "NS6":  "domain imports a module layer (Law 1: arrows point down only)",
    "NS7":  "infrastructure imports an application/domain layer (Law 1 violation)",
    "NS8":  "cross-domain import bypasses ports.py/events.py/read_models (Law 3 violation)",  # FIXED
    "NS9":  "_legacy/ strangler shim carries real logic (def/class bodies) — shims are re-export ONLY and deleted when the slice is 100% ready (strangler rule, P1)",  # ADDED (code emits it; was missing here)
    "NS11": "root models/ still canonical while domain models absent (migration not done)",
    "NS12": "consumer import still binds to an abolished flat layer (services/controllers/routers/root models) from a non-_legacy file — runtime still depends on abolished code; migration claim is FALSE (P0)",  # ADDED
    "NS13": "sys.path manipulation injects '_legacy' onto the import path so abolished-layer imports silently resolve to shims — false-green cheat; remove the hack and migrate the imports (P0)",  # ADDED
    "NS14": "ARCHITECTURE_DIAGRAM.md adoption ratio below target (measured over backend imports)",
    "NS15": "feature atom used via require_feature() literal but not registered in domains/*/features.py (Law 4 single-source, P0)",
    "NS16": "rbac/catalog.py does not aggregate domains/*/features.py via package scan — catalog is hand-maintained and drifts from domains (Law 4 single-source, P0)",  # FIXED
    "NS17": "duplicate feature-atom keys across domains/*/features.py (ambiguous capability, P1)",
    "NS18": "thin-router violation: router module carries business logic instead of delegating to ONE domain-service call in domains/*/services (Law 2, P1)",  # FIXED (was "module service/use-case")
    "NS19": "module-actor discipline violation: non-standard actor sub-package under modules/, or direct _legacy import instead of a port (Law 5 module axis, P1)",  # ADDED
    "NS20": "inverted dependency arrow: middleware/providers/infrastructure import upward application layers (Law 1, P0)",
    "NS21": "country scope axis missing: country-scoped data exists but no domains/country scoping layer (Law 5 orthogonal country axis, P2)",  # FIXED (was "axis 3")
    "NS22": "schema discipline violation: domain model table lacks __table_args__ schema='<domain>' (Law 6, P1)",
    "NS23": "abolished db/ layer still present at backend root (must be infrastructure/database/)",
    "NS24": "abolished utils/ layer still present at backend root (must be infrastructure/utils/ + kernel/)",
    "NS25": "non-canonical core/ package at backend root (no home in the target architecture; must be domains/*/services/ or infrastructure/)",
    "NS26": "non-canonical dependencies/ package at backend root (no home in the target architecture; must be domains/*/ or infrastructure/)",
    "NS27": "non-canonical tasks/ package at backend root — background work lives in jobs/ (closed root set, diagram §3, P1)",  # ADDED
    "NS28": "non-canonical events/ package at backend root — events live per-domain as domains/*/events.py (closed root set, diagram §3, P1)",  # ADDED
    "NS29": "non-canonical uploads/ package at backend root — media blobs live in infrastructure/storage/ (object storage), never in the repo tree (closed root set, P1)",  # ADDED
    "NS30": "non-canonical var/ package at backend root — runtime state is not a backend package (closed root set, P2)",  # ADDED
    "NS31": "non-canonical venv/ at backend root — tooling, not app structure; gitignore and delete (closed root set, P2)",  # ADDED
    "NS32": "non-canonical tools/ package at backend root — one-off migration helpers belong in scripts/, not the runtime tree (closed root set, P2)",  # ADDED
    "NS33": "module router gates with a pre-ARCHITECTURE_DIAGRAM per-module auth helper (require_admin/require_finance_permission/...) instead of rbac.dependencies.require_feature — Feature axis (Law 4) not wired (P2)",
    "NS34": "kernel/ imports a layer above it (modules/domains/rbac/providers/jobs/middleware); kernel is a pure shared kernel: domains -> kernel -> infrastructure primitives only (Law 1, P1)",  # FIXED
    "NS35": "module router imports providers/ directly; providers are called only by services/jobs, never by thin module routers (Law 1, P0)",
    "NS36": "domain imports rbac/; rbac is imported by modules/middleware only — domains enforce policies, not permissions (Law 4, P0)",
    "NS37": "DOMAIN_ALLOWLIST.yaml missing, or contains a phantom cross-domain entry that matches no real import (allowlist rule, Law 7, P2)",
    "NS38": "backend root entry outside the closed set defined by ARCHITECTURE_DIAGRAM.md §3 (main.py · config.py · DOMAIN_ALLOWLIST.yaml · modules/ domains/ rbac/ kernel/ infrastructure/ providers/ jobs/ middleware/ alembic/ scripts/ tests/) (P1)",  # NEW
    "NS39": "domain folder missing features.py — every domain seeds its permission atoms (Law 4 single-source, P0)",  # NEW
    "NS40": "module missing required internals — each actor needs auth/ + routers/ + serializers/ (diagram §3 Axis 1, P1)",  # NEW
    "NS41": "module router exceeds the thin contract — more than one domain-service call per endpoint (Law 2, P1)",  # NEW
    "NS42": "tests/architecture/ contract tests missing (test_import_laws.py · test_feature_catalog.py) (diagram §3, P2)",  # NEW
    "NS43": "heavy domain exceeds slice threshold without slicing (> ~8 services OR > ~12 tables → slice into sub-capability folders, e.g. finance: ledger/ payouts/ treasury/) (diagram §3, P2)",  # NEW
    # ═══════════════════════════════════════════════════════════
    # DATABASE AUDIT RULES (DBA prefix to avoid collision with DB1-DB3)
    # ═══════════════════════════════════════════════════════════
    "DBA01": "model declares a forbidden (core/platform/identity) PostgreSQL schema= argument",
    "DBA02": "Base.metadata.create_all not safely dev-gated",
    "DBA03": "mandatory column set / mixin missing",
    "DBA04": "country_code width mismatch",
    "DBA05": "RLS coverage missing or weak (ONE canonical enforcer: infrastructure/database/security.py)",  # FIXED
    "DBA06": "forbidden schema-prefixed FK (core/platform/identity); use a domain schema e.g. customer.user.id",
    "DBA07": "unsafe or missing FK cascade rule",
    "DBA08": "FK column missing index",
    "DBA09": "JSONB column missing GIN index signal",
    "DBA10": "file bytes stored in database",
    "DBA11": "database naming convention violation",
    "DBA12": "migration governance missing or unsafe",
    "DBA13": "migration head / ORM-only table drift",
    "DBA14": "dev/prod database gate missing or weak",
    "DBA15": "connection pool configuration mismatch (target: pool_size=5, max_overflow=10 behind PgBouncer)",  # FIXED
    "DBA16": "SQLite production risk",
    "DBA17": "event outbox tables missing",
    "DBA18": "audit log taxonomy missing or fragmented",
    "DBA19": "analytics snapshot discipline missing / live aggregate risk",
    "DBA20": "finance ledger immutability risk",
    "DBA21": "AI staging discipline missing or direct commit risk",
    "DBA22": "hardcoded business config constant",
    "DBA23": "partition strategy missing for hot append-only tables",
    "DBA24": "production checklist gap",
    "DBA25": "live database drift / live check result",
    "DBA26": "ORM model outside domains/*/models/",
    "DBA27": "broken or suspicious migration file (ADR-018 risk)",
    "DBA28": "migration contract-test harness missing",
    "DBA29": "required canonical table missing",
    "DBA30": "required analytics snapshot table missing",
    "DBA31": "required composite index signal missing",
    "DBA32": "unsafe pagination/query pattern (OFFSET on hot list; use keyset/cursor pagination)",  # FIXED
    "DBA33": "finance write outside ledger service boundary",
    "DBA34": "RLS fail-closed signal missing",
    "DBA35": "idempotency/webhook dedupe table missing",
    "DBA36": "archive/retention signal missing",
    "DBA37": "data dictionary generator missing ERD/Mermaid output",
    "DBA38": "country_staff_assignments table missing (Law 5: country is the orthogonal scope axis — RLS session context + country_staff_assignments)",  # NEW
    # ═══════════════════════════════════════════════════════════
    # DESIGN AUDIT RULES
    # ═══════════════════════════════════════════════════════════
    "DS01": "hardcoded CSS: inline style={{...}} object in component",
    "DS02": "hardcoded CSS: <style> </style> tag inside a component file",
    "DS03": "raw/off-palette color literal (bypasses design tokens)",
    "DS04": "color theme drift: near-duplicate colors used as if different",
    "DS05": "Tailwind arbitrary value bypassing tokens",
    "DS06": "!important usage (specificity war)",
    "DS07": "hardcoded typography (font size / family literal)",
    "DS08": "hardcoded spacing/dimension (raw px)",
    "DS09": "inconsistent border-radius values",
    "DS10": "magic z-index (>=1000)",
    "DS11": "inconsistent box-shadow values",
    "DS12": "design token source missing or weak",
    "DS13": "cross-workspace palette mismatch (web vs mobile differ)",
    "DS14": "mixed styling systems (CSS-in-JS alongside Tailwind)",
    "DS15": "low-contrast foreground/background pair",
    "DS16": "inconsistent motion durations (transition/animation)",
    "DS17": "unused design tokens",
    "DS18": "media-query breakpoint outside the screen scale",
    # ═══════════════════════════════════════════════════════════
    # HEALTH AUDIT RULES
    # ═══════════════════════════════════════════════════════════
    "HL101": "oversized Python file",
    "HL102": "oversized Python function",
    "HL110": "missing docstring on public domain-service / module function",  # FIXED (was "service/controller" — controllers abolished)
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
    "PL101": "pipeline component missing (diagram §1 CI: ci.yml · import-lint.yml · schema-drift.yml · e2e.yml)",  # FIXED
    "RT200": "runtime endpoint healthy",
    "RT201": "runtime endpoint slow",
    "RT404": "runtime health endpoint missing",
    "RT500": "runtime endpoint unhealthy/unreachable",
    # ── Missing Health rule meanings ──
    "HL901": "high count of TODO/FIXME comment markers (debt threshold exceeded)",
    "HL902": "commented-out code lines (dead code)",
    "HL801": "function needs timing/metrics instrumentation",
    "RT000": "runtime probe enabled",
    "RT400": "runtime endpoint non-success",
    "HC1": "health contract endpoint missing (/health, /health/deps, /health/ready)",
    "PRV1": "provider class does not subclass BaseProvider/BaseAIProvider (providers/_base.py)",  # FIXED
    "PRV2": "provider missing health_check() implementation",
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
    "SEC11", "SC1", "SC2", "SC3",
    "PERF3", "PERF4", "PERF5", "PERF6",
    "FE7", "FE8", "FE9", "FE10", "FE11", "FE12", "FE13",
    "MET2", "MET3", "MET4", "MET5",
    "BC1", "BC2", "BC3",
    "REG1", "REG2", "REG3",
    "SCF1",

    # Database hotlist
    "DBA02", "DBA05", "DBA10", "DBA13", "DBA16", "DBA20", "DBA26",
    "DBA27", "DBA33",
    # Design hotlist
    "DS02", "DS03", "DS05", "DS06", "DS10", "DS12", "DS13", "DS15",
    # Health hotlist
    "HL402", "SEC101", "SEC105", "HL601", "HL602", "SC102",
    # Additional health hotlist
    "HL401", "HL902", "PG101", "PG103", "HL601", "MR101",

    # ARCHITECTURE_DIAGRAM.md compliance gate
    "NS0", "NS1", "NS2", "NS3", "NS4", "NS5", "NS6", "NS7", "NS8", "NS11",
    "NS12", "NS14", "NS15", "NS16", "NS17", "NS18", "NS19", "NS20", "NS21", "NS22",
    "NS33", "NS34", "NS35", "NS36", "NS37",
    # NEW gap-closing compliance codes + non-canonical root packages (companion update)
    "NS23", "NS24", "NS25", "NS26", "NS27", "NS28", "NS29", "NS30", "NS31", "NS32",
    "NS38", "NS39", "NS40", "NS41", "NS42", "NS43",
    "FE14", "DBA38",
}

# Codes that the audit emits but were missing from the hotlist, plus the new
# gap-closing NS/FE/DBA codes reserved by the ARCHITECTURE_DIAGRAM.md alignment.
HOTLIST_RULES |= {
    # already emitted by the code but absent from the hotlist:
    "NS23", "NS24", "NS25", "NS26",
    "NS27", "NS28", "NS29", "NS30", "NS31", "NS32",
    # new gap-closing codes:
    "NS38", "NS39", "NS40", "NS41", "NS42", "NS43",
    "FE14", "DBA38",
}

# Companion update: ADDED + NEW codes that were missing from the hotlist.
# (NS9/NS12/NS13/NS19 are emitted by the code; NS23-NS32, NS38-NS43, FE14, DBA38 added.)
HOTLIST_RULES |= {
    "NS23", "NS24", "NS25", "NS26",
    "NS27", "NS28", "NS29", "NS30", "NS31", "NS32",
    "NS38", "NS39", "NS40", "NS41", "NS42", "NS43",
    "FE14", "DBA38",
}

# ---------------------------------------------------------------------------
# DEFAULT CONSTANTS (each defined ONCE)
# ---------------------------------------------------------------------------

DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox",
    "htmlcov", ".next", ".expo", ".kotlin", "gradle", "android", "ios", ".idea", ".vscode", "test-results", ".playwright-artifacts-0",
    "playwright-out", "static-tmp", ".web-build-test", "artifacts", "uploads", ".turbo", "dist", "build", "coverage", "playwright-report", 
    "test-output", "tmp", ".hypothesis", ".kilo", ".kilocode", "worktrees", ".repo", "e2e", "__tests__", "__mocks__", ".storybook", ".web", "web-dist",
    "var", "_migration_trash",
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

# Backend root holds ONLY bootstrap + config per ARCHITECTURE_DIAGRAM.md.
# Abolished dev launchers run_server.py / start_server.py are intentionally excluded
# (the app boots via main.py under Gunicorn/Docker; no launcher scripts at root).
DEFAULT_BACKEND_ROOT_ALLOW = {
    "__init__.py", "main.py", "lifespan.py", "config.py", "DOMAIN_ALLOWLIST.yaml",
}

DEFAULT_ALLOW_ROOT_MD = {
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md",
    "SECURITY.md", "LICENSE.md", "LICENSE",
    "ARCHITECTURE_AUDIT_REPORT.md", "DATABASE_AUDIT_REPORT.md",
    "DESIGN_AUDIT_REPORT.md", "REPO_LAYOUT_AUDIT_REPORT.md",
    "PROJECT_SCAFFOLDING.md", "FEATURES_LIST.md",
    "GOVERNANCE_REPORT.md", "GOVERNANCE_AUDIT_REPORT.md",
    "HEALTH_AUDIT_REPORT.md",
    "ARCHITECTURE_DIAGRAM.md",
    "SYSTEM_AUDIT_REPORT.md",  # emitted by this audit at repo root
}

DEFAULT_ALLOW_DOCS_ROOT = {"scope", "archive", "README.md", "DOCUMENTATION_INDEX.md", "INDEX.md"}
DEFAULT_DOC_EXT = {".md", ".txt", ".rst", ".adoc", ".pdf"}

DEFAULT_FORBIDDEN_ROOT = {
    "backend": [
        r".*\.(log|db|db-shm|db-wal)$",
        r"^token\.tmp$",
        r"^.*\.json$",
        r"^(?!requirements\.txt$).*\.txt$",
        r".*\.bak$",
    ],
    "backend/alembic": [r"^_.*\.py$"],
    "frontend": [r".*\.(log|tsbuildinfo)$", r".*\.bak$"],
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

# ARCHITECTURE_DIAGRAM.md dependency circuit (SEVEN LAWS — arrows point DOWN only):
#   modules -> domains -> infrastructure
#   modules/{actor}/routers -> rbac.dependencies (feature gate)
#   jobs -> domains -> infrastructure
#   providers <- services/jobs only
#   kernel -> (nothing)
#   infrastructure -> (nothing above it)
#   rbac -> imported by modules + middleware ONLY (it is configuration/decision logic)
DEFAULT_FORBIDDEN_EDGES = {
    # DOMAINS own logic + data. They MUST NEVER import a module layer.
    "domains": [
        "modules",
    ],

    # MODULES compose. Thin routers (modules/{actor}/routers) import
    # rbac.dependencies (feature gate) + ONE domain service call only.
    # They must not reach providers/kernel/jobs directly.
    # NOTE: modules -> infrastructure is handled as a CIR2 thin-router
    # bypass (see ARCHITECTURE_DIAGRAM_CIRCUIT_BYPASS_IMPORTS) so the
    # advisory fires instead of being silently dropped.
    "modules": [
        "providers",
        "kernel",
        "jobs",
    ],

    # RBAC is configuration/decision logic. It AGGREGATES every domain's
    # features.py (domains/*/features.py) via package scan and reads
    # infrastructure/kernel primitives. It is IMPORTED by modules + middleware
    # ONLY. Per ARCHITECTURE_DIAGRAM.md it may import domains/infrastructure/
    # kernel, so those are NOT forbidden. It may NOT import modules, providers,
    # jobs, middleware.
    "rbac": [
        "modules", "providers", "jobs", "middleware",
    ],

    # INFRASTRUCTURE imports nothing above it (zero business logic).
    "infrastructure": [
        "modules", "domains", "rbac", "providers", "kernel", "jobs", "middleware",
    ],

    # KERNEL = pure business primitives (money/numbering/country/period).
    # May import infrastructure/ primitives only (per ARCHITECTURE_DIAGRAM.md).
    # Imports nothing else above it.
    "kernel": [
        "modules", "domains", "rbac", "providers", "jobs", "middleware",
    ],

    # PROVIDERS are leaf adapters (3rd-party/AI). Used ONLY by services + jobs.
    # May import infrastructure + kernel primitives (per ARCHITECTURE_DIAGRAM.md),
    # so those are NOT forbidden. May NOT import modules, rbac, middleware, jobs.
    "providers": [
        "modules", "rbac", "middleware", "jobs",
    ],

    # JOBS -> domains -> infrastructure/kernel only. May import domains,
    # infrastructure, kernel, providers (per ARCHITECTURE_DIAGRAM.md), so those
    # are NOT forbidden. May NOT import modules, rbac, middleware.
    "jobs": [
        "modules", "rbac", "middleware",
    ],

    # MIDDLEWARE may import infrastructure + kernel primitives + rbac.dependencies
    # (per ARCHITECTURE_DIAGRAM.md and ARCHITECTURE_DIAGRAM_CIRCUIT_ALLOWED_IMPORTS).
    # It must NOT import modules/domains/providers/jobs directly.
    "middleware": [
        "modules", "domains", "providers", "jobs",
    ],
}


# Variable names that represent DB sessions — only method calls on these
# objects should be flagged as W1 layer-contract violations.
DB_SESSION_NAMES = frozenset({
    "db", "session", "db_session", "sess", "_db", "_session",
    "_db_session", "_sess", "session_scope", "db_session_scope",
})



DEFAULT_WRITE_VERBS: set[str] = {
    "add", "add_all", "commit", "flush", "delete", "merge",
    "bulk_insert_mappings", "bulk_save_objects", "bulk_update_mappings",
    "begin", "begin_nested", "savepoint",
}

DEFAULT_READ_VERBS: set[str] = {
    "query", "get", "scalar", "scalars", "first", "all",
    "one", "one_or_none", "refresh", "expire", "expunge",
}

SQL_WRITE_RE = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|MERGE|UPSERT)\b",
    re.I,
)
SQL_READ_RE = re.compile(
    r"\b(SELECT|SHOW|DESCRIBE|EXPLAIN|WITH)\b",
    re.I,
)


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
    "database.py": "infrastructure/database/database.py",
    "schemas.py": "domains/{domain}/schemas/{name}.py",
    "config.py": "config.py",
    "auth.py": "infrastructure/security/auth.py",
    "email_service.py": "infrastructure/utils/email_service.py",
}

# Modules treated as audit/route-generation TOOLING that must never originate a
# dependency-graph edge (they discover routes via AST and emit thin routers).
_AUDIT_TOOLING_MODULES: set[str] = set()

DEFAULT_SURFACE_NAMES = {"admin","employee","supplier","customer","logistics","public",
                         "webhooks","webhook","api","internal","external","partner",}

# Domain-internal layers (a domain owns these sub-folders under domains/{domain}/).
# NOTE: there is NO flat backend layer for these anymore — they live UNDER a domain.
DEFAULT_DOMAIN_LAYERS    = {"services", "models", "schemas", "policies",
                            "events", "subscribers", "features", "read_models", "ports"}
# Ownership layers = the layers that "own" a business domain (used by placement engine).
DEFAULT_OWNERSHIP_LAYERS = {"services", "models"}

DEFAULT_GRAPH_EXEMPT_LAYERS = {"tests", "scripts", "alembic", "monitoring", "docs", "tools"}

DEFAULT_DEAD_EXEMPT_LAYERS = {"tests","scripts","alembic","monitoring","docs","tools"}

    # Audit layers = application layers that may host live code per ARCHITECTURE_DIAGRAM.md.
DEFAULT_DEAD_AUDIT_LAYERS = {"modules","domains","rbac","infrastructure","kernel","providers","jobs","middleware","events"}

DEFAULT_DEAD_ENTRYPOINTS = [
    r"^main$", r"^lifespan$",
    r"^modules(\.|$)", r"^domains(\.|$)", r"^rbac(\.|$)",
    r"^infrastructure(\.|$)", r"^kernel(\.|$)",
    r"^alembic\.env$", r"^scripts(\.|$)", r"^tests(\.|$)",
    r"^tools(\.|$)",
    r"^middleware(\.|$)", r"^providers(\.|$)",
    r"^events(\.|$)", r"^jobs(\.|$)",
    r"^infrastructure\.database\.base$", r"^infrastructure\.database\.database$",
]

DEFAULT_DUP_CLASS_IGNORE = {
    "Base", "Metadata", "Config", "Enum", "Schema", "Model",
    "Table", "Mixin", "Settings", "Exception", "Error",
}

# ARCHITECTURE_DIAGRAM.md canonical backend packages (AXIS 1/2/3 + platform).
DEFAULT_EXPECTED_BACKEND_PACKAGES = [
    "modules", "domains", "rbac", "infrastructure", "kernel",
    "providers", "jobs", "middleware", "alembic",
    "tests", "scripts",
]

DEFAULT_NO_INIT_DIRS = {"scripts", "tests", "alembic", "tools", "monitoring", "docs"}
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
    # ══════════════════════════════════════════════════════════
    # FINANCIAL DOMAINS
    # ══════════════════════════════════════════════════════════
    "finance": {
        # Financial operations — ledger, journal, AP/AR, treasury (canonical
        # domain per ARCHITECTURE_DIAGRAM.md line 103)
        "finance", "financial", "ledger", "sub_ledger", "general_ledger",
        "journal", "invoice", "invoices", "tax", "vat", "commission",
        "accounting", "posting", "credit_control", "period_close",
        "erp", "commission_write", "financial_reports",
        "financial_reporting", "finance_automation", "finance_erp",
        "fiscal", "budget", "reconciliation",
        # folded from former "treasury" domain
        "treasury", "treasurer", "cash", "bank", "payout", "payouts",
        "settlement", "settlements", "gateway_reconciliation",
        "payment_engine", "payment_orchestrator", "auto_payout",
        "payout_batch", "cash_flow", "fx",
    },
    "accounts": {
        # Chart of accounts / bookkeeping (canonical domain; distinct from finance ops)
        "accounts", "account", "chart_of_accounts", "coa",
        "gl_account", "fiscal_period",
    },

    # ══════════════════════════════════════════════════════════
    # COMMERCE DOMAINS
    # ══════════════════════════════════════════════════════════
    "orders": {
        "order", "orders", "checkout", "cart", "purchase", "purchases",
        "return", "returns", "dispute", "disputes", "fulfillment",
        "ghost",  # ghost orders — NOT in security
    },
    "catalog": {
        # NOTE: "inventory"/"stock"/"search" removed — own domains below
        "catalog", "product", "products", "category", "categories",
        "variant", "variants", "filter", "filters", "moderation",
        "verification", "advanced_filter", "advanced_search",
        "product_verification", "product_moderation", "sku",
    },
    "suppliers": {
        # canonical domain is plural (diagram line 104)
        "supplier", "suppliers", "vendor", "vendors", "onboarding",
        "kyc", "badge", "storefront", "supplier_badge", "supplier_health",
        "supplier_profile", "supplier_products", "supplier_inventory",
        "supplier_onboarding", "contract",
    },
    "customers": {
        "customer", "customers", "address", "addresses", "point",
        "points", "profile", "preferences", "customer_health",
        "segment",
    },
    "payments": {
        # Payment gateways + billing (folded from former "gateway"/"billing")
        "payments", "payment", "payment_gateway", "payment_provider",
        "payment_adapter", "payment_processor", "gateway", "checkout_gateway",
        "stripe", "paypal", "tap", "thawani", "paytabs",
        "supplier_payments", "logistic_payments",
        "billing", "subscription", "subscriptions", "billing_cycle",
        "billing_cycles", "receipt", "receipts", "charge", "charges",
    },
    "logistics": {
        # folded from former "shipping" domain
        "logistics", "shipping", "shipment", "shipments", "dispatch",
        "delivery", "carrier", "fleet", "route", "routes", "pod",
        "tracking", "parcel", "geofence", "geo_fence", "map",
        "live_tracking", "shipping_rate", "shipping_rates",
        "shipping_zone", "shipping_zones", "carrier_config", "carrier_configs",
    },

    # ══════════════════════════════════════════════════════════
    # SUPPORTING DOMAINS
    # ══════════════════════════════════════════════════════════
    "comms": {
        "chat", "comm", "comms", "communication", "email", "fix_chat",
        "meeting", "message", "messages", "notification", "notifications",
        "push", "sms", "ticket", "video", "translation",
        "websocket_manager", "write_chat",
    },
    "hr": {
        "hr", "employee", "employees", "attendance", "shift", "shifts",
        "leave", "coi", "lms", "performance", "succession", "travel",
        "hse", "dei", "offboarding", "roster", "handover", "payroll",
        "background", "shift_handover", "shift_roster",
        "shift_scheduling", "background_check", "recruitment",
    },


    # ══════════════════════════════════════════════════════════
    # IDENTITY domain (actor user table lives in each domain schema, e.g. customer.user; no core/platform/identity schema)
    # ══════════════════════════════════════════════════════════


    # ══════════════════════════════════════════════════════════
    # GEOGRAPHY & MEDIA
    # ══════════════════════════════════════════════════════════
    "country": {
        # canonical domain is "country" (diagram line 104); folded from
        # former "geography" domain
        "country", "countries", "city", "cities", "region", "zone",
        "territory", "postal", "currency", "border", "cross_border",
        "cross_border_tracker", "country_detection", "country_research",
        "economics", "geo", "geography", "localization", "location",
        "location_service",
    },
    "media": {
        "media", "asset", "assets", "image", "images", "upload",
        "uploads", "file", "storage", "free_image", "cdn", "video",
    },

    # ══════════════════════════════════════════════════════════
    # ANALYTICS & CONFIGURATION
    # ══════════════════════════════════════════════════════════


    # ══════════════════════════════════════════════════════════
    # EXTENDED DOMAINS (for 300+ tables)
    # ══════════════════════════════════════════════════════════


    # ══════════════════════════════════════════════════════════
    # PLATFORM / INFRA DOMAINS (real backend folders)
    # ══════════════════════════════════════════════════════════
    "governance": {
        # folded from former "audit" domain; compliance/governance engine
        "governance", "policy", "policies", "compliance_engine",
        "governance_engine", "rule_engine", "tenant", "tenancy",
        "compliance", "gdpr", "sox", "audit", "worm", "audit_log",
        "audit_trail", "permission_audit", "communication_audit", "auditor",
    },
}


# Build alias lookup (built ONCE at module load)
PLACEMENT_ALIAS_TO_DOMAIN: dict[str, str] = {}
for _dom, _aliases in PLACEMENT_DOMAIN_KEYWORDS.items():
    PLACEMENT_ALIAS_TO_DOMAIN[_dom.lower()] = _dom
    for _a in _aliases:
        PLACEMENT_ALIAS_TO_DOMAIN[str(_a).lower()] = _dom


def _rebuild_placement_aliases() -> None:
    """Rebuild alias lookup after external governance taxonomy is loaded."""
    PLACEMENT_ALIAS_TO_DOMAIN.clear()
    for dom, aliases in PLACEMENT_DOMAIN_KEYWORDS.items():
        canonical = str(dom).lower()
        PLACEMENT_ALIAS_TO_DOMAIN[canonical] = canonical
        for alias in aliases:
            PLACEMENT_ALIAS_TO_DOMAIN[str(alias).lower()] = canonical

# Generic tokens that must NEVER become domain names
# ===========================================================================
# CANONICAL DOMAINS — single source of truth for the 13 bounded contexts
# defined in ARCHITECTURE_DIAGRAM.md (AXIS 2). PLACEMENT_DOMAIN_KEYWORDS keeps
# a richer alias list for *inference* (mapping legacy tokens to a domain), but
# everything an AI agent READS (the placement contract, domain-folder validity)
# must use exactly these 13 — never treasury/core/identity/gateway/etc.
# ===========================================================================
CANONICAL_DOMAINS: list[str] = [
    "finance", "accounts", "catalog", "orders", "payments", "logistics",
    "suppliers", "customers", "hr", "comms", "media", "country", "governance",
]

# Alias → canonical domain. Folded from PLACEMENT_DOMAIN_KEYWORDS so the
# published contract teaches AI where synonyms actually belong (e.g. treasury
# is a finance/ sub-capability, not its own domain).
CANONICAL_DOMAIN_ALIASES: dict[str, set[str]] = {
    "finance": {"finance", "financial", "ledger", "sub_ledger", "general_ledger",
                "journal", "invoice", "invoices", "tax", "vat", "commission",
                "accounting", "posting", "credit_control", "period_close", "erp",
                "commission_write", "financial_reports", "financial_reporting",
                "finance_automation", "finance_erp", "fiscal", "budget",
                "reconciliation", "treasury", "treasurer", "cash", "bank",
                "payout", "payouts", "settlement", "settlements",
                "gateway_reconciliation", "payment_engine", "payment_orchestrator",
                "auto_payout", "payout_batch", "cash_flow", "fx"},
    "accounts": {"accounts", "account", "gl_account", "chart_of_accounts"},
    "catalog": {"catalog", "product", "products", "category", "categories",
                "variant", "variants", "filter", "filters", "moderation",
                "verification", "advanced_filter", "advanced_search",
                "product_verification", "product_moderation", "sku", "search",
                "synonym", "synonyms", "search_index", "search_log",
                "search_config", "autocomplete", "inventory", "stock", "warehouse",
                "warehouses", "reservation", "reservations", "stock_movement",
                "stock_adjustment", "reorder"},
    "orders": {"order", "orders", "checkout", "cart", "purchase", "purchases",
               "return", "returns", "dispute", "disputes", "fulfillment", "ghost",
               "commerce", "promotion", "promotions", "coupon", "coupons",
               "discount", "discounts", "flash_sale", "wishlist", "referral",
               "loyalty", "campaign", "voucher", "banner", "banners"},
    "payments": {"payment", "payments", "gateway", "checkout_gateway",
                 "payment_gateway", "payment_provider", "payment_adapter",
                 "payment_processor", "stripe", "paypal", "tap", "thawani",
                 "paytabs", "supplier_payments", "logistic_payments", "billing",
                 "subscription", "subscriptions", "billing_cycle",
                 "billing_cycles", "receipt", "receipts", "charge", "charges"},
    "logistics": {"logistics", "shipping", "shipment", "shipments", "dispatch",
                  "delivery", "carrier", "fleet", "route", "routes", "pod",
                  "tracking", "parcel", "geofence", "geo_fence", "map",
                  "live_tracking", "shipping_rate", "shipping_rates",
                  "shipping_zone", "shipping_zones", "carrier_config",
                  "carrier_configs"},
    "suppliers": {"supplier", "suppliers", "vendor", "vendors", "onboarding",
                  "kyc", "badge", "storefront", "supplier_badge",
                  "supplier_health", "supplier_profile", "supplier_products",
                  "supplier_inventory", "supplier_onboarding", "contract"},
    "customers": {"customer", "customers", "address", "addresses", "point",
                  "points", "profile", "preferences", "customer_health", "segment",
                  "reviews", "rating", "ratings", "review", "review_moderation",
                  "review_response"},
    "hr": {"hr", "employee", "employees", "attendance", "shift", "shifts",
           "leave", "coi", "lms", "performance", "succession", "travel", "hse",
           "dei", "offboarding", "roster", "handover", "payroll", "background",
           "shift_handover", "shift_roster", "shift_scheduling",
           "background_check", "recruitment"},
    "comms": {"chat", "comm", "comms", "communication", "email", "fix_chat",
              "meeting", "message", "messages", "notification", "notifications",
              "push", "sms", "ticket", "video", "translation", "websocket_manager",
              "write_chat", "notification_template", "notification_templates",
              "push_token", "push_tokens", "email_template", "sms_template"},
    "media": {"media", "asset", "assets", "image", "images", "upload", "uploads",
              "file", "storage", "free_image", "cdn", "video", "documents",
              "document", "certificate", "certificates", "attachment",
              "attachments", "contract_document"},
    "country": {"geography", "country", "countries", "city", "cities", "region",
                "zone", "territory", "postal", "currency", "border",
                "cross_border", "cross_border_tracker", "country_detection",
                "country_research", "economics", "geo", "localization",
                "location", "location_service"},
    "governance": {"governance", "policy", "policies", "compliance_engine",
                   "governance_engine", "rule_engine", "tenant", "tenancy",
                   "permissions", "permission_grant", "permission_grants",
                   "rbac_policy", "rbac_policies", "access_control", "webhooks",
                   "webhook", "webhook_endpoint", "webhook_delivery",
                   "webhook_log", "events", "outbox", "outbox_events",
                   "event_log", "event_subscription", "event_subscriptions",
                   "saga", "reporting", "scheduled_report", "scheduled_reports",
                   "export", "exports", "report_template", "fraud", "risk",
                   "compliance", "gdpr", "sox", "audit", "worm", "audit_log",
                   "audit_trail", "permission_audit", "communication_audit",
                   "auditor"},
}


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

# Domain-internal layers (sub-folders of domains/{domain}/), per ARCHITECTURE_DIAGRAM.md.
PLACEMENT_DOMAIN_LAYERS = [
    "services", "models", "schemas", "policies", "events", "subscribers", "features", "read_models", "ports",
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
# SECTION 3: CIRCUIT CONTRACT — ACTIVE (documents/ARCHITECTURE_DIAGRAM.md, seven laws)
# ============================================================================
# Canonical layers and the ONLY imports each may make. This table IS the circuit the
# audit enforces (Law 1: arrows point down only):
#
#   modules      -> domains, rbac, infrastructure           (thin routers; no DB writes)
#   domains       -> infrastructure, kernel, providers       (owns logic + data)
#   rbac          -> infrastructure, kernel                  (aggregates features; decision only)
#   kernel        -> infrastructure                          (pure business primitives)
#   infrastructure-> (nothing above it)                      (platform; zero business logic)
#   providers     -> infrastructure, kernel                  (3rd-party/AI adapters)
#   jobs          -> domains, infrastructure, kernel, providers
#   middleware     -> infrastructure, kernel
#
# Abolished flat root layers (controllers/ routers/ services/ models/ db/ utils/
# core/ dependencies/) are deliberately ABSENT here. check_architecture_diagram_compliance
# reports them as NS1-NS4 at the folder level; check_circuit_contract skips any layer
# not present in this table, so an abolished layer can never be validated as a
# legitimate circuit (which would let a cheating AI fake a pre-migration implementation).
ARCHITECTURE_DIAGRAM_CIRCUIT_ALLOWED_IMPORTS: dict[str, set[str]] = {
    "main": {"modules", "domains", "rbac", "infrastructure", "kernel",
             "providers", "jobs", "middleware", "config"},
    "modules": {"domains", "rbac"},
    "domains": {"infrastructure", "kernel", "providers"},
    "rbac": {"infrastructure", "kernel", "domains"},
    "kernel": {"infrastructure"},
    "infrastructure": set(),
    "providers": {"infrastructure", "kernel"},
    "jobs": {"domains", "infrastructure", "kernel", "providers"},
    "middleware": {"infrastructure", "kernel", "rbac"},
    "config": set(),
    "data": set(),
}

ARCHITECTURE_DIAGRAM_CIRCUIT_BYPASS_IMPORTS: dict[tuple[str, str], str] = {
    ("modules", "infrastructure"): (
        "module routers stay thin (Law 2): routers must not import infrastructure "
        "directly — delegate to domains/*/services. Only modules/{actor}/auth may "
        "import infrastructure security primitives (JWT/session)."
    ),
    ("modules", "providers"): (
        "providers are called by domains/*/services and jobs only, never by module routers"
    ),
    ("modules", "kernel"): (
        "module routers stay thin (Law 2): no direct kernel primitives — delegate to domains/*/services"
    ),
    ("domains", "modules"): (
        "arrows point down only (Law 1) — domains must never import a module"
    ),
    ("domains", "rbac"): (
        "rbac is imported by modules/middleware only — domains enforce policies, not permissions"
    ),
    ("rbac", "modules"): (
        "rbac is imported by modules/middleware only — never the reverse"
    ),
    ("kernel", "modules"): (
        "kernel is a leaf primitive — imports nothing above it"
    ),
    ("kernel", "domains"): (
        "kernel is a leaf primitive — imports nothing above it"
    ),
    ("kernel", "rbac"): (
        "kernel is a leaf primitive — imports nothing above it"
    ),
    ("infrastructure", "modules"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("infrastructure", "domains"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("infrastructure", "rbac"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("infrastructure", "kernel"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("infrastructure", "providers"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("infrastructure", "jobs"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("infrastructure", "middleware"): (
        "infrastructure imports nothing above it (Law 1)"
    ),
    ("providers", "modules"): (
        "providers are imported by services/jobs only — never the reverse"
    ),
    ("providers", "domains"): (
        "providers are imported by services/jobs only — never the reverse"
    ),
    ("providers", "rbac"): (
        "providers are imported by services/jobs only — never the reverse"
    ),
}

_AUDIT_ROUTER_TOOLING_SUBDIRS: set[str] = {"generated"}


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
    priority: str = "P3"
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
        self,
        sev: str,
        code: str,
        domain: str,
        path: str,
        message: str,
        intended: str = "",
        line: int | None = None,
        priority: str | None = None,
        count: int = 1,
        examples: list[str] | None = None,
    ) -> None:
        key = (code, path, line, message)
        if key in self._seen:
            return
        self._seen.add(key)
        if priority is None:
            priority = _get_rule_priority(code)
        self.findings.append(
            Finding(
                sev=sev, code=code, domain=domain,
                path=path, message=message,
                intended=intended, line=line,
                priority=priority, count=count,
                examples=examples or [],
            )
        )
        self.counters[code] += count
        

def _get_rule_priority(code: str) -> str:
    """Map rule code to priority tier."""
    _PRIORITY_MAP = {
        # ── P0: Production / security risk ──
        "HL402": "P0", "SEC101": "P0", "SEC105": "P0", "RT500": "P0",
        "SEC5": "P0", "SEC8": "P0",
        "DBA02": "P0", "DBA05": "P0", "DBA10": "P0", "DBA20": "P0", "DBA33": "P0",
        "CIR1": "P0", "W1": "P0", "DG": "P0", "DG3": "P0",
        "SEC2": "P0", "SEC3": "P0", "SEC4": "P0",
        "X1": "P0", "F5": "P0", "M1": "P0", "R1": "P0",
        "CG1": "P0", "CG2": "P0", "CG3": "P0",
        "MW3": "P0", "FE8": "P0", "FE11": "P0", "CA3": "P0",
        # ── P1: Scaling / performance risk ──
        "HL403": "P1", "HL601": "P1", "HL602": "P1", "SC102": "P1",
        "PG102": "P1", "PG103": "P1", "SC501": "P1", "SC101": "P1",
        "HL501": "P1", "OB101": "P1", "OB102": "P1",
        "DBA13": "P1", "DBA16": "P1", "DBA26": "P1",
        "DBA27": "P1",
        "DS02": "P1", "DS06": "P1", "DS10": "P1", "DS12": "P1", "DS15": "P1",
        "CIR2": "P1", "W2": "P1", "W3": "P1", "DG2": "P1",
        "PERF1": "P1", "PERF2": "P1",
        "L1": "P1", "G1": "P1",
        "DOM3": "P1", "S4": "P1", "M3": "P1",
        "LC1": "P1", "BC1": "P1", "BC3": "P1",
        "MET5": "P1",
        # ── P2: Maintainability / structure ──
        "HL101": "P2", "HL102": "P2", "FEH101": "P2", "FEH501": "P2",
        "HL502": "P2", "API101": "P2", "MR104": "P2",
        "DP101": "P2", "DP103": "P2", "DP104": "P2",
        "FEH301": "P2", "FEH801": "P2", "PG101": "P2",
        "DS01": "P2", "DS03": "P2", "DS04": "P2", "DS05": "P2",
        "DS07": "P2", "DS09": "P2", "DS11": "P2", "DS13": "P2", "DS14": "P2",
        "DBA01": "P2", "DBA03": "P2", "DBA07": "P2", "DBA08": "P2",
        "DBA09": "P2", "DBA11": "P2", "DBA12": "P2",
        "Q1": "P2", "W4": "P2", "D1": "P2", "D2": "P2", "D3": "P2",
        "S1": "P2", "S2": "P2", "S3": "P2", "S5": "P2",
        "M2": "P2", "M4": "P2",
        "P2": "P2", "P3": "P2", "P4": "P2", "P5": "P2",
        "DOM1": "P2", "DOM2": "P2", "DOM7": "P2",
        "MV1": "P2", "MV2": "P2", "MV3": "P2",
        "RN1": "P2", "RN2": "P2", "RN3": "P2",
        "DB1": "P2", "DB2": "P2", "DB3": "P2",
        "FE1": "P2", "FE3": "P2", "FE4": "P2", "FE5": "P2",
        "FE7": "P2", "FE9": "P2", "FE10": "P2", "FE12": "P2", "FE13": "P2",
        "QUAL1": "P2", "QUAL3": "P2",
        "A1": "P2", "MET2": "P2",
        "CFG1": "P2", "CFG2": "P2", "CFG3": "P2", "CFG4": "P2",
        "MW1": "P2", "MW2": "P2",
        "PF1": "P2", "PF2": "P2",
        "AS1": "P2", "AS2": "P2",
        "SEC6": "P2", "SEC7": "P2", "SEC9": "P2", "SEC10": "P2",
        "PERF3": "P2", "PERF4": "P2", "PERF5": "P2", "PERF6": "P2",
        "FT1": "P2", "FT2": "P2",
        "CA1": "P2", "CA2": "P2",
        "BC2": "P2",
        "SYM2": "P2", "API2": "P2",
        # ── NS / NEW codes (ARCHITECTURE_DIAGRAM.md alignment) ──
        "NS9": "P1", "NS12": "P0", "NS13": "P0", "NS19": "P1",
        "NS23": "P0", "NS24": "P0", "NS25": "P1", "NS26": "P1",
        "NS27": "P1", "NS28": "P1", "NS29": "P1",
        "NS30": "P2", "NS31": "P2", "NS32": "P2",
        "NS38": "P1", "NS39": "P0", "NS40": "P1", "NS41": "P1",
        "NS42": "P2", "NS43": "P2",
        "FE14": "P2", "DBA38": "P2",
        # ── P3: Hygiene / style ──
        "HL201": "P3", "HL203": "P3", "HL204": "P3",
        "HL301": "P3", "HL302": "P3", "HL303": "P3",
        "HL401": "P3", "HL901": "P3", "HL902": "P3",
        "FEH201": "P3", "FEH401": "P3", "FEH402": "P3",
        "FEH503": "P3", "FEH504": "P3", "FEH601": "P3",
        "FEH802": "P3", "DP102": "P3", "DP105": "P3",
        "DS08": "P3", "DS16": "P3", "DS17": "P3", "DS18": "P3",
        "DBA04": "P3", "DBA17": "P3", "DBA18": "P3", "DBA19": "P3",
        "DBA21": "P3", "DBA22": "P3", "DBA23": "P3",
        "F1": "P3", "F2": "P3", "F3": "P3", "F4": "P3",
        "F6": "P3", "F7": "P3", "F8": "P3", "F9": "P3", "G0": "P3",
        "P1": "P3", "H1": "P3",
        "QUAL2": "P3", "QUAL4": "P3",
        "A2": "P3", "FE2": "P3", "FE6": "P3",
        "SYM1": "P3", "API1": "P3",
        "AS3": "P3", "MET3": "P3", "MET4": "P3",
        "REG1": "P3", "REG2": "P3", "REG3": "P3",
        "CFG5": "P3",
        "HL110": "P3", "HL801": "P3",
        "MR101": "P3",
        "FEH502": "P3", "FEH701": "P3",
        "PG201": "P3",
        "PL101": "P3",
        "RT201": "P3", "RT404": "P3", "RT400": "P3",
        "DBA14": "P3", "DBA15": "P3", "DBA24": "P3",
        "DBA28": "P3", "DBA29": "P3", "DBA30": "P3",
        "DBA31": "P3", "DBA32": "P3", "DBA34": "P3",
        "DBA35": "P3", "DBA36": "P3", "DBA37": "P3",
        "DG4": "P3", "DG5": "P3",
        "LC2": "P3", "LC3": "P3",
        "HC1": "P2", "PRV1": "P2", "PRV2": "P1",
        # ── NS / gap-closing code priorities (companion update) ──
        "NS9":  "P1", "NS12": "P0", "NS13": "P0", "NS19": "P1",
        "NS23": "P0", "NS24": "P0", "NS25": "P1", "NS26": "P1",
        "NS27": "P1", "NS28": "P1", "NS29": "P1",
        "NS30": "P2", "NS31": "P2", "NS32": "P2",
        "NS38": "P1", "NS39": "P0", "NS40": "P1", "NS41": "P1",
        "NS42": "P2", "NS43": "P2",
        "FE14": "P2", "DBA38": "P2",
    }
    return _PRIORITY_MAP.get(code, "P3")

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


def _domain_of_fallback(path_rel: str) -> str:
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
        return _domain_of_fallback(path_rel)
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
    cyc = list(cycle)
    if len(cyc) > 1 and cyc[0] == cyc[-1]:
        cyc = cyc[:-1]
    if not cyc:
        return []
    min_i = min(range(len(cyc)), key=lambda i: cyc[i])
    return cyc[min_i:] + cyc[:min_i]


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

def dotted_name(node: ast.AST) -> str:
    """Return dotted name from an AST Name/Attribute chain.
    Used by health audit for call resolution."""
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def is_public_name(name: str) -> bool:
    """Return True if the name is public (no leading underscore)."""
    return bool(name) and not name.startswith("_")

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
        "artifact_names", "dup_class_ignore",
        "expected_backend_packages", "frontend_root_allow",
    }
    scalar_keys = {
        "max_read_bytes", "flat_threshold", "large_subpackage_threshold",
        "god_fan_out", "god_fan_in", "max_cycles", "max_cycle_length",
        "frontend_flat_threshold", "frontend_large_folder_threshold",
        "detect_module_cycles",
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


def _apply_scaffolding_contract(eff: dict, contract: dict | None) -> None:
    """
    Apply .governance/scaffolding_contract.json.

    This contract is the repo's canonical placement source. It can coexist
    with documents/scope YAML/JSON files, but it must win for folder patterns,
    canonical domains, surfaces, and explicit forbidden folders.
    """
    if not isinstance(contract, dict):
        return

    placement_rules = contract.get("placement_rules")
    if not isinstance(placement_rules, dict):
        placement_rules = {}

    valid_domains: set[str] = set()
    for layer_name in ("domains", "services", "models", "providers"):
        layer_rule = placement_rules.get(layer_name)
        if not isinstance(layer_rule, dict):
            continue
        for domain in layer_rule.get("valid_domains", []) or []:
            valid_domains.add(str(domain).lower())

    domain_keywords = contract.get("domain_keywords")
    if isinstance(domain_keywords, dict) or valid_domains:
        normalized_keywords: dict[str, set[str]] = {}
        if isinstance(domain_keywords, dict):
            for domain, keywords in domain_keywords.items():
                canonical = str(domain).lower()
                values = {canonical}
                if isinstance(keywords, list):
                    values |= {str(item).lower() for item in keywords}
                normalized_keywords[canonical] = values
                valid_domains.add(canonical)

        for domain in valid_domains:
            normalized_keywords.setdefault(domain, {domain})

        domain_aliases = {
            "comms": "communication",
            "comm": "communication",
            "geography": "country",
            "geo": "country",
        }
        for alias, canonical in domain_aliases.items():
            if canonical in normalized_keywords:
                normalized_keywords[canonical].add(alias)

        PLACEMENT_DOMAIN_KEYWORDS.clear()
        PLACEMENT_DOMAIN_KEYWORDS.update(normalized_keywords)
        _rebuild_placement_aliases()

        for domain in sorted(valid_domains):
            eff.setdefault("domains", {}).setdefault(domain, {"may_import": []})

    router_rule = placement_rules.get("router_layout")
    if isinstance(router_rule, dict):
        pattern = str(router_rule.get("pattern", "") or "")
        eff["router_pattern"] = pattern
        if "{surface}/" in pattern.replace("\\", "/"):
            eff["router_layout"] = "surface_dirs"
        elif pattern:
            eff["router_layout"] = "flat"
        if isinstance(router_rule.get("valid_surfaces"), list):
            eff["surface_names"] = {
                str(surface).lower()
                for surface in router_rule.get("valid_surfaces", [])
            }

    forbidden_folders = contract.get("forbidden_folders")
    if isinstance(forbidden_folders, list):
        eff["forbidden_contract_folders"] = [
            str(item).replace("\\", "/").strip("/")
            for item in forbidden_folders
            if str(item).strip()
        ]

    surface_domain_matrix = contract.get("surface_domain_matrix")
    if isinstance(surface_domain_matrix, dict):
        eff["surface_domain_matrix"] = {
            str(surface).lower(): [str(domain).lower() for domain in domains]
            for surface, domains in surface_domain_matrix.items()
            if isinstance(domains, list)
        }

    frontend_rules = contract.get("frontend_rules")
    if isinstance(frontend_rules, dict):
        eff["frontend_rules"] = frontend_rules


def rules_source_label(eff: dict) -> str:
    sources = [str(item) for item in eff.get("rule_sources", []) if str(item).strip()]
    if sources:
        return ", ".join(dict.fromkeys(sources))
    return "embedded defaults"


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
        "rule_sources": [],
        "known_layers": set(),
        "router_layout": "modules",
        "router_pattern": "backend/modules/{surface}/routers/{domain}_{operation}_router.py",
        "forbidden_contract_folders": [],
        # configurable policy defaults
        "feature_stop_names": set(FEATURE_STOP_NAMES),
        "feature_suffixes": list(FEATURE_SUFFIXES),
        "repo_root_min_top_dirs": 8,
        "repo_root_min_py_files": 50,
        "local_path_scan_tops": ["backend", "frontend", "scripts"],
        "media_scan_layers": [
            "modules", "domains", "rbac", "infrastructure", "kernel",
            "providers", "jobs", "middleware",
        ],
        "scratch_scan_roots": ["frontend", "scripts", "."],
        "logical_domains": {
            "database": {"parts": ["alembic", "infrastructure.database"]},
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
            {"layer": "services", "flat_code": "S1", "large_code": "S5"},
            {"layer": "models", "flat_code": "M2", "large_code": "M4"},
            {"layer": "policies", "flat_code": "S1", "large_code": "S5"},
            {"layer": "schemas", "flat_code": "M2", "large_code": "M4"},
        ],
        "codeowners": {
            "default_owner": "@zozi/backend",
            "domain_owner_template": "@zozi/{domain}",
            "domain_paths": ["backend/domains/{domain}/services/", "backend/domains/{domain}/models/"],
            "surface_paths": ["backend/modules/{surface}/routers/", "backend/modules/{surface}/auth/"],
        },
        "placement": {
            "enabled": True,
            "layers": ["services", "models", "policies", "schemas", "events", "subscribers", "features", "providers", "jobs"],
            "router_layer": "modules",
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
    candidates.append(repo / ".governance")

    struct = None
    layer_cfg = None
    gov = None
    contract = (
        _read_cfg(repo / ".governance" / "scaffolding_contract.json")
        or _read_cfg(repo / ".governance" / "scaffolding_contract.yaml")
        or _read_cfg(repo / ".governance" / "scaffolding_contract.yml")
    )
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

    if contract:
        eff["from_yaml"] = True
        eff["rule_sources"].append(".governance/scaffolding_contract.json")
        _apply_scaffolding_contract(eff, contract)
    if struct:
        eff["from_yaml"] = True
        eff["rule_sources"].append("repo_structure")
        _apply_structure(eff, struct)
    if layer_cfg:
        eff["from_yaml"] = True
        eff["rule_sources"].append("layer_rules")
        _apply_layer(eff, layer_cfg)
    if gov:
        eff["from_yaml"] = True
        eff["rule_sources"].append("governance")
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

    # ARCHITECTURE_DIAGRAM §10.1: routers/generated/auto_router.py is TOOLING,
    # not a runtime layer. It discovers controller route declarations via AST only
    # and emits thin routers into routers/ — it must never originate a
    # dependency-graph edge, and generated routers stay plain `routers` members.
    audit_tooling_modules = eff.get("audit_tooling_modules", _AUDIT_TOOLING_MODULES)

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
        if module in audit_tooling_modules:
            # Tooling module: skip edge extraction so it never enters the circuit.
            continue
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
        return "move into domains/<domain>/models/ and add __table_args__ schema"
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
                c.name, "a layer package (modules/ domains/ rbac/ infrastructure/ kernel/ providers/ jobs/ middleware/)",
            )
            rep.add(
                YEL, "P3", "backend", rp,
                "module at backend root (shadows the canonical home or is mis-placed)",
                intended=f"move to {home}; backend/ root holds only main/lifespan/config/DOMAIN_ALLOWLIST",
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
        {"layer": "services", "flat_code": "S1", "large_code": "S5"},
        {"layer": "models", "flat_code": "M2", "large_code": "M4"},
        {"layer": "schemas", "flat_code": "SC1", "large_code": "SC5"},
        {"layer": "policies", "flat_code": "P1", "large_code": "P5"},
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
    # Abolished flat root layers (controllers/ routers/ services/ models/
    # utils/ db/ core/) are reported by check_architecture_diagram_compliance as
    # NS1-NS4 (abolished / must be re-homed). They are NOT a valid grouping
    # target here. Domain-internal layers (domains/{d}/services|models|...)
    # are surface-agnostic by design and must not contain surface sub-folders.



def check_contract_forbidden_folders(repo: Path, rep: Report, eff: dict) -> None:
    """Report folders explicitly forbidden by the scaffolding contract."""
    for folder in eff.get("forbidden_contract_folders", []) or []:
        folder_rel = str(folder).replace("\\", "/").strip("/")
        if not folder_rel:
            continue
        folder_path = repo / folder_rel
        if not folder_path.exists():
            continue
        rep.add(
            YEL,
            "SCF1",
            "backend" if folder_rel.startswith("backend/") else "repo",
            folder_rel + "/",
            "folder exists but is explicitly forbidden by scaffolding_contract.json",
            intended="move files to a permitted domain folder from .governance/scaffolding_contract.json",
        )


def check_rls_cluster(repo: Path, rep: Report, eff: dict) -> None:
    """L1 + SEC11: Detect multiple/divergent RLS enforcers.

    L1:    Multiple files *named* rls_* / country_rls          (YEL)
    SEC11: Multiple *independent* RLS policy definitions        (RED)
           Per ARCHITECTURE_DIAGRAM §2.4 / §10.4:
           exactly ONE canonical RLS enforcer.  A second/divergent
           implementation is a fail-open security violation.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    # ── L1: filename-based detection (original behaviour) ── (enhanced) ──
    hits = [
        rel(f, repo)
        for f in iter_text_files(backend, eff)
        if f.suffix.lower() == ".py"
        and (f.stem.startswith("rls_") or f.stem == "country_rls")
    ]
    # Also check data/ directory for SQL-based RLS
    data_dir = backend / "data"
    if data_dir.exists():
        for f in data_dir.glob("*.sql"):
            if "rls" in f.stem.lower() or "policy" in f.stem.lower():
                hits.append(rel(f, repo))

    if len(hits) >= 2:
        rep.add(
            YEL, "L1", "security", "middleware/ + infrastructure/database/",
            f"{len(hits)} RLS-named modules -> two enforcers = fail-open risk",
            intended="consolidate to ONE canonical RLS enforcer (e.g. "
                     "backend/infrastructure/database/security.py) applied uniformly via a "
                     "session hook or shared auth dependency; alias/delete the rest: "
                     + ", ".join(hits),
        )

    # ── SEC11: content-based detection of independent RLS implementations ──
    rls_define_re = re.compile(
        r"(?:ENABLE\s+ROW\s+LEVEL\s+SECURITY"
        r"|FORCE\s+ROW\s+LEVEL\s+SECURITY"
        r"|CREATE\s+POLICY\s+\w+\s+ON"
        r"|CREATE\s+RLS\s+POLICY)",
        re.I,
    )
    rls_context_re = re.compile(
        r"set_config\s*\(\s*['\"]app\.current_country_code",
        re.I,
    )

    rls_definers: list[str] = []
    rls_context_setters: list[str] = []

    for f in iter_text_files(backend, eff):
        if f.suffix.lower() not in {".py", ".sql"}:
            continue
        text = read_text(f) or ""
        if rls_define_re.search(text):
            rls_definers.append(rel(f, repo))
        if rls_context_re.search(text):
            rls_context_setters.append(rel(f, repo))

    # Multiple independent RLS policy definers → RED (fail-open)
    if len(rls_definers) > 1:
        rep.add(
            RED, "SEC11", "security", ", ".join(rls_definers[:3]),
            f"{len(rls_definers)} independent RLS policy definitions detected. "
            f"A path that omits RLS silently bypasses tenant/country isolation.",
            intended="consolidate to ONE canonical RLS enforcer "
                     "(e.g. backend/infrastructure/database/security.py) applied uniformly via a "
                     "session/connection hook or a shared auth dependency; a single "
                     "RLS SQL policy file (data/*rls*.sql) is acceptable only if it is "
                     "THE one canonical source, never a second scattered module",
        )

    # Too many context setters → YEL (inconsistency risk)
    if len(rls_context_setters) > 2:
        rep.add(
            YEL, "SEC11", "security", ", ".join(rls_context_setters[:3]),
            f"{len(rls_context_setters)} files set app.current_country_code — "
            f"risk of inconsistent RLS context",
            intended="set RLS context in exactly one place "
                     "(middleware or dependency), not scattered across modules",
        )


def check_scaling_readiness(repo: Path, rep: Report, eff: dict) -> None:
    """SC1 / SC2 / SC3: Scaling-readiness checks per ARCHITECTURE_DIAGRAM §9.3.

    SC1: DB pool_size must be ≤ 5 behind PgBouncer.
    SC2: Sync-only SQLAlchemy blocks the event loop (Phase B blocker).
    SC3: In-process WebSocket fan-out won't scale past one replica.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    # ── SC1: pool size vs PgBouncer requirement ──────────────────
    pool_size: int | None = None
    pool_file: str | None = None
    for candidate in (
        backend / "utils" / "config.py",
        backend / "db"    / "database.py",
        backend / "settings.py",
    ):
        if not candidate.exists():
            continue
        text = read_text(candidate) or ""
        for pat in (r"DB_POOL_SIZE\s*=\s*(\d+)", r"pool_size\s*=\s*(\d+)"):
            m = re.search(pat, text)
            if m:
                pool_size = int(m.group(1))
                pool_file = rel(candidate, repo)
                break
        if pool_size is not None:
            break

    if pool_size is not None and pool_size > 5:
        rep.add(
            YEL, "SC1", "backend", pool_file or "backend/",
            f"DB pool_size={pool_size} exceeds PgBouncer-safe limit (§9.3). "
            f"Each replica holds {pool_size}+overflow connections.",
            intended="set pool_size=5, max_overflow=10; put PgBouncer "
                     "(transaction mode) in front for connection multiplexing",
        )

    # ── SC2: sync-only SQLAlchemy (Phase B blocker) ──────────────
    db_dir = backend / "db"
    has_async = False
    has_sync  = False
    if db_dir.exists():
        for f in db_dir.glob("*.py"):
            text = read_text(f) or ""
            if re.search(r"create_async_engine|AsyncSession|async_sessionmaker", text):
                has_async = True
            if re.search(r"create_engine\(|Session\(|sessionmaker\(", text):
                has_sync = True

    if has_sync and not has_async:
        rep.add(
            YEL, "SC2", "backend", "backend/db/",
            "100% sync SQLAlchemy — blocks the event loop under concurrent "
            "load (§9.3 Phase B blocker). Sync drivers serialise all DB I/O.",
            intended="convert hot read/write paths to AsyncPG + SQLAlchemy 2.0 "
                     "async sessions (create_async_engine + AsyncSession)",
        )

    # ── SC3: WebSocket fan-out mechanism ─────────────────────────
    utils_dir = backend / "utils"
    has_inprocess_ws = False
    has_redis_pubsub = False
    ws_file: str | None = None

    if utils_dir.exists():
        for f in utils_dir.glob("*.py"):
            text = read_text(f) or ""
            if re.search(
                r"dict\[.*WebSocket\]|connections\s*[:=]\s*\{"
                r"|active_connections|_connections\s*[:=]",
                text,
            ):
                has_inprocess_ws = True
                ws_file = rel(f, repo)
            if re.search(r"\.publish\(|pubsub|PubSub", text, re.I):
                has_redis_pubsub = True

    if has_inprocess_ws and not has_redis_pubsub:
        rep.add(
            YEL, "SC3", "backend", ws_file or "backend/utils/",
            "WebSocket broadcast uses in-process connection dict — "
            "only the holding replica can reach those sockets (§9.3). "
            "Won't scale past a single replica.",
            intended="move broadcast fan-out to Redis pub/sub so any "
                     "replica can publish to any connected socket",
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
These checks enforce the ZOZI backend circuit per documents/ARCHITECTURE_DIAGRAM.md
(three axes + seven laws). Arrows point DOWN only:

  modules/*/routers (thin) → domains/*/services → infrastructure/database
  jobs/* → domains/*/services → infrastructure
  providers/* ← services/* + jobs/* only
  rbac/* imported by modules/* + middleware/* only
  infrastructure/* imports nothing above it; kernel/* imports nothing above it

Rules enforced:
  - Imports may only flow DOWNWARD (higher layer → lower layer)
  - DB writes (session.add/commit/delete) only in domains/*/services/
  - Module routers stay THIN: auth ctx + require_feature(...) + one service call
  - Middleware may NOT import from domains/*/rbac/*/providers/*/modules/*
  - Providers may NOT import from modules/*/domains/*/rbac/*
  - Module routers may NOT contain business logic (only call a domain service)
  - Domain A may NOT import from Domain B except via ports.py/events.py/subscribers.py
  - Abolished flat layers (controllers/ routers/ services/ models/ db/ utils/ core/
    dependencies/) are violations, not targets.
"""




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
        if str(x).lower() not in exempt and str(x).lower() not in ("routers", "modules")
    }
    if not allowed_top:
        allowed_top = {
            "modules", "domains", "rbac", "infrastructure", "kernel",
            "providers", "jobs", "middleware", "events", "tasks", "api",
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
                        "APIRouter outside modules/*/routers/ -> endpoint mis-registered/shadowed",
                        intended="modules/{module}/routers/{domain}_router.py",
                        line=node.lineno,
                    )
                    break


def _classify_execute(node: ast.Call, source_lines: list[str] | None) -> str:
    """
    Inspect the arguments of session.execute(...) to determine
    whether it is a READ or WRITE operation.

    Returns:
        "write"  — INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE
        "read"   — SELECT/SHOW/DESCRIBE/EXPLAIN/WITH
        "unknown" — cannot determine (treat as advisory YEL, not RED W1)
    """
    if not node.args:
        return "unknown"

    # Collect the text of the first argument (the SQL statement)
    arg = node.args[0]
    sql_text = ""

    # Case 1: literal string  session.execute("INSERT ...")
    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        sql_text = arg.value

    # Case 2: text("INSERT ...")  or  text(sql_var)
    elif isinstance(arg, ast.Call):
        func_name = ""
        if isinstance(arg.func, ast.Name):
            func_name = arg.func.id
        elif isinstance(arg.func, ast.Attribute):
            func_name = arg.func.attr
        if func_name == "text" and arg.args:
            inner = arg.args[0]
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                sql_text = inner.value
            # Variable reference — try to resolve from source lines
            elif isinstance(inner, ast.Name) and source_lines:
                var_name = inner.id
                for line in source_lines[:arg.lineno]:
                    if var_name in line and ("=" in line or "INSERT" in line.upper()
                                              or "UPDATE" in line.upper()
                                              or "DELETE" in line.upper()
                                              or "SELECT" in line.upper()):
                        sql_text = line
                        break

    # Case 3: f-string  session.execute(f"UPDATE {table} ...")
    elif isinstance(arg, ast.JoinedStr):
        parts = []
        for value in arg.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                parts.append("{...}")
        sql_text = "".join(parts)

    # Case 4: variable reference  session.execute(sql_stmt)
    elif isinstance(arg, ast.Name) and source_lines:
        var_name = arg.id
        for line in source_lines[:arg.lineno]:
            if var_name in line and ("=" in line):
                sql_text = line
                break

    if not sql_text:
        return "unknown"

    sql_upper = sql_text.upper()
    if SQL_WRITE_RE.search(sql_upper):
        return "write"
    if SQL_READ_RE.search(sql_upper):
        return "read"
    return "unknown"


def check_layer_writes(repo: Path, rep: Report, eff: dict) -> None:
    """
    W1: Flag DB WRITE operations in module routers (modules/*/routers) and the
        abolished routers/controllers layers.
    Q1: Flag DB READ operations in module routers / abolished routers/controllers (advisory).

    ARCHITECTURE_DIAGRAM.md laws:
      - W1 = db.add / db.add_all / db.commit / db.flush / db.delete / db.merge
      - Q1 = db.query / db.scalar / db.first / db.all / db.get / db.refresh
      - session.execute() is classified by SQL content:
          INSERT/UPDATE/DELETE → W1 (write)
          SELECT/SHOW/WITH     → Q1 (read, advisory)
          unknown              → YEL advisory (not RED)

    Only domains/*/services/ may own DB transactions. Module routers stay thin
    (auth + require_feature + one service call).
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    write_verbs = eff.get("write_verbs", DEFAULT_WRITE_VERBS)
    read_verbs = eff.get("read_verbs", DEFAULT_READ_VERBS)

    # Layers that must NOT write to DB. The real router home is
    # modules/{actor}/routers/ (and modules/{actor}/auth/); backend/routers/
    # is an abolished path that no longer exists, so it is scanned only as a
    # fallback. Glob entries (containing "*") expand to every matching dir.
    forbidden_write_layers = {
        "routers": "backend/routers/",
        "controllers": "backend/controllers/",
        "middleware": "backend/middleware/",
        "dependencies": "backend/dependencies/",
        "module router": "backend/modules/*/routers/",
        "module auth": "backend/modules/*/auth/",
    }

    SESSION_NAMES = set(DB_SESSION_NAMES)

    # Resolve each entry to one or more existing directories to scan.
    _scan_targets: list[tuple[str, Path]] = []
    for layer_name, layer_prefix in forbidden_write_layers.items():
        if "*" in layer_prefix:
            matched = list(repo.glob(layer_prefix)) or list(
                backend.glob(layer_prefix.replace("backend/", "", 1))
            )
            for _d in matched:
                if _d.is_dir():
                    _scan_targets.append((layer_name, _d))
        else:
            layer_dir = backend / layer_name
            if not layer_dir.exists():
                layer_dir = repo / layer_prefix
            if layer_dir.exists():
                _scan_targets.append((layer_name, layer_dir))

    for layer_name, layer_dir in _scan_targets:

        for py_file in layer_dir.rglob("*.py"):
            if py_file.suffix.lower() != ".py":
                continue

            rel_f = rel(py_file, repo)
            if eff.get("ignore_dirs"):
                if any(x in rel_f for x in eff["ignore_dirs"]):
                    continue

            text = read_text(py_file)
            if not text:
                continue

            tree = parse_safe(py_file)
            if tree is None:
                continue

            source_lines = text.splitlines() if text else None

            # Track which variables hold session references
            session_vars: set[str] = set(SESSION_NAMES)
            # Detect: def endpoint(..., db: Session = Depends(get_db), ...)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                        arg_name = arg.arg
                        # Common session parameter names
                        if arg_name in DB_SESSION_NAMES:
                            session_vars.add(arg_name)
                        # Type annotation check: param: Session
                        elif arg.annotation:
                            ann_str = ast.dump(arg.annotation)
                            if "Session" in ann_str or "AsyncSession" in ann_str:
                                session_vars.add(arg_name)

            # Scan for method calls on session objects
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                if not isinstance(node.func, ast.Attribute):
                    continue

                method_name = node.func.attr
                # Get the object the method is called on
                obj = node.func.value
                obj_name = ""
                if isinstance(obj, ast.Name):
                    obj_name = obj.id
                elif isinstance(obj, ast.Attribute):
                    obj_name = obj.attr

                if obj_name not in session_vars:
                    continue

                line_no = node.lineno if hasattr(node, "lineno") else None

                # ── WRITE operations → RED W1 ──
                if method_name in write_verbs:
                    rep.add(
                        RED, "W1", layer_name, rel_f,
                        f"{layer_name} must not call session.{method_name}() "
                        f"— DB writes belong in services/",
                        intended="move this write into domains/<domain>/services/; "
                                 "module routers (modules/*/routers) stay thin — no DB writes",
                        line=line_no,
                    )

                # ── session.execute() → SQL-aware classification ──
                elif method_name == "execute":
                    classification = _classify_execute(node, source_lines)

                    if classification == "write":
                        rep.add(
                            RED, "W1", layer_name, rel_f,
                            f"{layer_name} must not call session.execute() "
                            f"with a WRITE statement (INSERT/UPDATE/DELETE) — "
                            f"DB writes belong in services/",
                            intended="move this write into domains/<domain>/services/; "
                                     "module routers (modules/*/routers) must not mutate data",
                            line=line_no,
                        )
                    elif classification == "read":
                        # SELECT via execute() is a read → Q1 advisory
                        rep.add(
                            YEL, "Q1", layer_name, rel_f,
                            f"{layer_name} reads via session.execute(SELECT ...) — "
                            f"delegate reads to services/",
                            intended="delegate DB reads to domains/<domain>/services/; "
                                     "module routers stay thin: call one domain-service method",
                            line=line_no,
                        )
                    else:
                        # Unknown → advisory YEL (not RED, not W1)
                        rep.add(
                            YEL, "Q1", layer_name, rel_f,
                            f"{layer_name} calls session.execute() with "
                            f"unclassifiable SQL — verify it is not a write",
                            intended="if this is a write, move it into "
                                     "domains/<domain>/services/; if a read, "
                                     "delegate to a domain-service method",
                            line=line_no,
                        )

                # ── READ operations → YEL Q1 (advisory) ──
                elif method_name in read_verbs:
                    # refresh/expire/expunge are session state ops, not queries
                    if method_name in {"refresh", "expire", "expunge"}:
                        continue  # These are not reads or writes — skip
                    rep.add(
                        YEL, "Q1", layer_name, rel_f,
                        f"{layer_name} reads via session.{method_name}() — "
                        f"delegate reads to services/",
                        intended="delegate DB reads to domains/<domain>/services/; "
                                 "module routers stay thin: call one domain-service method",
                        line=line_no,
                    )


def check_dependency_graph(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    edges = eff["forbidden_edges"]
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
                # controllers/ is an ABOLISHED layer (NS1). Any import from it is
                # abolished-layer code still reachable at runtime. Report it as a violation
                # of the ARCHITECTURE_DIAGRAM structure, never as a normal live-layer import.
                is_mis_housed = caller_layer in {
                    "services", "models", "providers", "events", "jobs",
                    "domains", "modules", "rbac", "kernel", "middleware",
                }
                if is_mis_housed:
                    key = ("W3", mod)
                    if key not in reported:
                        reported.add(key)
                        rep.add(
                            RED, "W3", "backend", caller_path,
                            f"imports abolished controller '{mod}' from {caller_layer} "
                            f"(controllers/ is abolished by ARCHITECTURE_DIAGRAM.md — see NS1). "
                            f"Controller logic must live in domains/<domain>/services/",
                            intended="delete the controllers/ import; re-home the logic "
                                     "into domains/<domain>/services/ (or a kernel/ primitive)",
                            line=line,
                        )
                    continue
            if (
                caller_layer == "controllers"
                and mod.startswith("controllers.")
                and mod != "controllers"
            ):
                key = ("W4", mod)
                if key not in reported:
                    reported.add(key)
                    rep.add(
                        YEL, "W4", "backend", caller_path,
                        f"abolished controllers/ layer imports another controller ('{mod}')",
                        intended="controllers/ is abolished (NS1); delete this file or "
                                 "re-home the shared logic into domains/<domain>/services/",
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
                            intended=f"layer contract: {caller_layer} may not depend on {pref}; "
                                     f"route via domains/<domain>/services/ (downward arrow only, Law 1)",
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
                intended="break the cycle by extracting shared logic into a lower layer "
                                     "(infrastructure/ or kernel/ primitive)",
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

    # FE11: frontend/shared/src/adminPermissions.ts must be deleted.
    # ARCHITECTURE_DIAGRAM.md mandates shared/src/permissions.ts (generated from
    # /rbac/catalog) as the single permission source for the shared package.
    # adminPermissions.ts is the old hand-written map — its presence proves the
    # frontend RBAC contract is not yet satisfied.
    _adm_perm = frontend / "shared" / "src" / "adminPermissions.ts"
    if _adm_perm.exists():
        rep.add(
            RED, "FE11", "frontend", rel(_adm_perm, repo),
            "frontend/shared/src/adminPermissions.ts must be DELETED. "
            "ARCHITECTURE_DIAGRAM.md mandates shared/src/permissions.ts (generated "
            "from backend /rbac/catalog) as the single shared permission source. "
            "adminPermissions.ts is the old hand-written map; keeping it "
            "duplicates the source of truth and allows drift.",
            intended="delete frontend/shared/src/adminPermissions.ts and rely "
                     "solely on the generated frontend/shared/src/permissions.ts",
            priority="P0",
        )

    # FE12: frontend/web_app/src/lib/rbac.ts must exist.
    # ARCHITECTURE_DIAGRAM.md mandates this file as the sole consumer of /rbac/catalog
    # in the web_app workspace, so UI gating and backend gating share one source.
    _rbac_ts = frontend / "web_app" / "src" / "lib" / "rbac.ts"
    if not _rbac_ts.exists():
        rep.add(
            RED, "FE12", "frontend", rel(_rbac_ts, repo),
            "frontend/web_app/src/lib/rbac.ts is MISSING. ARCHITECTURE_DIAGRAM.md "
            "mandates this file as the sole consumer of /rbac/catalog in the "
            "web_app workspace; without it UI gating cannot share one source "
            "with the backend.",
            intended="create frontend/web_app/src/lib/rbac.ts that fetches "
                     "/rbac/catalog once and exports helpers consumed by all "
                     "admin/customer/employee/supplier/logistics route guards",
            priority="P2",
        )

    # FE13: frontend/shared/src/permissions.ts must exist.
    # ARCHITECTURE_DIAGRAM.md mandates this file as the generated, shared permission
    # map consumed by all workspaces (web_app + mobile_app).
    _perm_ts = frontend / "shared" / "src" / "permissions.ts"
    if not _perm_ts.exists():
        rep.add(
            RED, "FE13", "frontend", rel(_perm_ts, repo),
            "frontend/shared/src/permissions.ts is MISSING. ARCHITECTURE_DIAGRAM.md "
            "mandates this file as the generated, shared permission map consumed "
            "by all workspaces (web_app + mobile_app); it must be produced from "
            "the backend /rbac/catalog response.",
            intended="generate frontend/shared/src/permissions.ts from the "
                     "backend /rbac/catalog endpoint so all workspaces import "
                     "permissions from one source",
            priority="P2",
        )


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
    app_layers = BACKEND_SCAN_LAYERS
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
        # down_revision may be None, a single id, or a tuple/Union of ids
        # (e.g. a merge migration). Collect every quoted revision id so merge
        # migrations resolve correctly; otherwise divergent heads look
        # un-merged -> false "multiple heads".
        dm = re.search(r"^down_revision(?:\s*:\s*[^=]+)?\s*=\s*(.*)$", t, re.M)
        if dm:
            val = dm.group(1).strip()
            if val and not val.lower().startswith("none"):
                for d in re.findall(r"['\"]([^'\"]+)['\"]", val):
                    downs.add(d)
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
# Authoritative target: documents/ARCHITECTURE_DIAGRAM.md.
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


def _pl_check_unknown_folders(repo: Path, rep: Report, eff: dict, known_domains: set[str]) -> None:
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
            if name in known_domains:
                continue
            if name in surfaces:
                continue
            canonical = _pl_normalize_domain(name)

            # ── FIX A1: if the folder IS a canonical domain key, skip ──
            if name in PLACEMENT_DOMAIN_KEYWORDS:
                continue

            # ── FIX A1: if canonical == name, it's already valid ──
            if canonical == name:
                continue

            if canonical and canonical != name and canonical in PLACEMENT_DOMAIN_KEYWORDS:
                rep.add(YEL, "DOM7", layer, rel(p, repo),
                        f"non-canonical domain folder '{name}/' should be '{canonical}/'",
                        intended=f"git mv backend/{layer}/{name} backend/{layer}/{canonical}",
                )
                continue
            if canonical in known_domains or canonical in PLACEMENT_DOMAIN_KEYWORDS:
                continue
            if name in stop:
                rep.add(YEL, "DOM7", layer, rel(p, repo),
                        f"generic folder '{name}/' is not a valid domain folder",
                        intended=(
                            "move its files into a real domain folder "
                            "(finance/orders/catalog/supplier/logistics/comms/...)"
                        ),
                )
                continue
            rep.add(YEL, "DOM7", layer, rel(p, repo),
                    f"unknown domain folder '{name}/'",
                    intended=(
                        f"if '{name}' is a real bounded context, add it to governance taxonomy; "
                        "otherwise move its files into the nearest canonical domain"
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

    # --- FE14: module actor 'employee' needs a web_app UI shell (diagram section 3) ---
    employee_module = repo / "backend" / "modules" / "employee"
    if employee_module.is_dir() and not (web_app / "employee").is_dir():
        rep.add(
            YEL, "FE14", "frontend",
            "frontend/web_app/src/app/employee/",
            "module actor 'employee' exists (backend/modules/employee/) but has no UI shell "
            "in web_app (diagram section 3 route tree) - employee/* route group missing.",
            intended="create frontend/web_app/src/app/employee/ route group",
            priority="P2",
        )


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
        "employee": {
            "required": ["dashboard", "profile"],
            "optional": [
                "attendance", "leave", "payslips", "tasks",
                "handover", "documents", "directory",
            ],
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
            {"services", "models", "providers", "events", "jobs"},
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
    """UNIFIED debt score across all four audit engines."""
    red = sum(f.count for f in rep.findings if f.sev == RED)
    yel = sum(f.count for f in rep.findings if f.sev == YEL)
    by = rep.counters
    score = red * 100 + yel * 15

    # ── Architecture rules ──
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
    score += by.get("SEC2", 0) * 80
    score += by.get("SEC3", 0) * 70
    score += by.get("SEC4", 0) * 60
    score += by.get("SEC11", 0) * 70
    score += by.get("SC1", 0) * 15
    score += by.get("SC2", 0) * 20
    score += by.get("SC3", 0) * 15
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

    # ── Database rules (DBA prefix) ──
    score += by.get("DBA02", 0) * 80
    score += by.get("DBA05", 0) * 80
    score += by.get("DBA10", 0) * 70
    score += by.get("DBA13", 0) * 60
    score += by.get("DBA16", 0) * 60
    score += by.get("DBA20", 0) * 80
    score += by.get("DBA26", 0) * 60
    score += by.get("DBA33", 0) * 60
    score += by.get("DBA03", 0) * 8
    score += by.get("DBA07", 0) * 10
    score += by.get("DBA08", 0) * 6
    score += by.get("DBA11", 0) * 3
    score += by.get("DBA12", 0) * 20
    score += by.get("DBA27", 0) * 70
    score += by.get("DBA29", 0) * 20
    score += by.get("DBA30", 0) * 12
    score += by.get("DBA31", 0) * 8
    score += by.get("DBA32", 0) * 10
    score += by.get("DBA35", 0) * 15

    # ── Design rules ──
    score += by.get("DS02", 0) * 30
    score += by.get("DS03", 0) * 6
    score += by.get("DS05", 0) * 8
    score += by.get("DS06", 0) * 10
    score += by.get("DS10", 0) * 25
    score += by.get("DS12", 0) * 60
    score += by.get("DS13", 0) * 18
    score += by.get("DS15", 0) * 15
    score += by.get("DS01", 0) * 4
    score += by.get("DS04", 0) * 12
    score += by.get("DS07", 0) * 8
    score += by.get("DS08", 0) * 4
    score += by.get("DS09", 0) * 8
    score += by.get("DS11", 0) * 8
    score += by.get("DS14", 0) * 12
    score += by.get("DS16", 0) * 5
    score += by.get("DS17", 0) * 4
    score += by.get("DS18", 0) * 5

    # ── Health rules ──
    score += by.get("HL402", 0) * 40
    score += by.get("SEC101", 0) * 80
    score += by.get("SEC105", 0) * 80
    score += by.get("SC102", 0) * 30
    score += by.get("HL601", 0) * 20
    score += by.get("HL602", 0) * 15
    score += by.get("HL101", 0) * 8
    score += by.get("HL102", 0) * 6
    score += by.get("HL501", 0) * 10
    score += by.get("HL502", 0) * 5
    score += by.get("HL201", 0) * 3
    score += by.get("HL301", 0) * 4
    score += by.get("HL302", 0) * 4
    score += by.get("HL401", 0) * 10
    score += by.get("HL901", 0) * 2
    score += by.get("HL902", 0) * 2
    score += by.get("HL203", 0) * 3
    score += by.get("HL204", 0) * 10
    score += by.get("PG101", 0) * 10
    score += by.get("PG102", 0) * 12
    score += by.get("PG103", 0) * 12
    score += by.get("PG201", 0) * 8
    score += by.get("SC101", 0) * 12
    score += by.get("SC501", 0) * 12
    score += by.get("API101", 0) * 5
    score += by.get("OB101", 0) * 6
    score += by.get("OB102", 0) * 6
    score += by.get("MR101", 0) * 4
    score += by.get("MR104", 0) * 8
    score += by.get("FEH101", 0) * 6
    score += by.get("FEH201", 0) * 3
    score += by.get("FEH301", 0) * 8
    score += by.get("FEH401", 0) * 4
    score += by.get("FEH402", 0) * 4
    score += by.get("FEH501", 0) * 8
    score += by.get("FEH502", 0) * 5
    score += by.get("FEH503", 0) * 4
    score += by.get("FEH504", 0) * 4
    score += by.get("FEH601", 0) * 4
    score += by.get("FEH701", 0) * 6
    score += by.get("FEH801", 0) * 6
    score += by.get("FEH802", 0) * 4
    score += by.get("DP101", 0) * 10
    score += by.get("DP102", 0) * 5
    score += by.get("DP103", 0) * 10
    score += by.get("DP104", 0) * 8
    score += by.get("DP105", 0) * 5
    score += by.get("PL101", 0) * 8

    score += by.get("HC1", 0) * 8
    score += by.get("PRV1", 0) * 10
    score += by.get("PRV2", 0) * 15
    return int(score)


def collect_info(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    backend = repo / "backend"

    def n(sub: str) -> int:
        d = backend / sub
        if not d.exists():
            return 0
        return sum(1 for x in d.rglob("*.py") if x.is_file())

    new_layers = ["modules", "domains", "rbac", "infrastructure", "kernel",
                  "providers", "jobs", "middleware"]
    abolished = ["controllers", "routers", "services", "models", "db", "utils", "core", "dependencies"]
    new_counts = {l: n(l) for l in new_layers}
    abolished_counts = {l: n(l) for l in abolished}
    new_summary = "  ".join(f"{l}={new_counts[l]}" for l in new_layers)
    abolished_present = [l for l in abolished if abolished_counts[l] > 0]
    abolished_summary = (
        "  abolished flat layers still present: " +
        "  ".join(f"{l}={abolished_counts[l]}" for l in abolished_present)
        if abolished_present else "  no abolished flat root layers present"
    )
    rep.add(
        GRN, "I1", "repo", rel(repo, repo),
        f"ARCHITECTURE_DIAGRAM layers -> {new_summary}; {abolished_summary}.",
    )
    src = rules_source_label(eff)
    rep.add(GRN, "I2", "repo", "documents/scope/", f"rules loaded from: {src}")
    rep.add(
        GRN, "I3", "repo", "backend/",
        f"module graph: modules={len(graph.modules)}, "
        f"edges={sum(len(v) for v in graph.edges.values())}, "
        f"classes={len(graph.classes)}",
    )


def build_summary(repo: Path, rep: Report,graph: ModuleGraph, debt_score: int, frontend_metrics: dict, reg: FeatureRegistry,) -> dict:

    n_red = sum(f.count for f in rep.findings if f.sev == RED)
    n_yel = sum(f.count for f in rep.findings if f.sev == YEL)
    n_grn = sum(f.count for f in rep.findings if f.sev == GRN)

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
            "Q1": (f"{count} DB read(s) via .query() in this file; "
                   "delegate reads to a service"),
            "W1": (f"{count} session write(s) in this file; "
                   "move writes into domains/<domain>/services/"),
            "W2": (f"{count} misnamed service-helper write location(s); "
                   "relocate logic to services/"),
            "PERF2": (f"{count} possible DB query inside loop (N+1 risk); "
                      "batch queries / use joins / preload relationships"),
            "QUAL1": (f"{count} weak exception handling location(s); "
                      "log or re-raise instead of swallowing exceptions"),
            "QUAL4": (f"{count} print/debug output location(s); "
                      "use structured logging instead of print()"),
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
        # ── FIX B1: preserve count and priority from original findings ──
        kept.append(
            Finding(
                sev=sev, code=code, domain=domain, path=path,
                message=message, intended=intended, line=None,
                priority=items[0].priority if items else "P3",
                count=count,
            )
        )
    rep.findings = kept
    rep.counters = defaultdict(int)
    for f in rep.findings:
        rep.counters[f.code] += f.count

# ============================================================================
# SECTION 18: RENDERING
# ============================================================================

def generate_ai_placement_contract() -> str:
    """
    Generate a prescriptive placement contract for AI agents.

    This tells AI where to put NEW files BEFORE it creates them, and is the
    primary compliance guard: it encodes documents/ARCHITECTURE_DIAGRAM.md (three
    orthogonal axes + seven laws). The abolished flat root layers
    (controllers/, routers/, services/, models/, db/, utils/, core/,
    dependencies/) are listed ONLY as forbidden/unlawful targets, never as
    canonical homes. An AI that emits any of those flat layers is in violation.
    """
    lines = [
        "## AI File Placement Contract (ZOZI ARCHITECTURE_DIAGRAM.md)",
        "",
        "> **Rule for AI:** Before creating or moving ANY backend file, use this contract.",
        "> The three axes are: **Module = `modules/` (who)**, **Domain = `domains/` (what)**,",
        "> **Feature = `rbac/` + `domains/*/features.py` (may)**. Platform = `infrastructure/`,",
        "> shared kernel = `kernel/`, adapters = `providers/`, workers = `jobs/`,",
        "> HTTP pipeline = `middleware/`.",
        "",
        "### Canonical layer rules (ARCHITECTURE_DIAGRAM structure)",
        "",
        "| Axis / Layer | Structure | Correct examples |",
        "|---|---|---|",
        "| `backend/modules/{module}/` (AXIS 1) | auth/ + routers/ per actor | "
        "`modules/admin/auth/`, `modules/admin/routers/finance_ledger_router.py`, "
        "`modules/customer/routers/checkout_router.py` |",
        "| `backend/modules/{module}/routers/` | **thin**: auth ctx + `require_feature(...)` + one domain-service call | "
        "`modules/admin/routers/finance_reports_router.py`, "
        "`modules/supplier/routers/payouts_router.py` |",
        "| `backend/domains/{domain}/` (AXIS 2) | services/ models/ schemas/ policies/ events.py subscribers.py features.py | "
        "`domains/finance/services/ledger_service.py`, "
        "`domains/finance/models/ledger.py` |",
        "| `backend/domains/{domain}/services/` | orchestration + transactions (NO HTTP) | "
        "`domains/orders/services/checkout_service.py` |",
        "| `backend/domains/{domain}/models/` | ORM only; flat per domain; `__table_args__={'schema': '<domain>'}` | "
        "`domains/catalog/models/products.py` |",
        "| `backend/domains/{domain}/features.py` | AXIS 3 seed: permission atoms | "
        "`domains/finance/features.py` (finance.ledger, finance.reporting, ...) |",
        "| `backend/rbac/` (AXIS 3) | catalog.py roles.py resolution.py dependencies.py service.py | "
        "`rbac/catalog.py`, `rbac/dependencies.py` |",
        "| `backend/infrastructure/` | platform: database redis storage messaging observability security utils | "
        "`infrastructure/database/database.py`, `kernel/money.py` |",
        "| `backend/kernel/` | business primitives: money numbering country period | "
        "`kernel/money.py`, `kernel/numbering.py` |",
        "| `backend/providers/` | 3rd-party/AI adapters; called ONLY by services/ and jobs/ | "
        "`providers/ai/image_analysis_provider.py` |",
        "| `backend/jobs/` | background workers/consumers (off-request only) | "
        "`jobs/finance/payout_sweep.py` |",
        "| `backend/middleware/` | flat HTTP pipeline; orchestrator.py orders it | "
        "`middleware/orchestrator.py`, `middleware/rate_limit.py` |",
        "",
        "### The seven laws (any violation = report it)",
        "",
        "1. Arrows point DOWN only: `modules → domains → infrastructure`; `jobs → domains → infrastructure`; "
        "`providers ← services/jobs`; `middleware → infrastructure`; `domains → kernel → (nothing)`. "
        "Domains NEVER import modules; `rbac` is imported by modules/middleware only (domains enforce policies, not permissions).",
        "2. Module routers stay THIN: auth ctx + `require_feature(...)` + one domain-service call. No DB writes, no business rules. "
        "Module routers NEVER import `providers/` directly (the domain service calls the provider).",
        "3. Cross-domain WRITES only via `events.py`/`subscribers.py`. Cross-domain READS only via the publishing "
        "domain's `ports.py` (or `read_models/`); direct `from domains.X.(services|models|repositories|schemas|policies)` "
        "outside `domains/X` is a build failure. `DOMAIN_ALLOWLIST.yaml` tracks the temporary exceptions (must shrink).",
        "4. Features are single-sourced in `domains/*/features.py`; aggregated by `rbac/catalog.py`. "
        "Any `require_feature(\"...\")` literal not in the catalog is a build failure.",
        "5. Country is the orthogonal scope axis (RLS + `country_staff_assignments`); independent of the feature check.",
        "6. Schema discipline: every table lives in a Postgres schema (`__table_args__={'schema': '<domain>'}`); "
        "Alembic is the only schema source; snake_case/plural naming lints apply.",
        "7. Allowlist rule (Law 7): `DOMAIN_ALLOWLIST.yaml` lists the temporary cross-domain imports still permitted and may only shrink.",
        "",
        "### ABOLISHED flat root layers — FORBIDDEN (do NOT create; these are violations)",
        "",
        "The following root layers are abolished (per ARCHITECTURE_DIAGRAM.md). Creating or leaving a file under any of them "
        "is a RED violation. There is no prescribed re-export/`_legacy` shim layer; abolished code must be "
        "split into the canonical locations and the originals deleted.",
        "",
        "```text",
        "backend/controllers/      # ABOLISHED — split into modules/*/routers/ + domains/*/services/",
        "backend/routers/          # ABOLISHED flat — re-home per actor under modules/*/routers/",
        "backend/services/         # ABOLISHED flat — move into domains/*/services/",
        "backend/models/           # ABOLISHED flat — move into domains/*/models/",
        "backend/db/               # ABOLISHED — move into infrastructure/database/",
        "backend/utils/            # ABOLISHED flat — split into infrastructure/utils/ + kernel/",
        "backend/core/             # ABOLISHED — move into domains/*/services/ or infrastructure/",
        "backend/dependencies/     # ABOLISHED — move into domains/*/ or infrastructure/",
        "```",
        "",
        "### Domain keyword routing (→ the NEW home is a domain folder)",
        "",
        "| Domain | Put business logic here (AXIS 2) | Keywords |",
        "|---|---|---|",
    ]
    for domain in CANONICAL_DOMAINS:
        aliases = sorted(CANONICAL_DOMAIN_ALIASES.get(domain, set()))
        examples = ", ".join(aliases[:14])
        lines.append(
            f"| `{domain}` | `backend/domains/{domain}/services/`, "
            f"`backend/domains/{domain}/models/`, `backend/domains/{domain}/features.py` "
            f"| {examples} |"
        )
    lines.extend([
        "",
        "### If domain is unclear",
        "",
        "If a file does not clearly belong to a domain, create the domain skeleton first:",
        "",
        "```text",
        "backend/domains/<new_domain>/services/  models/  schemas/  policies/  events.py  subscribers.py  features.py",
        "```",
        "",
        "Then add the surface where needed under `backend/modules/<module>/routers/`. "
        "Never drop it into an abolished flat root layer.",
        "",
    ])
    return "\n".join(lines)


def ordered_report_domains(rep: Report) -> list[str]:
    """Return all domains present in findings, priority first."""
    priority = ["repo", "backend", "database", "frontend", "security", "docs", "infra"]
    present = {f.domain for f in rep.findings if f.domain}
    ordered = [d for d in priority if d in present]
    extra = sorted(d for d in present if d not in priority)
    return ordered + extra


def render_stdout(repo: Path, rep: Report, summary: dict) -> int:
    """Print audit results to stdout. Returns RED count."""
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary.get("debt_score", 0)

    print("=" * 76)
    print("  ZOZI SYSTEM ARCHITECTURE GOVERNANCE AUDIT v5.0")
    print("  structure · layers · dependency graph · cycles · ownership · metrics")
    print("  dynamic imports · policy validation · frontend scaling · auto-discovery")
    print("=" * 76)
    print(f"  repo: {repo}")
    print(f"  [RED] VIOLATIONS : {n_red}    "
          f"[YEL] ADVISORIES : {n_yel}    "
          f"[GRN] INFO : {n_grn}")
    print(f"  ARCHITECTURE DEBT SCORE: {debt}")
    print("  by rule: " + ", ".join(
        f"{k}={v}" for k, v in sorted(rep.counters.items())))

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
    print(f"  modules: {summary['modules']}   "
          f"edges: {summary['edges']}   "
          f"classes: {summary['classes']}")
    if summary.get("layer_counts"):
        print("  layer counts: " + ", ".join(
            f"{k}={v}" for k, v in sorted(summary["layer_counts"].items())))
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
            print(f"    {ws}: source_files={m.get('source_files', 0)}, "
                  f"dirs={m.get('dirs', 0)}")
    if summary.get("auto_discovery"):
        ad = summary["auto_discovery"]
        print("\nAuto-discovery:")
        print(f"    domains={ad.get('domains', 0)}")
        print(f"    features={ad.get('features', 0)}")
        print(f"    frontend_features={ad.get('frontend_features', 0)}")
        print(f"    backend_top_dirs={ad.get('backend_top_dirs', 0)}")
        print(f"    learned_domain_edges={ad.get('domain_edges', 0)}")

    # ── Health / Database / Design summaries ──
    if summary.get("health"):
        hl = summary["health"]
        print(f"\n  HEALTH SCORE: {hl.get('health_score', '?')}/100 "
              f"({hl.get('grade', '?')})")
    if summary.get("database"):
        db = summary["database"]
        print(f"  DATABASE: {db.get('models', 0)} models, "
              f"{db.get('tables', 0)} tables, "
              f"heads: {', '.join(db.get('migration_heads', [])) or 'none'}")
    if summary.get("design"):
        ds = summary["design"]
        print(f"  DESIGN: {ds.get('palette_tokens', 0)} tokens, "
              f"coverage: {ds.get('coverage', 0):.1f}%")

    print("\n" + "=" * 76)
    return n_red


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


def check_dead_symbols(repo: Path, rep: Report, eff: dict,
                       index: SymbolIndex, graph: ModuleGraph) -> None:
    """
    SYM1: Detect symbols defined but never used anywhere.
    Only checks public functions/classes in application layers.
    FIX A2: Honor __all__ re-exports — symbols re-exported via __all__
    in a package __init__.py are NOT dead.
    """
    app_layers = BACKEND_SCAN_LAYERS
    exempt_names = {"init", "main", "setup", "configure"}

    # ── FIX A2: Build set of symbols re-exported via __all__ ──
    reexported: set[str] = set()
    backend = repo / "backend"
    if backend.exists():
        for init_file in backend.rglob("__init__.py"):
            text = read_text(init_file)
            if not text:
                continue
            # Parse __all__ = [...]
            try:
                tree = ast.parse(text)
            except (SyntaxError, ValueError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__":
                            if isinstance(node.value, (ast.List, ast.Tuple)):
                                for elt in node.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                        reexported.add(elt.value)

    reported = 0
    for name, symbols in sorted(index.symbols.items()):
        if name in exempt_names or name.startswith("_"):
            continue

        # ── FIX A2: Skip symbols re-exported via __all__ ──
        if name in reexported:
            continue

        for sym in symbols:
            layer = layer_of_module(sym.module)
            if layer not in app_layers:
                continue
            usages = index.symbol_usages.get(name, [])
            external_usages = [
                (m, l) for m, l in usages if m != sym.module
            ]
            if not external_usages and sym.kind in ("function", "class"):
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
        "middleware": 1,
        # ARCHITECTURE_DIAGRAM.md canonical axes (arrows point DOWN only)
        "rbac": 1,
        "modules": 2,
        "domains": 4,
        "infrastructure": 8, "kernel": 8,
        "providers": 5,
        "events": 4, "jobs": 4,
    }

    # ── CG2 Exemption Configuration ──
    # These modules legitimately call models/db for cross-cutting concerns.
    # Configurable via YAML: circuit_exempt_modules
    DEFAULT_CG2_EXEMPT_MODULES: set[str] = set()

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

    # Forbidden cross-layer calls — ARCHITECTURE_DIAGRAM.md seven-law circuit only
    # (axes point DOWN: modules→domains→infrastructure, jobs→domains→
    #  infrastructure, providers←services/jobs, middleware→infrastructure,
    #  rbac/kernel/infrastructure are leaves). Abolished flat layers
    # (controllers/routers/services/models/db/utils/core/dependencies) are
    # reported by NS1-NS4/NS23-NS26, never treated as circuit nodes here.
    forbidden_calls: set[tuple[str, str]] = {
        # ── ARCHITECTURE_DIAGRAM.md seven-law forbidden calls (axes point DOWN only) ──
        # KEPT IN SYNC WITH ARCHITECTURE_DIAGRAM_CIRCUIT_ALLOWED_IMPORTS: any edge the
        # circuit explicitly ALLOWS must NEVER appear here, or correct code is flagged
        # RED. Removed (allowed by circuit): rbac→domains/infrastructure/kernel,
        # jobs→domains/infrastructure/kernel/providers, providers→infrastructure/kernel,
        # kernel→infrastructure, middleware→kernel, modules→infrastructure.
        ("domains", "modules"),
        ("modules", "providers"),
        ("modules", "kernel"),
        ("modules", "jobs"),
        ("rbac", "modules"),
        ("rbac", "providers"),
        ("rbac", "jobs"),
        ("rbac", "middleware"),
        ("infrastructure", "modules"),
        ("infrastructure", "domains"),
        ("infrastructure", "rbac"),
        ("infrastructure", "providers"),
        ("infrastructure", "kernel"),
        ("infrastructure", "jobs"),
        ("infrastructure", "middleware"),
        ("kernel", "modules"),
        ("kernel", "domains"),
        ("kernel", "rbac"),
        ("kernel", "providers"),
        ("kernel", "jobs"),
        ("kernel", "middleware"),
        ("providers", "modules"),
        ("providers", "rbac"),
        ("providers", "middleware"),
        ("jobs", "modules"),
        ("jobs", "rbac"),
        ("jobs", "middleware"),
        ("middleware", "modules"),
        ("middleware", "domains"),
        ("middleware", "providers"),
        ("middleware", "jobs"),
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

        # Exempt layers (tests, scripts, etc.) are outside the circuit;
        # they may call any lower layer without triggering CG2.
        graph_exempt = eff.get("graph_exempt_layers", DEFAULT_GRAPH_EXEMPT_LAYERS)
        if caller_layer in graph_exempt:
            continue

        caller_order = layer_order.get(caller_layer, 99)
        callee_order = layer_order.get(callee_layer, 99)

        # ── Exemption check: skip audit/logging/security utilities ──
        caller_module_lower = edge.caller_module.lower()
        if edge.caller_module in DEFAULT_CG2_EXEMPT_MODULES:
            continue
        if any(pattern in caller_module_lower for pattern in CG2_EXEMPT_PATTERNS):
            continue

        # Upward call violation (calling a higher layer). The ARCHITECTURE_DIAGRAM structure's leaves
        # are infrastructure/ and kernel/ (order 8) — they are never a callee with a
        # lower order, so this guard is a safety net for any other leaf-like layer.
        if callee_order < caller_order and callee_layer not in ("infrastructure", "kernel"):
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
            intended="break the cycle; extract shared logic to a lower layer "
                     "(infrastructure/ or kernel/ primitive)",
            line=None,
        )


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

    # API1: Public symbols without documentation (potential instability).
    # ARCHITECTURE_DIAGRAM.md: business surfaces live under domains/<domain>/ and
    # module routers under modules/<actor>/; the abolished flat layers
    # (services/controllers) are reported by NS1-NS4, never scanned here.
    ARCH_API1_LAYERS = {
        "domains", "modules", "providers", "rbac", "kernel",
        "infrastructure", "jobs", "middleware", "events",
    }
    for name, symbols in sorted(index.symbols.items()):
        for sym in symbols:
            if (sym.is_public and sym.kind in ("function", "class")
                    and not sym.docstring
                    and not sym.name.startswith("test_")):
                layer = layer_of_module(sym.module)
                if layer in ARCH_API1_LAYERS:
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
        "employee": "oversight",
        "admin": "oversight",
    },
    "finance": {
        "customer": "one_way_in",
        "supplier": "one_way_out",
        "logistics": "one_way_out",
        "employee": "oversight",
        "admin": "tree",
    },
    "catalog": {
        "supplier": "one_way_in",
        "customer": "one_way_out",
        "employee": "oversight",
        "admin": "oversight",
    },
    "comms": {
        "customer": "multi_way",
        "supplier": "multi_way",
        "employee": "multi_way",
        "admin": "multi_way",
        "logistics": "multi_way",
    },
    "communication": {
        "customer": "multi_way",
        "supplier": "multi_way",
        "employee": "multi_way",
        "admin": "multi_way",
    },
    "logistics": {
        "logistics": "forward",
        "supplier": "forward",
        "customer": "forward",
        "employee": "oversight",
        "admin": "oversight",
    },
    "supplier": {
        "supplier": "forward",
        "employee": "oversight",
        "admin": "oversight",
    },
    "hr": {
        "employee": "forward",
        "admin": "tree",
    },
    "security": {
        "employee": "oversight",
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

    app_layers = BACKEND_SCAN_LAYERS
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

def check_split_file_candidates(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    """
    CA2: Detect files with strong signals for multiple domains.
    FIX A4: Raise threshold to 3+ domains AND require each domain
    to have 3+ signals. Exempt orchestration services.
    """
    backend = repo / "backend"
    if not backend.exists():
        return
    app_layers = BACKEND_SCAN_LAYERS
    aliases = PLACEMENT_ALIAS_TO_DOMAIN
    reported = 0

    # Orchestration service names that legitimately span domains
    ORCHESTRATION_EXEMPT = {
        "cash_management", "payment_orchestrator", "order_orchestrator",
        "async_workers", "config", "registry", "base", "common",
    }

    for module, f in graph.modules.items():
        layer = layer_of_module(module)
        if layer not in app_layers:
            continue

        # ── FIX A4: Skip orchestration services ──
        stem = f.stem.lower()
        if any(ex in stem for ex in ORCHESTRATION_EXEMPT):
            continue

        tree = parse_safe(f)
        if tree is None:
            continue
        text = read_text(f)
        if not text:
            continue

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

        # ── FIX A4: Require 3+ domains, each with 3+ signals ──
        significant_domains = {
            d: count for d, count in domain_signals.items()
            if count >= 3
        }
        if len(significant_domains) >= 3:
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
                f"{domains_str} — consider splitting if sub-domains are independently reusable",
                intended="split only if a sub-domain is independently reusable; "
                         "multi-domain orchestration services are normal",
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
    "employee": {
        "approve_supplier", "configure_commission", "configure_platform",
        "manage_roles", "manage_permissions", "ban_user", "moderate_all",
        "view_ledger", "override",
    },
}


def check_surface_operations(repo: Path, rep: Report, eff: dict,
                             graph: ModuleGraph) -> None:
    """
    CA3: Detect surface-inappropriate operations.

    ARCHITECTURE_DIAGRAM.md: thin routers live under modules/<actor>/routers/ (Law 2).
    The abolished flat layers (routers/ controllers/) are reported by NS1/NS2
    and are never scanned here.
    """
    backend = repo / "backend"
    if not backend.exists():
        return

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    reported = 0

    modules_dir = backend / "modules"
    if not modules_dir.is_dir():
        return

    for actor in modules_dir.iterdir():
        if not actor.is_dir():
            continue
        routers_dir = actor / "routers"
        if not routers_dir.is_dir():
            continue

        for f in iter_text_files(routers_dir, eff):
            if f.suffix.lower() != ".py":
                continue

            tree = parse_safe(f)
            if tree is None:
                continue

            # Determine surface
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
                            RED, "CA3", "modules/routers",
                            rel(f, repo),
                            f"surface-inappropriate operation '{node.name}' "
                            f"in {surface} module router "
                            f"(forbidden: {', '.join(sorted(violations))})",
                            intended=f"move '{node.name}' to the appropriate "
                                     f"surface (likely admin) or extract to "
                                     f"a domains/<domain>/service",
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

                if module_name.startswith(("routers.", "controllers.",
                                           "services.", "models.", "db.", "utils.", "core.", "dependencies.")):
                    rep.add(
                        RED, "MW3", "backend",
                        rel(f, repo),
                        f"middleware imports from '{module_name}' "
                        f"(circuit violation)",
                        intended="middleware must import only infrastructure/ "
                                 "(+ kernel); never application layers "
                                 "(modules/ domains/ rbac) — use dependency injection or events",
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
    "employee": ["/employee", "/api/employee", "/api/v1/employee"],
    "logistics": ["/logistics", "/api/logistics", "/api/v1/logistics"],
    "internal": ["/internal", "/api/internal", "/health", "/webhooks"],
    "external": ["/external", "/webhooks", "/callbacks"],
}


def check_api_shape(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
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

        # AS2: OpenAPI tag alignment with router surface/domain.
        # A tag that maps to a known domain must match the router's surface;
        # a mismatch means the route is mis-tagged (or in the wrong surface).
        tag_matches = AUTO_ROUTE_TAGS_RE.findall(text)
        for tag_str in tag_matches:
            tags = re.findall(r"['\"]([^'\"]+)['\"]", tag_str)
            for tag in tags:
                tag_domain = aliases.get(tag.lower())
                if tag_domain and surface and tag_domain != surface:
                    rep.add(
                        YEL, "AS2", "routers",
                        rel(f, repo),
                        f"OpenAPI tag '{tag}' maps to domain '{tag_domain}' "
                        f"but router belongs to surface '{surface}'",
                        intended=f"align OpenAPI tags with the '{surface}' domain "
                                 f"(or move the route to the correct surface)",
                    )
                    reported += 1

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
    re.compile(r"f['\"].*SELECT.*\{", re.I),
    re.compile(r"f['\"].*INSERT.*\{", re.I),
    re.compile(r"f['\"].*UPDATE.*\{", re.I),
    re.compile(r"f['\"].*DELETE.*\{", re.I),
    re.compile(r"\.format\(.*(?:SELECT|INSERT|UPDATE|DELETE)", re.I),
    re.compile(r"%\s*(?:SELECT|INSERT|UPDATE|DELETE).*%\s*\(", re.I),
    re.compile(r"execute\(\s*f['\"]", re.I),
    re.compile(r"execute\(\s*['\"].*['\"]\s*\+", re.I),
]

# Patterns that indicate SAFE parameterized SQL
SEC_PARAMETERIZED_RE = re.compile(
    r"(:[\w]+|:\s*\(|\bparams\b|\bbindparams\b|\bparameters\b"
    r"|\btext\(\s*['\"].*:[\w]+.*['\"].*,\s*\{)",
    re.I,
)
# Allowlisted identifiers that are safe to interpolate (table/column names from constants)
SEC_SAFE_INTERPOLATION_RE = re.compile(
    r"\{(?:table_name|schema|column|field|index_name|constraint|order_by|sort_col)\}",
    re.I,
)

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


def check_advanced_security(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    """SEC5-SEC10: Advanced security checks (CORRECTED: parameterization-aware)."""
    backend = repo / "backend"
    if not backend.exists():
        return

    # SEC9: CSRF protection must be wired for state-changing endpoints.
    # The app relies on a global CSRFMiddleware (double-submit cookie); if it
    # is not registered in the middleware pipeline, every POST/PUT/PATCH/DELETE
    # endpoint is unprotected (webhook paths are the only intentional opt-out).
    mw_dir = backend / "middleware"
    csrf_wired = False
    if mw_dir.exists():
        for _p in mw_dir.rglob("*.py"):
            if "venv" in _p.parts:
                continue
            if "CSRFMiddleware" in read_text(_p):
                csrf_wired = True
                break
    if not csrf_wired:
        rep.add(
            RED, "SEC9", "security", "backend/middleware",
            "CSRF protection is not wired into the middleware pipeline; "
            "state-changing endpoints (POST/PUT/PATCH/DELETE) are unprotected",
            intended="register CSRFMiddleware (double-submit cookie) in the "
                     "middleware orchestrator for all non-webhook state-changing routes",
        )

    reported = 0
    for module, f in graph.modules.items():
        text = read_text(f)
        if not text:
            continue
        layer = layer_of_module(module)
        rel_path = rel(f, repo)

        # SEC5: SQL injection — with parameterization exemption
        for rx in SEC_SQL_INJECTION_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    # Skip comments
                    stripped = line.strip()
                    if stripped.startswith("#"):
                        continue
                    # Check if this is parameterized SQL (safe)
                    context_start = max(0, i - 3)
                    context_end = min(len(text.splitlines()), i + 3)
                    context = "\n".join(text.splitlines()[context_start:context_end])
                    if SEC_PARAMETERIZED_RE.search(context):
                        # Parameterized query — downgrade to advisory
                        rep.add(YEL, "SEC5", layer, rel_path,
                                "SQL with string interpolation detected, but bound "
                                "parameters present — verify no user input is interpolated",
                                intended="confirm all interpolated values are constants "
                                         "or allowlisted identifiers, not user input",
                                line=i)
                    elif SEC_SAFE_INTERPOLATION_RE.search(line):
                        # Only safe identifiers interpolated — informational
                        rep.add(YEL, "SEC5", layer, rel_path,
                                "SQL with identifier interpolation (table/column names) — "
                                "verify identifiers come from constants",
                                intended="ensure interpolated identifiers are from "
                                         "allowlisted constants, not user input",
                                line=i)
                    else:
                        rep.add(RED, "SEC5", layer, rel_path,
                                "potential SQL injection: string interpolation "
                                "in SQL query without visible parameterization",
                                intended="use parameterized queries or SQLAlchemy ORM; "
                                         "never interpolate user input into SQL",
                                line=i)
                    reported += 1
                    break

        # SEC6: SSRF
        for rx in SEC_SSRF_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    if line.strip().startswith("#"):
                        continue
                    rep.add(YEL, "SEC6", layer, rel_path,
                            "potential SSRF: URL from variable used in HTTP request",
                            intended="validate/whitelist URLs before making requests",
                            line=i)
                    reported += 1
                    break

        # SEC7: Path traversal
        for rx in SEC_PATH_TRAVERSAL_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    if line.strip().startswith("#"):
                        continue
                    rep.add(YEL, "SEC7", layer, rel_path,
                            "potential path traversal: user-controlled path component",
                            intended="sanitize file paths; use allowlist",
                            line=i)
                    reported += 1
                    break

        # SEC8: Insecure JWT
        for rx in SEC_JWT_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    if line.strip().startswith("#"):
                        continue
                    rep.add(RED, "SEC8", layer, rel_path,
                            "insecure JWT/token handling detected",
                            intended="always verify signatures; never use algorithm='none'",
                            line=i)
                    reported += 1
                    break

        # SEC10: Insecure CORS — wildcard origin (exploitable with credentials)
        for i, line in enumerate(text.splitlines(), 1):
            if "allow_origins" in line.lower() and '"*"' in line:
                rep.add(
                    RED, "SEC10", layer, rel_path,
                    "insecure CORS: allow_origins contains wildcard '*' "
                    "(combined with allow_credentials=True this is exploitable)",
                    intended="use an explicit allowlist from CORS_ORIGINS env; "
                             "never use '*' when allow_credentials is enabled",
                    line=i,
                )
                reported += 1
                break

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

    # ARCHITECTURE_DIAGRAM.md: thin module routers live under modules/<actor>/routers/
    # and DB-owning logic lives under domains/<domain>/services/. The abolished
    # flat layers (routers/controllers/services) are reported by NS1-NS4 and
    # are never scanned here.
    ARCH_PERF_SCAN_LAYERS = {
        "modules", "domains", "providers", "jobs", "middleware",
        "rbac", "kernel", "infrastructure", "events",
    }

    for module, f in graph.modules.items():
        layer = layer_of_module(module)
        if layer not in ARCH_PERF_SCAN_LAYERS:
            continue

        text = read_text(f)
        if not text:
            continue

        tree = parse_safe(f)
        if tree is None:
            continue

        rel_path = rel(f, repo)

        # PERF3: Missing pagination on list endpoints (module routers are thin;
        # any list endpoint must be cursor/limit bounded).
        if layer == "modules":
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

        # PERF4: Unbounded query (no limit) — domain services own DB access.
        if layer == "domains":
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

        # PERF5: Large transaction risk — domain services own transactions.
        if layer == "domains":
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

    # FE10: Raw fetch()/XMLHttpRequest bypasses the typed API client.
    # Architecture (§10.4) mandates a single typed client in src/lib/api/* as the
    # only network entrypoint for *client* code; components/hooks/pages must not
    # call the global fetch() directly (auth, errors and caching would be
    # decentralized). The client itself (src/lib/api/**) and Next.js server
    # route handlers (src/app/api/**/route.ts, which act as a BFF/proxy) may use
    # fetch legitimately and are excluded. router.prefetch()/apiFetch() are not
    # the global fetch and must not be flagged, so a word-boundary regex is used.
    web_app = frontend / "web_app"
    if web_app.exists():
        fetch_re = re.compile(r"(?<![\w.])fetch\(")
        for f in iter_text_files(web_app, eff):
            if f.suffix.lower() not in source_ext:
                continue
            low = str(f).replace("\\", "/").lower()
            # The typed client itself legitimately uses fetch — never flag it.
            if "/src/lib/api/" in low:
                continue
            # Next.js server route handlers legitimately call fetch (BFF/proxy).
            if "/src/app/api/" in low:
                continue
            # Only inspect client-side code: components/hooks always, and app
            # pages/layouts only when they opt in with the "use client" directive.
            is_client = ("/src/components/" in low or "/src/hooks/" in low)
            if not is_client:
                head = "\n".join(read_text(f).splitlines()[:5]).replace('"', "'")
                if "'use client'" not in head:
                    continue
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                s = line.strip()
                if s.startswith("//") or s.startswith("*") or s.startswith("import"):
                    continue
                if fetch_re.search(line) or "XMLHttpRequest" in line:
                    rep.add(
                        YEL, "FE10", "frontend",
                        rel(f, repo),
                        "raw fetch()/XMLHttpRequest bypasses the typed API "
                        "client (src/lib/api/*)",
                        intended="route all backend calls through the typed API "
                                 "client so auth, errors and caching are centralized",
                        line=i,
                    )
                    reported += 1
                    break

            if reported >= 200:
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

    # Accumulate layer-level afferent/efferent coupling (proxy for package
    # instability used by MET4).
    _layer_ca_accum: dict[str, int] = defaultdict(int)
    _layer_ce_accum: dict[str, int] = defaultdict(int)
    for module in graph.modules.keys():
        layer = layer_of_module(module)
        if not layer:
            continue
        _layer_ca_accum[layer] += graph.fan_in.get(module, 0)
        _layer_ce_accum[layer] += graph.fan_out.get(module, 0)

    for layer, counts in package_classes.items():
        total = counts["total"]
        if total == 0:
            continue

        abstractness = counts["abstract"] / total
        # MET4: Distance from main sequence D = |A + I - 1|.
        # Instability I is approximated at the layer ("package") level from the
        # aggregated afferent/efferent coupling of its modules. A high D means
        # the layer is simultaneously concrete and stable (or abstract and
        # unstable) — i.e. it violates the main sequence.
        layer_ca = _layer_ca_accum.get(layer, 0)
        layer_ce_val = _layer_ce_accum.get(layer, 0)
        denom = layer_ca + layer_ce_val
        if denom:
            instability = layer_ce_val / denom
            distance = abs(abstractness + instability - 1.0)
            if distance > 0.6:
                rep.add(
                    GRN, "MET4", layer, f"backend/{layer}/",
                    f"distance from main sequence high: D={distance:.2f} "
                    f"(A={abstractness:.2f}, I={instability:.2f})",
                    intended="balance abstractness and instability: stable, "
                             "concrete packages vs unstable, abstract ones",
                )
                reported += 1

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

    # BC2: Domain event definitions must be well-formed.
    # Every class whose name ends with "Event" in an events/ package must be a
    # typed @dataclass or model with a unique id and a serialization method,
    # otherwise cross-domain consumers cannot reliably publish/consume it.
    backend = repo / "backend"
    if backend.exists():
        event_dirs = [
            p for p in backend.rglob("events")
            if p.is_dir() and "venv" not in p.parts
        ]
        for ev_root in event_dirs:
            for f in iter_text_files(ev_root, eff):
                if f.suffix.lower() != ".py":
                    continue
                tree = parse_safe(f)
                if tree is None:
                    continue
                relp = rel(f, repo)
                for node in ast.walk(tree):
                    if not (isinstance(node, ast.ClassDef)
                            and node.name.endswith("Event")):
                        continue
                    is_dataclass = any(
                        (isinstance(d, ast.Name) and d.id == "dataclass")
                        or (isinstance(d, ast.Call)
                            and getattr(d.func, "id", "") == "dataclass")
                        for d in node.decorator_list
                    )
                    base_ids = {
                        getattr(b, "id", getattr(b, "attr", ""))
                        for b in node.bases
                    }
                    is_model = bool(
                        base_ids & {"BaseModel", "Base", "OrmBase",
                                    "_PermissiveBase", "SQLModel"}
                    )
                    if not (is_dataclass or is_model):
                        rep.add(
                            YEL, "BC2", "events", relp,
                            f"domain event '{node.name}' is not a @dataclass or "
                            f"model — define it with typed payload fields",
                            intended="define domain events as @dataclass or "
                                     "pydantic/ORM model with typed fields",
                            line=node.lineno,
                        )
                        reported += 1
                        continue
                    field_names = {
                        getattr(t.target, "id", "")
                        for t in node.body
                        if isinstance(t, ast.AnnAssign)
                        and isinstance(getattr(t, "target", None), ast.Name)
                    }
                    method_names = {
                        n.name for n in node.body
                        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    }
                    has_id = bool(
                        field_names & {"event_id", "id", "uuid", "event_uuid"}
                    )
                    has_serialize = bool(
                        method_names
                        & {"to_dict", "serialize", "model_dump", "dict", "schema"}
                    )
                    if not (has_id or has_serialize):
                        rep.add(
                            YEL, "BC2", "events", relp,
                            f"domain event '{node.name}' lacks a unique event id "
                            f"and a serialization method",
                            intended="add a unique event id (event_id/uuid) and a "
                                     "to_dict()/serialize() method for traceability",
                            line=node.lineno,
                        )
                        reported += 1

        if reported >= 300:
            return


# ============================================================================
# SECTION 35: ARCHITECTURE REGISTRY
# ============================================================================

# ============================================================================
# SECTION 35B: TARGET ARCHITECTURE (from ARCHITECTURE_DIAGRAM.md) + NEW CHECKS
# ============================================================================

def target_architecture_diagram() -> str:
    """
    Build the target-architecture section from ARCHITECTURE_DIAGRAM.md.
    Each mermaid block is assembled separately to avoid triple-quote /
    backtick collisions that break AI-generated output.

    NOTE: the architecture uses DOMAIN schemas (customer, supplier, logistics,
    admin, employee, …), each owning its own `user` table (customer.user.id,
    supplier.user.id, …). The forbidden schemas are core/platform/identity.
    """
    FENCE = "```"          # single source for the fence marker
    parts: list[str] = []

    # ── header ──────────────────────────────────────────────
    parts.append("## 2. Target Architecture (should-be, from ARCHITECTURE_DIAGRAM.md)")
    parts.append("")

    # ── 2.1 System Context ──────────────────────────────────
    parts.append("### 2.1 System Context")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart LR\n'
        '    subgraph FE["FRONTEND — Next.js 16.3.1 (frontend/web_app)"]\n'
        '        FEA["App Router (src/app/*)"]\n'
        '        FEL["API client (src/lib/api/*) — fetches /rbac/catalog"]\n'
        '        FES["Zustand stores (cart/currency/wishlist/...)"]\n'
        '    end\n'
        '    subgraph BE["BACKEND — FastAPI (backend/) — N stateless replicas"]\n'
        '        BEM["middleware/ pipeline (orchestrator.py)"]\n'
        '        BEMOD["modules/*/routers/ (thin: auth + require_feature + 1 service call)"]\n'
        '        BEDOM["domains/*/services/ (business logic + DB access)"]\n'
        '        BEFEAT["rbac/ (catalog · roles · resolution · dependencies)"]\n'
        '        BEK["kernel/ (money · numbering · country · period)"]\n'
        '        BEP["providers/ (AI/ML + 3rd-party adapters)"]\n'
        '        BEJ["jobs/ + events (background consumers)"]\n'
        '    end\n'
        '    subgraph INF["infrastructure/ (platform — zero business logic)"]\n'
        '        BEDB["database/ (get_db · RLS enforcer)"]\n'
        '        RED[(redis: auth cache · catalog cache · sessions · realtime)]\n'
        '    end\n'
        '    subgraph DB["DATA — PostgreSQL (domain schemas: finance/catalog/orders/…; one schema per domain)"]\n'
        '        DBE[("Pooled via PgBouncer")]\n'
        '        DBM[("Models — domains/*/models/ (schema per domain)")]\n'
        '    end\n'
        '    subgraph EXT["EXTERNAL"]\n'
        '        PG[(Payment gateway)]\n'
        '        AI[("AI/ML models")]\n'
        '        SMTP[("SMTP / email")]\n'
        '        CDN[("CDN / static + images")]\n'
        '    end\n'
        '    CDN --> FE\n'
        '    FEA --> FEL --> BEM --> BEMOD\n'
        '    FES -. state .- FEA\n'
        '    BEMOD --> BEFEAT\n'
        '    BEMOD --> BEDOM\n'
        '    BEDOM --> BEK\n'
        '    BEDOM --> BEP\n'
        '    BEDOM --> BEDB\n'
        '    BEDOM --> RED\n'
        '    BEP --> AI\n'
        '    BEJ --> DBE\n'
        '    BEDB --> DBE\n'
        '    DBE --> DBM\n'
        '    BEDOM --> PG\n'
        '    BEDOM --> SMTP'
    )
    parts.append(FENCE)
    parts.append("")

    # ── 2.2 Backend Circuit ─────────────────────────────────
    parts.append("### 2.2 Backend Circuit (target request lifecycle)")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart TD\n'
        '    Client([Client / Load Balancer])\n'
        '    subgraph BE["BACKEND — FastAPI + Middleware (middleware/orchestrator.py)"]\n'
        '        direction TB\n'
        '        L1["1 FOUNDATION: GZip · CORS · IP extract · RequestID · API-Version"]\n'
        '        L2["2 SECURITY: SecurityHeaders · ImpossibleTravel · CSRF"]\n'
        '        L3["3 RATE LIMIT: Sliding-window /path"]\n'
        '        L4["4 GEO/COUNTRY: CountryContext"]\n'
        '        L5["5 OBSERVABILITY: RequestLogging"]\n'
        '        L6["6 COMPLIANCE: PCI-DSS (prod only)"]\n'
        '        L1 --> L2 --> L3 --> L4 --> L5 --> L6\n'
        '    end\n'
        '    subgraph MOD["modules/*/routers/ — thin; require_feature gate; NO db writes"]\n'
        '        H["GET /health · /health/deps · /health/ready"]\n'
        '        R["Module routers: modules/admin/routers/finance_*, modules/customer/routers/checkout_*, ..."]\n'
        '        G["AUTO-GENERATED public routers (emitted from domain route contracts)"]\n'
        '    end\n'
        '    subgraph SEC["SECURITY / AUTH (modules/{m}/auth/ + rbac/dependencies.py)"]\n'
        '        AUTH["get_current_user<br/>verify_token(JWT jti) → Redis cache → db lookup"]\n'
        '        FEAT["require_feature(finance.ledger.post) → rbac/resolution.py"]\n'
        '    end\n'
        '    subgraph SVC["domains/*/services/ → infrastructure"]\n'
        '        S["domains/finance/services/* (owns DB access + transactions)"]\n'
        '        K["kernel/ (money · numbering · country · period)"]\n'
        '    end\n'
        '    subgraph DBL["infrastructure/database/ (single RLS enforcer)"]\n'
        '        POOL[("Engine + Pool (PgBouncer in front)")]\n'
        '        GETDB["get_db() dep — open → yield → rollback/close"]\n'
        '        KEYS["Keyset pagination (cursor), NEVER OFFSET on hot lists"]\n'
        '        MODELS[("Domains models — one Postgres schema per domain; e.g. schema=finance; each domain owns its tables")]\n'
        '    end\n'
        '    Client --> L1\n'
        '    L6 --> H\n'
        '    L6 --> R\n'
        '    H --> DBL\n'
        '    R --> AUTH\n'
        '    R --> FEAT\n'
        '    G --> AUTH\n'
        '    G --> FEAT\n'
        '    AUTH --> GETDB\n'
        '    FEAT --> S\n'
        '    R --> S\n'
        '    S --> K\n'
        '    S --> GETDB\n'
        '    GETDB --> POOL\n'
        '    POOL --> MODELS\n'
        '    S --> KEYS'
    )
    parts.append(FENCE)
    parts.append("")

    # ── 2.3 Database Subsystem ──────────────────────────────
    parts.append("### 2.3 Database Subsystem")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart TD\n'
        '    subgraph DBL["infrastructure/database/ — connection + sessions"]\n'
        '        URL["DATABASE_URL from settings"]\n'
        '        ENGINE["create_async_engine<br/>AsyncPG (SQLAlchemy 2.0.51 — async present)"]\n'
        '        POOL["PgBouncer (transaction mode) in front<br/>pool_pre_ping · pool_recycle"]\n'
        '        SCHEMA["Domain-owned schemas<br/>finance.* · accounts.* · catalog.* · orders.* · payments.* · logistics.* · suppliers.* · customers.* · hr.* · comms.* · media.* · country.* · governance.* (one schema per domain; no core/platform/identity)"]\n'
        '        GETDB["get_db() — one session source; rollback/close on exit"]\n'
        '        KEYS["Keyset cursor pagination helper (no OFFSET on hot paths)"]\n'
        '        CHK["check_connection_health() → SELECT 1"]\n'
        '    end\n'
        '    subgraph OPS["schema + migration"]\n'
        '        BASE["infrastructure/database/base.py → Base"]\n'
        '        MIG["alembic/ migrations (versioned, single source of truth)"]\n'
        '        SEED["infrastructure/database/seed.py (idempotent)"]\n'
        '    end\n'
        '    subgraph TBL["Tables — domain schemas; no core/platform/identity"]\n'
        '        S1["customer.user · supplier.user · logistics.user · customers.user · accounts.user · finance.user"]\n'
        '        S2["customer.orders · catalog.products · orders.checkout"]\n'
        '        S3["finance.* · accounts.* · catalog.* · orders.* · payments.* · logistics.* · suppliers.* · customers.* · hr.* · comms.* · media.* · country.* · governance.* (domain schemas)"]\n'
        '    end\n'
        '    URL --> ENGINE --> POOL --> SCHEMA\n'
        '    POOL --> GETDB --> SCHEMAS\n'
        '    KEYS --> GETDB\n'
        '    CHK --> ENGINE\n'
        '    BASE --> SCHEMAS --> MIG\n'
        '    SEED --> SCHEMAS'
    )
    parts.append(FENCE)
    parts.append("")

    # ── 2.4 Security Subsystem ──────────────────────────────
    parts.append("### 2.4 Security Subsystem")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart TD\n'
        '    Client([Request])\n'
        '    subgraph MW["Middleware (middleware/orchestrator.py)"]\n'
        '        CORS["CORSMiddleware (CORS_ORIGINS env)"]\n'
        '        IP["IPExtractionMiddleware"]\n'
        '        SH["EnhancedSecurityHeadersMiddleware (CSP · HSTS)"]\n'
        '        IT["ImpossibleTravelMiddleware"]\n'
        '        CSRF["CSRFMiddleware (prod)"]\n'
        '        RL["RateLimitMiddleware (per-path)"]\n'
        '        CC["CountryContextMiddleware"]\n'
        '        PCI["PCIDSSMiddleware (prod only)"]\n'
        '    end\n'
        '    subgraph AUTH["Auth deps (rbac/dependencies.py · modules/{m}/auth)"]\n'
        '        SCHEME["OAuth2PasswordBearer tokenUrl per actor (modules/{m}/auth/login)"]\n'
        '        GU["get_current_user — verify_token(JWT jti) → Redis → db"]\n'
        '        GOU["get_optional_user"]\n'
        '        GA["get_current_{module} (modules/{m}/auth)"]\n'
        '    end\n'
        '    subgraph SECUTILS["Security primitives"]\n'
        '        TOK["infrastructure/security/auth.py — verify_token · cache · get_redis_health_status"]\n'
        '        RED[(Redis — token cache + blacklist)]\n'
        '        ZT["infrastructure/security/zero_trust_auth.py"]\n'
        '    end\n'
        '    Client --> CORS --> IP --> SH --> IT --> CSRF --> RL --> CC --> PCI\n'
        '    PCI --> GU & GOU & GA\n'
        '    GU --> TOK --> RED\n'
        '    ZT --> GU'
    )
    parts.append(FENCE)
    parts.append("")

    # ── 2.5 Providers Subsystem ─────────────────────────────
    parts.append("### 2.5 Providers Subsystem")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart TD\n'
        '    subgraph PB["providers/_base.py — abstraction (REQUIRED base)"]\n'
        '        BP["BaseProvider: is_available() · health_check()"]\n'
        '        BAI["BaseAIProvider: load_model · predict · preprocess · postprocess"]\n'
        '    end\n'
        '    subgraph PM["Provider modules (must subclass base)"]\n'
        '        ANA["analytics · ai · automation · auth"]\n'
        '        GEO["geography · image · media · news"]\n'
        '        SRCH["comms · finance · payments · security · voice"]\n'
        '    end\n'
        '    subgraph PF["Domain sub-packages (swappable adapters)"]\n'
        '        PFPY["ai · analytics · auth · automation"]\n'
        '        PFC["comms · finance · geography · image · media · news · payments · security · voice"]\n'
        '    end\n'
        '    subgraph INF["Infra"]\n'
        '        AW["async_workers.py (off-request AI)"]\n'
        '        CFG["config.py"]\n'
        '    end\n'
        '    BP --> PM --> AW\n'
        '    BP --> PF --> AW\n'
        '    AW --> EXT[("External AI/ML + 3rd-party APIs")]\n'
        '    subgraph CALLERS["Allowed callers (contract)"]\n'
        '        SVC["domains/*/services/**"]\n'
        '        JOB["jobs/* (mcp_server, seed_all)"]\n'
        '    end\n'
        '    SVC --> PM & PF\n'
        '    SVC --> AW\n'
        '    JOB --> PM\n'
        '    JOB --> AW'
    )
    parts.append(FENCE)
    parts.append("")

    # ── 2.6 Frontend Subsystem ──────────────────────────────
    parts.append("### 2.6 Frontend Subsystem")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart TD\n'
        '    subgraph FEA["App Router (frontend/web_app/src/app)"]\n'
        '        LAY["layout.tsx · error.tsx · global-error.tsx · loading.tsx"]\n'
        '        ROUTES["Route groups: admin · auth · cart · checkout · products · orders · supplier · logistics-partner · wishlist · profile · chatbot · tracking"]\n'
        '    end\n'
        '    subgraph FEL["API + data (src/lib)"]\n'
        '        CLIENT["lib/api/client.ts (typed fetch wrapper)"]\n'
        '        AUTH["lib/api/auth.ts"]\n'
        '        ERR["lib/api/errors.ts · index.ts"]\n'
        '        USEAPI["useApi.ts · useAuth.tsx"]\n'
        '    end\n'
        '    subgraph FEST["State (Zustand)"]\n'
        '        CART["cartStore · wishlistStore"]\n'
        '        CUR["currencyStore · localeStore · themeStore"]\n'
        '        BG["backgroundJobs · backgroundJobStore"]\n'
        '    end\n'
        '    subgraph FEC["Components (src/components)"]\n'
        '        UI["ui/ (design-system, tokens only)"]\n'
        '        ADMIN["admin/ (command center)"]\n'
        '        AUTHc["auth/ · chat/ · country/ · map/ · supplier/ · comms/ · ems/"]\n'
        '    end\n'
        '    subgraph FER["Infra"]\n'
        '        RT["utils/realtime.ts (WebSocket)"]\n'
        '        THEME["theme/ · styles/ (Tailwind + DESIGN TOKENS — no inline <style>)"]\n'
        '    end\n'
        '    ROUTES --> CLIENT --> AUTH & ERR\n'
        '    USEAPI --> FEST\n'
        '    ROUTES --> FEC --> FEST\n'
        '    RT -. live .-> BG\n'
        '    FEL -->|HTTP /api/v1/*| BE[("Backend FastAPI")]'
    )
    parts.append(FENCE)
    parts.append("")

    # ── 2.7 Production Scaling Topology ─────────────────────
    parts.append("### 2.7 Production Scaling Topology (100K target)")
    parts.append(FENCE + "mermaid")
    parts.append(
        'flowchart LR\n'
        '    subgraph EDGE["EDGE (CDN + WAF + rate limit)"]\n'
        '        WAF["WAF / DDoS"]; EC["Edge cache: catalog, static, images"]; RL["Edge rate limit"]\n'
        '    end\n'
        '    subgraph GW["GATEWAY"]\n'
        '        APIGW["API Gateway / LB (TLS, auth offload)"]; WSG["WS Gateway (Redis fan-out, Node/Go at 100K+)"]\n'
        '    end\n'
        '    subgraph COMPUTE["COMPUTE (stateless autoscale)"]\n'
        '        FE["Next.js 16.3.1 (ISR/edge)"]; BE["FastAPI pods (AsyncPG)"]; WR["Async workers (Kafka consumers — Phase C)"]\n'
        '    end\n'
        '    subgraph MESH["EVENT & DATA MESH (Phase C target)"]\n'
        '        KAFKA["Kafka (event bus)"]; CDC["Debezium (WAL CDC)"]; REDIS["Redis Cluster (sessions, cart, cache, pub/sub)"]; ES["OpenSearch/ES (catalog facets)"]\n'
        '    end\n'
        '    subgraph DB["DATA"]\n'
        '        PGP[("Postgres PRIMARY (writes)")]; PGR[("Read replicas (auto)")]; PB["PgBouncer"]\n'
        '    end\n'
        '    EXT["AI / Payment gateways"]\n'
        '    U((100K users)) --> WAF --> EC --> APIGW\n'
        '    U --> WSG\n'
        '    APIGW --> FE & BE\n'
        '    BE --> REDIS & ES & PGR\n'
        '    BE -->|commands| KAFKA\n'
        '    KAFKA --> WR --> PGP & EXT\n'
        '    PGP -->|WAL| CDC --> KAFKA --> ES\n'
        '    PGP --> PB --> PGR\n'
        '    WSG <-->|pub/sub| REDIS'
    )
    parts.append(FENCE)
    parts.append("")

    # ── Phase annotations ───────────────────────────────────
    parts.append("### 2.8 Phase Annotations")
    parts.append("")
    parts.append("| Phase | Goal | Pre-req | Status in codebase |")
    parts.append("|---|---|---|---|")
    parts.append("| **A** | ~10K–20K concurrent (existing code) | PgBouncer + read replica + single Redis + CDN + keyset pagination | Config-only; `utils/cache.py` + `redis_client.py` present |")
    parts.append("| **B** | ~50K+ concurrent | AsyncPG + SQLAlchemy 2.0 async sessions + replica fan-out + Redis pub/sub WS fan-out | Async engine present (create_async_engine + AsyncSession); scale-out remaining |")
    parts.append("| **C** | 100K throughput | Kafka + Debezium CDC + OpenSearch + Redis Cluster + dedicated WS gateway + partitioned primary | Greenfield; not in codebase |")
    parts.append("")
    parts.append("> **Note:** the architecture uses DOMAIN schemas (finance, accounts, catalog, orders, payments, logistics, suppliers, customers, hr, comms, media, country, governance, …), each owning its own `user` table (customer.user.id, supplier.user.id, …). The forbidden schemas are core/platform/identity.")
    parts.append("")

    return "\n".join(parts)


# Keep backward-compatible module-level constant so existing
# render_markdown() code that references TARGET_ARCHITECTURE_DIAGRAM
# continues to work without any other change.
TARGET_ARCHITECTURE_DIAGRAM = target_architecture_diagram()
    
# ============================================================================
# SECTION 40: DATABASE AUDIT — CONSTANTS & DATA MODELS
# ============================================================================

# --- Database domain taxonomy (unified with PLACEMENT_DOMAIN_KEYWORDS) ---
    # DOMAIN schemas are used (finance, accounts, catalog, orders, payments, logistics, suppliers, customers, hr, comms, media, country, governance, …), each
    # owning its own `user` table (referenced as customer.user.id, supplier.user.id, …).
    # The FORBIDDEN schemas are core/platform/identity — any model or FK using one is a
    # deviation (flagged by DBA01 / DBA06). Domain schemas and schema=None are allowed.
DBA_FORBIDDEN_SCHEMAS: set[str] = {"core", "platform", "identity"}




DBA_EXPECTED_EVENT_TABLES = {
    "outbox_events", "inbox_events", "event_retry_queue", "event_dead_letter",
}

DBA_EXPECTED_AI_TABLES = {
    "ai_requests", "ai_results", "ai_embeddings", "ai_upload_jobs",
    "ai_staging_products", "ai_staging_variants", "ai_staging_images",
    "ai_audit_log", "ai_generation_logs", "upload_jobs",
}

DBA_PARTITION_EXPECTED_TABLES = {
    "journal_entries", "audit_logs", "chat_messages", "shipment_events",
}

DBA_FINANCE_PROTECTED_TABLES = {
    "journal_entries", "journal_entry_lines", "ap_ledger_entries",
    "ar_ledger_entries", "ledger_entries", "accounts", "payouts",
}


DBA_BINARY_TYPES = {"LARGEBINARY", "BLOB", "BYTEA", "IMAGE"}
DBA_JSON_TYPES = {"JSON", "JSONB"}
DBA_DATETIME_TYPES = {"DATETIME", "TIMESTAMP", "DATE", "TIME"}

DBA_TABLE_SINGULAR_ALLOW = {
    "alembic_version", "audit", "worm_audit", "metadata", "data",
    "coupon_usage", "search_usage", "token_usage",
}

# Naming-convention allow-lists for DBA11. These reflect widely-used,
# recommended conventions (not just the narrow is_/has_/can_ prefixes) so the
# checker stops flagging correct code as violations.
DBA_BOOLEAN_OK_PREFIX = (
    "is_", "has_", "can_", "allow_", "enable_", "disable_", "was_",
    "must_", "should_", "need_", "do_", "did_",
    "use_", "requires_", "show_", "supports_", "auto_", "manual_",
    "include_", "exclude_", "accept_", "reject_", "send_", "mark_",
    "hide_", "process_", "generate_", "sync_", "skip_", "attach_",
    "has_", "want_", "prefer_", "track_", "notify_", "block_",
)
DBA_BOOLEAN_OK_SUFFIX = (
    "_enabled", "_active", "_disabled", "_visible", "_verified", "_deleted",
    "_published", "_featured", "_required", "_completed", "_locked",
    "_confirmed", "_archived", "_blocked", "_suspended", "_flagged", "_open",
    "_closed", "_pending", "_ready", "_draft", "_live", "_hidden", "_selected",
    "_default", "_primary", "_valid", "_invalid", "_available", "_unavailable",
    "_on", "_off", "_set", "_expired", "_paid", "_shipped", "_cancelled",
    "_canceled", "_refunded", "_approved", "_rejected", "_resolved", "_managed",
    "_tracked", "_anonymous", "_public", "_private", "_secure", "_insecure",
    "_registered", "_activated", "_blacklisted", "_whitelisted", "_banned",
    "_allowed", "_applied", "_used", "_flag", "_supported", "_included",
    "_requested", "_review", "_evaluated", "_generated", "_calculated",
    "_synced", "_matched", "_processed", "_skipped", "_restricted",
    "_requested", "_ignored", "_permitted", "_authorized", "_granted",
    "_compliant", "_inclusive", "_residency", "_triggered", "_ed",
)
DBA_BOOLEAN_OK_NAMES = {
    "active", "enabled", "disabled", "visible", "verified", "deleted",
    "published", "featured", "required", "completed", "locked", "confirmed",
    "archived", "blocked", "suspended", "open", "closed", "pending", "ready",
    "draft", "live", "hidden", "selected", "default", "primary", "valid",
    "available", "unavailable", "paid", "shipped", "cancelled", "canceled",
    "refunded", "approved", "rejected", "resolved", "managed", "tracked",
    "anonymous", "public", "private", "secure", "insecure", "registered",
    "activated", "blacklisted", "whitelisted", "banned", "guest", "staff",
    "superuser", "admin", "member", "owner",
    "smtp_use_tls", "smtp_use_ssl", "use_tls", "use_ssl",
    "conversion", "success", "flagged", "reconciled", "used",
    "pass_fee_to_customer", "pass_fee", "fee_to_customer",
}
DBA_JSON_OK_SUFFIX = (
    "_json", "_payload", "_attributes", "_config", "_data", "_meta", "_info",
    "_details", "_settings", "_spec", "_profile", "_content", "_body", "_tags",
    "_options", "_params", "_fields", "_schema", "_extra", "_custom",
    "_definition", "_raw", "_blob", "_document", "_state", "_snapshot",
    "_tree", "_map", "_list", "_dict", "_obj", "_xml", "_yaml", "_geometry",
    "_coordinates", "_location", "_metadata",
    "_ids", "_items", "_types", "_links", "_methods", "_rules", "_variables",
    "_regions", "_roles", "_projects", "_tasks", "_vectors", "_lists",
    "_sets", "_notes", "_flags", "_logs", "_entries", "_records", "_docs",
)
DBA_JSON_OK_NAMES = {
    "details", "config", "permissions", "benefits", "factors", "settings",
    "metadata", "attributes", "payload", "content", "body", "tags", "options",
    "params", "fields", "schema", "definition", "spec", "profile", "extra",
    "custom", "data", "info", "meta", "document", "state", "snapshot", "tree",
    "map", "list", "dict", "obj", "raw", "blob", "xml", "yaml", "geometry",
    "coordinates", "location", "rules", "mapping", "template", "translation",
    "localization", "preferences", "properties",
    "countries", "sizes", "materials", "media", "urls", "axes", "images",
    "files", "assets", "videos", "documents", "labels", "categories",
    "metrics", "dimensions", "coords", "points", "nodes", "edges", "values",
    "entries", "records", "attachments", "comments", "notes", "children",
    "members", "participants", "recipients", "histogram", "series", "timeline",
    "additional_media", "evidence_urls", "variant_axes", "variant_options",
    "segments", "buckets", "bins", "vectors", "embeddings", "tokens",
    "detail", "action_items", "allowed_roles", "coverage_regions",
    "credentials", "document_types", "lines", "product_ids", "search_vector",
    "service_types", "social_links", "staff_assigned_projects",
    "staff_assigned_tasks", "supported_methods", "triggered_rules",
    "variables", "credentials_json", "allowed", "supported",
}
DBA_DATETIME_OK_SUFFIX = (
    "_at", "_on", "_date", "_time", "_start", "_end", "_from", "_to",
    "_since", "_until", "_when", "_ts", "_expiry", "_deadline", "_occurrence",
)
DBA_DATETIME_OK_PREFIX = (
    "last_", "first_", "estimated_", "actual_", "previous_", "next_",
    "scheduled_", "expected_",
)
DBA_DATETIME_OK_NAMES = {
    "date", "dob", "dob_date", "timestamp", "created", "updated",
    "birthdate", "birth_date", "time", "datetime", "since", "until", "when",
    "expiry", "deadline", "occurrence", "login", "seen", "sent", "received",
    "modified", "processed",
}
# Hot/large tables where OFFSET deep-pagination is a real concern (DBA32).
DBA_HOT_TABLES = {
    "orders", "order_items", "order_item", "products", "product", "carts",
    "cart_items", "cart_item", "users", "customers", "customer", "shipments",
    "shipment_events", "shipment_event", "payments", "payment_transactions",
    "notifications", "messages", "message", "journal_entries", "audit_logs",
    "payouts", "commissions", "coupons", "reviews", "addresses", "address",
    "suppliers", "inventory", "inventories", "transactions", "invoices",
    "refunds", "disputes", "tickets", "sessions", "search_results", "feeds",
    "activities", "activity", "events", "logs", "items", "line_items",
}

DBA_REQUIRED_CANONICAL_TABLES = {
    "media_assets", "worm_audit", "processed_webhook_events",
    "commission_rules", "country_configs", "feature_flags",
    "country_staff_assignments",
}

DBA_REQUIRED_SNAPSHOT_TABLES = {
    "mv_daily_sales", "mv_monthly_sales", "kpi_customer", "kpi_supplier",
    "kpi_country", "kpi_revenue", "kpi_orders", "kpi_retention",
    "kpi_conversion", "mv_cash_position", "mv_facet_counts",
}

# --- Database data models ---
@dataclass
class DBAColumnInfo:
    name: str
    line: int
    type_name: str = ""
    type_args: str = ""
    is_pk: bool = False
    is_index: bool = False
    is_unique: bool = False
    nullable: bool | None = None
    fk_target: str | None = None
    fk_ondelete: str | None = None
    raw: str = ""

@dataclass
class DBAModelInfo:
    name: str
    file: Path
    rel_path: str
    line: int
    table: str | None
    schema: str | None
    domain: str
    bases: list[str]
    columns: list[DBAColumnInfo]
    table_args_text: str = ""
    mixin_names: set[str] = field(default_factory=set)
    has_pk: bool = False
    has_uuid: bool = False
    has_country_code: bool = False
    has_created_at: bool = False
    has_updated_at: bool = False
    has_is_deleted: bool = False
    has_deleted_at: bool = False
    has_version: bool = False
    has_created_by: bool = False
    has_updated_by: bool = False

@dataclass
class DBAMigrationInfo:
    alembic_dir_exists: bool = False
    env_exists: bool = False
    ini_exists: bool = False
    versions_dir_exists: bool = False
    files: list[Path] = field(default_factory=list)
    revisions: dict[str, tuple[str, ...] | None] = field(default_factory=dict)
    heads: list[str] = field(default_factory=list)
    multiple_heads: bool = False
    tables_created: set[str] = field(default_factory=set)
    has_partition: bool = False
    downgrade_missing: list[str] = field(default_factory=list)
    stubs: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

@dataclass
class DBARLSInfo:
    sql_files: list[Path] = field(default_factory=list)
    rls_tables: set[str] = field(default_factory=set)
    interceptor_files: list[str] = field(default_factory=list)
    sets_context: bool = False


# ============================================================================
# SECTION 41: DATABASE AUDIT — MODEL PARSER
# ============================================================================

def dba_unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""

def dba_func_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""

def dba_dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))

def dba_annotation_type(annotation: ast.AST | None) -> str:
    if annotation is None:
        return ""
    s = dba_unparse(annotation).lower()
    if "int" in s: return "INTEGER"
    if "str" in s: return "STRING"
    if "bool" in s: return "BOOLEAN"
    if "datetime" in s: return "DATETIME"
    if "date" in s: return "DATE"
    if "uuid" in s: return "UUID"
    if "dict" in s or "json" in s: return "JSON"
    if "decimal" in s or "float" in s: return "NUMERIC"
    if "bytes" in s: return "BINARY"
    return ""

def dba_extract_table_args(value: ast.AST) -> tuple[str | None, str]:
    text = dba_unparse(value)
    schema = None
    dicts: list[ast.Dict] = []
    if isinstance(value, ast.Dict):
        dicts.append(value)
    elif isinstance(value, (ast.Tuple, ast.List)):
        for elt in value.elts:
            if isinstance(elt, ast.Dict):
                dicts.append(elt)
    for d in dicts:
        for k, v in zip(d.keys, d.values):
            if (isinstance(k, ast.Constant) and k.value == "schema"
                    and isinstance(v, ast.Constant)):
                schema = str(v.value)
    return schema, text

def dba_extract_column(name: str, call: ast.Call, line: int,
                       annotation: ast.AST | None = None) -> DBAColumnInfo:
    type_name = ""
    type_args = ""
    if call.args:
        first = call.args[0]
        if isinstance(first, ast.Call):
            type_name = dba_func_name(first.func)
            if first.args:
                args: list[str] = []
                for a in first.args:
                    if isinstance(a, ast.Constant):
                        args.append(str(a.value))
                type_args = ",".join(args)
        elif isinstance(first, (ast.Name, ast.Attribute)):
            type_name = dba_dotted_name(first).split(".")[-1]
    if type_name.upper() == "FOREIGNKEY":
        type_name = ""
    if not type_name and annotation is not None:
        type_name = dba_annotation_type(annotation)
    is_pk = is_index = is_unique = False
    nullable = fk_target = fk_ondelete = None
    for kw in call.keywords:
        if kw.arg == "primary_key" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            is_pk = True
        if kw.arg == "index" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            is_index = True
        if kw.arg == "unique" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
            is_unique = True
        if kw.arg == "nullable" and isinstance(kw.value, ast.Constant):
            nullable = bool(kw.value.value)
    for arg in call.args:
        if isinstance(arg, ast.Call) and dba_func_name(arg.func).endswith("ForeignKey"):
            if arg.args and isinstance(arg.args[0], ast.Constant):
                fk_target = str(arg.args[0].value)
            for kw in arg.keywords:
                if kw.arg == "ondelete" and isinstance(kw.value, ast.Constant):
                    fk_ondelete = str(kw.value.value)
    return DBAColumnInfo(
        name=name, line=line, type_name=type_name, type_args=type_args,
        is_pk=is_pk, is_index=is_index, is_unique=is_unique,
        nullable=nullable, fk_target=fk_target, fk_ondelete=fk_ondelete,
        raw=dba_unparse(call),
    )

def dba_infer_domain(backend: Path, f: Path, schema: str | None,
                     table: str | None) -> str:
    if schema:
        return schema.lower()
    try:
        parts = [p.lower() for p in f.relative_to(backend).parts]
    except ValueError:
        parts = []
    if len(parts) >= 3 and parts[0] == "models":
        candidate = parts[1]
        if candidate not in DEFAULT_SURFACE_NAMES and candidate not in DEFAULT_IGNORE_DIRS:
            return candidate
    text = f.stem.lower() + " " + (table or "")
    tokens = {t for t in re.split(r"[-_.\s]+", text) if t}
    for dom, keywords in PLACEMENT_DOMAIN_KEYWORDS.items():
        if tokens & {str(k).lower() for k in keywords}:
            return dom
    return "_triage"

def dba_parse_models(repo: Path) -> list[DBAModelInfo]:
    models: list[DBAModelInfo] = []
    backend = repo / "backend"
    if not backend.exists():
        return models
    for f in iter_text_files(backend, _ACTIVE_EFF or {"ignore_dirs": DEFAULT_IGNORE_DIRS, "text_ext": {".py"}, "max_read_bytes": DEFAULT_MAX_READ_BYTES}):
        if f.suffix.lower() != ".py":
            continue
        tree = parse_safe(f)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            table = schema = None
            table_args_text = ""
            columns: list[DBAColumnInfo] = []
            bases: list[str] = []
            for base in node.bases:
                nm = dba_dotted_name(base) or dba_unparse(base)
                if nm:
                    bases.append(nm)
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        if target.id == "__tablename__":
                            if isinstance(stmt.value, ast.Constant):
                                table = str(stmt.value.value)
                        elif target.id == "__table_args__":
                            schema, table_args_text = dba_extract_table_args(stmt.value)
                        elif isinstance(stmt.value, ast.Call):
                            fname = dba_func_name(stmt.value.func)
                            if fname in {"Column", "mapped_column"}:
                                columns.append(dba_extract_column(target.id, stmt.value, stmt.lineno))
                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if isinstance(stmt.value, ast.Call):
                        fname = dba_func_name(stmt.value.func)
                        if fname in {"Column", "mapped_column"}:
                            columns.append(dba_extract_column(stmt.target.id, stmt.value, stmt.lineno, stmt.annotation))
            if not table:
                continue
            mixin_names = {b.split(".")[-1] for b in bases if "Mixin" in b}
            colnames = {c.name.lower() for c in columns}
            domain = dba_infer_domain(backend, f, schema, table)
            models.append(DBAModelInfo(
                name=node.name, file=f, rel_path=rel(f, repo), line=node.lineno,
                table=str(table), schema=schema, domain=domain, bases=bases,
                columns=columns, table_args_text=table_args_text,
                mixin_names=mixin_names,
                has_pk=any(c.is_pk for c in columns) or ("id" in colnames),
                has_uuid="uuid" in colnames or any(c.type_name.upper() == "UUID" for c in columns),
                has_country_code="country_code" in colnames or "TenantMixin" in mixin_names,
                has_created_at="created_at" in colnames or "AuditMixin" in mixin_names or "TimestampMixin" in mixin_names,
                has_updated_at="updated_at" in colnames or "AuditMixin" in mixin_names or "TimestampMixin" in mixin_names,
                has_is_deleted="is_deleted" in colnames or "SoftDeleteMixin" in mixin_names,
                has_deleted_at="deleted_at" in colnames or "SoftDeleteMixin" in mixin_names,
                has_version="version" in colnames,
                has_created_by="created_by" in colnames or "AuditMixin" in mixin_names,
                has_updated_by="updated_by" in colnames or "AuditMixin" in mixin_names,
            ))
    return models


# ============================================================================
# SECTION 42: DATABASE AUDIT — MIGRATION PARSER
# ============================================================================

def dba_parse_migrations(repo: Path) -> DBAMigrationInfo:
    info = DBAMigrationInfo()
    backend = repo / "backend"
    alembic = backend / "alembic"
    versions = alembic / "versions"
    archive = alembic / "versions_archive"
    info.alembic_dir_exists = alembic.exists()
    info.env_exists = (alembic / "env.py").exists()
    info.versions_dir_exists = versions.exists()
    ini_candidates = [backend / "alembic.ini", repo / "alembic.ini", alembic / "alembic.ini"]
    info.ini_exists = any(p.exists() for p in ini_candidates)
    live_files = sorted(versions.glob("*.py")) if versions.exists() else []
    archive_files = sorted(archive.glob("*.py")) if archive.exists() else []
    info.files = live_files
    if alembic.exists():
        for f in alembic.glob("_*.py"):
            info.diagnostics.append(rel(f, repo))
    for f in live_files + archive_files:
        text = read_text(f) or ""
        low = text.lower()
        if "postgresql_partition_by" in low or "partition by" in low:
            info.has_partition = True
        for m in re.finditer(r"op\.create_table\(\s*['\"]([^'\"]+)['\"]", text):
            info.tables_created.add(m.group(1).split(".")[-1].lower())
        for m in re.finditer(r"op\.rename_table\(\s*['\"][^'\"]+['\"]\s*,\s*['\"]([^'\"]+)['\"]", text):
            info.tables_created.add(m.group(1).split(".")[-1].lower())
    downs: set[str] = set()
    for f in live_files:
        text = read_text(f) or ""
        rev_match = re.search(r"^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
        if rev_match:
            rev = rev_match.group(1)
            # down_revision may be None, a single id, or a tuple/Union of ids,
            # e.g.  down_revision = ('02ebc285f66f', '20260808_0001')
            # Collect every quoted revision id so merge migrations resolve
            # correctly; otherwise divergent heads look un-merged -> false heads.
            dm = re.search(r"^down_revision(?:\s*:\s*[^=]+)?\s*=\s*(.*)$", text, re.M)
            down_ids: list[str] = []
            if dm:
                val = dm.group(1).strip()
                if val and not val.lower().startswith("none"):
                    down_ids = re.findall(r"['\"]([^'\"]+)['\"]", val)
            info.revisions[rev] = tuple(down_ids) if down_ids else None
            for d in down_ids:
                downs.add(d)
        if "stub" in f.name.lower():
            info.stubs.append(rel(f, repo))
        tree = parse_safe(f)
        has_downgrade = False
        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
                    has_downgrade = True
                    only_pass = all(isinstance(s, ast.Pass) for s in node.body)
                    only_docstring = (len(node.body) == 1 and isinstance(node.body[0], ast.Expr)
                                     and isinstance(node.body[0].value, ast.Constant))
                    if only_pass or only_docstring:
                        info.downgrade_missing.append(f"{rel(f, repo)} (empty downgrade)")
        if not has_downgrade:
            info.downgrade_missing.append(rel(f, repo))
    info.heads = sorted(set(info.revisions.keys()) - downs)
    info.multiple_heads = len(info.heads) > 1
    return info


# ============================================================================
# SECTION 43: DATABASE AUDIT — RLS PARSER
# ============================================================================

def dba_parse_rls(repo: Path) -> DBARLSInfo:
    info = DBARLSInfo()
    backend = repo / "backend"
    candidates = [
        backend / "data" / "pg_rls_policies.sql",
        repo / "data" / "pg_rls_policies.sql",
        backend / "infrastructure" / "database" / "pg_rls_policies.sql",
    ]
    for p in candidates:
        if p.exists() and p not in info.sql_files:
            info.sql_files.append(p)
    for d in (backend / "data", repo / "data"):
        if not d.exists():
            continue
        for f in d.glob("*.sql"):
            text = read_text(f) or ""
            if "ROW LEVEL SECURITY" in text.upper():
                if f not in info.sql_files:
                    info.sql_files.append(f)
    enable_re = re.compile(
        r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?([a-zA-Z0-9_\.]+)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY", re.I)
    policy_re = re.compile(r"CREATE\s+POLICY\s+\w+\s+ON\s+([a-zA-Z0-9_\.]+)", re.I)
    for f in info.sql_files:
        text = read_text(f) or ""
        for rx in (enable_re, policy_re):
            for m in rx.finditer(text):
                table = m.group(1).split(".")[-1].lower()
                info.rls_tables.add(table)
    context_re = re.compile(r"app\.current_country_code|set_config\(\s*['\"]app\.current_country_code", re.I)
    for f in iter_text_files(backend, _ACTIVE_EFF or {"ignore_dirs": DEFAULT_IGNORE_DIRS, "text_ext": {".py"}, "max_read_bytes": DEFAULT_MAX_READ_BYTES}):
        if f.suffix.lower() != ".py":
            continue
        low = f.stem.lower()
        if "rls" in low:
            info.interceptor_files.append(rel(f, repo))
        parts = {p.lower() for p in f.parts}
        if ("middleware" in parts or "dependencies" in parts or f.name in {"main.py", "lifespan.py"}):
            text = read_text(f) or ""
            if context_re.search(text):
                info.sets_context = True
    return info


# ============================================================================
# SECTION 44: DATABASE AUDIT — STATIC CHECKS
# ============================================================================

def dba_parse_fk_target(fk_target: str) -> tuple[str | None, str, str]:
    """Parse a SQLAlchemy ForeignKey target string correctly.

    SQLAlchemy FK formats:
      - "table.column"           → (None,    "table",   "column")   ← NO schema
      - "schema.table.column"    → ("schema", "table",   "column")  ← WITH schema

    The old parser treated 2-part refs as schema.table, which is wrong.
    """
    parts = fk_target.strip().split(".")
    if len(parts) == 3:
        return parts[0].lower(), parts[1].lower(), parts[2].lower()
    elif len(parts) == 2:
        return None, parts[0].lower(), parts[1].lower()
    elif len(parts) == 1:
        return None, parts[0].lower(), ""
    return None, fk_target.lower(), ""


def dba_run_all_checks(repo: Path, rep: Report) -> tuple[list[DBAModelInfo], DBAMigrationInfo, DBARLSInfo]:
    """Run ALL database audit checks. Returns parsed data for summary."""
    models = dba_parse_models(repo)
    minfo = dba_parse_migrations(repo)
    rls = dba_parse_rls(repo)
    model_tables = {m.table.lower() for m in models if m.table}
    all_tables = set(model_tables) | set(minfo.tables_created)

    # ── FIX A1: Build table→domain lookup (was missing, caused NameError) ──
    table_to_domain: dict[str, str] = {}
    for m in models:
        if m.table:
            table_to_domain[m.table.lower()] = m.domain

    # ── Shared-reference FK exemption sets ──
    SHARED_REF_TARGETS: set[str] = {
    "customer.user.id",           # actor FK (shared reference, domain schema)
    "country.country_configs.code", # geography is shared reference
    }

    SHARED_REF_COLUMNS: set[str] = {
        "user_id", "created_by", "updated_by", "deleted_by",
        "approved_by", "rejected_by", "reviewed_by", "assigned_to",
        "assigned_by", "performed_by", "sender_id", "recipient_id",
        "actor_id", "author_id", "owner_id", "modified_by",
        "country_code",
    }

    # DBA26: Model placement — ORM models MUST live in domains/<domain>/models/.
    # Correctly-placed models (domains/{d}/models/...) must NOT be flagged (false-RED fix).
    # Models in exempt top-level dirs (tests/scripts/alembic/data/monitoring/docs) are
    # not part of the production ORM surface and are skipped.
    backend = repo / "backend"
    exempt_top = {"tests", "scripts", "alembic", "data", "monitoring", "docs"}
    for m in models:
        try:
            parts = [p.lower() for p in m.file.relative_to(backend).parts]
        except ValueError:
            parts = []
        if parts and parts[0] in exempt_top:
            continue
        if not (len(parts) >= 4 and parts[0] == "domains" and parts[2] == "models"):
            rep.add(RED, "DBA26", "models", m.rel_path,
                    f"ORM model '{m.name}' table '{m.table}' is outside domains/*/models/",
                    intended="move ORM models into domains/<domain>/models/", line=m.line)

    # DBA01: Forbidden schemas (core/platform/identity) must not be declared on any model.
    # Domain schemas (customer, supplier, …) are allowed — each owns its `user` table.
    reported = 0
    for m in models:
        if not m.table:
            continue
        if m.schema and m.schema in DBA_FORBIDDEN_SCHEMAS:
            rep.add(YEL, "DBA01", "models", m.rel_path,
                    f"model '{m.name}' table '{m.table}' declares forbidden schema '{m.schema}'",
                    intended="use a domain schema (e.g. schema='customer'); core/platform/identity are forbidden",
                    line=m.line)
            reported += 1
        if reported >= 300:
            break

    # DBA03: Standard columns
    reported = 0
    for m in models:
        if not m.table:
            continue
        if not m.has_pk:
            rep.add(RED, "DBA03", "models", m.rel_path,
                    f"model '{m.name}' table '{m.table}' has no primary key signal",
                    intended="every table must have an explicit PK", line=m.line)
            reported += 1
        missing: list[str] = []
        if not m.has_uuid:
            missing.append("uuid")
        if not (m.has_created_at and m.has_updated_at):
            missing.append("created_at/updated_at")
        if not (m.has_is_deleted or m.has_deleted_at):
            missing.append("soft-delete")
        if not m.has_version:
            missing.append("version")
        if not (m.has_created_by and m.has_updated_by):
            missing.append("created_by/updated_by")
        if missing:
            rep.add(YEL, "DBA03", "models", m.rel_path,
                    f"model '{m.name}' table '{m.table}' missing: {', '.join(missing)}",
                    intended="use AuditMixin + SoftDeleteMixin + TenantMixin", line=m.line)
            reported += 1
        if reported >= 400:
            break

    # DBA04: Country code width
    lengths: dict[str, list[str]] = defaultdict(list)
    for m in models:
        for c in m.columns:
            if c.name.lower() == "country_code" and c.type_args:
                lengths[c.type_args].append(f"{m.table}")
    if len(lengths) > 1:
        detail = "; ".join(f"{k}: {len(v)} tables" for k, v in sorted(lengths.items()))
        rep.add(YEL, "DBA04", "database", "backend/domains/",
                f"country_code width mismatch ({detail})",
                intended="unify country_code width in one migration")

    # DBA11: Naming conventions (advisory). Only flag genuinely non-conventional
    # names; widely-used conventions (active/enabled/details/config/period_start)
    # are accepted via the DBA_*_OK_* allow-lists above.
    reported = 0
    for m in models:
        if not m.table:
            continue
        issues: list[str] = []
        if not re.match(r"^[a-z0-9_]+$", m.table):
            issues.append("not snake_case")
        if not m.table.endswith(("s", "es", "ies")) and m.table not in DBA_TABLE_SINGULAR_ALLOW:
            issues.append("should be plural")
        if issues:
            rep.add(YEL, "DBA11", "models", m.rel_path,
                    f"table '{m.table}': " + "; ".join(issues),
                    intended="snake_case plural table names", line=m.line)
            reported += 1
        col_issues: list[str] = []
        for c in m.columns:
            if not re.match(r"^[a-z0-9_]+$", c.name):
                col_issues.append(f"{c.name} not snake_case")
            upper = c.type_name.upper()
            if upper in DBA_JSON_TYPES:
                if not (c.name.endswith(DBA_JSON_OK_SUFFIX) or c.name in DBA_JSON_OK_NAMES):
                    col_issues.append(f"{c.name} JSON should follow JSON naming")
            if upper == "BOOLEAN":
                if not (c.name.startswith(DBA_BOOLEAN_OK_PREFIX)
                        or c.name.endswith(DBA_BOOLEAN_OK_SUFFIX)
                        or c.name in DBA_BOOLEAN_OK_NAMES):
                    col_issues.append(f"{c.name} boolean should follow boolean naming")
            if upper in DBA_DATETIME_TYPES:
                if not (c.name.startswith(DBA_DATETIME_OK_PREFIX)
                        or c.name.endswith(DBA_DATETIME_OK_SUFFIX)
                        or c.name in DBA_DATETIME_OK_NAMES):
                    col_issues.append(f"{c.name} datetime should follow datetime naming")
        if col_issues:
            rep.add(YEL, "DBA11", "models", m.rel_path,
                    f"table '{m.table}' column issues: " + "; ".join(col_issues[:8]),
                    intended="follow naming conventions", line=m.line)
            reported += 1
        if reported >= 400:
            break

    # ══════════════════════════════════════════════════════════════
    # Build table → domain lookup (needed by DBA07/DBA08).
    # Was previously inside the retired DBA06 block — moved here
    # so it is always available.
    # ══════════════════════════════════════════════════════════════
    table_to_domain: dict[str, str] = {}
    for m in models:
        if m.table:
            table_to_domain[m.table.lower()] = m.domain

    # Shared reference targets that many domains legitimately FK to.
    # These get softer treatment (no CASCADE alarm, but still need index).
    SHARED_REF_TARGETS: set[str] = {
        "users", "roles", "auth_accounts",
        "country_configs",
    }

    # Domains whose tables must NEVER be CASCADE-deleted into
    PROTECTED_DOMAINS: set[str] = {
        "finance", "treasury", "audit", "security",
        "identity", "orders", "hr",
    }

    # ══════════════════════════════════════════════════════════════
    # DBA07 / DBA08 — FK hygiene only.
    # DBA06 RETIRED: ARCHITECTURE_DIAGRAM §3 / §10.3 states
    # cross-domain FKs are CORRECT and allowed across domain schemas (e.g. order → customer.user.id)
    # PostgreSQL design.  The old parser bug (treating "table.column"
    # as schema.table) is fixed by dba_parse_fk_target().
    # Domain-actor isolation is handled by check_domain_actor_isolation().
    # ══════════════════════════════════════════════════════════════
    reported = 0
    for m in models:
        if not m.table:
            continue
        for c in m.columns:
            if not c.fk_target:
                continue

            _fk_schema, fk_table, _fk_column = dba_parse_fk_target(c.fk_target)
            target_domain = table_to_domain.get(fk_table)
            is_shared_ref = fk_table in SHARED_REF_TARGETS

            # ── DBA08: FK column missing index ──
            if (not c.is_index and not c.is_unique and not c.is_pk
                    and c.name not in m.table_args_text):
                rep.add(YEL, "DBA08", "database", m.rel_path,
                        f"FK column '{m.table}.{c.name}' has no explicit index signal",
                        intended="every FK should have an explicit index",
                        line=c.line)
                reported += 1

            # ── DBA07: ON DELETE rule ──
            if c.fk_ondelete is None:
                rep.add(YEL, "DBA07", "database", m.rel_path,
                        f"FK '{m.table}.{c.name}' missing ON DELETE rule",
                        intended="default RESTRICT; CASCADE only for composition",
                        line=c.line)
                reported += 1

            elif c.fk_ondelete.upper() == "CASCADE":
                # Self-referencing FK with CASCADE can wipe entire trees
                if fk_table == m.table.lower():
                    rep.add(YEL, "DBA07", "database", m.rel_path,
                            f"self-referencing CASCADE: {m.table}.{c.name} → "
                            f"{m.table}.{_fk_column or 'id'} — deleting a root "
                            f"row cascades the entire subtree",
                            intended="use SET NULL or soft-delete for "
                                     "hierarchical tables",
                            line=c.line)
                    reported += 1

                # CASCADE into protected domain tables
                elif (fk_table in DBA_FINANCE_PROTECTED_TABLES
                      or target_domain in PROTECTED_DOMAINS):
                    rep.add(RED, "DBA07", "database", m.rel_path,
                            f"dangerous CASCADE into protected table: "
                            f"{m.table}.{c.name} → {c.fk_target}",
                            intended="never CASCADE into finance/audit/security/"
                                     "identity/orders/hr — use RESTRICT",
                            line=c.line)
                    reported += 1

                # CASCADE into shared reference tables (users, roles, country)
                elif is_shared_ref:
                    rep.add(RED, "DBA07", "database", m.rel_path,
                            f"CASCADE into shared reference table: "
                            f"{m.table}.{c.name} → {c.fk_target}",
                            intended="shared references (users/roles/country) "
                                     "must use RESTRICT — deleting a user "
                                     "must not cascade-delete business data",
                            line=c.line)
                    reported += 1

            elif c.fk_ondelete.upper() == "SET NULL":
                # SET NULL on a NOT NULL column will fail at runtime
                if getattr(c, "nullable", True) is False:
                    rep.add(RED, "DBA07", "database", m.rel_path,
                            f"SET NULL on NOT NULL FK: {m.table}.{c.name} — "
                            f"will raise IntegrityError at runtime",
                            intended="either make the column nullable or "
                                     "use RESTRICT / CASCADE",
                            line=c.line)
                    reported += 1

            if reported >= 600:
                break
        if reported >= 600:
            break


    # DBA09: JSONB indexes
    reported = 0
    for m in models:
        for c in m.columns:
            if c.type_name.upper() not in DBA_JSON_TYPES:
                continue
            args_low = m.table_args_text.lower()
            if not c.is_index and "gin" not in args_low and c.name not in args_low:
                rep.add(YEL, "DBA09", "database", m.rel_path,
                        f"JSONB column '{m.table}.{c.name}' has no GIN index signal",
                        intended="add GIN index for JSONB filters/facets", line=c.line)
                reported += 1
            if reported >= 250:
                break
        if reported >= 250:
            break

    # DBA10: Media bytes
    reported = 0
    for m in models:
        for c in m.columns:
            if c.type_name.upper() in DBA_BINARY_TYPES:
                rep.add(RED, "DBA10", "database", m.rel_path,
                        f"file bytes column: {m.table}.{c.name} ({c.type_name})",
                        intended="store metadata in DB; bytes in object storage", line=c.line)
                reported += 1
            if reported >= 200:
                break
        if reported >= 200:
            break

    # DBA02: create_all  (CORRECTED: broader gate detection)
    backend_dir = repo / "backend"
    _db_eff = _ACTIVE_EFF or {
        "ignore_dirs": DEFAULT_IGNORE_DIRS,
        "text_ext": {".py"},
        "max_read_bytes": DEFAULT_MAX_READ_BYTES,
    }
    if backend_dir.exists():
        create_re = re.compile(r"Base\.metadata\.create_all|metadata\.create_all\(")
        # CORRECTED: broader gate detection including production refusal patterns
        gate_re = re.compile(
            r"APP_ENV|development|is_development|settings\.ENV"
            r"|getenv\(['\"]APP_ENV|config\.ENV"
            r"|[Rr]efus.*production|[Rr]aise.*production"
            r"|ENVIRONMENT|environ|env\s*[!=]=\s*['\"]"
            r"|not\s+.*production|if\s+.*debug",
            re.I,
        )
        for f in iter_text_files(backend_dir, _db_eff):
            if f.suffix.lower() != ".py":
                continue
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if create_re.search(line):
                    gated = bool(gate_re.search(text))
                    if gated:
                        rep.add(YEL, "DBA02", "dev", rel(f, repo),
                                "create_all present but appears dev-gated",
                                intended="ensure impossible in production", line=i)
                    else:
                        rep.add(RED, "DBA02", "dev", rel(f, repo),
                                "create_all present without visible dev gate",
                                intended="gate behind APP_ENV=development", line=i)
                    break

    # DBA12/DBA13: Migrations
    if not minfo.ini_exists or not minfo.env_exists or not minfo.versions_dir_exists:
        rep.add(RED, "DBA12", "migrations", "backend/alembic/",
                "Alembic pipeline missing required components",
                intended="alembic.ini + env.py + versions/ are mandatory")
    if minfo.multiple_heads:
        rep.add(RED, "DBA13", "migrations", "backend/alembic/versions/",
                f"multiple Alembic heads: {', '.join(minfo.heads[:5])}",
                intended="merge to a single head")
    for f in minfo.downgrade_missing[:80]:
        rep.add(YEL, "DBA12", "migrations", f,
                "migration missing usable downgrade()",
                intended="every migration must have a real downgrade path")
    orm_only = sorted(model_tables - minfo.tables_created - {"alembic_version"})
    if orm_only:
        rep.add(YEL, "DBA13", "migrations", "backend/domains/",
                f"{len(orm_only)} model tables not in migrations: " + ", ".join(orm_only[:20]),
                intended="verify migrations exist for all ORM tables")

    # DBA05: RLS
    country_tables = sorted(
        {m.table.lower() for m in models if m.has_country_code and m.table}
    )
    if country_tables and not rls.sql_files:
        rep.add(RED, "DBA05", "security", "backend/infrastructure/database/security.py",
                "country-scoped models exist but no RLS enforcer found",
                intended="add ONE canonical RLS enforcer (e.g. backend/infrastructure/database/security.py) "
                         "and enable RLS uniformly via a session hook / shared auth dependency")
    if rls.sql_files:
        missing_rls = [t for t in country_tables if t not in rls.rls_tables]
        if missing_rls:
            rep.add(YEL, "DBA05", "security", "backend/data/pg_rls_policies.sql",
                    f"{len(missing_rls)} tables missing RLS: " + ", ".join(missing_rls[:20]),
                    intended="enable RLS + policies for every country_code table")
    if country_tables and not rls.sets_context:
        rep.add(RED, "DBA05", "security", "backend/middleware/",
                "no middleware signal setting app.current_country_code",
                intended="set RLS context per request; fail closed")

    # DBA17: Event tables
    missing_events = sorted(DBA_EXPECTED_EVENT_TABLES - all_tables)
    if missing_events:
        rep.add(YEL, "DBA17", "database", "backend/domains/",
                f"missing event/outbox tables: {', '.join(missing_events)}",
                intended="implement transactional outbox")

    # DBA18: Audit tables
    if "audit_logs" not in all_tables:
        rep.add(YEL, "DBA18", "database", "backend/domains/",
                "audit_logs table not detected",
                intended="use one append-only partitioned audit_logs table")

    # DBA19: Analytics
    has_snapshot = any(t.startswith("mv_") or t.startswith("kpi_") for t in all_tables)
    if not has_snapshot:
        rep.add(YEL, "DBA19", "analytics", "backend/domains/",
                "no analytics snapshot tables detected (mv_*/kpi_*)",
                intended="dashboards should read snapshots, not live aggregates")

    # DBA20: Finance immutability
    if backend_dir.exists():
        finance_re = re.compile(
            r"(?i)\b(update|delete)\s*\(\s*"
            r"(journal_entries|journal_entry_lines|ap_ledger_entries"
            r"|ar_ledger_entries|ledger_entries|accounts)\b"
        )
        reported = 0
        for f in iter_text_files(backend_dir, _db_eff):
            if f.suffix.lower() != ".py":
                continue
            parts = {p.lower() for p in f.parts}
            if "tests" in parts or "scripts" in parts or "alembic" in parts:
                continue
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if finance_re.search(line):
                    rep.add(RED, "DBA20", "finance", rel(f, repo),
                            "possible mutation of finance ledger table",
                            intended="posted ledger entries must be immutable", line=i)
                    reported += 1
                    break
            if reported >= 80:
                break

    # DBA22: Config constants
    if backend_dir.exists():
        const_re = re.compile(
            r"(?i)\b(COMMISSION|DELIVERY_FEE|REFUND_PERCENT|VAT_PERCENT|TAX_PERCENT)"
            r"\s*[:=]\s*\d"
        )
        reported = 0
        for f in iter_text_files(backend_dir, _db_eff):
            if f.suffix.lower() != ".py":
                continue
            parts = {p.lower() for p in f.parts}
            if {"tests", "scripts", "alembic", "data"} & parts:
                continue
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if const_re.search(line):
                    rep.add(YEL, "DBA22", "configuration", rel(f, repo),
                            "hardcoded business constant detected",
                            intended="store business rules in config tables", line=i)
                    reported += 1
                    break
            if reported >= 100:
                break

    # DBA29: Canonical tables
    missing_canonical = sorted(DBA_REQUIRED_CANONICAL_TABLES - all_tables)
    if missing_canonical:
        rep.add(YEL, "DBA29", "database", "backend/domains/",
                f"missing canonical tables: {', '.join(missing_canonical)}",
                intended="create required canonical tables")

    # DBA38: country_staff_assignments (Law 5 orthogonal country axis)
    if "country_staff_assignments" not in all_tables:
        rep.add(YEL, "DBA38", "database", "backend/domains/",
                "country_staff_assignments table missing - Law 5: country is the orthogonal "
                "scope axis; RLS session context needs country_staff_assignments.",
                intended="create country_staff_assignments table (country-scoped staff assignment)")

    # DBA30: Snapshot tables
    missing_snap = sorted(DBA_REQUIRED_SNAPSHOT_TABLES - all_tables)
    if missing_snap:
        rep.add(YEL, "DBA30", "analytics", "backend/domains/",
                f"missing analytics snapshot tables: {', '.join(missing_snap[:10])}",
                intended="dashboards must read snapshots per ADR-008")

    # DBA31: Composite index signals
    reported = 0
    for m in models:
        cols = {c.name.lower() for c in m.columns}
        if "country_code" in cols and "created_at" in cols:
            args_low = m.table_args_text.lower()
            has_composite = "country_code" in args_low and "created_at" in args_low
            country_indexed = any(
                c.name.lower() == "country_code" and (c.is_index or c.is_unique)
                for c in m.columns
            )
            if not has_composite and not country_indexed:
                rep.add(YEL, "DBA31", "database", m.rel_path,
                        f"table '{m.table}' has country_code + created_at but no composite index",
                        intended="add composite index (country_code, created_at)", line=m.line)
                reported += 1
        if reported >= 200:
            break

    # DBA32: OFFSET pagination — only a real concern on HOT/large tables
    # (deep OFFSET is slow there). Flagging every .offset() across services/
    # controllers produces massive advisory noise for correct, low-traffic
    # endpoints. Restrict to request-path routers that touch hot tables.
    if (backend_dir / "routers").exists():
        offset_re = re.compile(r"\.offset\(|\bOFFSET\b", re.I)
        reported = 0
        routers_dir = backend_dir / "routers"
        for f in iter_text_files(routers_dir, _db_eff):
            if f.suffix.lower() != ".py":
                continue
            parts = {p.lower() for p in f.parts}
            if "tests" in parts:
                continue
            text = read_text(f)
            if not text:
                continue
            low = text.lower()
            if not any(t in low for t in DBA_HOT_TABLES):
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if offset_re.search(line):
                    rep.add(YEL, "DBA32", "backend", rel(f, repo),
                            "OFFSET pagination on hot table detected",
                            intended="use cursor-based (keyset) pagination for hot lists", line=i)
                    reported += 1
                    break
            if reported >= 150:
                break

    # DBA33: Finance boundary
    if backend_dir.exists():
        finance_write_re = re.compile(
            r"(?i)(session\.add\(\s*(Journal|Ledger|ApLedger|ArLedger|Payout)\w*"
            r"|\.query\(\s*(JournalEntry|LedgerEntry)\w*\s*\)\s*\.(add|update|delete)"
            r"|insert\(\s*(journal_entries|ap_ledger_entries|ar_ledger_entries"
            r"|ledger_entries|payouts)\b)"
        )
        reported = 0
        for f in iter_text_files(backend_dir, _db_eff):
            if f.suffix.lower() != ".py":
                continue
            parts = [p.lower() for p in f.parts]
            if any(x in parts for x in ("tests", "scripts", "alembic", "data", "monitoring", "docs")):
                continue
            path_low = str(f).replace("\\", "/").lower()
            allowed = (
                "services/finance" in path_low
                or "services/treasury" in path_low
                or "ledger_service" in f.stem.lower()
                or "treasury_service" in f.stem.lower()
            )
            if allowed:
                continue
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if finance_write_re.search(line):
                    rep.add(RED, "DBA33", "finance", rel(f, repo),
                            "finance write outside ledger/treasury service boundary",
                            intended="finance writes must go through ledger service", line=i)
                    reported += 1
                    break
            if reported >= 100:
                break

    # DBA35: Idempotency
    if "processed_webhook_events" not in all_tables:
        rep.add(YEL, "DBA35", "database", "backend/domains/",
                "processed_webhook_events table not detected",
                intended="external/write actions must be idempotent")

    # ── DBA14/15/16: Dev/Prod gate ──
    db_files = [
        backend_dir / "infrastructure" / "database" / "database.py",
        backend_dir / "infrastructure" / "config.py",
        backend_dir / "config.py",
    ]
    db_texts: list[str] = []
    for p in db_files:
        if p.exists():
            t = read_text(p)
            if t:
                db_texts.append(t)
    combined_db = "\n".join(db_texts)
    gate_re = re.compile(
        r"APP_ENV|development|production|is_development|settings\.ENV"
        r"|getenv\(['\"]APP_ENV",
        re.I,
    )
    if "sqlite" in combined_db.lower() and not gate_re.search(combined_db):
        rep.add(YEL, "DBA16", "dev", "backend/db/database.py",
                "SQLite usage detected without visible environment gate",
                intended="SQLite is dev-only; production must use PostgreSQL")
    if re.search(r"echo\s*=\s*True", combined_db) and not gate_re.search(combined_db):
        rep.add(YEL, "DBA14", "dev", "backend/db/database.py",
                "SQL echo=True detected without visible dev gate",
                intended="enable echo only in development")
    # Pool may be configured literally (pool_size=5) OR via settings
    # (settings.db_pool_size / settings.db_max_overflow), which is exactly the
    # recommended pattern. Detect both.
    settings_pool = bool(re.search(r"\bdb_pool_size\b|\bdb_max_overflow\b", combined_db))
    pool_size_m = re.search(r"pool_size\s*=\s*(\d+)", combined_db)
    max_overflow_m = re.search(r"max_overflow\s*=\s*(\d+)", combined_db)
    if not pool_size_m and not settings_pool:
        rep.add(YEL, "DBA15", "production", "backend/db/database.py",
                "pool_size not detected",
                intended="app pool should be 5 with max_overflow 10 behind PgBouncer")
    elif pool_size_m and max_overflow_m:
        ps = int(pool_size_m.group(1))
        mo = int(max_overflow_m.group(1))
        if ps != 5 or mo != 10:
            rep.add(YEL, "DBA15", "production", "infrastructure/database/database.py",
                    f"connection pool config detected pool_size={ps}, max_overflow={mo}",
                    intended="grounded target: pool_size=5, max_overflow=10 behind PgBouncer")

    # ── DBA21: AI staging ──
    missing_ai = sorted(DBA_EXPECTED_AI_TABLES - all_tables)
    if missing_ai:
        rep.add(YEL, "DBA21", "ai", "backend/domains/",
                f"missing AI staging/audit tables: {', '.join(missing_ai)}",
                intended="AI writes to staging/ai_* tables; commit explicitly with audit")
    if backend_dir.exists():
        ai_direct_re = re.compile(
            r"session\.add\(\s*Product|add\(\s*Product\(|insert\(\s*products\b"
            r"|\.query\(\s*Product\s*\)\s*\.(update|delete)"
        )
        ai_reported = 0
        for f in iter_text_files(backend_dir, _db_eff):
            if f.suffix.lower() != ".py":
                continue
            parts = [p.lower() for p in f.parts]
            if "ai" not in parts and "ai" not in f.stem.lower():
                continue
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if ai_direct_re.search(line):
                    rep.add(YEL, "DBA21", "ai", rel(f, repo),
                            "possible direct AI write into business table",
                            intended="AI output must go to staging first, then explicit commit",
                            line=i)
                    ai_reported += 1
                    break
            if ai_reported >= 80:
                break

    # ── DBA27: Broken migrations ──
    versions_dir = backend_dir / "alembic" / "versions"
    if versions_dir.exists():
        rev_re = re.compile(
            r"^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]", re.M
        )
        broken_reported = 0
        for f in sorted(versions_dir.glob("*.py")):
            text = read_text(f)
            if text is None:
                rep.add(RED, "DBA27", "migrations", rel(f, repo),
                        "migration file could not be read",
                        intended="repair or remove this migration")
                broken_reported += 1
                continue
            if parse_safe(f) is None:
                rep.add(RED, "DBA27", "migrations", rel(f, repo),
                        "migration file is not valid Python (broken head risk)",
                        intended="fix syntax/import error; ADR-018 requires a runnable Alembic chain")
                broken_reported += 1
            if not rev_re.search(text):
                rep.add(RED, "DBA27", "migrations", rel(f, repo),
                        "migration file missing revision identifier",
                        intended="every Alembic migration must declare revision/down_revision")
                broken_reported += 1
            if re.search(r"\bUnion\b", text):
                if not re.search(
                    r"from\s+typing\s+import.*\bUnion\b|import\s+typing", text
                ):
                    rep.add(YEL, "DBA27", "migrations", rel(f, repo),
                            "suspicious Union reference without visible typing import",
                            intended="verify this migration imports Union correctly")
                    broken_reported += 1
            if broken_reported >= 100:
                break

    # ── DBA12-ext: Destructive migrations ──
    if versions_dir.exists():
        # Only table-destroying operations violate the "keep all tables"
        # constitution. op.drop_column / op.drop_constraint are routine, safe
        # schema evolutions and must not be flagged as destructive.
        destructive_re = re.compile(
            r"op\.drop_table\(|op\.rename_table\(",
            re.I,
        )
        dest_reported = 0
        for f in sorted(versions_dir.glob("*.py")):
            text = read_text(f)
            if not text:
                continue
            for i, line in enumerate(text.splitlines(), 1):
                if destructive_re.search(line):
                    rep.add(YEL, "DBA12", "migrations", rel(f, repo),
                            "destructive migration operation detected",
                            intended="constitution: keep all tables; drop/rename only via controlled ADR",
                            line=i)
                    dest_reported += 1
                    break
            if dest_reported >= 100:
                break

    # ── DBA28: Migration contract tests ──
    tests_dir = backend_dir / "tests"
    if not tests_dir.exists():
        rep.add(YEL, "DBA28", "migrations", "backend/tests/",
                "backend/tests/ directory not found",
                intended="add database contract/integration tests per 01_DATABASE §8.2")
    else:
        test_files = [p.name.lower() for p in tests_dir.rglob("*.py") if p.is_file()]
        if not any("test_database" in name for name in test_files):
            rep.add(YEL, "DBA28", "migrations", "backend/tests/",
                    "test_database.py not found",
                    intended="add database contract tests asserting schema shape")
        if not any(("migration" in n or "contract" in n or "alembic" in n) for n in test_files):
            rep.add(YEL, "DBA28", "migrations", "backend/tests/",
                    "no migration/contract test file detected",
                    intended="every migration should have a contract test")

    # ── DBA18-ext: Audit log shape ──
    for m in models:
        if not m.table or m.table.lower() != "audit_logs":
            continue
        cols = {c.name.lower() for c in m.columns}
        missing_audit: list[str] = []
        for col in ("log_type", "actor", "entity", "country_code"):
            if col not in cols:
                missing_audit.append(col)
        has_payload = any(
            c in cols
            for c in ("old_value_json", "new_value_json", "old_new_value_json", "payload_json")
        )
        if not has_payload:
            missing_audit.append("old/new_value_json")
        if missing_audit:
            rep.add(YEL, "DBA18", "database", m.rel_path,
                    f"audit_logs model missing expected columns: {', '.join(missing_audit)}",
                    intended="audit_logs should have log_type, actor, entity, old/new_value_json, country_code",
                    line=m.line)
        break

    # ── DBA23-ext: Partition specific tables ──
    alembic_dir = backend_dir / "alembic"
    if alembic_dir.exists():
        part_files: list[Path] = []
        vd = alembic_dir / "versions"
        ad = alembic_dir / "versions_archive"
        if vd.exists():
            part_files.extend(sorted(vd.glob("*.py")))
        if ad.exists():
            part_files.extend(sorted(ad.glob("*.py")))
        missing_part: list[str] = []
        for table in sorted(DBA_PARTITION_EXPECTED_TABLES):
            found = False
            for f in part_files:
                text = read_text(f)
                if not text:
                    continue
                low = text.lower()
                if table in low and ("partition by" in low or "postgresql_partition_by" in low):
                    found = True
                    break
            if not found:
                missing_part.append(table)
        if missing_part:
            rep.add(YEL, "DBA23", "production", "backend/alembic/versions/",
                    f"no partition signal for expected hot tables: {', '.join(missing_part)}",
                    intended="add monthly range partitioning for journal_entries/audit_logs/chat_messages/shipment_events")

    # ── DBA34: RLS fail-closed ──
    if rls.sql_files:
        force_found = False
        for f in rls.sql_files:
            text = read_text(f) or ""
            if re.search(r"FORCE\s+ROW\s+LEVEL\s+SECURITY", text, re.I):
                force_found = True
                break
        if not force_found:
            rep.add(YEL, "DBA34", "security", "infrastructure/database/pg_rls_policies.sql",
                    "no FORCE ROW LEVEL SECURITY signal detected",
                    intended="use FORCE ROW LEVEL SECURITY so table owners cannot bypass RLS")
        registry_found = False
        for f in iter_text_files(backend_dir, _db_eff):
            text = read_text(f)
            if text and "COUNTRY_AWARE_TABLES" in text:
                registry_found = True
                break
        if not registry_found:
            rep.add(YEL, "DBA34", "security", "backend/",
                    "no COUNTRY_AWARE_TABLES registry signal detected",
                    intended="maintain an explicit RLS table registry")

    # ── DBA36: Archive/retention ──
    if alembic_dir.exists():
        archive_found = False
        for f in alembic_dir.rglob("*.py"):
            text = read_text(f)
            if not text:
                continue
            low = text.lower()
            if "archive" in low or "detach_partition" in low or "retention" in low:
                archive_found = True
                break
        if not archive_found:
            rep.add(YEL, "DBA36", "production", "backend/alembic/",
                    "no archive/retention signal detected in migrations",
                    intended="implement archive schema / partition detach / retention policy per §2.8")

    # ── DBA37: Data dictionary ERD ──
    gen_dd = backend_dir / "scripts" / "generate_data_dictionary.py"
    if gen_dd.exists():
        dd_text = read_text(gen_dd) or ""
        if not re.search(r"erDiagram|mermaid|\.mmd", dd_text, re.I):
            rep.add(YEL, "DBA37", "database", rel(gen_dd, repo),
                    "data dictionary generator does not appear to emit Mermaid ERD output",
                    intended="extend generator to emit FK edges + Mermaid erDiagram per §6.4")

    # ── DBA24: Production checklist ──
    gi = repo / ".gitignore"
    gi_text = read_text(gi) or ""
    gi_ok = gi.exists() and "*.db" in gi_text and ".env" in gi_text
    if not gi_ok:
        rep.add(YEL, "DBA24", "production", ".gitignore",
                "root .gitignore does not protect DB/env files",
                intended="add *.db* and .env to .gitignore")
    env_example_ok = (repo / ".env.example").exists() or (backend_dir / ".env.example").exists()
    if not env_example_ok:
        rep.add(YEL, "DBA24", "production", ".env.example",
                ".env.example not found",
                intended="repository should contain .env.example, never real .env")
    monitoring_ok = (backend_dir / "monitoring").exists() or (repo / "monitoring").exists()
    if not monitoring_ok:
        rep.add(YEL, "DBA24", "production", "monitoring/",
                "monitoring directory not found",
                intended="add Prometheus/Grafana/Promtail stack")
    dict_gen_ok = (backend_dir / "scripts" / "generate_data_dictionary.py").exists()
    if not dict_gen_ok:
        rep.add(YEL, "DBA24", "production", "backend/scripts/generate_data_dictionary.py",
                "data dictionary generator not found",
                intended="add backend/scripts/generate_data_dictionary.py")

    return models, minfo, rls

# ============================================================================
# SECTION 50: DESIGN AUDIT — CONSTANTS & COLOR MATH
# ============================================================================

DS_SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"}
DS_CSS_EXT = {".css", ".scss"}
DS_MAX_READ_BYTES = 2_000_000

DS_PALETTE_FILE_RE = re.compile(r"(^|[/\\])(colors|tokens|theme|palette)\.(ts|tsx|js|jsx)$", re.I)
DS_CONFIG_FILE_RE = re.compile(
    r"(tailwind|postcss|metro|babel|next|eslint|jest|playwright|sentry)\.config\.", re.I)

DS_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
DS_RGB_RE = re.compile(r"rgba?\(\s*[\d.]+[,\s]+[\d.]+[,\s]+[\d.]+(?:[,\s]+[\d.]+)?\s*\)", re.I)
DS_HSL_RE = re.compile(r"hsla?\(\s*[\d.]+[^\)]*\)", re.I)
DS_TW_COLOR_RE = re.compile(r"([\w$-]+)\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]")
DS_CSS_VAR_RE = re.compile(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^\)]+\)|hsla?\([^\)]+\))", re.I)

DS_STYLE_OBJ_RE = re.compile(r"style\s*=\s*\{\{")
DS_STYLE_TAG_RE = re.compile(r"<style[\s>/]", re.I)
DS_IMPORTANT_RE = re.compile(r"!\s*important", re.I)
DS_ZINDEX_RE = re.compile(r"z-index\s*:\s*(\d+)", re.I)
DS_ARB_RE = re.compile(
    r"(?<![\w-])(bg|text|border|from|to|via|ring|decoration|placeholder|fill|stroke|outline|divide"
    r"|w|h|size|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|rounded|z|shadow"
    r"|top|left|right|bottom|inset|leading|tracking|space-x|space-y|min-w|max-w|min-h|max-h|basis)"
    r"-\[([^\]]+)\]")
DS_ARB_COLOR_PREFIXES = {"bg", "text", "border", "from", "to", "via", "ring",
                          "decoration", "placeholder", "fill", "stroke", "outline", "divide"}
DS_TW_SCREENS = {320, 375, 425, 640, 768, 820, 1024, 1280, 1440, 1536, 1920, 2560}
DS_NAMED_COLORS = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#008000",
    "blue": "#0000ff", "gray": "#808080", "grey": "#808080", "orange": "#ffa500",
    "purple": "#800080", "yellow": "#ffff00", "pink": "#ffc0cb", "teal": "#008080",
    "cyan": "#00ffff", "transparent": None, "inherit": None, "currentcolor": None,
}
DS_COLOR_PROPS = {"color", "backgroundColor", "borderColor", "tintColor", "background", "fill", "stroke"}

DS_SPACING_PROPS = {
    "padding", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight",
    "paddingHorizontal", "paddingVertical", "margin", "marginTop", "marginBottom",
    "marginLeft", "marginRight", "marginHorizontal", "marginVertical",
    "width", "height", "top", "left", "right", "bottom", "gap", "rowGap",
    "columnGap", "borderWidth", "borderRadius", "fontSize", "lineHeight",
    "minWidth", "maxWidth", "minHeight", "maxHeight", "flexBasis",
}

DS_STYLE_PROP_RE = re.compile(r"([A-Za-z]\w*)\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|([\d.]+))")
DS_SHADOW_CSS_RE = re.compile(r"(?:box-shadow|text-shadow)\s*:\s*([^;}{]+)", re.I)
DS_RADIUS_CSS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.I)
DS_FONTSIZE_CSS_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.I)
DS_FONTFAM_CSS_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
DS_MQ_RE = re.compile(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*(\d+)px", re.I)
DS_MS_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)ms\b")
DS_PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
DS_APPLY_RE = re.compile(r"@apply\b")

DS_NEAR_DUP_THRESHOLD = 14.0
DS_NEAR_TOKEN_THRESHOLD = 10.0

def ds_hex_to_rgb(h: str):
    h = h.strip().lstrip("#").lower()
    if len(h) == 3: h = "".join(c * 2 for c in h)
    elif len(h) == 4: h = "".join(c * 2 for c in h[:3])
    elif len(h) == 8: h = h[:6]
    if len(h) != 6: return None
    try: return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError: return None

def ds_to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)

def ds_hsl_to_rgb(h: float, s: float, l: float):
    s /= 100.0
    l /= 100.0
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs(((h / 60.0) % 2) - 1))
    m = l - c / 2
    if h < 60: r, g, b = c, x, 0
    elif h < 120: r, g, b = x, c, 0
    elif h < 180: r, g, b = 0, c, x
    elif h < 240: r, g, b = 0, x, c
    elif h < 300: r, g, b = x, 0, c
    else: r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

def ds_parse_color(lit: str):
    lit = lit.strip().lower()
    if lit.startswith("#"): return ds_hex_to_rgb(lit)
    m = re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", lit)
    if m:
        try: return tuple(min(255, int(float(m.group(i)))) for i in (1, 2, 3))
        except ValueError: return None
    m = re.match(r"hsla?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)", lit)
    if m:
        try: return ds_hsl_to_rgb(float(m.group(1)), float(m.group(2)), float(m.group(3)))
        except ValueError: return None
    if lit in DS_NAMED_COLORS:
        v = DS_NAMED_COLORS[lit]
        return ds_hex_to_rgb(v) if v else None
    return None

def ds_color_distance(a, b) -> float:
    rmean = (a[0] + b[0]) / 2.0
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return ((2 + rmean / 256.0) * dr * dr + 4 * dg * dg + (2 + (255 - rmean) / 256.0) * db * db) ** 0.5

def ds_chan(c: float) -> float:
    c /= 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

def ds_rel_luminance(rgb) -> float:
    return 0.2126 * ds_chan(rgb[0]) + 0.7152 * ds_chan(rgb[1]) + 0.0722 * ds_chan(rgb[2])

def ds_contrast_ratio(a, b) -> float:
    la, lb = ds_rel_luminance(a), ds_rel_luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

def ds_cluster_colors(hexes: list[str], threshold: float = DS_NEAR_DUP_THRESHOLD):
    rgb_map = {h: ds_hex_to_rgb(h) for h in hexes}
    clusters = []
    used = set()
    for h in hexes:
        if h in used or rgb_map[h] is None: continue
        cl = [h]
        used.add(h)
        for o in hexes:
            if o in used or rgb_map[o] is None: continue
            if ds_color_distance(rgb_map[h], rgb_map[o]) <= threshold:
                cl.append(o)
                used.add(o)
        clusters.append(cl)
    return clusters

@dataclass
class DSFileProfile:
    path: str = ""
    workspace: str = ""
    kind: str = "component"
    colors: dict = field(default_factory=lambda: defaultdict(int))
    off_palette: dict = field(default_factory=lambda: defaultdict(int))
    inline_style_blocks: int = 0
    style_tag: int = 0
    important: int = 0
    arb_color: dict = field(default_factory=lambda: defaultdict(int))
    arb_size: int = 0
    arb_z: list = field(default_factory=list)
    arb_radius: list = field(default_factory=list)
    px_values: int = 0
    zmagic: list = field(default_factory=list)
    shadows: set = field(default_factory=set)
    radii: set = field(default_factory=set)
    font_sizes: set = field(default_factory=set)
    font_families: set = field(default_factory=set)
    durations: set = field(default_factory=set)
    breakpoints_off: set = field(default_factory=set)
    contrast_pairs: list = field(default_factory=list)
    css_in_js: int = 0
    apply_count: int = 0
    score: int = 0


# ============================================================================
# SECTION 51: DESIGN AUDIT — PALETTE DISCOVERY
# ============================================================================

def ds_discover_palette(frontend: Path) -> dict:
    tokens: dict[str, str] = {}
    value_index: dict[str, str] = {}
    sources: list[str] = []
    if not frontend.exists():
        return {"tokens": tokens, "value_index": value_index, "sources": sources}
    eff = _ACTIVE_EFF or {"ignore_dirs": DEFAULT_IGNORE_DIRS}
    for d, entries in walk_dirs(frontend, eff.get("ignore_dirs", DEFAULT_IGNORE_DIRS)):
        for e in entries:
            if not e.is_file(): continue
            if e.suffix.lower() not in DS_SOURCE_EXT | DS_CSS_EXT: continue
            text = read_text(e)
            if not text: continue
            name = e.name
            if name.startswith("tailwind.config"):
                sources.append(rel(e, frontend.parent.parent))
                for m in DS_TW_COLOR_RE.finditer(text):
                    key, val = m.group(1), m.group(2)
                    rgb = ds_hex_to_rgb(val)
                    if rgb is None: continue
                    hx = ds_to_hex(rgb)
                    tokens.setdefault(key, hx)
                    value_index.setdefault(hx, key)
            elif e.suffix.lower() in DS_CSS_EXT:
                for m in DS_CSS_VAR_RE.finditer(text):
                    var_name, raw = m.group(1), m.group(2)
                    rgb = ds_parse_color(raw)
                    if rgb is None: continue
                    hx = ds_to_hex(rgb)
                    tokens.setdefault(var_name, hx)
                    value_index.setdefault(hx, var_name)
            elif DS_PALETTE_FILE_RE.search(str(e)):
                sources.append(rel(e, frontend.parent.parent))
                for m in DS_TW_COLOR_RE.finditer(text):
                    key, val = m.group(1), m.group(2)
                    rgb = ds_hex_to_rgb(val)
                    if rgb is None: continue
                    hx = ds_to_hex(rgb)
                    tokens.setdefault(key, hx)
                    value_index.setdefault(hx, key)
    return {"tokens": tokens, "value_index": value_index, "sources": sources}

def ds_make_classifier(palette: dict):
    value_index = palette["value_index"]
    pal_rgbs = []
    for hx in value_index:
        rgb = ds_hex_to_rgb(hx)
        if rgb: pal_rgbs.append(rgb)
    cache: dict[str, str] = {}
    def classify(lit_hex: str) -> str:
        if lit_hex in cache: return cache[lit_hex]
        rgb = ds_hex_to_rgb(lit_hex)
        if rgb is None:
            cache[lit_hex] = "off"; return "off"
        if lit_hex in value_index:
            cache[lit_hex] = "token"; return "token"
        best = 9999.0
        for pr in pal_rgbs:
            d = ds_color_distance(rgb, pr)
            if d < best: best = d
            if best <= DS_NEAR_TOKEN_THRESHOLD: break
        verdict = "near-token" if best <= DS_NEAR_TOKEN_THRESHOLD else "off"
        cache[lit_hex] = verdict
        return verdict
    return classify


# ============================================================================
# SECTION 53: DESIGN FILE SCANNERS
# ============================================================================

def ds_extract_style_objects(text: str) -> list[tuple[int, str]]:
    """Best-effort extraction of style={{ ... }} object bodies."""
    out = []
    for m in DS_STYLE_OBJ_RE.finditer(text):
        start = m.end() - 1
        depth = 0
        i = start
        while i < len(text):
            ch = text[i]
            if ch == "{": depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0: break
            i += 1
        out.append((m.start(), text[start + 1:i]))
    return out




# ============================================================================
# SECTION 52: DESIGN AUDIT — RUN ALL CHECKS
# ============================================================================

def ds_run_all_checks(repo: Path, rep: Report) -> dict:
    """Run ALL design audit checks. Returns summary data."""
    frontend = repo / "frontend"
    if not frontend.exists():
        return {"palette_tokens": 0, "coverage": 100.0}

    palette = ds_discover_palette(frontend)
    classify = ds_make_classifier(palette)
    token_count = len(palette["tokens"])

    # DS12: Token source health
    if token_count == 0:
        rep.add(RED, "DS12", "design", rel(frontend, repo),
                "no design token source found",
                intended="create shared/src/tokens/colors.ts + tailwind.config theme.extend.colors")
    elif token_count < 5:
        rep.add(YEL, "DS12", "design", rel(frontend, repo),
                f"weak token source: only {token_count} color tokens",
                intended="define full brand palette as tokens")

    # Scan files
    profiles: list[DSFileProfile] = []
    eff = _ACTIVE_EFF or {"ignore_dirs": DEFAULT_IGNORE_DIRS}
    for d, entries in walk_dirs(frontend, eff.get("ignore_dirs", DEFAULT_IGNORE_DIRS)):
        for e in entries:
            if not e.is_file():
                continue
            if e.suffix.lower() not in DS_SOURCE_EXT | DS_CSS_EXT:
                continue
            if e.suffix.lower() == ".ts" and e.name.endswith(".d.ts"):
                continue
            if DS_CONFIG_FILE_RE.search(e.name):
                continue
            if DS_PALETTE_FILE_RE.search(str(e)):
                continue
            if ".min." in e.name:
                continue
            text = read_text(e)
            if not text:
                continue
            try:
                if e.stat().st_size > DS_MAX_READ_BYTES:
                    continue
            except OSError:
                continue
            try:
                parts = e.relative_to(frontend).parts
                ws = parts[0] if parts and parts[0] in ("web_app", "mobile_app", "shared") else "frontend-root"
            except ValueError:
                ws = "frontend-root"

            p = DSFileProfile(path=rel(e, repo), workspace=ws,
                              kind="css" if e.suffix.lower() in DS_CSS_EXT else "component")
            lines = text.splitlines()

            # Color literals
            for rx in (DS_HEX_RE, DS_RGB_RE, DS_HSL_RE):
                for m in rx.finditer(text):
                    line_no = text.count("\n", 0, m.start()) + 1
                    try:
                        line = lines[line_no - 1]
                        if line.strip().startswith("//") or line.strip().startswith("*"):
                            continue
                    except IndexError:
                        pass
                    rgb = ds_parse_color(m.group(0))
                    if rgb is None:
                        continue
                    hx = ds_to_hex(rgb)
                    p.colors[hx] += 1
                    if classify(hx) == "off":
                        p.off_palette[hx] += 1

            # Inline styles
            p.inline_style_blocks = len(DS_STYLE_OBJ_RE.findall(text))
            p.style_tag = len(DS_STYLE_TAG_RE.findall(text))
            p.important = len(DS_IMPORTANT_RE.findall(text))
            p.css_in_js = len(re.findall(
                r"from\s+['\"](?:styled-components|@emotion/styled|@emotion/react)['\"]", text))

            # Inline style objects — extract properties for contrast/spacing/typography
            for _pos, body in ds_extract_style_objects(text):
                line_no = text.count("\n", 0, _pos) + 1
                fg_rgb = None
                bg_rgb = None
                for pm in DS_STYLE_PROP_RE.finditer(body):
                    prop = pm.group(1)
                    val = pm.group(2) or pm.group(3) or pm.group(4) or ""
                    if not val:
                        continue
                    if prop in DS_COLOR_PROPS:
                        rgb_val = ds_parse_color(val)
                        if rgb_val:
                            hx = ds_to_hex(rgb_val)
                            p.colors[hx] += 1
                            if classify(hx) == "off":
                                p.off_palette[hx] += 1
                            if prop == "color":
                                fg_rgb = rgb_val
                            elif prop in ("backgroundColor", "background"):
                                bg_rgb = rgb_val
                    elif prop in DS_SPACING_PROPS:
                        if pm.group(4) or "px" in val:
                            p.px_values += 1
                    if prop == "zIndex":
                        try:
                            z = int(float(val))
                            if z >= 1000:
                                p.zmagic.append(z)
                        except ValueError:
                            pass
                    elif prop == "borderRadius":
                        p.radii.add(val.strip())
                    elif prop in ("boxShadow", "shadow"):
                        p.shadows.add(re.sub(r"\s+", " ", val.strip()))
                    elif prop == "fontSize":
                        p.font_sizes.add(val.strip())
                    elif prop == "fontFamily":
                        p.font_families.add(val.strip().strip("'\""))
                    elif prop in ("transition", "animation"):
                        for dm in DS_MS_RE.finditer(val):
                            p.durations.add(f"{dm.group(1)}ms")
                # DS15: contrast check within same style block
                if fg_rgb and bg_rgb:
                    ratio = ds_contrast_ratio(fg_rgb, bg_rgb)
                    if ratio < 3.2:
                        p.contrast_pairs.append(
                            (round(ratio, 2), ds_to_hex(fg_rgb), ds_to_hex(bg_rgb), line_no))

            # Tailwind arbitrary values
            for m in DS_ARB_RE.finditer(text):
                prefix, val = m.group(1), m.group(2)
                is_color_val = val.startswith("#") or "rgb" in val.lower() or "hsl" in val.lower()
                if prefix in DS_ARB_COLOR_PREFIXES and is_color_val:
                    p.arb_color[val.lower()] += 1
                elif prefix == "z":
                    p.arb_z.append(val)
                    try:
                        if int(val) >= 1000:
                            p.zmagic.append(int(val))
                    except ValueError:
                        pass
                elif prefix == "rounded":
                    p.arb_radius.append(val)
                    p.radii.add(val)
                elif prefix == "shadow":
                    p.shadows.add(f"tw:{val}")
                else:
                    if re.search(r"\d", val):
                        p.arb_size += 1

            # CSS-specific scans
            if p.kind == "css":
                for m in DS_ZINDEX_RE.finditer(text):
                    z = int(m.group(1))
                    if z >= 1000:
                        p.zmagic.append(z)
                for m in DS_SHADOW_CSS_RE.finditer(text):
                    p.shadows.add(re.sub(r"\s+", " ", m.group(1).strip()))
                for m in DS_RADIUS_CSS_RE.finditer(text):
                    p.radii.add(re.sub(r"\s+", " ", m.group(1).strip()))
                for m in DS_FONTSIZE_CSS_RE.finditer(text):
                    p.font_sizes.add(m.group(1).strip())
                for m in DS_FONTFAM_CSS_RE.finditer(text):
                    p.font_families.add(m.group(1).strip())
                for m in DS_MS_RE.finditer(text):
                    p.durations.add(f"{m.group(1)}ms")
                for m in DS_MQ_RE.finditer(text):
                    bp = int(m.group(1))
                    if bp not in DS_TW_SCREENS:
                        p.breakpoints_off.add(bp)
                p.apply_count = len(DS_APPLY_RE.findall(text))
                p.px_values += len(DS_PX_RE.findall(text))

            # Score
            s = 0
            s += p.inline_style_blocks * 3
            s += p.style_tag * 25
            s += p.important * 8
            s += sum(p.arb_color.values()) * 5
            s += p.arb_size * 1
            s += len(p.zmagic) * 20
            s += sum(p.off_palette.values()) * 4
            s += min(p.px_values, 60) * 1
            s += min(len(p.shadows), 10) * 2
            s += min(len(p.radii), 10) * 2
            s += min(len(p.font_sizes), 10) * 2
            s += min(len(p.durations), 10)
            s += len(p.breakpoints_off) * 3
            s += sum(1 for r, *_ in p.contrast_pairs if r < 2.0) * 20
            s += sum(1 for r, *_ in p.contrast_pairs if 2.0 <= r < 3.2) * 6
            s += p.css_in_js * 10
            p.score = s
            profiles.append(p)

    # Aggregate checks
    literal_usage: dict[str, int] = defaultdict(int)
    total_occurrences = 0
    on_palette = 0
    for p in profiles:
        for hx, cnt in p.colors.items():
            literal_usage[hx] += cnt
            total_occurrences += cnt
            if classify(hx) != "off":
                on_palette += cnt
    coverage = (on_palette / total_occurrences * 100) if total_occurrences else 100.0

    # DS03: Off-palette
    off_literals = sorted((hx for hx in literal_usage if classify(hx) == "off"),
                          key=lambda hx: (-literal_usage[hx], hx))
    for hx in off_literals[:30]:
        rep.add(YEL, "DS03", "design", "frontend/",
                f"off-palette color {hx} used {literal_usage[hx]}×",
                intended="replace with nearest design token")

    # DS01: Inline styles
    for p in sorted((p for p in profiles if p.inline_style_blocks >= 3),
                    key=lambda p: -p.inline_style_blocks)[:60]:
        rep.add(YEL, "DS01", p.workspace, p.path,
                f"{p.inline_style_blocks} inline style object(s)",
                intended="move to Tailwind classes / StyleSheet.create")

    # DS02: Style tags
    for p in (p for p in profiles if p.style_tag):
        rep.add(RED, "DS02", p.workspace, p.path,
                f"{p.style_tag} <style> tag(s) inside component",
                intended="delete; styles belong in design system")

    # DS05: Arbitrary Tailwind
    for p in sorted((p for p in profiles if p.arb_color),
                    key=lambda p: -sum(p.arb_color.values()))[:40]:
        worst = ", ".join(sorted(p.arb_color, key=lambda v: -p.arb_color[v])[:4])
        rep.add(YEL, "DS05", p.workspace, p.path,
                f"{sum(p.arb_color.values())} arbitrary Tailwind color(s): {worst}",
                intended="use palette classes instead of bg-[#...]")

    # DS06: !important
    for p in sorted((p for p in profiles if p.important), key=lambda p: -p.important)[:20]:
        rep.add(RED, "DS06", p.workspace, p.path,
                f"!important used {p.important}×",
                intended="fix specificity; never !important in design system")

    # DS10: Magic z-index
    for p in sorted((p for p in profiles if p.zmagic), key=lambda p: -max(p.zmagic))[:15]:
        rep.add(RED, "DS10", p.workspace, p.path,
                f"magic z-index: {', '.join(str(z) for z in sorted(set(p.zmagic))[:5])}",
                intended="use z-index scale token; never 9999+")

    # DS14: Mixed styling
    for p in (p for p in profiles if p.css_in_js):
        rep.add(YEL, "DS14", p.workspace, p.path,
                "CSS-in-JS library alongside Tailwind",
                intended="pick ONE system (Tailwind)")

    # DS17: Unused tokens
    if token_count:
        used_hexes = set(literal_usage.keys())
        unused = [name for name, hx in palette["tokens"].items() if hx not in used_hexes]
        if unused:
            rep.add(YEL, "DS17", "design", ", ".join(palette["sources"][:2]) or "palette",
                    f"{len(unused)} palette token(s) never referenced: " + ", ".join(sorted(unused)[:12]),
                    intended="remove dead tokens or use them")

    # DS04/DS13: Color drift clusters
    distinct_colors = sorted(literal_usage.keys())
    clusters = ds_cluster_colors(distinct_colors)
    for cl in clusters:
        if len(cl) < 2:
            continue
        total = sum(literal_usage.get(hx, 0) for hx in cl)
        if total < 3:
            continue
        detail = " ≈ ".join(f"{hx} (×{literal_usage.get(hx, 0)})" for hx in sorted(cl))
        rep.add(YEL, "DS04", "design", "frontend/",
                f"color drift ({total}× total): {detail}",
                intended="pick ONE token; these are visually the same color")

    # DS07: Typography
    all_font_sizes: set[str] = set()
    all_font_families: set[str] = set()
    for p in profiles:
        all_font_sizes |= p.font_sizes
        all_font_families |= p.font_families
    if len(all_font_sizes) > 8:
        rep.add(YEL, "DS07", "design", "frontend/",
                f"{len(all_font_sizes)} distinct hardcoded font sizes",
                intended="collapse onto a type scale; max ~8 steps")
    if len(all_font_families) > 2:
        rep.add(YEL, "DS07", "design", "frontend/",
                f"{len(all_font_families)} distinct font families",
                intended="one brand family + one mono; reference from theme token")

    # DS08: Spacing/px
    total_px = sum(p.px_values for p in profiles)
    if total_px > 100:
        rep.add(YEL, "DS08", "design", "frontend/",
                f"{total_px} raw px values across files",
                intended="use the spacing scale (p-2/gap-4...) or design tokens")

    # DS09: Border radius
    all_radii: set[str] = set()
    for p in profiles:
        all_radii |= p.radii
    if len(all_radii) > 5:
        rep.add(YEL, "DS09", "design", "frontend/",
                f"{len(all_radii)} distinct border-radius values",
                intended="standardize on 3-4 radii tokens (sm/md/lg/full)")

    # DS11: Shadows
    all_shadows: set[str] = set()
    for p in profiles:
        all_shadows |= p.shadows
    if len(all_shadows) > 4:
        rep.add(YEL, "DS11", "design", "frontend/",
                f"{len(all_shadows)} distinct shadow definitions — no elevation system",
                intended="define 3 elevation tokens (shadow-sm/md/lg) and reuse them")

    # DS15: Low contrast pairs
    reported_contrast = 0
    for p in profiles:
        for ratio, fg, bg, line_no in p.contrast_pairs:
            sev = RED if ratio < 2.0 else YEL
            rep.add(sev, "DS15", p.workspace, p.path,
                    f"low contrast {ratio}:1 — text {fg} on {bg}",
                    intended="WCAG minimum 4.5:1 for body text; fix the token pairing",
                    line=line_no)
            reported_contrast += 1
            if reported_contrast >= 25:
                break
        if reported_contrast >= 25:
            break

    # DS16: Motion
    all_durations: set[str] = set()
    for p in profiles:
        all_durations |= p.durations
    if len(all_durations) > 6:
        rep.add(YEL, "DS16", "design", "frontend/",
                f"{len(all_durations)} distinct animation durations",
                intended="standardize on 2-3 motion tokens (150ms/250ms/400ms)")

    # DS18: Breakpoints
    all_bps: set[int] = set()
    for p in profiles:
        all_bps |= p.breakpoints_off
    if all_bps:
        rep.add(YEL, "DS18", "design", "frontend/",
                f"media-query breakpoints outside the screen scale: "
                + ", ".join(f"{bp}px" for bp in sorted(all_bps)[:10]),
                intended="use Tailwind screens (sm=640, md=768, lg=1024, xl=1280, 2xl=1536)")

    return {
        "palette_tokens": token_count,
        "coverage": coverage,
        "total_occurrences": total_occurrences,
        "distinct_colors": len(literal_usage),
        "profiles": profiles,
    }


# ============================================================================
# SECTION 60: HEALTH AUDIT — CONSTANTS
# ============================================================================

HL_HEAVY_PY_MODULES = {
    "torch", "transformers", "tensorflow", "cv2", "PIL", "pandas",
    "numpy", "sklearn", "matplotlib", "reportlab", "openpyxl",
    "weasyprint", "pdfkit", "imageio", "scipy", "xlsxwriter",
    "pdf2image", "pydub", "moviepy", "selenium", "playwright",
}
HL_BLOCKING_CALLS = {
    "time.sleep", "requests.get", "requests.post", "requests.put",
    "requests.patch", "requests.delete", "requests.head", "requests.options",
    "httpx.get", "httpx.post", "httpx.put", "httpx.patch", "httpx.delete",
    "urllib.request.urlopen", "subprocess.run", "subprocess.call",
    "subprocess.check_output", "shutil.copy", "shutil.copy2", "os.system",
}
HL_SYNC_IO_CALLS = {
    "open", "os.read", "os.write", "os.listdir", "os.walk",
    "os.stat", "os.path.exists", "shutil.rmtree", "shutil.move",
    "glob.glob", "json.load", "json.dump", "csv.reader",
}
HL_EXTERNAL_PREFIXES = (
    "requests.", "httpx.", "urllib.request", "aiohttp.",
    "boto3.", "botocore.", "stripe.", "smtplib.",
)
HL_SLEEP_ALLOWED = {"jobs", "scripts", "tasks", "monitoring", "tools"}





HL_CONSOLE_RE = re.compile(r"\bconsole\.(log|debug|info|warn|error)\b")
HL_DEBUGGER_RE = re.compile(r"\bdebugger\b")
HL_KEY_INDEX_RE = re.compile(r"key=\{(?:index|i|idx)\}")
HL_USEEFFECT_FETCH_RE = re.compile(
    r"useEffect\(\s*\(\s*\)\s*=>\s*\{[\s\S]*?(fetch\(|axios\.|api\.|\.get\(|\.post\()", re.I)
HL_DIRECT_DOM_RE = re.compile(r"\bdocument\.getElementById|\bdocument\.querySelector|\bwindow\.")
HL_HEAVY_FE_RE = re.compile(
    r"from\s+['\"](moment|lodash|@mui/material|@mui/icons-material|chart\.js|recharts|"
    r"date-fns|dayjs|xlsx|pdfjs-dist|three|d3|monaco-editor|antd)['\"]")
HL_DB_CALL_RE = re.compile(
    r"\b(db|session|conn|engine|cursor)\s*\.\s*"
    r"(query|execute|commit|rollback|flush|add|merge|bulk_save|bulk_insert|scalars|scalar)\s*\(",
    re.I,)

HL_CONN_INIT_PATTERNS = {"redis.Redis", "Redis", "redis_client", "StrictRedis"}
HL_TOOL_FILE_KEYWORDS = {"schema_audit", "check_", "validate_", "verify_", "diag_", "smoke_", "analyze_", "probe_"}
HL_INLINE_HANDLER_RE = re.compile(r"\bon[A-Z]\w*=\{?\s*\(\s*\)?\s*=>")
HL_MAP_RE = re.compile(r"\.map\(")
HL_ERROR_BOUNDARY_RE = re.compile(r"ErrorBoundary|componentDidCatch|getDerivedStateFromError")
HL_MEMO_RE = re.compile(r"\buseMemo\b|\buseCallback\b|\bReact\.memo\b")
HL_SUSPENSE_RE = re.compile(r"\bSuspense\b|\bReact\.lazy\b|\bnext/dynamic\b|\blazy\(")


HL_WEB_WORKER_RE = re.compile(r"\bnew\s+Worker\b|\buseWorker\b|worker_threads")
# ── Missing Health Constants ──


HL_FIX_PATTERNS: dict[str, dict[str, str]] = {
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

# ── Missing Health Helpers ──
def _hl_lines_example(lines: list[int], limit: int = 6) -> str:
    example = ", ".join(str(x) for x in lines[:limit])
    if len(lines) > limit:
        example += f" +{len(lines) - limit} more"
    return example

def _hl_is_request_path_layer(app_layer: str) -> bool:
    return app_layer in BACKEND_SCAN_LAYERS

def _hl_is_conn_init(call_name: str) -> bool:
    return any(pat in call_name for pat in HL_CONN_INIT_PATTERNS)

def hl_frontend_domain(path: str) -> str:
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
    if "lib" in parts: return "lib"
    if "hooks" in parts: return "hooks"
    if "shared" in parts: return "shared"
    return "other"

# ============================================================================
# SECTION 61: HEALTH AUDIT — PYTHON ANALYZER
# ============================================================================

def hl_analyze_python(f: Path, text: str, tree: ast.Module | None, repo: Path) -> dict:
    """Analyze a single Python file for ALL health issues in one pass."""
    a: dict[str, Any] = {
        "path": rel(f, repo), "line_count": len(text.splitlines()),
        "app_layer": "", "is_test": False, "is_script": False,
        "is_migration": False, "is_background": False,
        "is_scheduler": False, "is_seed": False, "is_tool": False,
        "print_lines": [], "bare_except": [], "swallowed": [], "broad": [],
        "blocking_async": [], "sync_io_async": [], "missing_timeout": [],
        "blocking_sleep": [], "sequential_http": [],
        "loop_db": [], "heavy_imports": [], "star_imports": [],
        "large_funcs": [], "missing_docs": [], "raw_sql": [],
        "hardcoded_secrets": [], "no_pagination": [], "no_response_model": [],
        "global_mutables": [], "has_logger": False, "has_request_id": False,
        "todo_count": 0, "commented_code_count": 0,
        "has_logging_basic_config": False,
        "json_heavy_funcs": [], "websocket_funcs": [],
        "cpu_bound": [], "timing_targets": [],
        "heavy_in_request": [], "large_list_comprehensions": [],
        "secret_log_lines": [],
        # Keep raw lines for SEC101 emission in hl_run_all_checks
        "_lines": text.splitlines(),
    }
    try:
        parts = [p.lower() for p in f.relative_to(repo).parts]
    except ValueError:
        parts = []
    a["is_test"] = any(x in parts for x in {"tests", "test", "e2e", "testing", "loadtests", "validation"})
    a["is_script"] = "scripts" in parts
    a["is_migration"] = "alembic" in parts and "versions" in parts
    a["is_background"] = any(x in parts for x in HL_SLEEP_ALLOWED)
    a["is_scheduler"] = any(x in a["path"].lower() for x in ("scheduler", "schedule", "cron", "worker"))
    a["is_seed"] = "seed" in a["path"].lower() or "migration_helpers" in a["path"].lower()
    a["is_tool"] = any(kw in a["path"].lower() for kw in HL_TOOL_FILE_KEYWORDS)
    if "backend" in parts:
        idx = parts.index("backend")
        if len(parts) > idx + 1:
            a["app_layer"] = parts[idx + 1]

    lines = text.splitlines()
    a["line_count"] = len(lines)

    # ── Line-level scans ──
    todo_re = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.I)
    comment_code_re = re.compile(
        r"^#\s*(import |from |def |class |if |for |while |return |try:|except|.*=\s*[\w\[\{])")
    log_secret_re = re.compile(
        r"(logger|logging|print|console).*?(password|secret|token|api_key|apikey|"
        r"authorization|cookie|jwt)", re.I)

    # ── SQL injection detection (parameterization-aware) ──
    # Matches: execute("..." + var), execute(f"..."), executemany with concat
    raw_sql_concat_re = re.compile(
        r"(execute|executemany)\s*\(\s*['\"].*?\+\s*\w", re.I)
    raw_sql_fstring_re = re.compile(
        r"(execute|executemany)\s*\(\s*f['\"]", re.I)
    raw_sql_percent_re = re.compile(
        r"(execute|executemany)\s*\(\s*['\"].*?%s", re.I)
    # text() with f-string interpolation
    raw_text_fstring_re = re.compile(r"text\s*\(\s*f['\"]", re.I)
    # Parameterized patterns (SAFE — do NOT flag)
    param_bind_re = re.compile(r":[\w]+|%\(\w+\)s|\?\s*[,)]", re.I)
    param_method_re = re.compile(r"\.params\s*\(|\.parameters\s*\(", re.I)

    secret_re = re.compile(
        r"""(password|secret|api_key|apikey|token|private_key)\s*=\s*['\"][^'\"]{8,}['\"]""", re.I)

    for i, raw_line in enumerate(lines, 1):
        stripped = raw_line.strip()
        if todo_re.search(stripped):
            a["todo_count"] += 1
        if stripped.startswith("#") and comment_code_re.search(stripped):
            a["commented_code_count"] += 1
        if not a["is_test"] and not a["is_script"] and log_secret_re.search(raw_line):
            a["secret_log_lines"].append(i)

        if not a["is_script"] and not a["is_test"] and not a["is_migration"]:
            # ── SQL injection: only flag if NOT parameterized ──
            is_raw_sql = False
            if raw_sql_concat_re.search(raw_line):
                is_raw_sql = True
            elif raw_sql_fstring_re.search(raw_line):
                is_raw_sql = True
            elif raw_sql_percent_re.search(raw_line):
                is_raw_sql = True
            elif raw_text_fstring_re.search(raw_line):
                is_raw_sql = True

            if is_raw_sql:
                # Check if parameterized (safe)
                if not param_bind_re.search(raw_line) and not param_method_re.search(raw_line):
                    a["raw_sql"].append(i)

            if secret_re.search(raw_line):
                low = raw_line.lower()
                if not any(x in low for x in {"example", "placeholder", "changeme",
                                               "dummy", "test", "xxx", "your_",
                                               "os.environ", "getenv", "settings."}):
                    a["hardcoded_secrets"].append(i)

    if "getLogger" in text or "structlog" in text or "loguru" in text:
        a["has_logger"] = True
    if "request_id" in text or "correlation_id" in text or "X-Request-ID" in text:
        a["has_request_id"] = True
    if "logging.basicConfig" in text:
        a["has_logging_basic_config"] = True
    if "websocket" in text.lower() and not a["is_script"]:
        a["websocket_funcs"].append(f.stem)

    if tree is None:
        return a

    # ── Top-level imports ──
    web_layers = BACKEND_SCAN_LAYERS
    for node in tree.body:
        module_names = []
        if isinstance(node, ast.Import):
            module_names = [al.name.split(".")[0] for al in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_names = [node.module.split(".")[0]]
        for m in module_names:
            if m in HL_HEAVY_PY_MODULES and a["app_layer"] in web_layers:
                a["heavy_imports"].append(m)
        if isinstance(node, ast.ImportFrom):
            for al in node.names:
                if al.name == "*":
                    a["star_imports"].append(node.lineno)

    # ── Global mutable state ──
    if not a["is_test"] and not a["is_script"]:
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        if isinstance(node.value, ast.List):
                            a["global_mutables"].append(target.id)
                        elif isinstance(node.value, ast.Dict):
                            has_var = any(
                                not isinstance(v, (ast.Constant, ast.List, ast.Tuple,
                                                    ast.Set, ast.Dict))
                                for v in node.value.values if v is not None)
                            if has_var:
                                a["global_mutables"].append(target.id)

    # ── Print statements ──
    if not a["is_script"] and not a["is_test"]:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and dotted_name(node.func) == "print":
                a["print_lines"].append(node.lineno)

    # ── Exception handlers ──
    if not a["is_script"]:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.type is None:
                a["bare_except"].append(node.lineno)
                continue
            exception_names = []
            if isinstance(node.type, ast.Name):
                exception_names = [node.type.id]
            elif isinstance(node.type, ast.Tuple):
                exception_names = [el.id for el in node.type.elts
                                   if isinstance(el, ast.Name)]
            if "Exception" in exception_names or "BaseException" in exception_names:
                a["broad"].append(node.lineno)
            only_pass = all(isinstance(s, ast.Pass) for s in node.body)
            has_log = any(isinstance(c, ast.Call) and "log" in dotted_name(c.func).lower()
                          for c in ast.walk(node))
            if only_pass or not has_log:
                a["swallowed"].append(node.lineno)

    # ── Function-level analysis ──
    for func in [n for n in ast.walk(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        func_name = func.name
        is_async = isinstance(func, ast.AsyncFunctionDef)

        # Size
        if (func.end_lineno and not a["is_migration"] and not a["is_script"]
                and not a["is_test"] and not a["is_seed"] and not a["is_tool"]):
            func_len = func.end_lineno - func.lineno + 1
            if func_len > 80:
                a["large_funcs"].append((func_name, func_len))

        # Docstrings
        if (is_public_name(func_name) and not a["is_script"] and not a["is_test"]
                and a["app_layer"] in {"modules", "domains",
                                        "providers", "jobs"}):
            try:
                if not ast.get_docstring(func):
                    a["missing_docs"].append(func_name)
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
            has_rm = any(any(kw.arg == "response_model" for kw in dec.keywords)
                         for dec in func.decorator_list if isinstance(dec, ast.Call))
            if not has_rm and func_name not in a["no_response_model"]:
                a["no_response_model"].append(func_name)

        # Loop ranges
        loop_ranges: list[tuple[int, int]] = []
        for child in ast.walk(func):
            if isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                if child.end_lineno:
                    loop_ranges.append((child.lineno, child.end_lineno))

        def _in_loop(lineno: int) -> bool:
            return any(s <= lineno <= e for s, e in loop_ranges)

        has_loop = len(loop_ranges) > 0
        http_count = 0
        has_transform = False
        call_count = 0
        json_ops = 0
        db_ops_in_loop = 0

        # Get function source for retry/pagination detection
        func_source = ""
        try:
            func_source = ast.get_source_segment(text, func) or ""
        except Exception:
            pass

        for child in ast.walk(func):
            if isinstance(child, ast.ListComp) and len(child.generators) > 1:
                a["large_list_comprehensions"].append((func_name, child.lineno))
            if not isinstance(child, ast.Call):
                continue
            call_name = dotted_name(child.func)
            call_count += 1
            child_line = getattr(child, "lineno", func.lineno)

            # Blocking sleep
            if call_name == "time.sleep":
                is_retry = ("retry" in func_name.lower() or "backoff" in func_source.lower()
                            or "attempt" in func_source.lower()
                            or "max_retries" in func_source)
                if (_hl_is_request_path_layer(a["app_layer"])
                        and not a["is_test"] and not a["is_script"]
                        and not a["is_background"] and not a["is_scheduler"]
                        and a["app_layer"] not in HL_SLEEP_ALLOWED
                        and a["app_layer"] != "middleware"
                        and not is_retry):
                    a["blocking_sleep"].append((func_name, child_line))

            if call_name in HL_BLOCKING_CALLS and is_async:
                a["blocking_async"].append((func_name, child_line, call_name))
            if call_name in HL_SYNC_IO_CALLS and is_async:
                a["sync_io_async"].append((func_name, child_line, call_name))
            if call_name.startswith(HL_EXTERNAL_PREFIXES):
                http_count += 1
                if not _hl_is_conn_init(call_name):
                    if not any(kw.arg == "timeout" for kw in child.keywords):
                        a["missing_timeout"].append((func_name, child_line))
            if call_name.startswith("json."):
                json_ops += 1
                has_transform = True
            if call_name.startswith(("re.", "hashlib.", "base64.")):
                has_transform = True

            # DB calls in loop (N+1 detection)
            if HL_DB_CALL_RE.search(call_name):
                if _in_loop(child_line):
                    db_ops_in_loop += 1

        # Post-function checks
        if http_count > 1 and not a["is_script"]:
            a["sequential_http"].append((func_name, http_count, is_async))
        if has_loop and has_transform and http_count == 0:
            a["cpu_bound"].append(func_name)
        if json_ops >= 5:
            a["json_heavy_funcs"].append((func_name, json_ops))
        if (not a["is_script"] and not a["is_test"] and not a["is_migration"]
                and not a["is_seed"] and not a["is_tool"]
                and a["app_layer"] not in {"utils", "tools", "scripts",
                                            "tasks", "monitoring"}):
            if http_count >= 2 or call_count >= 25:
                a["timing_targets"].append((func_name, call_count, http_count))
        if (not a["is_script"] and not a["is_test"] and not a["is_migration"]
                and a["app_layer"] != "middleware" and not a["is_seed"]
                and a["app_layer"] != "jobs"
                and "seed" not in a["path"].lower()
                and "migration_helpers" not in a["path"].lower()):
            if db_ops_in_loop >= 2:
                a["loop_db"].append((func_name, db_ops_in_loop))
        if is_endpoint and has_loop and has_transform and call_count > 15:
            a["heavy_in_request"].append(func_name)
        if is_endpoint and not is_write_endpoint:
            if ("skip" not in func_source and "limit" not in func_source
                    and "offset" not in func_source and "page" not in func_source
                    and "cursor" not in func_source
                    and ".all()" in func_source):
                a["no_pagination"].append(func_name)

    return a

# ============================================================================
# SECTION 62: HEALTH AUDIT — RUN ALL CHECKS
# ============================================================================

def hl_run_all_checks(repo: Path, rep: Report, base_url: str | None = None) -> dict:
    """Run ALL health audit checks. base_url=None skips runtime probing."""
    ob101_by_layer: dict[str, list[str]] = defaultdict(list)
    ob102_by_layer: dict[str, list[str]] = defaultdict(list)
    hl110_all: list[tuple[str, list[str]]] = []

    _fallback_eff = {
        "ignore_dirs": DEFAULT_IGNORE_DIRS,
        "text_ext": DEFAULT_TEXT_EXT,
        "source_ext": DEFAULT_SOURCE_EXT,
        "max_read_bytes": DEFAULT_MAX_READ_BYTES,
    }

    # ══════════════════════════════════════════════════════════
    # PYTHON CHECKS — all values come from hl_analyze_python
    # ══════════════════════════════════════════════════════════
    for root in [repo / "backend", repo / "scripts"]:
        if not root.exists():
            continue
        eff = _ACTIVE_EFF or _fallback_eff
        for f in iter_text_files(root, eff):
            if f.suffix.lower() != ".py":
                continue
            text = read_text(f)
            if not text:
                continue
            tree = parse_safe(f)
            a = hl_analyze_python(f, text, tree, repo)
            rp = a["path"]

            # HL101: Oversized file
            if a["line_count"] > 900 and not a["is_script"] and not a["is_test"]:
                rep.add(YEL, "HL101", "python", rp,
                        f"oversized file ({a['line_count']} lines)",
                        intended="split by responsibility/domain")

            # SEC105: Hardcoded credentials
            if a["hardcoded_secrets"]:
                rep.add(RED, "SEC105", "security", rp,
                        f"hardcoded credential (lines: {_hl_lines_example(a['hardcoded_secrets'])})",
                        intended="move to env vars / Vault / secrets manager")

            # SEC101: Raw SQL
            if a["raw_sql"]:
                rep.add(RED, "SEC101", "security", rp,
                        f"raw SQL concatenation (lines: {_hl_lines_example(a['raw_sql'])})",
                        intended="use parameterized queries / SQLAlchemy ORM")

            # HL501: Heavy imports
            if a["heavy_imports"]:
                rep.add(YEL, "HL501", "performance", rp,
                        f"heavy top-level import: {', '.join(sorted(set(a['heavy_imports'])))}",
                        intended="lazy-import inside the function/job that needs them")

            # HL502: Star imports
            if a["star_imports"]:
                rep.add(YEL, "HL502", "python", rp,
                        f"star import at lines: {_hl_lines_example(a['star_imports'])}",
                        intended="use explicit imports")

            # HL203: logging.basicConfig
            if a["has_logging_basic_config"]:
                rep.add(YEL, "HL203", "logging", rp,
                        "logging.basicConfig() in module code",
                        intended="configure once in main; modules use getLogger()")

            # HL201: Print statements
            if a["print_lines"]:
                rep.add(YEL, "HL201", "logging", rp,
                        f"{len(a['print_lines'])} print() (lines: {_hl_lines_example(a['print_lines'])})",
                        intended="use structured logging with request_id/domain/context")

            # HL204: Secret in logs
            if a["secret_log_lines"]:
                rep.add(YEL, "HL204", "security", rp,
                        f"possible secret in log (lines: {_hl_lines_example(a['secret_log_lines'])})",
                        intended="never log secrets; log only IDs/status")

            # OB101: Collect missing logger
            if (not a["has_logger"]
                    and a["app_layer"] in BACKEND_SCAN_LAYERS):
                ob101_by_layer[a["app_layer"]].append(rp)

            # OB102: Collect missing request_id
            if (not a["has_request_id"]
                    and a["app_layer"] in BACKEND_SCAN_LAYERS):
                ob102_by_layer[a["app_layer"]].append(rp)

            # HL301: Bare except
            if a["bare_except"]:
                rep.add(YEL, "HL301", "error-handling", rp,
                        f"bare except (lines: {_hl_lines_example(a['bare_except'])})",
                        intended="catch specific exceptions; log; re-raise or return safe error")

            # HL302: Swallowed exception
            if a["swallowed"] and not a["is_script"]:
                rep.add(YEL, "HL302", "error-handling", rp,
                        f"swallowed exception (lines: {_hl_lines_example(a['swallowed'])})",
                        intended="log with logger.exception(...); re-raise or return controlled error")
            elif a["broad"] and not a["is_script"]:
                rep.add(YEL, "HL303", "error-handling", rp,
                        f"broad except Exception (lines: {_hl_lines_example(a['broad'])})",
                        intended="narrow exception types; always log with context")

            # HL102: Oversized functions
            if (a["large_funcs"] and not a["is_migration"] and not a["is_script"]
                    and not a["is_test"] and not a["is_seed"] and not a["is_tool"]):
                examples = ", ".join(f"{n} ({l}L)" for n, l in a["large_funcs"][:6])
                rep.add(YEL, "HL102", "python", rp,
                        f"oversized function(s): {examples}",
                        intended="extract smaller functions")

            # HL110: Collect missing docstrings (grouped later, NOT per-file)
            if a["missing_docs"]:
                hl110_all.append((rp, a["missing_docs"]))

            # HL401: Blocking sleep in request path
            if a["blocking_sleep"]:
                examples = ", ".join(f"{n}:{l}" for n, l in a["blocking_sleep"][:6])
                rep.add(YEL, "HL401", "performance", rp,
                        f"blocking sleep in request path: {examples}",
                        intended="use async sleep, scheduler, or background job")

            # HL402: Blocking call in async
            if a["blocking_async"]:
                examples = ", ".join(f"{n}:{l} ({c})" for n, l, c in a["blocking_async"][:6])
                rep.add(RED, "HL402", "performance", rp,
                        f"blocking call inside async: {examples}",
                        intended="use async client or run_in_executor")

            # HL403: Sync I/O in async
            if a["sync_io_async"]:
                examples = ", ".join(f"{n}:{l} ({c})" for n, l, c in a["sync_io_async"][:6])
                rep.add(YEL, "HL403", "performance", rp,
                        f"sync I/O inside async: {examples}",
                        intended="use aiofiles / async pathlib / run_in_executor")

            # HL601: Sequential HTTP calls
            if a["sequential_http"] and not a["is_script"]:
                examples = ", ".join(f"{n} ({c} calls)" for n, c, _ in a["sequential_http"][:6])
                rep.add(YEL, "HL601", "concurrency", rp,
                        f"sequential external calls: {examples}",
                        intended="use asyncio.gather or ThreadPoolExecutor; add timeout + retry")

            # HL602: Missing timeout
            if a["missing_timeout"] and not a["is_script"] and not a["is_test"]:
                examples = ", ".join(f"{n}:{l}" for n, l in a["missing_timeout"][:6])
                rep.add(YEL, "HL602", "concurrency", rp,
                        f"external call(s) missing timeout: {examples}",
                        intended="always set timeout; add retry + circuit breaker")

            # PG101: Heavy JSON serialization
            if a["json_heavy_funcs"]:
                examples = ", ".join(f"{n} ({c} json ops)" for n, c in a["json_heavy_funcs"][:6])
                rep.add(YEL, "PG101", "polyglot", rp,
                        f"heavy JSON serialization: {examples}",
                        intended="use orjson (3-10x faster) or Node.js sidecar")

            # PG102: WebSocket in Python
            if a["websocket_funcs"]:
                examples = ", ".join(set(a["websocket_funcs"][:6]))
                rep.add(YEL, "PG102", "polyglot", rp,
                        f"WebSocket handler in Python: {examples}",
                        intended="Python for business logic; Node.js gateway for high-throughput real-time")

            # PG103: CPU-bound in request path
            if a["heavy_in_request"]:
                examples = ", ".join(a["heavy_in_request"][:6])
                rep.add(YEL, "PG103", "polyglot", rp,
                        f"CPU-bound in request path: {examples}",
                        intended="offload to worker (Celery/arq) or Node.js worker thread")

            # SC101: Missing pagination
            if a["no_pagination"]:
                examples = ", ".join(a["no_pagination"][:6])
                rep.add(YEL, "SC101", "scaling", rp,
                        f"list endpoint(s) missing pagination: {examples}",
                        intended="add skip/limit or cursor pagination")

            # SC102: N+1 DB operations
            if a["loop_db"]:
                examples = ", ".join(f"{n} ({c} ops)" for n, c in a["loop_db"][:6])
                rep.add(YEL, "SC102", "scaling", rp,
                        f"N+1 DB operations in loop: {examples}",
                        intended="use bulk operations / joinedload / batch insert")

            # SC501: Heavy operation in request path
            if a["heavy_in_request"]:
                examples = ", ".join(a["heavy_in_request"][:6])
                rep.add(YEL, "SC501", "scaling", rp,
                        f"heavy operation in request path: {examples}",
                        intended="offload to background job; return 202 Accepted")

            # API101: Missing response_model
            if a["no_response_model"]:
                examples = ", ".join(a["no_response_model"][:6])
                rep.add(YEL, "API101", "api-health", rp,
                        f"endpoint(s) missing response_model: {examples}",
                        intended="add response_model for type safety and docs")

            # MR101: Nested list comprehension
            if a["large_list_comprehensions"]:
                examples = ", ".join(f"{n}:{l}" for n, l in a["large_list_comprehensions"][:6])
                rep.add(YEL, "MR101", "memory", rp,
                        f"nested list comprehension: {examples}",
                        intended="use generator expression for large datasets")

            # MR104: Global mutable state
            if a["global_mutables"] and not a["is_seed"] and not a["is_tool"] and not a["is_script"]:
                examples = ", ".join(a["global_mutables"][:6])
                rep.add(YEL, "MR104", "memory", rp,
                        f"global mutable state: {examples}",
                        intended="use dependency injection / singleton")

            # HL801: Timing/metrics targets
            if (a["timing_targets"] and not a["is_script"] and not a["is_test"]
                    and not a["is_seed"] and not a["is_tool"]
                    and a["app_layer"] not in {"utils", "tools", "scripts", "tasks", "monitoring"}):
                examples = ", ".join(f"{n} (calls={c})" for n, c, _ in a["timing_targets"][:6])
                rep.add(YEL, "HL801", "observability", rp,
                        f"function(s) need timing/metrics: {examples}",
                        intended="add timing decorator / Prometheus histogram / duration_ms logs")

            # HL901: TODO markers
            if a["todo_count"] > 5:
                rep.add(YEL, "HL901", "python", rp,
                        f"{a['todo_count']} TODO/FIXME/HACK markers",
                        intended="convert to tasks/ADRs; delete stale")

            # HL902: Commented-out code
            if a["commented_code_count"] > 15 and not a["is_test"]:
                rep.add(YEL, "HL902", "python", rp,
                        f"{a['commented_code_count']} commented-out code lines",
                        intended="remove dead code; rely on git history")

    # ══════════════════════════════════════════════════════════
    # GROUPED PYTHON FINDINGS
    # ══════════════════════════════════════════════════════════
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

    # HL110: Grouped docstring finding (ONLY here, never per-file)
    if hl110_all:
        total_funcs = sum(len(funcs) for _, funcs in hl110_all)
        total_files = len(hl110_all)
        layer_counts_hl: dict[str, int] = defaultdict(int)
        for path_hl, funcs in hl110_all:
            parts_hl = path_hl.replace("\\", "/").split("/")
            if "backend" in parts_hl:
                idx_hl = parts_hl.index("backend")
                ln = parts_hl[idx_hl + 1] if len(parts_hl) > idx_hl + 1 else "root"
                layer_counts_hl[ln] += len(funcs)
        layer_summary = ", ".join(
            f"{l}/ ({c})" for l, c in sorted(layer_counts_hl.items(), key=lambda x: -x[1])[:5])
        top_files = [Path(p).name for p, _ in hl110_all[:5]]
        extra = f" +{total_files - 5} more" if total_files > 5 else ""
        rep.add(YEL, "HL110", "documentation", "backend/",
                f"{total_funcs} public functions missing docstrings across {total_files} files",
                intended=f"By layer: {layer_summary}. Top: {', '.join(top_files)}{extra}")

    # ══════════════════════════════════════════════════════════
    # FRONTEND HEALTH CHECKS
    # ══════════════════════════════════════════════════════════
    frontend = repo / "frontend"
    feh402: list[str] = []
    feh501: list[str] = []
    feh503: list[str] = []
    feh201: list[str] = []
    feh802: list[str] = []

    _fe_ext = {".ts", ".tsx", ".js", ".jsx", ".cjs", ".mjs"}

    if frontend.exists():
        eff = _ACTIVE_EFF or _fallback_eff
        for d, entries in walk_dirs(frontend, eff.get("ignore_dirs", DEFAULT_IGNORE_DIRS)):
            for e in entries:
                if not e.is_file() or e.suffix.lower() not in _fe_ext:
                    continue
                text = read_text(e)
                if not text:
                    continue
                rp = rel(e, repo)
                try:
                    parts = [p.lower() for p in e.relative_to(repo).parts]
                except ValueError:
                    parts = []
                is_test = any(x in parts for x in {"tests", "test", "e2e", "__tests__", "testing"})
                line_count = len(text.splitlines())
                fname = e.name.lower()
                fe_domain = hl_frontend_domain(rp)

                # FEH101: Oversized frontend file
                if line_count > 600:
                    rep.add(YEL, "FEH101", f"frontend/{fe_domain}", rp,
                            f"oversized frontend file ({line_count} lines)",
                            intended="split into smaller components/hooks/features")

                # FEH201: Console/debugger (collect for grouped)
                if not is_test:
                    if HL_CONSOLE_RE.search(text) or HL_DEBUGGER_RE.search(text):
                        feh201.append(rp)

                # FEH401: Inline JSX handlers
                inline_count = len(HL_INLINE_HANDLER_RE.findall(text))
                if inline_count > 20:
                    rep.add(YEL, "FEH401", f"frontend/{fe_domain}", rp,
                            f"{inline_count} inline JSX handler(s)",
                            intended="extract handlers; use useCallback/React.memo")

                # FEH402: Index as key (collect for grouped)
                if HL_KEY_INDEX_RE.search(text):
                    feh402.append(rp)

                # FEH501: Data fetching in useEffect (collect for grouped)
                if "useEffect" in text and HL_USEEFFECT_FETCH_RE.search(text):
                    feh501.append(rp)

                # FEH502: Heavy frontend import
                heavy = HL_HEAVY_FE_RE.findall(text)
                if heavy:
                    rep.add(YEL, "FEH502", f"frontend/{fe_domain}", rp,
                            f"heavy import(s): {', '.join(sorted(set(heavy)))}",
                            intended="use modular imports / dynamic import / next dynamic")

                # FEH503: Direct DOM access (collect for grouped)
                if HL_DIRECT_DOM_RE.search(text):
                    feh503.append(rp)

                # FEH504: Large list rendering
                map_count = len(HL_MAP_RE.findall(text))
                if map_count > 35:
                    rep.add(YEL, "FEH504", f"frontend/{fe_domain}", rp,
                            f"large list rendering ({map_count} .map calls)",
                            intended="use virtualization, pagination, or server-driven lists")

                # FEH301: Error boundary
                if fname in {"app.tsx", "layout.tsx", "_app.tsx", "main.tsx", "index.tsx"}:
                    if not HL_ERROR_BOUNDARY_RE.search(text):
                        rep.add(YEL, "FEH301", f"frontend/{fe_domain}", rp,
                                "app/layout entry has no ErrorBoundary",
                                intended="wrap app/routes in ErrorBoundary")

                # FEH601: Memoization
                if line_count > 400 and inline_count > 10 and not HL_MEMO_RE.search(text):
                    rep.add(YEL, "FEH601", f"frontend/{fe_domain}", rp,
                            "large component without memoization",
                            intended="use useMemo/useCallback/React.memo where measured")

                # FEH701: Heavy transformation
                json_heavy = text.count("JSON.parse") + text.count("JSON.stringify")
                if json_heavy > 10 and (map_count > 10 or "for " in text):
                    rep.add(YEL, "FEH701", f"frontend/{fe_domain}", rp,
                            f"heavy client-side transformation ({json_heavy} JSON ops)",
                            intended="move to Web Worker / WASM / server")

                # FEH801: Suspense/lazy
                if line_count > 300 and not HL_SUSPENSE_RE.search(text):
                    if "import " in text and ("page" in fname or "screen" in fname):
                        rep.add(YEL, "FEH801", f"frontend/{fe_domain}", rp,
                                "route/page without Suspense/lazy loading",
                                intended="use React.lazy + Suspense or next/dynamic")

                # FEH802: Raw img (collect for grouped)
                if re.search(r"<img\s", text) and not re.search(r"next/image|<Image\s", text):
                    feh802.append(rp)

                # PG201: Web Worker
                if json_heavy > 15 and not HL_WEB_WORKER_RE.search(text):
                    rep.add(YEL, "PG201", "polyglot", rp,
                            f"heavy computation on main thread ({json_heavy} JSON ops)",
                            intended="move to Web Worker; keep main thread for rendering")

    # Grouped FE findings — use message text for count, not params
    if feh402:
        top = feh402[:5]
        extra = f" +{len(feh402) - 5} more" if len(feh402) > 5 else ""
        rep.add(YEL, "FEH402", "react", "frontend/",
                f"{len(feh402)} files use array index as list key",
                intended=f"Use item.id instead of index. Top: {', '.join(top)}{extra}",
                count=len(feh402), examples=top)

    if feh501:
        top = feh501[:5]
        extra = f" +{len(feh501) - 5} more" if len(feh501) > 5 else ""
        rep.add(YEL, "FEH501", "react", "frontend/",
                f"{len(feh501)} files fetch data inside useEffect",
                intended=f"Migrate to React Query/SWR. Create shared useApiQuery() hook. Top: {', '.join(top)}{extra}",
                count=len(feh501), examples=top)

    if feh503:
        top = feh503[:5]
        extra = f" +{len(feh503) - 5} more" if len(feh503) > 5 else ""
        rep.add(YEL, "FEH503", "react", "frontend/",
                f"{len(feh503)} files use direct DOM/window access",
                intended=f"Isolate browser APIs in hooks. Top: {', '.join(top)}{extra}",
                count=len(feh503), examples=top)

    if feh201:
        top = feh201[:5]
        extra = f" +{len(feh201) - 5} more" if len(feh201) > 5 else ""
        rep.add(YEL, "FEH201", "frontend", "frontend/",
                f"{len(feh201)} files have console/debugger statements",
                intended=f"Remove before merge; use structured logger. Top: {', '.join(top)}{extra}",
                count=len(feh201), examples=top)

    if feh802:
        top = feh802[:5]
        extra = f" +{len(feh802) - 5} more" if len(feh802) > 5 else ""
        rep.add(YEL, "FEH802", "frontend", "frontend/",
                f"{len(feh802)} files use raw <img> without next/image",
                intended=f"Use next/image for lazy loading + WebP. Top: {', '.join(top)}{extra}",
                count=len(feh802), examples=top)

    # ══════════════════════════════════════════════════════════
    # DEPLOYMENT CHECKS
    # ══════════════════════════════════════════════════════════
    if not (repo / "Dockerfile").exists() and not (repo / "backend" / "Dockerfile").exists():
        rep.add(YEL, "DP101", "deployment", "repo", "no Dockerfile found",
                intended="add multi-stage Dockerfile")
    if not (repo / ".dockerignore").exists():
        rep.add(YEL, "DP105", "deployment", "repo", "missing .dockerignore",
                intended="exclude .git, node_modules, __pycache__, .venv, uploads")

    for compose_name in ["docker-compose.yml", "docker-compose.prod.yml"]:
        compose = repo / compose_name
        if compose.exists():
            compose_text = read_text(compose) or ""
            if "healthcheck" not in compose_text:
                rep.add(YEL, "DP102", "deployment", compose_name,
                        f"{compose_name} missing healthcheck",
                        intended="add healthcheck with test/interval/timeout/retries")

    main_py = repo / "backend" / "main.py"
    if main_py.exists():
        main_text = read_text(main_py) or ""
        if "SIGTERM" not in main_text and "graceful" not in main_text and "on_shutdown" not in main_text:
            rep.add(YEL, "DP104", "deployment", "backend/main.py",
                    "no graceful shutdown handler",
                    intended="handle SIGTERM/SIGINT; drain connections; flush logs")

    backend = repo / "backend"
    if backend.exists():
        has_env = False
        for f in iter_text_files(backend, _ACTIVE_EFF or _fallback_eff):
            if f.suffix.lower() != ".py":
                continue
            text = read_text(f) or ""
            if "BaseSettings" in text or "pydantic_settings" in text:
                has_env = True
                break
        if not has_env:
            rep.add(YEL, "DP103", "deployment", "backend/",
                    "no env var validation at startup",
                    intended="use pydantic BaseSettings; fail fast on missing vars")

    # ══════════════════════════════════════════════════════════
    # PIPELINE CHECKS
    # ══════════════════════════════════════════════════════════
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

    # ══════════════════════════════════════════════════════════
    # RUNTIME PROBING (only if base_url is provided)
    # ══════════════════════════════════════════════════════════
    if base_url:
        base = base_url.rstrip("/")
        for path in ["/health", "/api/health", "/api/v1/health", "/openapi.json"]:
            url = base + path
            start = time.time()
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": "zozi-health-audit",
                                  "Accept": "application/json, text/plain, */*"})
                with urllib.request.urlopen(req, timeout=5) as response:
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

    return {}

# ============================================================================
# SECTION 65: HEALTH SCORING & REPORTING
# ============================================================================

def compute_health_score(rep: Report) -> tuple[int, str]:
    """Compute 0-100 health score. Higher = healthier."""
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

def compute_file_health_scores(rep: Report) -> list[tuple[str, int, list[str]]]:
    """Rank files by weighted finding count. Returns top 20."""
    file_weights: dict[str, int] = defaultdict(int)
    file_codes: dict[str, set[str]] = defaultdict(set)
    weight_map = {"P0": 10, "P1": 5, "P2": 2, "P3": 1}
    for f in rep.findings:
        if f.path and f.path not in {"repo", "frontend/", "backend/", "CI/CD"}:
            w = weight_map.get(f.priority, 1) * f.count
            file_weights[f.path] += w
            file_codes[f.path].add(f.code)
    ranked = sorted(file_weights.items(), key=lambda x: -x[1])[:20]
    return [(path, score, sorted(file_codes[path])) for path, score in ranked]

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
    E2E --> CANARY["Canary"]
    CANARY --> PROD["Production"]

"""


def generate_fix_patterns_section() -> str:
    lines = ["## Fix Patterns (Before → After)", ""]
    for code, pattern in HL_FIX_PATTERNS.items():
        meaning = RULE_MEANING.get(code, code)
        lines.extend([
            f"### {code}: {meaning}",
            "",
            "**Before:**",
            "```",
            f"{pattern['before']}",
            "```",
            "**After:**",
            "```",
            f"{pattern['after']}",
            "```",
            f"**Action:** {pattern['action']}",
            "",
        ])
    return "\n".join(lines)


def generate_executive_summary(rep: Report, score: int, grade: str) -> str:
    """Generate executive summary with priority breakdown."""
    priority_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for f in rep.findings:
        p = getattr(f, "priority", "P3")
        if p in priority_counts:
            priority_counts[p] += f.count

    lines = [
        "## Executive Summary",
        "",
        f"**Health Score: {score}/100 ({grade})**",
        "",
        "| Priority | Count | Action |",
        "|---|---:|---|",
        f"| 🔴 P0 (fix today) | {priority_counts['P0']} | Production / security risk |",
        f"| 🟠 P1 (fix this sprint) | {priority_counts['P1']} | Scaling / performance risk |",
        f"| 🟡 P2 (fix this month) | {priority_counts['P2']} | Maintainability / structure |",
        f"| 🟢 P3 (fix when convenient) | {priority_counts['P3']} | Hygiene / style |",
    ]
    return "\n".join(lines)

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
# Unknown Place
# ============================================================================

def feature_of_path(path_rel: str) -> str:
    """Bucket a finding path into a human-trackable feature area."""
    parts = [p.lower() for p in Path(path_rel).parts]
    if not parts:
        return "repo"

    p0 = parts[0]

    # ── Backend ──
    if p0 == "backend":
        if len(parts) >= 3:
            layer = parts[1]
            if layer in {"modules", "domains", "providers", "jobs"}:
                return f"backend/{layer}/{parts[2]}"
            return f"backend/{layer}"
        if len(parts) == 2:
            return f"backend/{parts[1]}"
        return "backend"

    # ── Frontend ──
    if p0 == "frontend" and len(parts) >= 3:
        ws = parts[1]
        rest = parts[2:]
        for marker in ("app", "components", "lib", "hooks", "styles", "theme"):
            if marker in rest:
                i = rest.index(marker)
                if marker == "app" and len(rest) > i + 1:
                    return f"frontend/{ws}/app/{rest[i + 1]}"
                if marker == "components" and len(rest) > i + 1:
                    return f"frontend/{ws}/components/{rest[i + 1]}"
                return f"frontend/{ws}/{marker}"
        return f"frontend/{ws}"

    return p0


REQUIRED_HEALTH_ENDPOINTS = ("/health", "/health/deps", "/health/ready")

def check_health_endpoints(repo: Path, rep: Report, eff: dict) -> None:
    """§8: liveness/readiness endpoints must exist in routers AND main.py."""
    backend = repo / "backend"
    found: set[str] = set()

    # Check routers/
    routers = backend / "routers"
    if routers.exists():
        for f in routers.glob("*.py"):
            t = read_text(f) or ""
            for ep in REQUIRED_HEALTH_ENDPOINTS:
                if f'"{ep}"' in t or f"'{ep}'" in t:
                    found.add(ep)

    # Also check main.py (health may be registered there)
    main_py = backend / "main.py"
    if main_py.exists():
        t = read_text(main_py) or ""
        for ep in REQUIRED_HEALTH_ENDPOINTS:
            if f'"{ep}"' in t or f"'{ep}'" in t:
                found.add(ep)

    # Also check dedicated health router
    health_router = routers / "health.py"
    if health_router.exists():
        t = read_text(health_router) or ""
        for ep in REQUIRED_HEALTH_ENDPOINTS:
            if f'"{ep}"' in t or f"'{ep}'" in t:
                found.add(ep)

    missing = [ep for ep in REQUIRED_HEALTH_ENDPOINTS if ep not in found]
    if missing:
        rep.add(
            YEL, "HC1", "backend", "backend/routers/health.py",
            f"missing health contract endpoint(s): {', '.join(missing)}",
            intended="expose GET /health, /health/deps, /health/ready (§8)",
        )


_PROV_BASES = {"BaseProvider", "BaseAIProvider"}
_PROVISH_METHODS = {
    "predict", "load_model", "preprocess", "postprocess",
    "analyze", "generate", "transcribe", "embed", "remove",
}


def check_provider_base_classes(repo: Path, rep: Report, eff: dict) -> None:
    """PRV1/PRV2: architecture §5 — providers must subclass the base and implement health_check()."""
    prov = repo / "backend" / "providers"
    if not prov.exists():
        return

    for f in iter_text_files(prov, eff):
        if f.suffix.lower() != ".py":
            continue
        tree = parse_safe(f)
        if tree is None:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name.startswith("_"):
                continue
            bases = {dba_dotted_name(b).split(".")[-1] for b in node.bases}
            methods = {
                m.name for m in node.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if bases & _PROV_BASES:
                if "health_check" not in methods:
                    rep.add(
                        YEL, "PRV2", "backend", rel(f, repo),
                        f"provider '{node.name}' missing health_check()",
                        intended="implement health_check() per architecture §5",
                        line=node.lineno,
                    )
            elif methods & _PROVISH_METHODS:
                rep.add(
                    YEL, "PRV1", "backend", rel(f, repo),
                    f"class '{node.name}' in providers/ does not subclass "
                    f"BaseProvider/BaseAIProvider",
                    intended="subclass the provider base so health/availability is uniform",
                    line=node.lineno,
                )

def check_scaling_phases(repo: Path, rep: Report, eff: dict) -> None:
    """§9.2: Verify Phase A/B/C prerequisites."""
    backend = repo / "backend"
    if not backend.exists():
        return

    # ── Phase A prerequisites ──
    # PgBouncer config reference
    has_pgbouncer_ref = False
    for candidate in (backend / "utils" / "config.py",
                      backend / "db" / "database.py",
                      repo / "docker-compose.yml",
                      repo / "docker-compose.prod.yml"):
        if candidate.exists():
            t = read_text(candidate) or ""
            if "pgbouncer" in t.lower() or "PGBOUNCER" in t:
                has_pgbouncer_ref = True
                break
    if not has_pgbouncer_ref:
        rep.add(YEL, "SC1", "backend", "backend/db/database.py",
                "no PgBouncer reference found — pool_size per replica "
                "will exhaust connections at scale (§9.2 Phase A)",
                intended="add PgBouncer (transaction mode) in front of PostgreSQL")

    # Read replica reference
    has_replica_ref = False
    for candidate in (backend / "db" / "database.py",
                      backend / "utils" / "config.py"):
        if candidate.exists():
            t = read_text(candidate) or ""
            if re.search(r"replica|read_replica|REPLICA_URL|READ_DB_URL", t, re.I):
                has_replica_ref = True
                break
    if not has_replica_ref:
        rep.add(YEL, "SC1", "backend", "backend/db/database.py",
                "no read-replica configuration found (§9.2 Phase A)",
                intended="configure read replica URL for read-heavy paths")

    # ── Phase B: async engine ──
    has_async = False
    for search_dir in (backend / "db",):
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.py"):
            t = read_text(f) or ""
            if re.search(r"create_async_engine|AsyncSession|async_sessionmaker", t):
                has_async = True
                break
        if has_async:
            break
    if not has_async:
        rep.add(YEL, "SC2", "backend", "backend/db/",
                "no async SQLAlchemy engine found — sync drivers block the "
                "event loop at ~50K+ concurrent (§9.2 Phase B)",
                intended="convert hot paths to AsyncPG + SQLAlchemy 2.0 async sessions")

    # ── Phase C: Kafka / OpenSearch / CDC ──
    has_kafka = False
    has_opensearch = False
    for search_dir in (backend / "events", backend / "utils"):
        if not search_dir.exists():
            continue
        for f in search_dir.rglob("*.py"):
            t = read_text(f) or ""
            if re.search(r"kafka|confluent_kafka|aiokafka", t, re.I):
                has_kafka = True
            if re.search(r"opensearch|elasticsearch|OpenSearch", t, re.I):
                has_opensearch = True
    if not has_kafka:
        rep.add(GRN, "SC3", "backend", "events/",
                "no Kafka command bus found (§9.2 Phase C — not yet required)",
                intended="add an events/ Kafka command bus (publish/consume) when "
                         "throughput modeling justifies Phase C")
    if not has_opensearch:
        rep.add(GRN, "SC3", "backend", "providers/",
                "no OpenSearch adapter found (§9.2 Phase C — not yet required)",
                intended="add a providers/ OpenSearch adapter for faceted "
                         "catalog search at Phase C")

def check_middleware_pipeline_order(repo: Path, rep: Report, eff: dict) -> None:
    """§2.2: Verify the 6-layer middleware pipeline order."""
    backend = repo / "backend"
    orchestrator = backend / "middleware" / "orchestrator.py"
    if not orchestrator.exists():
        rep.add(YEL, "MW2", "backend", "backend/middleware/orchestrator.py",
                "middleware orchestrator not found",
                intended="create middleware/orchestrator.py with the 6-layer pipeline")
        return

    text = read_text(orchestrator) or ""

    # Expected middleware in order (§2.2)
    expected_order = [
        ("GZip", "foundation"),
        ("CORS", "foundation"),
        ("IP", "foundation"),
        ("RequestID", "foundation"),
        ("SecurityHeaders", "security"),
        ("ImpossibleTravel", "security"),
        ("CSRF", "security"),
        ("RateLimit", "rate_limit"),
        ("CountryContext", "geo"),
        ("RequestLogging", "observability"),
        ("PCI", "compliance"),
    ]

    found_positions: list[tuple[str, int]] = []
    for name, _category in expected_order:
        # Find first occurrence of add_middleware with this name
        pattern = re.compile(rf"add_middleware\s*\(\s*\w*{name}\w*", re.I)
        m = pattern.search(text)
        if m:
            found_positions.append((name, m.start()))

    # Check order
    for i in range(len(found_positions) - 1):
        name_a, pos_a = found_positions[i]
        name_b, pos_b = found_positions[i + 1]
        if pos_a > pos_b:
            rep.add(YEL, "MW1", "backend", "backend/middleware/orchestrator.py",
                    f"middleware order violation: {name_a} appears after {name_b} "
                    f"(§2.2 pipeline order)",
                    intended=f"reorder: {name_b} must come before {name_a}")


def check_realtime_policy(repo: Path, rep: Report, eff: dict) -> None:
    """§10.9: WebSocket fan-out must use Redis pub/sub, not in-process dicts."""
    backend = repo / "backend"
    realtime_file = backend / "utils" / "realtime.py"
    if not realtime_file.exists():
        return

    text = read_text(realtime_file) or ""

    has_inprocess = bool(re.search(
        r"dict\[.*WebSocket\]|connections\s*[:=]\s*\{"
        r"|active_connections|_connections\s*[:=]", text))
    has_redis_bridge = bool(re.search(
        r"redis.*pubsub|pubsub.*redis|Redis.*publish|publish.*Redis", text, re.I))

    if has_inprocess and not has_redis_bridge:
        rep.add(YEL, "SC3", "backend", "backend/utils/realtime.py",
                "WebSocket fan-out uses in-process dict without Redis pub/sub "
                "bridge (§10.9) — will not scale past one replica",
                intended="add Redis pub/sub bridge so any replica can "
                         "publish to any socket")            


def check_background_infrastructure(repo: Path, rep: Report, eff: dict) -> None:
    """    §7.1: domains/*/events.py, jobs/, async_workers must exist."""
    backend = repo / "backend"

    # events/ publisher
    events_dir = backend / "events"
    if not events_dir.exists():
        rep.add(YEL, "P4", "backend", "backend/events/",
                "events/ directory missing (§7.1)",
                intended="create backend/events/ with domain event publishers")

    # jobs/ background tasks
    jobs_dir = backend / "jobs"
    if not jobs_dir.exists():
        rep.add(YEL, "P4", "backend", "backend/jobs/",
                "jobs/ directory missing (§7.1)",
                intended="create backend/jobs/ with background task runners")

    # async_workers off-request AI
    async_workers = backend / "providers" / "async_workers.py"
    if not async_workers.exists():
        rep.add(YEL, "P4", "backend", "backend/providers/async_workers.py",
                "providers/async_workers.py missing (§7.1) — heavy AI work "
                "must run off-request",
                intended="create async_workers.py for off-request AI processing")

    # lifespan.py startup sequence
    lifespan = backend / "lifespan.py"
    if not lifespan.exists():
        rep.add(YEL, "P4", "backend", "backend/lifespan.py",
                "lifespan.py missing (§7.2)",
                intended="create lifespan.py with migration gate → schema init "
                         "→ seed → cache warm-up startup sequence")

    # monitoring/
    monitoring = repo / "monitoring"
    if not monitoring.exists():
        rep.add(YEL, "P4", "repo", "monitoring/",
                "monitoring/ directory missing (§7.3)",
                intended="create monitoring/ with docker-compose.monitoring.yml "
                         "+ prometheus.yml")

def check_lifespan_startup(repo: Path, rep: Report, eff: dict) -> None:
    """§7.2: lifespan.py boots: migration gate → schema init (dev) → seed → cache warm-up."""
    backend = repo / "backend"
    lifespan = backend / "lifespan.py"
    if not lifespan.exists():
        rep.add(YEL, "P4", "backend", "backend/lifespan.py",
                "lifespan.py missing (§7.2)",
                intended="create lifespan.py with migration gate → schema init "
                         "→ seed → cache warm-up startup sequence")
        return

    text = read_text(lifespan) or ""
    expected_signals = [
        ("migration", r"alembic|migration|upgrade"),
        ("schema_init", r"create_all|init_db|schema"),
        ("seed", r"seed|treasury_seeder"),
        ("cache_warm", r"cache.*warm|warm.*cache|redis.*init"),
    ]
    missing = []
    for name, pattern in expected_signals:
        if not re.search(pattern, text, re.I):
            missing.append(name)

    if missing:
        rep.add(YEL, "P4", "backend", "backend/lifespan.py",
                f"lifespan.py missing startup signal(s): {', '.join(missing)} (§7.2)",
                intended="lifespan should boot: migration gate → schema init (dev) "
                         "→ seed → cache warm-up")

def check_get_db_single_session(repo: Path, rep: Report, eff: dict) -> None:
    """§3: get_db() is the only session source; services own transactions."""
    backend = repo / "backend"
    db_dir = backend / "db"
    if not db_dir.exists():
        return

    # Check that get_db exists in database.py
    database_py = db_dir / "database.py"
    if not database_py.exists():
        return

    text = read_text(database_py) or ""
    if not re.search(r"def\s+get_db\s*\(", text):
        rep.add(YEL, "DBA02", "backend", "backend/db/database.py",
                "get_db() dependency not found in db/database.py (§3)",
                intended="get_db() must be the single session source; "
                         "services own transactions")

    # Check for multiple session factories
    session_factory_re = re.compile(r"sessionmaker\s*\(")
    factories = session_factory_re.findall(text)
    if len(factories) > 1:
        rep.add(YEL, "DBA02", "backend", "backend/db/database.py",
                f"{len(factories)} sessionmaker() calls in database.py — "
                f"multiple session sources (§3)",
                intended="use exactly one sessionmaker bound to get_db()")

def check_jwt_jti_blacklist(repo: Path, rep: Report, eff: dict) -> None:
    """§4: JWT validated with jti blacklist."""
    backend = repo / "backend"
    auth_files = [
        backend / "utils" / "auth.py",
        backend / "controllers" / "auth_controller.py",
    ]
    has_jti = False
    for f in auth_files:
        if f.exists():
            t = read_text(f) or ""
            if re.search(r"jti|blacklist|token_blacklist", t, re.I):
                has_jti = True
                break
    if not has_jti:
        rep.add(YEL, "SEC4", "backend", "backend/utils/auth.py",
                "no JWT jti blacklist signal found (§4)",
                intended="validate JWT with jti claim + Redis blacklist")


def check_csrf_pci_prod_only(repo: Path, rep: Report, eff: dict) -> None:
    """§4: CSRF + PCI-DSS active in production only."""
    backend = repo / "backend"
    orchestrator = backend / "middleware" / "orchestrator.py"
    if not orchestrator.exists():
        return
    text = read_text(orchestrator) or ""
    # Check if CSRF/PCI middleware is conditionally added
    csrf_pattern = re.compile(r"CSRF.*prod|prod.*CSRF|IS_PRODUCTION.*CSRF", re.I)
    pci_pattern = re.compile(r"PCI.*prod|prod.*PCI|IS_PRODUCTION.*PCI", re.I)
    if re.search(r"CSRFMiddleware", text) and not csrf_pattern.search(text):
        rep.add(YEL, "SEC4", "backend", "backend/middleware/orchestrator.py",
                "CSRFMiddleware not gated on production (§4)",
                intended="CSRF + PCI-DSS should be active in production only")
    if re.search(r"PCIDSSMiddleware", text) and not pci_pattern.search(text):
        rep.add(YEL, "SEC4", "backend", "backend/middleware/orchestrator.py",
                "PCIDSSMiddleware not gated on production (§4)",
                intended="CSRF + PCI-DSS should be active in production only")


def check_async_workers_off_request(repo: Path, rep: Report, eff: dict) -> None:
    """§5: Heavy provider work runs via async_workers off the request path."""
    backend = repo / "backend"
    async_workers = backend / "providers" / "async_workers.py"
    if not async_workers.exists():
        rep.add(YEL, "PRV2", "backend", "backend/providers/async_workers.py",
                "providers/async_workers.py missing (§5)",
                intended="heavy AI/ML work must run off-request via async_workers")

def check_domain_actor_isolation(repo: Path, rep: Report, models: list, eff: dict) -> None:
    """
    ARCHITECTURE_DIAGRAM §10.3: domain schemas, each owning its `user` table
    (customer.user, supplier.user, logistics.user, admin.user, employee.user, …).
    The forbidden schemas are core/platform/identity — they must never appear in a
    table or FK reference.

    ❌ hr_employees.user_id → core.user.id         (forbidden core schema)
    ✅ hr_employees.user_id → customer.user.id     (domain schema, allowed)
    """
    for m in models:
        if not m.table:
            continue

        # Iterate through COLUMNS; FK presence is signalled by fk_target
        # (DBAColumnInfo has no is_fk field — matching DBA07's detection).
        for c in m.columns:
            target = getattr(c, "fk_target", "") or ""
            if not target:
                continue

            _fk_schema, fk_table, _fk_column = dba_parse_fk_target(target)
            if _fk_schema and _fk_schema in DBA_FORBIDDEN_SCHEMAS:
                rep.add(
                    RED, "DBA06", "database",
                    f"{m.file}:{m.line}",
                    f"forbidden schema-prefixed FK: {m.table}.{c.name} "
                    f"→ {target}. The '{_fk_schema}' schema is forbidden; "
                    f"use a domain schema instead (e.g. customer.user.id).",
                    intended="use a domain schema (customer/supplier/logistics/admin/employee/…), "
                             f"not core/platform/identity",
                )

# ============================================================================
# SECTION 37: RENDER — SINGLE COMPREHENSIVE MARKDOWN REPORT
# ============================================================================

def render_markdown(repo, rep, out, summary, placements, eff, reg, graph) -> None:
    """Render the single SYSTEM_AUDIT_REPORT.md with target diagrams,
    feature-wise and file-wise problem tracking."""
    n_red, n_yel, n_grn = summary["red"], summary["yellow"], summary["green"]
    debt = summary.get("debt_score", 0)

    L: list[str] = []
    L += [
        "# ZOZI System Audit Report (target-contract aligned)",
        "",
        f"> **Generated:** {summary.get('timestamp', '')}  ",
        f"> **Repo:** `{repo}`  ",
        f"> **Result:** 🔴 {n_red} violations · 🟡 {n_yel} advisories · 🟢 {n_grn} info  ",
        f"> **Architecture Debt Score:** {debt}  ",
        "**Ephemeral. Add to `.gitignore`.**",
        "",
        "---", "",
    ]

    # ── §1 Target layer contract (ARCHITECTURE_DIAGRAM.md: three axes + seven laws) ──
    L += [
        "## 1. The Grid Line (Target Layer Contract — ARCHITECTURE_DIAGRAM.md)", "",
        "Three orthogonal axes: (1) **Module** `modules/{actor}/`, "
        "(2) **Domain** `domains/{domain}/`, (3) **Feature** `rbac/` via `require_feature()`.",
        "",
        "| Layer (axis) | May import | Must NOT (law) |",
        "|---|---|---|",
        "| modules/* (AXIS 1) | domains/*/services, rbac (require_feature) | other modules (compose, don't reach in); infrastructure/DB access (law 2: thin routers, delegate to domains/*/services); abolished root layers (controllers/ routers/ services/ models/ db/ utils/) |",
        "| domains/* (AXIS 2) | infrastructure (read-only), kernel, providers, events, subscribers, ports (cross-domain only via ports/events) | modules/* (law 1: arrows point DOWN, never import rbac); other domains except via ports/events (law 3) |",
        "| rbac/* (AXIS 3) | kernel, infrastructure | modules/*, domains/* business logic (imported BY modules+middleware only) |",
        "| infrastructure/* | kernel, providers, db(read-only), utils | modules/*, domains/* (law 1: imports nothing above it) |",
        "| kernel/* | (nothing above) | any app layer |",
        "| providers/* | providers._base, infrastructure, kernel | modules/*, domains/* |",
        "| jobs/* | domains/*, infrastructure, providers | routers, main |",
        "| middleware/* | infrastructure(read-only), kernel, rbac | modules/*, domains/*, routers (law: middleware imports downward only; may import rbac per diagram) |",
        "| frontend/src/lib/api/* | backend /api/v1/* only | direct DB; raw fetch from pages; abolished root layers |",
        "",
        "**Seven Laws:** (1) modules→domains→infrastructure, arrows down only; "
        "(2) routers delegate to ONE domains/*/services call (thin routers; no DB writes); "
        "(3) cross-domain only via `ports.py`/`events.py`/`subscribers.py`; "
        "(4) `require_feature()` is the single source of truth for capabilities; "
        "(5) middleware/providers/infrastructure never import upward; "
        "(6) domain models declare `__table_args__ = {'schema': '<domain>'}`; "
        "(7) `DOMAIN_ALLOWLIST.yaml` may only shrink (allowlist rule).",
        "Abolished flat root layers (controllers/, routers/, services/, models/, db/, utils/) "
        "are **violations**, not targets.",
        "", "---", "",
    ]

    # ── §2 Target diagrams from ARCHITECTURE_DIAGRAM.md ──
    L += [TARGET_ARCHITECTURE_DIAGRAM, "", "---", ""]

    # ── §3 AI placement contract ──
    L += ["## 3. AI File Placement Contract", "",
           generate_ai_placement_contract(), "", "---", ""]

    # ── §4 Scorecard ──
    L += ["## 4. Scorecard", "",
           "| Code | Count | Sev | Meaning |",
           "|---|---:|---|---|"]
    for code in sorted(rep.counters):
        sev = next((f.sev for f in rep.findings if f.code == code), GRN)
        L.append(f"| {code} | {rep.counters[code]} | {SEV_ICON[sev]} {sev} | {RULE_MEANING.get(code, '')} |")
    L += ["", "---", ""]

    # ── §5 Hotlist ──
    hot = sorted([f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED],
                  key=lambda f: (0 if f.sev == RED else 1, f.code))
    L += ["## 5. 🔥 Damage Hotlist (fix these first)", "",
           "| Sev | Rule | Domain | Location | Problem | Fix |",
           "|---|---|---|---|---|---|"]
    for f in hot:
        L.append(f"| {SEV_ICON[f.sev]} | {f.code} | {f.domain} | `{f.loc()}` | {f.message} | {f.intended or '-'} |")
    L += ["", "---", ""]

    # ── §6 By domain ──
    by_dom: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        by_dom[f.domain].append(f)
    L += ["## 6. All Findings by Domain", ""]
    for dom in ordered_report_domains(rep):
        items = by_dom.get(dom, [])
        if not items:
            continue
        L += [f"### {dom.upper()} ({len(items)} findings)", ""]
        for f in items:
            L.append(f"- {SEV_ICON[f.sev]} **{f.code}** `{f.loc()}` — {f.message}"
                      + (f" → *{f.intended}*" if f.intended else ""))
        L.append("")
    L += ["---", ""]

    # ── §7 By FEATURE (trackable buckets) ──
    by_feat: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        if f.sev == GRN:
            continue
        by_feat[feature_of_path(f.path)].append(f)
    L += ["## 7. Problems by Feature (cumulative view)", "",
           "| Feature | 🔴 | 🟡 | Total | Top codes |",
           "|---|---:|---:|---:|---|"]
    feat_rows = []
    for feat, items in by_feat.items():
        r = sum(1 for x in items if x.sev == RED)
        y = sum(1 for x in items if x.sev == YEL)
        codes = sorted({x.code for x in items})
        feat_rows.append((feat, r, y, len(items), codes))
    for feat, r, y, tot, codes in sorted(feat_rows, key=lambda t: (-t[1], -t[3])):
        L.append(f"| `{feat}` | {r} | {y} | {tot} | {', '.join(codes[:8])} |")
    L += ["", "---", ""]

    # ── §8 By FILE (worst first, per-file problem list) ──
    by_file: dict[str, list[Finding]] = defaultdict(list)
    for f in rep.findings:
        if f.sev == GRN or not f.path:
            continue
        by_file[f.path].append(f)
    L += ["## 8. Problems by File (worst first)", ""]
    file_rows = sorted(by_file.items(),
                       key=lambda kv: (-sum(1 for x in kv[1] if x.sev == RED), -len(kv[1])))
    for path, items in file_rows[:100]:
        r = sum(1 for x in items if x.sev == RED)
        y = sum(1 for x in items if x.sev == YEL)
        L += [f"### `{path}`  (🔴 {r} · 🟡 {y})", ""]
        for x in items:
            line_info = f":{x.line}" if x.line else ""
            L.append(f"- {SEV_ICON[x.sev]} **{x.code}**{line_info} — {x.message}"
                      + (f" → *{x.intended}*" if x.intended else ""))
        L.append("")
    L += ["---", ""]

    # ── §9 Move suggestions ──
    if placements:
        L += ["## 9. File Move Suggestions", "",
               f"**{len(placements)} file(s) need relocation:**", "",
               "| # | Current | Suggested | Reason | Confidence |",
               "|---:|---|---|---|---:|"]
        for i, p in enumerate(placements, 1):
            L.append(f"| {i} | `{p['from']}` | `{p['to']}` | {p.get('reason', '')} | {p.get('confidence', 0):.0%} |")
        L += ["", "---", ""]

    # ── §10 Metrics ──
    L += ["## 10. Architecture Metrics", "",
           f"- **Debt Score:** {debt}",
           f"- **Modules:** {summary['modules']}",
           f"- **Edges:** {summary['edges']}",
           f"- **Classes:** {summary['classes']}", ""]
    if summary.get("top_fan_in"):
        L += ["### Top Fan-In", "", "| Module | Fan-In |", "|---|---:|"]
        for m, c in summary["top_fan_in"]:
            L.append(f"| `{m}` | {c} |")
        L.append("")
    L += ["---", ""]

    # ── §11 Auto-discovery ──
    if summary.get("auto_discovery"):
        ad = summary["auto_discovery"]
        L += ["## 11. Auto-Discovery Summary", "",
               f"- Domains: {ad.get('domains', 0)} · Features: {ad.get('features', 0)} ·  "
               f"FE features: {ad.get('frontend_features', 0)} · Cross-domain edges: {ad.get('domain_edges', 0)}", ""]

    # ── §12 Database summary ──
    if "database" in summary:
        db = summary["database"]
        L += ["## 12. Database Audit Summary", "",
               f"- Models: {db.get('models', 0)} · Tables: {db.get('tables', 0)} ·  "
               f"Heads: {', '.join(db.get('migration_heads', [])) or 'none'} · RLS tables: {db.get('rls_tables', 0)}",
               "", "---", ""]

    # ── §13 Design summary ──
    if "design" in summary:
        ds = summary["design"]
        L += ["## 13. Design Audit Summary", "",
               f"- Palette tokens: {ds.get('palette_tokens', 0)} · Coverage: {ds.get('coverage', 0):.1f}%",
               "", "---", ""]

    # ── §14 Health summary ──
    if "health" in summary:
        hl = summary["health"]
        L += ["## 14. Health & Scaling Summary", "",
               f"**Health Score: {hl.get('health_score', 0)}/100 ({hl.get('grade', '?')})**", "",
               generate_executive_summary(rep, hl.get('health_score', 0), hl.get('grade', '?')), "",
               "### Top 20 Unhealthiest Files", "",
               "| # | File | Weight | Issues |",
               "|---|---|---:|---|"]
        for i, item in enumerate(hl.get("file_ranking", []), 1):
            L.append(f"| {i} | `{item['file']}` | {item['weight']} | {', '.join(item['codes'])} |")
        L += ["", "---", "",
               generate_health_contract(), "", "---", "",
               "## Recommended Pipeline", "",
               generate_pipeline_mermaid(), "", "---", "",
               generate_fix_patterns_section(), ""]

    L += ["---", "",
           "> **Single source of truth:** this report validates the codebase against ARCHITECTURE_DIAGRAM.md (target).",
           "> Fix RED first, then YELLOW. Work file-by-file using §8.", ""]

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

# ============================================================================
# SECTION 38: MAIN — ZERO ARGUMENTS, FULLY INDEPENDENT
# ============================================================================

# ============================================================================
# SECTION 69: ARCHITECTURE_DIAGRAM.md COMPLIANCE GATE
# ----------------------------------------------------------------------------
# Hard-codes the authoritative target from documents/ARCHITECTURE_DIAGRAM.md so the
# audit verifies ACTUAL structure instead of trusting migration claims.
# Stops "cheating" AIs that report 100% placement while old layers persist.
# ============================================================================

ARCHITECTURE_DIAGRAM_SPEC = "documents/ARCHITECTURE_DIAGRAM.md"

ARCH_AXIS_REQUIRED_PACKAGES = ("modules", "domains", "rbac", "infrastructure",
                                "kernel", "middleware", "alembic")
ARCH_AXIS_ADVISORY_PACKAGES = ("kernel", "providers", "jobs", "middleware", "alembic")

# Abolished flat root layers - must NOT exist at backend root
# (per documents/ARCHITECTURE_DIAGRAM.md §1 forbidden root layers).
ARCH_ABOLISHED_ROOT_LAYERS = {
    "controllers": "NS1",   # controllers layer abolished; split into module routers + domain services
    "routers":     "NS2",   # routers must be modules/{actor}/routers/, not flat at root
    "services":    "NS3",   # services must be domains/{domain}/services/, not flat at root
    "models":      "NS4",   # models must be domains/{domain}/models/, not flat at root
    "db":          "NS23",  # db must be infrastructure/database/
    "utils":       "NS24",  # utils must be infrastructure/utils/ + kernel/
}

# Non-canonical backend root dirs. ARCHITECTURE_DIAGRAM.md §1 defines a CLOSED set for
# backend/ root (main.py, config.py, DOMAIN_ALLOWLIST.yaml, modules/, domains/,
# rbac/, infrastructure/, providers/, jobs/, middleware/, alembic/, scripts/,
# tests/). Anything else at backend root is a stray package that the
# audit must flag — these are NOT abolition targets (they have no prescribed
# home), they are "this package has no home in the target architecture".
ARCH_NON_CANONICAL_ROOT_LAYERS = {
    "tasks":       "NS27",  # tasks/ is not a target root layer; background work lives in jobs/
    "events":      "NS28",  # events/ is not a target root layer; events live per domain (events.py)
    "uploads":     "NS29",  # uploads/ is not a target root layer; media lives in infrastructure/storage/
    "var":         "NS30",  # var/ is not a target root layer; runtime state is not a backend package
    "venv":        "NS31",  # venv/ is not a target root layer; it is tooling, not app structure
    "tools":       "NS32",  # tools/ is not a target root layer; one-off migration helpers, not app structure
    # Generic stray root packages that also have no home in the target architecture.
    # Flagged RED when they contain Python so common AI-created strays (api/,
    # handlers/, app/, core/, common/, lib/) cannot hide from the closed-set check.
    "api":         "NS27",  # api/ is not a target root layer; route surfaces live under modules/{actor}/routers/
    "handlers":    "NS27",  # handlers/ is not a target root layer; use modules/{actor}/routers/
    "app":         "NS27",  # app/ is not a target root layer; app bootstrap is main.py
    "core":        "NS27",  # core/ is a forbidden word (law 6); primitives belong in kernel/
    "common":      "NS27",  # common/ is not a target root layer; share via kernel/ or infrastructure/
    "lib":         "NS27",  # lib/ is not a target root layer; platform code lives in infrastructure/
}

# Prescribed ARCHITECTURE_DIAGRAM backend layers (documents/ARCHITECTURE_DIAGRAM.md).
ARCH_CANONICAL_BACKEND_LAYERS = {
    "modules", "domains", "rbac", "infrastructure", "kernel",
    "providers", "jobs", "middleware",
}
# Abolished flat root layers — included in scan sets ONLY so the transitional
# codebase is still scanned and reported (NS1-NS4). They are violation targets,
# never canonical homes.
ABOLISHED_BACKEND_LAYERS = {
    "controllers", "routers", "services", "models",
    "db", "utils",
}
# Union used by quality/health scans that iterate backend top-level layers.
BACKEND_SCAN_LAYERS = ARCH_CANONICAL_BACKEND_LAYERS | ABOLISHED_BACKEND_LAYERS

ARCH_MODULE_ACTORS = {"customer", "supplier", "logistics", "admin", "employee"}
ARCH_DOMAIN_FOLDERS = {
    "finance", "accounts", "catalog", "orders", "payments", "logistics",
    "suppliers", "customers", "hr", "comms", "media", "country", "governance",
}

# Sub-package names that represent a domain's *internal* business logic. Importing
# another domain's internals directly (instead of via ports.py / events.py) is the
# cross-domain violation caught by NS8 (law 3).
_NS_CROSS_DOMAIN_BLOCKED = {
    "services", "models", "repositories", "schemas", "policies",
}

# Layers an infrastructure package must NEVER import (law 1).
_INFRA_FORBIDDEN_IMPORTS = {
    "modules", "domains", "rbac", "providers", "jobs", "services",
    "models", "controllers", "routers", "events",
}

# kernel/ is a pure shared kernel: domains -> kernel -> (nothing). It may import
# infrastructure (platform primitives) but nothing above it.
_NS_KERNEL_FORBIDDEN_IMPORTS = {
    "modules", "domains", "rbac", "providers", "jobs", "middleware",
    "controllers", "services", "models", "db", "utils", "core", "dependencies",
}


def _ns_backend_root(repo: Path) -> Path:
    cand = repo / "backend"
    return cand if cand.is_dir() else repo


def _ns_norm_allow_pair(item: str) -> tuple[str, str]:
    """Normalise a DOMAIN_ALLOWLIST entry to a (src, dst) domain pair."""
    item = item.strip().strip("'\"")
    for sep in (">>", "->", "=>", ">", ":", " "):
        if sep in item:
            a, b = item.split(sep, 1)
            return (a.strip(), b.strip())
    return (item.strip(), item.strip())


def _ns_load_domain_allowlist(backend: Path) -> set[tuple[str, str]]:
    """Parse backend/DOMAIN_ALLOWLIST.yaml -> set of (src, dst) domain pairs that
    are permitted as temporary cross-domain import debt (allowlist rule (Law 7), law 7).

    Dependency-free: handles both flow style (`[a>b, c>d]`) and block style
    (`- a>b`). The file is optional; an empty/absent file yields an empty set,
    meaning every cross-domain service/model/repo/schema/policy import is flagged.
    """
    allow: set[tuple[str, str]] = set()
    p = backend / "DOMAIN_ALLOWLIST.yaml"
    if not p.is_file():
        return allow
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return allow
    m = re.search(r"cross_domain_imports:\s*(.*?)(?:\n\S|\Z)", text, re.S)
    if not m:
        return allow
    body = m.group(1)
    fm = re.match(r"\s*\[(.*)\]\s*$", body.strip())
    if fm:
        entries = [e for e in re.split(r",", fm.group(1)) if e.strip()]
    else:
        entries = []
        for line in body.splitlines():
            s = line.strip()
            if s.startswith("-"):
                entries.append(s[1:])
    for e in entries:
        e = e.strip().strip("'\"")
        if e:
            allow.add(_ns_norm_allow_pair(e))
    return allow


def _ns_iter_py(backend: Path, *subdirs: str):
    """Yield (path, ast.Module) for .py files under given backend subdirs."""
    for sub in subdirs:
        base = backend / sub
        if not base.is_dir():
            continue
        for p in base.rglob("*.py"):
            if set(p.parts) & DEFAULT_IGNORE_DIRS:
                continue
            try:
                tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            yield p, tree


# --- consumer-side import-debt helpers (NS12/NS14) ---
_AXIS_IMPORT_TOPS = {"domains", "modules", "rbac", "infrastructure", "kernel"}








def _ns_scan_inverted_arrows(backend):
    hits = []
    for layer in ("middleware", "providers", "infrastructure"):
        if not (backend / layer).is_dir():
            continue
        for p, tree in _ns_iter_py(backend, layer):
            for node in ast.walk(tree):
                mod = None
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                elif isinstance(node, ast.Import):
                    mod = node.names[0].name
                if not mod:
                    continue
                top = mod.split(".")[0]
                if top in ("domains", "modules", "rbac", "services", "controllers", "routers", "models"):
                    hits.append((p, node.lineno, "layer '" + layer + "' imports upward app layer: '" + mod + "'"))
    return hits


def _ns_scan_country_scope(backend):
    hits = []
    dom = backend / "domains"
    if (dom / "country").is_dir():
        return hits
    if dom.is_dir():
        for p in dom.rglob("*.py"):
            if set(p.parts) & DEFAULT_IGNORE_DIRS:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"country", text, re.I) and "Column" in text:
                hits.append((dom, 0, "country-scoped data (country columns) present but no domains/country scoping axis"))
                break
    return hits


_TABLE_ARGS_RE = re.compile(r"__table_args__\s*=\s*\(")
_SCHEMA_ARG_RE = re.compile(r"schema\s*=\s*['\"]([^'\"]+)['\"]")
def _ns_scan_schema_discipline(backend):
    hits = []
    dom = backend / "domains"
    if not dom.is_dir():
        return hits
    for p in dom.rglob("*.py"):
        if set(p.parts) & DEFAULT_IGNORE_DIRS:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "__tablename__" not in text:
            continue
        if not _TABLE_ARGS_RE.search(text):
            hits.append((p, 0, "model without __table_args__ (schema discipline missing)"))
        elif not _SCHEMA_ARG_RE.search(text):
            hits.append((p, 0, "__table_args__ present but lacks schema='<domain>' (Law 6)"))
    return hits


# Abolished flat root layers whose import names still count as abolished-layer
# import debt (the not-yet-migrated surface of the codebase).
_NS_AXIS_IMPORT_ROOTS = {"modules", "domains", "rbac", "infrastructure", "kernel", "providers", "jobs", "middleware"}

# Abolished flat root layers (per ARCHITECTURE_DIAGRAM.md Law 1 + Seven Laws).
# These are layer names that, when found as top-level import roots, indicate
# code still living in abolished flat layers rather than under the canonical
# axis-protected locations.
_NS_ABOLISHED_IMPORT_ROOTS = {
    "controllers", "routers", "services", "models", "db", "utils",
}


def _ns_scan_import_debt(backend: Path):
    """Count import statements binding to abolished flat layers (abolished-layer
    debt) vs the NEW axis packages (new adoption).

    Returns (abolished_count, new_count, abolished_by_mod, new_by_mod).
    """
    abolished_count = 0
    new_count = 0
    abolished_by_mod: dict[str, int] = {}
    new_by_mod: dict[str, int] = {}

    ignore = set(DEFAULT_IGNORE_DIRS)
    for p in sorted(backend.rglob("*.py")):
        if "site-packages" in p.parts:
            continue
        if any(part in ignore for part in p.parts):
            continue
        if p.name == "__init__.py":
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        for node in ast.walk(tree):
            mod = None
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
            elif isinstance(node, ast.Import):
                if node.names:
                    mod = node.names[0].name
            if not mod:
                continue
            top = mod.split(".")[0]
            if top in _NS_ABOLISHED_IMPORT_ROOTS:
                abolished_count += 1
                abolished_by_mod[mod] = abolished_by_mod.get(mod, 0) + 1
            elif top in _NS_AXIS_IMPORT_ROOTS:
                new_count += 1
                new_by_mod[mod] = new_by_mod.get(mod, 0) + 1

    return abolished_count, new_count, abolished_by_mod, new_by_mod


def _ns_string_values(node: "ast.AST") -> list[str]:
    """Extract string constants from a list/set/dict literal node."""
    out: list[str] = []
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                out.append(elt.value)
            else:
                out.extend(_ns_string_values(elt))
    elif isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                out.append(k.value)
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                out.append(v.value)
    return out


def _ns_collect_feature_atoms(backend: Path):
    """Collect (required_atoms, defined_atoms).

    required_atoms = atoms referenced by require_feature(...) across the backend.
    defined_atoms  = atoms registered in any domains/*/features.py (Law 4 SSoT).
    Returns (set, list) so duplicates across domains can be detected.
    """
    required_atoms: set[str] = set()
    defined_atoms: list[str] = []
    req_re = re.compile(r"require_feature\(\s*['\"]?([A-Za-z0-9_][A-Za-z0-9_\.]*?)['\"]?\s*[,)]")

    for p in sorted(backend.rglob("*.py")):
        if "site-packages" in p.parts:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in req_re.finditer(text):
            required_atoms.add(m.group(1))

    domains_dir = backend / "domains"
    if domains_dir.is_dir():
        for feat_file in sorted(domains_dir.rglob("features.py")):
            try:
                tree = ast.parse(feat_file.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for tgt in node.targets:
                        name = getattr(tgt, "id", "") or getattr(tgt, "name", "")
                        if "feature" in name.lower():
                            defined_atoms.extend(_ns_string_values(node.value))
    return required_atoms, defined_atoms


def _ns_scan_thin_router_violations(backend: Path) -> list[tuple[Path, int, str]]:
    """Routers must stay THIN (Law 2): auth context + require_feature(...) + ONE
    domain-service call. They MUST NOT:
      * import abolished/upward layers (core, db, utils, dependencies,
        controllers, infrastructure, providers, kernel, middleware, events);
      * reach past the service layer into domain repositories/models directly;
      * perform inline DB writes (session.add/commit/delete/merge/flush).
    NOTE: `from domains.<d>.services` is REQUIRED by ARCHITECTURE_DIAGRAM.md (the router
    calls exactly one domain service) and is deliberately NOT flagged here — the
    previous regex flagged it and produced hundreds of false positives on valid
    thin routers, which an AI could use to discredit the audit.
    """
    hits: list[tuple[Path, int, str]] = []
    leak_re = re.compile(
        r"^\s*(from|import)\s+(?:backend\.)?(?:"
        r"(?:core|db|utils|dependencies|controllers|infrastructure|providers|"
        r"kernel|middleware|events)\b"
        r"|domains\.\w+\.(repositories|models)\b)"
    )
    write_re = re.compile(
        r"\b(?:session|db|conn|connection)\.(?:add|commit|delete|merge|flush|"
        r"bulk_insert_mappings|bulk_save_objects|bulk_update_mappings)\s*\("
    )
    for p in sorted(backend.rglob("*.py")):
        if "site-packages" in p.parts or "routers" not in p.parts:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, 1):
            if leak_re.search(line) or write_re.search(line):
                hits.append((p, i, line.strip()))
    return hits


def _ns_scan_router_feature_gate(backend: Path) -> list[tuple[Path, int, str]]:
    """Law 4 / Law 2: module routers must gate with rbac.dependencies.require_feature
    (the Feature axis) — NOT the pre-ARCHITECTURE_DIAGRAM per-module auth helpers (require_admin,
    require_finance_permission, require_employee, ...). Flag module routers that
    expose routes behind an abolished per-module gate instead of require_feature/require_module.
    Public/webhook routers (public_*/webhook) are exempt.

    This closes a real compliance gap: a migration can create modules/*/routers/
    and domains/*/features.py yet never WIRE require_feature into the routes, so
    the Feature axis exists on paper but is not enforced. That is a "claimed but
    not done" migration that directory checks alone cannot catch.
    """
    hits: list[tuple[Path, int, str]] = []
    route_re = re.compile(r"@\w*(router|api)\.(get|post|put|delete|patch|options|head)\(")
    rbac_gate_re = re.compile(r"require_feature|require_module|rbac\.dependencies")
    abolished_gate_re = re.compile(
        r"require_admin|require_finance_permission|require_employee|"
        r"require_supplier|require_logistics|require_customer|"
        r"hasAdminPermission|require_permission\b|Depends\(\s*require_"
    )
    for p in sorted(backend.rglob("*.py")):
        if "site-packages" in p.parts or "routers" not in p.parts:
            continue
        # Only module routers (modules/<actor>/routers/...).
        if "modules" not in p.parts:
            continue
        name = p.name.lower()
        if name.startswith("public_") or "webhook" in name:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        has_route = False
        has_rbac_gate = False
        abolished_gate_line = None
        for i, line in enumerate(lines, 1):
            if route_re.search(line):
                has_route = True
            if rbac_gate_re.search(line):
                has_rbac_gate = True
            if abolished_gate_re.search(line) and abolished_gate_line is None:
                abolished_gate_line = (i, line.strip())
        if not has_route or has_rbac_gate:
            continue
        if abolished_gate_line is not None:
            hits.append((p, abolished_gate_line[0], abolished_gate_line[1]))
        else:
            hits.append((p, 0, "module router exposes routes with NO require_feature/require_module gate (Feature axis unwired)"))
    return hits


def _ns_scan_module_actor_violations(backend: Path, actors: set[str]) -> list[tuple[Path, int, str]]:
    """Flag module files whose top actor segment is not a recognised actor (Law 5)."""
    hits: list[tuple[Path, int, str]] = []
    modules_dir = backend / "modules"
    if not modules_dir.is_dir():
        return hits
    for p in sorted(modules_dir.rglob("*.py")):
        parts = p.relative_to(modules_dir).parts
        if len(parts) > 1 and parts[0] not in actors:
            hits.append((p, 0, "module under non-standard actor segment '" + parts[0] + "/'"))
    return hits


# NEW compliance checks: NS38-NS43 (ARCHITECTURE_DIAGRAM.md section 3 gate)
_ARCH_BACKEND_ROOT_CLOSED_SET = {
    "main.py", "config.py", "DOMAIN_ALLOWLIST.yaml",
    "modules", "domains", "rbac", "kernel", "infrastructure",
    "providers", "jobs", "middleware", "alembic", "scripts", "tests",
}

# Build/cache/venv artifacts are NEVER architecture packages. They must be
# ignored by the closed-root and module-internals scans so the audit does not
# emit false-positive violations for generated folders (e.g. __pycache__).
_NS_IGNORED_DIRS = {
    "__pycache__", ".venv", "venv", "env", "node_modules", ".git",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox", ".eggs",
    "htmlcov", "dist", "build", ".idea", ".vscode",
}



def _ns_scan_domain_features(backend):
    # NS39: every domain must seed features.py (Law 4 single source).
    hits = []
    dom = backend / "domains"
    if not dom.is_dir():
        return hits
    for d in sorted(dom.iterdir()):
        if not d.is_dir():
            continue
        if d.name in _NS_IGNORED_DIRS:
            continue
        if not (d / "features.py").is_file():
            if any(d.rglob("*.py")):
                hits.append((d, 0, d.name))
    return hits


def _ns_scan_module_internals(backend):
    # NS40: each actor needs auth/ + routers/ + serializers/ (Axis 1).
    hits = []
    mod = backend / "modules"
    if not mod.is_dir():
        return hits
    for actor in sorted(mod.iterdir()):
        if not actor.is_dir():
            continue
        if actor.name in _NS_IGNORED_DIRS:
            continue
        missing = [x for x in ("auth", "routers", "serializers") if not (actor / x).is_dir()]
        if missing:
            hits.append((actor, 0, actor.name + " missing " + ", ".join(missing)))
    return hits


def _ns_scan_thin_router_calls(backend):
    # NS41: a module router endpoint must call at most ONE domain service (Law 2).
    hits = []
    route_attrs = {"get", "post", "put", "delete", "patch", "options", "head"}
    for p in sorted(backend.rglob("*.py")):
        if "site-packages" in p.parts or "routers" not in p.parts or "modules" not in p.parts:
            continue
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(src)
        except (OSError, SyntaxError):
            continue
        lines = src.splitlines()
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            is_route = False
            for dec in fn.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if dec.func.attr in route_attrs:
                        is_route = True
                        break
            if not is_route:
                continue
            lo = fn.lineno
            hi = getattr(fn, "end_lineno", fn.lineno)
            func_src = "\n".join(lines[lo - 1:hi])
            doms = set(re.findall(r"domains\.(\w+)\.services\b", func_src))
            if len(doms) > 1:
                hits.append((p, lo, "endpoint '" + fn.name + "' calls >1 domain service: " + ", ".join(sorted(doms))))
    return hits


def _ns_scan_tests_architecture(backend):
    # NS42: contract tests present in tests/architecture/.
    ta = backend / "tests" / "architecture"
    if not ta.is_dir():
        return False
    return (ta / "test_import_laws.py").is_file() and (ta / "test_feature_catalog.py").is_file()


def _ns_scan_heavy_domains(backend):
    # NS43: heavy domain (>8 services, no slicing) should be sliced.
    hits = []
    dom = backend / "domains"
    if not dom.is_dir():
        return hits
    for d in sorted(dom.iterdir()):
        if d.name in _NS_IGNORED_DIRS:
            continue
        svc = d / "services"
        if not svc.is_dir():
            continue
        py = [f for f in svc.iterdir() if f.is_file() and f.suffix == ".py" and f.name != "__init__.py"]
        subdirs = [f for f in svc.iterdir() if f.is_dir()]
        if len(py) > 8 and not subdirs:
            hits.append((d.name, len(py)))
    return hits


def check_architecture_diagram_compliance(repo: Path, rep: "Report", eff) -> None:
    """Verify the repo against documents/ARCHITECTURE_DIAGRAM.md (compliance gate).

    Detects:
      * abolished root layers still present (NS1-NS4)
      * missing required ARCHITECTURE_DIAGRAM axis packages (NS5)
      * domain -> module inverted arrow (NS6)
      * infrastructure importing above it (NS7)
      * cross-domain import bypassing ports/events (NS8)
      * root models/ still canonical while domain models absent (NS11)
      * consumers still importing abolished flat layers (import debt) (NS12)
       * real ARCHITECTURE_DIAGRAM axis adoption ratio vs abolished-layer import debt (NS14)
    """
    backend = _ns_backend_root(repo)
    if not backend.is_dir():
        rep.add(RED, "NS5", "backend", str(backend),
                "backend directory not found; cannot verify ARCHITECTURE_DIAGRAM.md compliance",
                intended="backend/ present with modules/ domains/ rbac/ infrastructure/",
                priority="P1")
        return

    rep.add(GRN, "NS0", "backend", ARCHITECTURE_DIAGRAM_SPEC,
            "Compliance gate active against authoritative spec documents/ARCHITECTURE_DIAGRAM.md "
            "(three axes + seven laws). Abolished layers at backend root are violations; "
            "migration claims are verified against the actual tree, not trusted.",
            priority="P3")

    # --- NS1-NS4: abolished root layers ---
    for layer, code in ARCH_ABOLISHED_ROOT_LAYERS.items():
        if (backend / layer).is_dir():
            rep.add(RED, code, "backend", "backend/" + layer + "/",
                    "Abolished/re-homed layer backend/" + layer + "/ still exists at backend root. "
                    "ARCHITECTURE_DIAGRAM.md abolishes or re-homes this layer. Its presence proves the "
                    "migration is incomplete; any '100% placed / migrated' claim is FALSE.",
                    intended="backend/" + layer + "/ deleted (it is an abolished/non-canonical root layer with no place at backend root)",
                    priority="P0")

    # --- NS5: missing required ARCHITECTURE_DIAGRAM axis packages ---
    for pkg in ARCH_AXIS_REQUIRED_PACKAGES:
        if not (backend / pkg).is_dir():
            rep.add(RED, "NS5", "backend", "backend/" + pkg + "/",
                    "Required ARCHITECTURE_DIAGRAM.md package backend/" + pkg + "/ is MISSING. "
                    "The target architecture cannot be satisfied without it.",
                    intended="backend/" + pkg + "/ created (AXIS package)",
                    priority="P0")
    # Advisory axis packages (providers/jobs) host 3rd-party adapters and workers.
    # Not P0-required, but their absence is worth flagging so they are not forgotten.
    for pkg in ARCH_AXIS_ADVISORY_PACKAGES:
        if pkg in ARCH_AXIS_REQUIRED_PACKAGES:
            continue
        if not (backend / pkg).is_dir():
            rep.add(YEL, "NS5", "backend", "backend/" + pkg + "/",
                    "Advisory ARCHITECTURE_DIAGRAM.md package backend/" + pkg + "/ is MISSING "
                    "(providers/jobs host 3rd-party adapters and background workers).",
                    intended="backend/" + pkg + "/ created when needed",
                    priority="P2")
    if not (backend / "kernel").is_dir():
        rep.add(YEL, "NS5", "backend", "backend/kernel/",
                "Advisory ARCHITECTURE_DIAGRAM.md package backend/kernel/ not present "
                "(refinement: shared business kernel money/numbering/country/period).",
                intended="backend/kernel/ created when business primitives are extracted",
                priority="P2")

    # --- NS27-NS31: non-canonical backend root packages ---
    # ARCHITECTURE_DIAGRAM.md §1 defines a CLOSED set for backend/ root. Any other
    # directory there is a stray package with no home in the target architecture.
    for layer, code in ARCH_NON_CANONICAL_ROOT_LAYERS.items():
        d = backend / layer
        if not d.is_dir():
            continue
        has_py = any(d.rglob("*.py"))
        if not has_py:
            continue  # empty (e.g. uploads/, var/, venv/) — not an app-structure issue
        rep.add(
            RED, code, "backend", "backend/" + layer + "/",
            f"backend/{layer}/ is NOT a target-architecture root layer. ARCHITECTURE_DIAGRAM.md "
            f"§1 defines a closed set for backend/ root (main.py, config.py, "
            f"DOMAIN_ALLOWLIST.yaml, modules/, domains/, rbac/, infrastructure/, "
            f"providers/, jobs/, middleware/, alembic/, scripts/, tests/).",
            intended={
                "tasks": "re-home background-task code into backend/jobs/ (or delete)",
                "events": "fold into backend/domains/<domain>/events.py per domain",
                "uploads": "re-home into backend/infrastructure/storage/",
                "var": "delete — runtime state is not a backend package",
                "venv": "delete from the repo — it is tooling, not app structure",
                "tools": "delete or move to scripts/ — one-off migration helpers are "
                         "not part of the runtime app structure",
                "api": "re-home route surfaces under backend/modules/{actor}/routers/",
                "handlers": "re-home HTTP handlers under backend/modules/{actor}/routers/ (or delete)",
                "app": "app bootstrap belongs in backend/main.py - delete app/",
                "core": "core/ is a forbidden word (law 6); move primitives into backend/kernel/",
                "common": "share code via backend/kernel/ or backend/infrastructure/ - delete common/",
                "lib": "platform code lives in backend/infrastructure/ - delete lib/",
            }[layer],
            priority="P1",
        )

    # --- NS38: any backend-root entry outside the closed set (ARCHITECTURE_DIAGRAM.md sec 3) ---
    CLOSED_ROOT_ENTRIES = {
        "main.py", "config.py", "DOMAIN_ALLOWLIST.yaml",
        "modules", "domains", "rbac", "infrastructure",
        "providers", "jobs", "middleware", "alembic", "scripts", "tests",
    }
    HANDLED_ROOT = (CLOSED_ROOT_ENTRIES | set(ARCH_ABOLISHED_ROOT_LAYERS)
                    | set(ARCH_NON_CANONICAL_ROOT_LAYERS)
                    | set(ARCH_AXIS_REQUIRED_PACKAGES)
                    | set(ARCH_AXIS_ADVISORY_PACKAGES))
    for full in sorted(backend.iterdir()):
        if not full.is_dir():
            continue
        entry = full.name
        if (entry.startswith(".") or entry in HANDLED_ROOT
                or entry in _NS_IGNORED_DIRS):
            continue
        rep.add(RED, "NS38", "backend", "backend/" + entry + "/",
                f"backend/{entry}/ is outside the closed root set defined by "
                f"ARCHITECTURE_DIAGRAM.md sec 3 (main.py . config.py . DOMAIN_ALLOWLIST.yaml . "
                f"modules/ domains/ rbac/ kernel/ infrastructure/ providers/ jobs/ middleware/ "
                f"alembic/ scripts/ tests/).",
                intended=f"re-home backend/{entry}/ into the target architecture or delete it",
                priority="P1")

    # --- NS11: root models/ canonical while domain models absent ---
    root_models = backend / "models"
    dom_models_present = False
    if (backend / "domains").is_dir():
        for d in (backend / "domains").iterdir():
            if d.is_dir() and (d / "models").is_dir() and any((d / "models").rglob("*.py")):
                dom_models_present = True
                break
    if root_models.is_dir() and any(root_models.rglob("*.py")) and not dom_models_present:
        rep.add(RED, "NS11", "backend", "backend/domains/",
                "root backend/models/ is still the canonical ORM home while NO domain owns "
                "models under domains/*/models/. The model migration claimed by ARCHITECTURE_DIAGRAM.md "
                "has NOT been performed. Refusing 'models placed' claims: content is not actually "
                "in the new architecture.",
                intended="ORM modules relocated into domains/*/models/; root models/ deleted",
                priority="P0")

    # --- NS6 / NS8: inverted arrows + illegal cross-domain imports (AST scan) ---
    # NOTE: NS8 must ONLY flag a GENUINE cross-domain import (importer domain !=
    # target domain). A service importing its OWN domain's models/services
    # (e.g. domains/finance/services/foo.py -> domains/finance/models) is normal
    # and was previously false-flagged ~thousands of times, which let a "migration
    # done" claim dismiss the whole audit as noisy. ports.py / events.py / read_models
    # remain the always-allowed cross-domain paths (they are not in the blocked set).
    if (backend / "domains").is_dir():
        allow = _ns_load_domain_allowlist(backend)
        seen_xd: set[tuple[str, str]] = set()
        for p, tree in _ns_iter_py(backend, "domains"):
            rel_parts = p.relative_to(backend).parts
            imp_dom = rel_parts[1] if len(rel_parts) > 1 and rel_parts[0] == "domains" else None
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.level == 0:
                    mod = node.module or ""
                    top = mod.split(".")[0]
                    if top == "modules":
                        rep.add(RED, "NS6", "domains", str(p),
                                "domain imports module layer: 'from " + mod + " import ...' "
                                "(law 1: arrows point down; domains never import modules).",
                                intended="move logic into a domain service; modules compose domains",
                                line=node.lineno, priority="P0")
                    elif top == "rbac":
                        rep.add(RED, "NS36", "domains", str(p),
                                "domain imports rbac layer: 'from " + mod + " import ...' "
                                "(law 4: rbac is imported by modules/middleware only; domains "
                                "enforce policies, not permissions).",
                                intended="domains must not depend on rbac; gating belongs in module routers",
                                line=node.lineno, priority="P0")
                    elif top == "domains" and len(mod.split(".")) >= 3:
                        parts = mod.split(".")
                        tgt = parts[1]
                        # ports.py / events.py / read_models/ are the sanctioned
                        # cross-domain paths (law 3) — never flagged.
                        if (tgt in ARCH_DOMAIN_FOLDERS
                                and tgt != imp_dom
                                and any(seg in _NS_CROSS_DOMAIN_BLOCKED for seg in parts[2:])
                                and not mod.startswith("domains." + tgt + ".ports")
                                and not mod.startswith("domains." + tgt + ".events")
                                and not mod.startswith("domains." + tgt + ".read_models")):
                            seen_xd.add((imp_dom, tgt))
                            if (imp_dom, tgt) in allow:
                                rep.add(YEL, "NS8", "domains", str(p),
                                        "allowlisted cross-domain import (temporary cross-domain import debt): 'from "
                                        + mod + " import ...' per DOMAIN_ALLOWLIST.yaml (importer='"
                                        + str(imp_dom) + "'). This debt must shrink to zero.",
                                        intended="route cross-domain reads via domains/<d>/ports.py",
                                        line=node.lineno, priority="P2")
                            else:
                                rep.add(RED, "NS8", "domains", str(p),
                                        "cross-domain import bypasses ports/events: 'from " + mod +
                                        " import ...' (law 3; importer domain='" + str(imp_dom)
                                        + "').",
                                        intended="cross-domain reads via domains/<d>/ports.py; writes via events.py/subscribers.py",
                                        line=node.lineno, priority="P0")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] == "modules":
                            rep.add(RED, "NS6", "domains", str(p),
                                    "domain imports module layer: 'import " + alias.name + "' (law 1).",
                                    line=node.lineno, priority="P0")
        # Compliance check: an allowlist entry that matches NO real cross-domain import
        # cannot be silencing the audit — flag it as probable pre-emption.
        for pair in sorted(allow - seen_xd):
            rep.add(YEL, "NS37", "backend", "backend/DOMAIN_ALLOWLIST.yaml",
                    "allowlist entry '" + pair[0] + ">" + pair[1] + "' references no actual "
                    "cross-domain import in the code (DOMAIN_ALLOWLIST.yaml must track REAL debt "
                    "and shrink to zero; a phantom entry cannot pre-empt NS8).",
                    intended="remove phantom entries; only list imports that exist", priority="P2")

    # --- NS7: infrastructure imports above it ---
    if (backend / "infrastructure").is_dir():
        for p, tree in _ns_iter_py(backend, "infrastructure"):
            for node in ast.walk(tree):
                mod = None
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                elif isinstance(node, ast.Import):
                    mod = node.names[0].name
                if mod and mod.split(".")[0] in _INFRA_FORBIDDEN_IMPORTS:
                    rep.add(RED, "NS7", "infrastructure", str(p),
                            "infrastructure imports above it: 'from " + mod + " import ...' "
                            "(law 1: infrastructure imports nothing above it).",
                            intended="infrastructure is platform-only; move business/domain code out",
                            line=node.lineno, priority="P0")

    # --- NS34: kernel/ must import nothing above it (law: domains -> kernel -> nothing) ---
    if (backend / "kernel").is_dir():
        for p, tree in _ns_iter_py(backend, "kernel"):
            for node in ast.walk(tree):
                mod = None
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                elif isinstance(node, ast.Import):
                    mod = node.names[0].name
                if mod and mod.split(".")[0] in _NS_KERNEL_FORBIDDEN_IMPORTS:
                    rep.add(RED, "NS34", "kernel", str(p),
                            "kernel imports above it: 'from " + mod + " import ...' "
                            "(law: domains -> kernel -> nothing; kernel is a pure shared kernel of "
                            "business primitives: money/numbering/country/period).",
                            intended="kernel imports only stdlib + infrastructure platform primitives",
                            line=node.lineno, priority="P1")

    # --- NS35: modules must not import providers (law 1: providers <- services/jobs) ---
    if (backend / "modules").is_dir():
        for p, tree in _ns_iter_py(backend, "modules"):
            for node in ast.walk(tree):
                mod = None
                if isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                elif isinstance(node, ast.Import):
                    mod = node.names[0].name
                if mod and mod.split(".")[0] == "providers":
                    rep.add(RED, "NS35", "modules", str(p),
                            "module imports providers layer: 'from " + mod + " import ...' "
                            "(law 1: providers are called only by services/jobs, never by thin "
                            "module routers).",
                            intended="call the domain service; let the service call the provider",
                            line=node.lineno, priority="P0")

    # --- NS37: DOMAIN_ALLOWLIST.yaml must exist (allowlist rule, law 7) ---
    if not (backend / "DOMAIN_ALLOWLIST.yaml").is_file():
        rep.add(YEL, "NS37", "backend", "backend/DOMAIN_ALLOWLIST.yaml",
                "DOMAIN_ALLOWLIST.yaml is MISSING. The allowlist rule (law 7) is required: "
                "it lists the temporary cross-domain imports still permitted and must only shrink.",
                intended="create DOMAIN_ALLOWLIST.yaml with cross_domain_imports: []", priority="P2")

    # --- NS12: consumers still import abolished flat layers (import debt) ---
    abolished_count, new_count, abolished_by_mod, new_by_mod = _ns_scan_import_debt(backend)
    if abolished_count > 0:
        top_examples = sorted(abolished_by_mod.items(), key=lambda kv: -kv[1])[:6]
        examples = ["from " + m + " (x" + str(n) + ")" for m, n in top_examples]
        rep.add(RED, "NS12", "backend", "backend/",
                str(abolished_count) + " import statements still bind to abolished flat layers "
                "(services/ controllers/ routers/ root models). The application runtime still depends "
                "on abolished-layer code at the import level even though those layers should not exist at "
                "backend root. This is hard proof of incomplete migration: directory checks alone are "
                "insufficient; the import graph must also be clean.",
                intended="zero consumers import abolished flat layers; all use domains/*/ or modules/*/",
                count=abolished_count, examples=examples, priority="P0")

    # --- NS14: real ARCHITECTURE_DIAGRAM axis adoption ratio vs abolished-layer import debt ---
    total = abolished_count + new_count
    if total > 0:
        ratio = new_count / total
        pct = round(ratio * 100)
        if abolished_count == 0:
            rep.add(GRN, "NS14", "backend", "backend/",
                    "ARCHITECTURE_DIAGRAM axis adoption " + str(pct) + "% (new=" + str(new_count) +
                    ", abolished=" + str(abolished_count) + "). No consumers bind to abolished flat layers.",
                    count=new_count, priority="P2")

        elif ratio < 0.05:
            rep.add(RED, "NS14", "backend", "backend/",
                    "ARCHITECTURE_DIAGRAM axis adoption only " + str(pct) + "% (new=" + str(new_count) +
                    ", abolished=" + str(abolished_count) + "). The codebase is overwhelmingly bound to "
                    "abolished flat layers at the import level. Runtime migration is "
                    "essentially NOT started.",
                    count=new_count, priority="P0")
        elif ratio < 0.5:
            rep.add(YEL, "NS14", "backend", "backend/",
                    "ARCHITECTURE_DIAGRAM axis adoption " + str(pct) + "% (new=" + str(new_count) +
                    ", abolished=" + str(abolished_count) + "). Roughly half or fewer imports use the new "
                    "axes; the abolished-layer surface still dominates.",
                    count=new_count, priority="P1")
        else:
            rep.add(GRN, "NS14", "backend", "backend/",
                    "ARCHITECTURE_DIAGRAM axis adoption " + str(pct) + "% (new=" + str(new_count) +
                    ", abolished=" + str(abolished_count) + "). Majority of imports use the ARCHITECTURE_DIAGRAM axes; "
                    "abolished-layer surface is now the minority.",
                    count=new_count, priority="P2")

    required_atoms, defined_atoms = _ns_collect_feature_atoms(backend)
    undefined = sorted(required_atoms - set(defined_atoms))
    if undefined:
        rep.add(RED, "NS15", "backend", "backend/",
                str(len(undefined)) + " require_feature() atom(s) used but NOT registered in any "
                "domains/*/features.py (Law 4: single source of truth). Unregistered atoms cannot be "
                "enforced by rbac. Examples: " + ", ".join(undefined[:8]),
                count=len(undefined), priority="P0")
    src_counts = {}
    for atom in defined_atoms:
        src_counts[atom] = src_counts.get(atom, 0) + 1
    dups = sorted([a for a, c in src_counts.items() if c > 1])
    if dups:
        rep.add(YEL, "NS17", "backend", "backend/domains/",
                str(len(dups)) + " feature-atom key(s) defined in multiple domains/*/features.py "
                "(ambiguous capability). Examples: " + ", ".join(dups[:8]),
                count=len(dups), priority="P1")
    # --- NS16: rbac/catalog.py must AGGREGATE from domains/*/features.py (Law 4) ---
    # Previously this was a no-op GREEN. Now it actively verifies the catalog is
    # not hand-maintained (which lets feature atoms drift from their domains).
    catalog_path = backend / "rbac" / "catalog.py"
    if catalog_path.is_file():
        try:
            _cat_text = catalog_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            _cat_text = ""
        _aggregates = bool(re.search(
            r"\bimport\s+domains\b|\bdomains\.__path__|iter_modules\(\s*domains", _cat_text))
        if not _aggregates and not re.search(r"features", _cat_text):
            rep.add(RED, "NS16", "backend", "backend/rbac/catalog.py",
                    "rbac/catalog.py does NOT aggregate feature atoms from "
                    "domains/*/features.py (Law 4: single source of truth). It appears "
                    "hand-maintained, which lets feature atoms drift from domains and lets "
                    "require_feature() literals go unenforced.",
                    intended="rbac/catalog.py must import `domains` and package-scan "
                             "domains/*/features.py (FEATURES)",
                    priority="P0")
        elif not _aggregates:
            rep.add(YEL, "NS16", "backend", "backend/rbac/catalog.py",
                    "rbac/catalog.py references 'features' but does not appear to "
                    "package-scan domains/*/features.py; verify it aggregates the domain "
                    "sources (Law 4 single-source).",
                    priority="P1")
        elif defined_atoms and not dups:
            rep.add(GRN, "NS16", "backend", "backend/domains/",
                    str(len(defined_atoms)) + " feature atoms registered in domains/*/features.py "
                    "and aggregated by rbac/catalog.py (single source of truth per domain, "
                    "no duplicates).",
                    count=len(defined_atoms), priority="P3")
    elif (backend / "rbac").is_dir():
        rep.add(RED, "NS16", "backend", "backend/rbac/",
                "backend/rbac/ exists but catalog.py is MISSING — there is no single source "
                "of truth aggregating domains/*/features.py (Law 4). Without it, require_feature() "
                "gates cannot be validated and the Feature axis is unenforced.",
                intended="create rbac/catalog.py that package-scans domains/*/features.py",
                priority="P0")

    router_hits = _ns_scan_thin_router_violations(backend)
    if router_hits:
        ex = [str(p.relative_to(repo)) + ":" + str(ln) + ": " + txt for p, ln, txt in router_hits[:6]]
        rep.add(YEL, "NS18", "backend", "backend/modules/",
                str(len(router_hits)) + " router module(s) leak business logic — import an abolished/upward "
                "layer (core/db/utils/dependencies/infrastructure/providers/...) or reach past the service "
                "layer into domain repositories/models, or perform inline DB writes (Law 2). "
                "NOTE: `from domains.<d>.services` is allowed and NOT flagged.",
                count=len(router_hits), examples=ex, priority="P1")

    # --- NS33: module routers gated by pre-ARCHITECTURE_DIAGRAM auth helper, not require_feature ---
    gate_hits = _ns_scan_router_feature_gate(backend)
    if gate_hits:
        ex = [str(p.relative_to(repo)) + ":" + str(ln) + ": " + txt for p, ln, txt in gate_hits[:6]]
        rep.add(YEL, "NS33", "backend", "backend/modules/",
                str(len(gate_hits)) + " module router(s) gate with a pre-ARCHITECTURE_DIAGRAM per-module auth helper "
                "(require_admin / require_finance_permission / ...) instead of rbac.dependencies."
                "require_feature. The Feature axis (Law 4) is therefore not wired into the routes — "
                "a 'claimed but not done' RBAC migration that directory checks cannot catch. "
                "Public/webhook routers are exempt.",
                count=len(gate_hits), examples=ex, priority="P2")

    actor_hits = _ns_scan_module_actor_violations(backend, ARCH_MODULE_ACTORS)
    if actor_hits:
        ex = [str(p.relative_to(repo)) + ": " + txt for p, ln, txt in actor_hits[:6]]
        rep.add(YEL, "NS19", "backend", "backend/modules/",
                str(len(actor_hits)) + " module-actor discipline issue(s) (non-standard subpackage) (Law 5).",
                count=len(actor_hits), examples=ex, priority="P1")

    inv_hits = _ns_scan_inverted_arrows(backend)
    if inv_hits:
        ex = [str(p.relative_to(repo)) + ":" + str(ln) + ": " + txt for p, ln, txt in inv_hits[:6]]
        rep.add(RED, "NS20", "backend", "backend/",
                str(len(inv_hits)) + " inverted dependency arrow(s): middleware/providers/infrastructure "
                "import upward application layers (Law 1).",
                count=len(inv_hits), examples=ex, priority="P0")

    country_hits = _ns_scan_country_scope(backend)
    if country_hits:
        ex = [str(p.relative_to(repo)) + ": " + txt for p, ln, txt in country_hits]
        rep.add(YEL, "NS21", "backend", "backend/domains/",
                "Country-scoped data exists but no domains/country scoping axis (axis 3).",
                examples=ex, priority="P2")


    # --- NS39: domain missing features.py (Law 4) ---
    feat_hits = _ns_scan_domain_features(backend)
    for d, _, dom in feat_hits:
        rep.add(RED, "NS39", "backend", "backend/domains/" + dom + "/",
                "domain backend/domains/" + dom + "/ has code but no features.py - every domain "
                "must seed its permission atoms (Law 4 single source).",
                intended="create backend/domains/" + dom + "/features.py", priority="P0")

    # --- NS40: module missing required internals (Axis 1) ---
    int_hits = _ns_scan_module_internals(backend)
    for actor, _, msg in int_hits:
        rep.add(YEL, "NS40", "backend", "backend/modules/" + actor.name + "/",
                "module actor backend/modules/" + actor.name + "/ " + msg + " (each actor needs "
                "auth/ + routers/ + serializers/ per diagram section 3 Axis 1).",
                intended="add the missing actor sub-packages", priority="P1")

    # --- NS41: router endpoint calls >1 domain service (Law 2) ---
    thin_calls = _ns_scan_thin_router_calls(backend)
    if thin_calls:
        ex = [str(p.relative_to(repo)) + ":" + str(ln) + ": " + txt for p, ln, txt in thin_calls[:6]]
        rep.add(YEL, "NS41", "backend", "backend/modules/",
                str(len(thin_calls)) + " module router endpoint(s) call more than one domain service "
                "(Law 2: thin router delegates to ONE domain-service call per endpoint).",
                count=len(thin_calls), examples=ex, priority="P1")

    # --- NS42: tests/architecture contract tests missing ---
    if not _ns_scan_tests_architecture(backend):
        rep.add(YEL, "NS42", "backend", "backend/tests/architecture/",
                "backend/tests/architecture/ contract tests missing "
                "(test_import_laws.py - test_feature_catalog.py) - required by diagram section 3.",
                intended="add backend/tests/architecture/test_import_laws.py and test_feature_catalog.py",
                priority="P2")

    # --- NS43: heavy domain not sliced ---
    heavy = _ns_scan_heavy_domains(backend)
    for dom, n in heavy:
        rep.add(YEL, "NS43", "backend", "backend/domains/" + dom + "/services/",
                "heavy domain '" + dom + "' has " + str(n) + " service files with no sub-folder slicing - "
                "slice into sub-capability folders (e.g. finance: ledger/ payouts/ treasury/).",
                intended="slice backend/domains/" + dom + "/services/ into sub-capability folders",
                priority="P2")

    schema_hits = _ns_scan_schema_discipline(backend)
    if schema_hits:
        rr = [str(p.relative_to(repo)) + ": " + txt for p, ln, txt in schema_hits[:6]]
        rep.add(YEL, "NS22", "backend", "backend/domains/",
                str(len(schema_hits)) + " domain model file(s) missing schema discipline: no "
                "__table_args__ schema='<domain>' (Law 6).",
                count=len(schema_hits), examples=rr, priority="P1")



# ============================================================================
# ----------------------------------------------------------------------------
def check_move_suggestions(repo: Path, rep: Report, eff: dict, graph, reg) -> list[dict]:
    """ARCHITECTURE_DIAGRAM.md move-suggestion engine.

    Detects files still living in ABOLISHED flat root layers
    (controllers/routers/services/models) plus cross-cutting root helpers
    (db/dependencies/utils) and suggests their canonical NEW homes:
      - services/<domain>/* -> domains/<domain>/services/
      - models/<domain>/*   -> domains/<domain>/models/
      - routers/*           -> modules/<actor>/routers/
      - controllers/*       -> split: module routers + domain services
      - db/dependencies/utils/* -> infrastructure/<layer>/
    Returns a list of dicts: {from, to, reason, confidence}.
    Abolished layers are treated ONLY as relocation sources, never as targets.
    """
    backend = _ns_backend_root(repo)
    moves: list[dict] = []
    if not backend.is_dir():
        return moves

    known_domains = _pl_known_domains(repo, eff, reg)

    def _py_files(layer_dir: Path):
        try:
            for f in sorted(layer_dir.rglob("*.py")):
                if f.name == "__init__.py":
                    continue
                rel_parts = [p.lower() for p in f.relative_to(backend).parts]
                if any(x in PLACEMENT_SKIP_PARTS for x in rel_parts):
                    continue
                yield f
        except OSError:
            return

    def _infer(f: Path) -> tuple[str | None, float, list[str]]:
        text = read_text(f) or ""
        signals = _pl_extract_signals(f, text, eff)
        return _pl_infer_domain(signals, known_domains, eff)

    # 1) Abolished domain-layered root layers -> domains/<domain>/<layer>/
    for layer in ("services", "models"):
        layer_dir = backend / layer
        if not layer_dir.is_dir():
            continue
        for f in _py_files(layer_dir):
            sub = f.relative_to(layer_dir)
            domain = sub.parts[0].lower() if len(sub.parts) > 1 else None
            if domain:
                target = f"backend/domains/{domain}/{layer}/{f.name}"
            else:
                dom, _conf, _reasons = _infer(f)
                if not dom:
                    continue
                target = f"backend/domains/{dom}/{layer}/{f.name}"
            moves.append({
                "from": rel(f, repo),
                "to": target,
                "reason": f"abolished-root-{layer}->domains/{domain or '<domain>'}/{layer}",
                "confidence": 0.7,
            })

    # 2) Abolished routers/ -> modules/<actor>/routers/
    routers_dir = backend / "routers"
    if routers_dir.is_dir():
        for f in _py_files(routers_dir):
            sub = f.relative_to(routers_dir)
            actor = sub.parts[0].lower() if len(sub.parts) > 1 else None
            if actor in ARCH_MODULE_ACTORS:
                target = f"backend/modules/{actor}/routers/{f.name}"
            else:
                target = "backend/modules/<actor>/routers/<file>"
            moves.append({
                "from": rel(f, repo),
                "to": target,
                "reason": "abolished-root-routers->modules/<actor>/routers",
                "confidence": 0.65,
            })

    # 3) Abolished controllers/ -> split into module routers + domain services
    controllers_dir = backend / "controllers"
    if controllers_dir.is_dir():
        for f in _py_files(controllers_dir):
            dom, _conf, _reasons = _infer(f)
            target = (
                f"backend/domains/{dom}/services/{f.name}" if dom
                else "backend/domains/<domain>/services/<file>"
            )
            moves.append({
                "from": rel(f, repo),
                "to": target,
                "reason": "abolished-root-controllers->modules/routers + domains/services",
                "confidence": 0.6,
            })

    # 4) Cross-cutting root helpers -> infrastructure/<layer>/
    for layer in ("db", "dependencies", "utils"):
        layer_dir = backend / layer
        if not layer_dir.is_dir():
            continue
        for f in _py_files(layer_dir):
            moves.append({
                "from": rel(f, repo),
                "to": f"backend/infrastructure/{layer}/{f.name}",
                "reason": f"abolished-root-{layer}->infrastructure/{layer}",
                "confidence": 0.5,
            })

    return moves

def check_circuit_contract(repo: Path, rep: Report, eff: dict, graph: ModuleGraph) -> None:
    """
    Enforce the ZOZI backend circuit from documents/ARCHITECTURE_DIAGRAM.md (Law 1:
    arrows point down only; Law 2: thin module routers).

    RED CIR1:
        Import is outside the allowed circuit (e.g. domains -> modules,
        infrastructure -> domains, module router -> infrastructure/DB).

    YEL CIR2:
        Import is a migration bypass, for example:
        modules -> infrastructure (thin-router violation)
        domains -> modules (upward arrow)
        infrastructure -> anything above it

    Abolished flat root layers (controllers/ routers/ services/ models/ db/
    utils/ core/ dependencies/) are NOT in ARCHITECTURE_DIAGRAM_CIRCUIT_ALLOWED_IMPORTS, so a
    caller living there is skipped (and reported as NS1-NS4 by
    check_architecture_diagram_compliance) instead of being validated as a circuit.

    Explicit forbidden edges in DEFAULT_FORBIDDEN_EDGES / layer_rules.yaml
    are still reported by check_dependency_graph as DG.
    """
    allowed = ARCHITECTURE_DIAGRAM_CIRCUIT_ALLOWED_IMPORTS
    bypass = ARCHITECTURE_DIAGRAM_CIRCUIT_BYPASS_IMPORTS
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


def check_controller_outside(repo: Path, rep: Report, eff: dict) -> None:
    """
    P2: detect ABOLISHED controller files anywhere in the backend.

    The `controllers/` layer is abolished by documents/ARCHITECTURE_DIAGRAM.md. Every
    `*_controller.py` file (whether inside a `controllers/` dir or anywhere else)
    is a violation: there is no longer a valid "controller" home. Split it:

      * route declarations / request shaping / auth wiring
            -> modules/{module}/routers/{domain}_router.py  (thin)
      * orchestration / business logic / DB access
            -> domains/{domain}/services/{...}_service.py

    Abolished `controllers/` code has no valid home under the target architecture;
    it must be split into module routers + domain services. No re-export shim layer
    is prescribed by documents/ARCHITECTURE_DIAGRAM.md.
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

        top = parts[0]

        # A controller that has been re-homed into a VALID ARCHITECTURE_DIAGRAM.md
        # package (modules/ domains/ rbac/ infrastructure/ kernel/ providers/
        # jobs/ middleware/) is no longer an abolished-layer violation — it is a
        # legitimately-placed file even if its basename contains "controller"
        # (e.g. domains/finance/services/sub_ledger_controller.py, or a module
        # router named command_center_controller.py). Only STRAY controller
        # files (outside those homes) or an actual `controllers/` directory are
        # abolished-layer violations. Flagging valid homes produced hundreds of
        # false positives that let a "migration done" claim look credible.
        _VALID_NS_HOMES = {
            "modules", "domains", "rbac", "infrastructure", "kernel",
            "providers", "jobs", "middleware",
        }
        if top in _VALID_NS_HOMES:
            continue

        if top in {
            "tests",
            "scripts",
            "alembic",
            "data",
            "monitoring",
            "docs",
        }:
            continue

        stem = f.stem.lower()

        # Abolished if the file is named like a controller OR lives under a
        # (now abolished) controllers/ directory.
        is_controller = stem.endswith("_controller") or "controllers" in parts

        if not is_controller:
            continue

        rep.add(
            RED,
            "P2",
            "backend",
            rel(f, repo),
            f"abolished controller file '{f.name}' (controllers/ layer is abolished)",
            intended=(
                "split it: route declarations -> modules/{module}/routers/{domain}_router.py "
                "(thin, require_feature gate); business logic/DB access -> "
                "domains/{domain}/services/. Delete the original once migrated."
            ),
        )

        reported += 1

        if reported >= 200:
            return


def check_layer_contracts(repo: Path, rep: Report, eff: dict, graph: ModuleGraph, call_graph: CallGraph) -> None:
    """
    LC1/LC2/LC3: Validate explicit layer contracts.
    CORRECTED:
    - Removed db.query from LC1 (reads are Q1 advisory, not LC1 violation)
    - Removed session.execute (can be read or write; too broad)
    - Added comment/docstring skipping
    - Only flags WRITE operations in forbidden layers
    """
    # Per ARCHITECTURE_DIAGRAM.md §3: canonical layers only.
    # Abolished layers (routers/controllers/services/models/db/utils/core/dependencies)
    # are detected by check_architecture_compliance as NS1-NS4 and need no contract here.
    contracts: dict[str, LayerContract] = {
        "modules": LayerContract(
            layer="modules",
            may_import={"domains", "rbac"},
            may_not_import={"infrastructure", "kernel", "providers", "jobs",
                            "middleware", "config", "data"},
            may_call={"domains", "rbac"},
            may_not_call={"infrastructure", "kernel", "providers"},
            forbidden_operations={"session.add", "session.commit", "session.delete",
                                  "session.merge", "session.flush"},
            forbidden_patterns=[r"session\.(add|commit|delete|merge|flush)\("],
        ),
        "domains": LayerContract(
            layer="domains",
            may_import={"infrastructure", "kernel", "providers", "domains"},
            may_not_import={"modules", "rbac", "jobs", "middleware", "config"},
            may_call={"infrastructure", "kernel", "providers"},
            may_not_call={"modules", "rbac"},
            forbidden_patterns=[],
        ),
        "rbac": LayerContract(
            layer="rbac",
            may_import={"infrastructure", "kernel", "domains"},
            may_not_import={"modules", "providers", "jobs", "middleware", "config", "data"},
            may_call={"infrastructure", "kernel", "domains"},
            may_not_call={"modules", "providers"},
            forbidden_patterns=[],
        ),
        "kernel": LayerContract(
            layer="kernel",
            may_import={"infrastructure"},
            may_not_import={"modules", "domains", "rbac", "providers", "jobs",
                            "middleware", "config", "data"},
            may_call={"infrastructure"},
            may_not_call=set(),
            forbidden_patterns=[],
        ),
        "infrastructure": LayerContract(
            layer="infrastructure",
            may_import=set(),
            may_not_import={"modules", "domains", "rbac", "kernel", "providers",
                            "jobs", "middleware", "config", "data"},
            may_call=set(),
            may_not_call=set(),
            forbidden_patterns=[],
        ),
        "providers": LayerContract(
            layer="providers",
            may_import={"infrastructure", "kernel"},
            may_not_import={"modules", "domains", "rbac", "jobs", "middleware", "config", "data"},
            may_call={"infrastructure", "kernel"},
            may_not_call=set(),
            forbidden_patterns=[],
        ),
        "jobs": LayerContract(
            layer="jobs",
            may_import={"domains", "infrastructure", "kernel", "providers"},
            may_not_import={"modules", "rbac", "middleware", "config", "data"},
            may_call={"domains", "infrastructure", "kernel", "providers"},
            may_not_call=set(),
            forbidden_patterns=[],
        ),
        "middleware": LayerContract(
            layer="middleware",
            # Diagram: "rbac is imported by modules + middleware ONLY" → middleware may import rbac.
            may_import={"infrastructure", "kernel", "rbac"},
            may_not_import={"modules", "domains", "providers",
                            "jobs", "config", "data"},
            may_call={"infrastructure", "kernel", "rbac"},
            may_not_call=set(),
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

        # CORRECTED: Use AST to check only actual code, skip comments/docstrings
        tree = parse_safe(f)
        if tree is None:
            continue

        for pattern in contract.forbidden_patterns:
            try:
                rx = re.compile(pattern)
            except re.error:
                continue

            # Search only non-comment, non-docstring lines
            in_docstring = False
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()

                # Skip single-line comments
                if stripped.startswith("#"):
                    continue

                # Track multi-line docstrings
                if '"""' in stripped or "'''" in stripped:
                    quote = '"""' if '"""' in stripped else "'''"
                    count = stripped.count(quote)
                    if count == 1:
                        in_docstring = not in_docstring
                    # count == 2 means open+close on same line (skip)
                    continue
                if in_docstring:
                    continue

                if rx.search(line):
                    rep.add(
                        RED, "LC1", layer,
                        rel(f, repo),
                        f"layer contract violation: write operation "
                        f"'{pattern}' found in {layer}/",
                        intended=f"{layer} must not perform DB writes; "
                                 f"move write operations to domains/<domain>/services/",
                        line=i,
                    )
                    reported += 1
                    break  # One finding per file per pattern
            if reported >= 200:
                return


def _check_module_router_naming(repo: Path, rep: Report, eff: dict) -> None:
    """
    Validate NEW module router placement (documents/ARCHITECTURE_DIAGRAM.md, Axis 1).

    Thin routers live per actor under:

        modules/{module}/routers/{domain}_{operation}_router.py

    The abolished `backend/routers/` layer (pre-ARCHITECTURE_DIAGRAM flat layout) is ABOLISHED and is flagged wherever it
    still exists (its NEW home is modules/{module}/routers/).
    """
    backend = repo / "backend"

    # --- Abolished root routers/ layer (pre-ARCHITECTURE_DIAGRAM flat layout) ---
    old_routers = backend / "routers"
    if old_routers.is_dir():
        for f in sorted(old_routers.rglob("*.py")):
            if f.name == "__init__.py":
                continue
                parts = [p.lower() for p in f.relative_to(backend).parts]
            rep.add(
                RED, "RN4", "routers", rel(f, repo),
                "router still lives under abolished root backend/routers/ (pre-ARCHITECTURE_DIAGRAM flat layer)",
                intended="re-home into modules/{module}/routers/{domain}_router.py "
                         "(thin: require_feature gate + one domain-service call)",
                line=1,
            )

    # --- Validate NEW module routers ---
    modules = backend / "modules"
    if not modules.is_dir():
        return

    aliases = PLACEMENT_ALIAS_TO_DOMAIN
    stop = set(PLACEMENT_STOP_TOKENS)

    def _tokens(stem: str) -> list[str]:
        return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", stem) if t]

    for actor_dir in sorted(modules.iterdir()):
        if not actor_dir.is_dir() or actor_dir.name.lower() == "__pycache__":
            continue
        routers_dir = actor_dir / "routers"
        if not routers_dir.is_dir():
            continue
        actor = actor_dir.name.lower()
        for f in sorted(routers_dir.rglob("*.py")):
            if f.name == "__init__.py":
                continue
            rel_parts = [p.lower() for p in f.relative_to(backend).parts]
            stem = f.stem.lower()
            if not stem.endswith("_router"):
                rep.add(
                    YEL, "RN1", "routers", rel(f, repo),
                    f"module router filename '{f.name}' must end with '_router.py'",
                    intended=f"rename to modules/{actor}/routers/{{domain}}_router.py",
                    line=1,
                )
                continue
            base = stem[: -len("_router")]
            if not base:
                continue
            toks = _tokens(base)
            has_domain = any(aliases.get(t) for t in toks) or any(
                len(t) >= 3 and t not in stop for t in toks
            )
            if not has_domain:
                rep.add(
                    YEL, "RN1", "routers", rel(f, repo),
                    f"module router '{f.name}' has no domain/feature token",
                    intended=f"name as modules/{actor}/routers/{{domain}}_router.py",
                    line=1,
                )


def check_router_naming_convention(repo: Path, rep: Report, eff: dict) -> None:
    """
    Validate router placement against documents/ARCHITECTURE_DIAGRAM.md (three axes).

    Per ARCHITECTURE_DIAGRAM.md the abolished `backend/routers/` layer (pre-ARCHITECTURE_DIAGRAM flat layout) is ABOLISHED. Thin
    routers are re-homed per actor under:

        modules/{module}/routers/{domain}_{operation}_router.py

    The default `router_layout` is "modules". Any surviving file under the
    abolished root `backend/routers/` is reported as a violation (the NEW home is
    modules/{module}/routers/). Legacy "flat"/"surface_dirs" layouts are no longer
    supported.
    """
    backend = repo / "backend"
    routers = backend / "routers"

    if not routers.exists():
        return

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}
    stop = set(PLACEMENT_STOP_TOKENS)
    aliases = PLACEMENT_ALIAS_TO_DOMAIN
    router_layout = str(eff.get("router_layout", "modules")).lower()
    router_pattern = str(eff.get("router_pattern", "") or "")

    # ARCHITECTURE_DIAGRAM.md: routers belong under modules/{module}/routers/.
    # The abolished root backend/routers/ layer is abolished — validate the NEW layout
    # and never re-validate the pre-ARCHITECTURE_DIAGRAM flat/surface_dirs convention.
    _check_module_router_naming(repo, rep, eff)
    return

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

    def _domain_or_feature(toks: list[str], surface: str | None = None) -> str | None:
        for t in toks:
            d = aliases.get(t)
            if d:
                return d
        for t in toks:
            if len(t) < 3:
                continue
            if t in stop:
                continue
            if surface and t == surface:
                continue
            return t
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

    def _surface_dir_target(stem: str, surface: str | None, domain_or_feature: str | None) -> str:
        if surface:
            rest = stem.lower()
            prefix = f"{surface}_"
            if rest.startswith(prefix):
                rest = rest[len(prefix):]
            if not rest:
                rest = domain_or_feature or stem.lower()
            return f"backend/routers/{surface}/{rest}.py"
        return "backend/routers/{surface}/{domain_or_feature}.py"

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

    if router_layout == "surface_dirs":
        try:
            subdirs = [
                p for p in routers.iterdir()
                if p.is_dir()
                and p.name.lower() not in eff.get("ignore_dirs", set())
                and p.name.lower() != "__pycache__"
                and p.name.lower() not in _AUDIT_ROUTER_TOOLING_SUBDIRS
            ]
        except OSError:
            subdirs = []

        for sd in sorted(subdirs):
            surface = sd.name.lower()
            if surface not in surfaces:
                rep.add(
                    YEL,
                    "RN3",
                    "routers",
                    rel(sd, repo),
                    f"router sub-folder '{sd.name}/' is not a configured surface",
                    intended=(
                        "use the configured router pattern "
                        f"`{router_pattern or 'backend/routers/{surface}/{domain_or_feature}.py'}`"
                    ),
                )
                continue

            for f in sorted(sd.rglob("*.py")):
                if f.name == "__init__.py":
                    continue
                try:
                    parts = f.relative_to(sd).parts
                except ValueError:
                    parts = ()
                if len(parts) > 1:
                    rep.add(
                        YEL,
                        "RN2",
                        "routers",
                        rel(f, repo),
                        "router file is nested deeper than the surface folder contract",
                        intended=f"move to backend/routers/{surface}/{f.name}",
                    )
                    continue

                toks = _tokens(f.stem)
                domain_or_feature = _domain_or_feature(toks, surface)
                if not domain_or_feature:
                    rep.add(
                        YEL,
                        "RN1",
                        "routers",
                        rel(f, repo),
                        f"router filename '{f.name}' has no domain/feature token",
                        intended=f"rename to backend/routers/{surface}/{{domain_or_feature}}.py",
                    )

        for f in sorted(routers.glob("*.py")):
            if f.name == "__init__.py":
                continue
            toks = _tokens(f.stem)
            surface = _surface(toks)
            domain_or_feature = _domain_or_feature(toks, surface)
            target = _surface_dir_target(f.stem, surface, domain_or_feature)
            missing = []
            if not surface:
                missing.append("surface")
            if not domain_or_feature:
                missing.append("domain_or_feature")
            detail = f"; missing {', '.join(missing)}" if missing else ""
            rep.add(
                YEL,
                "RN1",
                "routers",
                rel(f, repo),
                f"router file is at routers/ root, but contract requires a surface folder{detail}",
                intended=f"move to {target}",
            )
        return

    # ------------------------------------------------------------------
    # RN3 + RN2: router sub-folders are not allowed.
    # ------------------------------------------------------------------
    try:
        subdirs = [
            p for p in routers.iterdir()
            if p.is_dir()
            and p.name.lower() not in eff.get("ignore_dirs", set())
            and p.name.lower() != "__pycache__"
            and p.name.lower() not in _AUDIT_ROUTER_TOOLING_SUBDIRS
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
        # Surface is optional for flat routers; unprefixed routers are treated
        # as the `internal` surface (already a configured surface name).
        surface = _surface(toks) or "internal"
        domain = _domain(toks)

        missing: list[str] = []

        if not domain:
            missing.append("domain")

        if missing:
            rep.add(
                YEL,
                "RN1",
                "routers",
                rel(f, repo),
                f"flat router filename '{f.name}' is not comprehensive; "
                f"missing {', '.join(missing)}",
                intended=(
                    "name as {surface}_{domain}.py (surface optional, defaults "
                    "to 'internal'), e.g. admin_orders.py, supplier_orders.py, "
                    "customer_cart.py, ai.py, finance.py"
                ),
            )


def check_surface_domain_matrix(repo: Path, rep: Report, eff: dict, graph: ModuleGraph,) -> None:
    """
    Validate the grouping axis against documents/ARCHITECTURE_DIAGRAM.md.

    Per ARCHITECTURE_DIAGRAM.md the abolished root layers controllers/ services/ models/
    events/ are ABOLISHED — they must not exist as root layers. If they survive at
    backend root they are flagged as abolition targets (NS1-NS4 own the canonical
    home mapping; here we flag the root-layer presence directly).

    The only legitimately domain-grouped root layer is `domains/`. `providers/`
    and `jobs/` are valid NEW root layers organised by capability, not by domain,
    so surface-named sub-folders inside them are allowed.
    """
    backend = repo / "backend"

    # Abolished flat root layers (Axis confusion). If present, flag them.
    _ABOLISHED_ROOT_DOMAIN_LAYERS = {
        "controllers": "split into modules/*/routers/ (thin) + domains/*/services/",
        "services":    "move into domains/{domain}/services/",
        "models":      "move into domains/{domain}/models/",
        "events":      "move into domains/{domain}/events.py (per-domain file)",
    }
    for layer, intended in _ABOLISHED_ROOT_DOMAIN_LAYERS.items():
        layer_dir = backend / layer
        if layer_dir.is_dir() and any(layer_dir.rglob("*.py")):
            rep.add(
                RED,
                "DOM3",
                layer,
                rel(layer_dir, repo),
                f"abolished root layer '{layer}/' still present at backend root",
                intended=intended,
                line=1,
            )

    surfaces = {str(x).lower() for x in eff.get("surface_names", set())}

    domains: set[str] = set(PLACEMENT_DOMAIN_KEYWORDS.keys())
    domains |= {str(x).lower() for x in eff.get("domains", {}).keys()}

    if _ACTIVE_REG is not None:
        domains |= {
            str(x).lower()
            for x in getattr(_ACTIVE_REG, "domains", set())
        }

    # Only domains/ is a legitimately domain-grouped root layer.
    domain_layers = ("domains",)

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



def main() -> int:
    """ZERO arguments. ZERO flags. Single output: SYSTEM_AUDIT_REPORT.md."""
    repo = find_repo(None)
    if not repo.is_dir():
        print(f"[FATAL] repo root not found: {repo}", file=sys.stderr)
        return 2

    eff = load_rules(repo, None)
    ensure_required_ignore_dirs(eff)
    global _ACTIVE_EFF, _ACTIVE_REG
    _ACTIVE_EFF = eff

    print(f"Scanning {repo} ...")
    print(f"  Rules source: {rules_source_label(eff)}")
    rep = Report()

    # PHASE 1: ARCHITECTURE
    print("  [1/4] Architecture audit...")
    graph = build_module_graph(repo, eff)
    reg = discover_features(repo, eff, graph)
    _ACTIVE_REG = reg
    placement_suggestions = check_move_suggestions(repo, rep, eff, graph, reg)
    if placement_suggestions:
        rep.add(GRN, "I4", "repo", "move-map",
                f"{len(placement_suggestions)} file move suggestions generated")
    model = learn_domain_model(repo, eff, reg)
    report_auto_domain_candidates(repo, rep, eff, model)

    for fn in (check_gitignore, check_lockfiles, check_cache_dirs, check_node_modules,
               check_hardcoded_local_paths):
        fn(repo, rep, eff)
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
    check_architecture_diagram_compliance(repo, rep, eff)
    check_rls_cluster(repo, rep, eff)
    check_raw_env_in_middleware(repo, rep, eff)
    check_media_on_disk(repo, rep, eff)
    check_contract_forbidden_folders(repo, rep, eff)
    check_middleware_pipeline(repo, rep, eff)
    check_middleware_pipeline_order(repo, rep, eff)     # ← NEW (C3)
    check_scaling_readiness(repo, rep, eff)

    check_scaling_phases(repo, rep, eff)                # ← NEW (C2)
    check_realtime_policy(repo, rep, eff)               # ← NEW (C4)
    check_background_infrastructure(repo, rep, eff)     # ← NEW (C5)
    check_health_endpoints(repo, rep, eff)              # ← UPDATED (C6)

    check_provider_base_classes(repo, rep, eff)

    symbol_index = build_symbol_index(repo, eff, graph)
    call_graph = build_call_graph(repo, eff, graph, symbol_index)
    check_layer_contracts(repo, rep, eff, graph, call_graph)
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
    check_dead_symbols(repo, rep, eff, symbol_index, graph)
    check_duplicate_symbols(repo, rep, eff, symbol_index)
    check_call_graph_violations(repo, rep, eff, call_graph, graph)
    check_public_api_stability(repo, rep, eff, symbol_index, graph)
    flow_types = classify_flow_types(repo, eff, reg, graph)
    check_flow_type_violations(repo, rep, eff, flow_types, graph)
    check_file_content_alignment(repo, rep, eff, graph)
    check_split_file_candidates(repo, rep, eff, graph)
    check_surface_operations(repo, rep, eff, graph)
    check_required_project_files(repo, rep, eff)
    check_scope_documentation(repo, rep, eff)
    check_scope_yaml_agreement(repo, rep, eff)
    check_api_shape(repo, rep, eff, graph)
    check_dynamic_dependency_signals(repo, rep, eff, graph)
    check_policy_config(repo, rep, eff)
    check_frontend_structure(repo, rep, eff)
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
    check_advanced_security(repo, rep, eff, graph)
    check_advanced_performance(repo, rep, eff, graph)
    check_advanced_frontend(repo, rep, eff)
    check_enhanced_metrics(repo, rep, eff, graph, symbol_index)
    check_bounded_contexts(repo, rep, eff, graph, reg)
    check_surface_domain_matrix(repo, rep, eff, graph)
    check_frontend_role_pages(repo, rep, eff)

    # PHASE 1: ARCHITECTURE — add after existing checks:
    check_lifespan_startup(repo, rep, eff)
    check_jwt_jti_blacklist(repo, rep, eff)
    check_csrf_pci_prod_only(repo, rep, eff)
    check_async_workers_off_request(repo, rep, eff)

    # PHASE 2: DATABASE
    print("  [2/4] Database audit...")
    db_models, db_minfo, db_rls = dba_run_all_checks(repo, rep)
    check_get_db_single_session(repo, rep, eff)

    # ── NEW: Domain actor isolation check ──
    check_domain_actor_isolation(repo, rep, db_models, eff)

    # PHASE 3: DESIGN
    print("  [3/4] Design audit...")
    ds_summary = ds_run_all_checks(repo, rep)

    # PHASE 4: HEALTH
    print("  [4/4] Health audit...")
    hl_run_all_checks(repo, rep, None)

    # PHASE 5: collapse + summary
    collapse_noisy_findings(rep)
    collect_info(repo, rep, eff, graph)
    frontend_metrics = collect_frontend_metrics(repo, eff)
    debt_score = compute_debt_score(rep, eff)
    rep.add(GRN, "MET1", "repo", "architecture-debt", f"UNIFIED debt score = {debt_score}")
    summary = build_summary(repo, rep, graph, debt_score, frontend_metrics, reg)
    summary["database"] = {
        "models": len(db_models),
        "tables": len({m.table.lower() for m in db_models if m.table}),
        "migration_heads": db_minfo.heads if db_minfo else [],
        "rls_tables": len(db_rls.rls_tables) if db_rls else 0,
    }
    summary["design"] = {
        "palette_tokens": ds_summary.get("palette_tokens", 0),
        "coverage": ds_summary.get("coverage", 100.0),
    }
    health_score, health_grade = compute_health_score(rep)
    summary["health"] = {
        "health_score": health_score,
        "grade": health_grade,
        "file_ranking": [
            {"file": p, "weight": w, "codes": c}
            for p, w, c in compute_file_health_scores(rep)
        ],
    }

    # PHASE 6: SINGLE output — SYSTEM_AUDIT_REPORT.md only
    n_red = render_stdout(repo, rep, summary)
    out = resolve_repo_output_path(repo, None, "SYSTEM_AUDIT_REPORT.md")
    render_markdown(repo, rep, out, summary, placement_suggestions, eff, reg, graph)

    print(f"\n{'=' * 76}")
    print("  UNIFIED SYSTEM AUDIT COMPLETE")
    print(f"  🔴 {summary['red']}  🟡 {summary['yellow']}  🟢 {summary['green']}  debt={debt_score}")
    print(f"  Report: {out}")
    print(f"{'=' * 76}")
    return 1 if n_red else 0

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    sys.exit(main())
