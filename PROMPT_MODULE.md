
## Production Standard (non-negotiable):
- We are at GO-TO-PRODUCTION level. Every fix must be PROFESSIONAL, ACCURATE,
  and COMPLETE. There is ZERO tolerance for drifting, loopholes, stubs,
  shortcuts, leftover TODOs, or any mistake that would fail in production.
- Every change must leave the code SMOOTHER, FASTER, and PROPERLY WIRED than
  before — never slower, never loosely connected, never half-working.
- You work INDEPENDENTLY. Do NOT ask for clarification, do NOT wait for input,
  do NOT assume external context. Read the code, read the diagram, diagnose,
  decide, fix, verify. You are the sole authority on what is broken and how to
  fix it.
- Do NOT create any EXTRA file. If a temporary file is unavoidable, create it
  ONLY under `D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files` and DELETE
  it immediately after use. Leave no new file that is not required by the final
  architecture.

## Objective:
- Bring the Target MODULE into 100% compliance with
  `D:\Projects\10- E-COMMERCE WEBSITE\zozi\ARCHITECTURE_DIAGRAM.md`
  (three axes + seven laws) AND make every router, every auth flow, and every
  serializer in it fully workable, logically correct, and production-ready
  end-to-end.
- DIAGNOSE every function in auth/, every router endpoint, and every serializer
  for LOGICAL ERRORS, broken execution paths, silent failures, incorrect
  transformations, missing error handling, and security vulnerabilities — not
  just structural placement.
- MERGE files whose content is similar/duplicated to eliminate excess and
  produce one clean canonical owner per responsibility — while preserving ALL
  logic.
- INTELLIGENTLY RE-ARRANGE all code so it runs smoothly, faster, and is
  properly wired; REPAIR every broken function AND every broken logic path;
  and complete the Target from ALL production perspectives.
- Run a CONTINUOUS loop: diagnose → fix → re-diagnose → fix → … until ZERO
  violations remain, ZERO logic errors remain, every file contains real
  substance, every function executes correctly, every route is reachable and
  gated, and the code runs cleanly. Do NOT stop after one pass.
- Do this WITHOUT drifting: never invent structure, never create empty/hollow
  files, never create extra files, never claim completion without evidence.

## Target:
- You are responsible to audit, diagnose, and repair everything inside
  `/backend/modules/logistics`, including its wiring into `domains/*/services/`,
  `rbac/dependencies.py`, `infrastructure/security/`, `middleware/`, and
  `main.py`.
  (Swap this line for any module actor: customer / supplier / logistics /
  admin / employee.)

## Ground Truth:
- The ONLY structural authority is
  `D:\Projects\10- E-COMMERCE WEBSITE\zozi\ARCHITECTURE_DIAGRAM.md`.
  Before creating, moving, merging, or deleting ANYTHING, open it and cite the
  exact section/line that justifies the change.
- Canonical MODULE layout (diagram §3, AXIS 1) — NOTHING else is allowed
  inside a module folder:
    auth/          # per-actor login/OTP/social → that actor's own tables;
                   #   sessions; device binding; JWT jti blacklist integration
    routers/       # THIN per-actor routers (auth + require_feature + ONE
                   #   service call); __init__.py lists routers/public_routers
                   #   for main.py
    serializers/   # per-actor view models (response shaping, field filtering,
                   #   nested expansion)
- Valid module actors (EXACTLY these 5): customer, supplier, logistics, admin,
  employee.
- The Seven Laws as they apply to a MODULE:
  (1) Arrows down only: modules → domains, rbac. Modules NEVER import other
      modules, providers, kernel, or jobs directly. Only modules/{actor}/auth
      may import infrastructure/security primitives (JWT, hashing, Redis
      session).
  (2) Routers stay THIN: auth context + require_feature(...) + ONE
      domain-service call. No DB writes, no business rules. Business logic
      belongs in domains/*/services/.
  (3) Cross-domain access: routers call ONE domain service; that service
      handles cross-domain reads/writes via ports/events. Routers NEVER import
      another domain's models/services directly.
  (4) Feature axis: gate every route with
      rbac.dependencies.require_feature(...). NEVER the old per-module helpers
      (require_admin / require_finance_permission / ...). Modules CONSUME
      features — they do NOT define features.py.
  (5) Country scope: RLS context is set by middleware, not by module code.
      Module routers do NOT set app.current_country_code.
  (6) Modules do NOT own ORM tables. The actor's user table lives in its own
      domain schema (e.g. customer.user, admin.user). Do not add models/ or
      __table_args__ inside a module.
  (7) DOMAIN_ALLOWLIST.yaml: modules do not add cross-domain imports. If a
      router needs data from another domain, it calls its OWN domain's service
      which uses ports.

## Process — LOOP until clean:

### PHASE A — Deep Inventory (re-run every iteration)
1. Walk the Target recursively. For EVERY file record: path, line count,
   non-comment code lines, imports, defined functions/classes, and whether it
   is EMPTY (<5 lines of real code) or HOLLOW (declares functions/classes with
   no body / `pass`).
2. Map every file's purpose: is it auth, a router, or a serializer? Anything
   else is misplaced.
3. SIMILARITY DETECTION (for merging): group files that are candidates for
   merge. Two files are "similar" when ANY of these hold:
   - Same sub-folder (auth/ or routers/ or serializers/) AND ≥60% overlap in
     function/class name tokens.
   - They implement the same endpoint or auth flow under different names.
   - One is a near-duplicate or older revision of the other.
   Record each merge group in RESOLVER.md with the chosen canonical owner.
4. ROUTE INVENTORY: list every route registered by this module (method, path,
   gate, service call). Cross-reference with the diagram's frontend route tree
   for this actor to find missing endpoints.
5. AUTH FLOW INVENTORY: list every auth function (login, OTP, social, refresh,
   logout, device binding) and trace its dependencies (JWT, Redis, DB session,
   infrastructure/security).
6. Write the full inventory + violations into `RESOLVER.md` as a table
   (one row per problem: ID, File, Problem, Diagram rule, Action).

### PHASE B — DEEP LOGIC DIAGNOSTICS (the critical missing layer)
For EVERY function in EVERY file under the Target, perform the following
diagnostic trace. Log every defect found.

#### B.1 — EXECUTION PATH TRACE
- Read each function top-to-bottom. For EVERY code path (if/else, try/except,
  loops, early returns):
  - Does every path produce a valid return value (or explicitly raise)?
  - Are there paths that fall through without returning (implicit `None`
    return)?
  - Are there unreachable code blocks after an unconditional return/raise?
  - Does every `try` block have a meaningful `except` that either handles or
    re-raises?
  - Are there `except` blocks that catch too broadly and hide the real error?
- DEFECT if: any path silently returns None where a value is expected; any
  exception is swallowed without logging; any code is unreachable.

#### B.2 — NAME RESOLUTION & IMPORT CHAIN
- For every name used inside a function body, verify it resolves:
  - Is it imported at the top of the file? (missing import = BROKEN)
  - Is it defined earlier in the same file? (forward reference = BROKEN)
  - Is it a parameter? (missing parameter in signature vs call-site mismatch =
    BROKEN)
  - Is it a class attribute? (accessing attribute that doesn't exist = BROKEN)
- For every import statement: does the imported module/symbol actually exist
  at that path?
- DEFECT if: any name is unresolved, any import points to a non-existent path,
  any call-site passes wrong argument count/types.

#### B.3 — AUTH FLOW CORRECTNESS (auth/ specific)
- For each auth function (login, register, OTP verify, social login, refresh,
  logout, device binding):
  - Does it correctly validate credentials before issuing a token?
  - Does it correctly generate JWT with jti claim for blacklist support?
  - Does it correctly store/verify refresh tokens in Redis?
  - Does logout correctly blacklist the jti in Redis?
  - Does device binding correctly generate and store device fingerprints?
  - Does OTP flow correctly generate, store (with TTL), and verify codes?
  - Does social login correctly exchange the provider token for a local
    session?
  - Are all error cases handled (wrong password, expired token, invalid OTP,
    unknown user, rate-limited)?
  - Are error responses controlled (no stack traces leaked to client)?
- DEFECT if: any auth flow has a security gap, missing validation, or
  unhandled error case.

#### B.4 — THIN-ROUTER CONTRACT (Law 2) — the core module check
- For every router endpoint function:
  - Does it contain ONLY: auth dependency + require_feature gate + ONE domain
    service call?
  - Does it contain ANY business logic (calculations, conditionals on domain
    data, loops over domain objects)? → DEFECT (NS41)
  - Does it call session.add/commit/delete/merge/flush (W1) or read via
    session.query/execute (Q1)? → DEFECT (must move to domains/*/services/)
  - Does it import providers/ directly? → DEFECT (NS35)
  - Does it import kernel/ or infrastructure/ directly (outside auth/)? →
    DEFECT (delegate to domain service)
  - Does it call MORE THAN ONE domain service? → DEFECT (NS41)
  - Does it import another module's auth or routers? → DEFECT (Law 1)
- DEFECT if: any router violates the thin contract.

#### B.5 — FEATURE GATING CORRECTNESS (Law 4)
- For every route in this module:
  - Is it gated with rbac.dependencies.require_feature(...)? (NS33)
  - Is the feature atom string correct and registered in some
    domains/*/features.py? (NS15)
  - Any leftover pre-ARCHITECTURE_DIAGRAM gate (require_admin /
    require_*_permission / Depends(require_...) / hasAdminPermission)? →
    DEFECT (replace with require_feature)
  - Public/webhook routers: are they correctly EXEMPT from gating?
- DEFECT if: any route is ungated, wrongly gated, or uses an abolished gate.

#### B.6 — SERIALIZER CORRECTNESS (serializers/ specific)
- For each serializer class/function:
  - Does it correctly shape the response from the domain service output?
  - Does it handle None inputs gracefully?
  - Does it handle empty collections?
  - Does the output shape match what the frontend expects for this actor?
  - Are nested objects correctly expanded (not just IDs)?
  - Are sensitive fields (password, token, jti) excluded from responses?
  - Are date/time fields correctly formatted?
  - Are money fields using Decimal (never float)?
- DEFECT if: serializer crashes on edge cases, leaks sensitive data, or
  produces wrong shape.

#### B.7 — DATA FLOW & TRANSFORMATION INTEGRITY
- Trace every piece of data from INPUT to OUTPUT through each function:
  - Input: What does the function receive? (request body, query params, path
    params, auth context)
  - Transformation: What operations are performed? (validation, extraction,
    delegation)
  - Output: What does it return? (JSON response, redirect, error)
- At each step verify:
  - Type consistency: does the output type match the expected input type of
    the next step?
  - Null/None safety: can any intermediate value be None? Is it checked?
  - Request validation: are Pydantic models used for request body validation?
- DEFECT if: data can become None/empty/corrupted between steps without a
  guard.

#### B.8 — CROSS-MODULE ISOLATION (Law 1)
- Does this module import ANY other module's code (auth, routers,
  serializers)? → DEFECT
- Does this module import providers/ directly? → DEFECT (NS35)
- Does this module import kernel/ directly (outside auth/)? → DEFECT
- Does this module import jobs/ or middleware/? → DEFECT
- Does this module's auth/ import infrastructure/security correctly (JWT,
  hashing, Redis)? → ALLOWED
- DEFECT if: any forbidden cross-module or upward import exists.

#### B.9 — WIRING & REGISTRATION
- Does modules/{actor}/routers/__init__.py correctly list ALL routers and
  public_routers for main.py?
- Are routers registered in main.py under this actor's correct route prefix
  (e.g. /admin/*, /customer/*, /supplier/*, /logistics/*, /employee/*)?
- Do the domain services these routers call actually exist and import cleanly?
- Are there orphaned router files not registered anywhere?
- Are there routes defined but unreachable (wrong prefix, missing include)?
- DEFECT if: any router is unwired, mis-registered, or calls a non-existent
  service.

#### B.10 — CONFIGURATION & ENVIRONMENT DEPENDENCY
- For every config value accessed (settings.X, os.environ, config.Y):
  - Does that key exist in the config/env model?
  - Is there a default value if the env var is missing?
  - Is the type correct (string vs int vs bool)?
- For auth/ specifically:
  - Is SECRET_KEY sourced from config (not hardcoded)?
  - Is JWT expiry configurable?
  - Is Redis URL for session/token blacklist configurable?
- DEFECT if: config key is undefined; type mismatch; hardcoded secrets.

### PHASE C — Structural & Code-Law Violation Checks
(Formerly PHASE B — now runs AFTER logic diagnostics so that both structural
AND logical defects are captured before repair begins)

A. STRUCTURE
   - Empty file? Defect. Hollow file? Defect. (Never keep, never create.)
   - Folder not one of {auth/, routers/, serializers/}? Defect (fabricated
     structure — e.g. services/, models/, schemas/, policies/, events.py,
     subscribers.py, features.py, ports.py, read_models/ inside a module are
     ALL violations).
   - Actor folder name not one of the 5 valid actors? Defect (NS19).
   - Missing one of auth/ routers/ serializers/? Defect (NS40).
   - Duplicated/similar files not yet merged? Defect (flag for merge).

B. ROUTER NAMING (diagram §3, Axis 1)
   - Router file must match pattern:
     modules/{module}/routers/{domain}[_{operation}]_router.py (RN1)
   - Router file must NOT be nested deeper than routers/ (RN2)
   - Router file must NOT be under abolished backend/routers/ (RN4)

C. API SHAPE
   - Route prefix aligns with surface/actor (AS1)
   - OpenAPI tags align with domain (AS2)
   - Endpoint naming is descriptive, not generic (AS3)

D. FLOW-TYPE COMPLIANCE
   - Operations in this module match the expected flow type for this
     actor × domain (FT1/FT2)
   - No oversight operations in non-admin surfaces (CA3)

### PHASE D — Repair (one root-cause at a time, safest first)
Order: broken imports → broken names/references → broken auth flows →
       broken router logic → hollow/empty consolidation & merges →
       misplaced-file relocation → thin-router extraction → feature gating →
       serializer fixes → wiring.

   - BROKEN IMPORTS & NAMES: Fix every unresolved import, every missing name,
     every broken reference. The fix must make the name resolve correctly.
   - BROKEN AUTH FLOWS: For every auth defect found in Phase B.3:
     - Fix missing validation (credentials, OTP, token expiry).
     - Fix missing jti in JWT generation.
     - Fix missing Redis blacklist on logout.
     - Fix missing device binding storage.
     - Add proper error handling for all failure cases.
     - Ensure no stack traces leak to client.
   - BROKEN ROUTER LOGIC: For every thin-router violation:
     - Extract business logic/DB access OUT of routers into
       domains/<domain>/services/.
     - Leave the router with ONLY: auth dep + require_feature + ONE service
       call.
     - NEVER create services/models/schemas inside the module.
   - MERGE SIMILAR FILES: For each merge group, keep ONE canonical owner,
     fold all unique logic into it, re-point every importer to the canonical
     file, then remove the redundant file ONLY after grep proves zero
     remaining references. NEVER lose logic.
   - EMPTY files: If referenced, merge real content in or relocate the
     reference; if truly dead AND unreferenced, remove ONLY after grep
     confirms zero usage.
   - HOLLOW files: Implement the real logic (recover intent from callers,
     similar files, and the diagram) OR merge into the canonical owner.
   - FEATURE GATING: Replace old auth gates with require_feature(...);
     verify each atom is registered in domains/*/features.py.
   - SERIALIZER FIXES: Fix None handling, sensitive field exclusion, correct
     response shape, Decimal for money.
   - WIRING: Fix __init__.py router lists, main.py registration, missing
     service imports.
   - After EVERY change: verify imports resolve (`python -c "import <module>"`)
     and the app still boots. Never leave the tree broken between changes.

### PHASE E — Verification (MANDATORY — no claim without evidence)
1. App boots: `python backend/main.py` (or test client) with zero import
   errors.
2. Every router endpoint is reachable: auth resolves, require_feature passes,
   and the single domain-service call succeeds. Write/run tests under
   `D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests` covering each endpoint.
3. Every auth flow works end-to-end: login → token → protected route →
   refresh → logout → blacklisted. Write/run tests for each flow.
4. Every serializer produces correct output for valid, empty, and None inputs.
5. Re-run the architecture audit: Target must show ZERO RED and ZERO relevant
   YEL (NS19/NS33/NS35/NS40/NS41/W1/Q1/R1/CA3/FT1/FT2/AS1/AS2/AS3/RN1/RN2/RN4
   all clear).
6. Confirm counts: no empty files, no hollow files, no fabricated folders,
   router count sane, all routers registered.
7. FILE-DIFF CLEANUP: compare the file set before vs after. Every created
   file must be justified by the diagram; delete ALL temp/scratch/extra
   artifacts.
8. Update `RESOLVER.md`: mark rows RESOLVED with evidence (test output, audit
   result).
9. If ANY problem remains → return to PHASE A. Repeat until fully clean,
   fully wired, fully repaired, and production-ready.

## Anti-Drift Guardrails (absolute):
- NEVER create an empty or placeholder file. Every file must contain real,
  working, production-grade code.
- NEVER create any EXTRA file. If a temporary file is unavoidable, create it
  ONLY under `D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files` and
  DELETE it immediately after use.
- NEVER create services/, models/, schemas/, policies/, events.py,
  subscribers.py, features.py, ports.py, or read_models/ inside a module —
  those belong to domains/, not modules/.
- NEVER put DB writes/reads or business rules in a router (Law 2). Delegate
  to domains/*/services/.
- NEVER gate a route with the old per-module auth helpers — use
  require_feature only.
- NEVER import providers/, kernel/ (outside auth/), jobs/, middleware/, or
  another module's code from within this module.
- NEVER set RLS context (app.current_country_code) in module code — that is
  middleware's job.
- NEVER delete logic. Improve, merge, rearrange. Delete only genuinely-dead,
  unreferenced files, and only after grep proves zero usage.
- NEVER lose logic during a merge — the canonical owner must retain every
  unique behavior from all merged files.
- NEVER mark anything RESOLVED without running the code and the audit.
- NEVER stop while any RED violation, empty file, broken function, failing
  test, or ungated route remains.
- NEVER assume a function works because it "looks correct" — TRACE it,
  verify every path, test edge cases.
- Work in small, verifiable increments; keep the tree importable after each
  change.

## Restriction:
- NEVER modify files inside `scripts/` (audit scripts read-only).
- Never touch `git add -A && git commit -m`, `git pull`, or any git write
  command.
- No hardcoded values; all config from environment / config.py.
- Use `D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files` for temporary
  files ONLY, and remove each one immediately after use.
- Use `D:\Projects\10- E-COMMERCE WEBSITE\zozi\tests` for test files.
- Never delete a file that still contains reachable logic; merging is allowed.
- Do NOT ask for user input at any point. Diagnose, decide, fix, verify —
  autonomously.
- Do NOT rely on git history, external documentation, or prior conversation
  context. The code + ARCHITECTURE_DIAGRAM.md are the ONLY sources of truth.
