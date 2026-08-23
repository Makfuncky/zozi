

  ## Production Standard (non-negotiable):
  - We are at GO-TO-PRODUCTION level. Every fix must be PROFESSIONAL, ACCURATE, and COMPLETE. There is ZERO tolerance for drifting, loopholes, stubs, shortcuts, leftover TODOs, or any mistake that would fail in production.
  - Every change must leave the code SMOOTHER, FASTER, and PROPERLY WIRED than before — never slower, never loosely connected, never half-working.
  - You work INDEPENDENTLY. Do NOT ask for clarification, do NOT wait for input, do NOT assume external context. Read the code, read the diagram, diagnose, decide, fix, verify. You are the sole authority on what is broken and how to fix it.

  ## Objective:
  - Bring the Target into 100% compliance with `D:\Projects\10- E-COMMERCE WEBSITE\zozi\ARCHITECTURE_DIAGRAM.md` (three axes + seven laws) AND make it fully workable, fully wired, logically correct, and production-ready end-to-end.
  - DIAGNOSE every function, every data flow, every integration point for LOGICAL ERRORS, broken execution paths, silent failures, incorrect transformations, and contract violations — not just structural placement.
  - MERGE files whose content is similar/duplicated to eliminate excess and produce one clean canonical owner per responsibility — while preserving ALL logic.
  - INTELLIGENTLY RE-ARRANGE all code so it runs smoothly, faster, and is properly wired; CHECK & COMPARE every data-table and its wiring; REPAIR every broken function AND every broken logic path; and complete the Target from ALL production perspectives.
  - Run a CONTINUOUS loop: diagnose → fix → re-diagnose → fix → … until ZERO violations remain, ZERO logic errors remain, every file contains real substance, every function executes correctly, every table is correct and wired, and the code runs cleanly. Do NOT stop after one pass.
  - Do this WITHOUT drifting: never invent structure, never create empty/hollow files, never create extra files, never claim completion without evidence.

  ## Target:
  - You are responsible to audit, diagnose, and repair everything inside `/backend/domains/finance`, including its wiring to `modules/*/routers`, `domains/*/services`, `jobs/`, `providers/`, and `infrastructure/`.
    (Swap this line for any domain/module/infrastructure package.)

  ## Ground Truth (the ONLY external reference):
  - The ONLY structural authority is `D:\Projects\10- E-COMMERCE WEBSITE\zozi\ARCHITECTURE_DIAGRAM.md`. Before creating, moving, merging, or deleting ANYTHING, open it and cite the exact section/line that justifies it.
  - Canonical domain layout (diagram §3) — NOTHING else is allowed inside a domain folder:
      services/  models/  schemas/  policies/
      events.py  subscribers.py  features.py  ports.py  read_models/
  - Slicing rule (diagram §3): > ~8 services OR > ~12 tables → slice into sub-capability folders. Otherwise flat.
  - The Seven Laws: (1) arrows down only; (2) thin routers; (3) cross-domain via ports/events only; (4) features single-sourced in features.py; (5) country scope; (6) schema discipline `__table_args__={'schema':'<domain>'}`; (7) allowlist only shrinks.
  - NO other external input is needed. The code itself + the diagram are sufficient to diagnose and repair everything.

  ## Process — LOOP until clean:

  ### PHASE A — Deep Inventory (re-run every iteration)
  1. Walk the Target recursively. For EVERY file record: path, line count, non-comment code lines, imports, defined functions/classes, and whether it is EMPTY (< 5 lines of real code) or HOLLOW (declares functions/classes with no body / `pass`).
  2. Map every file's domain signals: `__tablename__`, class names, function names, imports, route tags — to determine where it SHOULD live per the placement contract.
  3. SIMILARITY DETECTION (for merging): group files that are candidates for merge. Two files are "similar" when ANY of these hold:
    - Same domain + same layer AND ≥ 60% overlap in function/class name tokens.
    - They define overlapping or duplicate ORM models / the same `__tablename__`.
    - They implement the same service purpose under different names (duplicated logic).
    - One is a near-duplicate or older revision of the other.
    Record each merge group with the chosen canonical owner.
  4. DATA-TABLE INVENTORY: list every ORM model (`__tablename__` + schema) and every Alembic-created table; prepare them for the wiring comparison in Phase C.
  5. Write the full inventory + violations into `RESOLVER.md` as a table (one row per problem: ID, File, Problem, Diagram rule, Action).

  ### PHASE B — DEEP LOGIC DIAGNOSTICS (the critical missing layer)
  For EVERY function in EVERY service file, perform the following diagnostic trace. Log every defect found.

  #### B.1 — EXECUTION PATH TRACE
  - Read each function top-to-bottom. For EVERY code path (if/else, try/except, loops, early returns):
    - Does every path produce a valid return value (or explicitly raise)?
    - Are there paths that fall through without returning (implicit `None` return)?
    - Are there unreachable code blocks after an unconditional return/raise?
    - Does every `try` block have a meaningful `except` that either handles or re-raises?
    - Are there `except` blocks that catch too broadly and hide the real error?
  - DEFECT if: any path silently returns None where a value is expected; any exception is swallowed without logging; any code is unreachable.

  #### B.2 — NAME RESOLUTION & IMPORT CHAIN
  - For every name used inside a function body, verify it resolves:
    - Is it imported at the top of the file? (missing import = BROKEN)
    - Is it defined earlier in the same file? (forward reference without declaration = BROKEN)
    - Is it a parameter? (missing parameter in signature vs call-site mismatch = BROKEN)
    - Is it a class attribute? (accessing attribute that doesn't exist on the class = BROKEN)
    - Is it a module-level constant? (referencing a constant that was moved/renamed = BROKEN)
  - For every import statement: does the imported module/symbol actually exist at that path?
  - DEFECT if: any name is unresolved, any import points to a non-existent path, any call-site passes wrong argument count/types.

  #### B.3 — DATA FLOW & TRANSFORMATION INTEGRITY
  - Trace every piece of data from INPUT to OUTPUT through the function:
    - Input: What does the function receive? (parameters, DB query results, event payloads)
    - Transformation: What operations are performed? (filtering, mapping, aggregation, computation)
    - Output: What does it return or write? (response dict, DB write, event emission)
  - At each transformation step, verify:
    - Type consistency: does the output type of step N match the expected input type of step N+1?
    - Null/None safety: can any intermediate value be None? Is it checked before use?
    - Collection safety: can any list/dict be empty? Is it checked before indexing?
    - Numeric safety: can any division divide by zero? Can any subtraction go negative where it shouldn't?
    - String safety: can any string operation fail on None or empty string?
  - DEFECT if: data can become None/empty/corrupted between steps without a guard; types are inconsistent across the pipeline.

  #### B.4 — DB SESSION & TRANSACTION LOGIC
  - For every function that touches the database:
    - Does it receive the session via dependency injection (get_db) or create its own?
    - Does it commit? If so, is there a rollback on exception?
    - Does it flush without commit (leaving a dangling transaction)?
    - Does it query using the correct model class and correct filters?
    - Does it handle the case where the query returns zero results?
    - Does it handle the case where the query returns multiple results when one is expected?
    - Are related objects loaded (joinedload/selectinload) or will accessing them cause lazy-load outside session?
  - DEFECT if: session is mismanaged; commit without rollback guard; query returns unhandled None/empty; lazy-load outside session context.

  #### B.5 — BUSINESS LOGIC CORRECTNESS
  - For each function, determine its BUSINESS PURPOSE from its name, docstring, parameters, and callers.
  - Then verify the implementation matches that purpose:
    - Does a "create" function actually create AND return the created object?
    - Does a "get" function handle the not-found case (return None? raise 404?)?
    - Does a "list" function apply correct filtering, pagination, and ordering?
    - Does an "update" function verify the object exists before mutating?
    - Does a "delete" function verify existence and handle cascading constraints?
    - Does a "calculate/compute" function handle edge cases (zero, negative, overflow)?
    - Does a "validate" function actually reject invalid input (not just pass everything)?
    - Does a "send/notify" function handle the failure case (recipient not found, service down)?
  - DEFECT if: the implementation contradicts the implied business contract; edge cases are unhandled; validation is bypassed.

  #### B.6 — CROSS-FUNCTION CONTRACT VERIFICATION
  - For every function that CALLS another function:
    - Does the call-site pass the correct number and type of arguments?
    - Does the call-site handle the return value correctly? (expects a list but gets a dict? expects an object but gets None?)
    - Does the call-site handle exceptions that the callee may raise?
  - For every function that IS CALLED:
    - Do ALL callers use it consistently? (one caller passes a string, another passes an int?)
    - Is the return value used correctly by all callers?
  - For every event emission (events.py):
    - Does the event payload match what subscribers expect?
    - Are all required fields present in the emitted event?
  - For every port consumption (ports.py):
    - Does the calling domain pass the correct parameters?
    - Does it handle the case where the port returns None/empty?
  - DEFECT if: any caller/callee mismatch; any event payload mismatch; any port contract violation.

  #### B.7 — SCHEMA & SERIALIZATION LOGIC
  - For every Pydantic schema in schemas/:
    - Does every field have the correct type annotation?
    - Are Optional fields actually optional in the corresponding ORM model?
    - Are required fields actually always populated by the service that builds the response?
    - Do validators actually validate (not just pass)?
    - Do `from_orm()` / `model_validate()` calls match the ORM model's attribute names?
  - For every serializer/transform function:
    - Does it handle None inputs gracefully?
    - Does it handle empty collections?
    - Does the output shape match what the router returns to the client?
  - DEFECT if: schema fields don't match ORM columns; required fields can be None; validators are no-ops; serialization crashes on edge cases.

  #### B.8 — EVENT FLOW & ASYNC INTEGRITY
  - For every event defined in events.py:
    - Is there a corresponding handler in subscribers.py?
    - Does the handler's signature match the event's payload?
    - Does the handler handle failures (retry, dead-letter, log)?
  - For every async function:
    - Are all awaited calls actually awaitable?
    - Are there blocking calls inside async functions (time.sleep, requests.get, synchronous DB)?
    - Is there proper error handling in async context (try/except around await)?
  - DEFECT if: event has no handler; handler signature mismatches event; blocking call inside async; missing await.

  #### B.9 — CONFIGURATION & ENVIRONMENT DEPENDENCY
  - For every config value accessed (settings.X, os.environ, config.Y):
    - Does that key exist in the config/env model?
    - Is there a default value if the env var is missing?
    - Is the type correct (string vs int vs bool)?
  - For every provider/external service call:
    - Is the API key/URL sourced from config (not hardcoded)?
    - Is there a timeout set?
    - Is there a retry/fallback for transient failures?
  - DEFECT if: config key is undefined; type mismatch; hardcoded secrets; no timeout on external calls.

  #### B.10 — DEAD CODE & LOGICAL ORPHANS
  - Functions defined but never called from anywhere in the Target or its consumers?
  - Imports that are unused?
  - Variables assigned but never read?
  - Conditional branches that can never be true (dead if-blocks)?
  - Event types defined but never emitted?
  - Feature atoms in features.py that are never gated by any router?
  - DEFECT if: dead code exists (flag for removal or wiring); orphaned logic that serves no purpose.

  ### PHASE C — Structural & Data-Table Violation Checks
  (Formerly PHASE B — now runs AFTER logic diagnostics so that both structural AND logical defects are captured before repair begins)

  A. STRUCTURE
    - Empty file? Defect. Hollow file? Defect. (Never keep, never create.)
    - Required file missing (events.py / subscribers.py / features.py / ports.py)? Defect.
    - Folder not in the canonical layout? Defect (fabricated structure).
    - Required folder empty? Defect — populate correctly or remove (decide by the diagram).
    - Too many flat service files (>8)? Must be sliced into sub-capability folders.
    - Duplicated/similar files not yet merged? Defect (flag for merge).

  B. PLACEMENT
    - File in wrong layer? (e.g. ORM model in services/, router logic in a service, schema in models/, business logic in schemas/)
    - File belongs to ANOTHER domain? → relocate per placement contract.

  C. CODE LAW CHECKS
    - Models: `__table_args__ = {"schema": "<domain>"}` present? Naming lint?
    - Services: import only domains/<self> + infrastructure + kernel (+ providers via services)? Any upward import (modules/rbac) or cross-domain import not via ports/events?
    - events.py/subscribers.py: typed events with id + serialization?
    - features.py: atoms defined here and registered in rbac/catalog.py?
    - Wiring: does at least one module router under modules/*/routers/ actually call these services with require_feature(...) gating? If not, it is unwired.

  D. DATA-TABLE INTEGRITY & WIRING (check AND compare)
    - Every ORM model has a matching Alembic migration. Any ORM-only table with no migration = drift. Defect.
    - Every migration-created table has a matching ORM model. Orphan migration = Defect.
    - `__tablename__` matches the migration table name exactly.
    - Primary key present; uuid, created_at/updated_at, is_deleted, version, and (where applicable) country_code present per the mandatory column set.
    - Every ForeignKey: target table EXISTS, target schema is a domain schema (NOT core/platform/identity), and the FK column has an index.
    - Naming lint: snake_case, plural table names, `<thing>_id` FKs.
    - Single Alembic head (no fractured migration graph).
    - No OFFSET pagination on hot tables (must be keyset/cursor).

  E. PERFORMANCE & PRODUCTION READINESS
    - Performance: no blocking call inside async; no DB query inside a loop (N+1); pagination on list endpoints; timeouts on external calls; no unbounded `.all()`.
    - Production hygiene: no `print()` in app code (structured logging with request_id); no hardcoded secrets (env/config only); no bare/swallowed exceptions; no leftover TODO/FIXME on critical paths.
    - Production wiring: env validated at startup (pydantic BaseSettings); graceful shutdown handler (SIGTERM); health endpoints (/health, /health/deps, /health/ready); rate limiting and security headers present; RLS enforcer single and canonical.

  ### PHASE D — Repair (one root-cause at a time, safest first)
  Order: broken imports → broken names/references → broken logic paths → broken function contracts → hollow/empty consolidation & merges → placement → schema/data-table fixes → circuit/features → wiring → performance.

    - BROKEN IMPORTS & NAMES: Fix every unresolved import, every missing name, every broken reference. The fix must make the name resolve correctly — either by adding the correct import, defining the missing symbol, or correcting the reference path.
    - BROKEN LOGIC PATHS: For every execution-path defect found in Phase B:
      - Add missing return statements.
      - Add None/empty guards before use.
      - Add proper exception handling (catch specific, log, re-raise or return controlled error).
      - Remove unreachable code.
      - Fix incorrect conditionals.
      - Add missing type conversions.
    - BROKEN FUNCTION CONTRACTS: For every function whose implementation contradicts its business purpose:
      - Implement the missing logic (infer correct behavior from: the function name, its parameters, its callers' expectations, its docstring, and the domain's business rules as implied by the diagram and sibling functions).
      - Add missing validation.
      - Add missing existence checks before mutation.
      - Add missing error handling for the not-found / conflict / constraint-violation cases.
      - Ensure the return value matches what all callers expect.
    - BROKEN DATA FLOWS: For every data-flow defect:
      - Add type guards / None checks at the point where data can become invalid.
      - Fix type mismatches between pipeline steps.
      - Add collection-empty guards before indexing.
      - Add division-by-zero guards.
    - BROKEN DB LOGIC: For every session/transaction defect:
      - Ensure get_db dependency injection is used.
      - Add rollback in except blocks.
      - Add existence checks before mutation.
      - Add eager loading (joinedload/selectinload) where lazy-load would fail.
      - Handle zero-result and multi-result cases.
    - BROKEN CROSS-FUNCTION CONTRACTS: For every caller/callee mismatch:
      - Fix the call-site to pass correct arguments.
      - Fix the callee to handle all caller patterns.
      - Ensure event payloads match handler expectations.
      - Ensure port call signatures match port definitions.
    - BROKEN SCHEMAS: For every schema defect:
      - Fix type annotations to match ORM columns.
      - Add missing validators.
      - Fix from_orm / model_validate calls.
      - Ensure Optional matches ORM nullability.
    - MERGE SIMILAR FILES: For each merge group, keep ONE canonical owner, fold all unique logic into it, re-point every importer to the canonical file, then remove the redundant file ONLY after grep proves zero remaining references. NEVER lose logic.
    - EMPTY files: If referenced, merge real content in or relocate the reference; if truly dead AND unreferenced, remove ONLY after grep confirms zero usage.
    - HOLLOW files: Implement the real logic OR merge into the canonical owner.
    - Consolidate scattered service files into coherent sub-capability slices — merge duplicates, keep all logic.
    - DATA-TABLE FIXES: Add missing `__table_args__` schema; create missing migrations for ORM-only tables; fix FK targets/indexes; enforce naming lint; merge Alembic heads to one; replace OFFSET with keyset pagination on hot tables.
    - PERFORMANCE FIXES: Convert blocking calls, batch N+1 loops, add pagination/timeouts.
    - Fabricated/empty folders: Populate correctly per diagram, or remove if not required and unreferenced.
    - Fix imports, cross-domain boundaries, and feature atoms.
    - After EVERY change: verify imports resolve (`python -c "import <module>"`) and the app still boots. Never leave the tree broken between changes.

  ### PHASE E — Verification (MANDATORY — no claim without evidence)
  1. App boots: `python backend/main.py` (or test client) with zero import errors.
  2. Every public function is reachable and exercised: write/run tests under `D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests` covering each public path — including EDGE CASES (None input, empty list, zero results, duplicate, concurrent access).
  3. Re-run the architecture audit: Target must show ZERO RED and ZERO relevant YEL.
  4. LOGIC VERIFICATION: For every function that was diagnosed with a logic defect in Phase B, confirm the fix by:
    - Tracing the corrected execution path manually (read the fixed code, verify all paths are safe).
    - Running the function with edge-case inputs (None, empty, boundary values).
    - Confirming the return value matches the expected contract.
  5. DATA-TABLE reconciliation: Confirm every ORM model ↔ migration pair matches, every FK resolves to a real domain-schema table, and there is exactly one Alembic head.
  6. FILE-DIFF CLEANUP: Compare the file set before vs after. Every created file must be justified by the diagram; delete ALL temp/scratch/extra artifacts. Confirm no empty files, no hollow files, and the file count is sane, merged, and sliced.
  7. PRODUCTION SIGN-OFF checklist (all must pass): env validated; no print(); structured logging; no secrets in code; error handling + rollback on writes; pagination + no OFFSET on hot tables; timeouts on external calls; rate limiting + security headers; graceful shutdown; health endpoints; single canonical RLS enforcer.
  8. Update `RESOLVER.md`: mark rows RESOLVED with evidence (test output, audit result, logic-trace confirmation).
  9. If ANY problem remains → return to PHASE A. Repeat until fully clean, fully wired, fully repaired, logically correct, and production-ready.

  ## Anti-Drift Guardrails (absolute):
  - NEVER create an empty, placeholder, or stub file. Every file must contain real, working, production-grade code.
  - NEVER create any EXTRA file. If a temporary file is unavoidable, create it ONLY under `D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files` and DELETE it immediately after use. Leave no new file that is not required by the final architecture.
  - NEVER invent a folder/file not sanctioned by ARCHITECTURE_DIAGRAM.md — cite the rule first.
  - NEVER delete logic. Improve, merge, rearrange. Delete only genuinely-dead, unreferenced files, and only after grep proves zero usage.
  - NEVER lose logic during a merge — the canonical owner must retain every unique behavior from all merged files.
  - NEVER mark anything RESOLVED without running the code AND verifying the logic.
  - NEVER leave a loophole, shortcut, or half-fix. Every repair must be production-safe.
  - NEVER stop while any RED violation, empty file, broken function, logic error, data-table mismatch, or failing test remains.
  - NEVER assume a function works because it "looks correct" — TRACE it, verify every path, test edge cases.
  - NEVER skip Phase B diagnostics. Structural compliance without logical correctness is NOT production-ready.
  - Work in small, verifiable increments; keep the tree importable after each change.

  ## Restriction:
  - NEVER modify files inside `scripts/` (audit scripts read-only).
  - Never touch `git add -A && git commit -m`, `git pull`, or any git write command.
  - No hardcoded values; all config from environment / config.py.
  - Use `D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files` for temporary files ONLY, and remove each one immediately after use.
  - Use `D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests` for test files.
  - Never delete a file that still contains reachable logic; merging is allowed and preferred for similar/duplicated files.
  - Do NOT ask for user input at any point. Diagnose, decide, fix, verify — autonomously.
  - Do NOT rely on git history, external documentation, or prior conversation context. The code + ARCHITECTURE_DIAGRAM.md are the ONLY sources of truth.
