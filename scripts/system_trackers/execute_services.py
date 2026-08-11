"""Execute the services/ reorganization described by _services_plan.json.

Usage:
    python scripts/system_trackers/execute_services.py --dry-run
    python scripts/system_trackers/execute_services.py --execute

Steps (per plan entry):
  - scratch        -> git mv to scripts/maintenance/
  - keep=="flat"   -> git rm stub subfolder file (if any), git mv flat -> services/<final>/<name>
  - keep=="sub"    -> git rm flat (subfolder copy stays)
  - no collision   -> git mv flat -> services/<final>/<name>
Then rewrite `services.<stem>` -> `services.<final>.<stem>` across all backend .py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
BACKEND = REPO / "backend"
SERVICES = BACKEND / "services"
PLAN = REPO / "scripts" / "system_trackers" / "_services_plan.json"


def git(args):
    return subprocess.run(["git"] + args, cwd=str(REPO), capture_output=True, text=True)


def tracked(rel: str) -> bool:
    # rel is repo-relative
    r = git(["ls-files", "--error-unmatch", rel])
    return r.returncode == 0


def do_remove(rel: str) -> None:
    p = REPO / rel
    if not p.exists():
        return
    if tracked(rel):
        git(["rm", "-f", rel])
    else:
        p.unlink()


def do_move(src_rel: str, dst_rel: str) -> None:
    sp = REPO / src_rel
    dp = REPO / dst_rel
    dp.parent.mkdir(parents=True, exist_ok=True)
    if sp.resolve() == dp.resolve():
        return
    was_tracked = tracked(src_rel)
    if dp.exists():
        do_remove(dst_rel)
    if was_tracked:
        git(["mv", src_rel, dst_rel])
    else:
        shutil.move(str(sp), str(dp))
        git(["add", dst_rel])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if not args.execute and not args.dry_run:
        args.dry_run = True
    DRY = not args.execute

    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    stem_to_final = {}
    moves, removes, scratch_moves = [], [], []
    for e in plan:
        stem = e["file"][:-3]
        if e["folder"] == "SCRATCH":
            scratch_moves.append(e["file"])
            continue
        final = e["final_folder"]
        if not final:
            continue
        stem_to_final[stem] = final
        if e["collision"]:
            if e["keep"] == "flat":
                # remove stub subfolder copy, then move flat over it
                removes.append(f"services/{e['collision']}/{e['file']}")
                moves.append((f"services/{e['file']}", f"services/{final}/{e['file']}"))
            else:
                removes.append(f"services/{e['file']}")
        else:
            moves.append((f"services/{e['file']}", f"services/{final}/{e['file']}"))

    # Build import-rewrite regexes (longest stem first)
    stems = sorted(stem_to_final, key=len, reverse=True)
    pats = [(re.compile(r"services\." + re.escape(s) + r"(?!\w)"),
             f"services.{stem_to_final[s]}.{s}") for s in stems]

    # Count import rewrites across backend
    backend_py = [p for p in BACKEND.rglob("*.py") if "__pycache__" not in p.parts]
    rewrite_count = 0
    rewrite_files = 0
    sample = []
    for p in backend_py:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        new = text
        hits = 0
        for pat, repl in pats:
            new, n = pat.subn(repl, new)
            hits += n
        if hits:
            rewrite_files += 1
            rewrite_count += hits
            if len(sample) < 12:
                for line in text.splitlines():
                    if any(pat.search(line) for pat, _ in pats):
                        sample.append((str(p.relative_to(REPO)), line.strip()))
                        break
    # also rewrite references to scratch modules (services.stem -> scripts.maintenance.stem)
    scratch_stems = {s[:-3] for s in scratch_moves}
    spats = [(re.compile(r"services\." + re.escape(s) + r"(?!\w)"),
              f"scripts.maintenance.{s}") for s in sorted(scratch_stems, key=len, reverse=True)]

    print(f"DRY_RUN={DRY}")
    print(f"moves (git mv): {len(moves)}")
    print(f"removes (git rm stub/duplicate): {len(removes)}")
    print(f"scratch moves: {len(scratch_moves)} -> {scratch_moves}")
    print(f"import-rewrite patterns: {len(pats)} modules")
    print(f"files needing import rewrite: {rewrite_files}, total reference rewrites: {rewrite_count}")
    print("--- sample rewrite lines ---")
    for f, line in sample:
        print(f"  {f}: {line}")
    if DRY:
        print("--- would execute (dry-run, no changes) ---")
        for src, dst in moves[:5]:
            print(f"  mv {src} -> {dst}")
        if removes:
            print(f"  rm {removes[0]}")
        return

    # ---- EXECUTE ----
    os.makedirs(REPO / "scripts" / "maintenance", exist_ok=True)
    # removes first (drop stub/duplicate copies before moving flats over them)
    for r in removes:
        do_remove(f"backend/{r}")
    for src, dst in moves:
        do_move(f"backend/{src}", f"backend/{dst}")
    for s in scratch_moves:
        do_move(f"backend/services/{s}", f"scripts/maintenance/{s}")
    # rewrite imports
    done = 0
    for p in backend_py:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        new = text
        for pat, repl in pats:
            new = pat.sub(repl, new)
        for pat, repl in spats:
            new = pat.sub(repl, new)
        if new != text:
            p.write_text(new, encoding="utf-8")
            done += 1
    print(f"EXECUTED: rewrote imports in {done} files")


if __name__ == "__main__":
    main()
