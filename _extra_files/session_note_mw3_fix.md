# Session note — MW3 middleware-circuit seam (2026-08-10)

## Finding
`MW3 | 4` — middleware importing services/models (circuit violation: middleware
may import only `db`, `utils`, `dependencies`, `data`):
- `middleware/coi_middleware.py:10` — `from services.coi_service import COIService`
- `middleware/country_context.py:59,150` — lazy `services.country_detection`
- `middleware/impossible_travel_middleware.py:152` — lazy `models.fraud`

## Fix (dependencies-layer seam)
1. **`middleware/coi_middleware.py` — deleted.** Verified dead duplicate of
   `dependencies/coi_dependency.py` (zero importers across the backend; identical
   `_coi_check_internal`; orchestrator does not import it).
2. **New `dependencies/country_detection.py`** — `detect_country_from_ip(headers,
   client_ip)` adapter with module-level cached service; behavior matches the
   middleware exactly (extract → private-IP skip → lookup → country or None).
   `middleware/country_context.py` now calls it; removed the lazy import and the
   now-unused `_get_country_detection_service`/`_country_detection_service`.
3. **New `dependencies/fraud_events.py`** — `record_impossible_travel_event(...)`
   owns the `FraudEvent` write incl. try/finally session close.
   `middleware/impossible_travel_middleware.py` now calls it (drops `models.fraud`).

## Validation
- Full middleware scan: zero `services`/`controllers` imports remain in
  `middleware/*.py` (module-level or lazy).
- Authoritative audit (18:28): **MW3 absent (4 → 0)**; LC1 stays resolved; RED
  total 1464 → 1420.
- `tests/test_mw3_middleware_circuit.py` — 5 tests. **5/5 pass.** Combined
  regression suites: **19 passed** (LC1 5 + PERF2 4 + SEC5 5 + MW3 5).
- Behavioral checks: fraud adapter no-ops without a live DB; country adapter
  returns None for no-IP/private-IP and resolves real lookups ("8.8.8.8" → "US").
- Import chain: orchestrator, country_context, impossible_travel, both adapters
  all import cleanly.

## Left for the agent (not MW3-scope)
- `middleware/country_context.py:32` `from models import User, ...` is the RLS
  scope logic — flagged as **DG** (not MW3), part of the agent's labeled
  "MERGED" RLS consolidation (dead `RowLevelSecurityMiddleware`, live
  `set_session_rls` SQLAlchemy event listener). Do not touch while the RLS
  rework is in flight.
