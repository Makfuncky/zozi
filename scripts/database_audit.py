# ./scripts/database_audit.py
"""
database_audit.py — ZOZI Database Governance Auditor.

Purpose:
  Read-only database governance auditor for ZOZI.
  Validates database architecture from development to production against
  documents/scope/01_DATABASE.md.

It checks:
  1.  Bounded-context schemas / ecosystem ownership.
  2.  ORM model placement.
  3.  Mandatory column set / mixins.
  4.  Naming conventions.
  5.  Foreign-key discipline.
  6.  Cross-ecosystem FK violations.
  7.  Cascade rules.
  8.  Missing FK indexes.
  9.  JSONB / GIN index discipline.
  10. Media bytes stored in DB.
  11. Alembic migration governance.
  12. Migration heads / ORM-only table drift.
  13. Downgrade safety.
  14. Dev/prod create_all gating.
  15. SQLite production risk.
  16. Connection pool configuration.
  17. Row-Level Security coverage.
  18. Event outbox tables.
  19. Audit log taxonomy.
  20. Analytics snapshot discipline.
  21. Finance ledger immutability.
  22. AI staging discipline.
  23. Config-as-data discipline.
  24. Partition strategy signals.
  25. Production checklist.
  26. Optional live PostgreSQL read-only checks.

Design:
  * READ-ONLY.
  * Does NOT import application code.
  * Static analysis by default.
  * Optional live DB checks only when explicitly requested.
  * Self-contained: no YAML required.

Severity:
  [RED] VIOLATION
  [YEL] ADVISORY
  [GRN] INFO

Usage:
  python scripts/database_audit.py
  python scripts/database_audit.py --no-fail
  python scripts/database_audit.py --json out/database_audit.json
  python scripts/database_audit.py --ci
  python scripts/database_audit.py --live-env
  python scripts/database_audit.py --live-dsn postgresql+psycopg2://user:pass@host:5432/zozi

Exit:
  1 if RED findings exist, unless --no-fail is passed.
"""

from __future__ import annotations

import argparse
import ast
import datetime
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


# ============================================================================
# 1. CONSTANTS
# ============================================================================

RED, YEL, GRN = "VIOLATION", "ADVISORY", "INFO"

SEV_ICON = {
    RED: "🔴",
    YEL: "🟡",
    GRN: "🟢",
}

IGNORE_DIRS = {
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

EXPECTED_SCHEMAS = {
    "core",
    "commerce",
    "supplier",
    "customer",
    "logistics",
    "finance",
    "treasury",
    "hr",
    "country",
    "media",
    "ai",
    "communication",
    "audit",
    "security",
    "analytics",
    "configuration",
}

EXPECTED_EXTENSIONS = {
    "vector",
    "pgcrypto",
    "citext",
    "btree_gin",
    "pg_trgm",
    "uuid-ossp",
}

EXPECTED_EVENT_TABLES = {
    "outbox_events",
    "inbox_events",
    "event_retry_queue",
    "event_dead_letter",
}

EXPECTED_AI_TABLES = {
    "ai_requests",
    "ai_results",
    "ai_embeddings",
    "ai_upload_jobs",
    "ai_staging_products",
    "upload_jobs",
}

PARTITION_EXPECTED_TABLES = {
    "journal_entries",
    "audit_logs",
    "chat_messages",
    "shipment_events",
}

FINANCE_PROTECTED_TABLES = {
    "journal_entries",
    "journal_entry_lines",
    "ap_ledger_entries",
    "ar_ledger_entries",
    "ledger_entries",
    "accounts",
    "payouts",
}

INTEGER_TYPES = {
    "INTEGER",
    "INT",
    "BIGINTEGER",
    "SMALLINTEGER",
}

BINARY_TYPES = {
    "LARGEBINARY",
    "BLOB",
    "BYTEA",
    "IMAGE",
}

JSON_TYPES = {
    "JSON",
    "JSONB",
}

DATETIME_TYPES = {
    "DATETIME",
    "TIMESTAMP",
    "DATE",
    "TIME",
}

TABLE_SINGULAR_ALLOW = {
    "alembic_version",
    "audit",
    "worm_audit",
    "metadata",
    "data",
}

SURFACE_NAMES = {
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

DOMAIN_KEYWORDS = {
    "core": {
        "user",
        "users",
        "role",
        "roles",
        "session",
        "sessions",
        "device",
        "devices",
        "auth",
        "identity",
        "permission",
        "permissions",
    },
    "commerce": {
        "product",
        "products",
        "variant",
        "variants",
        "category",
        "categories",
        "cart",
        "carts",
        "order",
        "orders",
        "checkout",
        "commerce",
    },
    "supplier": {
        "supplier",
        "suppliers",
        "vendor",
        "vendors",
        "onboarding",
    },
    "customer": {
        "customer",
        "customers",
        "address",
        "addresses",
        "wishlist",
        "wishlists",
        "point",
        "points",
    },
    "logistics": {
        "logistics",
        "shipment",
        "shipments",
        "fleet",
        "route",
        "routes",
        "pod",
        "delivery",
        "carrier",
    },
    "finance": {
        "finance",
        "account",
        "accounts",
        "journal",
        "ledger",
        "ap",
        "ar",
        "invoice",
        "invoices",
        "commission",
        "tax",
    },
    "treasury": {
        "treasury",
        "cash",
        "bank",
        "reconciliation",
        "payout",
        "payouts",
    },
    "hr": {
        "employee",
        "employees",
        "attendance",
        "shift",
        "shifts",
        "leave",
        "coi",
    },
    "country": {
        "country",
        "countries",
        "city",
        "cities",
    },
    "media": {
        "media",
        "asset",
        "assets",
        "image",
        "images",
        "video",
        "videos",
    },
    "ai": {
        "ai",
        "embedding",
        "embeddings",
        "request",
        "requests",
        "result",
        "results",
        "job",
        "jobs",
        "staging",
    },
    "communication": {
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
    },
    "audit": {
        "audit",
        "worm",
        "permission_audit",
    },
    "security": {
        "security",
        "api_key",
        "api_keys",
        "fraud",
        "risk",
        "blacklist",
        "mfa",
        "otp",
    },
    "analytics": {
        "analytics",
        "snapshot",
        "snapshots",
        "kpi",
        "mv",
    },
    "configuration": {
        "config",
        "configuration",
        "setting",
        "settings",
        "feature_flag",
        "toggle",
    },
}

RULE_MEANING = {
    "DB01": "bounded-context schema missing or unknown",
    "DB02": "Base.metadata.create_all not safely dev-gated",
    "DB03": "mandatory column set / mixin missing",
    "DB04": "country_code width mismatch",
    "DB05": "RLS coverage missing or weak",
    "DB06": "cross-ecosystem foreign key detected",
    "DB07": "unsafe or missing FK cascade rule",
    "DB08": "FK column missing index",
    "DB09": "JSONB column missing GIN index signal",
    "DB10": "file bytes stored in database",
    "DB11": "database naming convention violation",
    "DB12": "migration governance missing or unsafe",
    "DB13": "migration head / ORM-only table drift",
    "DB14": "dev/prod database gate missing or weak",
    "DB15": "connection pool configuration mismatch",
    "DB16": "SQLite production risk",
    "DB17": "event outbox tables missing",
    "DB18": "audit log taxonomy missing or fragmented",
    "DB19": "analytics snapshot discipline missing / live aggregate risk",
    "DB20": "finance ledger immutability risk",
    "DB21": "AI staging discipline missing or direct commit risk",
    "DB22": "hardcoded business config constant",
    "DB23": "partition strategy missing for hot append-only tables",
    "DB24": "production checklist gap",
    "DB25": "live database drift / live check result",
    "DB26": "ORM model outside backend/models/",
}

HOTLIST_RULES = {
    "DB02",
    "DB05",
    "DB06",
    "DB10",
    "DB13",
    "DB14",
    "DB16",
    "DB20",
    "DB25",
    "DB26",
}

# ============================================================================
# v2 CONSTITUTION ENHANCEMENTS
# ============================================================================

RULE_MEANING.update({
    "DB27": "broken or suspicious migration file (ADR-018 risk)",
    "DB28": "migration contract-test harness missing",
    "DB29": "required canonical table missing",
    "DB30": "required analytics snapshot table missing",
    "DB31": "required composite index signal missing",
    "DB32": "unsafe pagination/query pattern (OFFSET in request path)",
    "DB33": "finance write outside ledger service boundary",
    "DB34": "RLS fail-closed signal missing",
    "DB35": "idempotency/webhook dedupe table missing",
    "DB36": "archive/retention signal missing",
    "DB37": "data dictionary generator missing ERD/Mermaid output",
    "DBT1": "database audit trend delta",
})

HOTLIST_RULES.update({
    "DB27",
    "DB28",
    "DB29",
    "DB30",
    "DB31",
    "DB32",
    "DB33",
    "DB34",
    "DB35",
    "DB36",
    "DB37",
})

REQUIRED_CANONICAL_TABLES = {
    "media_assets",
    "worm_audit",
    "processed_webhook_events",
    "commission_rules",
    "country_configs",
    "feature_flags",
}

REQUIRED_SNAPSHOT_TABLES = {
    "mv_daily_sales",
    "mv_monthly_sales",
    "kpi_customer",
    "kpi_supplier",
    "kpi_country",
    "kpi_revenue",
    "kpi_orders",
    "kpi_retention",
    "kpi_conversion",
    "mv_cash_position",
    "mv_facet_counts",
}

EXPECTED_PARTITION_TABLES = {
    "journal_entries",
    "audit_logs",
    "chat_messages",
    "shipment_events",
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
class ColumnInfo:
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
class ModelInfo:
    name: str
    file: Path
    rel_path: str
    line: int
    table: str | None
    schema: str | None
    domain: str
    bases: list[str]
    columns: list[ColumnInfo]
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
class MigrationInfo:
    alembic_dir_exists: bool = False
    env_exists: bool = False
    ini_exists: bool = False
    versions_dir_exists: bool = False
    files: list[Path] = field(default_factory=list)
    revisions: dict[str, str | None] = field(default_factory=dict)
    heads: list[str] = field(default_factory=list)
    multiple_heads: bool = False
    tables_created: set[str] = field(default_factory=set)
    has_partition: bool = False
    downgrade_missing: list[str] = field(default_factory=list)
    stubs: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class RLSInfo:
    sql_files: list[Path] = field(default_factory=list)
    rls_tables: set[str] = field(default_factory=set)
    interceptor_files: list[str] = field(default_factory=list)
    sets_context: bool = False


# ============================================================================
# 3. GENERIC HELPERS
# ============================================================================


def rel(p: Path, base: Path) -> str:
    try:
        return str(p.relative_to(base))
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
            if e.is_dir() and e.name.lower() not in IGNORE_DIRS:
                stack.append(e)


def iter_python_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return

    for d, entries in walk_dirs(root):
        for e in entries:
            if e.is_file() and e.suffix.lower() == ".py":
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


def _unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""

    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _func_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id

    if isinstance(func, ast.Attribute):
        return func.attr

    return ""


def _dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    cur = node

    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value

    if isinstance(cur, ast.Name):
        parts.append(cur.id)

    return ".".join(reversed(parts))


def _annotation_type(annotation: ast.AST | None) -> str:
    if annotation is None:
        return ""

    s = _unparse(annotation).lower()

    if "int" in s:
        return "INTEGER"

    if "str" in s:
        return "STRING"

    if "bool" in s:
        return "BOOLEAN"

    if "datetime" in s:
        return "DATETIME"

    if "date" in s:
        return "DATE"

    if "uuid" in s:
        return "UUID"

    if "dict" in s or "json" in s:
        return "JSON"

    if "decimal" in s or "float" in s:
        return "NUMERIC"

    if "bytes" in s:
        return "BINARY"

    return ""


def _extract_table_args(value: ast.AST) -> tuple[str | None, str]:
    text = _unparse(value)
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
            if (
                isinstance(k, ast.Constant)
                and k.value == "schema"
                and isinstance(v, ast.Constant)
            ):
                schema = str(v.value)

    return schema, text


def _extract_column(
    name: str,
    call: ast.Call,
    line: int,
    annotation: ast.AST | None = None,
) -> ColumnInfo:
    type_name = ""
    type_args = ""

    if call.args:
        first = call.args[0]

        if isinstance(first, ast.Call):
            type_name = _func_name(first.func)

            if first.args:
                args: list[str] = []
                for a in first.args:
                    if isinstance(a, ast.Constant):
                        args.append(str(a.value))
                type_args = ",".join(args)

        elif isinstance(first, (ast.Name, ast.Attribute)):
            type_name = _dotted_name(first).split(".")[-1]

    if type_name.upper() == "FOREIGNKEY":
        type_name = ""

    if not type_name and annotation is not None:
        type_name = _annotation_type(annotation)

    is_pk = False
    is_index = False
    is_unique = False
    nullable = None
    fk_target = None
    fk_ondelete = None

    for kw in call.keywords:
        if kw.arg == "primary_key":
            if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                is_pk = True

        if kw.arg == "index":
            if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                is_index = True

        if kw.arg == "unique":
            if isinstance(kw.value, ast.Constant) and kw.value.value is True:
                is_unique = True

        if kw.arg == "nullable":
            if isinstance(kw.value, ast.Constant):
                nullable = bool(kw.value.value)

    for arg in call.args:
        if isinstance(arg, ast.Call) and _func_name(arg.func).endswith("ForeignKey"):
            if arg.args and isinstance(arg.args[0], ast.Constant):
                fk_target = str(arg.args[0].value)

            for kw in arg.keywords:
                if kw.arg == "ondelete" and isinstance(kw.value, ast.Constant):
                    fk_ondelete = str(kw.value.value)

    return ColumnInfo(
        name=name,
        line=line,
        type_name=type_name,
        type_args=type_args,
        is_pk=is_pk,
        is_index=is_index,
        is_unique=is_unique,
        nullable=nullable,
        fk_target=fk_target,
        fk_ondelete=fk_ondelete,
        raw=_unparse(call),
    )


def infer_domain(
    backend: Path,
    f: Path,
    schema: str | None,
    table: str | None,
) -> str:
    if schema:
        return schema.lower()

    try:
        parts = [p.lower() for p in f.relative_to(backend).parts]
    except ValueError:
        parts = []

    if len(parts) >= 3 and parts[0] == "models":
        candidate = parts[1]
        if candidate not in SURFACE_NAMES and candidate not in IGNORE_DIRS:
            return candidate

    text = f.stem.lower() + " " + (table or "")
    tokens = {t for t in re.split(r"[-_.\s]+", text) if t}

    for dom, keywords in DOMAIN_KEYWORDS.items():
        if tokens & keywords:
            return dom

    return "_triage"


# ============================================================================
# 4. MODEL PARSER
# ============================================================================


def parse_models(repo: Path) -> list[ModelInfo]:
    models: list[ModelInfo] = []
    backend = repo / "backend"

    if not backend.exists():
        return models

    for f in iter_python_files(backend):
        tree = parse_safe(f)
        if tree is None:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue

            table = None
            schema = None
            table_args_text = ""
            columns: list[ColumnInfo] = []
            bases: list[str] = []

            for base in node.bases:
                nm = _dotted_name(base) or _unparse(base)
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
                            schema, table_args_text = _extract_table_args(stmt.value)

                        elif isinstance(stmt.value, ast.Call):
                            fname = _func_name(stmt.value.func)
                            if fname in {"Column", "mapped_column"}:
                                columns.append(
                                    _extract_column(
                                        target.id,
                                        stmt.value,
                                        stmt.lineno,
                                    )
                                )

                elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if isinstance(stmt.value, ast.Call):
                        fname = _func_name(stmt.value.func)
                        if fname in {"Column", "mapped_column"}:
                            columns.append(
                                _extract_column(
                                    stmt.target.id,
                                    stmt.value,
                                    stmt.lineno,
                                    stmt.annotation,
                                )
                            )

            if not table:
                continue

            mixin_names = {b.split(".")[-1] for b in bases if "Mixin" in b}
            colnames = {c.name.lower() for c in columns}

            has_pk = any(c.is_pk for c in columns) or ("id" in colnames)

            has_uuid = "uuid" in colnames or any(
                c.type_name.upper() == "UUID" for c in columns
            )

            has_country_code = (
                "country_code" in colnames or "TenantMixin" in mixin_names
            )

            has_created_at = (
                "created_at" in colnames
                or "AuditMixin" in mixin_names
                or "TimestampMixin" in mixin_names
            )

            has_updated_at = (
                "updated_at" in colnames
                or "AuditMixin" in mixin_names
                or "TimestampMixin" in mixin_names
            )

            has_is_deleted = (
                "is_deleted" in colnames or "SoftDeleteMixin" in mixin_names
            )

            has_deleted_at = (
                "deleted_at" in colnames or "SoftDeleteMixin" in mixin_names
            )

            has_version = "version" in colnames

            has_created_by = (
                "created_by" in colnames or "AuditMixin" in mixin_names
            )

            has_updated_by = (
                "updated_by" in colnames or "AuditMixin" in mixin_names
            )

            domain = infer_domain(backend, f, schema, table)

            models.append(
                ModelInfo(
                    name=node.name,
                    file=f,
                    rel_path=rel(f, repo),
                    line=node.lineno,
                    table=str(table),
                    schema=schema,
                    domain=domain,
                    bases=bases,
                    columns=columns,
                    table_args_text=table_args_text,
                    mixin_names=mixin_names,
                    has_pk=has_pk,
                    has_uuid=has_uuid,
                    has_country_code=has_country_code,
                    has_created_at=has_created_at,
                    has_updated_at=has_updated_at,
                    has_is_deleted=has_is_deleted,
                    has_deleted_at=has_deleted_at,
                    has_version=has_version,
                    has_created_by=has_created_by,
                    has_updated_by=has_updated_by,
                )
            )

    return models


# ============================================================================
# 5. MIGRATION PARSER
# ============================================================================


def parse_migrations(repo: Path) -> MigrationInfo:
    info = MigrationInfo()

    backend = repo / "backend"
    alembic = backend / "alembic"
    versions = alembic / "versions"
    archive = alembic / "versions_archive"

    info.alembic_dir_exists = alembic.exists()
    info.env_exists = (alembic / "env.py").exists()
    info.versions_dir_exists = versions.exists()

    ini_candidates = [
        backend / "alembic.ini",
        repo / "alembic.ini",
        alembic / "alembic.ini",
    ]

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

        for m in re.finditer(
            r"op\.rename_table\(\s*['\"][^'\"]+['\"]\s*,\s*['\"]([^'\"]+)['\"]",
            text,
        ):
            info.tables_created.add(m.group(1).split(".")[-1].lower())

    downs: set[str] = set()

    for f in live_files:
        text = read_text(f) or ""

        rev_match = re.search(
            r"^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]",
            text,
            re.M,
        )

        down_match = re.search(
            r"^down_revision(?:\s*:\s*[^=]+)?\s*=\s*(?:['\"]([^'\"]+)['\"]|None\b)",
            text,
            re.M,
        )

        if rev_match:
            rev = rev_match.group(1)
            down = down_match.group(1) if down_match else None

            info.revisions[rev] = down

            if down:
                downs.add(down)

        if "stub" in f.name.lower():
            info.stubs.append(rel(f, repo))

        tree = parse_safe(f)
        has_downgrade = False

        if tree is not None:
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == "downgrade":
                    has_downgrade = True

                    only_pass = all(isinstance(s, ast.Pass) for s in node.body)

                    only_docstring = (
                        len(node.body) == 1
                        and isinstance(node.body[0], ast.Expr)
                        and isinstance(node.body[0].value, ast.Constant)
                    )

                    if only_pass or only_docstring:
                        info.downgrade_missing.append(f"{rel(f, repo)} (empty downgrade)")

        if not has_downgrade:
            info.downgrade_missing.append(rel(f, repo))

    info.heads = sorted(set(info.revisions.keys()) - downs)
    info.multiple_heads = len(info.heads) > 1

    return info


# ============================================================================
# 6. RLS PARSER
# ============================================================================


def parse_rls(repo: Path) -> RLSInfo:
    info = RLSInfo()

    backend = repo / "backend"

    candidates = [
        backend / "data" / "pg_rls_policies.sql",
        repo / "data" / "pg_rls_policies.sql",
        backend / "db" / "pg_rls_policies.sql",
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
        r"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?([a-zA-Z0-9_\.]+)\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY",
        re.I,
    )

    policy_re = re.compile(
        r"CREATE\s+POLICY\s+\w+\s+ON\s+([a-zA-Z0-9_\.]+)",
        re.I,
    )

    for f in info.sql_files:
        text = read_text(f) or ""

        for rx in (enable_re, policy_re):
            for m in rx.finditer(text):
                table = m.group(1).split(".")[-1].lower()
                info.rls_tables.add(table)

    context_re = re.compile(
        r"app\.current_country_code|set_config\(\s*['\"]app\.current_country_code",
        re.I,
    )

    for f in iter_python_files(backend):
        low = f.stem.lower()

        if "rls" in low:
            info.interceptor_files.append(rel(f, repo))

        parts = {p.lower() for p in f.parts}

        if (
            "middleware" in parts
            or "dependencies" in parts
            or f.name in {"main.py", "lifespan.py"}
        ):
            text = read_text(f) or ""
            if context_re.search(text):
                info.sets_context = True

    return info


# ============================================================================
# 7. STATIC CHECKS
# ============================================================================


def check_model_placement(repo: Path, models: list[ModelInfo], rep: Report) -> None:
    backend = repo / "backend"

    exempt_top = {
        "models",
        "tests",
        "scripts",
        "alembic",
        "data",
        "monitoring",
        "docs",
    }

    for m in models:
        try:
            parts = [p.lower() for p in m.file.relative_to(backend).parts]
        except ValueError:
            parts = []

        if not parts:
            continue

        if parts[0] not in exempt_top:
            rep.add(
                RED,
                "DB26",
                "models",
                m.rel_path,
                f"ORM model '{m.name}' table '{m.table}' is outside backend/models/",
                intended="move ORM models into backend/models/<domain>/; db/ holds infrastructure only",
                line=m.line,
            )


def check_bounded_context_schemas(models: list[ModelInfo], rep: Report) -> None:
    reported = 0

    for m in models:
        if not m.table:
            continue

        if not m.schema:
            rep.add(
                YEL,
                "DB01",
                "models",
                m.rel_path,
                f"model '{m.name}' table '{m.table}' missing bounded-context schema",
                intended="__table_args__ = {'schema': '<domain>'}",
                line=m.line,
            )
            reported += 1

        elif m.schema.lower() not in EXPECTED_SCHEMAS:
            rep.add(
                YEL,
                "DB01",
                "models",
                m.rel_path,
                f"model '{m.name}' uses unknown schema '{m.schema}'",
                intended=f"use one of: {', '.join(sorted(EXPECTED_SCHEMAS))}",
                line=m.line,
            )
            reported += 1

        if reported >= 300:
            break


def check_standard_columns(models: list[ModelInfo], rep: Report) -> None:
    reported = 0

    for m in models:
        if not m.table:
            continue

        if not m.has_pk:
            rep.add(
                RED,
                "DB03",
                "models",
                m.rel_path,
                f"model '{m.name}' table '{m.table}' has no primary key signal",
                intended="every table must have an explicit PK (integer id preferred)",
                line=m.line,
            )
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
            rep.add(
                YEL,
                "DB03",
                "models",
                m.rel_path,
                f"model '{m.name}' table '{m.table}' missing standard columns: {', '.join(missing)}",
                intended="use AuditMixin + SoftDeleteMixin + TenantMixin; add integer PK + uuid",
                line=m.line,
            )
            reported += 1

        id_col = next((c for c in m.columns if c.name.lower() == "id"), None)

        if id_col and id_col.type_name:
            if id_col.type_name.upper() not in INTEGER_TYPES:
                rep.add(
                    YEL,
                    "DB03",
                    "models",
                    m.rel_path,
                    f"model '{m.name}' id column is {id_col.type_name or 'unknown'}; integer PK preferred",
                    intended="use INTEGER/BIGINTEGER PK for performance; keep UUID for external refs",
                    line=id_col.line,
                )
                reported += 1

        if reported >= 400:
            break


def check_country_code_width(models: list[ModelInfo], rep: Report) -> None:
    lengths: dict[str, list[str]] = defaultdict(list)

    for m in models:
        for c in m.columns:
            if c.name.lower() == "country_code" and c.type_args:
                lengths[c.type_args].append(f"{m.table}")

    if len(lengths) > 1:
        detail = "; ".join(
            f"{k}: {len(v)} tables" for k, v in sorted(lengths.items())
        )

        rep.add(
            YEL,
            "DB04",
            "database",
            "backend/models/",
            f"country_code width mismatch ({detail})",
            intended="unify country_code width in one migration before joins (01_DATABASE finding c)",
        )


def check_naming_conventions(models: list[ModelInfo], rep: Report) -> None:
    reported = 0

    for m in models:
        if not m.table:
            continue

        issues: list[str] = []

        if not re.match(r"^[a-z0-9_]+$", m.table):
            issues.append("table name is not snake_case")

        if (
            not m.table.endswith(("s", "es", "ies"))
            and m.table not in TABLE_SINGULAR_ALLOW
        ):
            issues.append("table name should be plural")

        if issues:
            rep.add(
                YEL,
                "DB11",
                "models",
                m.rel_path,
                f"table '{m.table}': " + "; ".join(issues),
                intended="snake_case plural table names",
                line=m.line,
            )
            reported += 1

        column_issues: list[str] = []

        for c in m.columns:
            if not re.match(r"^[a-z0-9_]+$", c.name):
                column_issues.append(f"{c.name} not snake_case")

            upper = c.type_name.upper()

            if upper in JSON_TYPES and not c.name.endswith(
                ("_json", "_payload", "_attributes", "_config")
            ):
                column_issues.append(f"{c.name} JSON/JSONB should end with _json")

            if upper == "BOOLEAN" and not c.name.startswith(
                ("is_", "has_", "can_", "allow_", "enable_")
            ):
                column_issues.append(f"{c.name} boolean should start with is_/has_/can_")

            if upper in DATETIME_TYPES and not c.name.endswith(
                ("_at", "_on", "_date", "_time")
            ):
                column_issues.append(f"{c.name} datetime should end with _at/_on")

        if column_issues:
            rep.add(
                YEL,
                "DB11",
                "models",
                m.rel_path,
                f"table '{m.table}' column convention issues: " + "; ".join(column_issues[:8]),
                intended="follow naming conventions: *_json, is_*, *_at",
                line=m.line,
            )
            reported += 1

        if reported >= 400:
            break


def check_foreign_keys(models: list[ModelInfo], rep: Report) -> None:
    table_to_domain: dict[str, str] = {}

    for m in models:
        if m.table:
            table_to_domain[m.table.lower()] = m.domain

    reported = 0

    for m in models:
        if not m.table:
            continue

        for c in m.columns:
            if not c.fk_target:
                continue

            target = c.fk_target.split(".")[-1].lower()
            target_schema = (
                c.fk_target.split(".")[0].lower() if "." in c.fk_target else None
            )

            target_domain = table_to_domain.get(target)

            if target_schema and m.schema and target_schema != m.schema.lower():
                rep.add(
                    RED,
                    "DB06",
                    "database",
                    m.rel_path,
                    f"cross-schema FK: {m.table}.{c.name} -> {c.fk_target}",
                    intended="cross-ecosystem communication must use services/events, not FKs",
                    line=c.line,
                )
                reported += 1

            elif target_domain and target_domain != m.domain:
                sev = (
                    RED
                    if target_domain in {"finance", "audit", "security", "treasury"}
                    else YEL
                )

                rep.add(
                    sev,
                    "DB06",
                    "database",
                    m.rel_path,
                    f"cross-domain FK: {m.domain}.{m.table}.{c.name} -> {target_domain}.{target}",
                    intended="use service call or durable event; no cross-ecosystem FK chains",
                    line=c.line,
                )
                reported += 1

            if (
                not c.is_index
                and not c.is_unique
                and not c.is_pk
                and c.name not in m.table_args_text
            ):
                rep.add(
                    YEL,
                    "DB08",
                    "database",
                    m.rel_path,
                    f"FK column '{m.table}.{c.name}' has no explicit index signal",
                    intended="every FK should have an explicit index",
                    line=c.line,
                )
                reported += 1

            if c.fk_ondelete is None:
                rep.add(
                    YEL,
                    "DB07",
                    "database",
                    m.rel_path,
                    f"FK '{m.table}.{c.name} -> {c.fk_target}' missing ON DELETE rule",
                    intended="default RESTRICT; CASCADE only for true composition",
                    line=c.line,
                )
                reported += 1

            elif c.fk_ondelete.upper() == "CASCADE":
                protected = (
                    target in FINANCE_PROTECTED_TABLES
                    or target_domain in {"finance", "audit", "security", "treasury"}
                )

                if protected:
                    rep.add(
                        RED,
                        "DB07",
                        "database",
                        m.rel_path,
                        f"dangerous CASCADE into protected table: {m.table}.{c.name} -> {c.fk_target}",
                        intended="never cascade into finance/audit/security; use RESTRICT",
                        line=c.line,
                    )
                    reported += 1

            if reported >= 600:
                return


def check_jsonb_indexes(models: list[ModelInfo], rep: Report) -> None:
    reported = 0

    for m in models:
        for c in m.columns:
            if c.type_name.upper() not in JSON_TYPES:
                continue

            table_args_low = m.table_args_text.lower()

            if (
                not c.is_index
                and "gin" not in table_args_low
                and c.name not in table_args_low
            ):
                rep.add(
                    YEL,
                    "DB09",
                    "database",
                    m.rel_path,
                    f"JSONB column '{m.table}.{c.name}' has no GIN index signal",
                    intended="add GIN index for JSONB attributes used in filters/facets",
                    line=c.line,
                )
                reported += 1

            if reported >= 250:
                return


def check_media_bytes(models: list[ModelInfo], rep: Report) -> None:
    reported = 0

    for m in models:
        for c in m.columns:
            if c.type_name.upper() in BINARY_TYPES:
                rep.add(
                    RED,
                    "DB10",
                    "database",
                    m.rel_path,
                    f"file bytes column detected: {m.table}.{c.name} ({c.type_name})",
                    intended="store metadata in DB; bytes in object storage/CDN (ADR-010)",
                    line=c.line,
                )
                reported += 1

            if reported >= 200:
                return


def scan_create_all(repo: Path) -> list[tuple[str, int, bool]]:
    backend = repo / "backend"
    hits: list[tuple[str, int, bool]] = []

    if not backend.exists():
        return hits

    create_re = re.compile(r"Base\.metadata\.create_all|metadata\.create_all\(")

    gate_re = re.compile(
        r"APP_ENV|development|is_development|settings\.ENV|getenv\(['\"]APP_ENV|config\.ENV",
        re.I,
    )

    for f in iter_python_files(backend):
        text = read_text(f)
        if not text:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if create_re.search(line):
                gated = bool(gate_re.search(text))
                hits.append((rel(f, repo), i, gated))
                break

    return hits


def check_create_all(repo: Path, rep: Report) -> list[tuple[str, int, bool]]:
    hits = scan_create_all(repo)

    for path, line, gated in hits:
        if gated:
            rep.add(
                YEL,
                "DB02",
                "dev",
                path,
                "create_all present but appears dev-gated",
                intended="ensure it is impossible in production; Alembic only",
                line=line,
            )
        else:
            rep.add(
                RED,
                "DB02",
                "dev",
                path,
                "create_all present without visible dev gate",
                intended="gate behind APP_ENV=development; production uses alembic upgrade head",
                line=line,
            )

    return hits


def check_dev_prod_gate(repo: Path, rep: Report) -> None:
    backend = repo / "backend"

    files = [
        backend / "db" / "database.py",
        backend / "utils" / "config.py",
        backend / "core" / "config.py",
    ]

    texts: list[str] = []

    for f in files:
        if f.exists():
            t = read_text(f)
            if t:
                texts.append(t)

    combined = "\n".join(texts)

    gate_re = re.compile(
        r"APP_ENV|development|production|is_development|settings\.ENV|getenv\(['\"]APP_ENV",
        re.I,
    )

    if "sqlite" in combined.lower():
        if not gate_re.search(combined):
            rep.add(
                YEL,
                "DB16",
                "dev",
                "backend/db/database.py",
                "SQLite usage detected without visible environment gate",
                intended="SQLite is dev-only; production must use PostgreSQL",
            )

    if re.search(r"echo\s*=\s*True", combined):
        if not gate_re.search(combined):
            rep.add(
                YEL,
                "DB14",
                "dev",
                "backend/db/database.py",
                "SQL echo=True detected without visible dev gate",
                intended="enable echo only in development",
            )

    if re.search(r"SEED_DATA_ON_STARTUP.*true", combined, re.I):
        if not gate_re.search(combined):
            rep.add(
                YEL,
                "DB14",
                "dev",
                "backend/db/database.py",
                "seed-on-startup appears enabled without visible environment gate",
                intended="disable seeding in production",
            )

    pool_size = re.search(r"pool_size\s*=\s*(\d+)", combined)
    max_overflow = re.search(r"max_overflow\s*=\s*(\d+)", combined)

    if not pool_size:
        rep.add(
            YEL,
            "DB15",
            "production",
            "backend/db/database.py",
            "pool_size not detected",
            intended="app pool should be 5 with max_overflow 10 behind PgBouncer",
        )
    else:
        ps = int(pool_size.group(1)) if pool_size else None
        mo = int(max_overflow.group(1)) if max_overflow else None

        if ps != 5 or mo != 10:
            rep.add(
                YEL,
                "DB15",
                "production",
                "backend/db/database.py",
                f"connection pool config detected pool_size={ps}, max_overflow={mo}",
                intended="grounded target: pool_size=5, max_overflow=10 behind PgBouncer",
            )


def check_migrations(
    repo: Path,
    minfo: MigrationInfo,
    models: list[ModelInfo],
    rep: Report,
) -> None:
    if not minfo.ini_exists or not minfo.env_exists or not minfo.versions_dir_exists:
        rep.add(
            RED,
            "DB12",
            "migrations",
            "backend/alembic/",
            "Alembic pipeline missing required components",
            intended="alembic.ini + env.py + versions/ are mandatory",
        )

    if minfo.multiple_heads:
        rep.add(
            RED,
            "DB13",
            "migrations",
            "backend/alembic/versions/",
            f"multiple Alembic heads detected: {', '.join(minfo.heads[:5])}",
            intended="merge to a single head; production must have one clean head",
        )

    for f in minfo.downgrade_missing[:80]:
        rep.add(
            YEL,
            "DB12",
            "migrations",
            f,
            "migration missing usable downgrade()",
            intended="every migration must have a real downgrade path",
        )

    for f in minfo.stubs[:30]:
        rep.add(
            YEL,
            "DB12",
            "migrations",
            f,
            "stub migration detected",
            intended="archive stubs; do not leave stub revisions in live chain",
        )

    for f in minfo.diagnostics[:30]:
        rep.add(
            YEL,
            "DB12",
            "migrations",
            f,
            "diagnostic script inside alembic/",
            intended="move diagnostics to backend/scripts/",
        )

    model_tables = {m.table.lower() for m in models if m.table}
    orm_only = sorted(model_tables - minfo.tables_created - {"alembic_version"})

    if orm_only:
        rep.add(
            YEL,
            "DB13",
            "migrations",
            "backend/models/",
            f"{len(orm_only)} model tables not found in migration create_table operations: "
            + ", ".join(orm_only[:20]),
            intended="verify migrations exist for all ORM tables; create missing migrations",
        )

    if not minfo.has_partition:
        rep.add(
            YEL,
            "DB23",
            "production",
            "backend/alembic/versions/",
            "no partitioning signal detected in migrations",
            intended=f"partition hot append-only tables: {', '.join(sorted(PARTITION_EXPECTED_TABLES))}",
        )


def check_rls(
    repo: Path,
    models: list[ModelInfo],
    rls: RLSInfo,
    rep: Report,
) -> None:
    country_tables = sorted(
        {m.table.lower() for m in models if m.has_country_code and m.table}
    )

    if country_tables and not rls.sql_files:
        rep.add(
            RED,
            "DB05",
            "security",
            "backend/data/pg_rls_policies.sql",
            "country-scoped models exist but no RLS SQL file found",
            intended="add pg_rls_policies.sql and enable RLS on every country-scoped table",
        )

    if rls.sql_files:
        missing = [t for t in country_tables if t not in rls.rls_tables]

        if missing:
            rep.add(
                YEL,
                "DB05",
                "security",
                "backend/data/pg_rls_policies.sql",
                f"{len(missing)} country-scoped tables missing RLS signal: "
                + ", ".join(missing[:20]),
                intended="enable RLS + policies for every country_code table",
            )

    if country_tables and not rls.sets_context:
        rep.add(
            RED,
            "DB05",
            "security",
            "backend/middleware/",
            "no middleware signal setting app.current_country_code",
            intended="set RLS context per request; fail closed",
        )

    if len(set(rls.interceptor_files)) > 1:
        rep.add(
            YEL,
            "DB05",
            "security",
            "backend/middleware/",
            f"multiple RLS-related modules detected: {', '.join(sorted(set(rls.interceptor_files))[:5])}",
            intended="keep ONE canonical RLS enforcer; alias/delete duplicates",
        )


def check_event_tables(all_tables: set[str], rep: Report) -> None:
    missing = sorted(EXPECTED_EVENT_TABLES - all_tables)

    if missing:
        rep.add(
            YEL,
            "DB17",
            "database",
            "backend/models/",
            f"missing event/outbox tables: {', '.join(missing)}",
            intended="implement transactional outbox: outbox_events, inbox_events, retry, DLQ",
        )


def check_audit_tables(all_tables: set[str], rep: Report) -> None:
    if "audit_logs" not in all_tables:
        rep.add(
            YEL,
            "DB18",
            "database",
            "backend/models/",
            "audit_logs table not detected",
            intended="use one append-only partitioned audit_logs table with log_type",
        )

    log_tables = sorted(
        {
            t
            for t in all_tables
            if "log" in t
            and t not in {"audit_logs", "worm_audit", "login_log", "activity_log"}
        }
    )

    if len(log_tables) > 3:
        rep.add(
            YEL,
            "DB18",
            "database",
            "backend/models/",
            f"possible log-table fragmentation: {', '.join(log_tables[:10])}",
            intended="consolidate into audit_logs with log_type enum; avoid many log tables",
        )


def check_analytics(repo: Path, all_tables: set[str], rep: Report) -> None:
    has_snapshot = any(
        t.startswith("mv_") or t.startswith("kpi_") for t in all_tables
    )

    if not has_snapshot:
        rep.add(
            YEL,
            "DB19",
            "analytics",
            "backend/models/",
            "no analytics snapshot/materialized-view tables detected (mv_*/kpi_*)",
            intended="dashboards should read snapshots/materialized views, not live aggregates",
        )

    agg_re = re.compile(r"func\.(sum|count|avg|min|max)\(|group_by\(", re.I)

    reported = 0

    for layer in ("routers", "controllers"):
        d = repo / "backend" / layer
        if not d.exists():
            continue

        for f in iter_python_files(d):
            text = read_text(f)
            if not text:
                continue

            if agg_re.search(text):
                rep.add(
                    YEL,
                    "DB19",
                    "analytics",
                    rel(f, repo),
                    "possible live aggregate in request path",
                    intended="move heavy aggregation to snapshots/materialized views",
                )
                reported += 1

            if reported >= 80:
                return


def check_finance_immutability(repo: Path, rep: Report) -> None:
    backend = repo / "backend"

    if not backend.exists():
        return

    finance_re = re.compile(
        r"(?i)\b(update|delete)\s*\(\s*"
        r"(journal_entries|journal_entry_lines|ap_ledger_entries|ar_ledger_entries|ledger_entries|accounts)\b"
        r"|\.query\(\s*(JournalEntry|LedgerEntry|ApLedgerEntry|ArLedgerEntry)\s*\)\s*\.(update|delete)"
    )

    reported = 0

    for f in iter_python_files(backend):
        parts = {p.lower() for p in f.parts}

        if "tests" in parts or "scripts" in parts or "alembic" in parts:
            continue

        text = read_text(f)
        if not text:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if finance_re.search(line):
                rep.add(
                    RED,
                    "DB20",
                    "finance",
                    rel(f, repo),
                    "possible mutation of finance ledger table",
                    intended="posted ledger entries must be immutable; use reversal/adjustment events",
                    line=i,
                )
                reported += 1
                break

        if reported >= 80:
            return


def check_ai_staging(repo: Path, all_tables: set[str], rep: Report) -> None:
    missing = sorted(EXPECTED_AI_TABLES - all_tables)

    if missing:
        rep.add(
            YEL,
            "DB21",
            "ai",
            "backend/models/",
            f"missing AI staging/audit tables: {', '.join(missing)}",
            intended="AI writes to staging/ai_* tables; commit explicitly with audit",
        )

    backend = repo / "backend"

    direct_re = re.compile(
        r"session\.add\(\s*Product|add\(\s*Product\(|insert\(\s*products\b|\.query\(\s*Product\s*\)\s*\.(update|delete)"
    )

    reported = 0

    for f in iter_python_files(backend):
        parts = [p.lower() for p in f.parts]

        if "ai" not in parts and "ai" not in f.stem.lower():
            continue

        text = read_text(f)
        if not text:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if direct_re.search(line):
                rep.add(
                    YEL,
                    "DB21",
                    "ai",
                    rel(f, repo),
                    "possible direct AI write into business table",
                    intended="AI output must go to staging first, then explicit commit",
                    line=i,
                )
                reported += 1
                break

        if reported >= 80:
            return


def check_config_constants(repo: Path, rep: Report) -> None:
    backend = repo / "backend"

    if not backend.exists():
        return

    const_re = re.compile(
        r"(?i)\b(COMMISSION|COMMISSION_PERCENT|DELIVERY_FEE|REFUND_PERCENT|REWARD_PERCENT|VAT_PERCENT|TAX_PERCENT)\s*[:=]\s*\d"
    )

    reported = 0

    for f in iter_python_files(backend):
        parts = {p.lower() for p in f.parts}

        if {"tests", "scripts", "alembic", "data"} & parts:
            continue

        text = read_text(f)
        if not text:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if const_re.search(line):
                rep.add(
                    YEL,
                    "DB22",
                    "configuration",
                    rel(f, repo),
                    "hardcoded business constant detected",
                    intended="store business rules in config tables, not code",
                    line=i,
                )
                reported += 1
                break

        if reported >= 100:
            return


# ============================================================================
# 8. PRODUCTION CHECKLIST
# ============================================================================


def check_production_checklist(
    repo: Path,
    rep: Report,
    models: list[ModelInfo],
    minfo: MigrationInfo,
    rls: RLSInfo,
    create_all_hits: list[tuple[str, int, bool]],
    live_summary: dict | None,
) -> list[dict]:
    checklist: list[dict] = []

    def add(name: str, ok: bool, detail: str, intended: str = "", critical: bool = False) -> None:
        checklist.append(
            {
                "name": name,
                "status": "PASS" if ok else "FAIL",
                "detail": detail,
            }
        )

        if not ok:
            rep.add(
                RED if critical else YEL,
                "DB24",
                "production",
                name,
                detail,
                intended=intended,
            )

    backend = repo / "backend"

    gi = repo / ".gitignore"
    gi_text = read_text(gi) or ""
    gi_ok = gi.exists() and "*.db" in gi_text and ".env" in gi_text
    add(
        "root .gitignore protects DB/env",
        gi_ok,
        ".gitignore must exclude *.db* and .env",
        intended="add strict root .gitignore",
        critical=True,
    )

    env_example_ok = (repo / ".env.example").exists() or (backend / ".env.example").exists()
    add(
        ".env.example exists",
        env_example_ok,
        "repository should contain .env.example, never real .env",
        intended="add .env.example",
    )

    alembic_ok = minfo.ini_exists and minfo.env_exists and minfo.versions_dir_exists
    add(
        "Alembic pipeline exists",
        alembic_ok,
        "alembic.ini + env.py + versions/ required",
        intended="restore Alembic pipeline",
        critical=True,
    )

    add(
        "single migration head",
        not minfo.multiple_heads,
        f"heads: {', '.join(minfo.heads[:5]) if minfo.heads else 'none'}",
        intended="merge heads to one clean production head",
        critical=True,
    )

    country_models = [m for m in models if m.has_country_code]

    rls_file_ok = bool(rls.sql_files) or not country_models
    add(
        "RLS policy file exists",
        rls_file_ok,
        "pg_rls_policies.sql required for country-scoped tables",
        intended="add backend/data/pg_rls_policies.sql",
        critical=bool(country_models),
    )

    add(
        "RLS context setter exists",
        rls.sets_context or not country_models,
        "middleware must set app.current_country_code",
        intended="add RLS interceptor/middleware",
        critical=bool(country_models),
    )

    table_models = [m for m in models if m.table]
    schema_models = [m for m in table_models if m.schema]
    pct = int((len(schema_models) / len(table_models) * 100)) if table_models else 100

    add(
        "models declare bounded-context schema",
        pct >= 80,
        f"{pct}% models declare __table_args__ schema",
        intended="add schema to all models",
    )

    ungated = [h for h in create_all_hits if not h[2]]
    add(
        "create_all safely gated",
        len(ungated) == 0,
        f"{len(ungated)} ungated create_all location(s)",
        intended="create_all must be dev-only",
        critical=True,
    )

    db_text = ""
    for p in (backend / "db" / "database.py", backend / "utils" / "config.py"):
        if p.exists():
            db_text += read_text(p) or ""

    pool_ok = bool(re.search(r"pool_size\s*=\s*\d+", db_text))
    add(
        "connection pool configured",
        pool_ok,
        "pool_size/max_overflow should be explicit",
        intended="use pool_size=5, max_overflow=10 behind PgBouncer",
    )

    monitoring_ok = (backend / "monitoring").exists() or (repo / "monitoring").exists()
    add(
        "monitoring present",
        monitoring_ok,
        "Prometheus/Grafana/Promtail stack expected",
        intended="add monitoring/",
    )

    dictionary_ok = (backend / "scripts" / "generate_data_dictionary.py").exists()
    add(
        "data dictionary generator present",
        dictionary_ok,
        "machine-generated data dictionary required",
        intended="add backend/scripts/generate_data_dictionary.py",
    )

    tests_ok = (backend / "tests" / "test_database.py").exists()
    add(
        "database tests present",
        tests_ok,
        "backend/tests/test_database.py expected",
        intended="add database contract/integration tests",
    )

    if live_summary:
        heads = live_summary.get("heads", [])
        add(
            "live DB single Alembic head",
            len(heads) <= 1,
            f"live heads: {', '.join(heads[:5]) if heads else 'none'}",
            intended="migrate/merge live database to single head",
            critical=True,
        )

    return checklist


# ============================================================================
# 9. OPTIONAL LIVE CHECKS
# ============================================================================


def safe_dsn(dsn: str) -> str:
    return re.sub(r"://([^@]+)@", "://***@", dsn)


def run_live_checks(dsn: str, rep: Report) -> dict:
    try:
        import sqlalchemy
        from sqlalchemy import text
    except Exception:
        rep.add(
            YEL,
            "DB25",
            "live",
            safe_dsn(dsn),
            "SQLAlchemy not available for live checks",
            intended="install sqlalchemy + psycopg2 to enable live read-only checks",
        )
        return {}

    engine = None
    heads: list[str] = []

    try:
        engine = sqlalchemy.create_engine(dsn, future=True, pool_pre_ping=True)

        with engine.connect() as conn:
            version = conn.execute(
                text("select current_setting('server_version')")
            ).scalar()

            rep.add(
                GRN,
                "DB25",
                "live",
                safe_dsn(dsn),
                f"connected; PostgreSQL server_version={version}",
            )

            extensions = {
                row[0]
                for row in conn.execute(text("select extname from pg_extension"))
            }

            missing_ext = sorted(EXPECTED_EXTENSIONS - extensions)

            if missing_ext:
                rep.add(
                    YEL,
                    "DB25",
                    "live",
                    "pg_extension",
                    f"missing extensions: {', '.join(missing_ext)}",
                    intended="install pgvector/pgcrypto/citext/btree_gin/pg_trgm/uuid-ossp as needed",
                )

            schemas = {
                row[0]
                for row in conn.execute(
                    text("select schema_name from information_schema.schemata")
                )
            }

            missing_schemas = sorted(EXPECTED_SCHEMAS - schemas)

            if missing_schemas:
                rep.add(
                    YEL,
                    "DB25",
                    "live",
                    "information_schema.schemata",
                    f"missing bounded-context schemas: {', '.join(missing_schemas)}",
                    intended="create PostgreSQL schemas per 01_DATABASE §2.2",
                )

            has_alembic = conn.execute(
                text("select to_regclass('alembic_version')")
            ).scalar()

            if has_alembic:
                heads = [
                    row[0]
                    for row in conn.execute(
                        text("select version_num from alembic_version")
                    )
                ]

                if len(heads) > 1:
                    rep.add(
                        RED,
                        "DB13",
                        "live",
                        "alembic_version",
                        f"live database has multiple heads: {', '.join(heads[:5])}",
                        intended="merge live Alembic heads immediately",
                    )
                elif len(heads) == 1:
                    rep.add(
                        GRN,
                        "DB25",
                        "live",
                        "alembic_version",
                        f"live Alembic head: {heads[0]}",
                    )
            else:
                rep.add(
                    YEL,
                    "DB12",
                    "live",
                    "alembic_version",
                    "alembic_version table not found in live database",
                    intended="initialize Alembic properly",
                )

            country_rows = conn.execute(
                text(
                    """
                    select table_schema, table_name
                    from information_schema.columns
                    where column_name = 'country_code'
                    """
                )
            ).fetchall()

            if country_rows:
                rls_rows = conn.execute(
                    text(
                        """
                        select n.nspname, c.relname, c.relrowsecurity
                        from pg_class c
                        join pg_namespace n on n.oid = c.relnamespace
                        where c.relkind in ('r', 'p')
                        """
                    )
                ).fetchall()

                rls_map = {(row[0], row[1]): bool(row[2]) for row in rls_rows}

                missing_rls = []

                for schema_name, table_name in country_rows:
                    if not rls_map.get((schema_name, table_name), False):
                        missing_rls.append(f"{schema_name}.{table_name}")

                if missing_rls:
                    rep.add(
                        RED,
                        "DB05",
                        "live",
                        "pg_class.relrowsecurity",
                        f"{len(missing_rls)} live country_code tables without RLS: "
                        + ", ".join(missing_rls[:20]),
                        intended="enable RLS fail-closed on every country-scoped table",
                    )

            table_counts = conn.execute(
                text(
                    """
                    select table_schema, count(*)
                    from information_schema.tables
                    where table_schema not in ('pg_catalog', 'information_schema')
                    group by table_schema
                    order by table_schema
                    """
                )
            ).fetchall()

            if table_counts:
                rep.add(
                    GRN,
                    "DB25",
                    "live",
                    "tables",
                    "tables by schema: "
                    + ", ".join(f"{s}={c}" for s, c in table_counts),
                )

            return {
                "version": version,
                "extensions": sorted(extensions),
                "schemas": sorted(schemas),
                "heads": heads,
                "table_counts": [
                    {"schema": s, "count": int(c)} for s, c in table_counts
                ],
            }

    except Exception as exc:
        rep.add(
            RED,
            "DB25",
            "live",
            safe_dsn(dsn),
            f"live database check failed: {exc}",
            intended="verify DSN/network; live checks are read-only SELECTs",
        )
        return {}


# ============================================================================
# 10. SUMMARY / SCORE
# ============================================================================


def compute_debt_score(rep: Report) -> int:
    red = sum(1 for f in rep.findings if f.sev == RED)
    yel = sum(1 for f in rep.findings if f.sev == YEL)

    by = rep.counters

    score = red * 100 + yel * 15

    score += by.get("DB02", 0) * 80
    score += by.get("DB05", 0) * 80
    score += by.get("DB06", 0) * 50
    score += by.get("DB10", 0) * 70
    score += by.get("DB13", 0) * 60
    score += by.get("DB14", 0) * 50
    score += by.get("DB16", 0) * 60
    score += by.get("DB20", 0) * 80
    score += by.get("DB25", 0) * 20
    score += by.get("DB26", 0) * 60
    score += by.get("DB03", 0) * 8
    score += by.get("DB07", 0) * 10
    score += by.get("DB08", 0) * 6
    score += by.get("DB09", 0) * 6
    score += by.get("DB11", 0) * 3
    score += by.get("DB12", 0) * 20
    score += by.get("DB17", 0) * 15
    score += by.get("DB18", 0) * 12
    score += by.get("DB19", 0) * 12
    score += by.get("DB21", 0) * 18
    score += by.get("DB22", 0) * 8
    score += by.get("DB23", 0) * 12
    score += by.get("DB24", 0) * 25
    score += by.get("DB27", 0) * 70
    score += by.get("DB28", 0) * 25
    score += by.get("DB29", 0) * 20
    score += by.get("DB30", 0) * 12
    score += by.get("DB31", 0) * 8
    score += by.get("DB32", 0) * 10
    score += by.get("DB33", 0) * 60
    score += by.get("DB34", 0) * 50
    score += by.get("DB35", 0) * 15
    score += by.get("DB36", 0) * 12
    score += by.get("DB37", 0) * 10

    return int(score)


def build_summary(
    repo: Path,
    rep: Report,
    models: list[ModelInfo],
    minfo: MigrationInfo,
    rls: RLSInfo,
    checklist: list[dict],
    live_summary: dict | None,
    debt_score: int,
) -> dict:
    n_red = sum(1 for f in rep.findings if f.sev == RED)
    n_yel = sum(1 for f in rep.findings if f.sev == YEL)
    n_grn = sum(1 for f in rep.findings if f.sev == GRN)

    table_models = [m for m in models if m.table]
    schema_models = [m for m in table_models if m.schema]

    pct = int((len(schema_models) / len(table_models) * 100)) if table_models else 100

    return {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": str(repo),
        "red": n_red,
        "yellow": n_yel,
        "green": n_grn,
        "debt_score": debt_score,
        "by_code": dict(rep.counters),
        "models": len(table_models),
        "tables": len({m.table.lower() for m in table_models}),
        "schemas_declared_pct": pct,
        "migration_heads": minfo.heads,
        "rls_tables": len(rls.rls_tables),
        "production_checklist": checklist,
        "live": live_summary or {},
    }


# ============================================================================
# 11. RENDERING
# ============================================================================


def render_stdout(repo: Path, rep: Report, summary: dict) -> int:
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary["debt_score"]

    print("=" * 78)
    print("  ZOZI DATABASE GOVERNANCE AUDIT")
    print("  dev · migrations · models · RLS · finance · AI · analytics · production")
    print("=" * 78)
    print(f"  repo: {repo}")
    print(f"  [RED] VIOLATIONS : {n_red}    [YEL] ADVISORIES : {n_yel}    [GRN] INFO : {n_grn}")
    print(f"  DATABASE DEBT SCORE: {debt}")
    print("  by rule: " + ", ".join(f"{k}={v}" for k, v in sorted(rep.counters.items())))

    hot = [f for f in rep.findings if f.code in HOTLIST_RULES or f.sev == RED]
    hot.sort(key=lambda f: (0 if f.sev == RED else 1, f.code, f.path))

    print("-" * 78)
    print(f"  DATABASE DAMAGE HOTLIST ({len(hot)} items)")
    print("-" * 78)

    for f in hot[:90]:
        print(f"  {SEV_ICON[f.sev]} {f.code:<5} [{f.domain:<10}] {f.loc()}")
        print(f"        {f.message}")
        if f.intended:
            print(f"        -> intended: {f.intended}")

    if len(hot) > 90:
        print(f"  ... +{len(hot) - 90} more")

    by_dom: dict[str, list[Finding]] = defaultdict(list)

    for f in rep.findings:
        by_dom[f.domain].append(f)

    for dom in [
        "database",
        "models",
        "migrations",
        "dev",
        "security",
        "finance",
        "ai",
        "analytics",
        "configuration",
        "production",
        "live",
    ]:
        items = by_dom.get(dom, [])
        if not items:
            continue

        print("\n" + "=" * 78)
        print(f"  DOMAIN: {dom.upper()} ({len(items)} finding(s))")
        print("=" * 78)

        for sev in (RED, YEL, GRN):
            for f in [x for x in items if x.sev == sev]:
                print(f"  {SEV_ICON[f.sev]} {f.code}  {f.loc()}")
                print(f"        {f.message}")
                if f.intended:
                    print(f"        -> {f.intended}")

    print("\n" + "=" * 78)
    print("  PRODUCTION CHECKLIST")
    print("=" * 78)

    for item in summary.get("production_checklist", []):
        icon = "✅" if item["status"] == "PASS" else "❌"
        print(f"  {icon} {item['name']:<42} {item['detail']}")

    if summary.get("live"):
        live = summary["live"]

        print("\n" + "=" * 78)
        print("  LIVE DATABASE")
        print("=" * 78)

        if live.get("version"):
            print(f"  version: {live['version']}")

        if live.get("heads"):
            print(f"  heads: {', '.join(live['heads'])}")

        if live.get("extensions"):
            print(f"  extensions: {', '.join(live['extensions'])}")

        if live.get("table_counts"):
            print("  tables by schema:")
            for row in live["table_counts"]:
                print(f"    {row['schema']}: {row['count']}")

    print("\n" + "=" * 78)

    return n_red


def render_markdown(repo: Path, rep: Report, out: Path, summary: dict) -> None:
    n_red = summary["red"]
    n_yel = summary["yellow"]
    n_grn = summary["green"]
    debt = summary["debt_score"]

    L = [
        "# ZOZI Database Governance Audit Report (GENERATED — do not hand-edit)",
        "",
        f"**Repo:** `{repo}`  ",
        f"**Result:** 🔴 {n_red} · 🟡 {n_yel} · 🟢 {n_grn}  ",
        f"**Database Debt Score:** `{debt}`  ",
        "**Ephemeral. Add to `.gitignore`.**",
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
        "## Database Damage Hotlist",
        "",
        "| Sev | Rule | Domain | Location | Problem | Intended |",
        "|---|---|---|---|---|---|",
    ]

    for f in hot:
        L.append(
            f"| {SEV_ICON[f.sev]} | {f.code} | {f.domain} | `{f.loc()}` | {f.message} | {f.intended or '-'} |"
        )

    L += [
        "",
        "## Production Checklist",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]

    for item in summary.get("production_checklist", []):
        icon = "✅" if item["status"] == "PASS" else "❌"
        L.append(f"| {icon} | {item['name']} | {item['detail']} |")

    by_dom: dict[str, list[Finding]] = defaultdict(list)

    for f in rep.findings:
        by_dom[f.domain].append(f)

    for dom in [
        "database",
        "models",
        "migrations",
        "dev",
        "security",
        "finance",
        "ai",
        "analytics",
        "configuration",
        "production",
        "live",
    ]:
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


# ============================================================================
# 12. MAIN
# ============================================================================


def _looks_like_repo_root(p: Path) -> bool:
    """
    Return True only if this directory looks like the real ZOZI repository root.

    This must NOT accept:
      zozi/scripts
      zozi/script
      zozi/backend/scripts

    as the repository root.
    """
    if not p.is_dir():
        return False

    # Strongest monorepo signal.
    if (p / "backend").is_dir() and (p / "frontend").is_dir():
        return True

    # Backend + docs signal.
    if (p / "backend" / "main.py").is_file() and (p / "documents").is_dir():
        return True

    # Backend-only fallback, but only if it really contains backend/main.py.
    if (p / "backend" / "main.py").is_file() and (p / "backend").is_dir():
        return True

    return False


def find_repo(explicit: str | None) -> Path:
    """
    Find the real ZOZI repository root.

    Priority:
      1. --root argument
      2. if script is inside scripts/ or script/, use its parent if that looks like repo root
      3. walk upward from script location
      4. walk upward from current working directory
      5. fail loudly
    """
    candidates: list[Path] = []

    if explicit:
        explicit_path = Path(explicit).resolve()
        if _looks_like_repo_root(explicit_path):
            return explicit_path

        # If user passed a wrong --root, still try it as fallback later.
        candidates.append(explicit_path)

    script_dir = Path(__file__).resolve().parent

    # If the script is inside scripts/ or script/, the repo root is usually the parent.
    if script_dir.name.lower() in {"scripts", "script"}:
        candidates.append(script_dir.parent)

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

    # First pass: direct candidates.
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

    # Second pass: walk upward from script directory.
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

    # Third pass: walk upward from current working directory.
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

    # Final practical fallback:
    # If script is inside scripts/ or script/, use its parent.
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
      --out DATABASE_AUDIT_REPORT.md
        -> <repo>/DATABASE_AUDIT_REPORT.md

      --out out/database_audit_report.md
        -> <repo>/out/database_audit_report.md

      --out D:/reports/db.md
        -> D:/reports/db.md
    """
    if not value:
        return repo / default_name

    p = Path(value)

    if p.is_absolute():
        return p.resolve()

    # IMPORTANT:
    # Relative paths must be anchored to the repository root,
    # NOT to the current working directory.
    return (repo / p).resolve()

def check_broken_migrations(repo: Path, rep: Report) -> None:
    """
    DB27:
    Detect broken/unparseable migration files and suspicious Union usage.
    Supports ADR-018.
    """
    versions = repo / "backend" / "alembic" / "versions"
    if not versions.exists():
        return

    rev_re = re.compile(
        r"^revision(?:\s*:\s*[^=]+)?\s*=\s*['\"]([^'\"]+)['\"]",
        re.M,
    )

    reported = 0

    for f in sorted(versions.glob("*.py")):
        text = read_text(f)

        if text is None:
            rep.add(
                RED,
                "DB27",
                "migrations",
                rel(f, repo),
                "migration file could not be read",
                intended="repair or remove this migration; Alembic chain must be readable",
            )
            reported += 1
            continue

        if parse_safe(f) is None:
            rep.add(
                RED,
                "DB27",
                "migrations",
                rel(f, repo),
                "migration file is not valid Python (broken head risk)",
                intended="fix syntax/import error; ADR-018 requires a runnable Alembic chain",
            )
            reported += 1

        if not rev_re.search(text):
            rep.add(
                RED,
                "DB27",
                "migrations",
                rel(f, repo),
                "migration file missing revision identifier",
                intended="every Alembic migration must declare revision/down_revision",
            )
            reported += 1

        # Suspicious Union reference without typing import.
        # This is a heuristic for the known broken-head class of issue.
        if re.search(r"\bUnion\b", text):
            has_typing_union = re.search(
                r"from\s+typing\s+import.*\bUnion\b|import\s+typing",
                text,
            )
            if not has_typing_union:
                rep.add(
                    YEL,
                    "DB27",
                    "migrations",
                    rel(f, repo),
                    "suspicious Union reference without visible typing import",
                    intended="verify this migration imports Union correctly; broken imports can fracture Alembic head",
                )
                reported += 1

        if reported >= 100:
            break


def check_destructive_migrations(repo: Path, rep: Report) -> None:
    """
    DB12:
    Detect destructive migration operations.
    Constitution says: keep all tables; never drop/merge to reduce count.
    """
    versions = repo / "backend" / "alembic" / "versions"
    if not versions.exists():
        return

    destructive_re = re.compile(
        r"op\.drop_table\(|op\.drop_column\(|op\.rename_table\(|op\.drop_constraint\(",
        re.I,
    )

    reported = 0

    for f in sorted(versions.glob("*.py")):
        text = read_text(f)
        if not text:
            continue

        for i, line in enumerate(text.splitlines(), 1):
            if destructive_re.search(line):
                rep.add(
                    YEL,
                    "DB12",
                    "migrations",
                    rel(f, repo),
                    "destructive migration operation detected",
                    intended="constitution: keep all tables; drop/rename only via controlled ADR + archive strategy",
                    line=i,
                )
                reported += 1
                break

        if reported >= 100:
            break


def check_migration_contract_tests(repo: Path, rep: Report) -> None:
    """
    DB28:
    Detect whether migration/contract test harness exists.
    """
    backend = repo / "backend"
    tests = backend / "tests"

    if not tests.exists():
        rep.add(
            YEL,
            "DB28",
            "migrations",
            "backend/tests/",
            "backend/tests/ directory not found",
            intended="add database contract/integration tests per 01_DATABASE §8.2",
        )
        return

    test_files = [p.name.lower() for p in tests.rglob("*.py") if p.is_file()]

    if not any("test_database" in name for name in test_files):
        rep.add(
            YEL,
            "DB28",
            "migrations",
            "backend/tests/",
            "test_database.py not found",
            intended="add database contract tests asserting schema shape",
        )

    if not any(
        ("migration" in name or "contract" in name or "alembic" in name)
        for name in test_files
    ):
        rep.add(
            YEL,
            "DB28",
            "migrations",
            "backend/tests/",
            "no migration/contract test file detected",
            intended="every migration should have a contract test asserting before/after shape",
        )


def check_required_canonical_tables(all_tables: set[str], rep: Report) -> None:
    """
    DB29:
    Detect missing canonical platform tables required by the constitution.
    """
    missing = sorted(REQUIRED_CANONICAL_TABLES - all_tables)

    if missing:
        rep.add(
            YEL,
            "DB29",
            "database",
            "backend/models/",
            f"missing canonical tables: {', '.join(missing)}",
            intended="create required platform tables per 01_DATABASE canonical patterns",
        )


def check_required_snapshot_tables(all_tables: set[str], rep: Report) -> None:
    """
    DB30:
    Detect missing analytics snapshot tables from §2.15.
    """
    missing = sorted(REQUIRED_SNAPSHOT_TABLES - all_tables)

    if missing:
        rep.add(
            YEL,
            "DB30",
            "analytics",
            "backend/models/",
            f"missing expected analytics snapshot tables: {', '.join(missing[:10])}",
            intended="dashboards must read snapshots/materialized views per ADR-008",
        )


def check_audit_log_shape(models: list[ModelInfo], rep: Report) -> None:
    """
    DB18:
    If audit_logs model exists, validate expected columns.
    """
    for m in models:
        if not m.table or m.table.lower() != "audit_logs":
            continue

        cols = {c.name.lower() for c in m.columns}

        missing = []

        for col in ("log_type", "actor", "entity", "country_code"):
            if col not in cols:
                missing.append(col)

        has_value_payload = any(
            c in cols
            for c in (
                "old_value_json",
                "new_value_json",
                "old_new_value_json",
                "payload_json",
            )
        )

        if not has_value_payload:
            missing.append("old/new_value_json")

        if missing:
            rep.add(
                YEL,
                "DB18",
                "database",
                m.rel_path,
                f"audit_logs model missing expected columns: {', '.join(missing)}",
                intended="audit_logs should have log_type, actor, entity, old/new_value_json, country_code",
                line=m.line,
            )

        return


def check_partition_specific(repo: Path, rep: Report) -> None:
    """
    DB23:
    Detect whether expected hot tables have partition signals in migrations.
    """
    alembic = repo / "backend" / "alembic"
    if not alembic.exists():
        return

    files = []

    versions = alembic / "versions"
    archive = alembic / "versions_archive"

    if versions.exists():
        files.extend(sorted(versions.glob("*.py")))

    if archive.exists():
        files.extend(sorted(archive.glob("*.py")))

    missing = []

    for table in sorted(EXPECTED_PARTITION_TABLES):
        found = False

        for f in files:
            text = read_text(f)
            if not text:
                continue

            low = text.lower()

            if table in low and (
                "partition by" in low or "postgresql_partition_by" in low
            ):
                found = True
                break

        if not found:
            missing.append(table)

    if missing:
        rep.add(
            YEL,
            "DB23",
            "production",
            "backend/alembic/versions/",
            f"no partition signal for expected hot tables: {', '.join(missing)}",
            intended="add monthly range partitioning for journal_entries/audit_logs/chat_messages/shipment_events",
        )


def check_composite_index_signals(models: list[ModelInfo], rep: Report) -> None:
    """
    DB31:
    Detect missing composite index signals for country_code + created_at.
    """
    reported = 0

    for m in models:
        cols = {c.name.lower() for c in m.columns}

        if "country_code" in cols and "created_at" in cols:
            args_low = m.table_args_text.lower()

            has_composite_signal = (
                "country_code" in args_low and "created_at" in args_low
            )

            country_indexed = any(
                c.name.lower() == "country_code" and (c.is_index or c.is_unique)
                for c in m.columns
            )

            if not has_composite_signal and not country_indexed:
                rep.add(
                    YEL,
                    "DB31",
                    "database",
                    m.rel_path,
                    f"table '{m.table}' has country_code + created_at but no composite index signal",
                    intended="add composite index (country_code, created_at) for tenant time-series queries",
                    line=m.line,
                )
                reported += 1

        if reported >= 200:
            break


def check_offset_pagination(repo: Path, rep: Report) -> None:
    """
    DB32:
    Detect OFFSET pagination in request-path layers.
    Constitution requires cursor-based pagination.
    """
    backend = repo / "backend"

    offset_re = re.compile(r"\.offset\(|\bOFFSET\b", re.I)

    reported = 0

    for layer in ("routers", "controllers", "services"):
        d = backend / layer
        if not d.exists():
            continue

        for f in iter_python_files(d):
            parts = {p.lower() for p in f.parts}

            if "tests" in parts or "scripts" in parts or "alembic" in parts:
                continue

            text = read_text(f)
            if not text:
                continue

            for i, line in enumerate(text.splitlines(), 1):
                if offset_re.search(line):
                    rep.add(
                        YEL,
                        "DB32",
                        "backend",
                        rel(f, repo),
                        "OFFSET pagination detected",
                        intended="use cursor-based pagination; OFFSET is forbidden on large tables",
                        line=i,
                    )
                    reported += 1
                    break

            if reported >= 150:
                return


def check_finance_boundary(repo: Path, models: list[ModelInfo], rep: Report) -> None:
    """
    DB33:
    Detect finance writes outside finance/treasury service boundary.
    """
    backend = repo / "backend"

    finance_write_re = re.compile(
        r"(?i)("
        r"session\.add\(\s*(Journal|Ledger|ApLedger|ArLedger|Payout)\w*"
        r"|\.query\(\s*(JournalEntry|LedgerEntry|ApLedgerEntry|ArLedgerEntry|Payout)\w*\s*\)\s*\.(add|update|delete)"
        r"|insert\(\s*(journal_entries|ap_ledger_entries|ar_ledger_entries|ledger_entries|payouts)\b"
        r")"
    )

    reported = 0

    for f in iter_python_files(backend):
        parts = [p.lower() for p in f.parts]

        if any(
            x in parts
            for x in ("tests", "scripts", "alembic", "data", "monitoring", "docs")
        ):
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
                rep.add(
                    RED,
                    "DB33",
                    "finance",
                    rel(f, repo),
                    "possible finance write outside ledger/treasury service boundary",
                    intended="finance writes must go only through ledger service per ADR-006",
                    line=i,
                )
                reported += 1
                break

        if reported >= 100:
            break

    services = backend / "services"
    has_ledger_service = False

    if services.exists():
        for f in services.rglob("*.py"):
            low = f.name.lower()
            if "ledger" in low or "finance_service" in low:
                has_ledger_service = True
                break

    if not has_ledger_service:
        rep.add(
            YEL,
            "DB33",
            "finance",
            "backend/services/",
            "no finance ledger service detected",
            intended="create services/finance/ledger_service.py as the only finance writer",
        )


def check_rls_fail_closed(repo: Path, rls: RLSInfo, rep: Report) -> None:
    """
    DB34:
    Detect missing fail-closed RLS signals.
    """
    if not rls.sql_files:
        return

    force_found = False

    for f in rls.sql_files:
        text = read_text(f) or ""

        if re.search(r"FORCE\s+ROW\s+LEVEL\s+SECURITY", text, re.I):
            force_found = True
            break

    if not force_found:
        rep.add(
            YEL,
            "DB34",
            "security",
            "backend/data/pg_rls_policies.sql",
            "no FORCE ROW LEVEL SECURITY signal detected",
            intended="use FORCE ROW LEVEL SECURITY so table owners cannot bypass RLS",
        )

    backend = repo / "backend"
    registry_found = False

    for f in iter_python_files(backend):
        text = read_text(f)
        if text and "COUNTRY_AWARE_TABLES" in text:
            registry_found = True
            break

    if not registry_found:
        rep.add(
            YEL,
            "DB34",
            "security",
            "backend/",
            "no COUNTRY_AWARE_TABLES registry signal detected",
            intended="maintain an explicit RLS table registry and lint country_code tables against it",
        )


def check_idempotency_tables(all_tables: set[str], rep: Report) -> None:
    """
    DB35:
    Detect missing idempotency / webhook dedupe tables.
    """
    if "processed_webhook_events" not in all_tables:
        rep.add(
            YEL,
            "DB35",
            "database",
            "backend/models/",
            "processed_webhook_events table not detected",
            intended="external/write actions must be idempotent; track processed events/webhooks",
        )


def check_archive_retention(repo: Path, rep: Report) -> None:
    """
    DB36:
    Detect missing archive/retention signals.
    """
    alembic = repo / "backend" / "alembic"
    if not alembic.exists():
        rep.add(
            YEL,
            "DB36",
            "production",
            "backend/alembic/",
            "no archive/retention signal detected",
            intended="add archive schema / partition detach / retention jobs per §2.8",
        )
        return

    found = False

    for f in alembic.rglob("*.py"):
        text = read_text(f)
        if not text:
            continue

        low = text.lower()

        if "archive" in low or "detach_partition" in low or "retention" in low:
            found = True
            break

    if not found:
        rep.add(
            YEL,
            "DB36",
            "production",
            "backend/alembic/",
            "no archive/retention signal detected in migrations",
            intended="implement archive schema / partition detach / retention policy per §2.8",
        )


def check_data_dictionary_erd(repo: Path, rep: Report) -> None:
    """
    DB37:
    Detect whether generate_data_dictionary.py emits Mermaid ERD output.
    """
    gen = repo / "backend" / "scripts" / "generate_data_dictionary.py"

    if not gen.exists():
        return

    text = read_text(gen) or ""

    if not re.search(r"erDiagram|mermaid|\.mmd", text, re.I):
        rep.add(
            YEL,
            "DB37",
            "database",
            rel(gen, repo),
            "data dictionary generator does not appear to emit Mermaid ERD output",
            intended="extend generator to emit FK edges + Mermaid erDiagram per §6.4",
        )

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


def print_database_trend(rep: Report, current: dict, baseline: dict | None) -> None:
    if not baseline:
        print("\nNo database trend baseline found. Use --update-trend to create one.")
        return

    old_red = int(baseline.get("red", 0))
    old_yel = int(baseline.get("yellow", 0))
    old_score = int(baseline.get("debt_score", 0))

    new_red = int(current.get("red", 0))
    new_yel = int(current.get("yellow", 0))
    new_score = int(current.get("debt_score", 0))

    print("\n" + "=" * 78)
    print("  DATABASE ARCHITECTURE TREND")
    print("=" * 78)
    print(f"  RED: {old_red} -> {new_red}   YEL: {old_yel} -> {new_yel}")
    print(f"  DATABASE DEBT SCORE: {old_score} -> {new_score}")

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
            print(f"    +{delta:<2} {code:<5} {old} -> {new}")

    if improvements:
        print("\n  Improvements:")
        for code, old, new, delta in improvements:
            print(f"    {delta:<3} {code:<5} {old} -> {new}")

    if not regressions and not improvements:
        print("\n  No database rule-count changes since baseline.")

    rep.add(
        GRN,
        "DBT1",
        "database",
        "trend",
        f"RED {old_red}->{new_red}, YEL {old_yel}->{new_yel}, DEBT {old_score}->{new_score}",
        intended="track database debt down continuously",
    )

def main() -> int:
    ap = argparse.ArgumentParser(
        description="ZOZI read-only database governance auditor."
    )

    ap.add_argument("--root", default=None, help="repo root")
    ap.add_argument("--out", default=None, help="markdown report path")
    ap.add_argument("--json", default=None, help="write JSON report")
    ap.add_argument("--no-write", action="store_true", help="do not write markdown report")
    ap.add_argument("--no-fail", action="store_true", help="always exit 0")
    ap.add_argument("--ci", action="store_true", help="CI mode")
    ap.add_argument("--trend-file", default=None, help="JSON file used for database audit trend comparison")
    ap.add_argument("--update-trend", action="store_true", help="overwrite database trend file with current summary")
    ap.add_argument("--live-dsn", default=None, help="optional live PostgreSQL DSN")
    ap.add_argument("--live-env",action="store_true",help="use DATABASE_URL environment variable for live checks",)

    args = ap.parse_args()

    repo = find_repo(args.root)

    print(f"[DEBUG] Repo root detected: {repo}")
    print(f"[DEBUG] Current working directory: {Path.cwd().resolve()}")

    if not repo.is_dir():
        print(f"[FATAL] repo root not found: {repo}", file=sys.stderr)
        return 2

    if args.ci:
        if not args.json:
            args.json = str(repo / "out" / "governance" / "database_audit.json")

        if not args.out and not args.no_write:
            args.out = str(repo / "out" / "governance" / "database_audit_report.md")

        if not args.trend_file:
            args.trend_file = str(repo / ".governance" / "database_trend.json")

    print(f"Scanning database architecture: {repo}")

    rep = Report()

    models = parse_models(repo)
    minfo = parse_migrations(repo)
    rls = parse_rls(repo)

    model_tables = {m.table.lower() for m in models if m.table}
    all_tables = set(model_tables) | set(minfo.tables_created)

    check_model_placement(repo, models, rep)
    check_bounded_context_schemas(models, rep)
    check_standard_columns(models, rep)
    check_country_code_width(models, rep)
    check_naming_conventions(models, rep)
    check_foreign_keys(models, rep)
    check_jsonb_indexes(models, rep)
    check_media_bytes(models, rep)

    create_all_hits = check_create_all(repo, rep)
    check_dev_prod_gate(repo, rep)

    check_migrations(repo, minfo, models, rep)
    check_rls(repo, models, rls, rep)

    check_event_tables(all_tables, rep)
    check_audit_tables(all_tables, rep)
    check_analytics(repo, all_tables, rep)
    check_finance_immutability(repo, rep)
    check_ai_staging(repo, all_tables, rep)
    check_config_constants(repo, rep)
    # v2 constitution enhancements
    check_broken_migrations(repo, rep)
    check_destructive_migrations(repo, rep)
    check_migration_contract_tests(repo, rep)
    check_required_canonical_tables(all_tables, rep)
    check_required_snapshot_tables(all_tables, rep)
    check_audit_log_shape(models, rep)
    check_partition_specific(repo, rep)
    check_composite_index_signals(models, rep)
    check_offset_pagination(repo, rep)
    check_finance_boundary(repo, models, rep)
    check_rls_fail_closed(repo, rls, rep)
    check_idempotency_tables(all_tables, rep)
    check_archive_retention(repo, rep)
    check_data_dictionary_erd(repo, rep)

    dsn = args.live_dsn

    if args.live_env and not dsn:
        dsn = os.environ.get("DATABASE_URL")

    live_summary = None

    if dsn:
        live_summary = run_live_checks(dsn, rep)

    checklist = check_production_checklist(
        repo,
        rep,
        models,
        minfo,
        rls,
        create_all_hits,
        live_summary,
    )

    debt_score = compute_debt_score(rep)

    summary = build_summary(
        repo,
        rep,
        models,
        minfo,
        rls,
        checklist,
        live_summary,
        debt_score,
    )

    trend_path = Path(args.trend_file).resolve() if getattr(args, "trend_file", None) else None

    if trend_path:
        if getattr(args, "update_trend", False):
            update_trend(trend_path, summary)
            print(f"\nDatabase trend file updated: {trend_path}")
        else:
            baseline = read_json(trend_path)
            print_database_trend(rep, summary, baseline)
            
    n_red = render_stdout(repo, rep, summary)

    if not args.no_write:
        out = resolve_repo_output_path(
            repo,
            args.out,
            "DATABASE_AUDIT_REPORT.md",
        )

        render_markdown(repo, rep, out, summary)
        print(f"\nReport written: {out}")

    if args.json:
        jp = resolve_repo_output_path(
            repo,
            args.json,
            "database_audit.json",
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

    return 1 if (n_red and not args.no_fail) else 0


if __name__ == "__main__":
    sys.exit(main())