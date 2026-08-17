# Plan: Re-arrange & Architecture-Align `EMPLOYEE_COMMUNICATION_SYSTEM.md`

## Context
`documents/EMPLOYEE_COMMUNICATION_SYSTEM.md` (~1141 lines) is the EMS + Communication Suite master spec. It was previously re-arranged into 10 logical Parts and its phase numbering (Part 4 / 5.1 / 5.2) was aligned to a single **Phases 0–14** sequence. This task re-reads it in full and (a) re-confirms logical order while **keeping every feature and detail**, and (b) **aligns the architecture descriptions and all file-path references to the real system folders**, using `scripts/system_trackers/feature_definitions.yaml` **P1** (architecture constitution) as the reference, cross-checked against the actual repo tree.

### Verified repo facts (ground truth for alignment)
- `backend/services/{domain}/` and `backend/controllers/{domain}/` and `backend/models/{domain}/` **already use domain subfolders** — e.g. `backend/services/comms/`, `backend/services/hr/`, `backend/controllers/comms/`, `backend/models/comms/`, `backend/models/hr/`.
- `backend/routers/` stays **flat** (`{surface}_{domain}_{feature}_router.py`) — matches P1. Legacy fat routers (`video_controller.py`, `email_controller.py`, `internal_channels.py`, `audit.py`) live here.
- Legacy monolithic model files still exist flat: `backend/models/core.py`, `backend/models/communication.py`, `backend/models/employee_models.py`.
- Frontend target (from SYS_001): `frontend/web_app/src/app/comms/...`, `frontend/web_app/src/components/comms/...`, `frontend/web_app/src/hooks/...`; mobile `frontend/mobile_app/app/comms/...`.
- **Contradiction resolved by user:** P1 lists schemas as `customer/supplier/logistic/admin/employee`, but the real repo + SYS_001 use **`hr` + `comms`** schemas. Decision: **keep `hr` + `comms`**; add a note in the doc that this intentionally deviates from P1's simplified schema list.

### The core defect to fix
The doc references **stale flat paths** that no longer match the tree:
- `backend/services/chat_system.py` → actual `backend/services/comms/chat_system.py`
- `backend/services/video_conferencing.py`, `email_gateway.py`, `internal_communication.py`, `external_contact.py`, `communication_audit.py`, `ediscovery.py`, `proxy_communication.py` → all under `backend/services/comms/`
- `backend/controllers/chat_controller.py` / `video_controller.py` / `email_controller.py` → legacy flat `backend/routers/{name}.py` AND new `backend/controllers/comms/{...}_controller.py`
- `core.py` / `communication.py` / `employee_models.py` → qualify as `backend/models/core.py` etc. (legacy monoliths) and map each model to its current module via grep
- `frontend/web_app/src/app/admin/communication/page.tsx` → `frontend/web_app/src/app/comms/...` (SYS_001)

## Target Document Structure (logical order — keep all 10 Parts, add alignment)
- **Title + Grounding note + TOC** — TOC updated to new section list; add a line: "Architecture aligned to P1 (`feature_definitions.yaml`) and the live repo tree; schemas retained as `hr`/`comms`."
- **Part 1 — Core Design Philosophy** (keep verbatim).
- **Part 2 — System Architecture (aligned to repo)** — restructure:
  - 2.1 Backend circuit (P1): Client → Middleware → Routers (thin) → Controllers (orchestrate) → Services (own DB) → Models/Providers/Redis → PostgreSQL (PgBouncer) → External APIs. Cite real layers.
  - 2.2 Frontend circuit: web_app `src/app/comms/*`, `src/components/comms/*`, `src/hooks/*`; mobile_app `app/comms/*`; shared.
  - 2.3 Integration Matrix (current 2.1 content — EMS ↔ core/finance/comms/etc.).
  - 2.4 Technical Architecture Principles (current 2.2 content).
  - **2.5 Repository File Map (NEW)** — table mapping each EMS/Comms subsystem → actual repo paths (services/{domain}, controllers/{domain}, models/{domain}, routers/, frontend). Grounded in verified files.
  - 2.6 Mandatory Architecture Contract (from P1): thin routers, controllers import **no FastAPI** + delegate DB to services, services own DB, media→object storage (no DB blobs), RLS on every table, Celery/Redis for heavy work. Add a "Current violations" note flagging legacy fat routers / controllers that still import FastAPI or do DB writes (the W1 debt P1 calls out).
- **Part 3 — Diagrams** (keep 3.1 master arch, 3.2 payroll circuit, 3.3 lifecycle). Update 3.1 to show the layered circuit + domain folders; keep Mermaid.
- **Part 4 — EMS Feature Roadmap (Phases 0–14)** (keep; already aligned). Optional: one-line "domain/files" pointer per phase to the File Map.
- **Part 5 — Step-by-Step Construction & Timeline** (keep; 5.1 already 0–14). Fix inline file refs (`auth_service.py` → `backend/services/identity/...` or `core/...` as verified; `chat_attachments` → `backend/models/comms/...`).
- **Part 6 — Automation System** (keep table; IDs 1–14 independent of phases — note already present).
- **Part 7 — UI/UX Layout** (keep; align any frontend path refs to `src/app/comms/...`, `src/components/comms/...`).
- **Part 8 — Communication Suite: Current Implementation Status** (keep audit). **Fix all Location/File columns**:
  - 8.1 models: resolve each model's current module via grep (`grep -rl "class X" backend/models`); update Location to actual module (e.g. `backend/models/comms/...`); preserve ✅/⚠️/❌ + line refs where still valid. Note legacy monolith vs new domain module.
  - 8.2 services: change `backend/services/<x>.py` → `backend/services/comms/<x>.py` (or `backend/services/hr/<x>.py` for HR services) for every row.
  - 8.3 endpoints: change `backend/controllers/<x>_controller.py` → actual resolved path (legacy `backend/routers/...` and/or new `backend/controllers/comms/...`); keep method/path tables.
  - 8.4–8.8 keep verbatim.
- **Part 9 — Unified Communication UI ("Confluence")** (keep all detail). Align §9.9.1 + §9.9.8 file tree to SYS_001 canonical paths (`frontend/web_app/src/app/comms/...`, `src/components/comms/...`). Keep the three ASCII deck grids (§9.2 / §9.4 / §9.9.2) as documented render variants but ensure each references the aligned paths.
- **Part 10 — Definition of Done & Acceptance Criteria** (keep verbatim).

## Path-Correction Rules (apply everywhere)
1. Every `backend/services/<file>.py` → `backend/services/{domain}/<file>.py` where domain ∈ {comms, hr, identity, finance, documents, governance, geography, core}. (Verified: comms + hr subfolders exist with these exact files.)
2. Every `backend/controllers/<file>_controller.py` → resolve to legacy `backend/routers/<file>_controller.py` and/or new `backend/controllers/comms/<file>_controller.py`; show both if both exist.
3. Every `core.py` / `communication.py` / `employee_models.py` → prefix `backend/models/`; map each class to its real module via grep; keep line numbers only if still accurate.
4. Every `frontend/web_app/src/app/admin/communication/...` → `frontend/web_app/src/app/comms/...`; `src/components/comms/...` already correct (keep).
5. Routers flat in `backend/routers/` stay flat (P1-compliant) — `internal_channels.py`, `audit.py` etc. unchanged.
6. Schemas: keep `hr` + `comms`; add a one-line note that P1's `employee/admin` list is a subset/simplification.

## Execution Steps (for the implementing agent)
1. Read full current file (1141 lines) and `feature_definitions.yaml` P1 + SYS_001.
2. Run targeted greps to resolve each stale model/service/controller path to its real module (capture a mapping table first).
3. Rewrite the doc in the target 10-Part structure, applying the 6 path-correction rules; insert new §2.5 File Map and §2.6 Contract; update §3.1 diagram; align Part 9 frontend paths.
4. Preserve ALL prose, tables, Mermaid, ASCII art, CSS/JSX snippets, endpoints, acceptance criteria — only paths/labels change.

## Validation
- `grep -nE "backend/services/(chat_system|video_conferencing|email_gateway|internal_communication|external_contact|communication_audit|ediscovery|proxy_communication)\.py"` → **0 matches** (all must be under a domain folder).
- `grep -nE "backend/controllers/chat_controller|backend/controllers/video_controller|backend/controllers/email_controller"` → 0 flat-controller matches (must be routers/ or controllers/{domain}/).
- `grep -n "app/admin/communication"` → 0 (replaced by `app/comms`).
- Line-count parity: new total within ~±5% of 1141; every Part 1–10 heading present (verify with `grep -nE "^## Part"` → 10 hits).
- TOC anchors match headings.
- Spot-check that a sample of unique features (e.g., "WORM", "proxy_*", "Maker-Checker", "5 login doors", "whisper transcript", "attrition-risk") still appear.

## Risks / Open Questions
- Some Part 8 model "Location" line numbers (`core.py:245`) may be stale if models moved into `backend/models/comms/`; implementer must grep-verify rather than assume.
- P1's "no FastAPI in controllers" contract is currently **violated** by legacy code; the doc should *describe the target* and flag the gap, not claim compliance.
- The three Confluence ASCII grids are near-duplicates; kept per "keep all details" but flagged as render variants to avoid implying three different designs.
