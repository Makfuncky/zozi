# audit_migration_tracker.py
"""
ZOZI Architecture Audit & Migration Tracker (v9 — Service Consolidation)
════════════════════════════════════════════════════════════════════════════════
v9 adds over v8:
  1. NEW: Service consolidation analysis (Tier 0–5 classification)
     - Tier 0: Safe deletes (junk/scratch/empty)
     - Tier 1: Exact content duplicates (byte-identical)
     - Tier 2: Naming-variant / domain sprawl (suppliers/ vs supplier/, etc.)
     - Tier 3: Read/Write split sprawl (*_read_service / *_write_service)
     - Tier 4: Thin forwarding services (only forward to other modules)
     - Tier 5: Structural near-duplicates (≥0.6 op-similarity)
  2. NEW: Service size distribution report
  3. NEW: Import-impact analysis for merge candidates
  4. FIX: All v8 fixes preserved (business logic, adapters, scan consistency)
════════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# ─────────────────────────────────────────────────────────────────────────────
# §0 — CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND = PROJECT_ROOT / "backend"
ROUTERS_DIR = BACKEND / "routers"
CONTROLLERS_DIR = BACKEND / "controllers"
SERVICES_DIR = BACKEND / "services"
MODELS_DIR = BACKEND / "models"
DB_DIR = BACKEND / "db"
SCHEMAS_DIR = BACKEND / "schemas"
PROVIDERS_DIR = BACKEND / "providers"
UTILS_DIR = BACKEND / "utils"
MIDDLEWARE_DIR = BACKEND / "middleware"

REPORT_OUTPUT = PROJECT_ROOT / "ARCHITECTURE_MIGRATION_REPORT.md"

CANONICAL_DOMAINS = [
    "ai", "analytics", "audit", "billing", "catalog", "commerce",
    "comms", "configuration", "customer", "documents", "events",
    "finance", "gateway", "geography", "hr", "identity", "inventory",
    "logistics", "media", "notifications", "orders", "permissions",
    "pricing", "reporting", "reviews", "search", "security",
    "shipping", "supplier", "treasury", "webhooks",
]

SURFACES = ["admin", "customer", "supplier", "logistics", "public", "system", "internal"]

# v9: Known naming variants that should be merged
NAMING_VARIANTS: dict[str, str] = {
    "suppliers": "supplier",
    "communication": "comms",
    "communications": "comms",
    "products": "catalog",
    "product": "catalog",
    "employee": "hr",
    "employees": "hr",
    "country": "geography",
    "countries": "geography",
    "payment": "gateway",
    "payments": "gateway",
    "notification": "notifications",
    "order": "orders",
    "user": "identity",
    "users": "identity",
    "security_auth": "security",
    "auth": "identity",
    "promotion": "commerce",
    "promotions": "commerce",
    "coupon": "commerce",
    "coupons": "commerce",
    "location": "geography",
    "location_service": "geography",
    "geo": "geography",
    "finance_erp": "finance",
    "erp": "finance",
    "treasury_cash": "treasury",
    "treasury_payout": "treasury",
    "treasury_admin": "treasury",
    "logistics_partner": "logistics",
    "logistics_health": "logistics",
    "logistics_shipment": "logistics",
    "media_storage": "media",
    "media_upload": "media",
    "comms_chat": "comms",
    "comms_email": "comms",
    "comms_notification": "comms",
    "comms_video": "comms",
}

# v9: Service size thresholds
SIZE_EMPTY_MAX = 5        # ≤5 lines = empty/stub
SIZE_TINY_MAX = 30        # ≤30 lines = tiny
SIZE_THIN_MAX = 100       # ≤100 lines = thin
SIZE_MEDIUM_MAX = 300     # ≤300 lines = medium
# >300 = large

# v9: Thin forwarder detection threshold
# If >80% of functions only forward to another module, it's a thin forwarder
THIN_FORWARDER_RATIO = 0.80

# v9: Structural similarity threshold for service consolidation
SERVICE_STRUCTURAL_THRESHOLD = 0.60

# v8: Only genuine ORM session/engine operations are business logic.
BUSINESS_LOGIC_LINE_PATTERNS = [
    r"\bdb\s*\.\s*add\s*\(",
    r"\bdb\s*\.\s*commit\s*\(",
    r"\bdb\s*\.\s*delete\s*\(",
    r"\bdb\s*\.\s*merge\s*\(",
    r"\bdb\s*\.\s*flush\s*\(",
    r"\bdb\s*\.\s*query\s*\(",
    r"\bdb\s*\.\s*execute\s*\(",
    r"\bdb\s*\.\s*scalar\s*\(",
    r"\bsession\s*\.\s*add\s*\(",
    r"\bsession\s*\.\s*commit\s*\(",
    r"\bsession\s*\.\s*delete\s*\(",
    r"\bsession\s*\.\s*merge\s*\(",
    r"\bsession\s*\.\s*flush\s*\(",
    r"\bsession\s*\.\s*query\s*\(",
    r"\bsession\s*\.\s*execute\s*\(",
    r"\bsession\s*\.\s*scalar\s*\(",
]

ORM_OPS = {"add", "commit", "delete", "merge", "flush", "execute", "scalar", "query"}
SESSION_RECEIVERS = {"db", "session", "engine", "self"}

SERVICE_CALL_PATTERN = re.compile(r"(?:from|import)\s+services[.\w]*")
CONTROLLER_CALL_PATTERN = re.compile(r"(?:from|import)\s+controllers[.\w]*")
MODEL_IMPORT_PATTERN = re.compile(r"(?:from|import)\s+models[.\w]*")
DB_IMPORT_PATTERN = re.compile(r"(?:from|import)\s+db[.\w]*")
SCHEMA_IMPORT_PATTERN = re.compile(r"(?:from|import)\s+(?:schemas|db\.schemas)[.\w]*")

ROUTE_DECORATOR_NAMES = {"get", "post", "put", "patch", "delete", "route", "route_meta"}

ROUTE_DECORATOR_ALIASES = {
    "api_get", "api_post", "api_put", "api_patch", "api_delete",
    "http_get", "http_post", "http_put", "http_patch", "http_delete",
}

ROUTE_DECORATOR_PATTERNS = [
    re.compile(r"@get\s*\("),
    re.compile(r"@post\s*\("),
    re.compile(r"@put\s*\("),
    re.compile(r"@patch\s*\("),
    re.compile(r"@delete\s*\("),
    re.compile(r"@route\s*\("),
    re.compile(r"@route_meta\s*\("),
]

PROVIDER_NAME_PREFIXES = ("require_", "get_current_", "_require")

MAX_RESCAN_ATTEMPTS = 3
SCAN_DIRS = ["routers", "controllers", "services", "models"]

MATCH_IDENTICAL = "IDENTICAL"
MATCH_STRUCTURAL = "STRUCTURAL"
MATCH_MODEL_OPS = "MODEL_OPS"

DUPLICATE_SIMILARITY_THRESHOLD = 0.65
PARTIAL_DUPLICATE_THRESHOLD = 0.40

MODEL_OPS_MIN_OVERLAP = 5
MODEL_OPS_MIN_RATIO = 0.50

MAX_ADVISORY_OVERLAPS_REPORT = 100
MAX_STRUCTURAL_REPORT = 100


# ─────────────────────────────────────────────────────────────────────────────
# §1 — DATA CLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FileInfo:
    path: Path
    name: str
    domain: str = ""
    surface: str = ""
    layer: str = ""
    has_business_logic: bool = False
    business_logic_lines: list[int] = field(default_factory=list)
    imports_services: bool = False
    imports_controllers: bool = False
    imports_models: bool = False
    imports_db: bool = False
    has_route_decorator: bool = False
    decorator_names_used: list[str] = field(default_factory=list)
    decorated_functions: list[str] = field(default_factory=list)
    undecorated_functions: list[str] = field(default_factory=list)
    is_adapter: bool = False
    adapter_reason: str = ""
    functions: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    lines_of_code: int = 0
    function_fingerprints: dict[str, str] = field(default_factory=dict)
    function_body_hashes: dict[str, str] = field(default_factory=dict)
    model_operations: list[str] = field(default_factory=list)
    function_model_ops: dict[str, list[str]] = field(default_factory=dict)
    db_operation_hashes: set[str] = field(default_factory=set)
    # v9: Service-specific analysis
    size_category: str = ""          # empty, tiny, thin, medium, large
    is_thin_forwarder: bool = False
    forwarding_targets: list[str] = field(default_factory=list)
    is_read_write_split: bool = False
    split_type: str = ""             # "read" or "write"
    canonical_domain: str = ""       # resolved canonical domain
    is_naming_variant: bool = False
    original_folder: str = ""


@dataclass
class ServiceConsolidationFinding:
    """A single service consolidation finding."""
    tier: int                        # 0-5
    tier_label: str
    file_a: str
    file_b: str = ""                 # empty for Tier 0 (single file findings)
    reason: str = ""
    similarity: float = 0.0
    action: str = ""                 # DELETE, MERGE, RENAME, STANDARDIZE, REVIEW
    risk: str = "LOW"                # LOW, MEDIUM, HIGH
    import_impact: list[str] = field(default_factory=list)
    recommendation: str = ""         # human-actionable next step (e.g. merge target)


@dataclass
class ServiceConsolidationReport:
    """Complete service consolidation analysis."""
    total_services: int = 0
    size_distribution: dict[str, int] = field(default_factory=dict)
    tier0_safe_deletes: list[ServiceConsolidationFinding] = field(default_factory=list)
    tier1_exact_duplicates: list[ServiceConsolidationFinding] = field(default_factory=list)
    tier2_naming_variants: list[ServiceConsolidationFinding] = field(default_factory=list)
    tier3_read_write_split: list[ServiceConsolidationFinding] = field(default_factory=list)
    tier4_thin_forwarders: list[ServiceConsolidationFinding] = field(default_factory=list)
    tier5_structural_dups: list[ServiceConsolidationFinding] = field(default_factory=list)
    consolidation_target: int = 0    # estimated final file count
    safe_immediate_reduction: int = 0
    realistic_target: int = 0


@dataclass
class MigrationTask:
    source_file: str
    target_file: str
    logic_type: str
    line_numbers: list[int] = field(default_factory=list)
    description: str = ""
    priority: str = "HIGH"
    status: str = "PENDING"
    already_exists_in: str = ""
    duplicate_function: str = ""
    duplicate_confidence: float = 0.0
    resolution: str = ""


@dataclass
class DuplicateFinding:
    source_file: str
    source_function: str
    source_lines: list[int]
    existing_file: str
    existing_function: str
    similarity: float
    match_type: str
    db_operations: list[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class WiringTask:
    model_file: str
    service_file: str
    controller_file: str
    router_file: str
    status: str = "INCOMPLETE"
    missing_pieces: list[str] = field(default_factory=list)


@dataclass
class MissingItem:
    item_type: str
    path: str
    reason: str
    priority: str = "MEDIUM"


@dataclass
class AuditReport:
    timestamp: str = ""
    scan_start_time: str = ""
    scan_end_time: str = ""
    scan_duration_ms: float = 0.0
    scan_attempts: int = 1
    scan_consistent: bool = True
    file_count_pre: int = 0
    file_count_post: int = 0

    total_routers: int = 0
    total_controllers: int = 0
    total_services: int = 0
    total_models: int = 0
    routers_with_business_logic: int = 0
    controllers_with_decorators: int = 0
    controllers_without_decorators: int = 0
    migration_tasks: list[MigrationTask] = field(default_factory=list)
    wiring_tasks: list[WiringTask] = field(default_factory=list)
    missing_items: list[MissingItem] = field(default_factory=list)
    ready_controllers: list[str] = field(default_factory=list)
    not_ready_controllers: list[str] = field(default_factory=list)
    adapter_controllers: list[str] = field(default_factory=list)
    file_infos: dict[str, FileInfo] = field(default_factory=dict)
    identical_findings: list[DuplicateFinding] = field(default_factory=list)
    structural_findings: list[DuplicateFinding] = field(default_factory=list)
    advisory_overlaps: list[DuplicateFinding] = field(default_factory=list)
    duplicates_skipped: int = 0
    partial_duplicates: int = 0
    actual_migrations_needed: int = 0
    # v9: Service consolidation
    service_consolidation: ServiceConsolidationReport = field(
        default_factory=ServiceConsolidationReport
    )


# ─────────────────────────────────────────────────────────────────────────────
# §1a — FILE INVENTORY SNAPSHOT
# ─────────────────────────────────────────────────────────────────────────────

def take_file_snapshot() -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for dir_name in SCAN_DIRS:
        scan_dir = BACKEND / dir_name
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            if py_file.name == "__init__.py":
                continue
            if py_file.name.startswith("__"):
                continue
            rel = str(py_file.relative_to(BACKEND))
            try:
                snapshot[rel] = py_file.stat().st_mtime
            except OSError:
                continue
    return snapshot


def compute_snapshot_hash(snapshot: dict[str, float]) -> str:
    entries = sorted(snapshot.items())
    content = "\n".join(f"{path}:{mtime}" for path, mtime in entries)
    return hashlib.sha256(content.encode()).hexdigest()


def check_snapshot_consistency(
    pre_snapshot: dict[str, float],
) -> tuple[bool, list[str], list[str], list[str]]:
    post_snapshot = take_file_snapshot()
    pre_keys = set(pre_snapshot.keys())
    post_keys = set(post_snapshot.keys())
    added = sorted(post_keys - pre_keys)
    removed = sorted(pre_keys - post_keys)
    modified = sorted(
        k for k in pre_keys & post_keys
        if pre_snapshot[k] != post_snapshot[k]
    )
    is_consistent = len(added) == 0 and len(removed) == 0 and len(modified) == 0
    return is_consistent, added, removed, modified


# ─────────────────────────────────────────────────────────────────────────────
# §2 — AST PARSER (SAFE — NEVER EXECUTES CODE)
# ─────────────────────────────────────────────────────────────────────────────

def parse_file_safe(file_path: Path) -> Optional[ast.Module]:
    try:
        source = file_path.read_text(encoding="utf-8", errors="replace")
        return ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None


def extract_file_info(file_path: Path, layer: str) -> FileInfo:
    info = FileInfo(path=file_path, name=file_path.name, layer=layer)
    info.domain = _detect_domain(file_path, layer)
    info.surface = _detect_surface(file_path)

    tree = parse_file_safe(file_path)
    if tree is None:
        return info

    try:
        source_text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return info
    source_lines = source_text.splitlines()
    info.lines_of_code = len(source_lines)

    # v9: Size categorization
    info.size_category = _categorize_size(info.lines_of_code)

    seen_function_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            if node.name in seen_function_names:
                continue
            seen_function_names.add(node.name)
            info.functions.append(node.name)

            fp = _fingerprint_function(node)
            info.function_fingerprints[node.name] = fp

            body_hash = _body_hash(node)
            info.function_body_hashes[node.name] = body_hash

            ops = _extract_model_ops_from_function(node)
            info.function_model_ops[node.name] = ops
            for op in ops:
                info.model_operations.append(op)
                op_hash = hashlib.md5(op.encode()).hexdigest()[:12]
                info.db_operation_hashes.add(op_hash)

        elif isinstance(node, ast.ClassDef):
            info.classes.append(node.name)

    if layer == "router":
        _check_business_logic(tree, source_lines, info)

    _check_imports(tree, info)

    if layer == "controller":
        _check_route_decorators(tree, source_lines, info)
        _detect_adapter_module(tree, source_lines, info)

    # v9: Service-specific analysis
    if layer == "service":
        _analyze_service_file(tree, source_lines, info)

    return info


# ─────────────────────────────────────────────────────────────────────────────
# §2a — FUNCTION FINGERPRINTING & BODY HASHING
# ─────────────────────────────────────────────────────────────────────────────

EMPTY_FINGERPRINT = hashlib.md5("".encode()).hexdigest()


def _categorize_size(lines: int) -> str:
    """Categorize file by line count."""
    if lines <= SIZE_EMPTY_MAX:
        return "empty"
    elif lines <= SIZE_TINY_MAX:
        return "tiny"
    elif lines <= SIZE_THIN_MAX:
        return "thin"
    elif lines <= SIZE_MEDIUM_MAX:
        return "medium"
    else:
        return "large"


def _fingerprint_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    ops: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            call_sig = _call_signature(child)
            if call_sig:
                ops.append(call_sig)
        elif isinstance(child, ast.Attribute):
            attr = child.attr
            if attr in ORM_OPS or attr in ("filter", "filter_by", "first", "all",
                        "join", "outerjoin", "order_by", "group_by", "limit", "offset"):
                ops.append(f"attr:{attr}")
    ops_str = " → ".join(ops)
    return hashlib.md5(ops_str.encode()).hexdigest()


def _body_hash(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    try:
        body_dump = ast.dump(node)
        return hashlib.md5(body_dump.encode()).hexdigest()
    except Exception:
        return ""


def _call_signature(node: ast.Call) -> Optional[str]:
    func = node.func
    if isinstance(func, ast.Attribute):
        method = func.attr
        if isinstance(func.value, ast.Name):
            obj = func.value.id
            return f"call:{obj}.{method}"
        elif isinstance(func.value, ast.Attribute):
            return f"call:??.{method}"
        return f"call:??.{method}"
    elif isinstance(func, ast.Name):
        return f"call:{func.id}"
    return None


def _extract_model_ops_from_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    ops: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if isinstance(child.func, ast.Attribute):
                method = child.func.attr
                if method == "query" and child.args:
                    model_name = _get_type_name(child.args[0])
                    if model_name:
                        ops.append(f"query:{model_name}")
                elif method in ("add", "delete", "merge"):
                    if child.args:
                        arg = child.args[0]
                        if isinstance(arg, ast.Call):
                            model_name = _get_type_name(arg.func)
                            if model_name:
                                ops.append(f"{method}:{model_name}")
                        elif isinstance(arg, ast.Name):
                            ops.append(f"{method}:var:{arg.id}")
                elif method in ("commit", "flush", "rollback"):
                    ops.append(f"{method}:session")
                elif method == "filter" and child.args:
                    filter_expr = ast.dump(child.args[0])
                    col_match = re.findall(r"attr='(\w+)'", filter_expr)
                    if col_match:
                        ops.append(f"filter:{'.'.join(col_match[:2])}")
    return ops


def _get_type_name(node: ast.expr) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return node.attr
    elif isinstance(node, ast.Call):
        return _get_type_name(node.func)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# §2b — SERVICE FILE ANALYSIS (v9 — NEW)
# ─────────────────────────────────────────────────────────────────────────────

def _analyze_service_file(tree: ast.Module, source_lines: list[str], info: FileInfo) -> None:
    """
    v9: Analyze a service file for consolidation signals.
    Detects:
    - Thin forwarders (functions that only call other modules)
    - Read/write split naming
    - Naming variants (suppliers/ vs supplier/)
    """
    # Detect read/write split
    stem_lower = info.path.stem.lower()
    if "_write_service" in stem_lower or "_write_svc" in stem_lower:
        info.is_read_write_split = True
        info.split_type = "write"
    elif "_read_service" in stem_lower or "_read_svc" in stem_lower:
        info.is_read_write_split = True
        info.split_type = "read"

    # Detect naming variant
    parent_folder = info.path.parent.name.lower()
    if parent_folder in NAMING_VARIANTS:
        info.is_naming_variant = True
        info.original_folder = parent_folder
        info.canonical_domain = NAMING_VARIANTS[parent_folder]
    else:
        info.canonical_domain = info.domain

    # Detect thin forwarders
    _detect_thin_forwarder(tree, info)


def _detect_thin_forwarder(tree: ast.Module, info: FileInfo) -> None:
    """
    Detect if a service file is a thin forwarder.
    A thin forwarder has functions that ONLY call functions from other modules
    (no local logic, no DB operations, no complex control flow).
    Uses top-level body statements only (nested helpers do not poison the result).
    """
    if not info.functions:
        info.is_thin_forwarder = False
        return

    forwarding_count = 0
    forwarding_targets: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue

        body_stmts = [s for s in node.body if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
        if len(body_stmts) > 4:
            continue

        has_db_op = False
        func_calls: list[str] = []
        for stmt in body_stmts:
            for child in ast.walk(stmt):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if child.func.attr in ORM_OPS:
                        has_db_op = True
                        break
                if isinstance(child, ast.Call):
                    call_sig = _call_signature(child)
                    if call_sig and call_sig.startswith("call:"):
                        func_calls.append(call_sig)
            if has_db_op:
                break

        if not has_db_op:
            forwarding_count += 1
            for fc in func_calls:
                forwarding_targets.add(fc)

    total_funcs = len(info.functions)
    if total_funcs > 0 and forwarding_count / total_funcs >= THIN_FORWARDER_RATIO:
        info.is_thin_forwarder = True
        info.forwarding_targets = sorted(forwarding_targets)[:10]


def _build_import_map(all_files: list[FileInfo]) -> dict[str, set[str]]:
    """Single-pass build: module_path -> set of files importing it (exact module match)."""
    import_map: dict[str, set[str]] = defaultdict(set)
    for fi in all_files:
        try:
            source = fi.path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(fi.path.relative_to(BACKEND))
        try:
            tree = ast.parse(source)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_map[alias.name].add(rel)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    import_map[node.module].add(rel)
    return import_map


def _get_importers(module_path: str, import_map: dict[str, set[str]]) -> set[str]:
    """Return set of files that import `module_path` (exact match or submodule)."""
    results: set[str] = set()
    for key, files in import_map.items():
        if key == module_path or key.startswith(module_path + "."):
            results.update(files)
    return results


def _service_module_path(svc: FileInfo) -> str:
    """Derive dotted module path for a service file, e.g. services.common.storage."""
    parts = svc.path.with_suffix("").parts
    if "services" in parts:
        return ".".join(parts[parts.index("services"):])
    rel = str(svc.path.relative_to(BACKEND))
    return rel.replace("/", ".").replace("\\", ".").removesuffix(".py")


# ─────────────────────────────────────────────────────────────────────────────
# §2c — BUSINESS LOGIC DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def _check_business_logic(tree: ast.Module, source_lines: list[str], info: FileInfo) -> None:
    for i, line in enumerate(source_lines, 1):
        for pattern in BUSINESS_LOGIC_LINE_PATTERNS:
            if re.search(pattern, line):
                info.has_business_logic = True
                info.business_logic_lines.append(i)
                break

    if info.has_business_logic:
        return

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr not in ORM_OPS:
            continue
        receiver = func.value
        name = ""
        if isinstance(receiver, ast.Name):
            name = receiver.id
        elif isinstance(receiver, ast.Attribute):
            name = receiver.attr
        if name in SESSION_RECEIVERS:
            if hasattr(node, "lineno") and node.lineno not in info.business_logic_lines:
                info.has_business_logic = True
                info.business_logic_lines.append(node.lineno)


# ─────────────────────────────────────────────────────────────────────────────
# §2d — ADAPTER/SHIM DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def _detect_adapter_module(tree: ast.Module, source_lines: list[str], info: FileInfo) -> None:
    source_text = "\n".join(source_lines)

    has_getattr = False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == "__getattr__":
                has_getattr = True
                break

    has_non_import_stmt = False
    has_public_func = False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Expr)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("__"):
                continue
            if _is_dependency_provider(node):
                continue
            has_public_func = True
            has_non_import_stmt = True
        elif isinstance(node, ast.ClassDef):
            has_non_import_stmt = True
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            has_non_import_stmt = True

    all_are_providers = True
    func_count = 0
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("__"):
                continue
            func_count += 1
            if not _is_dependency_provider(node):
                all_are_providers = False

    if has_getattr and not has_public_func:
        info.is_adapter = True
        info.adapter_reason = "__getattr__ lazy-reexport hook (no handlers)"
    elif func_count == 0 and not has_non_import_stmt:
        info.is_adapter = True
        info.adapter_reason = "Pure re-export shim (no handlers)"
    elif func_count > 0 and all_are_providers:
        info.is_adapter = True
        info.adapter_reason = "FastAPI Depends provider module (no handlers)"
    elif func_count == 0:
        info.is_adapter = True
        info.adapter_reason = "No public functions (no handlers)"


def _is_dependency_provider(node: ast.AST) -> bool:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False

    if node.name.startswith(PROVIDER_NAME_PREFIXES):
        return True

    args = node.args
    defaults = list(getattr(args, "defaults", []))
    if args.args and defaults and len(defaults) == len(args.args):
        for d in defaults:
            if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "Depends":
                return True

    if node.returns:
        ret_str = _annotation_to_str(node.returns)
        if ret_str and ret_str in ("Session", "User", "dict", "Optional[User]"):
            if node.name.startswith(("get_", "require_")):
                return True

    return False


# ─────────────────────────────────────────────────────────────────────────────
# §2e — HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def _annotation_to_str(node: Optional[ast.expr]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "Any"


def _detect_domain(file_path: Path, layer: str) -> str:
    parts = file_path.relative_to(BACKEND).parts

    if layer in ("controller", "service", "model"):
        if len(parts) >= 2:
            candidate = parts[1].removesuffix(".py")
            if candidate in CANONICAL_DOMAINS:
                return candidate

            if candidate == "delegators" and len(parts) >= 3:
                delegator_stem = file_path.stem.lower()
                for domain in sorted(CANONICAL_DOMAINS, key=len, reverse=True):
                    if delegator_stem.startswith(domain + "_"):
                        return domain
                first_word = delegator_stem.split("_")[0]
                if first_word in CANONICAL_DOMAINS:
                    return first_word

            stem_lower = file_path.stem.lower()
            stem_words = set(stem_lower.replace("-", "_").split("_"))

            for domain in sorted(CANONICAL_DOMAINS, key=len, reverse=True):
                if domain in stem_words:
                    return domain

    elif layer == "router":
        name = file_path.stem.lower()
        for domain in CANONICAL_DOMAINS:
            if f"_{domain}_" in name or name.startswith(f"{domain}_"):
                return domain

    return "unknown"


def _detect_surface(file_path: Path) -> str:
    name = file_path.stem.lower()
    for surface in SURFACES:
        if name.startswith(surface + "_"):
            return surface
    return "unknown"


def _check_imports(tree: ast.Module, info: FileInfo) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _categorize_import(alias.name, info)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                _categorize_import(node.module, info)


def _categorize_import(module_name: str, info: FileInfo) -> None:
    if module_name.startswith("services"):
        info.imports_services = True
    elif module_name.startswith("controllers"):
        info.imports_controllers = True
    elif module_name.startswith("models"):
        info.imports_models = True
    elif module_name.startswith("db"):
        info.imports_db = True


def _check_route_decorators(tree: ast.Module, source_lines: list[str], info: FileInfo) -> None:
    source_text = "\n".join(source_lines)
    all_decorator_names = set(ROUTE_DECORATOR_NAMES) | set(ROUTE_DECORATOR_ALIASES)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and ("auto_router" in node.module or "route" in node.module):
                for alias in node.names:
                    if alias.name in ROUTE_DECORATOR_NAMES:
                        all_decorator_names.add(alias.asname or alias.name)
                    if alias.asname:
                        all_decorator_names.add(alias.asname)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue

            has_decorator = False
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    if dec.func.id in all_decorator_names:
                        has_decorator = True
                        canonical = _normalize_decorator_name(dec.func.id)
                        if canonical not in info.decorator_names_used:
                            info.decorator_names_used.append(canonical)
                elif isinstance(dec, ast.Name):
                    if dec.id in all_decorator_names:
                        has_decorator = True
                        canonical = _normalize_decorator_name(dec.id)
                        if canonical not in info.decorator_names_used:
                            info.decorator_names_used.append(canonical)
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                    if dec.func.attr in all_decorator_names:
                        has_decorator = True
                        canonical = _normalize_decorator_name(dec.func.attr)
                        if canonical not in info.decorator_names_used:
                            info.decorator_names_used.append(canonical)

            if has_decorator:
                info.has_route_decorator = True
                info.decorated_functions.append(node.name)
            else:
                info.undecorated_functions.append(node.name)

    if not info.has_route_decorator:
        for pattern in ROUTE_DECORATOR_PATTERNS:
            if pattern.search(source_text):
                info.has_route_decorator = True
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if not node.name.startswith("_"):
                            if node.name not in info.decorated_functions:
                                info.decorated_functions.append(node.name)
                break


def _normalize_decorator_name(name: str) -> str:
    alias_map = {
        "api_get": "get", "api_post": "post", "api_put": "put",
        "api_patch": "patch", "api_delete": "delete",
        "http_get": "get", "http_post": "post", "http_put": "put",
        "http_patch": "patch", "http_delete": "delete",
    }
    return alias_map.get(name, name)


def _name_similarity(name1: str, name2: str) -> float:
    set1 = set(name1.replace("_", " ").split())
    set2 = set(name2.replace("_", " ").split())
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union)


# ─────────────────────────────────────────────────────────────────────────────
# §2f — SERVICE CONSOLIDATION ANALYSIS (v9 — NEW)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_service_consolidation(
    services: list[FileInfo],
    all_files: list[FileInfo],
    import_map: dict[str, set[str]] | None = None,
) -> ServiceConsolidationReport:
    """
    v9: Complete service consolidation analysis.
    Returns tiered findings with actionable recommendations.
    """
    report = ServiceConsolidationReport()
    report.total_services = len(services)

    size_distribution: dict[str, int] = {}
    for svc in services:
        size_distribution[svc.size_category] = size_distribution.get(svc.size_category, 0) + 1
    report.size_distribution = size_distribution

    svc_modules: dict[str, FileInfo] = {}
    for svc in services:
        parts = svc.path.with_suffix("").parts
        if "services" in parts:
            mod = ".".join(parts[parts.index("services"):])
        else:
            mod = str(svc.path.relative_to(BACKEND)).replace("/", ".").replace("\\", ".").removesuffix(".py")
        svc_modules[mod] = svc

    # ── Tier 0: Safe deletes (junk/empty) ──
    for svc in services:
        if svc.size_category not in ("empty", "tiny"):
            continue
        rel = str(svc.path.relative_to(BACKEND))
        try:
            parts = svc.path.with_suffix("").parts
            mod = ".".join(parts[parts.index("services"):])
        except (ValueError, IndexError):
            mod = rel.replace("/", ".").replace("\\", ".").removesuffix(".py")
        importers = _get_importers(mod, import_map) if import_map else set()
        public_count = len(svc.functions) + len(svc.classes)
        if public_count == 0 and len(importers) == 0:
            report.tier0_safe_deletes.append(ServiceConsolidationFinding(
                tier=0,
                tier_label="Safe Delete (junk/empty, 0 importers)",
                file_a=rel,
                reason=f"Empty/stub file ({svc.lines_of_code} lines, 0 public symbols, 0 importers)",
                action="DELETE",
                risk="LOW",
                import_impact=sorted(importers),
                recommendation="DELETE — remove file as-is (0 public symbols, 0 importers); no merge needed.",
            ))
        elif public_count == 0 and len(importers) > 0:
            report.tier0_safe_deletes.append(ServiceConsolidationFinding(
                tier=0,
                tier_label="Safe Delete (no public API, but imported)",
                file_a=rel,
                reason=f"No public API ({svc.lines_of_code} lines) but imported by {len(importers)} file(s): {', '.join(sorted(importers)[:3])}",
                action="REVIEW",
                risk="MEDIUM",
                import_impact=sorted(importers),
                recommendation="Do NOT delete yet. Merge any referenced logic into the nearest possible file "
                                "(the importing module or a same-domain sibling), then delete only once the file is empty/orphaned.",
            ))

    tier0_files = {f.file_a for f in report.tier0_safe_deletes}

    # ── Tier 1: Exact content duplicates (byte-identical, non-empty) ──
    content_hashes: dict[str, list[FileInfo]] = defaultdict(list)
    for svc in services:
        if svc.lines_of_code == 0:
            continue
        try:
            content_hash = hashlib.sha256(
                svc.path.read_bytes()
            ).hexdigest()
            content_hashes[content_hash].append(svc)
        except OSError:
            continue

    for content_hash, file_group in content_hashes.items():
        if len(file_group) >= 2:
            for i in range(len(file_group)):
                for j in range(i + 1, len(file_group)):
                    a = str(file_group[i].path.relative_to(BACKEND))
                    b = str(file_group[j].path.relative_to(BACKEND))
                    report.tier1_exact_duplicates.append(ServiceConsolidationFinding(
                        tier=1,
                        tier_label="Exact Content Duplicate",
                        file_a=a,
                        file_b=b,
                        reason="Byte-identical content (non-empty)",
                        similarity=1.0,
                        action="MERGE",
                        risk="LOW",
                    import_impact=sorted(
                        _get_importers(_service_module_path(file_group[i]), import_map)
                        | _get_importers(_service_module_path(file_group[j]), import_map)
                    ) if import_map else [],
                    recommendation=f"Merge with nearest identical file `{b}` — keep one copy, fold the byte-identical duplicate in.",
                    ))

    tier1_files = set()
    for f in report.tier1_exact_duplicates:
        tier1_files.add(f.file_a)
        tier1_files.add(f.file_b)

    # ── Tier 2: Naming variants / domain sprawl ──
    variant_files: dict[str, list[FileInfo]] = defaultdict(list)
    for svc in services:
        if svc.is_naming_variant:
            variant_files[svc.original_folder].append(svc)

    for variant_folder, file_group in variant_files.items():
        canonical = NAMING_VARIANTS.get(variant_folder, variant_folder)
        for svc in file_group:
            rel = str(svc.path.relative_to(BACKEND))
            report.tier2_naming_variants.append(ServiceConsolidationFinding(
                tier=2,
                tier_label="Naming Variant / Domain Sprawl",
                file_a=rel,
                reason=f"Folder '{variant_folder}/' is a naming variant; canonical is '{canonical}/' (opinion, not factual error)",
                action="RENAME",
                risk="MEDIUM",
                import_impact=sorted(
                    _get_importers(_service_module_path(svc), import_map)
                ) if import_map else [],
                recommendation=f"Rename/move into canonical domain folder '{canonical}/' (no logic change).",
            ))

    for svc in services:
        if svc.path.parent == SERVICES_DIR:
            rel = str(svc.path.relative_to(BACKEND))
            report.tier2_naming_variants.append(ServiceConsolidationFinding(
                tier=2,
                tier_label="Root-level service file",
                file_a=rel,
                reason=f"Service '{svc.name}' dumped in services/ root, should be in domain folder (opinion)",
                action="RENAME",
                risk="MEDIUM",
                import_impact=sorted(
                    _get_importers(_service_module_path(svc), import_map)
                ) if import_map else [],
                recommendation="Move into its domain folder under services/<domain>/ (no logic change).",
            ))

    tier2_files = {f.file_a for f in report.tier2_naming_variants}

    # ── Tier 3: Read/Write split sprawl ──
    for svc in services:
        if svc.is_read_write_split:
            rel = str(svc.path.relative_to(BACKEND))
            report.tier3_read_write_split.append(ServiceConsolidationFinding(
                tier=3,
                tier_label=f"Read/Write Split ({svc.split_type})",
                file_a=rel,
                reason=f"{'Read' if svc.split_type == 'read' else 'Write'} service split — "
                       f"should be consolidated with its counterpart",
                action="STANDARDIZE",
                risk="MEDIUM",
                import_impact=sorted(
                    _get_importers(".".join(svc.path.with_suffix("").parts[svc.path.parts.index("services"):]), import_map)
                ) if import_map else [],
                recommendation=f"Merge with nearest possible file — consolidate this {svc.split_type} service "
                               f"with its {('write' if svc.split_type == 'read' else 'read')} counterpart in the same domain.",
            ))

    tier3_files = {f.file_a for f in report.tier3_read_write_split}

    # ── Tier 4: Thin forwarding services ──
    for svc in services:
        if not svc.is_thin_forwarder:
            continue
        rel = str(svc.path.relative_to(BACKEND))
        mod = _service_module_path(svc)
        importers = _get_importers(mod, import_map) if import_map else set()
        public_count = len(svc.functions) + len(svc.classes)
        targets_str = ", ".join(svc.forwarding_targets[:3]) if svc.forwarding_targets else "unknown"
        if public_count > 3 or len(importers) > 5:
            risk = "HIGH"
            action = "REVIEW"
            reason = (
                f"Classified as thin forwarder (forwards to: {targets_str}) "
                f"but has {public_count} public symbols and is imported by {len(importers)} file(s). "
                f"Merging would have wide impact. Verify before merging."
            )
        else:
            risk = "MEDIUM"
            action = "MERGE"
            reason = f"Only forwards to: {targets_str}"
        report.tier4_thin_forwarders.append(ServiceConsolidationFinding(
            tier=4,
            tier_label="Thin Forwarding Service",
            file_a=rel,
            reason=reason,
            action=action,
            risk=risk,
            import_impact=sorted(importers),
            recommendation=f"Merge with nearest possible file — fold this thin forwarder into its target(s): {targets_str}.",
        ))

    tier4_files = {f.file_a for f in report.tier4_thin_forwarders}

    # ── Tier 5: Structural near-duplicates (≥0.6 op-similarity, size-guarded) ──
    services_by_domain: dict[str, list[FileInfo]] = defaultdict(list)
    for svc in services:
        if svc.domain != "unknown":
            services_by_domain[svc.domain].append(svc)

    seen_pairs: set[tuple[str, str]] = set()
    for domain, domain_services in services_by_domain.items():
        for i, s1 in enumerate(domain_services):
            for j, s2 in enumerate(domain_services):
                if i >= j:
                    continue
                p1 = str(s1.path.relative_to(BACKEND))
                p2 = str(s2.path.relative_to(BACKEND))
                pair_key = (min(p1, p2), max(p1, p2))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                ops1 = set(s1.model_operations)
                ops2 = set(s2.model_operations)
                if not ops1 or not ops2:
                    continue

                overlap = ops1 & ops2
                smaller = min(len(ops1), len(ops2))
                larger = max(len(ops1), len(ops2))
                if smaller == 0:
                    continue

                # Size guard: if files differ by >2x in op-count, they're not near-duplicates
                if larger > smaller * 2:
                    continue

                # Use larger-set denominator so subset-inflation can't reach 100%
                similarity = len(overlap) / larger

                if similarity >= SERVICE_STRUCTURAL_THRESHOLD:
                    report.tier5_structural_dups.append(ServiceConsolidationFinding(
                        tier=5,
                        tier_label="Structural Near-Duplicate",
                        file_a=p1,
                        file_b=p2,
                        reason=f"{len(overlap)} shared DB operations ({similarity:.0%} similarity, size-guarded)",
                        similarity=similarity,
                        action="REVIEW",
                        risk="HIGH",
                        import_impact=sorted(
                            _get_importers(_service_module_path(s1), import_map)
                            | _get_importers(_service_module_path(s2), import_map)
                        ) if import_map else [],
                        recommendation=f"Merge with nearest possible file — consolidate with `{p2}` "
                                       f"({len(overlap)} shared DB operations, {similarity:.0%} overlap).",
                    ))

    tier5_files = set()
    for f in report.tier5_structural_dups:
        tier5_files.add(f.file_a)
        tier5_files.add(f.file_b)

    # ── Calculate consolidation targets from UNIQUE files across tiers ──
    tier0_delete_files = {f.file_a for f in report.tier0_safe_deletes if f.action == "DELETE"}
    tier0_review_files = {f.file_a for f in report.tier0_safe_deletes if f.action == "REVIEW"}
    tier1_files = set()
    for f in report.tier1_exact_duplicates:
        tier1_files.add(f.file_a)
        tier1_files.add(f.file_b)
    tier2_files = {f.file_a for f in report.tier2_naming_variants}
    tier3_files = {f.file_a for f in report.tier3_read_write_split}
    tier4_merge_files = {f.file_a for f in report.tier4_thin_forwarders if f.action == "MERGE"}
    tier4_review_files = {f.file_a for f in report.tier4_thin_forwarders if f.action == "REVIEW"}
    tier5_files = set()
    for f in report.tier5_structural_dups:
        tier5_files.add(f.file_a)
        tier5_files.add(f.file_b)

    safe_immediate = tier0_delete_files | tier1_files | tier4_merge_files
    unique_actionable = (
        tier0_delete_files | tier0_review_files | tier1_files |
        tier2_files | tier3_files | tier4_merge_files | tier4_review_files | tier5_files
    )

    report.safe_immediate_reduction = len(safe_immediate)
    report.realistic_target = max(report.total_services - len(unique_actionable), 80)
    report.consolidation_target = report.realistic_target

    return report


# ─────────────────────────────────────────────────────────────────────────────
# §3 — SCANNER
# ─────────────────────────────────────────────────────────────────────────────

def scan_directory(directory: Path, layer: str) -> list[FileInfo]:
    files = []
    if not directory.exists():
        return files
    for py_file in sorted(directory.rglob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        if py_file.name == "__init__.py":
            continue
        if py_file.name.startswith("__"):
            continue
        info = extract_file_info(py_file, layer)
        files.append(info)
    return files


# ─────────────────────────────────────────────────────────────────────────────
# §4 — DUPLICATE DETECTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def build_global_operation_index(
    all_files: list[FileInfo],
) -> dict[str, list[tuple[str, str]]]:
    index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for fi in all_files:
        rel_path = str(fi.path.relative_to(BACKEND))
        for func_name, fp in fi.function_fingerprints.items():
            index[f"fp:{fp}"].append((rel_path, func_name))
        for func_name, ops in fi.function_model_ops.items():
            for op in ops:
                index[f"op:{op}"].append((rel_path, func_name))
    return index


def find_duplicates_for_router_logic(
    router: FileInfo,
    logic_type: str,
    line_numbers: list[int],
    all_files: list[FileInfo],
    op_index: dict[str, list[tuple[str, str]]],
) -> Optional[DuplicateFinding]:
    router_path = str(router.path.relative_to(BACKEND))
    router_model_ops: set[str] = set()
    try:
        source = router.path.read_text(encoding="utf-8", errors="replace")
        lines = source.splitlines()
        for ln in line_numbers:
            if ln <= len(lines):
                line = lines[ln - 1]
                model_matches = re.findall(
                    r"(?:query|add|delete|merge)\s*\(\s*(\w+)", line
                )
                for m in model_matches:
                    router_model_ops.add(m)
    except OSError:
        pass

    if not router_model_ops:
        return None

    best_match: Optional[DuplicateFinding] = None
    best_score = 0.0

    for fi in all_files:
        if fi.layer not in ("service", "controller"):
            continue
        fi_path = str(fi.path.relative_to(BACKEND))
        if fi_path == router_path:
            continue

        for func_name, func_ops_list in fi.function_model_ops.items():
            func_ops = set()
            for op in func_ops_list:
                parts = op.split(":")
                if len(parts) >= 2:
                    func_ops.add(parts[1])

            overlap = router_model_ops & func_ops
            if not overlap:
                continue

            score = len(overlap) / max(len(router_model_ops), 1)
            name_sim = _name_similarity(
                router.name.replace(".py", "").lower(),
                func_name.lower()
            )
            combined_score = score * 0.7 + name_sim * 0.3

            if combined_score > best_score:
                best_score = combined_score
                if score >= 0.9:
                    match_type = MATCH_STRUCTURAL
                elif score >= DUPLICATE_SIMILARITY_THRESHOLD:
                    match_type = MATCH_STRUCTURAL
                else:
                    match_type = MATCH_MODEL_OPS

                best_match = DuplicateFinding(
                    source_file=router_path,
                    source_function=f"lines {line_numbers[0]}-{line_numbers[-1]}" if line_numbers else "unknown",
                    source_lines=line_numbers,
                    existing_file=fi_path,
                    existing_function=func_name,
                    similarity=combined_score,
                    match_type=match_type,
                    db_operations=[f"query:{m}" for m in overlap],
                    recommendation="",
                )

    if best_match and best_match.similarity >= PARTIAL_DUPLICATE_THRESHOLD:
        if best_match.similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
            best_match.recommendation = (
                f"SKIP MIGRATION — similar logic exists in "
                f"`{best_match.existing_file}` → `{best_match.existing_function}()`. "
                f"Wire router to call this existing function instead."
            )
        else:
            best_match.recommendation = (
                f"PARTIAL OVERLAP — similar logic exists in "
                f"`{best_match.existing_file}` → `{best_match.existing_function}()`. "
                f"Review before migrating: consolidate or extend the existing function."
            )
        return best_match

    return None


def find_cross_file_duplicates(
    all_files: list[FileInfo],
) -> tuple[list[DuplicateFinding], list[DuplicateFinding], list[DuplicateFinding]]:
    identical_findings: list[DuplicateFinding] = []
    structural_findings: list[DuplicateFinding] = []
    advisory_overlaps: list[DuplicateFinding] = []
    seen_pairs: set[tuple[str, str, str]] = set()

    services = [f for f in all_files if f.layer == "service"]
    controllers = [f for f in all_files if f.layer == "controller"]

    # IDENTICAL: same function name + same AST body hash
    body_index: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for fi in services + controllers:
        rel_path = str(fi.path.relative_to(BACKEND))
        for func_name, bh in fi.function_body_hashes.items():
            if bh:
                body_index[bh].append((rel_path, func_name, bh))

    for bh, locations in body_index.items():
        if len(locations) < 2:
            continue
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                file_a, func_a, _ = locations[i]
                file_b, func_b, _ = locations[j]
                if func_a != func_b:
                    continue
                pair_key = (min(file_a, file_b), max(file_a, file_b), func_a)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                identical_findings.append(DuplicateFinding(
                    source_file=file_a,
                    source_function=func_a,
                    source_lines=[],
                    existing_file=file_b,
                    existing_function=func_b,
                    similarity=1.0,
                    match_type=MATCH_IDENTICAL,
                    db_operations=[],
                    recommendation=(
                        f"TRUE DUPLICATE — `{file_a}::{func_a}()` is byte-identical "
                        f"to `{file_b}::{func_b}()`. "
                        f"Keep ONE, delete the other, import from canonical location."
                    ),
                ))

    # STRUCTURAL: same operation sequence, different function names
    fp_index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for fi in services + controllers:
        rel_path = str(fi.path.relative_to(BACKEND))
        for func_name, fp in fi.function_fingerprints.items():
            if fp == EMPTY_FINGERPRINT:
                continue
            fp_index[fp].append((rel_path, func_name))

    for fp, locations in fp_index.items():
        if len(locations) < 2:
            continue
        for i in range(len(locations)):
            for j in range(i + 1, len(locations)):
                file_a, func_a = locations[i]
                file_b, func_b = locations[j]
                pair_key_ident = (min(file_a, file_b), max(file_a, file_b), func_a)
                if pair_key_ident in seen_pairs:
                    continue
                if func_a == func_b and file_a != file_b:
                    continue
                pair_key = (min(file_a, file_b), max(file_a, file_b), f"{func_a}:{func_b}")
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                structural_findings.append(DuplicateFinding(
                    source_file=file_a,
                    source_function=func_a,
                    source_lines=[],
                    existing_file=file_b,
                    existing_function=func_b,
                    similarity=0.85,
                    match_type=MATCH_STRUCTURAL,
                    db_operations=[],
                    recommendation=(
                        f"STRUCTURAL SIMILARITY — `{file_a}::{func_a}()` and "
                        f"`{file_b}::{func_b}()` share the same operation sequence. "
                        f"These are NOT identical functions. Review for consolidation "
                        f"only if they truly do the same thing."
                    ),
                ))

    # MODEL_OPS overlaps
    services_by_domain: dict[str, list[FileInfo]] = defaultdict(list)
    for s in services:
        if s.domain != "unknown":
            services_by_domain[s.domain].append(s)

    controllers_by_domain: dict[str, list[FileInfo]] = defaultdict(list)
    for c in controllers:
        if c.domain != "unknown":
            controllers_by_domain[c.domain].append(c)

    for domain, domain_services in services_by_domain.items():
        for i, s1 in enumerate(domain_services):
            for s2 in domain_services[i + 1:]:
                _check_model_ops_overlap(s1, s2, advisory_overlaps, seen_pairs)

    for domain, domain_controllers in controllers_by_domain.items():
        for i, c1 in enumerate(domain_controllers):
            for c2 in domain_controllers[i + 1:]:
                _check_model_ops_overlap(c1, c2, advisory_overlaps, seen_pairs)

    for domain in set(list(services_by_domain.keys()) + list(controllers_by_domain.keys())):
        for c in controllers_by_domain.get(domain, []):
            for s in services_by_domain.get(domain, []):
                _check_model_ops_overlap(c, s, advisory_overlaps, seen_pairs)

    return identical_findings, structural_findings, advisory_overlaps


def _check_model_ops_overlap(
    f1: FileInfo,
    f2: FileInfo,
    advisory_overlaps: list[DuplicateFinding],
    seen_pairs: set[tuple[str, str, str]],
) -> None:
    p1 = str(f1.path.relative_to(BACKEND))
    p2 = str(f2.path.relative_to(BACKEND))

    pair_key = (min(p1, p2), max(p1, p2), "model_ops")
    if pair_key in seen_pairs:
        return
    seen_pairs.add(pair_key)

    ops1 = set(f1.model_operations)
    ops2 = set(f2.model_operations)

    if not ops1 or not ops2:
        return

    overlap = ops1 & ops2
    overlap_count = len(overlap)

    if overlap_count < MODEL_OPS_MIN_OVERLAP:
        return

    smaller_set_size = min(len(ops1), len(ops2))
    if smaller_set_size == 0:
        return
    overlap_ratio = overlap_count / smaller_set_size
    if overlap_ratio < MODEL_OPS_MIN_RATIO:
        return

    similarity = min(overlap_ratio, 1.0)

    advisory_overlaps.append(DuplicateFinding(
        source_file=p1,
        source_function="(multiple functions)",
        source_lines=[],
        existing_file=p2,
        existing_function="(multiple functions)",
        similarity=similarity,
        match_type=MATCH_MODEL_OPS,
        db_operations=sorted(overlap)[:5],
        recommendation=(
            f"ADVISORY OVERLAP — {overlap_count} shared DB operations "
            f"({overlap_ratio:.0%} of smaller set) between `{p1}` and `{p2}`. "
            f"Review for consolidation: {', '.join(sorted(overlap)[:3])}..."
        ),
    ))


# ─────────────────────────────────────────────────────────────────────────────
# §5 — AUDIT ENGINE (v9)
# ─────────────────────────────────────────────────────────────────────────────

def run_full_audit(strict: bool = False) -> AuditReport:
    report = AuditReport()
    report.timestamp = datetime.now(timezone.utc).isoformat()

    print("=" * 80)
    print("  ZOZI ARCHITECTURE AUDIT & MIGRATION TRACKER (v9 — Service Consolidation)")
    print("=" * 80)
    print()

    # ── Pre-scan snapshot ──
    print("📸 Taking pre-scan file inventory snapshot...")
    pre_snapshot = take_file_snapshot()
    pre_hash = compute_snapshot_hash(pre_snapshot)
    pre_count = len(pre_snapshot)
    report.file_count_pre = pre_count
    print(f"   Snapshot: {pre_count} files, hash={pre_hash[:16]}...")
    print()

    # ── Scan with drift detection ──
    scan_start = datetime.now(timezone.utc)
    report.scan_start_time = scan_start.isoformat()

    for attempt in range(1, MAX_RESCAN_ATTEMPTS + 1):
        report.scan_attempts = attempt

        if attempt > 1:
            print(f"🔄 Rescan attempt {attempt}/{MAX_RESCAN_ATTEMPTS} (drift detected)...")
            pre_snapshot = take_file_snapshot()
            pre_hash = compute_snapshot_hash(pre_snapshot)
            pre_count = len(pre_snapshot)
            report.file_count_pre = pre_count
            scan_start = datetime.now(timezone.utc)
            report.scan_start_time = scan_start.isoformat()
            print()

        # Phase 1: Scan all layers
        print("📂 Phase 1: Scanning all layers...")
        routers = scan_directory(ROUTERS_DIR, "router")
        controllers = scan_directory(CONTROLLERS_DIR, "controller")
        services = scan_directory(SERVICES_DIR, "service")
        models = scan_directory(MODELS_DIR, "model")

        # Post-scan consistency check
        is_consistent, added, removed, modified = check_snapshot_consistency(pre_snapshot)

        if is_consistent:
            report.scan_consistent = True
            print(f"   ✅ Scan consistent (no file changes during scan)")
            break
        else:
            report.scan_consistent = False
            drift_details = []
            if added:
                drift_details.append(f"+{len(added)} added: {', '.join(added[:3])}")
            if removed:
                drift_details.append(f"-{len(removed)} removed: {', '.join(removed[:3])}")
            if modified:
                drift_details.append(f"~{len(modified)} modified: {', '.join(modified[:3])}")
            drift_str = "; ".join(drift_details)
            print(f"   ⚠️  Drift detected during scan: {drift_str}")
            if attempt >= MAX_RESCAN_ATTEMPTS:
                print(f"   ❌ Max rescan attempts reached. Proceeding with last scan.")
                if strict:
                    print(f"   ❌ --strict mode: exiting with code 2.")
                    sys.exit(2)
            else:
                print(f"   Retrying scan...")

    scan_end = datetime.now(timezone.utc)
    report.scan_end_time = scan_end.isoformat()
    report.scan_duration_ms = (scan_end - scan_start).total_seconds() * 1000

    post_snapshot = take_file_snapshot()
    report.file_count_post = len(post_snapshot)

    report.total_routers = len(routers)
    report.total_controllers = len(controllers)
    report.total_services = len(services)
    report.total_models = len(models)

    print(f"   Routers:     {len(routers)}")
    print(f"   Controllers: {len(controllers)}")
    print(f"   Services:    {len(services)}")
    print(f"   Models:      {len(models)}")
    print(f"   Scan window: {report.scan_start_time} → {report.scan_end_time} "
          f"({report.scan_duration_ms:.0f} ms)")
    print()

    all_files = routers + controllers + services + models
    for f in all_files:
        key = str(f.path.relative_to(BACKEND))
        report.file_infos[key] = f

    # Phase 2: Identify business logic in routers
    print("🔍 Phase 2: Identifying business logic in routers...")
    routers_with_logic = [r for r in routers if r.has_business_logic]
    report.routers_with_business_logic = len(routers_with_logic)
    print(f"   Routers with business logic: {len(routers_with_logic)} / {len(routers)}")
    print()

    # Phase 3: Check controller decorator readiness
    print("🏷️  Phase 3: Checking controller decorator readiness...")
    decorated = [c for c in controllers if c.has_route_decorator]
    undecorated = [c for c in controllers if not c.has_route_decorator]
    adapters = [c for c in controllers if c.is_adapter]
    genuine_undecorated = [c for c in undecorated if not c.is_adapter]

    report.controllers_with_decorators = len(decorated)
    report.controllers_without_decorators = len(genuine_undecorated)
    report.ready_controllers = [str(c.path.relative_to(BACKEND)) for c in decorated]
    report.not_ready_controllers = [str(c.path.relative_to(BACKEND)) for c in genuine_undecorated]
    report.adapter_controllers = [str(c.path.relative_to(BACKEND)) for c in adapters]

    all_decorator_names: set[str] = set()
    for c in decorated:
        all_decorator_names.update(c.decorator_names_used)

    decorator_label = "/".join(f"@{d}" for d in sorted(all_decorator_names)) if all_decorator_names else "@get/@post/@put/@patch/@delete"

    print(f"   Controllers with route decorators ({decorator_label}): {len(decorated)}")
    print(f"   Adapter/shim/delegator/Depends-provider (excluded): {len(adapters)}")
    print(f"   Genuine controllers missing decorators: {len(genuine_undecorated)}")
    print()

    # Phase 3a: Build global operation index
    print("🔎 Phase 3a: Building global operation index...")
    op_index = build_global_operation_index(all_files)
    total_ops = sum(len(v) for v in op_index.values())
    print(f"   Indexed {total_ops} operation references across {len(all_files)} files")
    print()

    # Phase 3b: Cross-file duplicate detection
    print("🔎 Phase 3b: Detecting cross-file duplicate logic...")
    identical_dups, structural_dups, advisory_overlaps = find_cross_file_duplicates(all_files)
    report.identical_findings = identical_dups
    report.structural_findings = structural_dups
    report.advisory_overlaps = advisory_overlaps[:MAX_ADVISORY_OVERLAPS_REPORT]

    print(f"   True duplicates (IDENTICAL):     {len(identical_dups)}")
    print(f"   Structural similarity matches:   {len(structural_dups)}")
    print(f"   Advisory overlaps (MODEL_OPS):   {len(advisory_overlaps)}")
    if len(advisory_overlaps) > MAX_ADVISORY_OVERLAPS_REPORT:
        print(f"   ⚠️  Advisory overlaps capped at {MAX_ADVISORY_OVERLAPS_REPORT} in report")
    print()

    # Phase 3c: v9 — Service consolidation analysis
    print("🔎 Phase 3c: Analyzing service consolidation (v9)...")
    import_map = _build_import_map(all_files)
    report.service_consolidation = analyze_service_consolidation(services, all_files, import_map)
    sc = report.service_consolidation
    print(f"   Total services:                 {sc.total_services}")
    print(f"   Size distribution:              {sc.size_distribution}")
    print(f"   Tier 0 (safe deletes):          {len(sc.tier0_safe_deletes)}")
    print(f"   Tier 1 (exact duplicates):      {len(sc.tier1_exact_duplicates)}")
    print(f"   Tier 2 (naming variants):       {len(sc.tier2_naming_variants)}")
    print(f"   Tier 3 (read/write split):      {len(sc.tier3_read_write_split)}")
    print(f"   Tier 4 (thin forwarders):       {len(sc.tier4_thin_forwarders)}")
    print(f"   Tier 5 (structural dups):       {len(sc.tier5_structural_dups)}")
    print(f"   Safe immediate reduction:       {sc.safe_immediate_reduction}")
    print(f"   Realistic consolidation target: {sc.realistic_target}")
    print()

    # Phase 4: Generate migration tasks
    print("📋 Phase 4: Generating migration tasks (routers → controllers/services)...")
    report.migration_tasks = _generate_migration_tasks(
        routers_with_logic, controllers, services, all_files, op_index, report
    )

    already_exists = [t for t in report.migration_tasks if t.resolution == "ALREADY_EXISTS"]
    partial_dups = [t for t in report.migration_tasks if t.resolution == "PARTIAL_DUPLICATE"]
    actual_migrations = [t for t in report.migration_tasks if t.resolution == "MIGRATE"]

    report.duplicates_skipped = len(already_exists)
    report.partial_duplicates = len(partial_dups)
    report.actual_migrations_needed = len(actual_migrations)

    print(f"   Total migration tasks:      {len(report.migration_tasks)}")
    print(f"   ⏭️  Skipped (already exists): {len(already_exists)}")
    print(f"   ⚠️  Partial duplicates:       {len(partial_dups)}")
    print(f"   ✅ Actual migrations needed:  {len(actual_migrations)}")
    print()

    # Phase 5: Generate wiring tasks
    print("🔗 Phase 5: Generating wiring plan (models ↔ services ↔ controllers)...")
    report.wiring_tasks = _generate_wiring_tasks(models, services, controllers, routers)
    print(f"   Wiring tasks generated: {len(report.wiring_tasks)}")
    print()

    # Phase 6: Identify missing files/folders
    print("🕳️  Phase 6: Identifying missing files and folders...")
    report.missing_items = _identify_missing_items(models, services, controllers, routers, import_map)
    print(f"   Missing items found: {len(report.missing_items)}")
    print()

    # Phase 7: Generate report
    print("📝 Phase 7: Generating report...")
    _generate_report(report, decorator_label)
    print(f"   Report saved to: {REPORT_OUTPUT}")
    print()

    # Summary
    print("=" * 80)
    print("  AUDIT SUMMARY (v9 — Service Consolidation)")
    print("=" * 80)
    print(f"  Scan window:                  {report.scan_start_time} → {report.scan_end_time}")
    print(f"  Scan duration:                {report.scan_duration_ms:.0f} ms")
    print(f"  Scan consistent:              {'✅ Yes' if report.scan_consistent else '⚠️ Drift detected'}")
    print(f"  Scan attempts:                {report.scan_attempts}")
    print(f"  Files pre-scan:               {report.file_count_pre}")
    print(f"  Files post-scan:              {report.file_count_post}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Total Routers:                {report.total_routers}")
    print(f"  Routers with business logic:  {report.routers_with_business_logic}")
    print(f"  Total Controllers:            {report.total_controllers}")
    print(f"    ├─ with decorators:         {report.controllers_with_decorators}")
    print(f"    ├─ adapter/shim (excluded): {len(report.adapter_controllers)}")
    print(f"    └─ genuine missing:         {report.controllers_without_decorators}")
    print(f"  Total Services:               {report.total_services}")
    print(f"    ├─ Size: empty={sc.size_distribution.get('empty', 0)}, "
          f"tiny={sc.size_distribution.get('tiny', 0)}, "
          f"thin={sc.size_distribution.get('thin', 0)}, "
          f"medium={sc.size_distribution.get('medium', 0)}, "
          f"large={sc.size_distribution.get('large', 0)}")
    print(f"    ├─ Tier 0 safe deletes:     {len(sc.tier0_safe_deletes)}")
    print(f"    ├─ Tier 1 exact dups:       {len(sc.tier1_exact_duplicates)}")
    print(f"    ├─ Tier 2 naming variants:  {len(sc.tier2_naming_variants)}")
    print(f"    ├─ Tier 3 read/write split: {len(sc.tier3_read_write_split)}")
    print(f"    ├─ Tier 4 thin forwarders:  {len(sc.tier4_thin_forwarders)}")
    print(f"    └─ Tier 5 structural dups:  {len(sc.tier5_structural_dups)}")
    print(f"  Total Models:                 {report.total_models}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Migration tasks (total):      {len(report.migration_tasks)}")
    print(f"  ⏭️  Already exists (SKIP):     {report.duplicates_skipped}")
    print(f"  ⚠️  Partial duplicates (REVIEW): {report.partial_duplicates}")
    print(f"  ✅ Actual migrations needed:   {report.actual_migrations_needed}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  True duplicates (IDENTICAL):  {len(report.identical_findings)}")
    print(f"  Structural similarity:        {len(report.structural_findings)}")
    print(f"  Advisory overlaps (heuristic):{len(report.advisory_overlaps)}")
    print(f"  Wiring tasks:                 {len(report.wiring_tasks)}")
    print(f"  Missing items:                {len(report.missing_items)}")
    print(f"  Ready for auto-gen:           {len(report.ready_controllers)}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Service consolidation target: {sc.consolidation_target} "
          f"(from {sc.total_services})")
    print("=" * 80)

    return report


# ─────────────────────────────────────────────────────────────────────────────
# §6 — MIGRATION TASK GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def _generate_migration_tasks(
    routers_with_logic: list[FileInfo],
    controllers: list[FileInfo],
    services: list[FileInfo],
    all_files: list[FileInfo],
    op_index: dict[str, list[tuple[str, str]]],
    report: AuditReport,
) -> list[MigrationTask]:
    tasks = []

    controllers_by_domain = defaultdict(list)
    services_by_domain = defaultdict(list)
    for c in controllers:
        controllers_by_domain[c.domain].append(c)
    for s in services:
        services_by_domain[s.domain].append(s)

    for router in routers_with_logic:
        domain = router.domain
        target_controller = _find_best_match(router, controllers_by_domain.get(domain, []))
        target_service = _find_best_match(router, services_by_domain.get(domain, []))
        logic_types = _categorize_logic_lines(router)

        for logic_type, lines in logic_types.items():
            if logic_type in ("db_write", "db_query", "model_access"):
                target = target_service or _suggest_service_path(domain, logic_type)
            else:
                target = target_controller or _suggest_controller_path(domain, router.surface)

            target_path = (
                str(target.path.relative_to(BACKEND))
                if isinstance(target, FileInfo)
                else target
            )

            dup = find_duplicates_for_router_logic(
                router, logic_type, lines, all_files, op_index
            )

            if dup and dup.similarity >= DUPLICATE_SIMILARITY_THRESHOLD:
                resolution = "ALREADY_EXISTS"
                status = "SKIP"
                description = (
                    f"SKIP — similar {logic_type} exists in "
                    f"`{dup.existing_file}` → `{dup.existing_function}()`. "
                    f"Wire router to call this existing function."
                )
                target_path = dup.existing_file
            elif dup and dup.similarity >= PARTIAL_DUPLICATE_THRESHOLD:
                resolution = "PARTIAL_DUPLICATE"
                status = "REVIEW"
                description = (
                    f"REVIEW — similar {logic_type} exists in "
                    f"`{dup.existing_file}` → `{dup.existing_function}()`. "
                    f"Consolidate before migrating."
                )
            else:
                resolution = "MIGRATE"
                status = "PENDING"
                description = (
                    f"Move {logic_type} from router to "
                    f"{'service' if logic_type in ('db_write', 'db_query', 'model_access') else 'controller'}"
                )

            task = MigrationTask(
                source_file=str(router.path.relative_to(BACKEND)),
                target_file=target_path,
                logic_type=logic_type,
                line_numbers=lines,
                description=description,
                priority="HIGH" if logic_type == "db_write" else "MEDIUM",
                status=status,
                already_exists_in=dup.existing_file if dup else "",
                duplicate_function=dup.existing_function if dup else "",
                duplicate_confidence=dup.similarity if dup else 0.0,
                resolution=resolution,
            )
            tasks.append(task)

    return tasks


def _find_best_match(router: FileInfo, candidates: list[FileInfo]) -> Optional[FileInfo]:
    if not candidates:
        return None
    for c in candidates:
        if c.domain == router.domain and c.surface == router.surface:
            return c
    for c in candidates:
        if c.domain == router.domain:
            return c
    router_name = router.path.stem.lower()
    best_score = 0
    best_match = None
    for c in candidates:
        score = _name_similarity(router_name, c.path.stem.lower())
        if score > best_score:
            best_score = score
            best_match = c
    return best_match if best_score > 0.3 else None


def _categorize_logic_lines(router: FileInfo) -> dict[str, list[int]]:
    categories = defaultdict(list)
    try:
        source = router.path.read_text(encoding="utf-8", errors="replace")
        lines = source.splitlines()
    except OSError:
        return categories

    for line_num in router.business_logic_lines:
        if line_num <= len(lines):
            line = lines[line_num - 1]
            if re.search(r"(db|session)\.(add|commit|delete|merge|flush)\(", line):
                categories["db_write"].append(line_num)
            elif re.search(r"(db|session)\.(query|execute|scalar)\(", line) or ".query(" in line:
                categories["db_query"].append(line_num)
            elif re.search(r"(from|import)\s+models", line):
                categories["model_access"].append(line_num)
            else:
                categories["business_logic"].append(line_num)

    return categories


def _suggest_service_path(domain: str, logic_type: str) -> str:
    return f"services/{domain}/{domain}_{logic_type}_service.py"


def _suggest_controller_path(domain: str, surface: str) -> str:
    return f"controllers/{domain}/{surface}_{domain}_controller.py"


# ─────────────────────────────────────────────────────────────────────────────
# §7 — WIRING TASK GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def _generate_wiring_tasks(
    models: list[FileInfo],
    services: list[FileInfo],
    controllers: list[FileInfo],
    routers: list[FileInfo],
) -> list[WiringTask]:
    tasks = []
    models_by_domain = defaultdict(list)
    services_by_domain = defaultdict(list)
    controllers_by_domain = defaultdict(list)
    routers_by_domain = defaultdict(list)

    for m in models:
        models_by_domain[m.domain].append(m)
    for s in services:
        services_by_domain[s.domain].append(s)
    for c in controllers:
        controllers_by_domain[c.domain].append(c)
    for r in routers:
        routers_by_domain[r.domain].append(r)

    all_domains = set(
        list(models_by_domain.keys()) + list(services_by_domain.keys()) +
        list(controllers_by_domain.keys()) + list(routers_by_domain.keys())
    )

    for domain in sorted(all_domains):
        if domain == "unknown":
            continue

        domain_models = models_by_domain.get(domain, [])
        if not domain_models:
            continue

        domain_services = services_by_domain.get(domain, [])
        domain_controllers = controllers_by_domain.get(domain, [])
        domain_routers = routers_by_domain.get(domain, [])

        for model in domain_models:
            model_name = model.path.stem.lower()
            matching_service = None
            for svc in domain_services:
                if _name_similarity(model_name, svc.path.stem.lower()) > 0.3:
                    matching_service = svc
                    break
            matching_controller = None
            for ctrl in domain_controllers:
                if _name_similarity(model_name, ctrl.path.stem.lower()) > 0.3:
                    matching_controller = ctrl
                    break
            matching_router = None
            for rtr in domain_routers:
                if _name_similarity(model_name, rtr.path.stem.lower()) > 0.3:
                    matching_router = rtr
                    break

            missing = []
            if not matching_service:
                missing.append(f"Service for {model.name}")
            if not matching_controller:
                missing.append(f"Controller for {model.name}")
            if not matching_router:
                missing.append(f"Router for {model.name}")
            if matching_service and not matching_service.imports_models:
                missing.append(f"Service {matching_service.name} doesn't import model")
            if matching_controller and not matching_controller.imports_services:
                missing.append(f"Controller {matching_controller.name} doesn't import service")

            status = "COMPLETE" if not missing else "INCOMPLETE"
            task = WiringTask(
                model_file=str(model.path.relative_to(BACKEND)),
                service_file=str(matching_service.path.relative_to(BACKEND)) if matching_service else "MISSING",
                controller_file=str(matching_controller.path.relative_to(BACKEND)) if matching_controller else "MISSING",
                router_file=str(matching_router.path.relative_to(BACKEND)) if matching_router else "MISSING",
                status=status,
                missing_pieces=missing,
            )
            tasks.append(task)

    return tasks


# ─────────────────────────────────────────────────────────────────────────────
# §8 — MISSING ITEMS IDENTIFIER
# ─────────────────────────────────────────────────────────────────────────────

def _identify_missing_items(
    models: list[FileInfo],
    services: list[FileInfo],
    controllers: list[FileInfo],
    routers: list[FileInfo],
    import_map: dict[str, set[str]] | None = None,
) -> list[MissingItem]:
    missing = []
    reported_paths: set[str] = set()

    def _add_missing(item_type: str, path: str, reason: str, priority: str = "MEDIUM") -> None:
        if path in reported_paths:
            return
        reported_paths.add(path)
        missing.append(MissingItem(
            item_type=item_type, path=path, reason=reason, priority=priority,
        ))

    for domain in CANONICAL_DOMAINS:
        model_domain_dir = MODELS_DIR / domain
        if not model_domain_dir.exists():
            imported = any(
                (k == f"models.{domain}" or k.startswith(f"models.{domain}."))
                for k in import_map.keys()
            ) if import_map else False
            if imported:
                _add_missing("folder", f"models/{domain}/",
                             f"Models reference domain '{domain}' but folder doesn't exist", "HIGH")

        service_domain_dir = SERVICES_DIR / domain
        if not service_domain_dir.exists():
            imported = any(
                (k == f"services.{domain}" or k.startswith(f"services.{domain}."))
                for k in import_map.keys()
            ) if import_map else False
            if imported:
                _add_missing("folder", f"services/{domain}/",
                             f"Services reference domain '{domain}' but folder doesn't exist", "HIGH")

        controller_domain_dir = CONTROLLERS_DIR / domain
        if not controller_domain_dir.exists():
            imported = any(
                (k == f"controllers.{domain}" or k.startswith(f"controllers.{domain}."))
                for k in import_map.keys()
            ) if import_map else False
            if imported:
                _add_missing("folder", f"controllers/{domain}/",
                             f"Controllers reference domain '{domain}' but folder doesn't exist", "HIGH")

    for c in controllers:
        if c.path.parent == CONTROLLERS_DIR:
            _add_missing("file", str(c.path.relative_to(BACKEND)),
                         f"Controller '{c.name}' is at root level, should be in controllers/{c.domain}/ (style recommendation)", "MEDIUM")

    for s in services:
        if s.path.parent == SERVICES_DIR:
            _add_missing("file", str(s.path.relative_to(BACKEND)),
                         f"Service '{s.name}' is at root level, should be in services/{s.domain}/ (style recommendation)", "MEDIUM")

    for domain in CANONICAL_DOMAINS:
        for layer_dir in [MODELS_DIR, SERVICES_DIR, CONTROLLERS_DIR]:
            domain_dir = layer_dir / domain
            if domain_dir.exists() and not (domain_dir / "__init__.py").exists():
                _add_missing("file", f"{layer_dir.name}/{domain}/__init__.py",
                             "Missing __init__.py in domain package (Python 3 namespace packages work without this — cosmetic)", "LOW")

    services_without_controllers = set()
    for s in services:
        if s.domain == "unknown":
            continue
        if not (CONTROLLERS_DIR / s.domain).exists():
            services_without_controllers.add(s.domain)
    for domain in sorted(services_without_controllers):
        _add_missing("file", f"controllers/{domain}/",
                     f"Domain '{domain}' has services but no controllers folder", "HIGH")

    controllers_without_services = set()
    for c in controllers:
        if c.domain == "unknown":
            continue
        if not (SERVICES_DIR / c.domain).exists():
            controllers_without_services.add(c.domain)
    for domain in sorted(controllers_without_services):
        _add_missing("file", f"services/{domain}/",
                     f"Domain '{domain}' has controllers but no services folder", "HIGH")

    return missing


# ─────────────────────────────────────────────────────────────────────────────
# §9 — REPORT GENERATOR (v9)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_report(report: AuditReport, decorator_label: str) -> None:
    lines = []
    lines.append("# ZOZI Architecture Migration & Audit Report (v9 — Service Consolidation)")
    lines.append(f"\n**Generated:** {report.timestamp}")
    lines.append(f"**Status:** {'🔴 ACTION REQUIRED' if report.actual_migrations_needed > 0 else '🟢 CLEAN'}")
    lines.append("")

    # Scan window metadata
    lines.append("## Scan Window")
    lines.append("")
    lines.append(f"| Property | Value |")
    lines.append(f"|----------|-------|")
    lines.append(f"| Scan start | `{report.scan_start_time}` |")
    lines.append(f"| Scan end | `{report.scan_end_time}` |")
    lines.append(f"| Duration | {report.scan_duration_ms:.0f} ms |")
    lines.append(f"| Attempts | {report.scan_attempts} |")
    lines.append(f"| Consistent | {'✅ Yes' if report.scan_consistent else '⚠️ Drift detected (rescanned)'} |")
    lines.append(f"| Files pre-scan | {report.file_count_pre} |")
    lines.append(f"| Files post-scan | {report.file_count_post} |")
    lines.append("")
    lines.append("> This report is accurate for the file system state within the scan window above.")
    lines.append("> Files added/removed after the scan window are NOT reflected in this report.")
    lines.append("")

    # Verification metadata
    lines.append("## Verification Status")
    lines.append("")
    lines.append("| Claim | Verification | Method |")
    lines.append("|-------|-------------|--------|")
    lines.append(f"| File counts (routers/controllers/services/models) | ✅ Verified | File inventory snapshot (pre/post scan) |")
    lines.append(f"| Decorator detection | ✅ Verified | AST parse + source text grep |")
    lines.append(f"| Adapter/shim detection | ✅ Verified | AST structure analysis |")
    lines.append(f"| Business logic detection | ✅ Verified | Scoped AST + regex (no ast.dump substring) |")
    lines.append(f"| Service size distribution | ✅ Verified | Line count analysis |")
    lines.append(f"| Tier 0 safe-delete eligibility | ✅ Verified | Size + 0 public symbols + 0 importers (single-pass import map) |")
    lines.append(f"| Tier 1 exact duplicates | ✅ Verified | SHA-256 content hash (empty files excluded) |")
    lines.append(f"| Tier 2 naming variants | ⚠️ Heuristic | Folder-name mapping (opinion, not factual error) |")
    lines.append(f"| Tier 3 read/write split | ✅ Verified | Filename pattern (_read_service / _write_service) |")
    lines.append(f"| Tier 4 thin forwarders | ⚠️ Heuristic | AST body-statement analysis (top-level only) + importer risk guard |")
    lines.append(f"| Tier 5 structural dups | ⚠️ Heuristic | DB-op set similarity (size-guarded, Jaccard on larger set) |")
    lines.append(f"| Missing folders | ✅ Verified | Live-tree existence + actual import-map check |")
    lines.append(f"| Root-level files (style) | ✅ Verified | File path inspection |")
    lines.append(f"| Structural similarity counts | ⚠️ Heuristic | Fingerprint hashing (operation sequence) |")
    lines.append(f"| True duplicate counts | ✅ Verified | AST body hash + same name (non-empty only) |")
    lines.append(f"| Advisory overlap counts | ⚠️ Heuristic | DB operation set intersection |")
    lines.append(f"| Migration task counts | ⚠️ Heuristic | Pattern-based logic extraction |")
    lines.append(f"| Wiring completeness | ⚠️ Heuristic | Name-similarity matching |")
    lines.append("")

    # Executive Summary
    sc = report.service_consolidation
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("| Metric | Count | Status |")
    lines.append("|--------|-------|--------|")
    lines.append(f"| Total Routers | {report.total_routers} | {'🔴' if report.routers_with_business_logic > 0 else '🟢'} |")
    lines.append(f"| Routers with Business Logic | {report.routers_with_business_logic} | {'🔴 NEEDS MIGRATION' if report.routers_with_business_logic > 0 else '🟢 CLEAN'} |")
    lines.append(f"| Total Controllers | {report.total_controllers} | - |")
    lines.append(f"| ├─ with route decorators ({decorator_label}) | {report.controllers_with_decorators} | 🟢 READY |")
    lines.append(f"| ├─ adapter/shim modules (no handlers — excluded by design) | {len(report.adapter_controllers)} | 🟢 CORRECT |")
    lines.append(f"| └─ genuine controllers missing decorators | {report.controllers_without_decorators} | {'🔴 NEEDS DECORATORS' if report.controllers_without_decorators > 0 else '🟢 NONE'} |")
    lines.append(f"| Total Services | {report.total_services} | {'🔴 NEEDS CONSOLIDATION' if report.total_services > 400 else '🟢 OK'} |")
    lines.append(f"| ├─ Size: empty | {sc.size_distribution.get('empty', 0)} | 🗑️ DELETE |")
    lines.append(f"| ├─ Size: tiny (≤30 lines) | {sc.size_distribution.get('tiny', 0)} | 🟡 REVIEW |")
    lines.append(f"| ├─ Size: thin (≤100 lines) | {sc.size_distribution.get('thin', 0)} | 🟡 REVIEW |")
    lines.append(f"| ├─ Size: medium (≤300 lines) | {sc.size_distribution.get('medium', 0)} | 🟢 OK |")
    lines.append(f"| └─ Size: large (>300 lines) | {sc.size_distribution.get('large', 0)} | 🟢 OK |")
    lines.append(f"| Total Models | {report.total_models} | - |")
    lines.append(f"| Migration Tasks (total) | {len(report.migration_tasks)} | - |")
    lines.append(f"| ⏭️ Already Exists (SKIP) | {report.duplicates_skipped} | - |")
    lines.append(f"| ⚠️ Partial Duplicates (REVIEW) | {report.partial_duplicates} | - |")
    lines.append(f"| ✅ Actual Migrations Needed | {report.actual_migrations_needed} | {'🔴 PENDING' if report.actual_migrations_needed > 0 else '🟢 NONE'} |")
    lines.append(f"| True Duplicates (IDENTICAL) | {len(report.identical_findings)} | {'🔴 CONSOLIDATE' if report.identical_findings else '🟢 CLEAN'} |")
    lines.append(f"| Structural Similarity (NOT exact) | {len(report.structural_findings)} | ⚠️ Heuristic |")
    lines.append(f"| Advisory Overlaps (heuristic) | {len(report.advisory_overlaps)} | ⚠️ Heuristic |")
    lines.append(f"| Wiring Tasks | {len(report.wiring_tasks)} | - |")
    lines.append(f"| Missing Items | {len(report.missing_items)} | {'🔴 GAPS FOUND' if report.missing_items else '🟢 COMPLETE'} |")
    lines.append("")

    # Section 2: Service Consolidation Analysis (v9 — NEW)
    lines.append("## 2. Service Consolidation Analysis (v9)")
    lines.append("")
    lines.append(f"**Total services: {sc.total_services}** → Target: **{sc.consolidation_target}**")
    lines.append("")
    lines.append(f"| Tier | Label | Count | Action | Risk |")
    lines.append(f"|------|-------|-------|--------|------|")
    lines.append(f"| Tier 0 | Safe deletes (junk/empty) | {len(sc.tier0_safe_deletes)} | DELETE | LOW |")
    lines.append(f"| Tier 1 | Exact content duplicates | {len(sc.tier1_exact_duplicates)} | MERGE | LOW |")
    lines.append(f"| Tier 2 | Naming variants / sprawl | {len(sc.tier2_naming_variants)} | RENAME | MEDIUM |")
    lines.append(f"| Tier 3 | Read/Write split sprawl | {len(sc.tier3_read_write_split)} | STANDARDIZE | MEDIUM |")
    lines.append(f"| Tier 4 | Thin forwarding services | {len(sc.tier4_thin_forwarders)} | MERGE | MEDIUM |")
    lines.append(f"| Tier 5 | Structural near-duplicates | {len(sc.tier5_structural_dups)} | REVIEW | HIGH |")
    lines.append("")
    lines.append(f"**Safe immediate reduction:** {sc.safe_immediate_reduction} files (Tier 0 + Tier 1)")
    lines.append(f"**Realistic consolidation target:** {sc.realistic_target} files")
    lines.append("")

    # Tier 0 details
    if sc.tier0_safe_deletes:
        lines.append(f"### 2.1 Tier 0 — Safe Deletes ({len(sc.tier0_safe_deletes)} files)")
        lines.append("")
        lines.append("| # | File | Reason | Action | Risk | Recommendation |")
        lines.append("|---|------|--------|--------|------|----------------|")
        for i, f in enumerate(sc.tier0_safe_deletes, 1):
            lines.append(f"| {i} | `{f.file_a}` | {f.reason} | {f.action} | {f.risk} | {f.recommendation} |")
        lines.append("")

    # Tier 1 details
    if sc.tier1_exact_duplicates:
        lines.append(f"### 2.2 Tier 1 — Exact Content Duplicates ({len(sc.tier1_exact_duplicates)} pairs)")
        lines.append("")
        lines.append("| # | File A | File B | Note | Action | Risk | Recommendation |")
        lines.append("|---|--------|--------|------|--------|------|----------------|")
        for i, f in enumerate(sc.tier1_exact_duplicates, 1):
            note = f"importers: {', '.join(f.import_impact[:3])}" if f.import_impact else "0 importers"
            lines.append(f"| {i} | `{f.file_a}` | `{f.file_b}` | {note} | {f.action} | {f.risk} | {f.recommendation} |")
        lines.append("")

    # Tier 2 details
    if sc.tier2_naming_variants:
        lines.append(f"### 2.3 Tier 2 — Naming Variants / Domain Sprawl ({len(sc.tier2_naming_variants)} files)")
        lines.append("")
        lines.append("| # | File | Reason | Action | Risk | Recommendation |")
        lines.append("|---|------|--------|--------|------|----------------|")
        for i, f in enumerate(sc.tier2_naming_variants, 1):
            lines.append(f"| {i} | `{f.file_a}` | {f.reason} | {f.action} | {f.risk} | {f.recommendation} |")
        lines.append("")

    # Tier 3 details
    if sc.tier3_read_write_split:
        lines.append(f"### 2.4 Tier 3 — Read/Write Split Sprawl ({len(sc.tier3_read_write_split)} files)")
        lines.append("")
        lines.append("| # | File | Type | Reason | Action | Risk | Recommendation |")
        lines.append("|---|------|------|--------|--------|------|----------------|")
        for i, f in enumerate(sc.tier3_read_write_split, 1):
            lines.append(f"| {i} | `{f.file_a}` | {f.tier_label} | {f.reason} | {f.action} | {f.risk} | {f.recommendation} |")
        lines.append("")

    # Tier 4 details
    if sc.tier4_thin_forwarders:
        lines.append(f"### 2.5 Tier 4 — Thin Forwarding Services ({len(sc.tier4_thin_forwarders)} files)")
        lines.append("")
        lines.append("| # | File | Forwards To | Action | Risk | Recommendation |")
        lines.append("|---|------|-------------|--------|------|----------------|")
        for i, f in enumerate(sc.tier4_thin_forwarders, 1):
            lines.append(f"| {i} | `{f.file_a}` | {f.reason} | {f.action} | {f.risk} | {f.recommendation} |")
        lines.append("")

    # Tier 5 details
    if sc.tier5_structural_dups:
        lines.append(f"### 2.6 Tier 5 — Structural Near-Duplicates ({len(sc.tier5_structural_dups)} pairs)")
        lines.append("")
        lines.append("| # | File A | File B | Similarity | Note | Action | Risk | Recommendation |")
        lines.append("|---|--------|--------|------------|------|--------|------|----------------|")
        for i, f in enumerate(sc.tier5_structural_dups[:50], 1):
            note = f"importers: {', '.join(f.import_impact[:3])}" if f.import_impact else ""
            lines.append(
                f"| {i} | `{f.file_a}` | `{f.file_b}` | "
                f"{f.similarity:.0%} | {note} | {f.action} | {f.risk} | {f.recommendation} |"
            )
        if len(sc.tier5_structural_dups) > 50:
            lines.append(f"| ... | ... | ... | ... | ... | ... | +{len(sc.tier5_structural_dups) - 50} more |")
        lines.append("")

    # Section 3: Duplicate Logic Findings (cross-file, all layers)
    lines.append("## 3. Duplicate Logic Findings (Cross-File)")
    lines.append("")

    if report.identical_findings:
        lines.append(f"### 3.1 True Duplicates (IDENTICAL) — {len(report.identical_findings)} found")
        lines.append("")
        lines.append("| # | File A | Function A | File B | Function B | Action |")
        lines.append("|---|--------|-----------|--------|-----------|--------|")
        for i, d in enumerate(report.identical_findings[:100], 1):
            lines.append(
                f"| {i} | `{d.source_file}` | `{d.source_function}` | "
                f"`{d.existing_file}` | `{d.existing_function}` | "
                f"Keep ONE, delete the other |"
            )
        if len(report.identical_findings) > 100:
            lines.append(f"| ... | ... | ... | ... | ... | +{len(report.identical_findings) - 100} more |")
        lines.append("")
    else:
        lines.append("### 3.1 True Duplicates (IDENTICAL)")
        lines.append("")
        lines.append("✅ No true identical duplicates detected.")
        lines.append("")

    if report.structural_findings:
        lines.append(f"### 3.2 Structural Similarity — {len(report.structural_findings)} found")
        lines.append("")
        lines.append("> ⚠️ **These are NOT exact duplicates.** They share the same operation")
        lines.append("> sequence but are different functions. Review before consolidating.")
        lines.append("")
        lines.append("| # | File A | Function A | File B | Function B | Action |")
        lines.append("|---|--------|-----------|--------|-----------|--------|")
        for i, d in enumerate(report.structural_findings[:MAX_STRUCTURAL_REPORT], 1):
            lines.append(
                f"| {i} | `{d.source_file}` | `{d.source_function}` | "
                f"`{d.existing_file}` | `{d.existing_function}` | "
                f"Review — NOT identical |"
            )
        if len(report.structural_findings) > MAX_STRUCTURAL_REPORT:
            lines.append(f"| ... | ... | ... | ... | ... | +{len(report.structural_findings) - MAX_STRUCTURAL_REPORT} more |")
        lines.append("")
    else:
        lines.append("### 3.2 Structural Similarity")
        lines.append("")
        lines.append("✅ No structural similarity matches detected.")
        lines.append("")

    if report.advisory_overlaps:
        lines.append(f"### 3.3 Advisory Overlaps (MODEL_OPS) — {len(report.advisory_overlaps)} found")
        lines.append("")
        lines.append("> ⚠️ **Heuristic overlaps, not precise defect counts.**")
        lines.append("")
        lines.append("| # | File A | File B | Shared Ops | Overlap % | Sample |")
        lines.append("|---|--------|--------|-----------|----------|--------|")
        for i, d in enumerate(report.advisory_overlaps[:50], 1):
            ops_str = ", ".join(d.db_operations[:3]) if d.db_operations else "-"
            lines.append(
                f"| {i} | `{d.source_file}` | `{d.existing_file}` | "
                f"{len(d.db_operations)} | {d.similarity:.0%} | {ops_str} |"
            )
        if len(report.advisory_overlaps) > 50:
            lines.append(f"| ... | ... | ... | ... | ... | +{len(report.advisory_overlaps) - 50} more |")
        lines.append("")
    else:
        lines.append("### 3.3 Advisory Overlaps (MODEL_OPS)")
        lines.append("")
        lines.append("✅ No advisory overlaps detected.")
        lines.append("")

    already_exists = [t for t in report.migration_tasks if t.resolution == "ALREADY_EXISTS"]
    partial_dups = [t for t in report.migration_tasks if t.resolution == "PARTIAL_DUPLICATE"]

    if already_exists:
        lines.append(f"### 3.4 Migration Tasks SKIPPED (similar logic exists) — {len(already_exists)}")
        lines.append("")
        lines.append("| # | Router (Source) | Similar Logic In | Function | Confidence | Action |")
        lines.append("|---|----------------|-----------------|----------|------------|--------|")
        for i, t in enumerate(already_exists, 1):
            lines.append(
                f"| {i} | `{t.source_file}` | `{t.already_exists_in}` | "
                f"`{t.duplicate_function}()` | {t.duplicate_confidence:.0%} | "
                f"Wire router to existing function |"
            )
        lines.append("")

    if partial_dups:
        lines.append(f"### 3.5 Migration Tasks Needing REVIEW — {len(partial_dups)}")
        lines.append("")
        lines.append("| # | Router (Source) | Similar Logic In | Function | Confidence | Action |")
        lines.append("|---|----------------|-----------------|----------|------------|--------|")
        for i, t in enumerate(partial_dups, 1):
            lines.append(
                f"| {i} | `{t.source_file}` | `{t.already_exists_in}` | "
                f"`{t.duplicate_function}()` | {t.duplicate_confidence:.0%} | "
                f"Review & consolidate |"
            )
        lines.append("")

    # Section 4: Business Logic Migration Plan
    lines.append("## 4. Business Logic Migration Plan (Routers → Controllers & Services)")
    lines.append("")
    lines.append("### 4.1 Summary")
    lines.append("")
    lines.append(f"**{report.routers_with_business_logic} routers** contain business logic.")
    lines.append(f"> ⚠️ Count derived from scoped AST + regex analysis (no false positives from ast.dump).")
    lines.append("")

    high_priority = [t for t in report.migration_tasks if t.priority == "HIGH" and t.resolution == "MIGRATE"]
    medium_priority = [t for t in report.migration_tasks if t.priority == "MEDIUM" and t.resolution == "MIGRATE"]

    lines.append(f"- ✅ **Actual migrations needed:** {len(high_priority) + len(medium_priority)}")
    lines.append(f"  - 🔴 HIGH priority (DB writes): {len(high_priority)}")
    lines.append(f"  - 🟡 MEDIUM priority (queries/logic): {len(medium_priority)}")
    lines.append(f"- ⏭️ **Skipped (similar logic exists):** {report.duplicates_skipped}")
    lines.append(f"- ⚠️ **Needs review (partial overlap):** {report.partial_duplicates}")
    lines.append("")

    lines.append("### 4.2 File-to-File Migration Plan")
    lines.append("")
    lines.append("| # | Source (Router) | Target | Logic Type | Lines | Resolution | Priority | Status |")
    lines.append("|---|----------------|--------|------------|-------|------------|----------|--------|")

    for i, task in enumerate(report.migration_tasks, 1):
        res_icon = {"MIGRATE": "✅", "ALREADY_EXISTS": "⏭️", "PARTIAL_DUPLICATE": "⚠️"}.get(task.resolution, "?")
        lines.append(
            f"| {i} | `{task.source_file}` | `{task.target_file}` | "
            f"{task.logic_type} | {len(task.line_numbers)} | "
            f"{res_icon} {task.resolution} | "
            f"{'🔴' if task.priority == 'HIGH' else '🟡'} {task.priority} | {task.status} |"
        )
    lines.append("")

    # Section 5: Controller Decorator Readiness
    lines.append("## 5. Controller Decorator Readiness for Auto-Generating Routers")
    lines.append("")
    lines.append(f"**Decorators used:** `{decorator_label}`")
    lines.append("")
    lines.append("### 5.1 Ready Controllers (have route decorators)")
    lines.append("")
    if report.ready_controllers:
        lines.append("| # | Controller File | Decorators Used | Status |")
        lines.append("|---|----------------|----------------|--------|")
        for i, ctrl_path in enumerate(report.ready_controllers, 1):
            ctrl_info = report.file_infos.get(ctrl_path)
            dec_names = ", ".join(f"@{d}" for d in ctrl_info.decorator_names_used) if ctrl_info and ctrl_info.decorator_names_used else decorator_label
            lines.append(f"| {i} | `{ctrl_path}` | {dec_names} | ✅ READY |")
    else:
        lines.append("⚠️ **No controllers have route decorators yet.**")
    lines.append("")

    lines.append("### 5.2 Controllers Needing Route Decorators")
    lines.append("")
    lines.append(f"**{len(report.not_ready_controllers)} controllers** need route decorators.")
    lines.append("")
    lines.append(
        f"> ℹ️ {len(report.adapter_controllers)} adapter modules (re-export shims, "
        f"auto-generated delegators, `__getattr__` lazy-reexport hooks, and FastAPI "
        f"`Depends` provider modules) are **excluded** — they have no route-handler "
        f"functions, so they cannot/should not receive route decorators, and their "
        f"endpoints are already served by the existing hand-written routers."
    )
    lines.append("")
    if report.not_ready_controllers:
        lines.append("| # | Controller File | Functions to Decorate | Status |")
        lines.append("|---|----------------|----------------------|--------|")
        for i, ctrl_path in enumerate(report.not_ready_controllers, 1):
            ctrl_info = report.file_infos.get(ctrl_path)
            func_count = len(ctrl_info.undecorated_functions) if ctrl_info else "?"
            lines.append(f"| {i} | `{ctrl_path}` | {func_count} functions | 🔴 NEEDS DECORATORS |")
    lines.append("")

    # Section 6: Wiring Completeness
    lines.append("## 6. Model ↔ Service ↔ Controller Wiring Plan")
    lines.append("")
    lines.append("> ⚠️ Wiring completeness is based on name-similarity matching (heuristic).")
    lines.append("")
    complete_wiring = [w for w in report.wiring_tasks if w.status == "COMPLETE"]
    incomplete_wiring = [w for w in report.wiring_tasks if w.status == "INCOMPLETE"]
    lines.append(f"- ✅ **Complete wiring:** {len(complete_wiring)}")
    lines.append(f"- 🔴 **Incomplete wiring:** {len(incomplete_wiring)}")
    lines.append("")
    lines.append("| # | Model | Service | Controller | Router | Status | Missing |")
    lines.append("|---|-------|---------|------------|--------|--------|---------|")
    for i, task in enumerate(report.wiring_tasks, 1):
        status_icon = "✅" if task.status == "COMPLETE" else "🔴"
        missing_str = ", ".join(task.missing_pieces[:2]) if task.missing_pieces else "-"
        lines.append(
            f"| {i} | `{task.model_file}` | `{task.service_file}` | "
            f"`{task.controller_file}` | `{task.router_file}` | "
            f"{status_icon} {task.status} | {missing_str} |"
        )
    lines.append("")

    # Section 7: Missing Files and Folders
    lines.append("## 7. Missing Files and Folders")
    lines.append("")
    lines.append("> ✅ All paths verified against live tree within scan window.")
    lines.append("")
    if report.missing_items:
        lines.append("| # | Type | Path | Reason | Priority |")
        lines.append("|---|------|------|--------|----------|")
        for i, item in enumerate(report.missing_items, 1):
            icon = "📁" if item.item_type == "folder" else "📄"
            lines.append(
                f"| {i} | {icon} {item.item_type} | `{item.path}` | "
                f"{item.reason} | {'🔴' if item.priority == 'HIGH' else '🟡'} {item.priority} |"
            )
    else:
        lines.append("✅ No missing files or folders detected.")
    lines.append("")

    # Section 8: Recommended Actions
    lines.append("## 8. Recommended Actions (Priority Order)")
    lines.append("")
    lines.append("### Phase 0: Safe Service Cleanup (Do This First — Zero Risk)")
    lines.append(f"1. Delete Tier 0 junk files: {len(sc.tier0_safe_deletes)} files")
    lines.append(f"2. Merge Tier 1 exact duplicates: {len(sc.tier1_exact_duplicates)} pairs")
    lines.append(f"3. **Immediate safe reduction: {sc.safe_immediate_reduction} files**")
    lines.append("")
    lines.append("### Phase 1: Service Consolidation (This Week)")
    lines.append(f"1. Rename Tier 2 naming variants: {len(sc.tier2_naming_variants)} files")
    lines.append(f"2. Merge Tier 4 thin forwarders: {len(sc.tier4_thin_forwarders)} files")
    lines.append(f"3. Review Tier 5 structural duplicates: {len(sc.tier5_structural_dups)} pairs")
    lines.append(f"4. **Realistic consolidation target: {sc.realistic_target} files**")
    lines.append("")
    lines.append("### Phase 2: Read/Write Standardization (This Sprint)")
    lines.append(f"1. Standardize Tier 3 read/write split: {len(sc.tier3_read_write_split)} files")
    lines.append("2. Define one naming rule: `{domain}_{entity}_service.py` (no read/write suffix)")
    lines.append("3. Rewire callers to use consolidated services")
    lines.append("")
    lines.append("### Phase 3: Router Migration (This Sprint)")
    lines.append("1. Migrate all DB writes from routers to services (HIGH priority MIGRATE tasks only)")
    lines.append("2. For ALREADY_EXISTS tasks: wire router to the existing service function")
    lines.append("3. Migrate all DB queries from routers to services")
    lines.append("")
    lines.append("### Phase 4: Auto-Generation (This Month)")
    lines.append("1. Add route decorators to all controller functions")
    lines.append("2. Run auto-generation script to regenerate all routers")
    lines.append("3. Validate all generated routers against architecture contract")
    lines.append("4. Add CI test asserting route count baseline")
    lines.append("5. Remove hand-written routers that are now auto-generated")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Report generated by ZOZI Architecture Audit Script v9 (Service Consolidation)*")
    lines.append(f"*Scan window: {report.scan_start_time} → {report.scan_end_time} ({report.scan_duration_ms:.0f} ms)*")
    lines.append("*Architecture contract: ARCHITECTURE_DIAGRAM.md §10*")
    lines.append(f"*Total findings: {len(report.migration_tasks)} migrations "
                 f"({report.duplicates_skipped} skipped, "
                 f"{report.partial_duplicates} partial, "
                 f"{report.actual_migrations_needed} actual), "
                 f"{len(report.wiring_tasks)} wiring tasks, "
                 f"{len(report.missing_items)} missing items, "
                 f"{len(report.identical_findings)} true duplicates, "
                 f"{len(report.structural_findings)} structural matches, "
                 f"{len(report.advisory_overlaps)} advisory overlaps, "
                 f"{len(sc.tier0_safe_deletes)} safe deletes, "
                 f"{len(sc.tier1_exact_duplicates)} exact dups, "
                 f"{len(sc.tier2_naming_variants)} naming variants, "
                 f"{len(sc.tier3_read_write_split)} read/write splits, "
                 f"{len(sc.tier4_thin_forwarders)} thin forwarders, "
                 f"{len(sc.tier5_structural_dups)} structural dups*")

    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# §10 — CLI ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Force UTF-8 on std streams for Windows
    for _stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(_stream, "reconfigure"):
                _stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass

    import argparse
    parser = argparse.ArgumentParser(
        description="ZOZI Architecture Audit & Migration Tracker (v9 — Service Consolidation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python audit_migration_tracker.py              # Full audit + report
    python audit_migration_tracker.py --json       # Output as JSON
    python audit_migration_tracker.py --summary    # Summary only
    python audit_migration_tracker.py --strict     # Exit code 2 if drift persists
        """,
    )
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    parser.add_argument("--summary", action="store_true", help="Print summary only")
    parser.add_argument("--strict", action="store_true",
                        help="Exit with code 2 if file drift persists after max rescans")
    args = parser.parse_args()

    report = run_full_audit(strict=args.strict)

    if args.json:
        sc = report.service_consolidation
        output = {
            "timestamp": report.timestamp,
            "version": "v9",
            "scan_window": {
                "start": report.scan_start_time,
                "end": report.scan_end_time,
                "duration_ms": report.scan_duration_ms,
                "attempts": report.scan_attempts,
                "consistent": report.scan_consistent,
                "files_pre": report.file_count_pre,
                "files_post": report.file_count_post,
            },
            "totals": {
                "routers": report.total_routers,
                "controllers": report.total_controllers,
                "services": report.total_services,
                "models": report.total_models,
                "routers_with_business_logic": report.routers_with_business_logic,
                "controllers_with_decorators": report.controllers_with_decorators,
                "controllers_without_decorators": report.controllers_without_decorators,
                "adapter_controllers": len(report.adapter_controllers),
            },
            "service_consolidation": {
                "total_services": sc.total_services,
                "size_distribution": sc.size_distribution,
                "tier0_safe_deletes": len(sc.tier0_safe_deletes),
                "tier1_exact_duplicates": len(sc.tier1_exact_duplicates),
                "tier2_naming_variants": len(sc.tier2_naming_variants),
                "tier3_read_write_split": len(sc.tier3_read_write_split),
                "tier4_thin_forwarders": len(sc.tier4_thin_forwarders),
                "tier5_structural_dups": len(sc.tier5_structural_dups),
                "safe_immediate_reduction": sc.safe_immediate_reduction,
                "realistic_target": sc.realistic_target,
                "consolidation_target": sc.consolidation_target,
            },
            "migration_summary": {
                "total_tasks": len(report.migration_tasks),
                "already_exists_skipped": report.duplicates_skipped,
                "partial_duplicates": report.partial_duplicates,
                "actual_migrations_needed": report.actual_migrations_needed,
            },
            "duplicates": {
                "true_duplicates_identical": len(report.identical_findings),
                "structural_similarity": len(report.structural_findings),
                "advisory_overlaps_heuristic": len(report.advisory_overlaps),
            },
            "wiring_tasks": len(report.wiring_tasks),
            "missing_items": len(report.missing_items),
            "ready_controllers": report.ready_controllers,
            "not_ready_controllers": report.not_ready_controllers,
        }
        print(json.dumps(output, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())