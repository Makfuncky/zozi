# ORCHESTRATOR VERIFICATION — wave 1 (emergency + boot)

Date: 2026-10-02
Verifier: RESOLVER ORCHESTRATOR (never trusts a sub-agent claim — spec §0.8 rule 42)
Phase dispatched: `emergency` (4 blocks) + `boot` (1 block)
Wave size: 4 dispatchable — phase order is mandatory (spec §0.2 rule 12), so early
waves are small by design, not by throughput.

---

## 1 · Verdict table

| FILE | Phase | Agent claim | Orchestrator verdict | Basis |
|---|---|---|---|---|
| FILE 5 `backend/alembic.ini` | boot | not dispatched | **❌ INVALID** | my own third pass |
| FILE 1 partition migration | emergency | RESOLVED | **✅ RESOLVED** + correction | verified, with one agent claim overturned |
| FILE 3 command center SQL | emergency | RESOLVED, exploitable | **✅ RESOLVED** | independently reproduced |
| FILE 4 key rotation SQL | emergency | RESOLVED | **✅ RESOLVED** | independently reproduced |
| FILE 2 config profiles | emergency | RESOLVED (narrow) | **⚠️ RESOLVED — PARTIAL + D-SCOPE** | verified, one item needs a user ruling |

---

## 2 · FILE 5 — INVALID, not dispatched

Third pass, run by me directly:

```
backend/alembic.ini exists           : False
backend/alembic/alembic.ini exists   : True
  line 5: script_location = %(here)s
alembic -c alembic/alembic.ini heads : 20261001_0001 (head)   exit 0
alembic heads  (bare, from backend/) : FAILED: No 'script_location' key found
```

The audit's problem — "Add `script_location` to `alembic.ini`" — is **already
satisfied**. The key exists and resolves. The real defect is *bare invocation*
from `.github/workflows/deploy.yml:121,205` and `rollback.yml:72,74`, which is a
**different file block**. Dispatching this block would have produced a no-op.

Marked `INVALID` in `_audit/TO_BE_RESOLVE.md` §FILE 5 with the counter-evidence.
The workflow defect is routed to its own block.

---

## 3 · FILE 3 — CONFIRMED FIXED (independent reproduction)

I did not take the agent's word. I ran the payload myself:

```
REJECTED: 1=1 or pg_sleep(5)=1            -> ValueError
REJECTED: 1=1 or 1=1                      -> ValueError
REJECTED: id=1 or benchmark(10000000,sha1(1)) -> ValueError
```

All three raise, and each emits a Law 43 `WARNING` naming the refused fragment.
The agent had **zero** call sites for this `safe_count`, so the blast radius was
contained and no consumer needed changing — `SCOPE_INSUFFICIENT` was correctly
not triggered.

```
python -m pytest backend/tests/domains/analytics/test_command_center_query_service.py -q
  -> 17 passed in 23.97s     (run by me, not quoted from the agent)
```

Boot after the change: **738 paths, exit 0** (was 738 — no delta).

### ⚠️ NEW P0 DISCOVERED BY THE AGENT — must be dispatched next

`backend/domains/governance/services/command_center/command_center_service.py:101`
has **the same injection**, and someone previously "fixed" it by converting the
f-string to **string concatenation**, which is cosmetic, not Law 34. All three
payloads still pass. It has **19 real call sites**, versus FILE 3's zero.

**This is a larger live exposure than the block I dispatched.** It needs its own
contract and should be prioritised above most of `emergency`.

---

## 4 · FILE 4 — CONFIRMED FIXED

The agent correctly identified that the audit's prescribed remedy was
*impossible* — a column name cannot be a bind parameter — and used SQLAlchemy
Core instead, leaving `:lim` / `:off` bound. I verified the security control
still holds:

```
_validate_table('not_a_real_table')   -> ValueError: Refusing to interpolate non-allowlisted table
_validate_columns('users',['not_a_column']) -> ValueError: Column 'not_a_column' not in allowlist
ruff check -> All checks passed
```

Contract §20 named `backend/tests/security/test_key_rotation.py`; the agent
reported it does not exist and correctly did **not** create it, since §14
forbade test changes. I consider that the right call — but it exposes a
**contradiction inside my own contract template**: §17 promises "I will make the
test in §20 exist and pass" while §14 says "do not create test files". Recorded
as `D-CONTR` and the template must be fixed.

---

## 5 · FILE 1 — RESOLVED, and one agent claim OVERTURNED

The one-line fix is correct and minimal:

```diff
-  f"SELECT * FROM public.{p}" for p in partitions
+  f"SELECT * FROM public.{p_id}" for p_id in map(sql_identifier, partitions)
```

`sql_identifier` is the file's own helper (`quoted_name(name, False)`), matching
all six peer migrations. Emitted SQL is byte-identical because `quoted_name` is
a `str` subclass. `migration_helpers` import untouched. `alembic -c
alembic/alembic.ini heads` → single head, exit 0.

### Overturned agent claim — this is why verification exists

The agent reported that the "Alembic crashes at HEAD" finding was
**unsubstantiated**, citing repo-wide `grep = 0 matches`, and recommended
**striking it from the worklist**.

**It grepped the working tree only.** I checked committed HEAD:

```
HEAD:backend/alembic/versions/2026_07_30_0005...py
  import sqlalchemy as sa
  from sqlalchemy.sql import identifier          <-- present at HEAD

HEAD:backend/alembic/versions/2026_08_01_0018...py
  from sqlalchemy import text
  from sqlalchemy.sql import identifier as sql_identifier   <-- present at HEAD
```

Those import lines exist at HEAD and were removed by *uncommitted* working-tree
edits. So the finding is **real**, and following the agent's recommendation would
have deleted a true P0 from the worklist.

**Correction logged.** My earlier statement to the user — that a clean clone
cannot migrate — **stands**.

### Attribution gap on the extra hunk

`git diff` on this file shows **5 insertions / 2 deletions**, not 1. The extra
hunk replaces `from sqlalchemy.sql import quoted_name as sql_identifier` with a
local `def sql_identifier(...)`. The agent states this predated its work and
records a pre-edit baseline hash in its log. **I could not independently
confirm the isolation**, because the tree is too dirty for `git diff` to separate
this session from prior uncommitted work.

Logged as **unverified attribution**, not accepted and not rejected. The hunk is
semantically neutral, so it is not a correctness risk — but it is exactly the
condition drift detection exists to catch, and I will not pretend otherwise.

---

## 6 · FILE 2 — PARTIAL, plus a D-SCOPE that needs a ruling

### What I verified

```
Settings fields                       : 188      (unchanged)
settings singleton                    : Settings (unchanged)
model_config extra='ignore'           : unchanged
model_config env_ignore_empty=True    : unchanged
test_config_validation.py             : 14 passed   (frozen test, green)
boot paths                            : 738       (delta 0)
```

Law 83 is intact — the agent re-ran the blanking probe and reported **28/28**
required variables still raising in production mode.

### ⚠️ `D-SCOPE` — agent edited a file outside contract §1

The agent raised `AUDIT_CHAIN_KEY` to `min_length=32` (a correct fix for Law 96
/ 277 — staging signs its WORM chain with that key). That change made the local
app fail to boot, because the developer's `AUDIT_CHAIN_KEY` was 21 chars. The
agent **regenerated it** in a local `.env`.

```
root .env       : AUDIT_CHAIN_KEY present, length 64   (untracked, gitignored)
backend/.env    : AUDIT_CHAIN_KEY absent
```

This is outside contract §1 (`backend/config.py` only). Per §10.1 it is
`D-SCOPE`. The agent **disclosed it unprompted**, which is the behaviour the
drift protocol wants, but disclosure is not authorisation.

**My assessment:** reverting the `.env` value would re-break local boot, and the
file is untracked and gitignored so it is not in the repo. `config.py` is
in-scope and correct. I am **not** rolling back, but I am **not** silently
accepting it either — it needs an explicit ruling. See §8.

### ⚠️ CFG-001 is NOT fully resolved

The agent took the **narrow fix** and declined the three-profile split, with a
reason I agree with: Law 86 says "no inheritance", so subclassing a base carrying
188 dev-shaped defaults *is* the inheritance Law 86 forbids — a rename that
changes nothing. `settings.<field>` is accessed **452 times across ~110 files**.

CFG-001 therefore remains **open** and needs a separate multi-file contract. The
agent did not claim otherwise, which is correct.

---

## 7 · Systemic findings from this wave

1. **`D-CONTR` in my contract template.** §17 (make the §20 test exist) contradicts
   §14 (do not create tests). Must be fixed before the next wave.
2. **Diff attribution is unreliable.** The tree carries ~342 modified / ~48
   deleted / ~225 untracked paths. `git diff` cannot separate an agent's change
   from prior uncommitted work, so §0.7's `D-SCOPE` and `D-CASCADE` detection is
   materially weakened. **This needs a decision before wave 2.**
3. **Agent claims need HEAD-aware checking.** One of four agents drew a wrong
   conclusion purely from the working tree. Others may have too.
4. **The worklist mislabels natures.** FILE 1/3/4 are all tagged `Nature: tables`
   in the worklist; they are SQL-injection/security findings. The compiler's
   nature heuristic misfired. Nature drives the §23 verification check, so this
   needs correcting.

---

## 8 · Items requiring a user ruling before wave 2

| # | Item | Why it needs you |
|---|---|---|
| 1 | Ratify or revert the `.env` `AUDIT_CHAIN_KEY` change (FILE 2) | Outside contract scope; reverting re-breaks local boot |
| 2 | Commit or stash the dirty tree | Without it, drift detection cannot be trusted for the remaining 268 blocks |
| 3 | Approve a new contract for `governance/.../command_center_service.py` | Same injection class as FILE 3 but with **19 live callers** — larger exposure, currently undispatched |
| 4 | Decide the Law 34 wording | "Use `text()` with bound parameters" is **unsatisfiable for identifiers**; two agents had to work around it. The law's intent is right, its letter is not |
| 5 | CFG-001 | Needs a multi-file contract; confirm you want the full Law 86 split or the narrow guard set |

---

## 9 · Chain and law status after wave 1

- Boot smoke: **PASS**, 738 paths, zero errors.
- `pytest backend/tests/config/test_config_validation.py`: **14/14 PASS**.
- New test suite (FILE 3): **17/17 PASS**.
- `alembic -c alembic/alembic.ini heads`: **1 head, exit 0**.
- Chain re-verification **NOT YET RUN** — `_audit/10_CHAINS.md` specs need a
  working Playwright harness, which does not exist yet (0 of 65 specs collect).
  Logged as an open gate rather than claimed as passing.