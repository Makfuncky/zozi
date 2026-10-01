#!/usr/bin/env python3
"""Check that Alembic migration filenames match the expected naming convention.

Expected pattern: YYYY_MM_DD_HH_MM[-<rev>]_description.py
The revision ID embedded in the filename must match the revision defined
in the file content.
"""
import os
import re
import sys


TIMESTAMP_RE = re.compile(r"^(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})")
REV_RE = re.compile(r"""revision(?:\s*:\s*str)?\s*=\s*['"]([^'"]+)['"]""")


def extract_filename_rev(filename: str) -> str | None:
    """Extract revision ID from migration filename."""
    stem = filename[:-3]  # strip .py
    # Pattern: YYYY_MM_DD_HH_MM-<rev>_description
    if "-" in stem:
        parts = stem.split("-", 1)
        if len(parts) == 2:
            return parts[1].split("_")[0]
    # Pattern: YYYY_MM_DD_HH_MM_description (rev = timestamp-derived)
    ts_match = TIMESTAMP_RE.match(stem)
    if ts_match:
        return f"{ts_match.group(1)}{ts_match.group(2)}{ts_match.group(3)}_{ts_match.group(4)}{ts_match.group(5)}"
    return None


def extract_file_rev(filepath: str) -> str | None:
    """Extract revision ID from migration file content."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    match = REV_RE.search(content)
    return match.group(1) if match else None


def check_migration(filepath: str) -> list[str]:
    """Check a single migration file. Returns list of errors."""
    filename = os.path.basename(filepath)
    errors = []

    if not filename.endswith(".py"):
        return errors

    if filename == "__init__.py":
        return errors

    fn_rev = extract_filename_rev(filename)
    if fn_rev is None:
        errors.append(f"{filename}: filename does not match YYYY_MM_DD_HH_MM[-<rev>]_description.py pattern")
        return errors

    file_rev = extract_file_rev(filepath)
    if file_rev is None:
        errors.append(f"{filename}: could not extract revision from file content")
        return errors

    # Check that filename rev matches file rev
    # For timestamp-derived revs, compare the numeric part
    ts_match = TIMESTAMP_RE.match(filename[:-3])
    if ts_match:
        # Filename uses timestamp; file rev should start with YYYYMMDD_HHMM
        expected_file_rev = f"{ts_match.group(1)}{ts_match.group(2)}{ts_match.group(3)}_{ts_match.group(4)}{ts_match.group(5)}"
        if not file_rev.startswith(expected_file_rev):
            errors.append(f"{filename}: file revision '{file_rev}' does not match filename timestamp (expected prefix '{expected_file_rev}')")
    else:
        # Filename has explicit rev
        if fn_rev != file_rev:
            errors.append(f"{filename}: file revision '{file_rev}' does not match filename revision '{fn_rev}'")

    return errors


def main() -> int:
    """Entry point for pre-commit hook."""
    errors = []
    for filepath in sys.argv[1:]:
        errors.extend(check_migration(filepath))

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
