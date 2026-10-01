# Master Prompt — Populate `_most_imp_docx/PROMPT_STACK.yaml` with Complete Feature Contracts

Below is the **complete, copy-paste-ready prompt** to hand to the AI (or to the orchestration agent). It is self-contained, references every required input, and enforces the P2 template exactly.

---

````markdown
# ZOZI — MASTER EXTRACTION & COMPLETION PROMPT
## Target: `_most_imp_docx/PROMPT_STACK.yaml`
## Working directory: `./_prompt_completion/**`

---

## 0. MISSION

Populate `_most_imp_docx/PROMPT_STACK.yaml` with **one complete feature contract per feature** listed in `_most_imp_docx/FEATURE_STACK_LIST.md`, using the **P2 template** already defined inside `PROMPT_STACK.yaml` (section `P2 - FEATURE INSTRUCTION TEMPLATE`).

Every feature must be extracted from the actual codebase, cross-checked against documents, aligned to the P1 architecture rules, and written so that a future AI agent can **build, test, audit, and complete** the feature without guessing.

This file becomes the **single source of truth** for the entire project. Every feature in it must be actionable.

---

## 1. INPUT SOURCES (read all before writing anything)

### 1.1 Codebase (ground truth — highest authority)
Read the **entire** `backend/` and `frontend/` trees, respecting the NEW_STRUCTURE layout:

- `backend/modules/{customer,supplier,logistics,admin,employee}/{auth,routers,serializers}/`
- `backend/domains/{accounts,analytics,audit,catalog,comms,country,customers,finance,governance,hr,logistics,media,orders,payments,promotions,security,suppliers}/`
- `backend/rbac/{catalog,roles,resolution,dependencies,service}.py`
- `backend/kernel/{money,numbering,country,period,currency,constants,mixins}.py`
- `backend/infrastructure/{database,valkey,storage,messaging,observability,security,events,utils,currency,http,ml,uploads}/`
- `backend/providers/{ai,analytics,auth,automation,barcode,bg_removal,comms,finance,geography,image,news,ocr,payments,qr,scanner,security,shipping,storage,voice}/`
- `backend/jobs/`
- `backend/middleware/`
- `frontend/web_app/src/{app,components,lib,hooks,services,theme,types,utils}/`
- `frontend/mobile_app/{app,components,lib,theme}/`
- `frontend/shared/src/`

**Rule:** If code and docs disagree, **code wins**, but flag the drift in `discussion_notes`.

### 1.2 Feature extraction workspace (pre-computed evidence)
Read **every file** under `_feature_extraction/**`:

- Any JSON/YAML/MD already extracted per feature
- Any API route dumps
- Any DB table listings
- Any test inventory
- Any UI page inventory

Treat these as **pre-verified hints** but always re-confirm against the live codebase.

### 1.3 Canonical documents (must read fully)
Read every file under `_most_imp_docx/`:

- `_most_imp_docx/FEATURE_STACK_LIST.md` — the master feature index (this is the source list to be converted)
- `_most_imp_docx/PROMPT_STACK.yaml` — target file; contains P1 rules, P2 template, P3 tracker spec
- `_most_imp_docx/TECHNOLOGY_STACK.md` — approved tech choices
- `_most_imp_docx/FEATURES.md` — deep feature spec (contains ❗ flags for approved/correct vs needs-alignment)
- `_most_imp_docx/ARCHITECTURE_STACK.md` — the 12 Laws, layer boundaries, dependency rules
- Any additional `*.md` in `_most_imp_docx/` that describes a subsystem (finance, treasury, comms, country, search, etc.)

### 1.4 Prior generated context (if present)
- `documents/CODEBASE_STATUS_MATRIX.md` (or `_AUTO.md`)
- `documents/RECOVERY_CLEANUP_AUDIT_*.md`
- `documents/NEW_STRUCTURE.md`
- Any `WORKFLOW_LIST.md`, `WORKFLOW_STATUS_SUMMARY.md`, `IMPLEMENTATION_STATUS_MATRIX.md`

---

## 2. NON-NEGOTIABLE RULES (P1 Architecture)

Every contract must obey these laws. Violations must be flagged in `discussion_notes` as `LAW_BREACH:` with the specific law cited.

1. **Three axes:** Module (WHO) = `backend/modules/`, Domain (WHAT) = `backend/domains/`, Feature (MAY) = `backend/rbac/` + `domains/*/features.py`. Country is the orthogonal 4th axis (RLS scope).
2. **Dependency direction:** `modules → domains → infrastructure`. Never the reverse. Cross-domain writes only via **events**; cross-domain reads only via **ports.py** or **read_models**.
3. **Thin routers:** module routers contain no DB writes, no business logic. They do: auth context + `require_feature(...)` + ONE service call + return `response_model`.
4. **Services own the DB:** only `domains/{domain}/services/` (or slice services) write to the domain's tables.
5. **Models:** SQLAlchemy ORM only; `__table_args__ = {"schema": "<domain>"}`; cross-domain FKs as **string targets only**; `relationship()` intra-domain only.
6. **RBAC:** every `require_feature("...")` literal must exist in the rbac catalog. Feature atoms live in `domains/*/features.py`.
7. **RLS:** every country-scoped table carries `country_code` and enforces RLS via the single canonical enforcer (`infrastructure/database/security.py`).
8. **Money:** Python `Decimal` + Postgres `NUMERIC(16,4)`. **Never float.**
9. **Immutable ledgers:** no `UPDATE` / `DELETE` on posted journal entries. Reversals only via counter-entries.
10. **Media bytes in R2/S3**, metadata in `media.assets`. **Never store blobs in Postgres.**
11. **Events via transactional outbox.** Cross-domain side effects go through `outbox_events`.
12. **AI outputs are staged** (`ai_staging_*`) and committed explicitly. AI never writes directly to business tables.
13. **Alembic is the single schema source of truth.** `create_all` is dev-only.
14. **Cursor pagination** on hot lists. **Never `OFFSET`.**
15. **No silent fallbacks.** Every degraded path returns an explicit status (`mode: "lexical"`, `degraded: true`, etc.).
16. **Analytics never live-aggregate transactional tables.** Use materialized views / snapshots.

---

## 3. THE P2 TEMPLATE (extract exactly, then fill)

Every feature contract must contain **all** of the following fields. If a field is genuinely not applicable, write `N/A` with a one-line reason — never omit the field.

```yaml
- id: SYS_XXX                            # next sequential; matches FEATURE_STACK_LIST ordering
  name: <Feature Title>                   # exact title from FEATURE_STACK_LIST.md
  update_version: "<NNN>_<DD-MM-YYYY>"   # e.g., "001_28-09-2026"
  description: |
    <the FULL binding build spec — see §4 below for required sub-sections>

  state_checkpoint: PENDING              # PENDING | AI-DONE | TESTED | HUMAN-APPROVED
  scope:                                 # one or more modules
    - Customer
    - Supplier
    - Logistics
    - Admin
    - Employee
    - Internal

  sections:
    §I_Platform_Infra: <one sentence>
    §II_Customer:      <one sentence>
    §III_Supplier:     <one sentence>
    §IV_Logistics:     <one sentence>
    §V_Admin:          <one sentence>
    §VI_Employee:      <one sentence>

  file_reference: |
    - documents/FEATURES.md#<anchor>
    - documents/<other>.md
    - _feature_extraction/<file>
    - media_assets:<asset_id>            # storage-ref, never blob

  workflow: |                            # COMPULSORY — end-to-end data flow
    backend/middleware/<mw>.py
      → backend/modules/{module}/routers/{domain}.py   (thin; require_feature)
      → backend/domains/{domain}/services/{feature}_service.py
      → backend/domains/{domain}/models/{aggregate}.py
      → backend/infrastructure/{db|valkey|storage|messaging}/...
    Events published: <event.name>
    Events consumed:  <event.name>
    Ports read from:  domains/<other>/ports.py::<fn>

  diagram: |                             # mermaid — required if feature has >2 states or >3 actors
    ```mermaid
    <flowchart or stateDiagram>
    ```

  expected:
    backend_files:
      - path: backend/modules/{module}/routers/{domain}.py
        purpose: <what this file must contain for THIS feature>
      - path: backend/modules/{module}/auth/{feature}_auth.py
        purpose: <...>
      - path: backend/domains/{domain}/services/{feature}_service.py
        purpose: <...>
      - path: backend/domains/{domain}/policies/{feature}_policy.py
        purpose: <...>
      - path: backend/domains/{domain}/ports.py
        purpose: <port functions added>
      - path: backend/domains/{domain}/read_models/{name}.py
        purpose: <dashboard projection, if any>
      - path: backend/domains/{domain}/events.py
        purpose: <events published>
      - path: backend/domains/{domain}/subscribers.py
        purpose: <events consumed>
      - path: backend/domains/{domain}/features.py
        purpose: <feature atoms added>
      - path: backend/rbac/{catalog|roles|resolution|dependencies|service}.py
        purpose: <rbac touch-points>
      - path: backend/kernel/{money|numbering|country|period|currency|constants|mixins}.py
        purpose: <kernel usage>
      - path: backend/infrastructure/{database|valkey|storage|messaging|observability|security}/...
        purpose: <infra touch-point>
      - path: backend/middleware/{function}_middleware.py
        purpose: <middleware involvement>
      - path: backend/jobs/{function}.py
        purpose: <worker/consumer>
      - path: backend/providers/{domain}/{name}.py
        purpose: <provider adapter>
      - path: backend/_legacy/{layer}/...
        purpose: <shim being removed, if any>

    database_files:
      - backend/infrastructure/database/migrations/<version>_<slug>.py
      - backend/infrastructure/database/mixins.py
      - backend/infrastructure/database/security.py
      - backend/infrastructure/database/seeds/<file>.py

    model_files:
      - backend/domains/{domain}/models/{aggregate}.py
        classes: [<ClassName>]
        schema: <domain>
        key_fields: [<field>: <type>, ...]
        indexes: [...]
        constraints: [...]

    frontend_web:
      - path: frontend/web_app/src/app/{module}/{domain}_{feature}/page.tsx
        purpose: <...>
      - path: frontend/web_app/src/components/{area}/{Component}.tsx
        purpose: <...>
      - path: frontend/web_app/src/lib/{helper}.ts
        purpose: <...>

    frontend_mobile:
      - path: frontend/mobile_app/app/{module}/{domain}_{feature}.tsx
        purpose: <...>

    frontend_shared:
      - path: frontend/shared/src/{file}.ts
        purpose: <...>

    tests:
      - backend/tests/architecture/test_import_laws.py
      - backend/tests/architecture/test_feature_catalog.py
      - backend/tests/architecture/test_schema_discipline.py
      - backend/tests/architecture/test_model_relocation.py
      - backend/tests/domains/{domain}/_test_{feature}.py
      - frontend/web_app/src/__tests__/_test_{module}_{domain}_{feature}.test.tsx
      - frontend/mobile_app/e2e/_test_{module}_{domain}_{feature}.test.tsx
      - backend/tests/playwright/<spec>.py

    extra_files:
      - _extra_files/<path>              # optional, untracked

    api_routes:
      - "GET  /{module}/{domain}/{path}"
      - "POST /{module}/{domain}/{path}"
      # actor-prefixed; must resolve to a module router

    models:
      - "<ModelClassName>"
```

---

## 4. `description:` REQUIRED SUB-SECTIONS

The `description` field is the **heart** of the contract. It must contain the following sub-sections **in this order**, exactly as headings:

```markdown
## Capabilities:
- <bullet per capability>
- Reference `media_assets:<id>` for images/videos (storage-ref, not blobs)

## Actors:
- Primary: <actor>
- Secondary: <actor>
- Denied: <actor> (with reason)

## Non-negotiables:
- **Bolded phrases become capability checkpoints.**
- **Every rule here is enforceable at CI or runtime.**

## User actions:
- <what the user physically does, step by step>

## System actions:
- <what the platform does in response, step by step>

## Step-by-step:
- **Step 1 — <milestone>** → this becomes a milestone checkpoint
- **Step 2 — <milestone>**
- ...

## State machine:
- initial: <state>
- states: [<...>]
- transitions:
  - { from: <A>, to: <B>, trigger: <event>, guard: <rule> }
- terminal: [<...>]

## Business rules:
- **BR-<DOMAIN>-NNN**: <plain-language rule> — enforcement: <backend|frontend|database|worker|policy>
- ...

## Calculations:
- <name>: formula `<...>` — precision: 2dp — currency_rule: <...> — audit: true

## Data:
- schema.table: [<table1>, <table2>]
- important_fields: <...>
- indexes: <...>
- constraints: <...>

## Events:
- produces: [<event.name>]
- consumes: [<event.name>]
- outbox_required: true

## Integrations:
- payment_gateway: <bool>
- logistics_provider: <bool>
- email / sms / ai / storage_r2: <bool>

## Audit:
- required: true
- log_table: governance.audit_events
- tracked_fields: [actor_id, country_code, entity_id, before, after, ip, user_agent]
- retention: 7_years
- immutability: append_only

## Notifications:
- channel: <email|push|in_app|sms>
- recipient: <actor>
- trigger: <event>
- template: <name>

## Edge cases:
- <bullet per edge case and how it's handled>

## Non-functional:
- performance: p95 < Xms
- security: pii_masking, no_card_data_storage, webhook_signature_verification
- compliance: pci_dss, data_residency, tax_reporting
- accessibility: wcag_level AA, keyboard_navigable, screen_reader_tested
- i18n: [en, ar], rtl_support, currency_formatting

## Acceptance criteria:
- **AC-<FEATURE_ID>-NNN**: Given <...>, When <...>, Then <...>
- ...

## Definition of done:
- Backend endpoint exists and is tested
- RBAC feature gate exists
- RLS policy enforced
- Frontend surface exists
- Audit log written
- Event emitted via outbox
- Tests green
- Status updated with evidence

## Rollback plan:
- feature_flag: <flag>
- db_migration_reversible: <bool>
- data_backfill_required: <bool>

## Observability:
- metrics: [<...>]
- logs: structured_json_required: true
- traces: distributed_tracing: true
- alerts: [<threshold → action>]

## AI instructions:
- must: [<...>]
- must_not: [<...>]
- references: [ARCHITECTURE_STACK.md, SECURITY_POSTURE.md, ...]

## Discussion notes:
- **Point 1 — <issue>**: <awareness + solution>
- **LAW_BREACH: Law N** — <where the current code violates a P1 law and how to fix>
- **DRIFT: code vs docs** — <discrepancy found; code wins>
- **MISSING** — <what is not yet built>
- **BROKEN** — <what is failing and why>
```

---

## 5. EXECUTION STRATEGY (multi-agent)

### 5.1 Setup
1. Create `_prompt_completion/` with subfolders:
   - `_prompt_completion/raw/` — raw evidence dumps per feature
   - `_prompt_completion/drafts/` — partial contracts per actor
   - `_prompt_completion/merged/` — merged contracts ready for the target YAML
   - `_prompt_completion/audit/` — law-breach and drift reports
   - `_prompt_completion/index/` — feature → contract status tracker

### 5.2 Sub-agent assignment (run in parallel)

| Agent | Scope | Input | Output |
|---|---|---|---|
| **A1 — Infra** | §1 Infra & Cross-Cutting (38 features) | codebase + docs | `drafts/infra.yaml` |
| **A2 — Customer** | §2 Customer (42+ features) | codebase + docs | `drafts/customer.yaml` |
| **A3 — Supplier** | §3 Supplier (34 features) | codebase + docs | `drafts/supplier.yaml` |
| **A4 — Logistics** | §4 Logistics Partner (30 features) | codebase + docs | `drafts/logistics.yaml` |
| **A5 — Employee** | §5 Employee (50+ features) | codebase + docs | `drafts/employee.yaml` |
| **A6 — Admin** | §6 Admin (87+ features) | codebase + docs | `drafts/admin.yaml` |
| **A7 — System** | §7 System & Automation (61+ features) | codebase + docs | `drafts/system.yaml` |
| **A8 — Cross-check** | Reads all drafts; enforces P1 laws; writes drift/law-breach report | all drafts + codebase | `audit/crosscheck.md` |
| **A9 — Merge** | Merges all drafts into final PROMPT_STACK.yaml schema; deduplicates overlapping features; assigns final IDs | all drafts | `merged/PROMPT_STACK.yaml` |
| **A10 — Validator** | Runs schema validation against the P2 template; checks every `require_feature`, every route, every model | merged file + codebase | `audit/validation.md` |

Each sub-agent must:
- Read **only** the files relevant to its scope (avoid context overflow).
- Use the P2 template exactly.
- Write to its own draft file.
- Never edit another agent's draft.
- Report back in the format: `{features_processed, features_gap, laws_violated, drifts_found}`.

### 5.3 Coordination rules
- **A8 runs after A1–A7 complete.**
- **A9 runs after A8.**
- **A10 runs after A9.**
- If A10 finds schema errors, route back to the responsible drafting agent (A1–A7) for correction.

---

## 6. FEATURE-LEVEL EXTRACTION PROTOCOL

For **each** feature in `FEATURE_STACK_LIST.md`, execute this protocol:

1. **Locate evidence:**
   - Backend: find the module router, domain service, domain model, feature atoms, events, providers, jobs, middleware.
   - Frontend: find the web page(s), mobile screen(s), shared helpers.
   - DB: find the migration(s) and table(s).
   - Tests: find the test files (unit, integration, e2e, security).

2. **Verify against P1 laws:**
   - Check router is thin.
   - Check service owns DB writes.
   - Check model schema matches domain.
   - Check `require_feature` literal exists in catalog.
   - Check RLS is enforced if country-scoped.
   - Check money uses Decimal.
   - Check events via outbox.
   - Check no blobs in Postgres.

3. **Cross-check against documents:**
   - Read the matching section in `FEATURES.md`.
   - Read the matching row in `FEATURE_STACK_LIST.md`.
   - Read any `_feature_extraction/` hint file.
   - If code and docs disagree → **code wins**, flag drift.

4. **Fill the P2 template:**
   - Every field mandatory.
   - `description` sub-sections in the exact order from §4.
   - Include at least **3 acceptance criteria** per feature.
   - Include at least **2 edge cases** per feature.

5. **Assign status:**
   - `LIVE` if endpoint + gate + frontend + tests green.
   - `BE_ONLY` if backend only.
   - `FE_ONLY` if frontend only.
   - `PARTIAL` if some sub-features live, some missing.
   - `MISSING` if not built.
   - `BROKEN` if exists but tests fail.
   - `BLOCKED` if dependency or decision pending.
   - Every `LIVE` requires a populated `evidence:` block with real paths.

6. **Write `discussion_notes`:**
   - Any law breach.
   - Any drift between code and docs.
   - Any missing/broken piece.
   - Any recommended addition (feature we should add but isn't in FEATURE_STACK_LIST).

7. **Emit the contract** into the actor draft file.

---

## 7. QUALITY GATES (must pass before merge)

| Gate | Check | Fail action |
|---|---|---|
| **G1** | Every feature ID is unique and matches `SYS_NNN` | Reject; ask drafting agent to fix |
| **G2** | Every `description` has all §4 sub-sections in order | Reject |
| **G3** | Every `api_routes` entry resolves to a real module router | Reject; flag as MISSING |
| **G4** | Every `models` class exists in `Base.metadata` | Reject; flag as MISSING |
| **G5** | Every `expected.backend_files` path exists or is marked as `TO_CREATE` | Flag |
| **G6** | Every `require_feature` literal in code appears as a feature atom in some contract | Reject |
| **G7** | Every `LIVE` feature has ≥1 test file per layer | Reject |
| **G8** | No feature violates P1 laws (or a `LAW_BREACH:` note is present with a fix plan) | Reject |
| **G9** | Every MISSING/BROKEN feature has a `discussion_notes` entry with a gap analysis | Reject |
| **G10** | Every feature has ≥3 acceptance criteria and ≥2 edge cases | Reject |
| **G11** | Every `mermaid` block (if present) is syntactically valid | Reject |
| **G12** | YAML parses cleanly | Reject |

---

## 8. FEATURES TO ADD (beyond FEATURE_STACK_LIST.md)

While extracting, watch for features that **should exist** but are not listed. Add them with `status: MISSING` and a `discussion_notes` entry. Examples to look for:

- Any endpoint in the codebase not covered by a feature contract.
- Any P1 law that requires infrastructure the list doesn't mention (e.g., **canonical RLS enforcer**, **outbox relay**, **schema-translate-map**, **keyset cursor helper**, **feature-catalog CI gate**, **import-law CI gate**).
- Any provider in `backend/providers/` not referenced by a feature.
- Any job in `backend/jobs/` not referenced by a feature.
- Any middleware in `backend/middleware/` not referenced by a feature.
- Any frontend route in `frontend/web_app/src/app/` not referenced by a feature.
- Any mobile screen in `frontend/mobile_app/app/` not referenced by a feature.

Reasoning: `PROMPT_STACK.yaml` is the **future build checklist**. If it misses a piece, the piece will be missed in the build.

---

## 9. DELIVERABLES

| File | Content |
|---|---|
| `_most_imp_docx/PROMPT_STACK.yaml` | **Final merged file** — every feature as a P2 contract. Single source of truth. |
| `_prompt_completion/drafts/{infra,customer,supplier,logistics,employee,admin,system}.yaml` | Per-actor drafts |
| `_prompt_completion/merged/PROMPT_STACK.yaml` | Merged, pre-validation |
| `_prompt_completion/audit/crosscheck.md` | Law breaches, drifts, contradictions |
| `_prompt_completion/audit/validation.md` | Gate results (G1–G12) |
| `_prompt_completion/audit/gaps.md` | All MISSING/BROKEN features with gap analysis |
| `_prompt_completion/index/tracker.md` | Feature → status → evidence table (auto-generated) |
| `_prompt_completion/index/new_features.md` | Features added beyond FEATURE_STACK_LIST |
| `_prompt_completion/raw/<feature_id>_evidence.md` | Raw evidence dumps per feature (traceability) |

---

## 10. SEQUENCE OF EXECUTION

```
Step  1  Setup folders under _prompt_completion/
Step  2  Load P1 rules, P2 template, FEATURE_STACK_LIST, docs
Step  3  Spawn A1–A7 (parallel extraction by actor)
Step  4  Each agent writes its draft + raw evidence
Step  5  Spawn A8 (cross-check laws + drift)
Step  6  Spawn A9 (merge into single PROMPT_STACK.yaml)
Step  7  Spawn A10 (validate against gates G1–G12)
Step  8  Route failures back to responsible agents; loop until green
Step  9  Write final _most_imp_docx/PROMPT_STACK.yaml
Step 10  Generate _prompt_completion/index/tracker.md + gaps.md
Step 11  Commit all deliverables; report summary
```

---

## 11. FINAL QUALITY BARS (must all be true before you stop)

- ✅ Every feature in `FEATURE_STACK_LIST.md` has one contract in `PROMPT_STACK.yaml`.
- ✅ Every contract has all P2 fields populated (or `N/A` with reason).
- ✅ Every contract's `description` has all §4 sub-sections in order.
- ✅ Every `LIVE` contract has a real, on-disk `evidence:` block.
- ✅ Every `MISSING` / `BROKEN` contract has a `discussion_notes` gap entry.
- ✅ Every P1 law violation is flagged with `LAW_BREACH: Law N` and a fix plan.
- ✅ Every code-vs-doc drift is flagged with `DRIFT:` and code wins.
- ✅ Every new feature discovered beyond the list is added with `status: MISSING`.
- ✅ Every `require_feature` literal in the codebase resolves to a contract.
- ✅ Every route in the codebase resolves to a contract (or is flagged as orphan).
- ✅ Every model in `Base.metadata` resolves to a contract (or is flagged as orphan).
- ✅ YAML parses; gates G1–G12 all green.
- ✅ `_prompt_completion/audit/*.md` files contain the full audit trail.

---

## 12. HOW TO REPORT BACK

When finished, output a single summary block:

```yaml
summary:
  total_features: <N>
  live: <N>
  be_only: <N>
  fe_only: <N>
  partial: <N>
  missing: <N>
  broken: <N>
  blocked: <N>
  laws_violated: <N>
  drifts_found: <N>
  new_features_added: <N>
  contracts_written: <N>
  gates_passed: <N>/12
  output_file: _most_imp_docx/PROMPT_STACK.yaml
  working_dir: _prompt_completion/
  next_action: <one line>
```

---

**This prompt is binding. Do not shorten sub-sections. Do not skip fields. Do not invent evidence. Every claim must be traceable to a file, a route, a model, or a document.**
````

---

**That is the prompt.** It is:

- **Self-contained** — references every input source and every output file.
- **Aligned to P1/P2/P3** — uses the exact template already in `PROMPT_STACK.yaml`.
- **Multi-agent ready** — defines 10 agents (A1–A10) with parallel and sequential phases.
- **Quality-gated** — 12 gates (G1–G12) that must pass before merge.
- **Traceable** — every claim must resolve to code, route, model, or doc.
- **Advanced** — flags law breaches, drifts, and new features beyond the list.
- **Reasonable** — no invented evidence; `N/A` is allowed but never omitted.

Paste it as the session opener whenever you start the feature-completion pass.