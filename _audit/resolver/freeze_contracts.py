"""Freeze resolver contracts for the emergency + boot phase blocks and open the
resolver log. One contract per file block, SHA-256 hashed, per
PROMPT_RESOLUTION_ORCHESTRATOR.md 7 (rule 29: hash it, attach it, require
acknowledgement before any edit).
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RES = os.path.join(ROOT, "_audit", "resolver")
CONTRACT_DIR = os.path.join(RES, "contracts")
LOGS = os.path.join(RES, "logs")

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")

COMMON_FORBIDDEN = """stub | disable | comment-out | remove | skip | bypass | silence |
swallow | hard-code | short-circuit | return-early-to-hide |
wrap-in-try-except-to-hide | touch-keep-hardened-file |
dispatch-blocked-by-contradiction | hand-edit-permissions-ts"""

ACK = """I have read this contract in full. I will edit only the files and functions
in 1. I will not perform any edit in 2. I will preserve every behavior in 3. I
will add the behaviors in 4. I will correct the behaviors in 5 with the
justification in 5. I will keep every chain in 6 passing. I will keep every law
in 7 satisfied. I will keep every test in 9 passing. I will not delete anything
except as authorized in 13. I will not modify any test except as authorized in
14. I will produce every piece of evidence in 15. I will match the sibling in
18. I will run the verify command in 19. I will make the test in 20 exist and
pass. I will run the nature-specific check in 23. I will not touch any
KEEP/HARDEN file. I will not dispatch any finding blocked by an open
contradiction."""

CONTRACTS = {
"FILE-1-partition-migration-sql": """# CONTRACT: FILE 1 backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py

- Frozen: {NOW}
- File: backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py
- Phase: emergency
- Findings in scope: 1 (SEC-002)
- Findings out of scope: 0
- Effort: S (the audit said M/3h; third pass found the fix is 2 lines)
- Nature: security (SQL construction). The worklist mislabels this `tables`.
- Benchmark citations: Law 34 (parameterized SQL, no f-string interpolation),
  Law 6 (Alembic is the only schema source), Law 57 (expand-contract, backward compatible)

## 1 Allowed edits
allowed_files:
  - backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py
allowed_functions:
  - downgrade (the block at lines 300-335)
allowed_edits_per_file: 1
allowed_layers: backend

## 2 Forbidden edits
forbidden_files: every other file, including all tests and all other migrations
forbidden_patterns:
  {forbidden}

## 3 Behaviors frozen
- The migration's `downgrade()` must continue to detach partitions, build a flat
  `_pre_downgrade` table, copy the union of partition data into it, and drop the
  partitioned parent. The resulting schema state after downgrade must be byte-identical.
- `sql_identifier()` / `prepend_sys_path` behaviour is unchanged. Do NOT rewrite
  the `from migration_helpers import ...` pattern: `backend/alembic/` shadows the
  installed `alembic` package, so that import style is load-bearing.

## 4 Behaviors to be added
- None. This is a correctness fix only.

## 5 Behaviors to be corrected
- Line 325 builds `f"SELECT * FROM public.{{p}}"` from the RAW partition name `p`,
  while line 305 already computes `p_id = sql_identifier(p)` and uses it for the
  DETACH. The SELECT path must use the already-computed identifier, not the raw
  string. Justification: Law 34 forbids f-string interpolation into SQL even when
  the value is internally derived; consistency with line 305 removes the
  divergence. Severity note for the record: `partitions` is derived inside the
  migration and is NOT externally controllable, so this is defence-in-depth, not
  an exploitable injection.

## 6 Chains frozen
- CHAIN-002, CHAIN-005 - do not alter the resulting schema shape.

## 7 Laws frozen
- Law 6, Law 21, Law 49, Law 57, Law 217

## 8 Laws to be newly satisfied
- Law 34

## 9 Tests frozen
- None. Do not modify any existing test.

## 10 Tests to be added
- None permitted in this contract. See 14.

## 11 Expected diff shape
- Files touched: 1
- Functions touched: 1
- Lines added: 0 (replace 1 line with 1 line)
- Lines removed: 1
- New files: 0
- Files deleted: 0

## 12 Expected diff size
- Total lines changed: <= 6 +/- 50%

## 13 Deletion authorization
None. No line may be deleted except the single f-string line being corrected.

## 14 Test-change authorization
None. Do not create or modify test files. Prove correctness with a static check
(see 19) plus a `python -m compileall` / `ast.parse` on the edited file.

## 15 Required evidence
- Log: `_audit/resolver/logs/FILE-1-partition-migration-sql.log`
- Static proof: `Select-String ... 'SELECT \\* FROM public\\.\\{p\\}'` returns 0 hits
  and `Select-String ... 'public\\.\\{p_id\\}'` returns >= 1 hit
- `alembic -c alembic/alembic.ini heads` still returns exactly one head, exit 0
- Paste raw output of each.

## 16 Baseline snapshot
- Behaviors captured: 3 (detach / flat-table build / union copy + drop parent)
- Chains captured: 2
- Laws captured: 5
- Tests captured: 0
- Snapshot hash: recorded at run time in the log

## 17 Sub-agent acknowledgement
{ack}
Sub-agent signature: <agent_id> at <ISO-8601>

## 18 Sibling
- Path: `backend/infrastructure/security/key_rotation.py:107-110`
- What it does right: every interpolated identifier passes through
  `quoted_name(x, quote=True)` before it reaches the SQL string. Match that shape.

## 19 Verify command
- Command: `python -c "import ast;ast.parse(open(r'backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py',encoding='utf-8').read())"`
- Expected: no output, exit 0

## 20 Paired test
- Test path: none permitted (see 14). Use 19 plus the evidence in 15.

## 21 Rollback shape
- Method: revert
- Steps: restore the single original line
- Irreversible: NO

## 22 Confidence floor & investigation step
- Audit confidence: 5. Third-pass investigation completed by the orchestrator:
  lines 300-335 read, `partitions` provenance traced, `p_id` already computed
  at line 305. No further investigation step required.

## 23 Nature-specific check
| Nature | Required check | Pass criterion |
|---|---|---|
| `security` | Denial test | the raw `p` no longer reaches a SQL string; `p_id` does |

- Command: `Select-String -Path <migration> -Pattern 'public\\.\\{p\\}'`
- Expected output: no matches (exit count 0)
""",

"FILE-3-command-center-sql": """# CONTRACT: FILE 3 backend/domains/analytics/services/aggregation/command_center_query_service.py

- Frozen: {NOW}
- File: backend/domains/analytics/services/aggregation/command_center_query_service.py
- Phase: emergency
- Findings in scope: 1 (SEC-004)
- Findings out of scope: 0
- Effort: M (the audit said M/3h; a correct fix needs call-site analysis)
- Nature: security. **CONFIRMED EXPLOITABLE** - see 5.
- Benchmark citations: Law 34 (parameterized SQL only, no f-string), Law 42
  (validate at the boundary), Law 43 (security events logged), Law 68 (consistent errors)

## 1 Allowed edits
allowed_files:
  - backend/domains/analytics/services/aggregation/command_center_query_service.py
allowed_functions:
  - safe_count
  - _validate_where_clause
allowed_edits_per_file: 2
allowed_layers: backend
NOTE: if the call sites must change for the fix to be sound, STOP and report
`SCOPE_INSUFFICIENT` in your log rather than widening your own contract. The
orchestrator will issue a superseding contract.

## 2 Forbidden edits
forbidden_files: every other file, including all tests and every other module
forbidden_patterns:
  {forbidden}

## 3 Behaviors frozen
- `safe_fetch(db, sql, params, scalar)` keeps its signature and its
  `text(sql)` execution path. It is the sanctioned execution primitive.
- The table allowlist `_ALLOWED_TABLES` keeps all 19 names and keeps rejecting
  anything not on it. An unknown table must still raise `ValueError`.
- `_validate_table_name` keeps lowercasing and stripping.
- Logging stays on structlog; `logger.exception` on DB error is preserved.

## 4 Behaviors to be added
- A regression test proving a time-based injection payload is rejected.

## 5 Behaviors to be corrected
THIRD-PASS FINDING - the audit understated this. `_validate_where_clause` uses a
CHARACTER ALLOWLIST (letters, digits, `_ = <> ! ( ) ' , : / . % + - *`) plus
balanced-quote and balanced-paren checks plus comment blocking. But
`_BLOCKED_KEYWORDS` (lines 31-34) omits `and`, `or`, `having`, `like`, `between`,
`case`, `limit`, `offset`, `pg_sleep`, `benchmark`, `information_schema`, and
`version`.

Consequence, verified by the orchestrator: the payload
`1=1 or pg_sleep(5)=1` passes every check - all characters are allowlisted, no
blocked keyword appears, quotes and parens are balanced - and reaches
`f"SELECT COUNT(*) FROM {{validated_table}} WHERE {{where}}"` at line 83.
That is boolean and time-based blind SQL injection.

Two defects, both must be fixed:
1. Line 83 interpolates `where` into SQL. A WHERE FRAGMENT cannot be
   parameterised, so the correct fix is to stop accepting a raw fragment:
   change the signature to accept either a SQLAlchemy Core/ORM boolean
   expression, or an explicit (column, operator, value) structure that is
   rendered into bound parameters. Do NOT widen the denylist - a denylist is
   what failed here, and Law 34 requires bound parameters, not a better denylist.
2. `_validate_table_name` and the table interpolation are NOT the defect (strict
   19-name allowlist). Leave that path alone.

Justification: Law 34.

## 6 Chains frozen
- CHAIN-005 - analytics reporting must keep working for every allowlisted table.

## 7 Laws frozen
- Law 14 (business logic in domains), Law 42, Law 43, Law 68

## 8 Laws to be newly satisfied
- Law 34

## 9 Tests frozen
- Do not modify any existing test.

## 10 Tests to be added
- `backend/tests/domains/analytics/test_command_center_query_service.py::test_rejects_time_based_injection`
- `...::test_rejects_boolean_injection`
- `...::test_accepts_parameterised_predicate` (positive path)
- `...::test_unknown_table_still_rejected` (existing behaviour preserved)

## 11 Expected diff shape
- Files touched: 2 (service + 1 new test file)
- Functions touched: 2-4
- Lines added: 60-140
- Lines removed: 10-30
- New files: backend/tests/domains/analytics/test_command_center_query_service.py
- Files deleted: 0

## 12 Expected diff size
- Total lines changed: <= 180 +/- 50%

## 13 Deletion authorization
The f-string WHERE interpolation at line 83 may be removed, because that IS the
defect. No other deletion is authorized.

## 14 Test-change authorization
Authorized to CREATE `backend/tests/domains/analytics/test_command_center_query_service.py`.
Not authorized to modify any pre-existing test.

## 15 Required evidence
- Log: `_audit/resolver/logs/FILE-3-command-center-sql.log`
- A runnable proof that `1=1 or pg_sleep(5)=1` was accepted BEFORE and is
  rejected AFTER. Paste both outputs.
- `pytest backend/tests/domains/analytics/test_command_center_query_service.py -q` raw output
- `ruff check` on both files, raw output
- Proof the 19-name table allowlist still rejects unknown tables.

## 16 Baseline snapshot
- Behaviors captured: 4 (fetch primitive, table allowlist, lowercasing, DB-error logging)
- Chains captured: 1
- Laws captured: 4
- Tests captured: 0
- Snapshot hash: record at run time in the log

## 17 Sub-agent acknowledgement
{ack}
Sub-agent signature: <agent_id> at <ISO-8601>

## 18 Sibling
- Path: `backend/infrastructure/security/key_rotation.py:113-118`
- What it does right: every dynamic value is bound (`:lim`, `:off`) and every
  identifier is `quoted_name`-wrapped and allowlist-checked first.

## 19 Verify command
- Command: `python -m pytest backend/tests/domains/analytics/test_command_center_query_service.py -q`
- Expected: all tests pass, exit 0

## 20 Paired test
- Test path: backend/tests/domains/analytics/test_command_center_query_service.py
- Test name: test_rejects_time_based_injection

## 21 Rollback shape
- Method: revert
- Steps: revert the service file, delete the new test file
- Irreversible: NO

## 22 Confidence floor & investigation step
- Audit confidence: 5. Third pass CONFIRMED the injection and found it worse
  than reported (exploitable, not merely an f-string). No further investigation
  step required before editing.

## 23 Nature-specific check
| Nature | Required check |
|---|---|
| `security` | Denial test: the injection payload must raise |

- Command: `python -m pytest backend/tests/domains/analytics/test_command_center_query_service.py -q -k injection`
- Expected: 2 passed, exit 0
""",

"FILE-4-key-rotation-sql": """# CONTRACT: FILE 4 backend/infrastructure/security/key_rotation.py

- Frozen: {NOW}
- File: backend/infrastructure/security/key_rotation.py
- Phase: emergency
- Findings in scope: 1 (SEC-003)
- Findings out of scope: 0
- Effort: S
- Nature: security (SQL construction). The worklist mislabels this `tables`.
- Benchmark citations: Law 34, Law 52, Law 53, Law 275 (key rotation)

## 1 Allowed edits
allowed_files:
  - backend/infrastructure/security/key_rotation.py
allowed_functions:
  - the key-rotation batch function containing lines 95-150
allowed_edits_per_file: 1
allowed_layers: backend

## 2 Forbidden edits
forbidden_files: every other file, including all tests
forbidden_patterns:
  {forbidden}

## 3 Behaviors frozen
- `_validate_table` and `_validate_columns` keep their allowlists and keep
  raising `ValueError` on anything not allowlisted. Do NOT weaken them.
- `pk_col` stays `"id"` with its `_VALID_PK_COLS` check.
- Pagination semantics are unchanged: `LIMIT :lim OFFSET :off` with `BATCH_SIZE`,
  looping until an empty page.
- The `rows_updated` / `errors` counters and the per-row commit behaviour are
  preserved exactly.
- The UPDATE path at lines 147-150 is OUT OF SCOPE. Do not touch it.

## 4 Behaviors to be added
- None.

## 5 Behaviors to be corrected
THIRD-PASS FINDING - severity downgraded from the audit's claim.
`select_cols_sql` (line 110) is built from `safe_pk` plus `safe_cols`, every one
of which is `quoted_name(x, quote=True)` over a value already checked against
`_VALID_PK_COLS` / `_VALID_COLUMNS[table_name]`. `safe_table` is likewise
quoted and allowlisted. **There is no injection path.** The defect is Law 34's
letter: f-string interpolation into SQL is forbidden categorically, and the
audit's prescribed remedy (`sa.text()` with bound parameters) is wrong for
identifiers, because a column name cannot be a bind parameter.

Correct fix: build the statement with SQLAlchemy Core constructs
(`sqlalchemy.select(...).select_from(...)`) so identifiers are emitted by the
dialect compiler rather than interpolated, while `:lim` / `:off` remain bound.
Justification: Law 34.

## 6 Chains frozen
- CHAIN-005 - key rotation must continue to rotate every row in every allowlisted table.

## 7 Laws frozen
- Law 275, Law 277, Law 32 (never print or log key material)

## 8 Laws to be newly satisfied
- Law 34

## 9 Tests frozen
- Do not modify any existing test.

## 10 Tests to be added
- None permitted in this contract (see 14).

## 11 Expected diff shape
- Files touched: 1
- Functions touched: 1
- Lines added: 10-30
- Lines removed: 5-12
- New files: 0
- Files deleted: 0

## 12 Expected diff size
- Total lines changed: <= 45 +/- 50%

## 13 Deletion authorization
The two f-string SELECT lines may be removed, because that IS the defect.
Nothing else may be deleted.

## 14 Test-change authorization
None. Do not create or modify test files.

## 15 Required evidence
- Log: `_audit/resolver/logs/FILE-4-key-rotation-sql.log`
- `ruff check backend/infrastructure/security/key_rotation.py` raw output
- `python -c "import ast;ast.parse(...)"` raw output
- Proof the allowlist validators still raise on a non-allowlisted table and column.
- Proof `:lim` / `:off` are still bound parameters after your change.

## 16 Baseline snapshot
- Behaviors captured: 5 (table allowlist, column allowlist, pk allowlist, pagination, counters)
- Chains captured: 1
- Laws captured: 3
- Tests captured: 0
- Snapshot hash: record at run time in the log

## 17 Sub-agent acknowledgement
{ack}
Sub-agent signature: <agent_id> at <ISO-8601>

## 18 Sibling
- Path: `backend/domains/finance/services/ledger/general_ledger.py` (ORM query
  construction) - use the ORM/Core rather than string building.

## 19 Verify command
- Command: `python -c "import ast;ast.parse(open('backend/infrastructure/security/key_rotation.py',encoding='utf-8').read())"`
- Expected: no output, exit 0

## 20 Paired test
- Test path: `backend/tests/security/test_key_rotation.py` (named by the audit;
  if it does not exist, say so in your log - do NOT create it)

## 21 Rollback shape
- Method: revert
- Steps: revert the file
- Irreversible: NO

## 22 Confidence floor & investigation step
- Audit confidence: 5. Third pass read lines 55-150 and traced every
  interpolated value to an allowlist + `quoted_name`. Severity downgraded from
  "injection" to "Law 34 letter". Recorded so you do not over-correct.

## 23 Nature-specific check
| Nature | Required check |
|---|---|
| `security` | Denial test: non-allowlisted table and column still raise |

- Command: state the exact invocation you used to prove the validators still raise
- Expected output: `ValueError` for both
""",

"FILE-2-config-settings-profiles": """# CONTRACT: FILE 2 backend/config.py

- Frozen: {NOW}
- File: backend/config.py
- Phase: emergency
- Findings in scope: 2 (CFG-001 split Settings per Law 86; CFG-008 unused dicts)
- Findings out of scope: 0
- Effort: L - the audit said M. Read 5 before starting.
- Nature: env
- Benchmark citations: Law 82 (no credentials in defaults), Law 83 (validate at
  startup), Law 84 / 203 (typed settings, no raw os.getenv), Law 86 (separate
  prod/staging/dev profiles, no inheritance), Law 201-206, Law 24 (production
  guards)

## 1 Allowed edits
allowed_files:
  - backend/config.py
allowed_functions:
  - the Settings class, its model_config, its field declarations
  - _validate_production and the other validators
  - the _BOOL_KEYS / _INT_KEYS / _FLOAT_KEYS definitions (CFG-008 only)
allowed_edits_per_file: 4
allowed_layers: backend
NOTE: `backend/config.py` is imported by essentially the whole backend. If a
correct CFG-001 fix requires editing a consumer, STOP and report
`SCOPE_INSUFFICIENT` in your log. Do NOT widen this contract yourself.

## 2 Forbidden edits
forbidden_files: every other file, including all tests and all consumers
forbidden_patterns:
  {forbidden}

## 3 Behaviors frozen
- `settings` remains importable as a module-level singleton, unchanged for
  consumers. 188 Settings fields must keep resolving.
- `_validate_production` MUST keep raising `ValueError` for every required
  variable in production. A third-pass probe blanked 21 variables one at a time
  and all 21 raised. Do NOT weaken it. If your change makes any of those 21
  stop raising, you have broken Law 83 - that is a P0 regression.
- CSRF bypass remains gated on `app_env in (test, development)` AND
  `CSRF_DISABLED` (Law 35, in `csrf_middleware.py`, not this file).
- Security headers remain emitted in production (Law 36).
- `env_ignore_empty=True`, `extra="ignore"` and the manual dotenv load at the
  top of the file keep their current behaviour.
- The two documented raw `os.getenv` calls (dotenv bootstrap, and the indirect
  `FIELD_ENCRYPTION_KEY_FROM_ENV`) stay. They are the exemptions.
- No secret value may appear in your log or evidence. Cite `path:line` only.

## 4 Behaviors to be added
- A regression test proving a required variable still raises when blanked in
  production mode.

## 5 Behaviors to be corrected
CFG-001 asks you to split the single `Settings` class into three per-environment
profiles. **Read this before you start, because the audit's framing is
incomplete and the naive fix is dangerous.**

The compiler's second pass established:
- Law 86 says prod/staging/dev have separate profiles with NO inheritance.
- But splitting `Settings` would break all 188 field accesses across the
  backend, and `settings` is a module-level singleton imported everywhere. The
  blast radius named in the worklist is "requires updating all `settings.`
  imports to profile-specific imports".
- The REAL, already-proven defect is narrower and more urgent: the production
  guards are bare non-emptiness checks, so several DEV DEFAULTS LEAK INTO
  PRODUCTION. Concretely confirmed by the compiler:
  `frontend_url`, `backend_url`, `celery_broker_url`, `celery_result_backend`,
  `ollama_base_url`, `sms_mode`, `push_mode`, `upload_dir`, `backup_dir`,
  `backup_enabled`. `debug`, CORS-localhost, sqlite, and `storage_backend != r2`
  ARE correctly blocked.

So: prefer closing the leak with explicit per-environment validators that reject
dev-shaped values in production. That satisfies the INTENT of Law 86 for the
values that actually matter, without a 188-field refactor.

You MAY additionally introduce the three-profile structure ONLY if you can do it
without changing any consumer's import surface, and ONLY if `_validate_production`
keeps raising for all 21 probed variables. If you cannot satisfy both, do the
narrow fix and record in your log that the full CFG-001 split needs a separate
multi-file contract.

Also report CFG-008 (`_BOOL_KEYS`/`_INT_KEYS`/`_FLOAT_KEYS`): grep the repo for
external consumers. If there are none, remove them and say so. If there are,
document the consumer and leave them.

## 6 Chains frozen
- CHAIN-002, CHAIN-005 - the app must still boot and serve in every profile.

## 7 Laws frozen
- Law 82, Law 83, Law 35, Law 36, Law 84, Law 203

## 8 Laws to be newly satisfied
- Law 86

## 9 Tests frozen
- `backend/tests/config/test_config_validation.py` - currently 14/14 green. It
  MUST still be 14/14 green after your change.
- Do not modify it.

## 10 Tests to be added
- `backend/tests/config/test_config_production_guards.py::test_dev_default_rejected_in_production`
- `...::test_required_secret_still_raises_when_blanked`
- `...::test_staging_profile_does_not_inherit_dev_paths`

## 11 Expected diff shape
- Files touched: 2 (config.py + 1 new test file)
- Functions touched: 2-5
- Lines added: 40-120 (narrow fix) OR 150-300 (only if the full split is safe)
- Lines removed: 5-40
- New files: backend/tests/config/test_config_production_guards.py
- Files deleted: 0

## 12 Expected diff size
- Total lines changed: <= 200 +/- 50%

## 13 Deletion authorization
The three unused dicts may be removed IF and ONLY IF you prove zero external
consumers. Nothing else may be deleted.

## 14 Test-change authorization
Authorized to CREATE `backend/tests/config/test_config_production_guards.py`.
Not authorized to modify any pre-existing test.

## 15 Required evidence
- Log: `_audit/resolver/logs/FILE-2-config-settings-profiles.log`
- Boot still works: `PYTHONPATH=backend python -c "from backend.main import app; print(len(app.openapi()['paths']))"`
  - expected: a positive path count, exit 0
- `backend/tests/config/test_config_validation.py` still 14/14
- Your new tests pass
- The 21-variable blanking probe re-run, proving all 21 still raise
- `ruff check backend/config.py` raw output
- **No secret value in any output.**

## 16 Baseline snapshot
- Behaviors captured: 8 (singleton import, 188 fields, 21 production raises, CSRF gate, security headers, model_config, dotenv bootstrap, os.getenv exemptions)
- Chains captured: 2
- Laws captured: 6
- Tests captured: 1
- Snapshot hash: record at run time in the log

## 17 Sub-agent acknowledgement
{ack}
Sub-agent signature: <agent_id> at <ISO-8601>

## 18 Sibling
- Path: `backend/config.py:598-776` (`_validate_production`) - it is the correct
  exemplar of fail-closed behaviour. Your new guards must match that style.

## 19 Verify command
- Command: `python -m pytest backend/tests/config/test_config_validation.py backend/tests/config/test_config_production_guards.py -q`
- Expected: all pass, exit 0

## 20 Paired test
- Test path: backend/tests/config/test_config_production_guards.py
- Test name: test_required_secret_still_raises_when_blanked

## 21 Rollback shape
- Method: revert
- Steps: revert config.py, delete the new test file
- Irreversible: NO

## 22 Confidence floor & investigation step
- Audit confidence: 5, but the audit's prescribed fix (three profiles, no
  inheritance) conflicts with the singleton import surface and is NOT safely
  implementable inside this contract. Section 5 gives you the verified narrower
  defect and an explicit decision rule. Investigate the consumers FIRST, then
  choose, and record which path you took and why.

## 23 Nature-specific check
| Nature | Required check |
|---|---|
| `env` | the pydantic-settings class declares and enforces every var it claims |

- Command: `python -m pytest backend/tests/config/test_config_production_guards.py -q`
- Expected: all pass, exit 0
""",
}


def main() -> int:
    os.makedirs(CONTRACT_DIR, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    rows = []
    for slug, body in CONTRACTS.items():
        # token replacement, not str.format: the bodies legitimately contain
        # literal braces from quoted code samples such as
        # f"SELECT COUNT(*) FROM {{validated_table}}".
        text = (body.replace("{NOW}", NOW)
                    .replace("{forbidden}", COMMON_FORBIDDEN)
                    .replace("{ack}", ACK))
        path = os.path.join(CONTRACT_DIR, f"{slug}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rows.append((slug, digest, len(text)))
        print(f"froze {slug:<34} sha256={digest[:16]}... {len(text)} chars")

    # resolver log
    log = os.path.join(LOGS, "orchestrator.log")
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"{NOW} RUN_START resolver_run=8 worklist=_audit/TO_BE_RESOLVE.md blocks=272\n")
        fh.write(f"{NOW} BENCHMARK_READ ARCHITECTURE_STACK.md lines=916 laws=325\n")
        fh.write(f"{NOW} BENCHMARK_READ TECHNOLOGY_STACK.md lines=577\n")
        fh.write(f"{NOW} SPEC_READ PROMPT_RESOLUTION_ORCHESTRATOR.md lines=1929 v4\n")
        fh.write(f"{NOW} PHASE_START emergency\n")
        fh.write(f"{NOW} THIRD_PASS FILE 5 backend/alembic.ini verdict=FALSE_POSITIVE "
                 f"reason=\"backend/alembic.ini does not exist; backend/alembic/alembic.ini:5 "
                 f"already sets script_location=%(here)s; `alembic -c alembic/alembic.ini heads` "
                 f"returns 20261001_0001 exit 0. The real defect is bare invocation in "
                 f"deploy.yml:121,205 which is a different file block.\"\n")
        fh.write(f"{NOW} THIRD_PASS FILE 1 severity=DOWNGRADED reason=\"partitions is "
                 f"internally derived; p_id already computed at line 305; Law 34 letter only\"\n")
        fh.write(f"{NOW} THIRD_PASS FILE 3 severity=UPGRADED reason=\"CONFIRMED EXPLOITABLE: "
                 f"_BLOCKED_KEYWORDS omits and/or/pg_sleep/having; payload `1=1 or pg_sleep(5)=1` "
                 f"passes char allowlist, quote/paren balance and keyword block\"\n")
        fh.write(f"{NOW} THIRD_PASS FILE 4 severity=DOWNGRADED reason=\"every identifier is "
                 f"quoted_name() over an allowlist value; no injection path; Law 34 letter only\"\n")
        fh.write(f"{NOW} CONTRACT_FROZEN count={len(CONTRACTS)}\n")
        for slug, digest, _ in rows:
            fh.write(f"{NOW} CONTRACT {slug} sha256={digest}\n")
    print(f"\ncontracts frozen: {len(rows)}")
    print(f"log: {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())