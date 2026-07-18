from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path


TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".css",
    ".html",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".env",
    ".mjs",
    ".bat",
    ".sh",
    ".sql",
    ".cfg",
    ".ps1",
    ".txt",
    ".svg",
}
TEXT_FILENAMES = {
    ".env",
    ".env.example",
    ".env.production",
    ".env.local",
}
SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    ".next",
    "__pycache__",
    ".pytest_cache",
    "uploads",
    "artifacts",
    "dist",
    "build",
    "coverage",
    ".recovery-null-backups",
}


@dataclass
class RecoveryEntry:
    path: str
    original_size: int
    cleaned_size: int
    removed_null_bytes: int


def iter_target_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def clean_file(path: Path) -> RecoveryEntry | None:
    payload = path.read_bytes()
    if not payload or b"\x00" not in payload:
        return None
    if not any(byte != 0 for byte in payload):
        return None

    cleaned = payload.replace(b"\x00", b"")
    removed = len(payload) - len(cleaned)
    if removed == 0:
        return None

    try:
        cleaned.decode("utf-8")
    except UnicodeDecodeError:
        return None

    path.write_bytes(cleaned)
    return RecoveryEntry(
        path=str(path),
        original_size=len(payload),
        cleaned_size=len(cleaned),
        removed_null_bytes=removed,
    )


def backup_file(root: Path, backup_root: Path, path: Path) -> None:
    destination = backup_root / path.relative_to(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, destination)


def main() -> int:
    parser = argparse.ArgumentParser(description="Strip null bytes from salvageable text files.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Rewrite files in place. Without this flag, the script only prints candidates.",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    backup_root = root / ".recovery-null-backups"
    manifest_path = root / "artifacts" / "recovery-null-strip-manifest.json"

    candidates: list[Path] = []
    for path in iter_target_files(root):
        payload = path.read_bytes()
        if b"\x00" in payload and any(byte != 0 for byte in payload):
            try:
                payload.replace(b"\x00", b"").decode("utf-8")
            except UnicodeDecodeError:
                continue
            candidates.append(path)

    if not args.apply:
        print(f"Candidates: {len(candidates)}")
        for path in candidates:
            print(path)
        return 0

    backup_root.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[RecoveryEntry] = []
    for path in candidates:
        backup_file(root, backup_root, path)
        entry = clean_file(path)
        if entry is not None:
            results.append(entry)

    manifest_path.write_text(
        json.dumps(
            {
                "root": str(root),
                "backups": str(backup_root),
                "cleaned_files": [asdict(entry) for entry in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Cleaned files: {len(results)}")
    print(f"Backups: {backup_root}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())