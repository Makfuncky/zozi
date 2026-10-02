# CONTRACT: FILE 3 backend/domains/analytics/services/aggregation/command_center_query_service.py

- Frozen: 2026-10-02T18:37:11+00:00
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
  stub | disable | comment-out | remove | skip | bypass | silence |
swallow | hard-code | short-circuit | return-early-to-hide |
wrap-in-try-except-to-hide | touch-keep-hardened-file |
dispatch-blocked-by-contradiction | hand-edit-permissions-ts

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
I have read this contract in full. I will edit only the files and functions
in 1. I will not perform any edit in 2. I will preserve every behavior in 3. I
will add the behaviors in 4. I will correct the behaviors in 5 with the
justification in 5. I will keep every chain in 6 passing. I will keep every law
in 7 satisfied. I will keep every test in 9 passing. I will not delete anything
except as authorized in 13. I will not modify any test except as authorized in
14. I will produce every piece of evidence in 15. I will match the sibling in
18. I will run the verify command in 19. I will make the test in 20 exist and
pass. I will run the nature-specific check in 23. I will not touch any
KEEP/HARDEN file. I will not dispatch any finding blocked by an open
contradiction.
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
