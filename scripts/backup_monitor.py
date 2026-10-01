"""ZOZI backup monitoring script.

Checks backup file existence and age, verifies backup integrity via pg_restore --list,
and sends alerts on failure.

Laws 215-220: Production validation — backup monitoring ensures deployment resilience.
"""

from __future__ import annotations

import os
import smtplib
import subprocess
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path


DEFAULT_MAX_AGE_HOURS = 25
DEFAULT_RETENTION_DAYS = 30


def get_backup_dir() -> Path:
    """Return the backup directory path."""
    return Path(os.environ.get("ZOZI_BACKUP_DIR", "/var/backups/zozi"))


def find_latest_backup(backup_dir: Path) -> Path | None:
    """Find the most recent backup file."""
    backups = sorted(backup_dir.glob("zozi_backup_*.dump"), reverse=True)
    return backups[0] if backups else None


def check_backup_exists(backup_dir: Path) -> tuple[bool, Path | None]:
    """Check that at least one backup file exists."""
    latest = find_latest_backup(backup_dir)
    return (latest is not None, latest)


def check_backup_age(backup_path: Path, max_age_hours: int = DEFAULT_MAX_AGE_HOURS) -> tuple[bool, float]:
    """Check that the latest backup is within acceptable age. Returns (ok, age_hours)."""
    if not backup_path.exists():
        return (False, float("inf"))
    mtime = datetime.fromtimestamp(backup_path.stat().st_mtime)
    age = datetime.now() - mtime
    age_hours = age.total_seconds() / 3600
    return (age_hours <= max_age_hours, age_hours)


def verify_backup_integrity(backup_path: Path) -> tuple[bool, str]:
    """Verify backup integrity using pg_restore --list."""
    if not backup_path.exists():
        return (False, "Backup file does not exist")
    cmd = ["pg_restore", "--list", str(backup_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return (False, result.stderr.strip() or "pg_restore --list failed")
    object_count = len(result.stdout.strip().splitlines())
    if object_count == 0:
        return (False, "Backup contains no objects")
    return (True, f"{object_count} objects in backup")


def check_expired_backups(backup_dir: Path, retention_days: int = DEFAULT_RETENTION_DAYS) -> int:
    """Count backup files exceeding retention policy. Returns count."""
    cutoff = datetime.now() - timedelta(days=retention_days)
    expired = 0
    for f in backup_dir.glob("zozi_backup_*.dump"):
        try:
            timestamp_str = f.stem.replace("zozi_backup_", "")
            file_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            if file_time < cutoff:
                expired += 1
        except ValueError:
            continue
    return expired


def send_alert(message: str, subject: str = "ZOZI Backup Alert") -> bool:
    """Send alert via email. Returns True if sent successfully."""
    smtp_host = os.environ.get("ALERT_SMTP_HOST", "")
    smtp_port = int(os.environ.get("ALERT_SMTP_PORT", "587"))
    smtp_user = os.environ.get("ALERT_SMTP_USER", "")
    smtp_pass = os.environ.get("ALERT_SMTP_PASS", "")
    alert_from = os.environ.get("ALERT_FROM", "zozi-backups@zozi.com")
    alert_to = os.environ.get("ALERT_TO", "ops@zozi.com")

    if not smtp_host:
        print(f"  [ALERT - no SMTP configured] {subject}: {message}")
        return False

    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = alert_from
        msg["To"] = alert_to

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.sendmail(alert_from, [alert_to], msg.as_string())
        return True
    except Exception as e:
        print(f"  [ALERT FAILED] Could not send email: {e}", file=sys.stderr)
        return False


def run_checks(
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    retention_days: int = DEFAULT_RETENTION_DAYS,
) -> dict:
    """Run all backup checks and return results dict."""
    backup_dir = get_backup_dir()
    results = {
        "timestamp": datetime.now().isoformat(),
        "backup_dir": str(backup_dir),
        "checks": {},
        "healthy": True,
    }

    # Check 1: backup exists
    exists, latest = check_backup_exists(backup_dir)
    results["checks"]["backup_exists"] = {"ok": exists}
    if not exists:
        results["checks"]["backup_exists"]["error"] = "No backup files found"
        results["healthy"] = False
        return results

    results["latest_backup"] = latest.name
    results["latest_backup_size_mb"] = round(latest.stat().st_size / (1024 * 1024), 1)

    # Check 2: backup age
    age_ok, age_hours = check_backup_age(latest, max_age_hours)
    results["checks"]["backup_age"] = {
        "ok": age_ok,
        "age_hours": round(age_hours, 1),
        "max_age_hours": max_age_hours,
    }
    if not age_ok:
        results["checks"]["backup_age"]["error"] = (
            f"Backup is {age_hours:.1f}h old (max: {max_age_hours}h)"
        )
        results["healthy"] = False

    # Check 3: integrity
    integrity_ok, integrity_msg = verify_backup_integrity(latest)
    results["checks"]["integrity"] = {
        "ok": integrity_ok,
        "detail": integrity_msg,
    }
    if not integrity_ok:
        results["checks"]["integrity"]["error"] = integrity_msg
        results["healthy"] = False

    # Check 4: expired backups count
    expired = check_expired_backups(backup_dir, retention_days)
    results["checks"]["expired_backups"] = {
        "ok": True,
        "count": expired,
        "retention_days": retention_days,
    }

    return results


def format_report(results: dict) -> str:
    """Format check results into a human-readable report."""
    lines = [
        f"ZOZI Backup Monitor Report — {results['timestamp']}",
        f"Backup directory: {results['backup_dir']}",
        f"Status: {'HEALTHY' if results['healthy'] else 'UNHEALTHY'}",
        "",
    ]

    if "latest_backup" in results:
        lines.append(f"Latest backup: {results['latest_backup']}")
        lines.append(f"Size: {results['latest_backup_size_mb']} MB")
        lines.append("")

    for check_name, check_data in results["checks"].items():
        status = "PASS" if check_data["ok"] else "FAIL"
        line = f"  [{status}] {check_name}"
        if "age_hours" in check_data:
            line += f" — {check_data['age_hours']}h old"
        if "detail" in check_data:
            line += f" — {check_data['detail']}"
        if "count" in check_data:
            line += f" — {check_data['count']} expired"
        if "error" in check_data:
            line += f"\n         ERROR: {check_data['error']}"
        lines.append(line)

    return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="ZOZI backup monitor")
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=int(os.environ.get("BACKUP_MAX_AGE_HOURS", DEFAULT_MAX_AGE_HOURS)),
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.environ.get("BACKUP_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)),
    )
    parser.add_argument("--no-alert", action="store_true", help="Suppress alert sending")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of text")

    args = parser.parse_args()

    results = run_checks(args.max_age_hours, args.retention_days)

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print(format_report(results))

    if not results["healthy"] and not args.no_alert:
        subject = f"ZOZI Backup UNHEALTHY — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        send_alert(format_report(results), subject)

    return 0 if results["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
