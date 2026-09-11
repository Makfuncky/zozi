```
=== AGENT LOG ===
PHASE: 03 — Dependency Forensic Audit
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_03_DEPENDENCY_FORENSICS.md
SCOPE_COVERED: root package.json + package-lock.json + neon.ts; frontend/package.json (orphan) + .npmrc; frontend/web_app package.json + package-lock.json (npm v3); frontend/shared package.json + package-lock.json; frontend/mobile_app package.json + pnpm-lock.yaml (pnpm v9); backend/requirements.txt, requirements-dev.txt, pyproject.toml, Dockerfile, Dockerfile.prod; backend/tests/playwright package.json + lock. Traced actual import usage across backend/ and frontend/ source.
FILES_EXAMINED: ~46 opened directly; grep-scanned ~300 source files
EVIDENCE_ITEMS: ~85 file:line citations
FINDINGS_TOTAL: 29  (VERIFIED: 24 / INFERRED: 3 / UNKNOWN: 2)
SEVERITY_BREAKDOWN: BLOCKER: 3 / HIGH: 2 / MEDIUM: 10 / LOW: 8 / INFO: 6
TOP_FINDINGS:
  1. web_app package.json ↔ package-lock.json out of sync; `npm ci` will fail — frontend/web_app/package.json:26-34 vs frontend/web_app/package-lock.json:22-28,5921,9144,10071,11402
  2. mobile_app package.json (Expo 57) ↔ pnpm-lock.yaml (Expo 55) describe two different apps; `pnpm install --frozen-lockfile` fails — frontend/mobile_app/package.json:13-31 vs frontend/mobile_app/pnpm-lock.yaml:8-118
  3. Root package.json has NO deps but root package-lock.json declares @neon/config/@neon/env; neon.ts imports @neon/config (used-without-declared) — package.json vs package-lock.json:11-13,236-256; neon.ts:1
  4. shared package.json (framer-motion v12 / tailwind-merge v3 / React 19) ↔ shared lock (v11 / v2 / React 18) stale — frontend/shared/package.json:26-31 vs frontend/shared/package-lock.json:11-38
  5. ~13 backend deps declared but never imported (duckdb, duckdb-engine, openpyxl, aiofiles, python-slugify, python-magic, babel, pytz, tzlocal, python-docx, schedule, websockets, faker) — backend/requirements.txt
  6. Test frameworks ship in prod image: requirements.txt (installed by both Dockerfiles) pins pytest==9.1.1 + pytest-asyncio — backend/requirements.txt:105-107; backend/Dockerfile:? ; backend/Dockerfile.prod:17-18
GAPS / NOT DETERMINABLE: (a) Legitimacy/provenance of @neon/config,@neon/env,@neon/sdk npm scope — not verifiable from repo. (b) CVE/vulnerability confirmation — no SCA tool run (READ-ONLY, offline); npm/pnpm/pip resolved transitive trees only partially available. (c) Real-world existence of unusually-high pins (requests==2.34.2, next 16.3.4, react 19.2.8, pytz==2026.3.post1) — not verifiable offline.
SELF_SKEPTICISM_RATING: 5
=== END AGENT LOG ===
```

# PHASE 03 — DEPENDENCY FORENSIC AUDIT

**Target:** Zozi e-commerce platform — third-party dependencies & package management ONLY.
**Method:** Read every manifest and lock file; grep actual `import`/`from`/`require` usage
across `backend/` and `frontend/` source to separate *declared* from *used*. Every claim is
labelled VERIFIED / INFERRED / UNKNOWN with `file:line` evidence. No file under audit was
modified. No SCA/network tooling was run (read-only, offline) — vulnerability claims are
therefore explicitly bounded.

---

## 1. MANIFEST & LOCK-FILE INVENTORY (VERIFIED)

| # | Project | Manifest | Lock file | Package mgr | Lock version |
|---|---------|----------|-----------|-------------|--------------|
| A | Root `zozi` | [package.json](package.json) (scripts only, **no deps**) | [package-lock.json](package-lock.json) | npm | 3 |
| B | `frontend` (orphan) | [frontend/package.json](frontend/package.json) (2 devDeps, no scripts) | *(none)* | npm | — |
| C | `frontend/web_app` (name: `frontend`) | [frontend/web_app/package.json](frontend/web_app/package.json) | [frontend/web_app/package-lock.json](frontend/web_app/package-lock.json) | npm | 3 |
| D | `@zozi/shared` | [frontend/shared/package.json](frontend/shared/package.json) | [frontend/shared/package-lock.json](frontend/shared/package-lock.json) | npm | 3 |
| E | `zozi-mobile-app` | [frontend/mobile_app/package.json](frontend/mobile_app/package.json) | [frontend/mobile_app/pnpm-lock.yaml](frontend/mobile_app/pnpm-lock.yaml) | **pnpm** | 9.0 |
| F | Backend | [backend/requirements.txt](backend/requirements.txt) + [backend/requirements-dev.txt](backend/requirements-dev.txt) | *(no lock — pinned reqs only)* | pip | — |
| G | Backend (config) | [backend/pyproject.toml](backend/pyproject.toml) | — | — | pytest config only, **no `[project]`/deps** |
| H | Backend E2E | [backend/tests/playwright/package.json](backend/tests/playwright/package.json) | [backend/tests/playwright/package-lock.json](backend/tests/playwright/package-lock.json) | npm | 3 |

**Structural observations (VERIFIED):**
- Two different JS package managers coexist in one monorepo: **npm** (A/C/D/H) and **pnpm** (E).
- Root [pyproject.toml](backend/pyproject.toml) is *not* a PEP 621 project — it only holds `[tool.pytest.ini_options]` (no `[project]`, no `[build-system]`, no dependency list). Backend dependency source of truth is `requirements*.txt` (unpinned-lock; pip has no transitive lock).
- `frontend/package.json` (row B) is an **orphan manifest**: no `name`, no `scripts`, only `@testing-library/jest-dom` + `@testing-library/react` devDeps, its own `frontend/node_modules/` and `frontend/.npmrc`, and **no lock file**. Root scripts target `frontend/web_app`, never `frontend` itself → ambiguous project root (see F28).

---

## 2. LOCK-FILE CONSISTENCY — THE CENTRAL FAILURE (VERIFIED)

Every JS lock file in this repo is **out of sync with its manifest**. Because `npm ci` /
`pnpm install --frozen-lockfile` require manifest↔lock agreement, reproducible installs are
broken in CI/Docker for all three JS projects and the root.

### F1 — web_app manifest ↔ lock drift — **BLOCKER** — VERIFIED
The manifest was bumped but `npm install` was never re-run to regenerate the lock.

| Package | Manifest spec ([package.json](frontend/web_app/package.json)) | Lock resolved ([package-lock.json](frontend/web_app/package-lock.json)) | Satisfies? |
|---|---|---|---|
| `next` | `16.3.4` (exact) — line 27 | `16.1.6` — line 9144 | ❌ NO |
| `react` | `19.2.8` (exact) — line 29 | `19.2.3` — line 10071 | ❌ NO |
| `react-dom` | `19.2.8` (exact) — line 31 | `19.2.3` — line 10090 | ❌ NO |
| `eslint-config-next` | `16.3.4` (exact) — line 49 | `16.1.6` — line 5301 | ❌ NO |
| `framer-motion` | `^12.0.0` — line 20 | `11.18.2` — line 5921 | ❌ NO (major) |
| `typescript` | `~5.10` — line 54 | `5.9.3` — line 11402 | ❌ NO |
| `zustand` | `^5.0.11` | `5.0.12` — line 11940 | ✅ |

Evidence: [frontend/web_app/package.json](frontend/web_app/package.json#L26) lines 26–34, 54; lock root `""` snapshot itself still records `next 16.1.6`, `eslint-config-next 16.1.6`, `typescript ^5` at [frontend/web_app/package-lock.json](frontend/web_app/package-lock.json#L22) lines 22–52.
**Impact:** `npm ci` aborts (`EUSAGE`/`ELOCKVERIFY`). Docker/CI builds relying on the lock cannot reproduce the intended React 19.2.8 / Next 16.3.4 / framer-motion 12 stack — they would install the older 16.1.6 / 19.2.3 / 11.18.2 set, or fail. Confidence: High.

### F2 — mobile_app manifest ↔ pnpm-lock describe two different apps — **BLOCKER** — VERIFIED
The current [frontend/mobile_app/package.json](frontend/mobile_app/package.json) is a slim **Expo 57** app; the committed [frontend/mobile_app/pnpm-lock.yaml](frontend/mobile_app/pnpm-lock.yaml) is a much larger **Expo 55** app.

| Aspect | Manifest (package.json) | pnpm-lock importer `.` |
|---|---|---|
| `expo` | `~57.0.9` (line 20) | `^55.0.8` → resolved `55.0.27` (lock line 33) |
| `react` | `19.1.0` (line 26) | `19.2.0` (lock line 105) |
| `react-native` | `0.81.4` (line 28) | `0.83.2` (lock line 109) |
| `@zozi/shared` | **absent** | `file:../shared/dist` (lock line ~30) |
| Extra deps only in lock | — | `expo-router`, `expo-camera`, `expo-image-picker`, `expo-secure-store`, `@sentry/react-native`, `@expo/vector-icons`, `@react-navigation/bottom-tabs`, `react-native-web`, `react-native-qrcode-svg`, `pngjs`, `is-arrayish`, `@babel/runtime` (lock lines 8–118+) |
| Deps in manifest not matching lock specifier | `@stripe/stripe-react-native`, `lucide-react-native`, `@react-native-async-storage/async-storage`, `dayjs`, `react-native-gesture-handler ^2.30.1` (lock: `~2.30.0`) | — |

Evidence: [frontend/mobile_app/package.json](frontend/mobile_app/package.json#L13) lines 13–31; [frontend/mobile_app/pnpm-lock.yaml](frontend/mobile_app/pnpm-lock.yaml#L8) lines 8–118.
**Impact:** `pnpm install --frozen-lockfile` (CI default) fails; `pnpm install` would rewrite the lock wholesale. The lock also references `file:../shared/dist` (a **built** output of `@zozi/shared`) which is produced only by `npm run build:shared` (`tsc --outDir dist`) — if `dist/` is absent the mobile install breaks. Confidence: High.

### F3 — shared manifest ↔ lock drift (React 18→19, framer-motion 11→12, tw-merge 2→3) — **HIGH** — VERIFIED
| Field | [frontend/shared/package.json](frontend/shared/package.json) | [frontend/shared/package-lock.json](frontend/shared/package-lock.json) root `""` |
|---|---|---|
| `framer-motion` | `^12.0.0` (line 27) | `^11.5.6` (line 13) |
| `tailwind-merge` | `^3.5.0` (line 29) | `^2.6.1` (line 14) |
| `react` (devDep) | `^19.2.17` (line 42) | `^18.3.1` (line 26) |
| `@types/react` | `^19.2.17` | `^18.3.1` (line 21) |
| `@types/react-native` | `~0.81.0` | `~0.73.0` (line 23) |
| peer `react-native` | `^0.81.0` (line 20) | `^0.70.0 || ^0.76.0` (line 34) |
| peer `react-native-web` | `^0.21.0` | `^0.19.0 || ^0.21.0` (line 36) |

**Impact:** `@zozi/shared` is consumed by web_app via `file:../shared`. The stale lock means its declared React-19 / framer-motion-12 baseline is not what a reproducible install would resolve. Confidence: High.

### F4 — Root manifest ↔ lock contradiction — **BLOCKER** — VERIFIED
[package.json](package.json) declares **no `dependencies` block at all**, yet [package-lock.json](package-lock.json) root `""` records `@neon/config ^1.2.0` + `@neon/env ^1.2.0` (lines 11–13) and materialises `node_modules/@neon/config` (line 236), `node_modules/@neon/env` (line 250), `node_modules/@neon/sdk` (line 272).
**Impact:** `npm ci` at repo root fails (lock declares deps the manifest does not). Confidence: High.

---

## 3. USED-WITHOUT-BEING-DECLARED / CONTRADICTIONS

### F5 — `neon.ts` uses `@neon/config` but root manifest never declares it — **HIGH** — VERIFIED (usage) / UNKNOWN (provenance)
[neon.ts](neon.ts#L1) line 1: `import { defineConfig } from "@neon/config/v1";` … `defineConfig({ auth: true })`. `@neon/config` appears **only** in [package-lock.json](package-lock.json#L236) (line 236), never in [package.json](package.json).
**Impact:** The import is real (used-without-declared at the manifest layer). If the lock is ever regenerated from the manifest, `@neon/*` disappears and `neon.ts` breaks. `neon.ts` is an isolated repo-root config file — no `frontend/` or `backend/` code imports it (INFERRED: platform/deploy config, likely Neon). **Provenance of the `@neon` npm scope (vs the real `@neondatabase/*`) is NOT DETERMINABLE FROM AVAILABLE CODE** — the lock claims `registry.npmjs.org` URLs but this cannot be verified offline. Confidence: High (contradiction) / Low (legitimacy).

### F6 — web_app's embedded `../shared` snapshot is stale — **MEDIUM** — VERIFIED
[frontend/web_app/package-lock.json](frontend/web_app/package-lock.json#L55) lines 55–66 embed `../shared` with `framer-motion ^11.5.6`, `tailwind-merge ^2.6.1`, `react ^18.3.1`, `@types/react-native ~0.73.0` — i.e. the *old* shared, not current [frontend/shared/package.json](frontend/shared/package.json). Two stale snapshots of the same package now disagree. Confidence: High.

---

## 4. PACKAGE-MANAGER & PEER-DEP HYGIENE

### F7 — Mixed package managers in one monorepo — **MEDIUM** — VERIFIED
npm (root, web_app, shared, backend E2E) + pnpm (mobile). [frontend/.npmrc](frontend/.npmrc) mixes **npm-only** and **pnpm-only** keys in a single file: `shamefully-hoist=true` (pnpm), `strict-peer-dependencies=false` (pnpm), `auto-install-peers=true` (pnpm), `legacy-peer-deps=true` (npm) — lines 1–4. Confidence: High.

### F8 — Peer-dependency enforcement disabled — **LOW** — VERIFIED
`legacy-peer-deps=true` + `strict-peer-dependencies=false` ([frontend/.npmrc](frontend/.npmrc#L2)) silence unmet-peer errors. This masks F17 (web_app does not declare shared's `react-native`/`react-native-svg`/`react-native-web` peers). Confidence: High.

---

## 5. MULTIPLE VERSIONS OF THE SAME PACKAGE (monorepo skew) — VERIFIED

### F9 — React version skew — **MEDIUM**
`19.2.8` (web_app manifest, [frontend/web_app/package.json](frontend/web_app/package.json#L29)) · `19.2.3` (web_app lock, line 10071) · `19.2.17` (shared manifest devDep) · `18.3.1` (shared lock, line 26) · `19.1.0` (mobile manifest, [frontend/mobile_app/package.json](frontend/mobile_app/package.json#L26)) · `19.2.0` (mobile lock, line 105). Six distinct React specifiers for shared components.

### F10 — framer-motion major skew (v11 vs v12) — **MEDIUM**
Manifests want `^12.0.0` (web_app line 20, shared line 27); both locks resolve **v11** (`11.18.2` web_app line 5921; `^11.5.6` shared line 13).

### F11 — tailwind-merge major skew (v2 vs v3) — **MEDIUM**
web_app resolves `3.5.0` (line 11006); shared lock pins `^2.6.1` (line 14) though shared manifest now says `^3.5.0`. `twMerge` is called in [frontend/shared/src/utils.ts](frontend/shared/src/utils.ts#L2) — a v2/v3 class-merging behavioural difference risk.

### F12 — zustand range spread — **LOW**
web_app `^5.0.11` → locked `5.0.12`; shared **requires** `^5.0.14`; mobile `^5.0.14`. Locked `5.0.12` does **not** satisfy shared's `^5.0.14` → potential duplicate/nested install once the shared lock is regenerated. Evidence: [frontend/web_app/package-lock.json](frontend/web_app/package-lock.json#L11940), [frontend/shared/package.json](frontend/shared/package.json#L30).

### F13 — Playwright version spread — **LOW**
`@playwright/test ^1.58.2` (web_app) · `playwright ^1.50.0` (mobile devDep) · `@playwright/test ^1.62.0` → `1.62.0` (backend E2E, [backend/tests/playwright/package-lock.json](backend/tests/playwright/package-lock.json#L13)). Three Playwright majors' browsers to provision.

---

## 6. UNUSED / DECLARED-BUT-NEVER-USED

### Frontend (web_app)
| # | Package | Declared | Import found in source? | Status |
|---|---------|----------|-------------------------|--------|
| F14a | `jspdf` `^4.1.0` | dep | **none** (grep `src/**`, `scripts/**`, config) | Declared-but-unused — VERIFIED |
| F14b | `core-js` `^3.37.1` | dep | **none** (no side-effect import; [next.config.ts](frontend/web_app/next.config.ts) has no polyfill wiring) | Declared-but-unused — VERIFIED |
| F14c | `class-variance-authority` `^0.7.1` | dep | **none** (`cva` never imported; only `clsx`+`tailwind-merge` used) | Declared-but-unused — VERIFIED |
| F15 | `@stripe/react-stripe-js` `^5.6.0`, `@stripe/stripe-js` `^8.7.0` | dep | **only** a `jest.mock` at [checkout.test.tsx](frontend/web_app/src/__tests__/pages/checkout.test.tsx#L81) lines 81,88 — no app import | Elements integration unwired — VERIFIED (absence) / INFERRED (intent) |

**F14 severity LOW; F15 MEDIUM-adjacent (LOW):** Stripe React SDKs are shipped and mocked in tests but never imported by application code — checkout likely uses a redirect/backend Stripe flow, or Elements is incomplete. Confidence: High for absence.

### Backend — declared in [requirements.txt](backend/requirements.txt) but never imported by application code
Verified by exhaustive `import`/`from` grep across `backend/` (excluding the architecture allow-list test, which merely *enumerates* sanctioned roots at [test_import_direction_all_packages.py](backend/tests/system/test_import_direction_all_packages.py#L120)):

| # | Package (line) | Import token | Used in app? | Status |
|---|---|---|---|---|
| F18a | `duckdb==1.5.5` (97), `duckdb-engine==0.17.0` (98) | `duckdb` | none | Declared-but-unused — VERIFIED |
| F18b | `openpyxl==3.1.5` (85) | `openpyxl` | none | Declared-but-unused — VERIFIED |
| F18c | `aiofiles==25.1.0` (47) | `aiofiles` | none | Declared-but-unused — VERIFIED |
| F18d | `python-slugify==8.0.4` (78) + `text-unidecode==1.3` (88) | `slugify` | none | Declared-but-unused — VERIFIED |
| F18e | `python-magic==0.4.27` (48) | `magic` | none | Declared-but-unused — VERIFIED |
| F18f | `babel==2.18.0` (81) | `babel` | none | Declared-but-unused — VERIFIED |
| F18g | `pytz==2026.3.post1` (79) | `pytz` | none | Declared-but-unused — VERIFIED |
| F18h | `tzlocal==5.4.4` (80) | `tzlocal` | none | Declared-but-unused — VERIFIED |
| F18i | `python-docx==1.2.0` (82) | `docx` | none | Declared-but-unused — VERIFIED |
| F18j | `schedule==1.2.2` (84) | `schedule` | none (celery + apscheduler are the real schedulers) | Declared-but-unused — VERIFIED |
| F18k | `websockets==16.1.1` (94) | `websockets` | none (WS handled via `fastapi.WebSocket`; only a docstring mention at [database.py](backend/infrastructure/database/database.py#L387)) | Declared-but-unused as direct dep — VERIFIED |
| F18l | `faker==40.36.0` (83) | `faker`/`Faker` | none in app code | Misplaced + unused — VERIFIED |

**F18 severity MEDIUM (cumulative):** ~13 packages (incl. native `duckdb`, `python-magic`→libmagic) are installed into every image for no code path. `feedparser` (guarded, [rss_provider.py](backend/providers/news/rss_provider.py#L13)), `numpy` ([dei_auditor.py](backend/domains/hr/services/performance/dei_auditor.py#L14), [supplier_supplier_upload_service.py](backend/domains/suppliers/services/products/supplier_supplier_upload_service.py#L16)), `phonenumbers` ([phone_utils.py](backend/infrastructure/utils/phone_utils.py#L6)), `cachetools`, `structlog`, `slowapi`, `sentry_sdk`, `stripe`, `apscheduler`, `celery` ARE used — so this is targeted, not blanket. Confidence: High (absence proven by grep).

### F17 — shared peer deps not imported by shared source — **INFO** — INFERRED
Shared declares peers `react-native-web` and `react-dom` but neither is imported in `frontend/shared/src` (only `react`, `react-native`, `react-native-svg`, `framer-motion`, `clsx`, `tailwind-merge`, `lucide-react`, `zustand/vanilla` are — see [utils.ts](frontend/shared/src/utils.ts#L1), [notificationStore.ts](frontend/shared/src/notificationStore.ts#L1)). `react-native`/`react-native-svg` appear only in `*.native.tsx` variants not consumed by web_app's web build. Confidence: Medium.

---

## 7. RUNTIME vs BUILD-TIME / DEV-IN-PROD MISCLASSIFICATION

### F19 — Test frameworks ship in the production image — **MEDIUM** — VERIFIED
Both [backend/Dockerfile](backend/Dockerfile) and [backend/Dockerfile.prod](backend/Dockerfile.prod#L17) install **only** `requirements.txt` (`pip install --no-cache-dir -r requirements.txt`), and `requirements.txt` ends with `pytest==9.1.1` + `pytest-asyncio==1.4.0` ([requirements.txt](backend/requirements.txt#L105) lines 105–107). Result: `pytest`, `pluggy`, `pytest-asyncio` are present in the runtime image. Bloat + larger attack surface, not a runtime break. Confidence: High.

### F16 — Frontend `@types/*` / test util misclassified as prod `dependencies` — **INFO** — VERIFIED
In [frontend/web_app/package.json](frontend/web_app/package.json#L11) `dependencies`: `@testing-library/dom` (a test util) and `@types/dompurify` (a type stub) are placed in prod deps rather than `devDependencies`. Additionally, `dompurify@^3.3.3` ships its own types, so `@types/dompurify` is likely a **redundant/deprecated stub** (DefinitelyTyped `@types/dompurify` was deprecated once DOMPurify 3 bundled types). Confidence: High (misclassification) / Medium (redundancy).

---

## 8. DECLARED-BUT-NEVER-USED vs DEV-IN-PROD — pytest CONFLICT

### F20 — pytest pinned to two different versions — **MEDIUM** — VERIFIED
`pytest==9.1.1` in [requirements.txt](backend/requirements.txt#L106) vs `pytest==9.2.0` in [requirements-dev.txt](backend/requirements-dev.txt#L3). Direct contradiction: which one "wins" depends on install order (prod-then-dev upgrades to 9.2.0; prod-only image stays on 9.1.1). Confidence: High.

### F21 — Loose/duplicate pins — **LOW** — VERIFIED
- `faker` appears **twice**: pinned `==40.36.0` in prod ([requirements.txt](backend/requirements.txt#L83)) and **unpinned** in dev ([requirements-dev.txt](backend/requirements-dev.txt#L8)).
- `hypothesis` unpinned ([requirements-dev.txt](backend/requirements-dev.txt#L6)); `starlette` unpinned in prod ([requirements.txt](backend/requirements.txt#L13)) — pip will pick any version inside FastAPI 0.115.2's `starlette` range, weakening reproducibility (no pip lock exists to freeze it).

---

## 9. REDUNDANT / OVERLAPPING LIBRARIES (backend)

### F22 — Two JWT libraries, both used — **MEDIUM** — VERIFIED
- `python-jose[cryptography]==3.5.0` (import `jose`) — app auth [auth.py](backend/infrastructure/security/auth.py#L14), [system_comms_status_service.py](backend/domains/comms/services/system_comms_status_service.py#L16), [providers/auth/jwt.py](backend/providers/auth/jwt.py#L9).
- `pyjwt==2.13.0` (import `jwt`) — [auth_service.py](backend/domains/accounts/services/auth/auth_service.py#L32), Apple Sign-In `PyJWKClient` [providers/auth/apple.py](backend/providers/auth/apple.py#L18) lines 18–19, [test_websocket_auth.py](backend/tests/security/test_websocket_auth.py#L17).

Two JWT implementations with potentially different default validation semantics in security-critical paths. `PyJWKClient` legitimately needs PyJWT; but overlapping encode/decode across two libs is an inconsistency risk. **python-jose maintenance/advisory history:** flagged for follow-up SCA only — **cannot confirm any CVE offline** (see §12). Confidence: High (both used) / Unknown (security).

### F23 — Two HTTP clients, both used — **LOW** — VERIFIED
`httpx==0.28.1` (payments, AI, geography providers) and `requests==2.34.2` ([apple.py](backend/providers/auth/apple.py#L21), [oauth.py](backend/providers/auth/oauth.py#L17), [bank_api.py](backend/providers/finance/bank_api.py#L14), [paytabs.py](backend/providers/payments/paytabs.py#L14), [tap.py](backend/providers/payments/tap.py#L14), [thawani.py](backend/providers/payments/thawani.py#L14)). Redundant transport stacks. Confidence: High.

### F24 — Dual Postgres drivers (NOT a defect) — **INFO** — VERIFIED
`asyncpg==0.31.0` (async) + `psycopg2-binary==2.9.12` (sync) are both intentional: [database.py](backend/infrastructure/database/database.py#L163) rewrites URLs to `postgresql+asyncpg://` for the async engine and falls back to sync `psycopg2` (see runtime log [var/uvicorn.out](backend/var/uvicorn.out#L90) showing a `psycopg2.OperationalError`). Reported for completeness; not flagged as waste. Confidence: High.

---

## 10. KNOWN INCOMPATIBLE COMBINATION

### F25 — `passlib[bcrypt]==1.7.4` + `bcrypt==5.0.0` — **MEDIUM** — VERIFIED (combo) / mitigated
[requirements.txt](backend/requirements.txt#L31) pins `bcrypt==5.0.0`; `passlib[bcrypt]==1.7.4` is also pinned. passlib 1.7.4 (last release 2020) reads `bcrypt.__about__.__version__`, which was removed in `bcrypt>=4.1` — a well-known breakage that makes passlib emit a version-detection error/traceback with modern bcrypt.
**Actual exposure is limited:** passlib is imported in exactly one place — the seed script [seed_loader.py](backend/scripts/seed_loader.py#L580) `from passlib.hash import bcrypt as _bcrypt`, wrapped in `try/except` with a pre-computed hash fallback (lines 580–586). Application auth uses `bcrypt` **directly** ([auth.py](backend/infrastructure/security/auth.py#L12)), bypassing passlib. So the incompatible combo is present but the failure path is caught and does not affect production auth. Confidence: High.

---

## 11. NATIVE / BINARY DEPENDENCIES — VERIFIED

- **Backend native:** `psycopg2-binary` (bundled libpq), `Pillow==12.3.0`, `numpy==2.2.6`, `bcrypt==5.0.0`, `python-magic` (needs system libmagic — but F18e shows it is unused), `duckdb==1.5.5` (native — but F18a shows it is unused). Base image `python:3.11-slim` ([backend/Dockerfile.prod](backend/Dockerfile.prod#L1)).
- **Dockerfile system libs vs Python deps mismatch (INFO):** Both Dockerfiles `apt-get install` GL/vision libs `libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1` ([Dockerfile.prod](backend/Dockerfile.prod#L5) lines 5–14) — these exist for `opencv`/`rembg`, which are **commented out** in [requirements.txt](backend/requirements.txt#L38) (lines 38, 42–43). So heavy system layers are installed for Python packages that are never installed → wasted image size (not a break; AI degrades via `HAS_*` flags per the file's own header comment).
- **Mobile native (RN):** `react-native-reanimated`, `react-native-gesture-handler`, `react-native-screens`, `react-native-svg`, `@react-native-async-storage/async-storage`, `@stripe/stripe-react-native` — all require native linking; governed by the Expo version, which is itself desynced (F2).

---

## 12. VULNERABILITIES — BOUNDED / NOT CONFIRMED

### F27 — No SCA performed; no CVE asserted — **UNKNOWN**
This audit is **read-only and offline**: `npm audit`, `pnpm audit`, `pip-audit`, and OSV/GitHub-advisory lookups were **not run** and could not be. Therefore **no CVE is confirmed or denied here.** Per the evidence standard, the following are *leads for a real SCA run*, not findings:
- `python-jose==3.5.0` — the `python-jose` project has a history of advisories on older lines (algorithm-confusion / JWE-DoS class issues affected `<=3.3.0`); `3.5.0` is a later release whose status **cannot be verified from the repo**. Classification: *potentially requires verification*.
- The unusually-high pins in F26 cannot be matched against any advisory DB offline.

**Action:** run `pip-audit -r backend/requirements.txt`, `npm audit --package-lock-only` in web_app/shared, and `pnpm audit` in mobile in a networked environment. Do NOT treat any package here as "known-vulnerable" without that output.

### F26 — Version provenance unverifiable — **INFO** — UNKNOWN
Several pins are higher than any release this audit can confirm offline and are reported *as declared* only: `requests==2.34.2` (public line historically at 2.32.x), `next 16.3.4` / `react 19.2.8` / `react-dom 19.2.8` (manifest), `pytz==2026.3.post1`, `redis==8.0.1`. `NOT DETERMINABLE FROM AVAILABLE CODE` whether these exact versions are published/installable. This matters because the locks resolve *different* (lower) versions (F1), so what actually installs ≠ what is written.

---

## 13. ORPHAN / STRUCTURAL

### F28 — Orphan `frontend/package.json` — **LOW** — VERIFIED
[frontend/package.json](frontend/package.json) has only `@testing-library/jest-dom` + `@testing-library/react` devDeps, no `name`, no `scripts`, no lock, but owns `frontend/node_modules/` and `frontend/.npmrc`. Root scripts always `cd frontend/web_app`. This is a second, ambiguous npm root inside `frontend/`. Confidence: High.

### F29 — E2E project isolated but version-forward — **INFO** — VERIFIED
[backend/tests/playwright/package.json](backend/tests/playwright/package.json) is a standalone npm project (`@playwright/test ^1.62.0`, lock consistent at `1.62.0`). It is the *only* JS lock in the repo that is internally consistent — but its Playwright major is ahead of web_app's (`^1.58.2`) and mobile's (`^1.50.0`) (F13).

---

## 14. FULL FINDINGS TABLE (per-package, high-signal subset)

| Package | Version (manifest) | Lock/resolved | Observed usage | Status | Severity |
|---|---|---|---|---|---|
| next | 16.3.4 | 16.1.6 | app framework (used) | manifest≠lock | BLOCKER (F1) |
| react/react-dom | 19.2.8 | 19.2.3 | used | manifest≠lock + skew | BLOCKER/MED (F1,F9) |
| framer-motion | ^12.0.0 | 11.18.2 | Logo/Loading (shared+web) | major manifest≠lock | MED (F10) |
| typescript | ~5.10 | 5.9.3 | build | manifest≠lock | HIGH (F1) |
| tailwind-merge | ^3.5.0 | 2.6.1 (shared lock) | `twMerge` used | major skew | MED (F11) |
| zustand | ^5.0.11 | 5.0.12 | stores (used) | range < shared req ^5.0.14 | LOW (F12) |
| @stripe/react-stripe-js, @stripe/stripe-js | ^5.6.0/^8.7.0 | present | test mock only | unused in app | LOW (F15) |
| jspdf | ^4.1.0 | present | none | unused | LOW (F14a) |
| core-js | ^3.37.1 | present | none | unused | LOW (F14b) |
| class-variance-authority | ^0.7.1 | present | none | unused | LOW (F14c) |
| @types/dompurify | ^3.0.5 | present (in `dependencies`) | types only | misplaced + redundant | INFO (F16) |
| @neon/config,@neon/env | (not in manifest) | in lock 1.2.0 | neon.ts import | used-without-declared | HIGH (F5) |
| expo | ~57.0.9 | 55.0.27 (lock) | mobile | manifest≠lock | BLOCKER (F2) |
| pytest | 9.1.1 (prod) / 9.2.0 (dev) | — | tests | conflict + in prod image | MED (F19,F20) |
| passlib | 1.7.4 | — | seed only (try/except) | incompatible w/ bcrypt 5 | MED (F25) |
| bcrypt | 5.0.0 | — | app auth (used) | ok directly | — |
| python-jose | 3.5.0 | — | app JWT (used) | 2nd JWT lib; SCA needed | MED (F22) |
| pyjwt | 2.13.0 | — | Apple/auth_service (used) | 2nd JWT lib | MED (F22) |
| httpx / requests | 0.28.1 / 2.34.2 | — | both used | redundant clients | LOW (F23) |
| asyncpg / psycopg2-binary | 0.31.0 / 2.9.12 | — | via SQLAlchemy URL | intentional dual | INFO (F24) |
| duckdb, duckdb-engine, openpyxl, aiofiles, python-slugify, text-unidecode, python-magic, babel, pytz, tzlocal, python-docx, schedule, websockets, faker | pinned | — | none in app | declared-but-unused | MED (F18) |
| feedparser, numpy, phonenumbers, cachetools, structlog, slowapi, sentry-sdk, stripe, celery, apscheduler | pinned | — | imported/used | OK | — |

---

## 15. DEPENDENCY HEALTH SCORE

Scores are 0–10 (10 = best), each justified by the evidence above.

### Correctness — **6 / 10**
Runtime dependency *usage* is largely correct: the core web (Next/React/zustand/dompurify/jose/chart.js/@zxing/qrcode) and backend (FastAPI/SQLAlchemy/celery/redis/stripe/structlog/bcrypt) stacks are genuinely imported and wired, and optional AI deps degrade via `HAS_*` flags. Deductions: one **genuine incompatible combo** (passlib 1.7.4 × bcrypt 5.0, F25, mitigated), **two JWT libraries** in security paths (F22), **two HTTP clients** (F23), and a used-without-declared root import (`@neon/config`, F5). No correctness-fatal runtime import failure was found in application code paths.

### Maintainability — **4 / 10**
Dragged down by **~13 unused backend packages** (F18) and **3–4 unused/half-wired web deps** (F14/F15), `@types`/test-utils misclassified into prod deps (F16), an **orphan `frontend/package.json`** (F28), **mixed npm+pnpm** with a conflated `.npmrc` (F7/F8), and **monorepo version skew** across React/framer-motion/tailwind-merge/Playwright (F9–F13). The surface area declared far exceeds the surface area used.

### Security — **5 / 10** (provisional — SCA not run)
No CVE is confirmed or denied (F27 — offline). Structural security concerns are real and evidence-backed: peer-dep enforcement disabled (`legacy-peer-deps`, F8) hiding install-time conflicts; two JWT libraries with divergent default validation (F22); `python-jose` flagged for mandatory follow-up scanning; and test frameworks shipped into the production image enlarging attack surface (F19). Score is provisional and should be recomputed after `pip-audit` / `npm audit` / `pnpm audit`.

### Reproducibility — **2 / 10**
The worst dimension. **Every** JS lock is desynced from its manifest — root (F4), web_app (F1), shared (F3), mobile (F2) — so `npm ci` and `pnpm install --frozen-lockfile` cannot succeed anywhere; exact pins in package.json (next 16.3.4, react 19.2.8) do not exist in the lock (16.1.6 / 19.2.3). Backend has **no pip lock at all** (only `requirements*.txt`) with **unpinned** entries (`starlette`, `hypothesis`, `faker`) and a **direct pytest version conflict** between prod and dev (9.1.1 vs 9.2.0, F20). What installs today ≠ what the manifests describe.

**Overall (unweighted mean): ~4.25 / 10.** The application *is* functionally assembled from real, mostly-used core libraries, but its dependency **management** — reproducibility above all — is broken across all sub-projects and carries substantial unused/duplicated surface area.

---
*End of Phase 03 report. Read-only audit; no codebase file was modified. Vulnerability confirmation requires a networked SCA run and was intentionally not asserted.*
```
=== AGENT LOG ===
PHASE: 03 — Dependency Forensic Audit
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_03_DEPENDENCY_FORENSICS.md
SCOPE_COVERED: root package.json + package-lock.json + neon.ts; frontend/package.json (orphan) + .npmrc; frontend/web_app package.json + package-lock.json (npm v3); frontend/shared package.json + package-lock.json; frontend/mobile_app package.json + pnpm-lock.yaml (pnpm v9); backend/requirements.txt, requirements-dev.txt, pyproject.toml, Dockerfile, Dockerfile.prod; backend/tests/playwright package.json + lock. Traced actual import usage across backend/ and frontend/ source.
FILES_EXAMINED: ~46 opened directly; grep-scanned ~300 source files
EVIDENCE_ITEMS: ~85 file:line citations
FINDINGS_TOTAL: 29  (VERIFIED: 24 / INFERRED: 3 / UNKNOWN: 2)
SEVERITY_BREAKDOWN: BLOCKER: 3 / HIGH: 2 / MEDIUM: 10 / LOW: 8 / INFO: 6
TOP_FINDINGS:
  1. web_app package.json ↔ package-lock.json out of sync; `npm ci` will fail — frontend/web_app/package.json:26-34 vs frontend/web_app/package-lock.json:22-28,5921,9144,10071,11402
  2. mobile_app package.json (Expo 57) ↔ pnpm-lock.yaml (Expo 55) describe two different apps; `pnpm install --frozen-lockfile` fails — frontend/mobile_app/package.json:13-31 vs frontend/mobile_app/pnpm-lock.yaml:8-118
  3. Root package.json has NO deps but root package-lock.json declares @neon/config/@neon/env; neon.ts imports @neon/config (used-without-declared) — package.json vs package-lock.json:11-13,236-256; neon.ts:1
  4. shared package.json (framer-motion v12 / tailwind-merge v3 / React 19) ↔ shared lock (v11 / v2 / React 18) stale — frontend/shared/package.json:26-31 vs frontend/shared/package-lock.json:11-38
  5. ~13 backend deps declared but never imported (duckdb, duckdb-engine, openpyxl, aiofiles, python-slugify, python-magic, babel, pytz, tzlocal, python-docx, schedule, websockets, faker) — backend/requirements.txt
  6. Test frameworks ship in prod image: requirements.txt (installed by both Dockerfiles) pins pytest==9.1.1 + pytest-asyncio — backend/requirements.txt:105-107; backend/Dockerfile:17-18; backend/Dockerfile.prod:17-18
GAPS / NOT DETERMINABLE: (a) Legitimacy/provenance of @neon/config,@neon/env,@neon/sdk npm scope — not verifiable from repo. (b) CVE/vulnerability confirmation — no SCA tool run (READ-ONLY, offline). (c) Real-world existence of unusually-high pins (requests==2.34.2, next 16.3.4, react 19.2.8, pytz==2026.3.post1) — not verifiable offline.
SELF_SKEPTICISM_RATING: 5
=== END AGENT LOG ===
```
