#!/usr/bin/env python3
"""
migrate_to_target_structure.py

Safe migration script for ZOZI repository restructuring.

DEFAULT BEHAVIOR:
  - DRY-RUN ONLY.
  - Prints planned operations.
  - Does NOT move anything unless --apply is passed.

SAFETY FEATURES:
  - Creates timestamped backup before applying.
  - Writes a JSON manifest of every operation.
  - Supports --reverse using the manifest.
  - Never overwrites existing files by default.
  - Supports optional dangerous code-move modes.
  - Rewrites Python imports only when code moves are explicitly enabled.
  - Snapshots modified Python files before import rewriting.

USAGE:
  # Dry-run safe migration
  python scripts/migrate_to_target_structure.py

  # Apply safe migration
  python scripts/migrate_to_target_structure.py --apply

  # Dry-run full planned migration including code moves and domain reorganization
  python scripts/migrate_to_target_structure.py --include-code-moves --include-domain-reorg --include-root-shadows --include-infra

  # Apply full planned migration
  python scripts/migrate_to_target_structure.py --apply --include-code-moves --include-domain-reorg --include-root-shadows --include-infra

  # Reverse latest migration
  python scripts/migrate_to_target_structure.py --reverse

  # Reverse a specific manifest
  python scripts/migrate_to_target_structure.py --reverse --manifest .structure_migration/manifest_20260730_120000.json

BACKUP:
  Default backup root:
      <project_parent>/zozi_structure_backups

  You can override:
      --backup-root D:/zozi_backups

  Default backup excludes regenerable directories like node_modules, .next, dist, etc.
  For a full backup:
      --full-backup
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# CONFIG
# ============================================================================

MIGRATION_DIR_NAME = ".structure_migration"
MANIFEST_LATEST_NAME = "manifest_latest.json"
CONTENT_SNAPSHOT_DIR_NAME = "content_snapshots"
DRY_RUN_PLAN_NAME = "dry_run_plan.json"

DEFAULT_BACKUP_EXCLUDES = [
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    ".expo",
    ".kotlin",
    "gradle",
    "android",
    "ios",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "coverage",
    "htmlcov",
    ".turbo",
    "playwright-report",
    "test-results",
    ".playwright-artifacts-0",
    "web-dist",
    "tmp",
    ".web-build-test",
    "static-tmp",
]

ALLOW_ROOT_MD = {
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "LICENSE.md",
    "LICENSE",
}

ALLOW_DOCUMENTS_ROOT = {
    "scope",
    "archive",
    "README.md",
    "DOCUMENTATION_INDEX.md",
    "INDEX.md",
}

ROOT_ARTIFACT_FILES = {
    "login_form.yml",
    "login_rsp.json",
    "mobile_app.html",
}

ROOT_LOG_FILES = {
    "backend_server.log",
}

ROOT_EXPERIMENT_DIRS = {
    "Working_API",
    "provider_test",
    "image",
}

ROOT_ARCHIVE_DIRS = {
    "_trash",
    "backup_20260729",
}

ROOT_DESIGN_DIRS = {
    "zozi-logo-app",
}

ROOT_DESIGN_FILES = {
    "stitch_zozi.zip",
    "zozi-logo-app.zip",
}

BACKEND_LOG_GLOB = "*.log"

BACKEND_ARTIFACT_FILES = {
    "_import_test_out.txt",
    "alembic_test.json",
    "schema-audit-report.json",
}

BACKEND_DOC_ARTIFACT_FILES = {
    "schema_mapping.json",
}

BACKEND_ROOT_SHADOW_FILES = {
    "database.py",
    "schemas.py",
    "database_logging.py",
    "seed_all.py",
}

BACKEND_CODE_MOVES = [
    ("backend/api/country_communications.py", "backend/routers/country_communications.py"),
    ("backend/alembic/_analyze_graph.py", "backend/scripts/alembic_diagnostics/_analyze_graph.py"),
    ("backend/alembic/_diagnose_tree.py", "backend/scripts/alembic_diagnostics/_diagnose_tree.py"),
    ("backend/alembic/_graph_analysis.py", "backend/scripts/alembic_diagnostics/_graph_analysis.py"),
    ("backend/db/migrations/new_tables.py", "documents/archive/backend_db_migrations/new_tables.py"),
]

BACKEND_DIR_CODE_MOVES = [
    ("backend/db/migrations", "documents/archive/backend_db_migrations"),
    ("scripts/backend", "archive/ghost_backend/scripts_backend"),
]

INFRA_MOVES = [
    ("monitoring", "infra/monitoring"),
    ("nginx", "infra/nginx"),
]

CREATE_DIRS = [
    "documents/scope",
    "documents/archive",
    "documents/archive/root_docs",
    "documents/archive/root_notes",
    "documents/archive/root_artifacts",
    "documents/archive/documents_archive",
    "documents/archive/backend_artifacts",
    "documents/archive/backend_db_migrations",
    "experiments",
    "design",
    "archive",
    "archive/logs",
    "archive/backend_log",
    "archive/backend_artifacts",
    "archive/frontend",
    "archive/frontend/web_app_scratch",
    "archive/frontend/mobile_app_logs",
    "archive/frontend/mobile_app_scripts_logs",
    "archive/frontend/baks",
    "archive/scripts_frontend_scratch",
    "archive/ghost_backend",
    "backend/scripts",
    "backend/scripts/alembic_diagnostics",
    "backend/routers/admin",
    "backend/routers/supplier",
    "backend/routers/customer",
    "backend/routers/public",
    "backend/routers/webhooks",
    "backend/controllers/finance",
    "backend/controllers/treasury",
    "backend/controllers/payments",
    "backend/controllers/orders",
    "backend/controllers/catalog",
    "backend/controllers/supplier",
    "backend/controllers/logistics",
    "backend/controllers/comms",
    "backend/controllers/hr",
    "backend/controllers/ai",
    "backend/controllers/country",
    "backend/controllers/security",
    "backend/controllers/governance",
    "backend/controllers/media",
    "backend/controllers/core",
    "backend/controllers/admin",
    "backend/controllers/_triage",
    "backend/services/finance",
    "backend/services/treasury",
    "backend/services/payments",
    "backend/services/orders",
    "backend/services/catalog",
    "backend/services/supplier",
    "backend/services/logistics",
    "backend/services/comms",
    "backend/services/hr",
    "backend/services/ai",
    "backend/services/country",
    "backend/services/security",
    "backend/services/governance",
    "backend/services/media",
    "backend/services/core",
    "backend/services/_triage",
    "backend/models/_packages",
]

SERVICE_DOMAIN_RULES: List[Tuple[str, List[str]]] = [
    ("treasury", [
        "treasury",
        "treasurer",
        "payout",
    ]),
    ("payments", [
        "payment",
        "gateway",
    ]),
    ("finance", [
        "finance",
        "financial",
        "ledger",
        "tax",
        "invoice",
        "credit",
        "refund",
        "commission",
        "expense",
        "trading",
        "sub_ledger",
        "period_close",
        "je_reversal",
        "cash",
        "fraud",
    ]),
    ("ai", [
        "ai",
        "bg_removal",
        "image_ai",
        "ocr",
        "free_image",
        "vision",
    ]),
    ("catalog", [
        "catalog",
        "search",
        "filter",
        "variant",
        "content",
        "upload_job",
    ]),
    ("orders", [
        "order",
        "fulfillment",
        "ghost_watchdog",
        "cross_border",
    ]),
    ("logistics", [
        "logistics",
        "shipping",
        "tracking",
        "asset_tracking",
    ]),
    ("supplier", [
        "supplier",
    ]),
    ("comms", [
        "chat",
        "email",
        "notification",
        "comm",
        "translation",
        "video",
        "websocket",
        "proxy_communication",
        "write_chat",
        "fix_chat",
        "entity_chat",
        "internal_communication",
    ]),
    ("hr", [
        "employee",
        "shift",
        "attendance",
        "leave",
        "offboarding",
        "onboarding",
        "lms",
        "okr",
        "performance",
        "retention",
        "succession",
        "travel",
        "hse",
        "dei",
        "background_check",
        "hierarchy",
    ]),
    ("country", [
        "country",
        "localization",
        "map",
        "geo",
    ]),
    ("security", [
        "auth",
        "biometric",
        "coi",
        "compliance",
        "data_residency",
        "permission",
        "rbac",
        "iam",
        "kms",
        "triple_auth",
        "incident",
        "ediscovery",
        "legal_contract",
        "worm_audit",
        "audit",
        "approval_matrix",
    ]),
    ("media", [
        "media",
        "storage",
        "video_service",
    ]),
    ("core", [
        "automation",
        "command_center",
        "confidence",
        "downstream",
        "external_contact",
        "import_service",
        "maker",
        "qr_service",
        "template",
        "webhook_processor",
        "workflow_engine",
        "customer_health",
        "promotion",
        "run_py",
        "script1",
        "write_files_script",
    ]),
]

CONTROLLER_DOMAIN_RULES: List[Tuple[str, List[str]]] = SERVICE_DOMAIN_RULES


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Operation:
    op_id: int
    category: str
    type: str  # mkdir | move_file | move_dir
    src: Optional[str]
    dst: str
    conflict_policy: str = "rename"  # rename | skip
    code: bool = False
    note: str = ""
    status: str = "pending"  # pending | done | skipped | failed | reversed
    src_sha256: Optional[str] = None
    dst_sha256: Optional[str] = None
    size: Optional[int] = None
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "op_id": self.op_id,
            "category": self.category,
            "type": self.type,
            "src": self.src,
            "dst": self.dst,
            "conflict_policy": self.conflict_policy,
            "code": self.code,
            "note": self.note,
            "status": self.status,
            "src_sha256": self.src_sha256,
            "dst_sha256": self.dst_sha256,
            "size": self.size,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Operation":
        return cls(
            op_id=data["op_id"],
            category=data["category"],
            type=data["type"],
            src=data.get("src"),
            dst=data["dst"],
            conflict_policy=data.get("conflict_policy", "rename"),
            code=data.get("code", False),
            note=data.get("note", ""),
            status=data.get("status", "pending"),
            src_sha256=data.get("src_sha256"),
            dst_sha256=data.get("dst_sha256"),
            size=data.get("size"),
            message=data.get("message", ""),
        )


@dataclass
class MigrationManifest:
    version: int = 1
    migration_id: str = ""
    started_at: str = ""
    root: str = ""
    backup_path: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    ops: List[Operation] = field(default_factory=list)
    content_snapshots: Dict[str, str] = field(default_factory=dict)
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "migration_id": self.migration_id,
            "started_at": self.started_at,
            "root": self.root,
            "backup_path": self.backup_path,
            "args": self.args,
            "ops": [op.to_dict() for op in self.ops],
            "content_snapshots": self.content_snapshots,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationManifest":
        manifest = cls(
            version=data.get("version", 1),
            migration_id=data.get("migration_id", ""),
            started_at=data.get("started_at", ""),
            root=data.get("root", ""),
            backup_path=data.get("backup_path"),
            args=data.get("args", {}),
            content_snapshots=data.get("content_snapshots", {}),
            completed=data.get("completed", False),
        )
        manifest.ops = [Operation.from_dict(op) for op in data.get("ops", [])]
        return manifest


# ============================================================================
# UTILITIES
# ============================================================================

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(msg: str) -> None:
    print(msg, flush=True)


def warn(msg: str) -> None:
    print(f"[WARN] {msg}", flush=True)


def error(msg: str) -> None:
    print(f"[ERROR] {msg}", file=sys.stderr, flush=True)


def to_posix_rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def root_join(root: Path, rel: str) -> Path:
    return root / Path(rel)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_size(path: Path) -> Optional[int]:
    try:
        return path.stat().st_size
    except OSError:
        return None


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path

    parent = path.parent
    if path.is_dir():
        base = path.name
        i = 1
        while True:
            candidate = parent / f"{base}.migrated_{i}"
            if not candidate.exists():
                return candidate
            i += 1
    else:
        stem = path.stem
        suffix = path.suffix
        i = 1
        while True:
            candidate = parent / f"{stem}.migrated_{i}{suffix}"
            if not candidate.exists():
                return candidate
            i += 1


def is_within(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def find_repo_root(explicit: Optional[str]) -> Path:
    if explicit:
        root = Path(explicit).resolve()
        if (root / "backend").is_dir() and (root / "frontend").is_dir():
            return root
        return root

    current = Path.cwd().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "backend").is_dir() and (candidate / "frontend").is_dir():
            return candidate

    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        if (candidate / "backend").is_dir() and (candidate / "frontend").is_dir():
            return candidate

    error("Could not auto-detect ZOZI repository root. Use --root.")
    sys.exit(2)


def migration_dir(root: Path) -> Path:
    return root / MIGRATION_DIR_NAME


def latest_manifest_path(root: Path) -> Path:
    return migration_dir(root) / MANIFEST_LATEST_NAME


def save_manifest(root: Path, manifest: MigrationManifest) -> Path:
    mdir = migration_dir(root)
    mdir.mkdir(parents=True, exist_ok=True)

    latest = latest_manifest_path(root)
    latest.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    stamped = mdir / f"manifest_{manifest.migration_id}.json"
    stamped.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")

    return latest


def load_manifest(path: Path) -> MigrationManifest:
    data = json.loads(path.read_text(encoding="utf-8"))
    return MigrationManifest.from_dict(data)


# ============================================================================
# BACKUP
# ============================================================================

def default_backup_root(root: Path) -> Path:
    return root.parent / "zozi_structure_backups"


def backup_project(
    root: Path,
    backup_root: Path,
    full_backup: bool,
    use_robocopy: bool,
) -> Path:
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()
    backup_dir = backup_root / f"zozi_backup_{stamp}"

    if backup_dir.exists():
        i = 1
        while True:
            candidate = backup_root / f"zozi_backup_{stamp}_{i}"
            if not candidate.exists():
                backup_dir = candidate
                break
            i += 1

    excludes = [] if full_backup else DEFAULT_BACKUP_EXCLUDES

    # Prevent backuping the backup directory itself if user chose backup inside repo.
    if is_within(backup_dir, root):
        excludes.append(backup_dir.name)

    log(f"Creating backup: {backup_dir}")
    if excludes:
        log(f"Backup excludes: {', '.join(excludes)}")
    else:
        log("Full backup requested: no excludes.")

    if use_robocopy and platform.system() == "Windows":
        cmd = [
            "robocopy",
            str(root),
            str(backup_dir),
            "/E",
            "/COPY:DAT",
            "/R:1",
            "/W:1",
            "/NFL",
            "/NDL",
            "/NJH",
            "/NJS",
        ]
        if excludes:
            cmd.append("/XD")
            cmd.extend(excludes)

        result = subprocess.run(cmd, capture_output=True, text=True)
        # Robocopy exit codes 0-7 are success/informational.
        if result.returncode >= 8:
            error("robocopy failed during backup.")
            error(result.stdout)
            error(result.stderr)
            sys.exit(3)
    else:
        ignore = shutil.ignore_patterns(*excludes) if excludes else None
        try:
            shutil.copytree(
                root,
                backup_dir,
                ignore=ignore,
                symlinks=True,
                dirs_exist_ok=False,
            )
        except Exception as exc:
            error(f"Python backup failed: {exc}")
            error("You can use --use-robocopy on Windows or choose a different --backup-root.")
            sys.exit(3)

    info = {
        "created_at": utc_now_iso(),
        "source_root": str(root),
        "backup_dir": str(backup_dir),
        "full_backup": full_backup,
        "excludes": excludes,
    }
    (backup_dir / "backup_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")

    log("Backup completed.")
    return backup_dir


# ============================================================================
# PLAN BUILDER
# ============================================================================

class PlanBuilder:
    def __init__(self, root: Path):
        self.root = root
        self.ops: List[Operation] = []
        self._seen_moves: set[Tuple[str, str]] = set()

    def _add_op(self, op: Operation) -> None:
        self.ops.append(op)

    def mkdir(self, rel: str, category: str, note: str = "") -> None:
        op = Operation(
            op_id=len(self.ops) + 1,
            category=category,
            type="mkdir",
            src=None,
            dst=rel,
            conflict_policy="skip",
            code=False,
            note=note,
        )
        self._add_op(op)

    def move_file(
        self,
        src_rel: str,
        dst_rel: str,
        category: str,
        conflict_policy: str = "rename",
        code: bool = False,
        note: str = "",
    ) -> None:
        src_abs = root_join(self.root, src_rel)
        if not src_abs.exists():
            return

        if src_rel == dst_rel:
            return

        key = (src_rel, dst_rel)
        if key in self._seen_moves:
            return
        self._seen_moves.add(key)

        op = Operation(
            op_id=len(self.ops) + 1,
            category=category,
            type="move_file",
            src=src_rel,
            dst=dst_rel,
            conflict_policy=conflict_policy,
            code=code,
            note=note,
        )
        self._add_op(op)

    def move_dir(
        self,
        src_rel: str,
        dst_rel: str,
        category: str,
        conflict_policy: str = "skip",
        code: bool = False,
        note: str = "",
    ) -> None:
        src_abs = root_join(self.root, src_rel)
        if not src_abs.is_dir():
            return

        if src_rel == dst_rel:
            return

        key = (src_rel, dst_rel)
        if key in self._seen_moves:
            return
        self._seen_moves.add(key)

        op = Operation(
            op_id=len(self.ops) + 1,
            category=category,
            type="move_dir",
            src=src_rel,
            dst=dst_rel,
            conflict_policy=conflict_policy,
            code=code,
            note=note,
        )
        self._add_op(op)

    def move_existing_by_glob(
        self,
        base_rel: str,
        pattern: str,
        dst_dir_rel: str,
        category: str,
        conflict_policy: str = "rename",
        code: bool = False,
        note: str = "",
    ) -> None:
        base_abs = root_join(self.root, base_rel)
        if not base_abs.is_dir():
            return

        dst_dir_abs = root_join(self.root, dst_dir_rel)
        dst_dir_abs.mkdir(parents=True, exist_ok=True)

        for path in sorted(base_abs.glob(pattern)):
            if not path.is_file():
                continue
            src_rel = to_posix_rel(path, self.root)
            dst_rel = f"{dst_dir_rel.rstrip('/')}/{path.name}"
            self.move_file(
                src_rel=src_rel,
                dst_rel=dst_rel,
                category=category,
                conflict_policy=conflict_policy,
                code=code,
                note=note,
            )


def classify_by_rules(stem: str, rules: List[Tuple[str, List[str]]]) -> Optional[str]:
    lowered = stem.lower()
    tokens = set(re.split(r"[^a-z0-9]+", lowered))
    tokens.discard("")

    for domain, keywords in rules:
        for keyword in keywords:
            keyword = keyword.lower()
            if keyword in tokens:
                return domain
            if keyword in lowered:
                return domain
    return None


def build_plan(root: Path, args: argparse.Namespace) -> PlanBuilder:
    plan = PlanBuilder(root)

    # ------------------------------------------------------------------
    # 1. Create target directories
    # ------------------------------------------------------------------
    for rel in CREATE_DIRS:
        plan.mkdir(rel, category="create_target_dirs", note="Planned target directory")

    # ------------------------------------------------------------------
    # 2. Safe root documentation / artifact moves
    # ------------------------------------------------------------------
    for path in sorted(root.iterdir()):
        rel = to_posix_rel(path, root)

        if path.is_file():
            if path.suffix.lower() == ".md" and path.name not in ALLOW_ROOT_MD:
                plan.move_file(
                    rel,
                    f"documents/archive/root_docs/{path.name}",
                    category="root_docs",
                    conflict_policy="rename",
                    note="Root markdown outside allow-list",
                )

            elif path.suffix.lower() == ".txt":
                plan.move_file(
                    rel,
                    f"documents/archive/root_notes/{path.name}",
                    category="root_notes",
                    conflict_policy="rename",
                    note="Root text note",
                )

            elif path.name in ROOT_ARTIFACT_FILES:
                plan.move_file(
                    rel,
                    f"documents/archive/root_artifacts/{path.name}",
                    category="root_artifacts",
                    conflict_policy="rename",
                    note="Root artifact file",
                )

            elif path.name in ROOT_LOG_FILES:
                plan.move_file(
                    rel,
                    f"archive/logs/{path.name}",
                    category="root_logs",
                    conflict_policy="rename",
                    note="Root log file",
                )

        elif path.is_dir():
            if path.name in ROOT_EXPERIMENT_DIRS:
                plan.move_dir(
                    rel,
                    f"experiments/{path.name}",
                    category="root_experiments",
                    conflict_policy="skip",
                    note="Experiment / output directory",
                )

            elif path.name in ROOT_ARCHIVE_DIRS:
                plan.move_dir(
                    rel,
                    f"archive/{path.name}",
                    category="root_archive",
                    conflict_policy="skip",
                    note="Archive / trash directory",
                )

            elif path.name in ROOT_DESIGN_DIRS:
                plan.move_dir(
                    rel,
                    f"design/{path.name}",
                    category="root_design",
                    conflict_policy="skip",
                    note="Design directory",
                )

    for name in ROOT_DESIGN_FILES:
        plan.move_file(
            name,
            f"design/{name}",
            category="root_design",
            conflict_policy="rename",
            note="Design asset",
        )

    # ------------------------------------------------------------------
    # 3. Documents root cleanup
    # ------------------------------------------------------------------
    docs = root / "documents"
    if docs.is_dir():
        for path in sorted(docs.iterdir()):
            rel = to_posix_rel(path, root)
            if path.name in ALLOW_DOCUMENTS_ROOT:
                continue

            if path.name == "archive":
                continue

            if path.is_dir():
                plan.move_dir(
                    rel,
                    f"documents/archive/documents_archive/{path.name}",
                    category="documents_cleanup",
                    conflict_policy="skip",
                    note="Documents root directory outside allow-list",
                )
            else:
                plan.move_file(
                    rel,
                    f"documents/archive/documents_archive/{path.name}",
                    category="documents_cleanup",
                    conflict_policy="rename",
                    note="Documents root file outside allow-list",
                )

    # ------------------------------------------------------------------
    # 4. Backend safe non-code artifact moves
    # ------------------------------------------------------------------
    plan.move_existing_by_glob(
        "backend/log",
        BACKEND_LOG_GLOB,
        "archive/backend_log",
        category="backend_logs",
        conflict_policy="rename",
        note="Backend log file",
    )

    for name in BACKEND_ARTIFACT_FILES:
        plan.move_file(
            f"backend/{name}",
            f"archive/backend_artifacts/{name}",
            category="backend_artifacts",
            conflict_policy="rename",
            note="Backend artifact file",
        )

    for name in BACKEND_DOC_ARTIFACT_FILES:
        plan.move_file(
            f"backend/{name}",
            f"documents/archive/backend_artifacts/{name}",
            category="backend_artifacts",
            conflict_policy="rename",
            note="Backend documentation artifact",
        )

    plan.move_dir(
        "backend/provider_test",
        "experiments/backend_provider_test",
        category="backend_experiments",
        conflict_policy="skip",
        note="Backend provider test outputs",
    )

    # ------------------------------------------------------------------
    # 5. Frontend safe scratch / artifact moves
    # ------------------------------------------------------------------
    web_root = "frontend/web_app"
    web_scratch_patterns = [
        "_audit_*.cjs",
        "_collect_icons.cjs",
        "_gen_lucide.cjs",
        "verify_*.cjs",
        "inspect-playwright.cjs",
        "build_final*.log",
        "build_out*.log",
        "build_log.txt",
        "build_output.txt",
        "bulk_test_output.txt",
        "bulk_test_verbose.txt",
        "logistics_test.txt",
        "staff_test*.txt",
        "standalone_test*.txt",
        "playwright-results.txt",
        "audit-logs-fixed.png",
        "command-center-fixed.png",
        "-w",
        "playwright.config.ts.bak",
        "tsconfig.tsbuildinfo",
    ]

    for pattern in web_scratch_patterns:
        plan.move_existing_by_glob(
            web_root,
            pattern,
            "archive/frontend/web_app_scratch",
            category="frontend_scratch",
            conflict_policy="rename",
            note="Frontend web_app scratch/artifact",
        )

    mobile_root = "frontend/mobile_app"
    mobile_log_patterns = [
        "expo-err.log",
        "expo-start.log",
    ]
    for pattern in mobile_log_patterns:
        plan.move_existing_by_glob(
            mobile_root,
            pattern,
            "archive/frontend/mobile_app_logs",
            category="frontend_logs",
            conflict_policy="rename",
            note="Frontend mobile_app log",
        )

    plan.move_existing_by_glob(
        f"{mobile_root}/scripts",
        "*.log",
        "archive/frontend/mobile_app_scripts_logs",
        category="frontend_logs",
        conflict_policy="rename",
        note="Mobile script log",
    )
    plan.move_existing_by_glob(
        f"{mobile_root}/scripts",
        "*.err",
        "archive/frontend/mobile_app_scripts_logs",
        category="frontend_logs",
        conflict_policy="rename",
        note="Mobile script err",
    )

    plan.move_dir(
        f"{mobile_root}/playwright-report",
        "archive/frontend/mobile_app_playwright_report",
        category="frontend_artifacts",
        conflict_policy="skip",
        note="Mobile Playwright report",
    )
    plan.move_dir(
        f"{mobile_root}/test-output",
        "archive/frontend/mobile_app_test-output",
        category="frontend_artifacts",
        conflict_policy="skip",
        note="Mobile test output",
    )
    plan.move_dir(
        f"{web_root}/coverage",
        "archive/frontend/web_app_coverage",
        category="frontend_artifacts",
        conflict_policy="skip",
        note="Web coverage output",
    )
    plan.move_dir(
        f"{web_root}/test-results",
        "archive/frontend/web_app_test-results",
        category="frontend_artifacts",
        conflict_policy="skip",
        note="Web test results",
    )

    # Move all .bak files under frontend to archive.
    frontend_abs = root / "frontend"
    if frontend_abs.is_dir():
        for path in sorted(frontend_abs.rglob("*.bak")):
            if not path.is_file():
                continue
            rel = to_posix_rel(path, root)
            safe_name = rel.replace("/", "__")
            plan.move_file(
                rel,
                f"archive/frontend/baks/{safe_name}",
                category="frontend_baks",
                conflict_policy="rename",
                note="Backup file under frontend",
            )

    # ------------------------------------------------------------------
    # 6. Scripts safe scratch moves
    # ------------------------------------------------------------------
    scripts_frontend_scratch = [
        "balance.js",
        "countDivs.js",
        "countDivs2.js",
        "linenums.js",
        "listDivs.js",
        "parse.js",
        "patch-vars.js",
        "patch-vars2.js",
        "printLines.js",
        "stackDivs.js",
        "tailwind.config.js",
    ]
    for name in scripts_frontend_scratch:
        plan.move_file(
            f"scripts/frontend/{name}",
            f"archive/scripts_frontend_scratch/{name}",
            category="scripts_scratch",
            conflict_policy="rename",
            note="Scratch frontend script",
        )

    # ------------------------------------------------------------------
    # 7. Optional infrastructure moves
    # ------------------------------------------------------------------
    if args.include_infra:
        for src, dst in INFRA_MOVES:
            plan.move_dir(
                src,
                dst,
                category="infra",
                conflict_policy="skip",
                note="Optional infra consolidation",
            )

    # ------------------------------------------------------------------
    # 8. Optional code moves
    # ------------------------------------------------------------------
    if args.include_code_moves:
        for src, dst in BACKEND_CODE_MOVES:
            plan.move_file(
                src,
                dst,
                category="backend_code_moves",
                conflict_policy="rename",
                code=True,
                note="Explicit code relocation",
            )

        for src, dst in BACKEND_DIR_CODE_MOVES:
            plan.move_dir(
                src,
                dst,
                category="backend_code_moves",
                conflict_policy="skip",
                code=True,
                note="Explicit code directory relocation",
            )

    # ------------------------------------------------------------------
    # 9. Optional backend root shadow moves
    # ------------------------------------------------------------------
    if args.include_root_shadows:
        for name in BACKEND_ROOT_SHADOW_FILES:
            plan.move_file(
                f"backend/{name}",
                f"backend/archive_root_shadows/{name}",
                category="backend_root_shadows",
                conflict_policy="rename",
                code=True,
                note="Backend root shadow module",
            )

    # ------------------------------------------------------------------
    # 10. Optional domain reorganization
    # ------------------------------------------------------------------
    if args.include_domain_reorg:
        add_service_domain_moves(root, plan, args)
        add_controller_domain_moves(root, plan, args)
        add_model_package_moves(root, plan, args)

    return plan


def add_service_domain_moves(root: Path, plan: PlanBuilder, args: argparse.Namespace) -> None:
    services = root / "backend" / "services"
    if not services.is_dir():
        return

    for path in sorted(services.glob("*.py")):
        if path.name == "__init__.py":
            continue

        stem = path.stem
        domain = classify_by_rules(stem, SERVICE_DOMAIN_RULES)

        if not domain:
            if args.allow_triage:
                domain = "_triage"
            else:
                continue

        src_rel = to_posix_rel(path, root)
        dst_rel = f"backend/services/{domain}/{path.name}"

        plan.move_file(
            src_rel,
            dst_rel,
            category="service_domain_reorg",
            conflict_policy="rename",
            code=True,
            note=f"Service domain classification: {domain}",
        )


def add_controller_domain_moves(root: Path, plan: PlanBuilder, args: argparse.Namespace) -> None:
    controllers = root / "backend" / "controllers"
    if not controllers.is_dir():
        return

    for path in sorted(controllers.glob("*.py")):
        if path.name == "__init__.py":
            continue

        stem = path.stem
        group: Optional[str] = None

        if stem.startswith("admin_"):
            group = "admin"
        elif stem.startswith("supplier_"):
            group = "supplier"
        elif stem.startswith("logistics_partner_"):
            group = "logistics"
        else:
            group = classify_by_rules(stem, CONTROLLER_DOMAIN_RULES)

        if not group:
            if args.allow_triage:
                group = "_triage"
            else:
                continue

        src_rel = to_posix_rel(path, root)
        dst_rel = f"backend/controllers/{group}/{path.name}"

        plan.move_file(
            src_rel,
            dst_rel,
            category="controller_domain_reorg",
            conflict_policy="rename",
            code=True,
            note=f"Controller group classification: {group}",
        )


def add_model_package_moves(root: Path, plan: PlanBuilder, args: argparse.Namespace) -> None:
    """
    Convert flat model modules into packages without changing import names.

    Example:
      backend/models/finance.py
      -> backend/models/finance/__init__.py

    This preserves imports like:
      from backend.models.finance import ...
      from models.finance import ...
    """
    models = root / "backend" / "models"
    if not models.is_dir():
        return

    for path in sorted(models.glob("*.py")):
        if path.name == "__init__.py":
            continue

        stem = path.stem
        target_dir = models / stem
        if target_dir.exists():
            continue

        src_rel = to_posix_rel(path, root)
        dst_rel = f"backend/models/{stem}/__init__.py"

        plan.mkdir(f"backend/models/{stem}", category="model_package_reorg", note="Model package directory")
        plan.move_file(
            src_rel,
            dst_rel,
            category="model_package_reorg",
            conflict_policy="skip",
            code=True,
            note="Convert flat model module to package preserving import path",
        )


# ============================================================================
# IMPORT REWRITE SUPPORT
# ============================================================================

def backend_module_from_path(path: Path, backend: Path) -> Optional[str]:
    try:
        rel = path.relative_to(backend)
    except ValueError:
        return None

    parts = list(rel.parts)
    if not parts:
        return None

    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].removesuffix(".py")

    if not parts:
        return None

    return ".".join(parts)


def build_import_mapping(root: Path, manifest: MigrationManifest) -> Dict[str, str]:
    backend = root / "backend"
    mapping: Dict[str, str] = {}

    for op in manifest.ops:
        if op.status != "done":
            continue
        if not op.code:
            continue
        if not op.src or not op.dst:
            continue

        src_abs = root_join(root, op.src)
        dst_abs = root_join(root, op.dst)

        if op.type == "move_file":
            if not op.src.endswith(".py") or not op.dst.endswith(".py"):
                continue

            old_mod = backend_module_from_path(src_abs, backend)
            new_mod = backend_module_from_path(dst_abs, backend)

            if old_mod and new_mod and old_mod != new_mod:
                mapping[old_mod] = new_mod

        elif op.type == "move_dir":
            old_mod = backend_module_from_path(src_abs / "__init__.py", backend)
            new_mod = backend_module_from_path(dst_abs / "__init__.py", backend)

            if old_mod and new_mod and old_mod != new_mod:
                mapping[old_mod] = new_mod

    return mapping


def rewrite_content(content: str, mapping: Dict[str, str]) -> str:
    # Sort by length descending so longer module paths are replaced first.
    items = sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True)

    for old, new in items:
        old_esc = re.escape(old)

        # from old import x
        # from old.sub import y
        content = re.sub(
            rf"(?m)^([ \t]*from[ \t]+){old_esc}([ \t]+import\b|\.|$)",
            lambda m: f"{m.group(1)}{new}{m.group(2)}",
            content,
        )

        # import old
        # import old as x
        # import old.sub
        # import old, other
        content = re.sub(
            rf"(?m)^([ \t]*import[ \t]+){old_esc}([ \t,]|$)",
            lambda m: f"{m.group(1)}{new}{m.group(2)}",
            content,
        )

    return content


def snapshot_file(root: Path, manifest: MigrationManifest, path: Path) -> None:
    rel = to_posix_rel(path, root)
    if rel in manifest.content_snapshots:
        return

    snapshot_root = migration_dir(root) / CONTENT_SNAPSHOT_DIR_NAME
    snapshot_path = snapshot_root / rel
    ensure_parent(snapshot_path)
    shutil.copy2(path, snapshot_path)

    manifest.content_snapshots[rel] = to_posix_rel(snapshot_path, root)


def rewrite_imports(root: Path, manifest: MigrationManifest) -> int:
    mapping = build_import_mapping(root, manifest)
    if not mapping:
        log("No Python module mapping found; skipping import rewrite.")
        return 0

    log("Import mapping:")
    for old, new in sorted(mapping.items()):
        log(f"  {old} -> {new}")

    backend = root / "backend"
    changed = 0

    for path in sorted(backend.rglob("*.py")):
        if not path.is_file():
            continue

        try:
            original = path.read_text(encoding="utf-8")
        except Exception as exc:
            warn(f"Could not read {path}: {exc}")
            continue

        updated = rewrite_content(original, mapping)
        if updated != original:
            snapshot_file(root, manifest, path)
            path.write_text(updated, encoding="utf-8")
            changed += 1
            log(f"Rewrote imports in: {to_posix_rel(path, root)}")

    return changed


# ============================================================================
# EXECUTION
# ============================================================================

def execute_operation(root: Path, op: Operation, manifest: MigrationManifest) -> None:
    src_abs = root_join(root, op.src) if op.src else None
    dst_abs = root_join(root, op.dst)

    try:
        if op.type == "mkdir":
            if dst_abs.exists():
                op.status = "skipped"
                op.message = "Already exists"
                return

            dst_abs.mkdir(parents=True, exist_ok=True)
            op.status = "done"
            op.message = "Created directory"
            return

        if op.type in ("move_file", "move_dir"):
            if not src_abs or not src_abs.exists():
                op.status = "skipped"
                op.message = "Source missing"
                return

            if op.type == "move_file":
                op.src_sha256 = sha256_file(src_abs)
                op.size = file_size(src_abs)

            if dst_abs.exists():
                if op.type == "move_file":
                    dst_hash = sha256_file(dst_abs)
                    if dst_hash == op.src_sha256:
                        op.status = "skipped"
                        op.message = "Destination already has identical file"
                        return

                if op.conflict_policy == "skip":
                    op.status = "skipped"
                    op.message = "Destination exists and conflict_policy=skip"
                    return

                dst_abs = unique_destination(dst_abs)
                op.dst = to_posix_rel(dst_abs, root)
                op.message = "Destination existed; renamed incoming file"

            ensure_parent(dst_abs)
            shutil.move(str(src_abs), str(dst_abs))

            if op.type == "move_file":
                op.dst_sha256 = sha256_file(dst_abs)
                if op.src_sha256 and op.dst_sha256 != op.src_sha256:
                    op.status = "failed"
                    op.message = "Post-move hash mismatch"
                    return

            op.status = "done"
            if not op.message:
                op.message = "Moved"
            return

        op.status = "failed"
        op.message = f"Unknown operation type: {op.type}"

    except Exception as exc:
        op.status = "failed"
        op.message = str(exc)


def apply_plan(root: Path, manifest: MigrationManifest, args: argparse.Namespace) -> None:
    log("Applying migration plan...")

    for op in manifest.ops:
        execute_operation(root, op, manifest)
        save_manifest(root, manifest)

        status_icon = {
            "done": "OK",
            "skipped": "SKIP",
            "failed": "FAIL",
        }.get(op.status, "?")

        src = op.src or "-"
        log(f"[{status_icon}] {op.category:<28} {src} -> {op.dst} :: {op.message}")

        if op.status == "failed" and args.stop_on_error:
            error("Stopping because --stop-on-error is enabled.")
            manifest.completed = False
            save_manifest(root, manifest)
            sys.exit(4)

    if args.include_code_moves or args.include_domain_reorg or args.include_root_shadows:
        changed = rewrite_imports(root, manifest)
        log(f"Import rewriting completed. Files changed: {changed}")

    manifest.completed = True
    save_manifest(root, manifest)
    log("Migration apply completed.")
    log(f"Manifest: {latest_manifest_path(root)}")


# ============================================================================
# REVERSE
# ============================================================================

def reverse_manifest(root: Path, manifest: MigrationManifest) -> None:
    log(f"Reversing migration: {manifest.migration_id}")

    # Reverse file/dir moves in reverse order.
    for op in reversed(manifest.ops):
        if op.type not in ("move_file", "move_dir"):
            continue
        if op.status != "done":
            continue
        if not op.src:
            continue

        src_abs = root_join(root, op.src)
        dst_abs = root_join(root, op.dst)

        try:
            if not dst_abs.exists():
                op.status = "skipped"
                op.message = "Reverse skipped: destination missing"
                log(f"[SKIP] {op.dst} missing; cannot reverse to {op.src}")
                continue

            if src_abs.exists():
                op.status = "failed"
                op.message = "Reverse failed: original source already exists"
                log(f"[FAIL] {op.src} already exists; cannot reverse {op.dst}")
                continue

            ensure_parent(src_abs)
            shutil.move(str(dst_abs), str(src_abs))
            op.status = "reversed"
            op.message = "Reversed"
            log(f"[OK] reversed {op.dst} -> {op.src}")

        except Exception as exc:
            op.status = "failed"
            op.message = f"Reverse error: {exc}"
            log(f"[FAIL] reverse {op.dst} -> {op.src}: {exc}")

        save_manifest(root, manifest)

    # Restore content snapshots after files are back.
    if manifest.content_snapshots:
        log("Restoring modified file contents from snapshots...")
        for rel, snap_rel in manifest.content_snapshots.items():
            target = root_join(root, rel)
            snap = root_join(root, snap_rel)
            try:
                if snap.exists():
                    ensure_parent(target)
                    shutil.copy2(snap, target)
                    log(f"Restored content: {rel}")
                else:
                    warn(f"Snapshot missing: {snap_rel}")
            except Exception as exc:
                warn(f"Could not restore {rel}: {exc}")

    # Remove directories created by this migration if empty.
    for op in reversed(manifest.ops):
        if op.type != "mkdir" or op.status != "done":
            continue

        dir_abs = root_join(root, op.dst)
        try:
            if dir_abs.is_dir() and not any(dir_abs.iterdir()):
                dir_abs.rmdir()
                op.status = "reversed"
                op.message = "Removed empty created directory"
                log(f"[OK] removed empty dir {op.dst}")
        except Exception as exc:
            warn(f"Could not remove dir {op.dst}: {exc}")

    manifest.completed = False
    save_manifest(root, manifest)
    log("Reverse completed.")


# ============================================================================
# DRY RUN
# ============================================================================

def print_dry_run(root: Path, plan: PlanBuilder) -> None:
    log("=" * 100)
    log("DRY RUN — no files will be moved")
    log("=" * 100)

    counts: Dict[str, int] = {}
    for op in plan.ops:
        counts[op.category] = counts.get(op.category, 0) + 1

    log("Planned operation counts:")
    for category, count in sorted(counts.items()):
        log(f"  {category:<32} {count}")

    log("-" * 100)

    for op in plan.ops:
        src = op.src or "-"
        log(f"[{op.type:<9}] {op.category:<28} {src} -> {op.dst}")
        if op.note:
            log(f"             note: {op.note}")

    dry_path = migration_dir(root) / DRY_RUN_PLAN_NAME
    migration_dir(root).mkdir(parents=True, exist_ok=True)
    data = {
        "generated_at": utc_now_iso(),
        "root": str(root),
        "ops": [op.to_dict() for op in plan.ops],
    }
    dry_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    log("-" * 100)
    log(f"Dry-run plan written to: {dry_path}")
    log("Run with --apply to perform the migration.")


# ============================================================================
# GIT PREFLIGHT
# ============================================================================

def git_preflight(root: Path, args: argparse.Namespace) -> None:
    git_dir = root / ".git"
    if not git_dir.exists():
        warn("No .git directory found. Skipping git clean check.")
        return

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            warn("git status failed. Skipping git clean check.")
            return

        if result.stdout.strip():
            warn("Git working tree is not clean.")
            warn("Commit or stash changes before applying migration.")
            if not args.allow_dirty:
                error("Use --allow-dirty to override, preferably after committing.")
                sys.exit(5)

    except FileNotFoundError:
        warn("git executable not found. Skipping git clean check.")


# ============================================================================
# MAIN
# ============================================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safe ZOZI structure migration script with backup and reverse support."
    )

    parser.add_argument("--root", default=None, help="Repository root. Default: auto-detect.")
    parser.add_argument("--apply", action="store_true", help="Apply migration. Default is dry-run.")
    parser.add_argument("--reverse", action="store_true", help="Reverse latest or specified manifest.")
    parser.add_argument("--manifest", default=None, help="Manifest file to reverse.")

    parser.add_argument(
        "--backup-root",
        default=None,
        help="Backup root directory. Default: <project_parent>/zozi_structure_backups",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backup. Dangerous. Requires --force-no-backup.",
    )
    parser.add_argument(
        "--force-no-backup",
        action="store_true",
        help="Acknowledge that you are applying without backup.",
    )
    parser.add_argument(
        "--full-backup",
        action="store_true",
        help="Backup everything, including node_modules/.git/etc. Large and slow.",
    )
    parser.add_argument(
        "--use-robocopy",
        action="store_true",
        help="Use robocopy on Windows for backup.",
    )

    parser.add_argument(
        "--include-code-moves",
        action="store_true",
        help="Enable explicit Python code relocations.",
    )
    parser.add_argument(
        "--include-domain-reorg",
        action="store_true",
        help="Enable service/controller/model domain reorganization.",
    )
    parser.add_argument(
        "--include-root-shadows",
        action="store_true",
        help="Move backend root shadow modules into backend/archive_root_shadows/.",
    )
    parser.add_argument(
        "--include-infra",
        action="store_true",
        help="Move monitoring/ and nginx/ into infra/.",
    )
    parser.add_argument(
        "--allow-triage",
        action="store_true",
        help="Move unclassified service/controller files into _triage domains.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow apply even if git working tree is dirty.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop applying if any operation fails.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = find_repo_root(args.root)

    log(f"Repository root: {root}")

    if args.reverse:
        manifest_path = Path(args.manifest) if args.manifest else latest_manifest_path(root)
        if not manifest_path.exists():
            error(f"Manifest not found: {manifest_path}")
            return 2

        manifest = load_manifest(manifest_path)
        reverse_manifest(root, manifest)
        return 0

    plan = build_plan(root, args)

    if not args.apply:
        print_dry_run(root, plan)
        return 0

    # Apply mode.
    git_preflight(root, args)

    if args.no_backup and not args.force_no_backup:
        error("--no-backup requires --force-no-backup.")
        return 2

    backup_path: Optional[Path] = None
    if not args.no_backup:
        backup_root = Path(args.backup_root) if args.backup_root else default_backup_root(root)
        backup_path = backup_project(
            root=root,
            backup_root=backup_root,
            full_backup=args.full_backup,
            use_robocopy=args.use_robocopy,
        )
    else:
        warn("Backup disabled by user. This is dangerous.")

    manifest = MigrationManifest(
        migration_id=now_stamp(),
        started_at=utc_now_iso(),
        root=str(root),
        backup_path=str(backup_path) if backup_path else None,
        args=vars(args),
        ops=plan.ops,
    )

    save_manifest(root, manifest)
    log(f"Manifest initialized: {latest_manifest_path(root)}")

    apply_plan(root, manifest, args)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())