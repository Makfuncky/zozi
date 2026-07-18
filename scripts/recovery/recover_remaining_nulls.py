from __future__ import annotations

import argparse
import json
import os
import shutil
import urllib.parse
from pathlib import Path

WORKSPACE = Path(r"F:\recovery_recuva_4\Projects\10- E-COMMERCE WEBSITE\zozi")
HISTORY_ROOT = Path(os.environ["APPDATA"]) / "Code" / "User" / "History"

SOURCE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".json",
    ".md",
    ".sh",
    ".yml",
    ".yaml",
    ".toml",
    ".ps1",
    ".bat",
    ".ini",
    ".txt",
    ".mjs",
    ".html",
}

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "backend/venv",
    "node_modules",
    ".next",
    ".git",
    "__pycache__",
}


def is_excluded(path: Path) -> bool:
    rel = path.relative_to(WORKSPACE).as_posix().lower()
    return any(excl in rel for excl in EXCLUDE_DIRS)


def is_null_like(path: Path) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        return True

    content = path.read_bytes()
    n = len(content)
    chunks = [content[: min(4096, n)]]
    if n > 8192:
        mid = n // 2
        chunks.append(content[mid : mid + 4096])
    if n > 4096:
        chunks.append(content[max(0, n - 4096) :])

    return all(all(b == 0 for b in chunk) for chunk in chunks if chunk)


def build_history_index() -> dict[str, list[tuple[int, Path]]]:
    index: dict[str, list[tuple[int, Path]]] = {}
    for folder in HISTORY_ROOT.iterdir():
        if not folder.is_dir():
            continue

        entries_file = folder / "entries.json"
        if not entries_file.exists():
            continue

        try:
            data = json.loads(entries_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        resource = data.get("resource", "")
        if not resource.startswith("file:///"):
            continue

        resource_path = urllib.parse.unquote(resource[len("file:///") :]).replace("\\", "/").lower()
        marker = resource_path.rfind("/zozi/")
        if marker < 0:
            continue

        rel = resource_path[marker + len("/zozi/") :]
        index.setdefault(rel, [])

        for entry in data.get("entries", []):
            entry_id = entry.get("id")
            ts = entry.get("timestamp", 0)
            if not entry_id:
                continue

            snapshot = folder / entry_id
            if snapshot.exists() and snapshot.stat().st_size > 0:
                index[rel].append((ts, snapshot))

    return index


def choose_latest_non_null(candidates: list[tuple[int, Path]]) -> tuple[int, Path] | None:
    best: tuple[int, Path] | None = None
    for ts, src in candidates:
        sample = src.read_bytes()[:4096]
        if sample and all(b == 0 for b in sample):
            continue
        if best is None or ts > best[0]:
            best = (ts, src)
    return best


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore remaining null-like source files from VS Code History.")
    parser.add_argument("--apply", action="store_true", help="Actually write restored files")
    args = parser.parse_args()

    history_index = build_history_index()

    targets: list[Path] = []
    for path in WORKSPACE.rglob("*"):
        if not path.is_file():
            continue
        if is_excluded(path):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        if is_null_like(path):
            targets.append(path)

    restored = 0
    missed = 0

    for target in sorted(targets):
        rel = target.relative_to(WORKSPACE).as_posix().lower()
        best = choose_latest_non_null(history_index.get(rel, []))
        if best is None:
            missed += 1
            continue

        ts, src = best
        if args.apply:
            backup = target.with_suffix(target.suffix + ".pre_null_restore.bak")
            if target.exists() and not backup.exists():
                shutil.copy2(target, backup)
            shutil.copy2(src, target)
            print(f"RESTORED {target.relative_to(WORKSPACE).as_posix()} <- {src} (ts={ts})")
        else:
            print(f"[DRY] {target.relative_to(WORKSPACE).as_posix()} <- {src} (ts={ts})")
        restored += 1

    print(f"Targets: {len(targets)}")
    print(f"Restorable: {restored}")
    print(f"Missed: {missed}")
    if not args.apply:
        print("Run with --apply to write files.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
