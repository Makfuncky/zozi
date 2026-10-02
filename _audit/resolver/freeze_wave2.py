"""Freeze the wave-2 governance SQL-injection contract, mark the two INVALID
blocks, and take the pre-dispatch baseline.

The governance twin of FILE 3 is a CONFIRMED active SQL injection with 20 live
call sites in a governance/admin surface. `_audit/SHARED_INSTRUCTIONS.md` names
SQL injection in the `emergency` phase, so it outranks most of what remains.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "_audit", "resolver")
CONTRACT_DIR = os.path.join(RES, "contracts")
LOGS = os.path.join(RES, "logs")
WL = os.path.join(ROOT, "_audit", "TO_BE_RESOLVE.md")

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
TARGET = "backend/domains/governance/services/command_center/command_center_service.py"
TEST = "backend/tests/domains/governance/test_command_center_service.py"

BODY = """# CONTRACT: FILE-NEW-1 {target}

- Frozen: {now}
- SHA-256: (computed after write; see orchestrator.log)
- File: {target}
- Phase: emergency
- Depends on files: none
- Findings in scope: 1 - active SQL injection, SEC-004 class, governance twin of FILE 3
- Findings out of scope: 0
- Effort: M
- Nature: security
- Benchmark citations: Law 34 (no f-string/interpolated SQL; bound parameters
  or ORM), Law 42 (validate at boundary), Law 43 (security events logged at
  WARNING+), Law 14 (business logic lives in domains)

## 0 · Proven exploit, reproduced by the orchestrator before this contract was written

```
BLOCKED_KEYWORDS (lines 46-49) = union, select, insert, update, delete, drop,
                                  create, alter, truncate, grant, revoke, exec,
                                  execute, xp_
  -- omits: and, or, having, like, between, case, limit, offset,
  --         pg_sleep, benchmark, information_schema, version

VULNERABLE -> accepted: '1=1 or pg_sleep(5)=1'
VULNERABLE -> accepted: '1=1 or 1=1'
VULNERABLE -> accepted: 'id=1 or benchmark(10000000,sha1(1))'
```

Line 101 concatenates them into live SQL:

```
101  sql = "SELECT COUNT(*) FROM " + validated_table + " WHERE " + validated_where
```

**Someone previously "fixed" this by converting the f-string to string
concatenation. That is cosmetic. Law 34 forbids the result, not the syntax.**

**20 `safe_count(` call sites exist in this file** (governance twin has live
consumers; the analytics twin FILE 3 had zero). Treat every one as in blast
radius.

## 1 · Allowed edits
allowed_files:
  - {target}
  - {test}   (new file; creation is authorised - see 14)
allowed_functions:
  - _validate_where_clause
  - safe_count
  - any helper those two introduce
allowed_edits_per_file: 2
allowed_layers: backend

**If a correct fix requires editing a call site outside this file, STOP and
write `SCOPE_INSUFFICIENT` in your log with the exact `path:line` list. Do NOT
widen your own contract.** 20 internal call sites are inside your scope.

## 2 · Forbidden edits
forbidden_files: every other file
forbidden_patterns:
  stub | disable | comment-out | remove | skip | bypass | silence | swallow |
  hard-code | short-circuit | return-early-to-hide |
  wrap-in-try-except-to-hide | touch-keep-hardened-file |
  dispatch-blocked-by-contradiction | hand-edit-permissions-ts |
  widen-own-denylist

## 3 · Behaviors frozen
- The table allowlist and its rejection behaviour are preserved. An unknown table
  must still raise.
- Table-name lowercasing/stripping preserved.
- `safe_fetch` / `safe_scalar` keep their signatures and their `text(sql)` path.
  They are the sanctioned execution primitives.
- `logger.exception` on database error preserved.
- **All 20 `safe_count(` call sites keep working** and return the same result for
  legitimate predicates. This is the primary regression risk: the current callers
  pass raw fragments, and if your new signature rejects fragments you MUST migrate
  every caller in this file.
- Response shapes consumed by the admin dashboard are unchanged.

## 4 · Behaviors to be added
- A regression test proving a time-based payload is refused.
- A regression test proving the 20 existing call sites still work.

## 5 · Behaviors to be corrected
A WHERE **fragment** cannot be parameterised, so the sound fix is to stop
accepting a raw fragment - exactly as done for the analytics twin. Mirror the
resolved shape of `{sibling}`:
  - accept `None`, a SQLAlchemy Core/ORM boolean expression, or a structured
    predicate (identifier + operator + value)
  - render into **bound parameters**
  - build `SELECT COUNT(*)` with Core constructs

**Do NOT widen the denylist.** A denylist is what failed. The new blocklist, if
any is retained at all, is defence-in-depth only and must not be the control.

Operators are an **allowlist** (`=`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `like`),
not a denylist. Identifiers get a strict regex.

Justification: Law 34; Law 43 for the refusal log.

## 6 · Chains frozen
- CHAIN-005 - governance/analytics reporting must keep returning counts.

## 7 · Laws frozen
- Law 14, Law 42, Law 43, Law 68

## 8 · Laws to be newly satisfied
- Law 34

## 9 · Tests frozen
- Do not modify any pre-existing test.

## 10 · Tests to be added
In `{test}`:
- `test_rejects_time_based_injection` - `1=1 or pg_sleep(5)=1` raises
- `test_rejects_boolean_injection` - `1=1 or 1=1` raises
- `test_unknown_table_still_rejected`
- `test_existing_call_sites_still_work` - exercises the migrated call sites
- `test_parameterised_predicate_accepted` - positive path

## 11 · Expected diff shape
- Files touched: 2 (service + new test)
- Functions touched: 2 plus the 20 call sites
- Lines added: 100-260
- Lines removed: 20-90
- New files: {test}
- Files deleted: 0

## 12 · Expected diff size
- Total lines changed: <= 350 +/- 50%

## 13 · Deletion authorization
The concatenating SQL construction at line 101 and the raw-fragment acceptance in
`_validate_where_clause` may be removed, because that IS the defect. The now-dead
`_BLOCKED_KEYWORDS` / `_KEYWORD_PATTERN` may also be removed **only if** nothing
else references them - grep first and paste the result. Nothing else.

## 14 · Test-change authorization
Authorised to CREATE `{test}`.
Not authorised to modify any pre-existing test.

## 15 · Required evidence
Raw output in `{log}` and under `_audit/resolver/evidence/FILE-NEW-1-governance-cc/`:
1. Contract acknowledgement (17) + sha256
2. Pre-fix exploit proof (all three payloads accepted) - reproduce it yourself
3. Post-fix rejection proof
4. Full list of the 20 call sites with `path:line` and how each was migrated
5. `python -m pytest {test} -q`
6. `ruff check` on both files
7. Boot still works: `PYTHONPATH=backend python -c "from backend.main import app; print(len(app.openapi()['paths']))"`
   - expected 738. Use `openapi()['paths']`, NOT `len(app.routes)` - this FastAPI
     build nests routers lazily and `app.routes` under-reports (returns 84).
8. Proof the table allowlist still rejects unknown tables
9. Proof `_BLOCKED_KEYWORDS` has no other referents (if you removed it)

## 16 · Baseline snapshot
- Behaviors captured: 6 (table allowlist, lowercasing, fetch/scalar primitives,
  DB-error logging, 20 call sites, response shapes)
- Chains captured: 1
- Laws captured: 4
- Tests captured: 0
- Snapshot hash: `_audit/resolver/baselines/wave2-governance.json` (taken by the
  orchestrator BEFORE dispatch, because the working tree is not committed)

## 17 · Sub-agent acknowledgement
I have read this contract in full. I will edit only the files and functions in 1.
I will not perform any edit in 2. I will preserve every behavior in 3. I will add
the behaviors in 4. I will correct the behaviors in 5 with the justification in 5.
I will keep every chain in 6 passing. I will keep every law in 7 satisfied. I will
keep every test in 9 passing. I will not delete anything except as authorized in
13. I will not modify any test except as authorized in 14. I will produce every
piece of evidence in 15. I will match the sibling in 18. I will run the verify
command in 19. I will run the nature-specific check in 23. I will not touch any
KEEP/HARDEN file. I will not dispatch any finding blocked by an open
contradiction. I will not widen my own contract.

Sub-agent signature: <agent_id> at <ISO-8601>

## 18 · Sibling (the correct exemplar)
- Path: `backend/domains/analytics/services/aggregation/command_center_query_service.py`
- What it does right: already resolved in this same wave. It refuses raw `str`
  fragments with a Law 43 WARNING, accepts only `None` / a Core-ORM boolean
  expression / a `Predicate`, renders through bound parameters, and builds
  `select(func.count())`. It has 17 passing tests. **Match that shape.**

## 19 · Verify command
- Command: `python -m pytest {test} -q`
- Expected: all pass, exit 0

## 20 · Paired test
- Test path: {test}
- Test name: test_rejects_time_based_injection

## 21 · Rollback shape
- Method: revert
- Steps: revert {target}, delete {test}
- Irreversible: NO

## 22 · Confidence floor & investigation step
- Audit confidence: 5. The orchestrator's third pass CONFIRMED the injection and
  confirmed it is live (20 call sites). No further investigation is required
  before editing. Reproduce the exploit yourself anyway - evidence 2 - and if it
  does NOT reproduce, STOP and report `AUDIT_CLAIM_WRONG`.

## 23 · Nature-specific check
| Nature | Required check |
|---|---|
| `security` | Denial test: the injection payload must raise |

- Command: `python -m pytest {test} -q -k injection`
- Expected: 2 passed, exit 0
"""


def main() -> int:
    os.makedirs(CONTRACT_DIR, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)

    text = (BODY.replace("{now}", NOW)
                .replace("{target}", TARGET)
                .replace("{test}", TEST)
                .replace("{log}", "_audit/resolver/logs/FILE-NEW-1-governance-cc.log")
                .replace("{sibling}",
                         "backend/domains/analytics/services/aggregation/"
                         "command_center_query_service.py"))
    path = os.path.join(CONTRACT_DIR, "FILE-NEW-1-governance-cc.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    print(f"froze FILE-NEW-1-governance-cc  sha256={digest}")

    # ---- mark INVALID blocks in the worklist -------------------------------
    wl = io.open(WL, encoding="utf-8").read()
    marks = 0
    for no, note in (
        ("5", "INVALID - `script_location` already present at "
              "`backend/alembic/alembic.ini:5`; `alembic -c alembic/alembic.ini "
              "heads` -> `20261001_0001 (head)` exit 0. Real defect is BARE "
              "invocation in `.github/workflows/deploy.yml:121,205` - a different "
              "file block. Third pass, orchestrator."),
        ("2", "PARTIAL - CFG-001 INVALID as written: Law 86's stated purpose "
              "(see its WHY column) is 'Prevents prod from inheriting dev "
              "defaults like debug=True', i.e. it forbids dev-default leakage, "
              "not three Python classes. The narrow guard fix delivers exactly "
              "that. TECH 20 presents one variable table with a per-variable "
              "Scope column, so one class scoped per environment is canonical."),
    ):
        pat = re.compile(r"(## FILE " + no + r": [^\n]*\n\n- \*\*Phase:\*\* [^\n]*\n"
                         r"- \*\*Depends on:\*\* [^\n]*\n- \*\*Findings:\*\* \d+\n"
                         r"- \*\*Effort:\*\* [^\n]*\n- \*\*Resolution status:\*\* )"
                         r"☐ PENDING")
        wl, n = pat.subn(r"\1" + note[:60] + " -- " + note[60:].replace("\\", "\\\\"), wl)
        marks += n
        print(f"  worklist FILE {no}: {'marked' if n else 'NO MATCH'}")
    io.open(WL, "w", encoding="utf-8").write(wl)

    # ---- log ----------------------------------------------------------------
    with open(os.path.join(LOGS, "orchestrator.log"), "a", encoding="utf-8") as fh:
        fh.write(f"{NOW} RISK_ACCEPTED user_chose_no_commit "
                 f"impact=D-SCOPE_and_D-CASCADE_unreliable "
                 f"mitigation=per-file SHA-256 baseline snapshot before every dispatch\n")
        fh.write(f"{NOW} MARK FILE 5 status=INVALID "
                 f"reason=script_location_exists_at_backend/alembic/alembic.ini:5\n")
        fh.write(f"{NOW} MARK FILE 2 CFG-001 status=INVALID "
                 f"reason=Law86_purpose_is_dev_default_leakage_not_three_classes\n")
        fh.write(f"{NOW} DISPATCH FILE-NEW-1-governance-cc phase=emergency "
                 f"nature=security sha256={digest} "
                 f"evidence=exploit_reproduced_3_payloads_20_call_sites\n")
    print(f"\nworklist marks applied: {marks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())