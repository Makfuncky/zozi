"""Recover any interrupted moves from git objects, then rewrite service imports.

Idempotent: skips files already present at their target; rewrites are no-ops if
already applied. Recovery sources the blob from git (staged or HEAD) so nothing
is lost even if a previous `git mv` was interrupted.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"
SERVICES = BACKEND / "services"
PLAN = REPO / "scripts" / "system_trackers" / "_services_plan.json"


def git(args):
    return subprocess.run(["git"] + args, cwd=str(REPO), capture_output=True, text=True)


def gitb(args):
    return subprocess.run(["git"] + args, cwd=str(REPO), capture_output=True)


def blob(ref: str):
    r = gitb(["cat-file", "-p", ref])
    return r.stdout if r.returncode == 0 and r.stdout else None


plan = json.loads(PLAN.read_text(encoding="utf-8"))
stem_to_final = {}
recovered = []
for e in plan:
    stem = e["file"][:-3]
    if e["folder"] == "SCRATCH":
        target = REPO / "scripts" / "maintenance" / e["file"]
        final = "scripts/maintenance"
    else:
        final = e["final_folder"]
        target = SERVICES / final / e["file"]
    if final:
        stem_to_final[stem] = final
    if target.exists():
        continue
    name = e["file"]
    refs = [
        f":backend/services/{name}",
        f"HEAD:backend/services/{name}",
        f":backend/services/{final}/{name}" if final else None,
        f"HEAD:backend/services/{final}/{name}" if final else None,
    ]
    data = None
    for rf in refs:
        if not rf:
            continue
        data = blob(rf)
        if data is not None:
            break
    if data is None:
        print(f"!! CANNOT RECOVER {name}", flush=True)
        continue
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        target.write_bytes(data)
    else:
        target.write_text(data, encoding="utf-8")
    rel = str(target.relative_to(REPO)).replace("\\", "/")
    git(["add", rel])
    recovered.append(rel)

print(f"RECOVERED {len(recovered)} files:", flush=True)
for r in recovered:
    print("  ", r, flush=True)

# ---- import rewrite (idempotent) ----
stems = sorted(stem_to_final, key=len, reverse=True)
pats = [(re.compile(r"services\." + re.escape(s) + r"(?!\w)"),
         f"services.{stem_to_final[s]}.{s}") for s in stems]
scratch_stems = {e["file"][:-3] for e in plan if e["folder"] == "SCRATCH"}
spats = [(re.compile(r"services\." + re.escape(s) + r"(?!\w)"),
          f"scripts.maintenance.{s}") for s in sorted(scratch_stems, key=len, reverse=True)]

backend_py = [p for p in BACKEND.rglob("*.py") if "__pycache__" not in p.parts]
done = 0
total = 0
for p in backend_py:
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    new = text
    for pat, repl in pats:
        new, n = pat.subn(repl, new)
        total += n
    for pat, repl in spats:
        new, n = pat.subn(repl, new)
        total += n
    if new != text:
        p.write_text(new, encoding="utf-8")
        done += 1
print(f"IMPORT REWRITE: {done} files updated, {total} references rewritten.", flush=True)
