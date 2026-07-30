# Fix: Backend Command Center 500 + Defensive Error Handler

## Root Cause
1. **`ValueError: Table 'supplier_kyc_requirements' is not allowed`**  
   `backend/controllers/command_center_controller.py` line 689 calls `safe_count(db, "supplier_kyc_requirements", ...)` but that table is missing from the `_ALLOWED_TABLES` whitelist. The model exists in `models/country_enhancements.py`.

2. **`ModuleNotFoundError: No module named 'sentry_sdk'`**  
   `sentry-sdk` is listed in `requirements.txt` but is not installed in the active venv. `_init_sentry()` catches `ImportError` gracefully, but `capture_exception()` unconditionally does `import sentry_sdk` at `utils/error_handler.py:106`, so the error handler itself crashes while handling the original 500.

## Plan

### Task 1 — Add missing table to command center allowlist
- **File:** `backend/controllers/command_center_controller.py`
- **Change:** Add `"supplier_kyc_requirements"` to the `_ALLOWED_TABLES` set (around line 24–30).

### Task 2 — Make `capture_exception` defensive for missing `sentry_sdk`
- **File:** `backend/utils/error_handler.py`
- **Change:** Replace the unconditional `import sentry_sdk` inside `capture_exception` (line 106) with a `try/except ImportError` block that returns early when the package is unavailable. Keep the existing structured logging so the error is still recorded.

### Task 3 — Install missing dependency into the active backend venv
- **Command:**  
  `backend\venv\Scripts\pip install "sentry-sdk[fastapi]>=2.0.0"`
- **Rationale:** `requirements.txt` already declares the dependency; the venv is simply missing it. Installing it makes Sentry operational rather than silently skipped.

## Validation
1. Restart backend and hit `GET /admin/command-center/comprehensive`.
2. Confirm `200 OK` with dashboard data, no `ValueError`.
3. Confirm no `ModuleNotFoundError` in server logs when errors occur.
4. Run backend test suite (if present): `cd backend && pytest`

## Risk / Edge Cases
- If `supplier_kyc_requirements` has no rows, the count returns 0 (safe_fetch falls back to 0 on exception).
- If `sentry-sdk` cannot be installed in the environment, Task 2 ensures the app still boots and logs errors locally.
