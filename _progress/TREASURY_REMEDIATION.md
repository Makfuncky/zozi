# Treasury Module Remediation — Progress

## Selected isolated area: TREASURY
Rationale: treasury & finance dirs were all COLD (no edits in last 30 min) while
the concurrent agent is editing comms/employee/fraud/services/controllers.
Avoided all HOT files. Verified by mtime before each edit.

## Files modified (all COLD — safe, no clobber risk)
1. `backend/services/treasury/__init__.py`  (NEW) — package marker (fixes P5)
2. `backend/controllers/treasury/__init__.py` (NEW) — package marker (fixes P5)
3. `backend/routers/treasury_api.py` (NEW) — re-export of the 4 query fns from
   `services.treasury.treasury_query_service` (fixes the broken
   `from routers.treasury_api import ...` in `routers/treasury.py` which crashed
   the whole app on router load — a pre-existing W1 relocation bug).
4. `backend/services/write_helpers.py` (NEW) — add_and_flush / commit_and_refresh /
   commit_only session helpers (referenced by treasury_query_service but never
   created; standard SQLAlchemy wrappers, reusable).
5. `backend/services/treasury/treasury_query_service.py` — fixed 3 broken imports:
   - `from utils.audit_log import ...`  -> `from utils.audit import ...` (module never existed)
   - `from services.write_helpers import ...` -> now valid (module created above)
   - removed dangling `from services.treasury.treasury_service import calculate_eosb`
     (module never existed; symbol unused in file)

## Validation performed
- `import services.treasury`, `controllers.treasury`, `routers.treasury_api` -> OK
- 4 re-exported fns resolve with correct signatures (db / db,country_code).
- `py_compile` clean on edited files.
- Could NOT run `backend/tests/test_auto_payout_sweep.py`: it errors in conftest
  fixture setup with `NoReferencedTableError: 'users'` because the test harness
  imports `models`, which transitively needs the BROKEN `auth_controller`
  (see BLOCKER below). This is app-wide, not treasury.

## BLOCKER (app-wide, OUT OF TREASURY SCOPE — flagged, not fixed)
`backend/controllers/auth_controller.py` imports `services.auth_write_service`,
a module that DOES NOT EXIST (large, 30+ fns). This breaks:
- `import main` (whole app boot)
- `import routers.treasury` (transitively via auth_controller)
- test conftest model metadata build (User table never registers -> FK error)
`auth_controller.py` is COLD (00:19) so fixing it is safe, but it is a large
reconstruction, NOT a treasury concern. Left for a dedicated auth isolated fix.

## Treasury findings NOT addressed (intentionally, to avoid HOT files / auth blocker)
- `routers/admin_treasury.py` DG/CIR1/CIR2: router reaches `db.database`,
  `models`, `services.treasury_engine` directly with inline queries.
  -> Fixing requires moving logic into services/controllers. Many endpoints.
  -> DEPENDS on `db` package (HOT: db/mixins.py at 02:15) -> avoided.
- `db/treasury_seeder.py` CIR1: `db -> models` circuit. `db` package is HOT -> avoided.
- A2 orphaned `controllers/treasury/*` controllers: no inbound imports.
  -> Would need wiring into routers (which depend on broken auth layer) -> deferred.

## Next (if continuing treasury):
- After the auth_write_service blocker is fixed, re-bootstrap app and re-run
  `scripts/system_trackers/system_architecture_audit.py` to confirm treasury
  import findings (P5 x2, W1) cleared; then tackle admin_treasury router->service
  refactor as its own isolated step.
