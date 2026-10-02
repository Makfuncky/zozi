# CONTRACT: FILE 2 backend/config.py

- Frozen: 2026-10-02T18:37:11+00:00
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
  stub | disable | comment-out | remove | skip | bypass | silence |
swallow | hard-code | short-circuit | return-early-to-hide |
wrap-in-try-except-to-hide | touch-keep-hardened-file |
dispatch-blocked-by-contradiction | hand-edit-permissions-ts

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
