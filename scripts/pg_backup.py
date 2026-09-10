"""ZOZI NEON production backup script.

Implements full pg_dump backups with WAL archiving support, 30-day retention,
and restore verification via pg_restore --list.

Laws 215-220: Production validation — backup/restore is a deployment prerequisite.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


DEFAULT_RETENTION_DAYS = 30
PG_DUMP_FORMAT = "custom"  # .dump format for pg_restore compatibility


def get_backup_dir() -> Path:
    """Return the root backup directory, creating it if needed."""
    backup_dir = Path(os.environ.get("ZOZI_BACKUP_DIR", "/var/backups/zozi"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_wal_dir() -> Path:
    """Return the WAL archive directory."""
    wal_dir = Path(os.environ.get("ZOZI_WAL_DIR", "/var/backups/zozi/wal"))
    wal_dir.mkdir(parents=True, exist_ok=True)
    return wal_dir


def pg_dump(
    db_url: str,
    output_path: Path,
    format: str = PG_DUMP_FORMAT,
) -> None:
    """Run pg_dump to create a full database backup."""
    cmd = [
        "pg_dump",
        "--format", format,
        "--file", str(output_path),
        "--verbose",
        "--no-owner",
        "--no-privileges",
        db_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pg_dump failed: {result.stderr}")


def verify_backup(backup_path: Path) -> bool:
    """Verify backup integrity using pg_restore --list."""
    if not backup_path.exists():
        return False
    cmd = ["pg_restore", "--list", str(backup_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and len(result.stdout.strip().splitlines()) > 0


def enforce_retention(backup_dir: Path, retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
    """Remove backup files older than retention_days. Returns count removed."""
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for f in backup_dir.glob("zozi_backup_*.dump"):
        try:
            timestamp_str = f.stem.replace("zozi_backup_", "")
            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            if file_time < cutoff:
                f.unlink()
                removed += 1
        except ValueError:
            continue
    return removed


def configure_wal_archiving(data_dir: str) -> None:
    """Verify WAL archiving is configured in NEON."""
    archive_dir = get_wal_dir()
    cmd = [
        "psql",
        "--no-align",
        "--tuples-only",
        "--command", "SHOW archive_mode;",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if "on" not in result.stdout.lower():
        print("WARNING: archive_mode is not 'on'. WAL archiving may not be configured.")
        print(f"  Add to postgresql.conf: archive_mode = on")
        print(f"  archive_command = 'cp %p {archive_dir}/%f'")
    else:
        print(f"WAL archiving enabled. Archive target: {archive_dir}")


def run_backup(
    db_url: str,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    verify: bool = True,
) -> Path:
    """Execute a full backup with optional verification and retention enforcement."""
    backup_dir = get_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"zozi_backup_{timestamp}.dump"
    output_path = backup_dir / filename

    print(f"[{datetime.now().isoformat()}] Starting backup: {filename}")
    pg_dump(db_url, output_path)
    print(f"  Backup written: {output_path} ({output_path.stat().st_size} bytes)")

    if verify:
        print("  Verifying backup integrity...")
        if verify_backup(output_path):
            print("  Verification PASSED")
        else:
            print("  ERROR: Backup verification FAILED", file=sys.stderr)
            output_path.unlink(missing_ok=True)
            raise RuntimeError("Backup verification failed — file removed")

    removed = enforce_retention(backup_dir, retention_days)
    if removed:
        print(f"  Retention: removed {removed} expired backup(s)")

    print(f"[{datetime.now().isoformat()}] Backup complete.")
    return output_path


def restore_backup(backup_path: Path, db_url: str, clean: bool = False) -> None:
    """Restore a backup to the target database."""
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    print(f"Restoring {backup_path}...")
    cmd = [
        "pg_restore",
        "--verbose",
        "--no-owner",
        "--no-privileges",
        "--dbname", db_url,
    ]
    if clean:
        cmd.append("--clean")
    cmd.append(str(backup_path))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pg_restore failed: {result.stderr}")
    print("Restore complete.")


def list_backups() -> list[Path]:
    """List all backup files sorted by age (newest first)."""
    backup_dir = get_backup_dir()
    backups = sorted(backup_dir.glob("zozi_backup_*.dump"), reverse=True)
    return backups


def main() -> int:
    parser = argparse.ArgumentParser(description="ZOZI NEON backup tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # backup
    backup_parser = subparsers.add_parser("backup", help="Run a full backup")
    backup_parser.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    backup_parser.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    backup_parser.add_argument("--no-verify", action="store_true")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore from backup")
    restore_parser.add_argument("--file", type=str, required=True, help="Path to .dump file")
    restore_parser.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    restore_parser.add_argument("--clean", action="store_true")

    # list
    subparsers.add_parser("list", help="List available backups")

    # verify
    verify_parser = subparsers.add_parser("verify", help="Verify a backup file")
    verify_parser.add_argument("--file", type=str, required=True)

    # wal-check
    subparsers.add_parser("wal-check", help="Check WAL archiving configuration")

    args = parser.parse_args()

    if args.command == "backup":
        if not args.db_url:
            print("ERROR: --db-url or DATABASE_URL required", file=sys.stderr)
            return 1
        try:
            run_backup(args.db_url, args.retention_days, verify=not args.no_verify)
            return 0
        except RuntimeError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    elif args.command == "restore":
        if not args.db_url:
            print("ERROR: --db-url or DATABASE_URL required", file=sys.stderr)
            return 1
        try:
            restore_backup(Path(args.file), args.db_url, args.clean)
            return 0
        except (RuntimeError, FileNotFoundError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    elif args.command == "list":
        backups = list_backups()
        if not backups:
            print("No backups found.")
            return 0
        for b in backups:
            size_mb = b.stat().st_size / (1024 * 1024)
            print(f"  {b.name}  ({size_mb:.1f} MB)")
        return 0

    elif args.command == "verify":
        path = Path(args.file)
        if verify_backup(path):
            print(f"OK: {path.name} is valid")
            return 0
        else:
            print(f"FAIL: {path.name} is corrupt or invalid", file=sys.stderr)
            return 1

    elif args.command == "wal-check":
        configure_wal_archiving("")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
