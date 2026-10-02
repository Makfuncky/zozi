"""Normalise known verdict-file schema deviations, explicitly and audibly.

The subcontract specifies the verdict array under the key `verdicts`. One agent
wrote it under `records` with an otherwise identical record schema. This script
renames that key and records the change in the compiler log rather than
silently absorbing it.

It refuses to touch anything else. It never edits a record's verdict, never
adds a record, never removes one.
"""

from __future__ import annotations

import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VERD = os.path.join(ROOT, "_audit", "compiler", "verdicts")
AUDIT = os.path.join(ROOT, "_audit", "compiler", "logs", "agent_performance.jsonl")

ALIASES = {"records": "verdicts"}


def main() -> int:
    changed = []
    for path in sorted(glob.glob(os.path.join(VERD, "*.json"))):
        name = os.path.basename(path)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if "verdicts" in data:
            continue
        for src, dst in ALIASES.items():
            if src in data and isinstance(data[src], list):
                data[dst] = data.pop(src)
                data["_schema_normalised"] = (
                    f"verdict array was under '{src}'; renamed to '{dst}' to match "
                    "the subcontract. Record contents untouched."
                )
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh, indent=1, ensure_ascii=False)
                changed.append((name, src, dst, len(data[dst])))
                break

    if not changed:
        print("no schema deviations found")
        return 0

    from datetime import datetime, timezone
    with open(AUDIT, "a", encoding="utf-8") as fh:
        for name, src, dst, n in changed:
            rec = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "event": "normalise",
                "agent_id": f"ORCHESTRATOR/{name}",
                "code": "SCHEMA_DEVIATION",
                "detail": f"verdict array key '{src}' -> '{dst}' ({n} records, contents unchanged)",
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"normalised {name}: {src} -> {dst} ({n} records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())