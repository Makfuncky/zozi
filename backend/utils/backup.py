
"""
Database backup utilities.

Supports two backends:
  • SQLite  — hot backup via sqlite3.connect(...).backup()
  • PostgreSQL — pg_dump -Fc (custom compressed format)

Backups are stored in <backup_dir>/ and rotated to keep at most
<backup_max_files> files. Optional S3 replication is available for
off-site storage, and each backup can be verified locally plus exercised
through a restore drill.
"""
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class BackupManager:
    """Manage periodic database backups."""

    def __init__(self) -> None:
        from utils.config import settings

        self._backup_dir = Path(settings.backup_dir)
        self._max_files = max(1, int(settings.backup_max_files or settings.max_backups or 48))
        self._db_url: str = settings.database_url
        self._verify_on_create = settings.backup_verify_on_create
        self._cloud_enabled = settings.backup_cloud_enabled
        self._cloud_provider = settings.backup_cloud_provider
        self._s3_bucket = settings.backup_s3_bucket
        self._s3_prefix = settings.backup_s3_prefix.strip("/")
        self._s3_region = settings.backup_s3_region
        self._s3_endpoint_url = settings.backup_s3_endpoint_url
        self._s3_access_key_id = settings.backup_s3_access_key_id
        self._s3_secret_access_key = settings.backup_s3_secret_access_key

    # ── Public API ────────────────────────────────────────────────────────────

    def create_backup(self) -> Optional[Path]:
        """
        Create a new backup file.

        Returns the Path of the created backup, or None on failure.
        """
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        try:
            if self._is_sqlite():
                path = self._backup_sqlite()
            else:
                path = self._backup_postgres()
        except Exception as exc:
            logger.error("Backup failed: %s", exc)
            return None

        metadata: dict[str, Any] = {
            "verified": False,
            "cloud_synced": False,
        }
        if self._verify_on_create:
            verification = self.verify_backup(path)
            metadata.update(verification)

        if self._cloud_enabled:
            cloud_result = self._upload_to_cloud(path)
            metadata.update(cloud_result)

        self._write_metadata(path, metadata)

        self._rotate_old_backups()
        logger.info("Backup created: %s", path)
        return path

    def list_backups(self) -> list[dict]:
        """Return metadata for all backup files, newest first."""
        if not self._backup_dir.exists():
            return []
        files = sorted(
            self._iter_backup_files(),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        result = []
        for f in files:
            stat = f.stat()
            metadata = self._read_metadata(f)
            result.append({
                "filename": f.name,
                "size_bytes": stat.st_size,
                "created_at": stat.st_mtime,
                **metadata,
            })
        return result

    def get_backup_path(self, filename: str) -> Path:
        """
        Resolve and validate a backup filename.

        Raises ValueError on path traversal attempts.
        """
        # Strip any directory components — only plain filename allowed
        safe_name = Path(filename).name
        if not safe_name or safe_name != filename:
            raise ValueError("Invalid backup filename")

        # Allow only safe characters (alphanumeric, _, -, .)
        if not re.fullmatch(r"[\w.\-]+", safe_name):
            raise ValueError("Invalid backup filename characters")

        path = self._backup_dir / safe_name
        # Resolve and verify the final path is still under backup_dir
        try:
            path.resolve().relative_to(self._backup_dir.resolve())
        except ValueError:
            raise ValueError("Path traversal detected")

        if not path.is_file():
            raise FileNotFoundError(f"Backup not found: {safe_name}")
        return path

    def run_restore_drill(self, filename: str | None = None) -> dict[str, Any]:
        """Exercise restore verification for the latest or named backup."""
        path = self.get_backup_path(filename) if filename else self._latest_backup_path()
        metadata = self._read_metadata(path)
        source_path = path
        cleanup_path: Path | None = None
        source = "local"

        try:
            if self._cloud_enabled and metadata.get("cloud_object_key"):
                source_path = self._download_from_cloud(str(metadata["cloud_object_key"]), path.suffix)
                cleanup_path = source_path
                source = "cloud_download"

            verification = self.verify_backup(source_path)
            result = {
                "filename": path.name,
                "source": source,
                **verification,
            }
            self._write_metadata(
                path,
                {
                    "last_restore_drill_at": result.get("verified_at"),
                    "last_restore_drill_status": "passed",
                    "last_restore_drill_source": source,
                },
            )
            return result
        except Exception as exc:
            self._write_metadata(
                path,
                {
                    "last_restore_drill_at": None,
                    "last_restore_drill_status": f"failed: {exc}",
                    "last_restore_drill_source": source,
                },
            )
            raise
        finally:
            if cleanup_path is not None:
                cleanup_path.unlink(missing_ok=True)

    def verify_backup(self, path: Path) -> dict[str, Any]:
        """Validate that a backup artifact can be read by its restore toolchain."""
        if path.suffix == ".sqlite":
            conn = sqlite3.connect(str(path))
            try:
                result = conn.execute("PRAGMA integrity_check").fetchone()
            finally:
                conn.close()
            if not result or result[0] != "ok":
                raise RuntimeError(f"SQLite integrity check failed for {path.name}")
            method = "sqlite_integrity_check"
        elif path.suffix == ".pgdump":
            pg_restore = shutil.which("pg_restore")
            if not pg_restore:
                raise RuntimeError("pg_restore not found on PATH; cannot verify PostgreSQL backup")
            result = subprocess.run(
                [pg_restore, "--list", str(path)],
                capture_output=True,
                timeout=300,
                check=False,
            )
            if result.returncode != 0:
                stderr = result.stderr.decode(errors="replace")
                raise RuntimeError(f"pg_restore verification failed (exit {result.returncode}): {stderr}")
            method = "pg_restore_list"
        else:
            raise RuntimeError(f"Unsupported backup extension for verification: {path.suffix}")

        from utils.datetime_utils import utcnow

        return {
            "verified": True,
            "verification_method": method,
            "verified_at": utcnow().isoformat(),
        }

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _is_sqlite(self) -> bool:
        return self._db_url.startswith("sqlite")

    def _timestamp(self) -> str:
        from utils.datetime_utils import utcnow
        import uuid
        return utcnow().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]

    def _backup_sqlite(self) -> Path:
        """Hot backup for SQLite without locking the source database."""
        # Extract file path from URL, e.g. sqlite:///./zozi.db → ./zozi.db
        raw = self._db_url.replace("sqlite:///", "").replace("sqlite://", "")
        source_path = Path(raw).resolve()

        dest_path = self._backup_dir / f"backup_{self._timestamp()}.sqlite"
        # Use sqlite3 online backup API — safe while DB may be in use
        src_conn = sqlite3.connect(str(source_path))
        dst_conn = sqlite3.connect(str(dest_path))
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()
        return dest_path

    def _backup_postgres(self) -> Path:
        """Backup PostgreSQL using pg_dump (custom compressed format -Fc)."""
        pg_dump = shutil.which("pg_dump")
        if not pg_dump:
            raise RuntimeError("pg_dump not found on PATH; cannot create PostgreSQL backup")

        dest_path = self._backup_dir / f"backup_{self._timestamp()}.pgdump"
        parsed = urlparse(self._db_url)

        env = os.environ.copy()
        if parsed.password:
            env["PGPASSWORD"] = parsed.password

        cmd = [
            pg_dump,
            "-Fc",
            "-h", parsed.hostname or "localhost",
            "-p", str(parsed.port or 5432),
            "-U", parsed.username or "postgres",
            "-d", (parsed.path or "").lstrip("/"),
            "-f", str(dest_path),
        ]
        result = subprocess.run(cmd, env=env, capture_output=True, timeout=300)
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace")
            raise RuntimeError(f"pg_dump failed (exit {result.returncode}): {stderr}")
        return dest_path

    def _iter_backup_files(self):
        if not self._backup_dir.exists():
            return []
        return [
            path
            for path in self._backup_dir.iterdir()
            if path.is_file() and not path.name.endswith(".metadata.json")
        ]

    def _metadata_path(self, backup_path: Path) -> Path:
        return backup_path.with_name(f"{backup_path.name}.metadata.json")

    def _read_metadata(self, backup_path: Path) -> dict[str, Any]:
        metadata_path = self._metadata_path(backup_path)
        if not metadata_path.is_file():
            return {}
        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            logger.warning("Backup metadata for %s is unreadable; ignoring sidecar", backup_path.name)
            return {}

    def _write_metadata(self, backup_path: Path, updates: dict[str, Any]) -> None:
        metadata = self._read_metadata(backup_path)
        metadata.update(updates)
        metadata_path = self._metadata_path(backup_path)
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")

    def _latest_backup_path(self) -> Path:
        backups = sorted(self._iter_backup_files(), key=lambda p: p.stat().st_mtime, reverse=True)
        if not backups:
            raise FileNotFoundError("No backups available")
        return backups[0]

    def _s3_client(self):
        try:
            import importlib
        except ImportError as exc:
            raise RuntimeError("importlib is required to load boto3 for S3 backup replication") from exc

        try:
            boto3 = importlib.import_module("boto3")
        except ModuleNotFoundError as exc:
            raise RuntimeError("boto3 is required for S3 backup replication") from exc

        session_kwargs: dict[str, Any] = {}
        if self._s3_access_key_id and self._s3_secret_access_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": self._s3_access_key_id,
                    "aws_secret_access_key": self._s3_secret_access_key,
                }
            )
        if self._s3_region:
            session_kwargs["region_name"] = self._s3_region

        session = boto3.session.Session(**session_kwargs)
        client_kwargs: dict[str, Any] = {}
        if self._s3_endpoint_url:
            client_kwargs["endpoint_url"] = self._s3_endpoint_url
        return session.client("s3", **client_kwargs)

    def _upload_to_cloud(self, path: Path) -> dict[str, Any]:
        if self._cloud_provider != "s3":
            raise RuntimeError(f"Unsupported backup cloud provider: {self._cloud_provider}")

        object_key = "/".join(part for part in [self._s3_prefix, path.name] if part)
        client = self._s3_client()
        client.upload_file(
            str(path),
            self._s3_bucket,
            object_key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )
        return {
            "cloud_synced": True,
            "cloud_provider": "s3",
            "cloud_bucket": self._s3_bucket,
            "cloud_object_key": object_key,
        }

    def _download_from_cloud(self, object_key: str, suffix: str) -> Path:
        if self._cloud_provider != "s3":
            raise RuntimeError(f"Unsupported backup cloud provider: {self._cloud_provider}")

        handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        handle.close()
        destination = Path(handle.name)
        client = self._s3_client()
        client.download_file(self._s3_bucket, object_key, str(destination))
        return destination

    def _rotate_old_backups(self) -> None:
        """Delete oldest backup files when over the retention limit."""
        files = sorted(
            self._iter_backup_files(),
            key=lambda p: p.stat().st_mtime,
        )
        excess = len(files) - self._max_files
        for f in files[:excess]:
            try:
                f.unlink()
                self._metadata_path(f).unlink(missing_ok=True)
                logger.info("Rotated old backup: %s", f.name)
            except OSError as exc:
                logger.warning("Could not delete old backup %s: %s", f.name, exc)


# ── Module-level singleton ────────────────────────────────────────────────────

_backup_manager: Optional[BackupManager] = None


def get_backup_manager() -> BackupManager:
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager

