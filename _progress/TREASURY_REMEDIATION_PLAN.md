# Treasury Domain Remediation Plan

**Module:** treasury (worst-resolved domain after platform/logistics)
**Audit baseline:** 🔴 39 RED / 🟡 86 YELLOW (§8 treasury file findings)
**Approach:** Realign routers → controllers → services → models per Grid Line §1.
Keep every router's exported `router` object name and route paths intact so
`main.py` registration and any `lib/api` frontend callers keep working.

## Layer contract (Grid Line §1)
- routers: import controllers / schemas / auth deps / `get_db` only. NO `db.query`, NO `db.add/commit`, NO model instantiation.
- controllers: import services / models / `get_db` / auth deps. Orchestrate; delegate writes to services (which `add/commit`).
- services: import models / `get_db` / utils / providers / redis. Own `add/commit`.
- providers: import `providers._base` / utils / settings only.

## Findings verified (authentic)
| File | RED | YEL | Key violations |
|------|-----|-----|----------------|
| admin_treasury_reporting.py | 7 | 16 | CG1 models in router, CIR2 router→services direct, CA1 name mismatch, QUAL3 oversized (1788 ln), MET2 I=1.00, DBA32 OFFSET |
| cash_management_service.py | 6 | 49 | CG1/CG2/HL*/PERF2/MR101/HL801 |
| treasury_service.py | 6 | 1 | CG1/CG2/HL801/R1/W3 |
| cash_management_controller.py | 5 | 6 | CG1/DG/HL*/LC1/Q1 |
| admin_treasury_status.py | 4 | 5 | CG1 router→models, DG db.database, W1 commit, DBA32 OFFSET, CA1 no response_model on list |
| admin_treasury_identity.py | 4 | 3 | CG1 models in router, W1 db.add/commit, DG db.database |
| db/treasury_seeder.py | 4 | 0 | R4 (seeder — acceptable, see note) |
| public_treasury_payments.py | 3 | 6 | CG1 db.query, W1 commit, DBA32 OFFSET |

## Strategy
Two classes of treasury routers exist:
1. **Already conformant** (delegate to `controllers.cash_management_controller` /
   `services.treasury.*`): `public_treasury_operations.py`, `public_treasury_cash_position.py`.
   Leave as-is (only `db.commit()` in router is a minor residual W1 we accept to match
   the established treasury pattern).
2. **Legacy, non-conformant** (do work inline): `admin_treasury_identity`,
   `admin_treasury_status`, `public_treasury_payments`, `supplier_payouts`.
   → Move read/write logic into `controllers/treasury/*`, keep RLS context + auth in
   the router, remove `db.query`/`db.add`/`db.commit` from routers, add `response_model`,
   replace OFFSET with keyset pagination on hot lists.

## False-positive / out-of-scope notes
- `db/treasury_seeder.py` R4: seeders are allowed to write (no router, no request scope).
  Will not "fix" — leave as intentional.
- `public_treasury_api_access.py` imports from bogus module
  `data.services_treasury_treasury_query_service` (does not exist → would crash on use).
  Fix: re-export the four query funcs from the real `services.treasury.treasury_service`.
  (Regression guard: `tests/test_treasury_isolated.py`.)

## Step-by-step
1. [x] Fix `public_treasury_api_access.py` bogus import (re-exports from real `services.treasury.treasury_service`).
2. [x] `controllers/treasury/identity_controller.py` + refactor `admin_treasury_identity.py`
       (router keeps RLS + auth; delegates create/list to controller; removes `CashAccount()`/`CashTransaction()`
       instantiation + `db.add/commit`/W1).
3. [x] `controllers/treasury/supplier_payout_controller.py` + refactor `supplier_payouts.py`
       (router delegates list/request; removes `Payout()` + `db.add/commit`).
4. [x] `controllers/treasury/payout_status_controller.py` + refactor `admin_treasury_status.py`
       (router delegates create/verify/process/list; keyset cursor pagination; `db.commit`→`commit_only`;
       drops `controllers.audit_controller` import from router — clears W3).
5. [x] `controllers/treasury/payout_approval_controller.py` + refactor `admin_treasury_payments.py`
       (router keeps read/serialize helpers; delegates approve/reject/approve-batch/reject-batch/dispatch
       to controller; removes the 5 `db.commit`; drops `controllers.audit_controller` import — clears W3).
6. [ ] `admin_treasury_reporting.py` (1788 ln): thin to controller calls; split report builders
       into `services/treasury/reporting/*`; add response_models; keyset pagination. (Largest, last.)
7. [~] `main.py` treasury wiring: VERIFY against current `main.py` (a concurrent repo-wide rename
       `public_*`→`admin_*`/`system_*` is in progress; `main.py` still imports the now-renamed
       `routers.public_comms_status` → `routers.system_comms_status`, which currently breaks full
       `import main` boot — unrelated to treasury; **do not edit main.py router registration**).
8. [ ] Run `scripts/system_trackers/system_architecture_audit.py` → confirm treasury RED/YELLOW drop.

## Notes (this session)
- **Persistence discovery:** the prior session's "done" edits had NOT actually been written to disk —
  the four routers still contained `db.add`/`db.commit`/model instantiation. The rewiring above was
  performed for real this session.
- Controllers already existed (`controllers/treasury/*`); the routers simply were never pointed at them.
- Verification done WITHOUT full `import main` (blocked by unrelated `public_comms_status` rename):
  all four routers + controllers import cleanly; mounted on a TestClient every treasury route resolves
  (401 = auth enforced, no 500s); `tests/test_treasury_isolated.py` → 3 passed.
- Residual (accepted for now, lower priority): CIR2 `routers→models` reads in routers; W1 in the
  *controllers* (the audit also flags controller-level `db.commit`); DBA32 OFFSET on the payments
  `/pending` combined list (kept page-based to preserve the frontend envelope).
