"""RN1 second pass: swap the stopword operation token `management`/`endpoint`
for a real operation verb on routers that HAVE a mappable domain.

Routers with no mappable domain (omnibus/cross-cutting: admin_core,
command_center, contact, ediscovery, escalation, ess, expenses, flash_sales,
frontend_errors, health, hierarchy, imports, internal_channels, ...) cannot be
satisfied by renaming and are left untouched (reported as a contract limitation).

Dry-run by default; pass --apply to execute (git mv / rename + ref rewrite +
main.py router_names + compileall + import verification).
"""
from __future__ import annotations

import argparse
import os
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
ROUTERS = REPO / "backend" / "routers"
VENV = REPO / "backend" / "venv" / "Scripts" / "python.exe"
SKIP_DIRS = {".git", "node_modules", "venv", "__pycache__", ".venv", "scripts"}


def load_tables():
    sys.path.insert(0, str(REPO / "scripts" / "system_trackers"))
    import system_architecture_audit as A
    return (set(A.PLACEMENT_STOP_TOKENS), A.PLACEMENT_ALIAS_TO_DOMAIN,
            {str(x).lower() for x in A.DEFAULT_SURFACE_NAMES})


def tokens(stem):
    return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", stem) if t]


def surface_of(toks, surfaces):
    for t in toks:
        if t in surfaces:
            return t
    return None


def domain_of(toks, aliases):
    for t in toks:
        if aliases.get(t):
            return aliases.get(t)
    return None


def op_verb(surface):
    return {
        "admin": "governance",
        "supplier": "fulfillment",
        "customer": "tracking",
        "public": "access",
        "partner": "operations",
        "logistics_partner": "operations",
    }.get(surface, "tracking")


def py_files():
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".py"):
                yield pathlib.Path(root) / f


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    stop, aliases, surfaces = load_tables()
    plan: dict[str, str] = {}
    skipped = []
    for f in sorted(ROUTERS.glob("*.py")):
        if f.name == "__init__.py":
            continue
        stem = f.stem
        m = re.match(r"^(.*)_(management|endpoint)$", stem)
        if not m:
            skipped.append((stem, "not *_management/_endpoint"))
            continue
        base = m.group(1)
        toks = tokens(base)
        s = surface_of(toks, surfaces)
        d = domain_of(toks, aliases)
        if d is None:
            skipped.append((stem, "no mappable domain (omnibus)"))
            continue
        verb = op_verb(s)
        new = f"{base}_{verb}"
        if new == stem:
            continue
        plan[stem] = new

    print(f"RN1 second-pass renames: {len(plan)}")
    for o, n in sorted(plan.items()):
        print(f"  {o}.py -> {n}.py")
    print(f"\nSkipped (cannot be fixed by renaming): {len(skipped)}")
    for s, why in skipped:
        print(f"  - {s}.py  ({why})")

    if not args.apply:
        print("\n[DRY RUN] pass --apply to execute.")
        return 0

    # 1) move
    for old, new in plan.items():
        src = ROUTERS / f"{old}.py"
        dst = ROUTERS / f"{new}.py"
        try:
            subprocess.run(["git", "mv", f"backend/routers/{old}.py",
                            f"backend/routers/{new}.py"], cwd=REPO,
                           check=True, capture_output=True)
        except subprocess.CalledProcessError:
            src.replace(dst)

    # 2) rewrite references
    stems = list(plan.keys())
    pat = re.compile(
        r"(?P<pre>routers\.|backend\.routers\.)"
        r"(?P<name>" + "|".join(re.escape(s) for s in stems) + r")"
        r"(?![A-Za-z0-9_])"
    )

    def repl(mm):
        return mm.group("pre") + plan[mm.group("name")]

    count = 0
    for p in py_files():
        try:
            data = p.read_text(encoding="utf-8")
        except Exception:
            continue
        nd = pat.sub(repl, data)
        if nd != data:
            p.write_text(nd, encoding="utf-8")
            count += 1
    print(f"\nUpdated references in {count} files.")

    # 3) main.py router_names
    main_py = REPO / "backend" / "main.py"
    mt = main_py.read_text(encoding="utf-8")
    mc = 0
    for old, new in plan.items():
        mt, n = re.subn(r'\("' + re.escape(old) + r'"\s*,', f'("{new}",', mt)
        mc += n
    main_py.write_text(mt, encoding="utf-8")
    print(f"Updated {mc} router_names entries in main.py.")

    # 4) verify
    r = subprocess.run([str(VENV), "-m", "compileall", "-q", "backend"],
                       cwd=REPO, capture_output=True, text=True)
    print("compileall rc=", r.returncode)
    if r.returncode != 0:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
        return 2
    newmods = sorted(plan.values())
    ver = REPO / "_extra_files" / "_rn1_verify.py"
    ver.write_text(
        "import importlib, sys\n"
        "sys.path.insert(0, 'backend')\n"
        "mods = %r\nfail = 0\n"
        "for m in mods:\n"
        "    try:\n        importlib.import_module('routers.' + m)\n"
        "    except Exception as e:\n"
        "        fail += 1\n"
        "        print('FAIL', m, type(e).__name__, str(e)[:200])\n"
        "print('IMPORT_FAILURES', fail)\n" % newmods
    )
    env = dict(os.environ, APP_ENV="test", CSRF_DISABLED="true",
               SECRET_KEY="test-secret-key-for-pytest-only-not-for-prod",
               FIELD_ENCRYPTION_KEY="test-field-key-00000000000000000000000000000000000")
    rv = subprocess.run([str(VENV), str(ver)], cwd=REPO, capture_output=True,
                        text=True, env=env)
    print(rv.stdout)
    if rv.returncode != 0:
        print(rv.stderr[-1500:])
    return 2 if rv.returncode != 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
