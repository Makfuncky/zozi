# Media Module — Audit Remediation Note

**Date:** 2026-08-06
**Module:** `media` (chosen from the audit's "All Findings by Domain")
**Approach:** "Safe + clear REDs" (user-selected)
**Source of truth:** `SYSTEM_AUDIT_REPORT.md` §9 (read-only; audit scripts in `scripts/` not modified)

---

## 1. RED findings cleared (DBA06 — cross-schema FK)

Six `DBA06` VIOLATION findings were reported against the media models:

- `models/media/media_models.py:21`  media_assets.product_id  -> commerce.products.id
- `models/media/media_models.py:22`  media_assets.supplier_id -> core.users.id
- `models/media/media_models.py:39`  media_assets.uploaded_by -> core.users.id
- `models/media/media_models.py:65`  media_upload_sessions.created_by -> core.users.id
- `models/media/upload_job.py:24`    upload_jobs.supplier_id -> core.users.id
- `models/media/upload_job.py:31`    upload_jobs.product_id -> commerce.products.id

**Fix:** Removed the `ForeignKey("commerce.products.id" / "core.users.id")` constraints from the
integer ID columns. The columns (`product_id`, `supplier_id`, `uploaded_by`, `created_by`) are
retained, indexed, and the ORM `relationship(...)` definitions kept working via explicit
`foreign_keys=[...]`. Referential integrity is now enforced application-side, not as a DB
constraint, satisfying the bounded-context "no cross-schema FK" rule.

**Verification:** importing `main.py` triggers an internal cross-schema FK analysis that now
reports `Total cross-schema FKs: 0` (`out/cross_schema_fk_analysis.json`, `total_count: 0`, all
categories empty). The 6 media REDs are gone.

---

## 2. Safe code-quality fix applied (HL602 — missing timeout)

`services/media/storage.py` constructs the boto3 client with `botocore.config.Config(
connect_timeout=10, read_timeout=30, retries=...)`. The timeout was already present, but the
values were hardcoded. Per the "config from environment, never hardcoded" rule, the S3 client
now reads them from env with safe defaults:

- `S3_CONNECT_TIMEOUT_SECONDS` (default 10)
- `S3_READ_TIMEOUT_SECONDS` (default 30)
- `S3_MAX_ATTEMPTS` (default 3)

---

## 3. Concurrent cleanup that landed on top of this work (reconciled, kept)

While this pass was in progress, the broader "Production-Ready" automation edited the same two
model files and:

- Added `AuditMixin, SoftDeleteMixin` to `MediaAsset`, `MediaUploadSession`, `UploadJob`
  (addresses **DBA03** — missing audit/soft-delete mixins).
- Renamed `ai_result` -> `ai_result_json` and the GIN index
  `ix_upload_jobs_ai_result_gin` -> `ix_upload_jobs_ai_result_json_gin`
  (addresses **DBA11** — JSON column naming).

That process initially introduced a **broken import**
(`from db.mixins import AuditMixin, SoftDeleteMixin, TenantMixin` — but `db/mixins.py` only
exports `AuditMixin, SoftDeleteMixin, TimestampMixin`; `TenantMixin` lives in `models/mixins.py`).
The import was corrected (split `TenantMixin` into `from ..mixins import TenantMixin`) before
this pass acted on it, so the app imports cleanly. My DBA06 removals survived intact.

Per user direction ("Fix import, keep cleanup"), this mixin/naming work is kept.

> **FLAGGED — migration gap (required, not yet present):** No Alembic migration adds the new
> mixin columns (`uuid, country_code, is_active, version, created_at, updated_at, created_by,
> updated_by, is_deleted, deleted_at, deleted_by, delete_reason`) to `media_assets` /
> `media_upload_sessions` / `upload_jobs`, renames `ai_result` -> `ai_result_json`, or drops the
> legacy FK constraints. The still-current migration `2026_07_30_0003` builds `upload_jobs` with
> `ai_result` (no mixin cols, with `fk_upload_jobs_supplier_id` / `fk_upload_jobs_product_id`).
> Until the cleanup process lands a migration, the app will fail against an **Alembic-built** DB
> (model expects `ai_result_json` + mixin cols). In DEV SQLite with `create_all` the model-driven
> schema is built correctly. This migration is the cleanup process's deliverable.

---

## 4. Findings verified as FALSE POSITIVES (reported in detail, NOT changed)

The audit report is **stale** relative to the current code: its line numbers and `except`
detections do not match the current sources. Every flagged `except` block already logs with
context. Changes were deliberately NOT made to avoid regressions.

### HL302 (swallowed exceptions)
- `services/media/free_image_tools.py:41` — `except ImportError: logger.exception(...); pass`
  (graceful optional-dep import; logs).
- `services/media/image_ai_service.py:45,269,385` — all `except` blocks use
  `logger.warning/exception/debug` with `exc_info=True`.
- `services/media/media_router_service.py:430,480` — these line numbers are inside the
  `batch_publish_products` docstring / a f-string; the real `except` blocks (lines 389, 405,
  436, 484, 593, 602) all use `logger.exception` / `logger.warning` / re-`raise`.
- `services/media/storage.py:109` — `except FileNotFoundError: pass` inside `delete()`, which is
  a documented no-op ("no-op if missing"); intentional, not a swallow.
- `routers/api_media_bulk.py:114,129,164` and `routers/api_media_bulk_2.py:68` — all `except`
  blocks use `logger.error/exception` or convert to `HTTPException` with context.

### HL303 (broad `except Exception`)
- `providers/media/image.py:182,197`, `services/media/media_service.py:123,179`,
  `services/media/upload_job_service.py:106,233` — each uses
  `except Exception as exc: logger.warning/exception(...)` (broad, but logs with context).
  Narrowing would risk dropping legitimate errors; current behaviour is acceptable.

### PERF4 (unbounded query)
- `services/media/media_router_service.py:121` — the `AIGenerationLog` query is
  `.order_by(...).limit(SAFE_QUERY_LIMIT).all()`. It is bounded; false positive.

---

## 5. Systemic / by-design findings (documented, NOT restructured under "Safe" scope)

- **CIR2** (routers -> services, e.g. `api_media_ingestion` -> `services.storage`,
  `api_media_bulk_2` -> `services.upload_job_service`): the platform's `data.*` circuit layer is
  an explicit, exempt indirection; media has no controllers, so routers call services directly
  by design.
- **CA2 / MV1 / DOM7**: `providers/image.py`, `providers/bg_remover.py` (root-level forwarders)
  and the empty `services/uploads/` folder are part of the deliberate shim/forwarder design.
  `bg_remover`'s canonical file lives in `providers/hr/bg_remover.py`; per the contract's domain
  keyword table `bg_removal`/`removal` map to `ai`, so this is a contract/placement inconsistency
  rather than a quick fix.
- **DG2** (`models/__init__.py` cycle via `models._exports`): a pre-existing import-cycle design
  used across the whole model layer; not introduced by media changes.
- **SYM2** (`create_ai_upload_job`, `cancel_ai_upload_job`, `batch_publish_products` defined in
  both router and service): intentional facade duplicates (thin router wrapper + service impl);
  consolidating would break router/service call sites.

---

## 6. Validation performed

- `models/media/media_models.py` + `models/media/upload_job.py` import and the SQLAlchemy mapper
  configures (mixins + relationships resolve).
- All media routers (`api_media_ingestion`, `api_catalog_media`, `api_media_bulk`,
  `api_media_bulk_2`), services (`media_router_service`, `media_service`, `upload_job_service`,
  `storage`, `free_image_tools`, `image_ai_service`), and `providers/media/image.py` import.
- `import main` builds the FastAPI app; the app's own cross-schema FK analysis => `total_count: 0`.
- `py_compile` on the edited model files passes.

**Note:** Full `app + tests` run is gated on the migration gap in §3 (the cleanup process's
deliverable). In DEV SQLite (`create_all`) the model-driven schema is internally consistent.
