# Anchored Summary — Router Flattening Migration

**Created:** 2026-08-03  
**Updated:** 2026-08-04 (fresh audit incorporated; security/ + internal/ subfolders flattened; router layout compliance corrected per ARCHITECTURE_AUDIT_REPORT.md)  
**Source:** Conversation history — user inquiry "What did we do so far?" + codebase analysis  
**Session ID:** (current)

---

## 1. Objective of the Summary

This document captures the state of the ZOZI backend codebase as of this session, focusing on the router flattening migration that was performed in prior work. It serves as an anchored reference for what has been done and what remains.

---

## 2. What Was Done

### 2.1 Router Flattening (main migration)

The backend routers were migrated from a **nested subdirectory structure** to a **flat file layout** under `backend/routers/`.

**Before (implied from prior state):**
- Routers lived in surface-based subfolders, e.g. `routers/communication/ws_chat.py`, `routers/security/auth.py`, `routers/supplier/products.py`, etc.
- Imports in `main.py` used dotted subpaths, e.g. `from routers.communication.ws_chat import websocket_user`.

**After (current state):**
- All routers are flat files directly under `backend/routers/`, e.g. `routers/ws_chat.py`, `routers/auth.py`, `routers/supplier_products.py`.
- Imports in `main.py` use flat module paths, e.g. `from routers.ws_chat import websocket_user` (line 169).
- The `_load_routers()` function in `backend/main.py` dynamically loads routers via `importlib.import_module(f"routers.{name}")` (line 347), trying `controllers.{name}` as fallback (line 350).

### 2.2 Key Code Changes in `backend/main.py`

| Change | Location | Detail |
|--------|----------|--------|
| ws_chat import fix | `main.py:169` | `from routers.ws_chat import websocket_user` (was `from routers.communication.ws_chat import ...`) |
| router_names list | `main.py:198-341` | 143 entries using flat module names (e.g. `"auth"`, `"admin_treasury"`, `"supplier_orders"`) |
| Dynamic loading | `main.py:347-350` | `importlib.import_module(f"routers.{name}")` with fallback to `controllers.{name}` |
| WebSocket route | `main.py:171` | `/ws/user` route mapped to `websocket_user` |
| Background jobs WS | `main.py:179-191` | `/ws/admin/background-jobs` route |

---

## 3. Current Codebase State

### 3.1 Router File Count

- **142 flat router files** in `backend/routers/` (excluding `__init__.py` and `__pycache__`)
- **143 entries** in the `router_names` list in `main.py:198-341`
- **3 duplicate entries**: `supplier_orders` (mounted twice at different prefixes), `supplier_payouts` (mounted twice), `supplier_finance` (mounted twice)

### 3.2 Remaining Nested Subdirectories (NOW RESOLVED)

Prior to this session, two subdirectories remained in `backend/routers/`:

| Subfolder | Files | Fate |
|-----------|-------|------|
| `security/` | 6 (auth, fraud_detection, iam, incident, permissions, risk) + `__init__.py` | Deleted — all 6 had flat counterparts already imported by `main.py`; nested copies were orphans |
| `internal/` | 29 router files + `__init__.py` (see git diff) | Deleted — 6 had flat counterparts imported by `main.py`; 23 were orphaned (no `router_names` entry, no flat counterpart) |

**Result:** `backend/routers/` is now **100% flat** — zero subdirectories remain.

### 3.3 Missing Structure

- **Root-level `data/` does not exist.** `backend/data/` exists with 90 flat `.py` files (forwarder shims and helper modules).
- **No surface subdirectories** (admin/, supplier/, customer/, etc.) exist under `backend/routers/` — all routers are flat files (now fully flattened).

### 3.4 main.py Statistics

- **414 lines** total (not 599 as noted in AGENTS.md, which may reflect a prior version)
- `_load_routers()` function handles lazy loading of all 143 router entries
- Additional hardcoded router registrations for special cases:
  - `admin_promotions` country router (line 371)
  - `logistics_partner` plural alias (line 380)
  - `countries` alias at `/admin/countries` (line 390)

### 3.5 Architectural Authority & Router Layout Compliance

`ARCHITECTURE_AUDIT_REPORT.md` is the **authoritative guide ("bible road")** for all structural changes. The `scaffolding_contract.json` is referenced for `_triage/` placement but is **superseded** by the audit report for router layout.

Per the audit report (lines 599–645):

- **Routers must be FLAT** — `backend/routers/` with filenames following `{surface}_{domain}_{operation}.py` (e.g. `admin_orders_management.py`, `supplier_orders_fulfillment.py`, `customer_orders_tracking.py`, `public_catalog_product_browsing.py`).
- **Surface subfolders under `routers/` are FORBIDDEN** — `backend/routers/admin/`, `backend/routers/finance/`, `backend/routers/catalog/`, `backend/routers/orders/` are all **RED violations**.
- "Admin is a surface, not a domain" (line 611). Do **not** create `backend/services/admin/`, `backend/controllers/admin/`, or `backend/routers/admin/`.
- The current flat layout is **correct by design**, not architectural debt. The prior scaffolding contract's `routers/{surface}/{domain}.py` pattern (with subdirectories) is outdated; the audit report supersedes it.

### 3.6 Architecture Audit Results (Updated — 2026-08-04)

A fresh audit was generated at `ARCHITECTURE_AUDIT_REPORT.md` (2026-08-03T20:25 UTC).

| Metric | Pre-flatten | Post-flatten | Change |
|--------|-------------|---------------|--------|
| RED violations | 126 | **120** | −6 |
| YELLOW advisories | 1,743 | **1,703** | −40 |
| GREEN info | 55 | 55 | 0 |
| Architecture debt score | 47,760 | **46,288** | −1,372 |
| Router modules | 159 | **142** | −17 |

**RED reduction:** 6 violations eliminated (126→120) — RN2 (router sub-folder) and RN3 (router nesting) violations from deleting `security/` and `internal/` subfolders, plus associated W1 and LC1 entries for those nested files. Debt score dropped 1,372 points (47,760→46,288).

Remaining RED rules to track: W1 (55 — db writes in controllers/routers), LC1 (38 — layer contract: db.query/execute in routers & controllers), SEC5 (17 — SQL injection), DG3 (3 — cross-domain imports), DOM3 (2 — surface folders in services), CG2 (3 — upward calls in tests/). F4 (8 total YELLOW, but 2 promoted to RED severity: `zozi.db` at backend root and repo root). Note: PERF4 (203), RN1 (133), A2 (150), SYM1 (100), SYM2 (100) are all YELLOW advisories, not RED violations.

The `_triage/` directory is explicitly recognized in the scaffolding contract (`backend/_triage/<file>.py`). This summary file is tracked there without introducing new RED violations.

---

## 4. Summary of Work Done

| # | Action | Status | Evidence |
|---|--------|--------|----------|
| 1 | Flattened router files from subfolders to `backend/routers/` | Done | 142 flat files (excl `__init__.py`); `main.py:169` uses `routers.ws_chat` |
| 2 | Updated `main.py` `_load_routers()` to use flat module names | Done | `main.py:347` — `importlib.import_module(f"routers.{name}")` |
| 3 | Fixed ws_chat import path | Done | `main.py:169` |
| 4 | Flattened security subfolder routers | **Done** | Deleted `backend/routers/security/` (6 files + `__init__.py`) — flat counterparts already existed |
| 4b | Flattened internal subfolder | **Done** | Deleted `backend/routers/internal/` (29 files + `__init__.py`) — 6 had flat counterparts; 23 were orphans |
| 5 | Ran architecture audit (fresh report) | Done | Pre-flatten: RED 126, YEL 1743, debt 47,760 → Post-flatten: RED 120, YEL 1703, debt 46,288 |
| 6 | Verified `data/` directory | Backend only | `backend/data/` has 90 flat `.py` files incl. `routers_security_auth.py`; no root-level `data/` |
| 7 | Fixed audit script Unicode crash | Done | Added stdout UTF-8 reconfiguration in `system_architecture_audit.py:117-124` |

---

## 5. Files Examined in This Session

| File | Status | Notes |
|------|--------|-------|
| `backend/main.py` | Read (414 lines) | Router loading, WSS routes, error handlers |
| `backend/routers/ws_chat.py` | Exists | Imported at `main.py:169` |
| `backend/routers/auth.py` | Exists (flat) | 318 lines; uses flat imports (`from db.database import`, etc.) |
| `backend/routers/security/auth.py` | **Deleted** | Was nested orphan; flat `routers/auth.py` is the active version |
| `backend/routers/security/` | **Deleted** | All 6 files + `__init__.py` removed; `routers/` is now 100% flat |
| `backend/routers/internal/` | **Deleted** | All 29 orphaned router files + `__init__.py` removed; 6 had flat counterparts, remainder were unassigned orphans |
| `backend/data/routers_security_auth.py` | Exists | Forwarder shim imports from `routers.auth` (flat) — still valid after security/ deletion |
| `scripts/system_architecture_audit.py` | Exists | Accepts `--no-fail`, `--show-intended`, `--root`, `--out`, `--emit-registry` |
| `.governance/scaffolding_contract.json` | Read | v3, defines intended router/controller/service/model placement |

---

## 6. Next Steps / Decisions Needed

1. **Router naming consistency**: Filenames should follow `{surface}_{domain}_{operation}.py` pattern per the audit report. Some existing flat files (e.g. `auth.py`, `products.py`, `countries.py`) use simple names without surface prefixes — these should be renamed to include the surface prefix (e.g. `auth.py` → `public_auth.py` or `admin_auth.py`) for compliance with RN1.
2. **Resolve RED violations**: 120 violations need triage — 55 are W1 (db writes in controllers/routers), 17 are SEC5 (SQL injection), 38 are LC1 (layer contract: db operations in routers/controllers), 3 CG2 (upward calls), 3 DG3 (cross-domain imports), 2 DOM3 (surface folders in services), 2 F4 (committed DB artifacts — `zozi.db`).
3. **Post-flattening audit completed**: RED 120, YEL 1703, debt 46,288 — confirmed all router nesting violations (RN2/RN3) resolved; `backend/routers/` is 100% flat with zero subdirectories, matching the audit report's intended layout.

---

## 7. Fixes Applied

### 7.1 Audit Script Unicode Crash (FIXED)

**Problem:** `scripts/system_architecture_audit.py` crashed with `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f534'` on Windows (cp1252) when printing emoji severity icons (`🔴`, `🟡`, `🟢`) via `print()`. This occurred in `render_stdout()` at line 5896 and at the final summary print at line 9606.

**Root cause:** The `SEV_ICON` dictionary (line 133) uses emoji characters that require UTF-8 encoding. Windows Python defaults to cp1252 for `sys.stdout`, which cannot encode these characters. The crash happened in `render_stdout()` which is called **before** `render_markdown()`, so even `--out` was unusable — the script crashed before the markdown report file could be written.

**Fix:** Added stdout/stderr UTF-8 reconfiguration at module load time (after imports, before constants) in `system_architecture_audit.py:117-124`:

```python
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
del _stream
```

This uses `errors="replace"` as a safety net so that even if the terminal can't display emoji, the script won't crash — it will show replacement characters instead.

**Verification:** Both `python scripts/system_architecture_audit.py --no-fail` and `python scripts/system_architecture_audit.py --no-fail --out report.md` now complete successfully without crashing.

---

## 8. Anchoring References

- **Conversation start**: User asked "What did we do so far?" — analysis performed on 2026-08-03.
- **Governance protocol**: `.governance/scaffolding_contract.json` (v3) — placement rules for `_triage/` and general layer structure.
- **Architecture audit report**: `ARCHITECTURE_AUDIT_REPORT.md` (2026-08-03T20:25 UTC) — **authoritative guide ("bible road")** for all structural changes; defines flat router layout `{surface}_{domain}_{operation}.py` and forbidden surface subfolders.
- **AGENTS.md**: Instructions for backend/frontend paths, env vars, and audit script usage.
- **Architecture audit script**: `scripts/system_architecture_audit.py` (v4.1)
