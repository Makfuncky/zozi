# CONTRACT: FILE 4 backend/infrastructure/security/key_rotation.py

- Frozen: 2026-10-02T18:37:11+00:00
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
  stub | disable | comment-out | remove | skip | bypass | silence |
swallow | hard-code | short-circuit | return-early-to-hide |
wrap-in-try-except-to-hide | touch-keep-hardened-file |
dispatch-blocked-by-contradiction | hand-edit-permissions-ts

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
