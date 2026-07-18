"""Run a backup restore drill against the latest or named backup artifact."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from utils.backup import get_backup_manager


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a ZOZI database backup restore drill")
    parser.add_argument("--filename", help="Specific local backup filename to verify")
    parser.add_argument(
        "--create-first",
        action="store_true",
        help="Create a fresh backup before running the restore drill",
    )
    args = parser.parse_args()

    manager = get_backup_manager()
    filename = args.filename

    if args.create_first:
        path = manager.create_backup()
        if path is None:
            print(json.dumps({"error": "backup_create_failed"}, indent=2))
            return 1
        filename = path.name

    try:
        result = manager.run_restore_drill(filename)
    except Exception as exc:  # pragma: no cover - CLI surface only
        print(json.dumps({"error": str(exc)}, indent=2))
        return 1

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())