"""Recovery audit script for post-restore hygiene checks.

Checks:
- null-byte and empty files in maintained source/docs/script trees
- suspicious recovery-style filenames
- duplicate-content groups in maintained trees
- legacy frontend/src folder presence
"""

from __future__ import annotations

import argparse
import hashlib
import re
from collections import defaultdict
from pathlib import Path


MAINTAINED_DIRS = ("backend", "frontend", "documents", "scripts")
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".next",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "build",
    "coverage",
    "test-results",
    "tmp-pw-output",
    "uploads",
    "artifacts",
}
SOURCE_EXTS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".yml",
    ".yaml",
    ".toml",
    ".txt",
    ".bat",
    ".ps1",
    ".sh",
    ".json",
    ".md",
    ".env",
    ".ini",
    ".cfg",
    ".sql",
    ".css",
    ".scss",
    ".html",
}
SPECIAL_FILES = {"Makefile", "Dockerfile", ".env", ".env.example", ".env.production"}
SUSPICIOUS_NAME_PATTERN = re.compile(
    r"(?i)(\.bak$|\.old$|\.new$|pre_restore|pre_symbol_recover|copy(?:\s+\d+)?\.html$)"
)
ALLOWED_DUPLICATE_GROUPS = {
    frozenset({".env.example", ".env.production"}),
    frozenset({"frontend/postcss.config.mjs", "frontend/web_app/postcss.config.mjs"}),
    frozenset({
        "frontend/shared/src/components/logo/Logo.web.tsx",
        "frontend/shared/src/logo/Logo.web.tsx",
    }),
    frozenset({
        "frontend/shared/src/components/logo/native.ts",
        "frontend/shared/src/logo/native.ts",
    }),
    frozenset({
        "frontend/shared/src/components/logo/types.ts",
        "frontend/shared/src/logo/types.ts",
    }),
    frozenset({
        "frontend/shared/src/components/logo/web.ts",
        "frontend/shared/src/logo/web.ts",
    }),
    frozenset({
        "frontend/shared/src/errorLogging.ts",
        "frontend/web_app/src/lib/errorLogging.ts",
    }),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run structural recovery checks.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root path (defaults to parent of scripts folder).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when issues are found.",
    )
    return parser.parse_args()


def _is_skipped(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _is_source_like(path: Path) -> bool:
    if path.name in SPECIAL_FILES:
        return True
    return path.suffix.lower() in SOURCE_EXTS


def iter_candidate_files(root: Path) -> list[Path]:
    files: list[Path] = []

    # Include maintained directories.
    for folder_name in MAINTAINED_DIRS:
        folder = root / folder_name
        if not folder.exists():
            continue
        for file_path in folder.rglob("*"):
            if not file_path.is_file() or _is_skipped(file_path):
                continue
            if _is_source_like(file_path):
                files.append(file_path)

    # Include source-like root files.
    for file_path in root.iterdir():
        if file_path.is_file() and _is_source_like(file_path):
            files.append(file_path)

    return sorted(set(files))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def legacy_frontend_src_files(root: Path) -> list[str]:
    legacy = root / "frontend" / "src"
    if not legacy.exists():
        return []

    return sorted(
        str(p.relative_to(legacy).as_posix())
        for p in legacy.rglob("*")
        if p.is_file() and not _is_skipped(p)
    )


def main() -> int:
    args = parse_args()
    root = args.root.resolve()

    files = iter_candidate_files(root)
    ok_files: list[str] = []
    null_files: list[tuple[str, int]] = []
    empty_files: list[str] = []
    suspicious_files: list[str] = []
    hash_groups: dict[str, list[str]] = defaultdict(list)

    for file_path in files:
        rel = file_path.relative_to(root).as_posix()
        if SUSPICIOUS_NAME_PATTERN.search(file_path.name):
            suspicious_files.append(rel)

        try:
            data = file_path.read_bytes()
        except OSError:
            continue

        if len(data) == 0:
            empty_files.append(rel)
            continue
        if all(byte == 0 for byte in data):
            null_files.append((rel, len(data)))
            continue

        ok_files.append(rel)
        try:
            file_hash = _sha256(file_path)
            hash_groups[file_hash].append(rel)
        except OSError:
            pass

    duplicate_groups = [sorted(group) for group in hash_groups.values() if len(group) > 1]
    duplicate_groups.sort(key=len, reverse=True)
    actionable_duplicate_groups = [
        group for group in duplicate_groups if frozenset(group) not in ALLOWED_DUPLICATE_GROUPS
    ]

    legacy_frontend_files = legacy_frontend_src_files(root)

    print("=" * 72)
    print("ZOZI PROJECT - RECOVERY STRUCTURE AUDIT")
    print("=" * 72)
    print(f"Root: {root}")
    print(f"Checked source-like files: {len(files)}")
    print(f"OK (readable non-empty):  {len(ok_files):>5}")
    print(f"NULL-byte files:          {len(null_files):>5}")
    print(f"EMPTY files:              {len(empty_files):>5}")
    print(f"Suspicious filenames:     {len(suspicious_files):>5}")
    print(f"Duplicate hash groups:    {len(duplicate_groups):>5}")
    print(f"Actionable duplicates:    {len(actionable_duplicate_groups):>5}")
    print("=" * 72)

    if null_files:
        print("\n=== NULL-BYTE FILES ===")
        for rel, size in sorted(null_files):
            print(f"  [{size:>8} bytes] {rel}")

    if empty_files:
        print("\n=== EMPTY FILES ===")
        for rel in sorted(empty_files):
            print(f"  {rel}")

    if suspicious_files:
        print("\n=== SUSPICIOUS RECOVERY FILENAMES ===")
        for rel in sorted(suspicious_files):
            print(f"  {rel}")

    if actionable_duplicate_groups:
        print("\n=== TOP DUPLICATE HASH GROUPS (source-like files) ===")
        for group in actionable_duplicate_groups[:20]:
            print(f"  - group size {len(group)}")
            for rel in group:
                print(f"      {rel}")

    if legacy_frontend_files:
        print("\n=== LEGACY FRONTEND TREE CHECK ===")
        print(f"  legacy frontend/src files detected: {len(legacy_frontend_files)}")
        print("  Sample files:")
        for rel in legacy_frontend_files[:20]:
            print(f"    {rel}")
    else:
        print("\n=== LEGACY FRONTEND TREE CHECK ===")
        print("  frontend/src is absent (expected after retirement).")

    issue_count = len(null_files) + len(empty_files) + len(suspicious_files)
    if args.strict and issue_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
