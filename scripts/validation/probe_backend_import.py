from __future__ import annotations

import sys
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / ".venv" / "Lib" / "site-packages"))


def main() -> int:
    target = sys.argv[1] if len(sys.argv) > 1 else "routers.addresses"
    try:
        __import__(target)
    except Exception:
        traceback.print_exc()
        return 1
    print(f"Imported {target} successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())