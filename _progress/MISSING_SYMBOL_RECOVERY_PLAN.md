# Missing-Symbol Recovery Plan (Circuit-Compliant)

## Objective
For every `_missing_symbol` stub in the codebase (~115 across 13 service shims +
`models/upload_job.py` + `routers/_permission_primitives.py`), either:
- **(A) Find it:** a real implementation exists somewhere in the working tree → rewire the shim to re-export it, or
- **(B) Write it:** no implementation exists anywhere → implement it from scratch in the canonical location, then wire it.

All work must comply with the **Grid Line circuit** (`ARCHITECTURE_DIAGRAM.md` §10.2:
routers → controllers → services → models; only `services/**` and `jobs/*` may call
providers; writes live in services, never routers/controllers/models).

## Hard constraints
- **No git** (filesystem search only — `grep`/`glob`/`read`).
- Circuit contract enforced for every written function.
- No hardcoded secrets — env config only.
- Atomic import updates; never break an import chain.
- Do NOT modify `scripts/` or `SYSTEM_AUDIT_REPORT.md`.

## Step 1 — Definitive inventory (one-time)
Build the table of every `= _missing_symbol(` assignment: `symbol | shim_module | domain`.
(Already captured: ~115 stubs — see `ADMIN_MODULE_REMEDIATION.md` per-service section.)

## Step 2 — Search other files for a real implementation
For each symbol, `grep` `def <name>(` across `backend/` (excluding the shim module itself
and the `_missing_symbol` helper). Classify each hit:
- **REAL** — `def` in `services/<domain>/…`, non-trivial body, plausible arity → **rewire candidate**.
- **NO-OP** — body is `(*_args, **_kwargs)` (e.g. `suppliers_write_service.py`) → ignore, treat as missing.
- **WRONG-LAYER** — router/`@router` handler returning `Response` (e.g. `routers/*`) → ignore, treat as missing.
- **MISSING** — no usable hit → must be **written**.
Also grep `data/models.py` / `models/*.py` for missing **model classes** (e.g. `UploadJob`).

## Step 3 — Rewire found implementations (path A)
Use the lazy `_REEXPORTS` / `__getattr__` pattern already proven in `services/orders_write_service.py`:
- Add the symbol to the shim's `_REEXPORTS` map pointing at the canonical module.
- Delete the `symbol = _missing_symbol('symbol')` line and (if now unused) the `_missing_symbol` helper.
- Assert `getattr(shim, name) is getattr(canon, name)` in a test.

## Step 4 — Implement missing functions (path B, circuit-compliant)
**Placement:** canonical `services/<domain>/<domain>_write_service.py` (create the module if absent).
**Conventions** (mirror `services/users/user_write_ops.py` + `services/orders/orders_write_service.py`):
- Signature `def name(db: Session, *args, **kwargs) -> Model` (or `-> None` for pure deletes).
- Construct ORM object → `db.add` → `db.commit` → `db.refresh` → return it.
- **Deletes** use `utils.soft_delete.soft_delete(db, Model, record_id, acting_user, reason=…)`
  (never raw `db.delete` unless a hard-delete is intended AND audited).
- **Admin-gated ops** accept `acting_user` and write an `AuditLog` entry.
- Imports use `from data.models import …` (NOT `from models import …`).
- No provider/network calls inline; delegate to the relevant `services/` module.
- No-op `(*_args, **_kwargs)` bodies are NOT acceptable — every written fn does real work.

## Step 5 — Close model-class gaps
`models/upload_job.py: UploadJob = _missing_symbol('UploadJob')` — the class is genuinely absent.
- Search `data/models.py` + migrations for any `upload_job` table; if found, point the shim at it.
- If not found: create the `UploadJob` model class + an Alembic migration. **Flag this for DBA sign-off**
  before execution (schema change, not just code).

## Step 6 — Wire the shims
Each shim re-exports every symbol (found or written) via `_REEXPORTS`/`__getattr__` from the
canonical module; remove all `_missing_symbol` definitions/stubs.

## Step 7 — Verification gates (per phase, then full)
1. `getattr(shim, name)` is a real callable for **all** symbols (no `_missing_symbol` sentinel).
2. Import smoke test: `import` every shim + every `controllers/*` / `routers/*` that imports it.
3. `grep -rn "= _missing_symbol(" backend/` returns **zero** hits.
4. Add a regression test per symbol: create → assert persisted → soft-delete round-trip where applicable.
5. `pytest` green on the touched services.

## Phasing (keep PRs reviewable; per-phase gates above)
- **P0 Foundation** — missing model classes (`UploadJob` + any other missing models + migrations).
- **P1 Financial (highest risk)** — payments, commissions, settlements, invoices, ledger entries.
- **P2 Logistics** — partner writes, shipments, pricing profiles/rules, vehicle rules, service areas.
- **P3 HR / IAM / Employee** — biometrics, geo-fence, QR sessions, attendance, documents, revoked tokens.
- **P4 Permissions / Analytics / Banners / Disputes / Misc** — including `routers/_permission_primitives.py` maps.
- **P5 Sweep** — full grep + import smoke + full `pytest`; confirm 0 stubs remain.

## Acceptance criteria
- **0** `_missing_symbol` stubs remain in the tree.
- Every former stub symbol is a callable, circuit-compliant function (no `(*_args,**_kwargs)` filler).
- All new regression tests green; no import regressions across `controllers/`/`routers/`.
