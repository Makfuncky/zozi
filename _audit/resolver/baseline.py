"""Pre-dispatch baseline snapshot — the mitigation for an uncommitted tree.

The working tree carries ~342 modified / ~225 untracked paths, so `git diff`
cannot separate this session's edits from prior uncommitted work. That breaks
`D-SCOPE` and `D-CASCADE` attribution (resolver 0.7).

A git commit is the real fix. Without one, this tool restores attribution
*within the session* by recording a SHA-256 of every file a contract is about to
touch, immediately before dispatch. After the agent returns, `diff` reports
exactly which allowed files changed, which changed when they should not have,
and which did not change at all.

Usage:
  python _audit/resolver/baseline.py snapshot <phase-label> <file> [<file> ...]
  python _audit/resolver/baseline.py diff <phase-label>
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SNAP_DIR = os.path.join(ROOT, "_audit", "resolver", "baselines")


def digest(path: str) -> dict:
    ap = os.path.join(ROOT, path)
    if not os.path.exists(ap):
        return {"path": path, "exists": False, "sha256": None,
                "size": None, "lines": None}
    data = open(ap, "rb").read()
    text = data.decode("utf-8", errors="replace")
    return {
        "path": path,
        "exists": True,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": len(data),
        "lines": text.count("\n") + 1,
    }


def snapshot(label: str, files: list[str]) -> int:
    os.makedirs(SNAP_DIR, exist_ok=True)
    rec = {
        "label": label,
        "taken_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Pre-dispatch baseline. git is not committed, so this file is "
                "the ONLY reliable attribution source for this wave.",
        "files": [digest(f) for f in files],
    }
    path = os.path.join(SNAP_DIR, f"{label}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    print(f"snapshot {label}: {len(files)} files -> {os.path.relpath(path, ROOT)}")
    for f in rec["files"]:
        mark = "ok " if f["exists"] else "MISSING"
        print(f"  [{mark}] {f['path']:<70} {str(f['sha256'])[:16]}  {f['lines']} lines")
    return 0


def diff(label: str) -> int:
    path = os.path.join(SNAP_DIR, f"{label}.json")
    if not os.path.exists(path):
        print(f"no baseline for {label}")
        return 1
    base = json.load(open(path, encoding="utf-8"))
    changed, unchanged, missing = [], [], []
    for f in base["files"]:
        now = digest(f["path"])
        if not now["exists"]:
            missing.append(f["path"])
        elif not f["exists"]:
            changed.append((f["path"], "CREATED", None, now["sha256"]))
        elif now["sha256"] != f["sha256"]:
            dl = (now["lines"] or 0) - (f["lines"] or 0)
            changed.append((f["path"], "MODIFIED", f["sha256"], now["sha256"], dl))
        else:
            unchanged.append(f["path"])

    print(f"BASELINE DIFF — {label}   (taken {base['taken_at']})")
    print("=" * 96)
    for c in changed:
        if c[1] == "MODIFIED":
            print(f"  MODIFIED  {c[0]}")
            print(f"            {c[2][:16]} -> {c[3][:16]}   net lines {c[4]:+d}")
        else:
            print(f"  CREATED   {c[0]}")
    for m in missing:
        print(f"  DELETED   {m}")
    for u in unchanged:
        print(f"  unchanged {u}")
    print("=" * 96)
    print(f"{len(changed)} changed, {len(unchanged)} unchanged, {len(missing)} deleted")
    if not changed:
        print("VERDICT: agent claimed a fix but changed NOTHING in scope -> D-EVIDENCE")
    return 0


def main() -> int:
    argv = sys.argv
    if len(argv) < 3:
        print(__doc__)
        return 1
    if argv[1] == "snapshot":
        return snapshot(argv[2], argv[3:])
    if argv[1] == "diff":
        return diff(argv[2])
    print("unknown action")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())