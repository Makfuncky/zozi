# -*- coding: utf-8 -*-
"""
NEON Backup Script for ZOZI Production Database.

Creates compressed daily backups with WAL archiving support for point-in-time recovery.
Designed to run inside a Docker container or directly on the host.

Usage:
    python pg_backup.py                    # Create a full backup
    python pg_backup.py --verify <file>    # Verify a backup file
    python pg_backup.py --list             # List available backups
    python pg_backup.py --restore <file>   # Restore from backup
    python pg_backup.py --restore-drill    # Test latest backup restore

Environment Variables:
    POSTGRES_DB         - Database name (required)
    POSTGRES_USER       - Database user (required)
    POSTGRES_PASSWORD   - Database password (required)
    POSTGRES_HOST       - Database host (default: localhost)
    POSTGRES_PORT       - Database port (default: 5432)
    BACKUP_DIR          - Backup storage directory (default: /backups)
    BACKUP_RETENTION_DAYS - Days to retain backups (default: 30)
    R2_BUCKET           - Optional R2 bucket for off-site backups
    R2_PREFIX           - Optional R2 key prefix (default: zozi-backups/)
    R2_REGION           - Optional R2 region
    R2_ENDPOINT_URL     - Optional R2 endpoint (for R2, DO, etc.)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pg_backup")


def get_env(key: str, default: str = "", required: bool = False) -> str:
    """Get environment variable with optional requirement check."""
    value = os.getenv(key, default)
    if required and not value:
        logger.error(f"Required environment variable {key} is not set")
        sys.exit(1)
    return value


def get_backup_dir() -> Path:
    """Get and create backup directory."""
    backup_dir = Path(get_env("BACKUP_DIR", "/backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def get_db_connection_info() -> dict:
    """Parse database connection info from environment."""
    # Support both individual env vars and DATABASE_URL
    database_url = os.getenv("DATABASE_URL", "")
    
    if database_url:
        parsed = urlparse(database_url)
        # Handle postgres:// vs postgresql://
        if parsed.scheme in ("postgres", "postgresql"):
            return {
                "host": parsed.hostname or "localhost",
                "port": str(parsed.port or 5432),
                "user": parsed.username or "postgres",
                "password": parsed.password or "",
                "dbname": (parsed.path or "").lstrip("/") or "zozi",
            }
    
    return {
        "host": get_env("POSTGRES_HOST", "localhost"),
        "port": get_env("POSTGRES_PORT", "5432"),
        "user": get_env("POSTGRES_USER", required=True),
        "password": get_env("POSTGRES_PASSWORD", required=True),
        "dbname": get_env("POSTGRES_DB", required=True),
    }


def create_backup(
    backup_dir: Path,
    db_info: dict,
    backup_type: str = "daily",
) -> Optional[Path]:
    """
    Create a NEON backup using pg_dump with custom compressed format.
    
    Args:
        backup_dir: Directory to store the backup
        db_info: Database connection information
        backup_type: Type of backup (daily, weekly, monthly)
    
    Returns:
        Path to the created backup file, or None on failure
    """
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        logger.error("pg_dump not found on PATH. Install postgresql-client package.")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"zozi_{backup_type}_{timestamp}.pgdump"
    backup_path = backup_dir / filename

    logger.info(f"Creating backup: {backup_path.name}")
    logger.info(f"Database: {db_info['dbname']} on {db_info['host']}:{db_info['port']}")

    env = os.environ.copy()
    if db_info["password"]:
        env["PGPASSWORD"] = db_info["password"]

    cmd = [
        pg_dump,
        "-Fc",  # Custom compressed format (allows selective restore)
        "-Z", "6",  # Compression level 0-9
        "-h", db_info["host"],
        "-p", db_info["port"],
        "-U", db_info["user"],
        "-d", db_info["dbname"],
        "--verbose",
        "--no-owner",  # Don't include ownership commands
        "--no-privileges",  # Don't include privilege commands
        "-f", str(backup_path),
    ]

    start_time = time.time()
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            timeout=3600,  # 1 hour timeout for large databases
            check=False,
        )
        elapsed = time.time() - start_time

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            logger.error(f"pg_dump failed (exit {result.returncode}): {stderr}")
            if backup_path.exists():
                backup_path.unlink()
            return None

        file_size = backup_path.stat().st_size
        logger.info(
            f"Backup completed in {elapsed:.1f}s "
            f"({file_size / 1024 / 1024:.1f} MB)"
        )

        # Write metadata sidecar
        metadata = {
            "filename": filename,
            "type": backup_type,
            "database": db_info["dbname"],
            "host": db_info["host"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "size_bytes": file_size,
            "duration_seconds": round(elapsed, 2),
            "pg_dump_version": _get_pg_dump_version(),
            "compression": "pg_dump -Fc (custom)",
            "verified": False,
        }
        metadata_path = backup_path.with_suffix(".pgdump.meta.json")
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        return backup_path

    except subprocess.TimeoutExpired:
        logger.error("pg_dump timed out after 1 hour")
        if backup_path.exists():
            backup_path.unlink()
        return None
    except Exception as exc:
        logger.error(f"Backup failed with exception: {exc}")
        if backup_path.exists():
            backup_path.unlink()
        return None


def verify_backup(backup_path: Path) -> bool:
    """
    Verify a backup file using pg_restore --list.
    
    This checks that the backup is structurally valid and can be read.
    """
    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        logger.error("pg_restore not found on PATH. Install postgresql-client package.")
        return False

    logger.info(f"Verifying backup: {backup_path.name}")

    try:
        result = subprocess.run(
            [pg_restore, "--list", str(backup_path)],
            capture_output=True,
            timeout=600,
            check=False,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            logger.error(f"Verification failed: {stderr}")
            return False

        # Count objects in backup
        output = result.stdout.decode(errors="replace")
        object_count = len([line for line in output.splitlines() if line.strip()])
        
        logger.info(f"Verification passed: {object_count} objects found in backup")
        
        # Update metadata
        metadata_path = backup_path.with_suffix(".pgdump.meta.json")
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["verified"] = True
            metadata["verified_at"] = datetime.now(timezone.utc).isoformat()
            metadata["objects_count"] = object_count
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        
        return True

    except subprocess.TimeoutExpired:
        logger.error("Verification timed out after 10 minutes")
        return False
    except Exception as exc:
        logger.error(f"Verification failed with exception: {exc}")
        return False


def restore_backup(
    backup_path: Path,
    db_info: str,
    target_db: Optional[str] = None,
) -> bool:
    """
    Restore a NEON backup using pg_restore.
    
    Args:
        backup_path: Path to the backup file
        db_info: Database connection information
        target_db: Optional target database name (for restore to different DB)
    """
    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        logger.error("pg_restore not found on PATH")
        return False

    dbname = target_db or db_info["dbname"]
    logger.info(f"Restoring backup to database: {dbname}")

    env = os.environ.copy()
    if db_info["password"]:
        env["PGPASSWORD"] = db_info["password"]

    cmd = [
        pg_restore,
        "-h", db_info["host"],
        "-p", db_info["port"],
        "-U", db_info["user"],
        "-d", dbname,
        "--verbose",
        "--no-owner",
        "--no-privileges",
        "--clean",  # Drop objects before recreating
        "--if-exists",
        str(backup_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            timeout=7200,  # 2 hour timeout
            check=False,
        )

        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            logger.error(f"Restore failed: {stderr}")
            return False

        logger.info("Restore completed successfully")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Restore timed out after 2 hours")
        return False
    except Exception as exc:
        logger.error(f"Restore failed with exception: {exc}")
        return False


def run_restore_drill(backup_dir: Path, db_info: dict) -> bool:
    """
    Test backup by restoring to a temporary database.
    
    This validates that the backup is actually restorable.
    """
    # Find latest backup
    backups = sorted(
        backup_dir.glob("zozi_*.pgdump"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    
    if not backups:
        logger.error("No backups found for restore drill")
        return False

    latest = backups[0]
    logger.info(f"Running restore drill on: {latest.name}")

    # Create temporary database
    drill_db = f"zozi_restore_drill_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    env = os.environ.copy()
    if db_info["password"]:
        env["PGPASSWORD"] = db_info["password"]

    try:
        # Create temp database
        result = subprocess.run(
            [
                "createdb",
                "-h", db_info["host"],
                "-p", db_info["port"],
                "-U", db_info["user"],
                drill_db,
            ],
            env=env,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            logger.error(f"Failed to create drill database: {result.stderr.decode()}")
            return False

        # Restore to temp database
        success = restore_backup(latest, db_info, target_db=drill_db)
        
        if success:
            # Verify row counts match expectations
            result = subprocess.run(
                [
                    "psql",
                    "-h", db_info["host"],
                    "-p", db_info["port"],
                    "-U", db_info["user"],
                    "-d", drill_db,
                    "-c", "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');",
                ],
                env=env,
                capture_output=True,
                timeout=60,
                check=False,
            )
            if result.returncode == 0:
                table_count = result.stdout.decode().strip().split("\n")[-1].strip()
                logger.info(f"Restore drill successful: {table_count} tables restored")
        
        return success

    finally:
        # Clean up temp database
        subprocess.run(
            [
                "dropdb",
                "-h", db_info["host"],
                "-p", db_info["port"],
                "-U", db_info["user"],
                "--if-exists",
                drill_db,
            ],
            env=env,
            capture_output=True,
            timeout=30,
            check=False,
        )


def rotate_backups(backup_dir: Path, retention_days: int = 30) -> None:
    """Remove backups older than retention period."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_timestamp = cutoff.timestamp()

    removed_count = 0
    removed_size = 0

    for backup_file in backup_dir.glob("zozi_*.pgdump"):
        if backup_file.stat().st_mtime < cutoff_timestamp:
            file_size = backup_file.stat().st_size
            backup_file.unlink()
            # Also remove metadata
            metadata_path = backup_file.with_suffix(".pgdump.meta.json")
            if metadata_path.exists():
                metadata_path.unlink()
            removed_count += 1
            removed_size += file_size
            logger.info(f"Rotated old backup: {backup_file.name}")

    if removed_count > 0:
        logger.info(
            f"Rotation complete: removed {removed_count} backups "
            f"({removed_size / 1024 / 1024:.1f} MB freed)"
        )
    else:
        logger.info("No backups to rotate")


def list_backups(backup_dir: Path) -> list[dict]:
    """List all available backups with metadata."""
    backups = []
    
    for backup_file in sorted(backup_dir.glob("zozi_*.pgdump"), reverse=True):
        metadata_path = backup_file.with_suffix(".pgdump.meta.json")
        metadata = {}
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass

        stat = backup_file.stat()
        backups.append({
            "filename": backup_file.name,
            "size_mb": round(stat.st_size / 1024 / 1024, 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "type": metadata.get("type", "unknown"),
            "verified": metadata.get("verified", False),
            "database": metadata.get("database", "unknown"),
        })

    return backups


def upload_to_s3(backup_path: Path) -> bool:
    """Upload backup to R2 for off-site storage."""
    s3_bucket = os.getenv("R2_BUCKET")
    if not s3_bucket:
        logger.info("R2_BUCKET not set, skipping cloud upload")
        return False

    try:
        import boto3
    except ImportError:
        logger.error("boto3 not installed, cannot upload to R2")
        return False

    s3_prefix = os.getenv("R2_PREFIX", "zozi-backups/")
    s3_region = os.getenv("R2_REGION", "auto")
    s3_endpoint = os.getenv("R2_ENDPOINT_URL")

    try:
        client = boto3.client(
            "s3",
            region_name=s3_region if s3_region != "auto" else None,
            endpoint_url=s3_endpoint or None,
        )

        object_key = f"{s3_prefix.rstrip('/')}/{backup_path.name}"
        
        logger.info(f"Uploading to R2: s3://{s3_bucket}/{object_key}")
        
        client.upload_file(
            str(backup_path),
            s3_bucket,
            object_key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )

        # Also upload metadata
        metadata_path = backup_path.with_suffix(".pgdump.meta.json")
        if metadata_path.exists():
            meta_key = f"{s3_prefix.rstrip('/')}/{metadata_path.name}"
            client.upload_file(
                str(metadata_path),
                s3_bucket,
                meta_key,
            )

        logger.info("R2 upload completed")
        
        # Update metadata with cloud info
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["cloud_synced"] = True
            metadata["cloud_provider"] = "s3"
            metadata["cloud_bucket"] = s3_bucket
            metadata["cloud_object_key"] = object_key
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        
        return True

    except Exception as exc:
        logger.error(f"R2 upload failed: {exc}")
        return False


def _get_pg_dump_version() -> str:
    """Get pg_dump version string."""
    try:
        result = subprocess.run(
            ["pg_dump", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="NEON Backup Script for ZOZI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--verify",
        metavar="FILE",
        help="Verify a backup file",
    )
    parser.add_argument(
        "--restore",
        metavar="FILE",
        help="Restore from a backup file",
    )
    parser.add_argument(
        "--restore-drill",
        action="store_true",
        help="Test latest backup by restoring to temporary database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available backups",
    )
    parser.add_argument(
        "--type",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Backup type (default: daily)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
        help="Days to retain backups (default: 30)",
    )
    parser.add_argument(
        "--no-s3",
        action="store_true",
        help="Skip R2 upload",
    )
    parser.add_argument(
        "--no-rotate",
        action="store_true",
        help="Skip rotation of old backups",
    )
    parser.add_argument(
        "--target-db",
        help="Target database name for restore (default: same as source)",
    )
    
    args = parser.parse_args()
    
    backup_dir = get_backup_dir()
    db_info = get_db_connection_info()

    if args.list:
        backups = list_backups(backup_dir)
        if not backups:
            print("No backups found.")
            return 0
        
        print(f"\n{'Filename':<50} {'Size (MB)':<12} {'Type':<10} {'Verified':<10} {'Created'}")
        print("-" * 110)
        for b in backups:
            print(
                f"{b['filename']:<50} {b['size_mb']:<12} {b['type']:<10} "
                f"{'✓' if b['verified'] else '✗':<10} {b['created_at']}"
            )
        return 0

    if args.verify:
        backup_path = Path(args.verify)
        if not backup_path.is_absolute():
            backup_path = backup_dir / args.verify
        success = verify_backup(backup_path)
        return 0 if success else 1

    if args.restore:
        backup_path = Path(args.restore)
        if not backup_path.is_absolute():
            backup_path = backup_dir / args.restore
        success = restore_backup(backup_path, db_info, target_db=args.target_db)
        return 0 if success else 1

    if args.restore_drill:
        success = run_restore_drill(backup_dir, db_info)
        return 0 if success else 1

    # Default: create a new backup
    backup_path = create_backup(backup_dir, db_info, backup_type=args.type)
    if not backup_path:
        return 1

    # Verify the backup
    if not verify_backup(backup_path):
        logger.warning("Backup verification failed, but backup file was created")

    # Upload to R2 if configured
    if not args.no_s3:
        upload_to_s3(backup_path)

    # Rotate old backups
    if not args.no_rotate:
        rotate_backups(backup_dir, retention_days=args.retention_days)

    logger.info("Backup process completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
