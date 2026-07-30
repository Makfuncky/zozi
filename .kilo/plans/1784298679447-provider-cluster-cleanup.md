# Plan: Consolidate & document the AI / OCR / Vision provider cluster

**Date:** 2026-07-20
**Decision (confirmed with user):** Do **NOT** create a new `backend/providers/**`
package. The AI/OCR/vision code is already consolidated in `backend/services/`.
We will **clean, standardize, and document** that existing cluster so it is
"easy to handle and easy to wire" — with **zero call-site changes** and **no
blast radius** on the 1438-route app.

---

## 1. Context / findings

The "providers" the user cares about (AI, OCR, bg-model, vision, automation) are
**already centralized inside `backend/services/`**, not scattered:

| Capability | Current module | Wraps / sources |
|---|---|---|
| Background removal (6 strategies) | `services/bg_removal_service.py` | `br_05/06/08/11/12/13.py` prototypes from `Working_API/zozi_ai_image_service` |
| Image AI (removal + multiview) | `services/image_ai_service.py` | rembg BiRefNet-lite, HF Inference API, TRELLIS |
| Product vision / variant config | `services/ai_variant_config.py` | Ollama `moondream` (vision) + `phi3:mini` (text) + CV heuristics |
| Bill / text OCR | `services/ocr_parser.py` | local regex parser (no external OCR API) |
| Finance LLM (email/bill/recon) | `services/llm_finance.py` | local Ollama, graceful rules fallback |
| BG removal presets | `services/bg_removal_presets.py` | preset configs |
| Free image tools | `services/free_image_tools.py` | magic_erase etc. |
| Country AI research | `services/country_research.py` | OpenAI (`OPENAI_API_KEY`) |
| AI copy jobs | `services/ai_copy_jobs.py` | uses `ai_variant_config` |

Call sites already import via `from services.X import ...`:
`routers/supplier.py`, `controllers/supplier_controller.py`,
`routers/accounting_extra.py`, `routers/api_v1_finance.py`, `routers/finance_erp.py`,
`routers/finance.py`, `services/ai_copy_jobs.py`, `services/country_research.py`,
`services/finance_automation.py`, `services/imap_mailer.py`, `services/free_image_tools.py`.

External (kept in `Working_API/`, not backend): `zozi_ai_upload_session/upload_auto_*.py`
— standalone bulk-upload automation that hits the live `/supplier/upload` API. Its
reusable logic (Ollama vision + fallback) is already in `ai_variant_config.py`.

**Conclusion:** a new `providers/` package would duplicate `services/` and force a
risky call-site migration. The real value is (a) a single **documented map** of
what each module does + which env keys it needs, and (b) light **standardization**
of the client-construction pattern so wiring is uniform.

---

## 2. Goal

Make the AI/OCR/vision cluster easy to find, easy to wire, and easy to extend —
without moving code or changing imports.

---

## 3. Tasks (implementation-ready)

### T1 — Write `backend/PROVIDERS.md` (the single source of truth)
Document every AI/OCR/vision provider with: capability, module path, function
entry points, required env/settings keys (from `utils/config.py`), fallback
behavior, and call sites. Mirror the table in §1, expanded. Include the env-key
cheat-sheet:
- `OPENAI_API_KEY` (`country_research`)
- `HF_API_TOKEN`, `BG_REMOVAL_MODEL`, `MULTIVIEW_SPACE_ID` (`image_ai_service`)
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL` (`ai_variant_config`, `llm_finance`)
- `AI_USE_VISION` flag (gates `moondream`, default off for VPS safety)

### T2 — Add a thin `backend/providers.py` facade (re-export only, no logic)
Pure pass-through wrappers so there is ONE predictable import surface for the
"AI stuff", while the real implementations stay in `services/`:
```python
from services.bg_removal_service import remove_background, BGRemovalError
from services.image_ai_service import remove_background as image_remove_background
from services.ai_variant_config import analyze_product_image
from services.ocr_parser import parse_bill_text
from services.llm_finance import parse_email_to_ledger, extract_bill_fields
```
This gives "easy wiring" (`from providers import remove_background, analyze_product_image`)
without duplicating code or touching existing call sites. Existing
`from services.X` imports keep working.

### T3 — Standardize the lazy-client pattern (low risk, optional polish)
Confirm each module reads config from `utils.config.settings` (not raw `os.getenv`
in call paths) and has a single obvious `get_*()` / entry function. Where a module
constructs an external client inline, extract a small `_get_client()` lazy factory.
Scope: only `bg_removal_service.py`, `image_ai_service.py`, `ai_variant_config.py`,
`ocr_parser.py`, `llm_finance.py`. No behavior change — refactor only.

### T4 — Update `DATABASE_ARCHITECTURE.md` (or a new `PROVIDERS` section)
Add a short cross-reference pointing to `PROVIDERS.md` so "where are the providers"
is answered from the architecture doc too.

### T5 — Leave out of scope (explicitly)
- **No** move of payments (Stripe/Tap), SMS (Twilio), email (Resend/SMTP), storage
  (S3), or Vault into `providers/`. Those stay in their current `services/` + `utils/config.py`.
- **No** migration of existing `from services.X` call sites (avoids 1438-route blast radius).
- `Working_API/zozi_ai_upload_session/*` stays external; not imported by backend.

---

## 4. Risks / guardrails
- T2 is re-export only → cannot break existing imports. Safe.
- T3 is refactor-only; guard with existing tests (`pytest`) + app-boot smoke
  (route count == 1438, 503 handler present) before/after.
- Do not introduce a generic `Provider` base class — the modules are different
  shapes; keep thin wrappers, not a unifying abstraction.

---

## 5. Validation
1. `python -c "import providers"` succeeds; facade exports resolve.
2. `python -c "import main; print(len(main.app.routes))"` → 1438 (unchanged).
3. `alembic heads` → single head (unchanged).
4. `pytest -q` (existing suite) green, especially `test_performance_fixes.py`,
   `test_image_pipeline.py`, `test_live_pipeline.py` if present.
5. Spot-check: `from providers import remove_background, analyze_product_image,
   parse_bill_text` works in a REPL.

---

## 6. Open questions (none blocking)
- Should `providers.py` also re-export `country_research` (OpenAI) and
  `ai_copy_jobs`? Recommend **yes** (they are AI), but they are not image/OCR —
  include under an "AI (text)" subsection in `PROVIDERS.md`.
