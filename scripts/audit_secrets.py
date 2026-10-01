#!/usr/bin/env python3
"""scripts/audit_secrets.py

Lightweight secret scanner for the ZOZI repository. Scans tracked files for
common secret patterns: database URLs, API tokens, hardcoded passwords, AWS
keys, Stripe keys, JWT secrets, and Cloudflare tokens.

Usage:
    python scripts/audit_secrets.py [--fix]

Exit codes:
    0 - no findings
    1 - findings detected
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDE_DIRS = {
    ".venv", "venv", "node_modules", "__pycache__", ".git",
    "dist", "build", ".expo", ".kilo", "worktrees",
}

SCANNER_IGNORE = REPO_ROOT / ".scannerignore"
SCANNER_IGNORE_PATTERNS: list[str] = []
if SCANNER_IGNORE.is_file():
    for line in SCANNER_IGNORE.read_text(encoding="utf-8", errors="ignore").splitlines():
        pattern = line.strip()
        if pattern and not pattern.startswith("#"):
            SCANNER_IGNORE_PATTERNS.append(pattern)


def is_scanner_ignored(path: Path) -> bool:
    rel = str(path.relative_to(REPO_ROOT)).replace(os.sep, "/")
    for pattern in SCANNER_IGNORE_PATTERNS:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(rel, f"**/{pattern}"):
            return True
    return False


RULES = [
    {
        "id": "database-url",
        "description": "Database URL with credentials",
        "regex": re.compile(
            r"(?i)(postgresql|mysql|mongodb)://[^:\n]+:[^@\n]+@[^:\n]+:[^/\n]+/[^\s'\n\"]+"
        ),
    },
    {
        "id": "cloudflare-api-token",
        "description": "Cloudflare API token",
        "regex": re.compile(r"(?i)CLOUDFLARE_API_TOKEN\s*=\s*[A-Za-z0-9_\-]+"),
    },
    {
        "id": "cloudflare-token-cfat",
        "description": "Cloudflare cfat_ token",
        "regex": re.compile(r"(?i)cfat_[A-Za-z0-9_\-]+"),
    },
    {
        "id": "generic-api-key",
        "description": "Generic API key",
        "regex": re.compile(
            r"(?i)(?:api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]"
        ),
    },
    {
        "id": "aws-access-key",
        "description": "AWS Access Key",
        "regex": re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    },
    {
        "id": "stripe-secret-key",
        "description": "Stripe Secret Key",
        "regex": re.compile(r"(?i)sk_live_[A-Za-z0-9]{16,}"),
    },
    {
        "id": "jwt-secret",
        "description": "JWT Secret",
        "regex": re.compile(
            r"(?i)jwt[_-]?secret\s*[:=]\s*['\"]([A-Za-z0-9_\-]{20,})['\"]"
        ),
    },
    {
        "id": "generic-password",
        "description": "Hardcoded password in source",
        "regex": re.compile(
            r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"]([A-Za-z0-9_\-!@#$%^&*]{6,})['\"]"
        ),
    },
]


def get_tracked_files() -> list[Path]:
    """Return tracked files from git index."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: git ls-files failed: {exc.stderr}", file=sys.stderr)
        sys.exit(2)

    files = []
    for line in result.stdout.splitlines():
        p = REPO_ROOT / line
        if p.is_file() and not is_scanner_ignored(p):
            files.append(p)
    return files


def redact(value: str) -> str:
    if len(value) <= 8:
        return value[:2] + "***"
    return value[:5] + "***...***" + value[-3:]


def is_placeholder_database_url(url: str) -> bool:
    """Return True if the database URL uses an obvious placeholder credential."""
    try:
        scheme_end = url.index("://") + 3
        auth_end = url.index("@", scheme_end)
        credential = url[scheme_end:auth_end]
    except ValueError:
        return False
    if ":" not in credential:
        return False
    user, _, pwd = credential.partition(":")
    placeholder_tokens = {"user", "pass", "password", "example", "username", "USER", "PASS", "PASSWORD", "EXAMPLE", "USERNAME"}
    if user in placeholder_tokens or pwd in placeholder_tokens:
        return True
    if user.endswith(("_name", "_replace", "_here")) or pwd.endswith(("_name", "_replace", "_here")):
        return True
    return False


def scan_file(path: Path) -> list[dict]:
    """Scan a single file for secret patterns."""
    findings = []
    text = None
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            text = path.read_text(encoding=enc, errors="ignore")
            if text and "\x00" not in text:
                break
        except Exception:
            continue

    if not text:
        return findings

    for rule in RULES:
        for match in rule["regex"].finditer(text):
            if rule["id"] == "database-url" and is_placeholder_database_url(match.group(0)):
                continue
            lineno = text[: match.start()].count("\n") + 1
            line_content = text.splitlines()[lineno - 1].rstrip()
            findings.append({
                "rule_id": rule["id"],
                "description": rule["description"],
                "file": str(path.relative_to(REPO_ROOT)),
                "line": lineno,
                "match": redact(match.group(0)),
                "raw_match": match.group(0),
                "context": line_content.strip(),
            })
    return findings


def safe_print(text: str) -> None:
    """Print text, replacing characters that the console encoding cannot handle."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="ZOZI secret scanner")
    parser.add_argument("--fix", action="store_true", help="Not implemented; scan only")
    args = parser.parse_args()

    tracked = get_tracked_files()
    all_findings: list[dict] = []

    for path in tracked:
        findings = scan_file(path)
        if findings:
            all_findings.extend(findings)

    if not all_findings:
        safe_print("No secrets found.")
        return 0

    safe_print(f"FINDINGS: {len(all_findings)} potential secret(s) detected\n")
    for f in all_findings:
        safe_print(f"[{f['rule_id']}] {f['description']}")
        safe_print(f"  File: {f['file']}:{f['line']}")
        safe_print(f"  Match: {f['match']}")
        safe_print(f"  Context: {f['context']}")
        safe_print("")

    return 1


if __name__ == "__main__":
    sys.exit(main())
