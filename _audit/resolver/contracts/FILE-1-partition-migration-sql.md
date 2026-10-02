# CONTRACT: FILE 1 backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py

- Frozen: 2026-10-02T18:37:11+00:00
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
  stub | disable | comment-out | remove | skip | bypass | silence |
swallow | hard-code | short-circuit | return-early-to-hide |
wrap-in-try-except-to-hide | touch-keep-hardened-file |
dispatch-blocked-by-contradiction | hand-edit-permissions-ts

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
- Static proof: `Select-String ... 'SELECT \* FROM public\.\{p\}'` returns 0 hits
  and `Select-String ... 'public\.\{p_id\}'` returns >= 1 hit
- `alembic -c alembic/alembic.ini heads` still returns exactly one head, exit 0
- Paste raw output of each.

## 16 Baseline snapshot
- Behaviors captured: 3 (detach / flat-table build / union copy + drop parent)
- Chains captured: 2
- Laws captured: 5
- Tests captured: 0
- Snapshot hash: recorded at run time in the log

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

- Command: `Select-String -Path <migration> -Pattern 'public\.\{p\}'`
- Expected output: no matches (exit count 0)
