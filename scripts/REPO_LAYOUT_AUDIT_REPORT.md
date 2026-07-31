# Architecture Governance Audit Report v3.2 (GENERATED — do not hand-edit)

**Repo:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\scripts`  
**Result:** 🔴 1 · 🟡 46 · 🟢 4  
**Architecture Debt Score:** `1138`  
**Ephemeral. Add to `.gitignore`. NOT an authoritative spec (those live in `documents/scope/`).**

# INTENDED ZOZI STRUCTURE (target — derived from governance model)
Logical domains `database` & `security` live INSIDE backend/ by design.
Sub-folder axis: SURFACE in routers/ & controllers/ (admin/supplier/...);
                 DOMAIN  in services/ & models/ (finance/orders/...).
```
zozi/
├── backend/
│   ├── routers/        (admin/ supplier/ customer/ public/ webhooks/ = surface OK)
│   ├── controllers/    (admin/ supplier/ ... surface OK; thin orchestration)
│   ├── services/       (finance/ orders/ catalog/ supplier/ logistics/ comms/ hr/ ai/ = domain REQUIRED)
│   ├── models/         (same domain sub-packages; each file declares __table_args__ schema)
│   ├── middleware/  dependencies/  providers/  utils/  events/  jobs/  data/
│   ├── db/  alembic/   (= the 'database' logical domain; ONLY migrations home)
│   └── tests/  scripts/
├── frontend/   (web_app · mobile_app · shared)
├── documents/
│   ├── scope/          (AUTHORITATIVE specs + optional YAML policy)
│   └── archive/        (everything else)
├── monitoring/  nginx/  (infra)
├── experiments/  design/   (gitignored outputs / logo source)
└── .gitignore  .env.example  README.md  docker-compose.yml  railway.toml
```

## Scorecard

| Code | Count | Sev | Meaning |
|---|---:|---|---|
| A2 | 5 | 🟡 ADVISORY | possibly dead/orphan module (no inbound imports; not an entrypoint) |
| CFG3 | 6 | 🟡 ADVISORY | malformed or contradictory policy rule |
| F1 | 7 | 🟡 ADVISORY | scratch/debug script (delete; ops scripts -> scripts/maintenance|validation) |
| F2 | 1 | 🟡 ADVISORY | hardcoded developer-local absolute path in source |
| F4 | 3 | 🟡 ADVISORY | committed cache/build/artifact present (bloat) |
| F9 | 2 | 🟡 ADVISORY | repo-root note outside allow-list / banned dir |
| FE1 | 4 | 🟡 ADVISORY | missing expected frontend workspace/package file |
| FE2 | 7 | 🟡 ADVISORY | frontend scratch/artifact script at package root |
| G0 | 1 | 🔴 VIOLATION | missing/weak root .gitignore (root cause of committed artifacts) |
| I1 | 1 | 🟢 INFO | structure summary |
| I2 | 1 | 🟢 INFO | rules source (yaml vs embedded fallback) |
| I3 | 1 | 🟢 INFO | architecture metric summary |
| MET1 | 1 | 🟢 INFO | architecture debt score |
| P4 | 11 | 🟡 ADVISORY | missing expected backend package |

## 🔥 Damage Hotlist (fix these first)

| Sev | Rule | Domain | Location | Problem | Intended home / action |
|---|---|---|---|---|---|
| 🔴 | G0 | repo | `.gitignore` | no root .gitignore -> artifacts/caches/secrets get committed | add strict root .gitignore (logs, *.db*, caches, node_modules, .env, backups) |
| 🟡 | A2 | backend | `backend\controllers\__init__.py` | module has no inbound imports and is not an obvious entrypoint | verify usage; delete if unused, or wire it through the correct layer |
| 🟡 | A2 | backend | `backend\services\__init__.py` | module has no inbound imports and is not an obvious entrypoint | verify usage; delete if unused, or wire it through the correct layer |
| 🟡 | A2 | backend | `backend\utils\auth.py` | module has no inbound imports and is not an obvious entrypoint | verify usage; delete if unused, or wire it through the correct layer |
| 🟡 | A2 | backend | `backend\utils\constants.py` | module has no inbound imports and is not an obvious entrypoint | verify usage; delete if unused, or wire it through the correct layer |
| 🟡 | A2 | backend | `backend\utils\migrations.py` | module has no inbound imports and is not an obvious entrypoint | verify usage; delete if unused, or wire it through the correct layer |
| 🟡 | CFG3 | repo | `governance.yaml` | graph_exempt_layers references unknown backend folder 'docs' | remove it or create the expected backend package |
| 🟡 | CFG3 | repo | `governance.yaml` | graph_exempt_layers references unknown backend folder 'monitoring' | remove it or create the expected backend package |
| 🟡 | CFG3 | repo | `governance.yaml` | dead_exempt_layers references unknown backend folder 'monitoring' | remove it or create the expected backend package |
| 🟡 | CFG3 | repo | `governance.yaml` | dead_exempt_layers references unknown backend folder 'docs' | remove it or create the expected backend package |
| 🟡 | CFG3 | repo | `governance.yaml` | no_init_dirs references unknown backend folder 'docs' | remove it or create the expected backend package |
| 🟡 | CFG3 | repo | `governance.yaml` | no_init_dirs references unknown backend folder 'monitoring' | remove it or create the expected backend package |
| 🟡 | F1 | frontend | `frontend\countDivs.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F1 | frontend | `frontend\countDivs2.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F1 | frontend | `frontend\linenums.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F1 | frontend | `frontend\patch-vars.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F1 | frontend | `frontend\patch-vars2.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F1 | frontend | `frontend\printLines.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F1 | frontend | `frontend\stackDivs.js` | scratch/debug script (one-off; not an ops/maintenance script) | delete; ops scripts live in scripts/maintenance or scripts/validation |
| 🟡 | F2 | frontend | `frontend\patch-vars.js:5` | hardcoded developer-local absolute path (portability + leak) | use repo-relative paths / config; never commit C:/d:/F:/home paths |
| 🟡 | F4 | backend | `backend\requirements.txt` | must not sit at backend (damages structure/scale) | relocate per scope/repo_structure.yaml or delete |
| 🟡 | F4 | repo | `generate_codebase.py` | must not sit at . (damages structure/scale) | relocate per scope/repo_structure.yaml or delete |
| 🟡 | F4 | repo | `generate_scaffolding.py` | must not sit at . (damages structure/scale) | relocate per scope/repo_structure.yaml or delete |
| 🟡 | F9 | repo | `REPO_LAYOUT_AUDIT_REPORT.md` | doc at repo root outside the allow-list | move to documents/scope/ (authoritative) or documents/archive/ |
| 🟡 | F9 | repo | `SYSTEM_ARCHTECTURE_AUDIT_USAGE.md` | doc at repo root outside the allow-list | move to documents/scope/ (authoritative) or documents/archive/ |
| 🟡 | FE1 | frontend | `frontend` | frontend root package.json missing | add workspace root package.json for monorepo scripts |
| 🟡 | FE1 | frontend | `frontend\mobile_app` | expected frontend workspace 'mobile_app' missing | create/maintain workspace or update governance.yaml |
| 🟡 | FE1 | frontend | `frontend\shared` | expected frontend workspace 'shared' missing | create/maintain workspace or update governance.yaml |
| 🟡 | FE1 | frontend | `frontend\web_app` | expected frontend workspace 'web_app' missing | create/maintain workspace or update governance.yaml |
| 🟡 | FE2 | frontend | `frontend\countDivs.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟡 | FE2 | frontend | `frontend\countDivs2.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟡 | FE2 | frontend | `frontend\linenums.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟡 | FE2 | frontend | `frontend\patch-vars.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟡 | FE2 | frontend | `frontend\patch-vars2.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟡 | FE2 | frontend | `frontend\printLines.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟡 | FE2 | frontend | `frontend\stackDivs.js` | frontend scratch/artifact script at package root | delete; keep only workspace config/package files at root |
| 🟢 | MET1 | repo | `architecture-debt` | architecture debt score = 1138 | track this number down over time; lower is healthier |
| 🟡 | P4 | backend | `backend\routers` | expected backend package 'routers' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\models` | expected backend package 'models' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\middleware` | expected backend package 'middleware' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\dependencies` | expected backend package 'dependencies' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\providers` | expected backend package 'providers' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\alembic` | expected backend package 'alembic' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\tests` | expected backend package 'tests' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\scripts` | expected backend package 'scripts' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\events` | expected backend package 'events' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\jobs` | expected backend package 'jobs' is missing | create the package if this layer is part of the target architecture |
| 🟡 | P4 | backend | `backend\data` | expected backend package 'data' is missing | create the package if this layer is part of the target architecture |

## Architecture Metrics

- architecture debt score: **1138**
- modules: **12**
- dependency edges: **5**
- classes: **154**
- layer counts: `controllers=1`, `db=4`, `main=1`, `services=1`, `utils=5`

### Top fan-in

| Module | Fan-in |
|---|---:|
| `db.database` | 2 |
| `utils.config` | 2 |
| `utils` | 1 |

### Top fan-out

| Module | Fan-out |
|---|---:|
| `main` | 2 |
| `db.models` | 2 |
| `utils.auth` | 1 |

### Auto-discovery

- domains: **0**
- features: **6**
- frontend features: **0**
- backend top dirs: **4**
- learned domain edges: **0**

## Domain: repo

- 🔴 **G0** `.gitignore` — no root .gitignore -> artifacts/caches/secrets get committed → *add strict root .gitignore (logs, *.db*, caches, node_modules, .env, backups)*
- 🟡 **F4** `generate_codebase.py` — must not sit at . (damages structure/scale) → *relocate per scope/repo_structure.yaml or delete*
- 🟡 **F4** `generate_scaffolding.py` — must not sit at . (damages structure/scale) → *relocate per scope/repo_structure.yaml or delete*
- 🟡 **F9** `REPO_LAYOUT_AUDIT_REPORT.md` — doc at repo root outside the allow-list → *move to documents/scope/ (authoritative) or documents/archive/*
- 🟡 **F9** `SYSTEM_ARCHTECTURE_AUDIT_USAGE.md` — doc at repo root outside the allow-list → *move to documents/scope/ (authoritative) or documents/archive/*
- 🟡 **CFG3** `governance.yaml` — graph_exempt_layers references unknown backend folder 'docs' → *remove it or create the expected backend package*
- 🟡 **CFG3** `governance.yaml` — graph_exempt_layers references unknown backend folder 'monitoring' → *remove it or create the expected backend package*
- 🟡 **CFG3** `governance.yaml` — dead_exempt_layers references unknown backend folder 'monitoring' → *remove it or create the expected backend package*
- 🟡 **CFG3** `governance.yaml` — dead_exempt_layers references unknown backend folder 'docs' → *remove it or create the expected backend package*
- 🟡 **CFG3** `governance.yaml` — no_init_dirs references unknown backend folder 'docs' → *remove it or create the expected backend package*
- 🟡 **CFG3** `governance.yaml` — no_init_dirs references unknown backend folder 'monitoring' → *remove it or create the expected backend package*
- 🟢 **I1** `.` — backend models=0 routers=0 controllers=1 services=1 middleware=0
- 🟢 **I2** `documents/scope/` — rules loaded from: EMBEDDED FALLBACK (create documents/scope/*.yaml to make scope authoritative)
- 🟢 **I3** `backend/` — module graph: modules=12, edges=5, classes=154
- 🟢 **MET1** `architecture-debt` — architecture debt score = 1138 → *track this number down over time; lower is healthier*

## Domain: backend

- 🟡 **F4** `backend\requirements.txt` — must not sit at backend (damages structure/scale) → *relocate per scope/repo_structure.yaml or delete*
- 🟡 **P4** `backend\routers` — expected backend package 'routers' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\models` — expected backend package 'models' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\middleware` — expected backend package 'middleware' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\dependencies` — expected backend package 'dependencies' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\providers` — expected backend package 'providers' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\alembic` — expected backend package 'alembic' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\tests` — expected backend package 'tests' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\scripts` — expected backend package 'scripts' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\events` — expected backend package 'events' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\jobs` — expected backend package 'jobs' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **P4** `backend\data` — expected backend package 'data' is missing → *create the package if this layer is part of the target architecture*
- 🟡 **A2** `backend\controllers\__init__.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*
- 🟡 **A2** `backend\services\__init__.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*
- 🟡 **A2** `backend\utils\auth.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*
- 🟡 **A2** `backend\utils\constants.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*
- 🟡 **A2** `backend\utils\migrations.py` — module has no inbound imports and is not an obvious entrypoint → *verify usage; delete if unused, or wire it through the correct layer*

## Domain: frontend

- 🟡 **F2** `frontend\patch-vars.js:5` — hardcoded developer-local absolute path (portability + leak) → *use repo-relative paths / config; never commit C:/d:/F:/home paths*
- 🟡 **F1** `frontend\countDivs.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **F1** `frontend\countDivs2.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **F1** `frontend\linenums.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **F1** `frontend\patch-vars.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **F1** `frontend\patch-vars2.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **F1** `frontend\printLines.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **F1** `frontend\stackDivs.js` — scratch/debug script (one-off; not an ops/maintenance script) → *delete; ops scripts live in scripts/maintenance or scripts/validation*
- 🟡 **FE1** `frontend` — frontend root package.json missing → *add workspace root package.json for monorepo scripts*
- 🟡 **FE1** `frontend\mobile_app` — expected frontend workspace 'mobile_app' missing → *create/maintain workspace or update governance.yaml*
- 🟡 **FE1** `frontend\shared` — expected frontend workspace 'shared' missing → *create/maintain workspace or update governance.yaml*
- 🟡 **FE1** `frontend\web_app` — expected frontend workspace 'web_app' missing → *create/maintain workspace or update governance.yaml*
- 🟡 **FE2** `frontend\countDivs.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
- 🟡 **FE2** `frontend\countDivs2.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
- 🟡 **FE2** `frontend\linenums.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
- 🟡 **FE2** `frontend\patch-vars.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
- 🟡 **FE2** `frontend\patch-vars2.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
- 🟡 **FE2** `frontend\printLines.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
- 🟡 **FE2** `frontend\stackDivs.js` — frontend scratch/artifact script at package root → *delete; keep only workspace config/package files at root*
