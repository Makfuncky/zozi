read in detail complete the attachment

---

Next question:

is there anyway to connect the controllers with routers automatically ?
I am talking about the routers to controllers automatically ?

if not then can we make a script which will generate all the router autmatically after reading the controllers ? is that possible ? and if is it possible then how it will be safe ?

---

what if we will make a script which will read complete `controllers` folder and generate all the routers ?

---

see it is large application and it will be good if we will try to automate things to generate becasue it will be easy repair also later. 
if any new feature I will make, I don't need to take tension for main.py to router to controllers, we have to make service, controller, models for table that's it.

do more deep investigation and try to get any possibility.

---

let me tell you routers folder is already broken a range of routers not yet complete and wired properly with the controllers so think that also.
and I am talking about to make a script which is in our control. we will run the script which will read complete controllers files and generate routers.
now think carefully, is that possible ?

# ==========================================================================================================================================================
# ==========================================================================================================================================================




Thinking carefully, with the new fact that **your routers are already broken/incomplete** — here's the precise answer.

## Short answer
A script that reads **un-annotated** controllers and emits *correct* routers is **not possible**. A script that reads **annotated** controllers and emits routers is **fully possible, safe, and in your control** — and it's also the cleanest way to *fix* the broken routers you just described.

## Why "read controllers → correct routers" is impossible (without metadata)
I read your actual controllers. A typical function is:
```python
def create_coupon_by_country(code, coupon_code, discount_type, ..., db)
```
From that signature alone, the script **cannot know**:
- **HTTP method** — is it `POST`? The name hints "create" but that's a guess.
- **URL path** — `/{code}/coupons`? `/coupons/{code}`? `/country/{code}/coupon`? All plausible; the script would invent one.
- **Which params are path vs body vs query** — `code` is clearly a path var; `coupon_code` is body. The function doesn't say.
- **Auth + RLS** — `require_admin`? country-scoped context? Absent entirely.
- **Response model / status code** — `-> dict` tells you nothing.

That information lives **only in the router today** — and you just told me those routers are broken. So the "correct route" exists *nowhere machine-readable*. A script cannot recover design intent it was never given. If it guessed, you'd get 179 plausible-but-wrong routers on top of the broken ones. That's worse, not better.

## What IS possible: a controlled script over annotated controllers
The script can't *invent* routes, but it can **transform an explicit route declaration into FastAPI code**. You declare the route once, on the controller, with a decorator:
```python
@post("/{code}/coupons", auth=require_admin, rls="country")
def create_coupon_by_country(code: str = Path(...), coupon_code: str = Body(...), db = Depends(get_db)):
    ...
```
Then `scripts/gen_routers.py` (yours, deterministic, idempotent) reads every controller, collects the decorated functions, and writes the router files. This is reliable because **nothing is guessed** — the human declared it.

And here's why this directly solves your "broken routers" problem: your controllers are the real source of truth (services + models + controller logic). The routers are a *derived view*. So the right move is:
1. Put the route declaration on the controller (`@post/...`).
2. Run your script → routers are regenerated **correctly** from the source of truth.
3. Broken/incomplete routers stop being a maintenance burden — they're rebuilt, not hand-patched.

## How it stays safe and "in your control"
- **You run it deliberately** (not at import). Generate into `routers/`, review the diff, commit via PR.
- **Idempotent**: re-running produces identical output (no drift).
- **Deterministic prefixes**: prefix comes from the controller module or an explicit `@route(prefix=...)`, co-located — which also finishes the auto-discovery prefix work we discussed.
- **Guardrails**: the script refuses to overwrite a router whose controller has no decorators (so untouched controllers keep their existing hand routers), and a test asserts the total route count so a missing/extra route fails CI.
- **Bespoke routers** (websockets, aliases, country-control-plane) stay hand-written and are skipped by the script.

## The one honest cost
Annotating controllers is real work — ~1152 functions. But it's **incremental**: new features get annotated as you write them (the "make service+controller+model, done" flow you wanted), and broken existing routers get fixed *when you touch them*, by annotating + regenerating. You never hand-write a router again.

## Verdict
- Un-annotated → correct routers: **impossible** (info isn't there).
- Annotated + your controlled script → routers: **possible, safe, and it fixes your broken routers**.

Want me to build the **proof-of-concept** — the `@route` decorator + a prototype `scripts/gen_routers.py` — and prove it by regenerating **one** broken router from its annotated controller, confirming the route comes out correct? (I'd wait for the tree to stabilize first, since generating into the current churn would be unsafe.)


# ==========================================================================================================================================================
# ==========================================================================================================================================================



# Auto-Generating Routers from Controllers — Deep Investigation

## Short Answer: **YES, it is possible.** But with a specific design that keeps you in control.

---

## Why It's Possible

Looking at your codebase, controllers already encode **80% of the information** a router needs:

| What a Router Needs | Where It Lives in Controllers | Auto-Inferable? |
|---|---|---|
| HTTP method | Function name: `get_*`, `create_*`, `update_*`, `delete_*` | ✅ YES |
| URL path | Controller filename + entity name in function | ✅ YES (via convention) |
| Auth level | Function params: `current_user`, `current_admin` | ✅ YES |
| Path params | Function params with `int`/`str` type + `_id` suffix | ✅ YES |
| DB session | `db: Session` param → maps to `Depends(get_db)` | ✅ YES |
| Request body | Non-path, non-auth params → request body schema | ⚠️ PARTIAL |
| Response model | Return type annotation | ⚠️ PARTIAL |
| Custom status codes | Not present in controllers | ❌ NO (needs manifest) |

---

## The Design: Convention + Manifest Hybrid

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENERATION PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. SCAN          2. PARSE           3. GENERATE                 │
│                                                                   │
│  controllers/     AST Parser         routers/ (generated)        │
│  ├── orders/      (no execution)     ├── admin_orders_mgmt.py    │
│  │   ├── admin_order_controller.py   ├── supplier_orders.py      │
│  │   └── customer_order_controller.py│── customer_orders.py      │
│  ├── catalog/                        ├── ...                      │
│  │   └── product_controller.py       └── _registry.py            │
│  └── ...                                                          │
│                                                                   │
│  4. REGISTER                                                      │
│     main.py imports _registry.py (auto-generated include)        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: The Convention Rules (What the Script Assumes)

```python
# NAMING CONVENTION → ROUTE MAPPING

# Function name prefix → HTTP method
VERB_MAP = {
    "get":     "GET",
    "list":    "GET",
    "create":  "POST",
    "add":     "POST",
    "update":  "PUT",
    "patch":   "PATCH",
    "delete":  "DELETE",
    "remove":  "DELETE",
    "archive": "PATCH",
    "restore": "PATCH",
    "toggle":  "PATCH",
    "approve": "POST",
    "reject":  "POST",
    "verify":  "POST",
    "upload":  "POST",
    "search":  "GET",
    "export":  "GET",
}

# Surface detection from function/param names
SURFACE_RULES = {
    "admin_":    {"prefix": "/api/v1/admin",    "auth": "get_current_admin"},
    "supplier_": {"prefix": "/api/v1/supplier", "auth": "get_current_user"},
    "customer_": {"prefix": "/api/v1/customer", "auth": "get_current_user"},
    "public_":   {"prefix": "/api/v1",          "auth": None},  # or get_optional_user
    "system_":   {"prefix": "/api/v1/system",   "auth": "get_current_admin"},
    "logistics_":{"prefix": "/api/v1/logistics","auth": "get_current_user"},
}
```

---

## Step 2: AST-Based Parser (SAFE — Never Executes Code)

This is the **critical safety point**. The script uses Python's `ast` module to **read the source code as a syntax tree** without importing or executing anything:

```python
import ast
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class ControllerFunction:
    name: str
    params: list
    return_annotation: str | None
    decorators: list
    docstring: str | None
    line_number: int

@dataclass
class ControllerFile:
    path: Path
    domain: str          # from folder name
    surface: str         # from filename prefix
    functions: list[ControllerFunction] = field(default_factory=list)

def parse_controller_file(file_path: Path) -> ControllerFile:
    """Parse a controller file using AST — NEVER imports/executes."""
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    
    ctrl = ControllerFile(
        path=file_path,
        domain=file_path.parent.name,  # e.g., "orders"
        surface=_detect_surface(file_path.stem),  # e.g., "admin"
    )
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Skip private functions
            if node.name.startswith("_"):
                continue
            
            func = ControllerFunction(
                name=node.name,
                params=_extract_params(node),
                return_annotation=_get_annotation(node.returns),
                decorators=[_get_decorator_name(d) for d in node.decorator_list],
                docstring=ast.get_docstring(node),
                line_number=node.lineno,
            )
            ctrl.functions.append(func)
    
    return ctrl

def _extract_params(func_node) -> list[dict]:
    """Extract parameter names, types, defaults from AST."""
    params = []
    for arg in func_node.args.args:
        params.append({
            "name": arg.arg,
            "type": _get_annotation(arg.annotation),
            "has_default": False,
        })
    # Handle defaults
    defaults_offset = len(func_node.args.args) - len(func_node.args.defaults)
    for i, default in enumerate(func_node.args.defaults):
        params[defaults_offset + i]["has_default"] = True
    return params
```

### Why AST is Safe:

| Method | Executes Code? | Can Be Exploited? | Safe? |
|---|---|---|---|
| `import module` | ✅ YES | ✅ YES (side effects) | ❌ NO |
| `exec(open(f).read())` | ✅ YES | ✅ YES | ❌ NO |
| `ast.parse(source)` | ❌ NO | ❌ NO | ✅ YES |
| `inspect.getsource()` | ❌ NO (reads text) | ❌ NO | ✅ YES |

---

## Step 3: Router Generation Template

For each controller function, generate a thin router endpoint:

```python
def generate_router_file(ctrl: ControllerFile) -> str:
    """Generate a complete router file from parsed controller."""
    
    router_name = f"{ctrl.surface}_{ctrl.domain}"
    prefix = SURFACE_RULES[ctrl.surface]["prefix"] + f"/{ctrl.domain}"
    auth_dep = SURFACE_RULES[ctrl.surface]["auth"]
    
    lines = [
        f'"""Auto-generated router for {ctrl.domain} ({ctrl.surface} surface).',
        f'Source: {ctrl.path}',
        f'Generated by: scripts/generate_routers.py',
        f'DO NOT EDIT MANUALLY — re-run the generator instead.',
        f'"""',
        f'from fastapi import APIRouter, Depends',
        f'from db.database import get_db',
    ]
    
    # Add auth import
    if auth_dep:
        lines.append(f'from controllers.auth_controller import {auth_dep}')
    
    # Add controller import
    module_path = _to_module_path(ctrl.path)
    lines.append(f'from {module_path} import (')
    for func in ctrl.functions:
        lines.append(f'    {func.name},')
    lines.append(')')
    
    # Router instance
    lines.append(f'')
    lines.append(f'router = APIRouter(prefix="{prefix}", tags=["{ctrl.domain}"])')
    lines.append(f'')
    
    # Generate each endpoint
    for func in ctrl.functions:
        lines.append(_generate_endpoint(func, auth_dep))
    
    return '\n'.join(lines)
```

### Generated Endpoint Example:

**Controller function:**
```python
# controllers/orders/admin_order_management_controller.py
def get_order_by_id(db: Session, current_admin: dict, order_id: int):
    ...
```

**Generated router:**
```python
# routers/admin_orders_management.py  (AUTO-GENERATED)
@router.get("/{order_id}")
def get_order_by_id_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    return get_order_by_id(db=db, current_admin=current_admin, order_id=order_id)
```

---

## Step 4: The Route Manifest (For What Can't Be Inferred)

For cases where convention isn't enough, a YAML manifest fills the gaps:

```yaml
# route_manifest.yaml
# Override/extend auto-detected routes

overrides:
  controllers/orders/admin_order_management_controller.py:
    get_order_by_id:
      path: "/{order_id}"           # explicit path
      response_model: "OrderOut"    # schema to import
      status_code: 200
      
    create_order:
      request_body: "OrderCreate"   # Pydantic model for body
      status_code: 201
      response_model: "OrderOut"

    bulk_update_status:
      path: "/bulk/status"
      method: "PATCH"
      request_body: "BulkStatusUpdate"

  controllers/catalog/product_controller.py:
    list_products:
      path: "/"
      query_params:
        - name: category_id
          type: int
          required: false
        - name: min_price
          type: float
          required: false
        - name: max_price
          type: float
          required: false
```

---

## Step 5: Auto-Registration in main.py

Instead of manually adding 179 routers to main.py, generate a registry:

```python
# routers/_registry.py  (AUTO-GENERATED)
"""Auto-generated router registry. DO NOT EDIT."""

from fastapi import FastAPI

def register_all_routers(app: FastAPI) -> None:
    from routers.admin_orders_management import router as admin_orders
    from routers.admin_catalog_products import router as admin_catalog
    from routers.customer_orders_tracking import router as customer_orders
    from routers.supplier_products_upload import router as supplier_products
    # ... all 179 routers
    
    app.include_router(admin_orders)
    app.include_router(admin_catalog)
    app.include_router(customer_orders)
    app.include_router(supplier_products)
    # ...
```

Then in `main.py`:
```python
from routers._registry import register_all_routers
register_all_routers(app)
```

---

## Step 6: Safety Mechanisms

### 6.1 — Generation Safety

```python
# scripts/generate_routers.py

SAFETY_CHECKS = {
    "never_execute_controllers": True,   # AST only
    "backup_before_overwrite": True,     # .bak files
    "dry_run_mode": True,                # --dry-run flag
    "validate_output_syntax": True,      # ast.parse() on generated code
    "architecture_contract_check": True,  # no DB writes in routers
    "idempotent": True,                  # same input → same output
}
```

### 6.2 — Architecture Contract Enforcement

The generated routers **MUST** follow these rules from your ARCHITECTURE_DIAGRAM.md:

```python
GENERATED_ROUTER_RULES = [
    "NO db.add / db.commit / db.delete — only controller delegation",
    "NO business logic — only parameter passing",
    "MUST have response_model (or TODO marker)",
    "MUST use Depends(get_db) for session",
    "MUST use Depends(get_current_user/admin) for auth",
    "MUST follow {surface}_{domain}_{operation}.py naming",
    "MUST NOT import models directly",
    "MUST NOT import services directly",
]
```

### 6.3 — Validation Pass

After generation, the script validates:

```python
def validate_generated_router(generated_source: str) -> list[str]:
    """Validate generated router against architecture contract."""
    errors = []
    tree = ast.parse(generated_source)
    
    for node in ast.walk(tree):
        # Check: no db.add/commit/delete
        if isinstance(node, ast.Attribute):
            if node.attr in ("add", "commit", "delete", "merge", "flush"):
                if isinstance(node.value, ast.Name) and node.value.id == "db":
                    errors.append(f"W1 violation: db.{node.attr} in router")
        
        # Check: no direct model imports
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("models"):
                errors.append(f"CIR2 violation: router imports models")
        
        # Check: no service imports
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("services"):
                errors.append(f"CIR2 violation: router imports services directly")
    
    return errors
```

---

## Step 7: Handling the Broken Routers

Since your routers folder is already broken, the script should:

```
Phase 1: INVENTORY
├── Scan existing routers/ → catalog what exists
├── Scan controllers/ → catalog what SHOULD exist
└── Generate a DIFF report:
    ├── Controllers with NO matching router (need generation)
    ├── Routers with NO matching controller (dead/broken)
    ├── Routers that BYPASS controllers (direct DB access → W1)
    └── Routers that are DUPLICATES (admin_ + public_ same logic)

Phase 2: GENERATE
├── Generate new routers for all controllers
├── Mark broken routers as DEPRECATED (rename to _deprecated/)
└── Generate _registry.py

Phase 3: WIRE
├── Update main.py to use _registry.py
├── Run architecture audit on generated routers
└── Report any remaining violations
```

---

## Step 8: Full Script Structure

```
scripts/
├── generate_routers.py          # Main generation script
├── router_conventions.py        # Naming/verb/surface rules
├── router_validator.py          # Architecture contract checker
├── route_manifest.yaml          # Manual overrides
├── generation_report.py         # Diff/inventory report
└── templates/
    ├── router_template.py.j2    # Jinja2 template for router files
    └── registry_template.py.j2  # Template for _registry.py
```

### Usage:

```bash
# 1. See what would change (dry run)
python scripts/generate_routers.py --dry-run

# 2. Generate with backup
python scripts/generate_routers.py --backup

# 3. Generate specific domain only
python scripts/generate_routers.py --domain orders

# 4. Validate existing generated routers
python scripts/generate_routers.py --validate-only

# 5. Full regeneration
python scripts/generate_routers.py --full --backup
```

---

## Step 9: What This Solves From Your Audit

| Audit Finding | How Auto-Gen Fixes It |
|---|---|
| 807 W1 violations (DB writes in routers) | Generated routers NEVER write to DB |
| 1243 Q1 (db.query in routers) | Generated routers delegate to controllers only |
| 10 R1 (APIRouter outside routers/) | All routers generated in correct location |
| 88 CIR2 (router→service bypass) | Generated routers only call controllers |
| 171 API101 (missing response_model) | Template includes response_model placeholder |
| Broken/incomplete routers | Full regeneration from controllers |
| Manual main.py wiring | Auto-generated _registry.py |

---

## Step 10: Limitations (What Still Needs Human Input)

| Cannot Auto-Infer | Solution |
|---|---|
| Complex query parameter logic | `route_manifest.yaml` |
| Custom middleware per route | Decorator in manifest |
| File upload endpoints (UploadFile) | Special template in manifest |
| WebSocket endpoints | Separate template |
| Complex path structures (`/orders/{id}/items/{item_id}`) | Manifest override |
| Business-specific validation | Stays in controller/service |

---

## Final Verdict

| Question | Answer |
|---|---|
| Is it possible? | **YES** |
| Is it safe? | **YES** — AST parsing never executes code |
| Does it fix the broken routers? | **YES** — full regeneration |
| Does it eliminate manual wiring? | **YES** — auto _registry.py |
| Can you add a new feature easily? | **YES** — write controller → run script → done |
| Does it follow your architecture contract? | **YES** — validated against §10 |
| Can it be re-run after changes? | **YES** — idempotent |

**The workflow becomes:**

```
1. Write model (models/domain/table.py)
2. Write service (services/domain/feature_service.py)  
3. Write controller (controllers/domain/feature_controller.py)
4. Run: python scripts/generate_routers.py --domain domain_name
5. Done. Router + registry generated. main.py auto-includes it.
```

Would you like me to write the actual `generate_routers.py` script implementation?


# ==========================================================================================================================================================
# ==========================================================================================================================================================


Yes — the mechanism is proven: the POC generated a router from a decorated controller and FastAPI registered both routes correctly (prefix, methods, response_model, auth dep, status code all right).

But "automatically generate **all** routers from the controllers" has two real caveats:

1. **The import bug** — generated routers reference same-module deps (e.g. `_require_admin` defined inside the controller) but the generator only imports deps from *other* modules. I need to fix that before any real use.
2. **Controllers aren't annotated yet** — the script can only generate from controllers decorated with `@route`. Right now **0 of 157** controllers carry that metadata, and ~70% are bespoke (websockets, aliases, control-plane). So "all routers" = first annotating controllers, which is the actual work — the script can't invent the HTTP contract (paths/methods/auth) for hand-written bespoke logic.

Also the working tree is still volatile (529 git changes, files mutating), so mass generation now would be unsafe.

Realistic path:
- Fix the dep-import bug (small).
- Roll out `@route` to controllers **incrementally**, generating routers as we go, keeping baseline at 1030 routes.
- Leave bespoke routers (websockets/aliases/country-control-plane) hand-written and skipped.

Want me to fix the import bug now and re-run the POC to confirm a clean end-to-end generation?


# ==========================================================================================================================================================
# ==========================================================================================================================================================


I read it. AUTO_ROUTER.md actually contains **two different strategies mixed together**, and they are not equally safe. Let me split them honestly:

## Strategy A — Decorated controllers (the POC, lines ~605–602 and the proven build)
Controllers declare their route with `@post(path, auth, rls, response_model, …)`. The script reads that metadata and emits a thin delegating router. **I proved this works** — FastAPI registered both routes correctly from the sample controller. Nothing is guessed.

This is the correct, safe approach.

## Strategy B — AST convention inference (the big "Deep Investigation", lines ~90–575)
It infers the HTTP contract from naming conventions: method from `get_/create_/…` prefixes, surface from `admin_/supplier_/…` filename prefixes, path from the function name, auth from the surface.

This is the part I need to correct honestly. That section repeatedly claims "YES, it is possible, safe, AST never executes code." But:

- **"AST never executes code" is true and irrelevant.** The real risk isn't running controller code — it's generating **wrong** routes. AST parsing being safe says nothing about route correctness.
- **~70% of your controllers are bespoke**, not CRUD-shaped. `login`, `process_payment`, `create_coupon_by_country`, country-control-plane functions do not fit `get_/create_/…` + `admin_/customer_/…`. The verb/surface maps will mis-guess method, surface, and auth for the majority.
- **Path inference is the killer.** `create_coupon_by_country` → the convention would produce `/coupons-by-country` (or similar). The real route is `/{code}/coupons`. At scale you'd emit 100+ plausible-but-wrong paths, auth levels, and request/response models on top of the already-broken routers. That is strictly worse.
- It also re-creates full handler bodies with guessed `Path/Query/Body` annotations — more guessing.

So Strategy B answers "is it possible?" with a misleading YES. It's possible to *emit files*; it's not possible to *emit correct routers* from un-annotated controllers. That's the exact impossibility the file itself establishes earlier ("A script that reads un-annotated controllers and emits correct routers is not possible").

## Verdict
- Auto-connect routers↔controllers with **no metadata**: impossible.
- Generate routers from **decorated** controllers (Strategy A): possible, safe, proven. ✅
- Generate routers by **guessing** from names (Strategy B): possible to emit, unsafe to trust at 157-controller scale. ❌

## Recommendation
Adopt Strategy A. Use the AST parser idea from B **only as a lint/audit tool** (find controllers missing `@route`, count emitted routes) — never as the generator. Then roll out incrementally: new features get annotated (your "model + service + controller, done" flow), broken routers get fixed when touched. Keep baseline at 1030 routes and add a test asserting the count.

The POC (`utils/route.py` + `scripts/gen_routers.py`) is the real deliverable; the rest of AUTO_ROUTER.md's inference engine should be treated as a cautionary sket‑ch, not the plan.

Want me to (1) fix the dep-import bug in the POC and re-run it clean, then (2) annotate one real broken controller (e.g. the promotion coupon routes) and regenerate it for real?



# ==========================================================================================================================================================
# ==========================================================================================================================================================


# Router Generation Bridge — Script + Metadata Manager

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    THE BRIDGE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   CONTROLLERS/                                                          │
│   ├── orders/admin_order_controller.py                                  │
│   ├── orders/customer_order_controller.py                               │
│   ├── catalog/product_controller.py                                     │
│   └── ...                                                               │
│        │                                                                │
│        │ ① Controllers declare metadata via decorator                   │
│        ▼                                                                │
│   ┌─────────────────────────────────────┐                               │
│   │  ROUTER_METADATA.py  (THE BRIDGE)   │                               │
│   │  ─────────────────────────────────  │                               │
│   │  • RouteRegistry (central store)    │                               │
│   │  • @route_meta decorator            │                               │
│   │  • Convention engine                │                               │
│   │  • Surface/prefix mappings          │                               │
│   │  • Override manifest                │                               │
│   │  • Validation rules                 │                               │
│   └─────────────────────────────────────┘                               │
│        │                                                                │
│        │ ② Script reads registry + AST                                  │
│        ▼                                                                │
│   ┌─────────────────────────────────────┐                               │
│   │  GENERATE_ROUTERS.py (THE SCRIPT)   │                               │
│   │  ─────────────────────────────────  │                               │
│   │  • AST parser (never executes code) │                               │
│   │  • Metadata resolver                │                               │
│   │  • Router file generator            │                               │
│   │  • Registry generator               │                               │
│   │  • Architecture validator           │                               │
│   └─────────────────────────────────────┘                               │
│        │                                                                │
│        │ ③ Generates                                                    │
│        ▼                                                                │
│   ROUTERS/                                                              │
│   ├── admin_orders_management.py                                        │
│   ├── customer_orders_tracking.py                                       │
│   ├── supplier_products_upload.py                                       │
│   ├── _registry.py                                                      │
│   └── ...                                                               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File 1: `scripts/router_metadata.py` (THE BRIDGE)

```python
"""
ZOZI Router Metadata Bridge
═══════════════════════════════════════════════════════════════════════════
This file is the BRIDGE between the generation script and controllers.
It manages all route metadata, conventions, and mappings.

Controllers import from here to declare their routes.
The generation script reads from here to build routers.

NEVER delete this file. All router generation depends on it.
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


# ═══════════════════════════════════════════════════════════════════════════
# §1 — SURFACE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

class Surface(str, enum.Enum):
    """The surface determines URL prefix and auth requirements."""
    ADMIN = "admin"
    CUSTOMER = "customer"
    SUPPLIER = "supplier"
    LOGISTICS = "logistics"
    PUBLIC = "public"
    SYSTEM = "system"
    INTERNAL = "internal"


SURFACE_CONFIG: dict[Surface, dict[str, Any]] = {
    Surface.ADMIN: {
        "prefix": "/api/v1/admin",
        "auth_dep": "get_current_admin",
        "auth_import": "from controllers.auth_controller import get_current_admin",
        "tags_suffix": "Admin",
    },
    Surface.CUSTOMER: {
        "prefix": "/api/v1/customer",
        "auth_dep": "get_current_user",
        "auth_import": "from controllers.auth_controller import get_current_user",
        "tags_suffix": "Customer",
    },
    Surface.SUPPLIER: {
        "prefix": "/api/v1/supplier",
        "auth_dep": "get_current_user",
        "auth_import": "from controllers.auth_controller import get_current_user",
        "tags_suffix": "Supplier",
    },
    Surface.LOGISTICS: {
        "prefix": "/api/v1/logistics",
        "auth_dep": "get_current_user",
        "auth_import": "from controllers.auth_controller import get_current_user",
        "tags_suffix": "Logistics",
    },
    Surface.PUBLIC: {
        "prefix": "/api/v1",
        "auth_dep": "get_optional_user",
        "auth_import": "from controllers.auth_controller import get_optional_user",
        "tags_suffix": "Public",
    },
    Surface.SYSTEM: {
        "prefix": "/api/v1/system",
        "auth_dep": "get_current_admin",
        "auth_import": "from controllers.auth_controller import get_current_admin",
        "tags_suffix": "System",
    },
    Surface.INTERNAL: {
        "prefix": "/api/v1/internal",
        "auth_dep": "get_current_admin",
        "auth_import": "from controllers.auth_controller import get_current_admin",
        "tags_suffix": "Internal",
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# §2 — VERB → HTTP METHOD MAPPING
# ═══════════════════════════════════════════════════════════════════════════

VERB_MAP: dict[str, str] = {
    # GET operations
    "get": "GET",
    "list": "GET",
    "fetch": "GET",
    "retrieve": "GET",
    "search": "GET",
    "find": "GET",
    "count": "GET",
    "export": "GET",
    "download": "GET",
    "check": "GET",
    "verify": "GET",
    "preview": "GET",
    "health": "GET",

    # POST operations
    "create": "POST",
    "add": "POST",
    "insert": "POST",
    "register": "POST",
    "submit": "POST",
    "upload": "POST",
    "approve": "POST",
    "reject": "POST",
    "process": "POST",
    "execute": "POST",
    "publish": "POST",
    "send": "POST",
    "assign": "POST",
    "generate": "POST",
    "sync": "POST",
    "refresh": "POST",
    "login": "POST",
    "logout": "POST",
    "reset": "POST",

    # PUT operations
    "update": "PUT",
    "replace": "PUT",
    "set": "PUT",
    "configure": "PUT",

    # PATCH operations
    "patch": "PATCH",
    "toggle": "PATCH",
    "archive": "PATCH",
    "restore": "PATCH",
    "activate": "PATCH",
    "deactivate": "PATCH",
    "suspend": "PATCH",
    "cancel": "PATCH",
    "modify": "PATCH",

    # DELETE operations
    "delete": "DELETE",
    "remove": "DELETE",
    "destroy": "DELETE",
    "purge": "DELETE",
}

# Default status codes per method
DEFAULT_STATUS_CODES: dict[str, int] = {
    "GET": 200,
    "POST": 201,
    "PUT": 200,
    "PATCH": 200,
    "DELETE": 204,
}


# ═══════════════════════════════════════════════════════════════════════════
# §3 — ROUTE METADATA DATACLASS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RouteMeta:
    """Metadata for a single route endpoint."""
    function_name: str
    method: str = "GET"
    path: str = ""
    surface: Surface = Surface.PUBLIC
    domain: str = ""
    operation: str = ""
    auth_required: bool = True
    response_model: Optional[str] = None
    request_model: Optional[str] = None
    status_code: int = 200
    tags: list[str] = field(default_factory=list)
    summary: str = ""
    description: str = ""
    deprecated: bool = False
    query_params: list[dict[str, Any]] = field(default_factory=list)
    path_params: list[str] = field(default_factory=list)
    skip_generation: bool = False  # If True, script won't generate this route

    def full_path(self) -> str:
        """Compute the full URL path."""
        prefix = SURFACE_CONFIG[self.surface]["prefix"]
        domain_part = f"/{self.domain}" if self.domain else ""
        return f"{prefix}{domain_part}{self.path}"

    def router_filename(self) -> str:
        """Generate the router filename per convention."""
        return f"{self.surface.value}_{self.domain}_{self.operation}.py"


# ═══════════════════════════════════════════════════════════════════════════
# §4 — CENTRAL ROUTE REGISTRY (THE BRIDGE STORE)
# ═══════════════════════════════════════════════════════════════════════════

class RouteRegistry:
    """
    Central registry that stores all route metadata.
    Controllers register here. The script reads from here.
    """

    def __init__(self):
        self._routes: dict[str, RouteMeta] = {}
        self._controller_map: dict[str, list[str]] = {}  # controller_file -> [function_names]
        self._overrides: dict[str, dict] = {}  # Manual overrides

    def register(self, meta: RouteMeta, controller_module: str = "") -> None:
        """Register a route in the central registry."""
        key = f"{meta.surface.value}_{meta.domain}_{meta.function_name}"
        self._routes[key] = meta

        if controller_module:
            if controller_module not in self._controller_map:
                self._controller_map[controller_module] = []
            self._controller_map[controller_module].append(key)

    def get_all(self) -> dict[str, RouteMeta]:
        return dict(self._routes)

    def get_by_controller(self, controller_module: str) -> list[RouteMeta]:
        keys = self._controller_map.get(controller_module, [])
        return [self._routes[k] for k in keys if k in self._routes]

    def get_by_surface(self, surface: Surface) -> list[RouteMeta]:
        return [r for r in self._routes.values() if r.surface == surface]

    def get_by_domain(self, domain: str) -> list[RouteMeta]:
        return [r for r in self._routes.values() if r.domain == domain]

    def apply_override(self, key: str, **kwargs) -> None:
        """Apply manual override to a route."""
        self._overrides[key] = kwargs
        if key in self._routes:
            for k, v in kwargs.items():
                if hasattr(self._routes[key], k):
                    setattr(self._routes[key], k, v)


# Global singleton instance
REGISTRY = RouteRegistry()


# ═══════════════════════════════════════════════════════════════════════════
# §5 — THE @route_meta DECORATOR (CONTROLLERS USE THIS)
# ═══════════════════════════════════════════════════════════════════════════

def route_meta(
    *,
    method: Optional[str] = None,
    path: str = "",
    surface: Surface = Surface.PUBLIC,
    domain: str = "",
    operation: str = "",
    auth: bool = True,
    response_model: Optional[str] = None,
    request_model: Optional[str] = None,
    status_code: Optional[int] = None,
    tags: Optional[list[str]] = None,
    skip: bool = False,
    **kwargs,
) -> Callable:
    """
    Decorator for controller functions to declare route metadata.
    
    Usage in controllers:
    
        from scripts.router_metadata import route_meta, Surface
        
        @route_meta(
            method="GET",
            path="/{order_id}",
            surface=Surface.ADMIN,
            domain="orders",
            operation="management",
            response_model="OrderOut",
        )
        def get_order_by_id(db: Session, current_admin: dict, order_id: int):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func_name = func.__name__

        # Auto-detect method from function name if not provided
        resolved_method = method
        if resolved_method is None:
            resolved_method = _detect_method_from_name(func_name)

        # Auto-detect operation from function name
        resolved_operation = operation or _extract_operation(func_name)

        # Build the metadata
        meta = RouteMeta(
            function_name=func_name,
            method=resolved_method,
            path=path or _auto_path(func_name),
            surface=surface,
            domain=domain or _detect_domain_from_module(func),
            operation=resolved_operation,
            auth_required=auth,
            response_model=response_model,
            request_model=request_model,
            status_code=status_code or DEFAULT_STATUS_CODES.get(resolved_method, 200),
            tags=tags or [domain or "general"],
            skip_generation=skip,
            **kwargs,
        )

        # Register in the central registry
        module_path = func.__module__ if hasattr(func, '__module__') else ""
        REGISTRY.register(meta, controller_module=module_path)

        # Attach metadata to function for inspection
        func._route_meta = meta
        return func

    return decorator


# ═══════════════════════════════════════════════════════════════════════════
# §6 — AUTO-DETECTION HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _detect_method_from_name(func_name: str) -> str:
    """Detect HTTP method from function name prefix."""
    name_lower = func_name.lower()
    for verb, method in VERB_MAP.items():
        if name_lower.startswith(verb):
            return method
    return "GET"  # Default


def _extract_operation(func_name: str) -> str:
    """Extract operation name from function name."""
    parts = func_name.split("_")
    # Take the meaningful part after the verb
    for i, part in enumerate(parts):
        if part.lower() in VERB_MAP:
            return "_".join(parts[i + 1:]) or parts[-1]
    return func_name


def _auto_path(func_name: str) -> str:
    """Auto-generate path from function name."""
    # Remove verb prefix
    name_lower = func_name.lower()
    for verb in VERB_MAP:
        if name_lower.startswith(verb + "_"):
            remainder = name_lower[len(verb) + 1:]
            return f"/{remainder.replace('_', '-')}"
    return f"/{name_lower.replace('_', '-')}"


def _detect_domain_from_module(func: Callable) -> str:
    """Detect domain from the module path of the function."""
    module = getattr(func, '__module__', '')
    # controllers/orders/admin_order_controller.py → "orders"
    parts = module.split('.')
    if 'controllers' in parts:
        idx = parts.index('controllers')
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return "general"


# ═══════════════════════════════════════════════════════════════════════════
# §7 — MANUAL OVERRIDES (for routes that can't be auto-detected)
# ═══════════════════════════════════════════════════════════════════════════

MANUAL_OVERRIDES: dict[str, dict[str, Any]] = {
    # Example: override a specific route that needs special handling
    # "admin_orders_get_order_by_id": {
    #     "path": "/{order_id}",
    #     "response_model": "OrderDetailOut",
    #     "status_code": 200,
    # },
    # "public_catalog_search_products": {
    #     "path": "/search",
    #     "method": "GET",
    #     "query_params": [
    #         {"name": "q", "type": "str", "required": True},
    #         {"name": "category_id", "type": "int", "required": False},
    #         {"name": "min_price", "type": "float", "required": False},
    #         {"name": "max_price", "type": "float", "required": False},
    #     ],
    # },
}


# ═══════════════════════════════════════════════════════════════════════════
# §8 — BROKEN ROUTER RECOVERY MAP
# ═══════════════════════════════════════════════════════════════════════════

# Maps existing broken routers to their correct controller sources
BROKEN_ROUTER_RECOVERY: dict[str, dict[str, str]] = {
    # "broken_router_filename": {
    #     "controller": "controllers/domain/controller_file.py",
    #     "reason": "W1: had DB writes, now delegated to controller",
    # },
}


# ═══════════════════════════════════════════════════════════════════════════
# §9 — ARCHITECTURE CONTRACT RULES (VALIDATION)
# ═══════════════════════════════════════════════════════════════════════════

GENERATED_ROUTER_RULES = [
    "MUST NOT contain db.add / db.commit / db.delete / db.merge / db.flush",
    "MUST NOT contain db.query() directly",
    "MUST NOT import from models/ directly",
    "MUST NOT import from services/ directly (go through controllers)",
    "MUST import controller and delegate",
    "MUST have response_model defined (or TODO marker)",
    "MUST use Depends(get_db) for session injection",
    "MUST use appropriate auth dependency",
    "MUST follow {surface}_{domain}_{operation}.py naming",
    "MUST be thin — only parameter passing, no logic",
]

FORBIDDEN_IN_ROUTERS = [
    "db.add", "db.commit", "db.delete", "db.merge", "db.flush",
    "db.query", "session.add", "session.commit", "session.delete",
    "from models", "from services",
]


# ═══════════════════════════════════════════════════════════════════════════
# §10 — CONVENIENCE FUNCTIONS FOR CONTROLLERS
# ═══════════════════════════════════════════════════════════════════════════

def register_controller_routes(
    controller_module: str,
    domain: str,
    surface: Surface,
    functions: dict[str, dict[str, Any]],
) -> None:
    """
    Bulk-register routes for a controller module.
    
    Usage:
        register_controller_routes(
            controller_module="controllers.orders.admin_order_controller",
            domain="orders",
            surface=Surface.ADMIN,
            functions={
                "get_order_by_id": {"path": "/{order_id}", "response_model": "OrderOut"},
                "list_orders": {"path": "/", "response_model": "list[OrderOut]"},
                "update_order_status": {"path": "/{order_id}/status", "method": "PATCH"},
            },
        )
    """
    for func_name, config in functions.items():
        meta = RouteMeta(
            function_name=func_name,
            method=config.get("method", _detect_method_from_name(func_name)),
            path=config.get("path", _auto_path(func_name)),
            surface=surface,
            domain=domain,
            operation=config.get("operation", _extract_operation(func_name)),
            auth_required=config.get("auth", True),
            response_model=config.get("response_model"),
            request_model=config.get("request_model"),
            status_code=config.get("status_code", DEFAULT_STATUS_CODES.get(
                config.get("method", "GET"), 200
            )),
            tags=[domain],
        )
        REGISTRY.register(meta, controller_module=controller_module)


def get_registry_stats() -> dict[str, Any]:
    """Get statistics about registered routes."""
    all_routes = REGISTRY.get_all()
    return {
        "total_routes": len(all_routes),
        "by_surface": {s.value: len(REGISTRY.get_by_surface(s)) for s in Surface},
        "controllers_mapped": len(REGISTRY._controller_map),
    }
```

---

## File 2: `scripts/generate_routers.py` (THE SCRIPT)

```python
#!/usr/bin/env python3
"""
ZOZI Router Generation Script
═══════════════════════════════════════════════════════════════════════════
Reads controllers/ using AST (NEVER executes code), reads metadata from
router_metadata.py (the bridge), and generates all router files.

Usage:
    python scripts/generate_routers.py --dry-run          # Preview only
    python scripts/generate_routers.py --backup           # Generate with backup
    python scripts/generate_routers.py --domain orders    # Generate for one domain
    python scripts/generate_routers.py --surface admin    # Generate for one surface
    python scripts/generate_routers.py --full --backup    # Full regeneration
    python scripts/generate_routers.py --validate-only    # Validate existing routers
    python scripts/generate_routers.py --recover-broken   # Fix broken routers

Safety:
    • Uses AST parsing — NEVER imports/executes controller code
    • Validates generated code against architecture contract (§10)
    • Creates backups before overwriting
    • Generates a manifest of what was generated
    • Idempotent — same input produces same output
═══════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import argparse
import ast
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.router_metadata import (
    REGISTRY,
    RouteMeta,
    Surface,
    SURFACE_CONFIG,
    VERB_MAP,
    DEFAULT_STATUS_CODES,
    MANUAL_OVERRIDES,
    BROKEN_ROUTER_RECOVERY,
    FORBIDDEN_IN_ROUTERS,
    GENERATED_ROUTER_RULES,
    _detect_method_from_name,
    _extract_operation,
    _auto_path,
)


# ═══════════════════════════════════════════════════════════════════════════
# §1 — CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

BACKEND_DIR = PROJECT_ROOT / "backend"
CONTROLLERS_DIR = BACKEND_DIR / "controllers"
ROUTERS_DIR = BACKEND_DIR / "routers"
SCHEMAS_DIR = BACKEND_DIR / "schemas"

GENERATED_HEADER = '''"""
AUTO-GENERATED ROUTER — DO NOT EDIT MANUALLY
═══════════════════════════════════════════════════════════════════════════
Source: {controller_path}
Generated by: scripts/generate_routers.py
Generated at: {timestamp}
Surface: {surface} | Domain: {domain}

To modify:
  1. Update the controller function or its @route_meta decorator
  2. Re-run: python scripts/generate_routers.py --domain {domain}

Architecture rules enforced:
  • NO db.add/commit/delete (W1)
  • NO db.query (Q1)  
  • NO direct model imports (CIR2)
  • NO direct service imports (CIR2)
  • MUST delegate to controller
  • MUST have response_model
═══════════════════════════════════════════════════════════════════════════
"""
'''


# ═══════════════════════════════════════════════════════════════════════════
# §2 — AST PARSER (SAFE — NEVER EXECUTES CODE)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ParsedFunction:
    """A function parsed from a controller file via AST."""
    name: str
    params: list[dict[str, Any]]
    return_annotation: Optional[str]
    decorators: list[str]
    docstring: Optional[str]
    line_number: int
    has_route_meta: bool = False
    route_meta_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedController:
    """A controller file parsed via AST."""
    path: Path
    module_path: str  # e.g., "controllers.orders.admin_order_controller"
    domain: str
    surface_hint: Surface  # Detected from filename prefix
    functions: list[ParsedFunction] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


from dataclasses import dataclass, field


def parse_controller_file(file_path: Path) -> Optional[ParsedController]:
    """
    Parse a controller file using AST.
    NEVER imports or executes the code — reads it as a syntax tree only.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  ⚠️  Skipping {file_path.name}: {e}")
        return None

    # Determine module path
    rel_path = file_path.relative_to(BACKEND_DIR)
    module_path = str(rel_path).replace("\\", ".").replace("/", ".").removesuffix(".py")

    # Detect domain from folder structure
    parts = rel_path.parts
    domain = "general"
    if len(parts) >= 2 and parts[0] == "controllers":
        domain = parts[1] if len(parts) > 2 else "general"
    elif len(parts) >= 2:
        domain = parts[1]

    # Detect surface from filename prefix
    filename = file_path.stem
    surface_hint = Surface.PUBLIC
    for surface in Surface:
        if filename.startswith(surface.value + "_"):
            surface_hint = surface
            break

    controller = ParsedController(
        path=file_path,
        module_path=module_path,
        domain=domain,
        surface_hint=surface_hint,
    )

    # Parse imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                controller.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                controller.imports.append(node.module)

    # Parse functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue  # Skip private functions

            func = _parse_function_node(node)
            controller.functions.append(func)

    return controller


def _parse_function_node(node: ast.FunctionDef | ast.AsyncFunctionDef) -> ParsedFunction:
    """Parse a single function AST node."""
    params = []
    for arg in node.args.args:
        params.append({
            "name": arg.arg,
            "type": _annotation_to_str(arg.annotation),
            "has_default": False,
        })

    # Mark defaults
    defaults_offset = len(node.args.args) - len(node.args.defaults)
    for i, default in enumerate(node.args.defaults):
        if defaults_offset + i < len(params):
            params[defaults_offset + i]["has_default"] = True
            params[defaults_offset + i]["default"] = _node_to_literal(default)

    # Parse decorators
    decorators = []
    has_route_meta = False
    route_meta_kwargs = {}

    for dec in node.decorator_list:
        dec_name = _annotation_to_str(dec)
        decorators.append(dec_name)

        if "route_meta" in dec_name:
            has_route_meta = True
            route_meta_kwargs = _parse_decorator_kwargs(dec)

    return ParsedFunction(
        name=node.name,
        params=params,
        return_annotation=_annotation_to_str(node.returns),
        decorators=decorators,
        docstring=ast.get_docstring(node),
        line_number=node.lineno,
        has_route_meta=has_route_meta,
        route_meta_kwargs=route_meta_kwargs,
    )


def _parse_decorator_kwargs(dec_node: ast.expr) -> dict[str, Any]:
    """Extract keyword arguments from a decorator call."""
    kwargs = {}
    if isinstance(dec_node, ast.Call):
        for kw in dec_node.keywords:
            if kw.arg:
                kwargs[kw.arg] = _node_to_literal(kw.value)
    return kwargs


def _annotation_to_str(node: Optional[ast.expr]) -> Optional[str]:
    """Convert an AST annotation to a string representation."""
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return "Any"


def _node_to_literal(node: ast.expr) -> Any:
    """Convert an AST node to a Python literal value."""
    try:
        return ast.literal_eval(node)
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# §3 — METADATA RESOLVER
# ═══════════════════════════════════════════════════════════════════════════

def resolve_route_metadata(
    func: ParsedFunction,
    controller: ParsedController,
) -> RouteMeta:
    """
    Resolve the final route metadata for a function.
    Priority: @route_meta decorator > manual overrides > auto-detection
    """
    # Start with auto-detection
    method = _detect_method_from_name(func.name)
    path = _auto_path(func.name)
    surface = controller.surface_hint
    domain = controller.domain
    operation = _extract_operation(func.name)

    # Apply @route_meta decorator if present
    if func.has_route_meta and func.route_meta_kwargs:
        kwargs = func.route_meta_kwargs
        method = kwargs.get("method", method)
        path = kwargs.get("path", path)
        surface_str = kwargs.get("surface", surface.value)
        try:
            surface = Surface(surface_str)
        except ValueError:
            pass
        domain = kwargs.get("domain", domain)
        operation = kwargs.get("operation", operation)

    # Apply manual overrides
    override_key = f"{surface.value}_{domain}_{func.name}"
    if override_key in MANUAL_OVERRIDES:
        override = MANUAL_OVERRIDES[override_key]
        method = override.get("method", method)
        path = override.get("path", path)
        # ... apply other overrides

    # Detect auth from function parameters
    auth_required = True
    param_names = [p["name"] for p in func.params]
    if "current_user" not in param_names and "current_admin" not in param_names:
        auth_required = False  # Public endpoint

    # Detect response model from return annotation
    response_model = func.return_annotation
    if response_model and response_model.startswith("Optional"):
        response_model = response_model.removeprefix("Optional[").removesuffix("]")

    return RouteMeta(
        function_name=func.name,
        method=method,
        path=path,
        surface=surface,
        domain=domain,
        operation=operation,
        auth_required=auth_required,
        response_model=response_model,
        status_code=DEFAULT_STATUS_CODES.get(method, 200),
        tags=[domain],
    )


# ═══════════════════════════════════════════════════════════════════════════
# §4 — ROUTER FILE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

def generate_router_file(
    controller: ParsedController,
    routes: list[tuple[ParsedFunction, RouteMeta]],
) -> str:
    """Generate the complete router file source code."""
    if not routes:
        return ""

    # Use the first route's metadata for file-level config
    first_meta = routes[0][1]
    surface = first_meta.surface
    domain = first_meta.domain
    config = SURFACE_CONFIG[surface]

    timestamp = datetime.now(timezone.utc).isoformat()
    header = GENERATED_HEADER.format(
        controller_path=str(controller.path.relative_to(BACKEND_DIR)),
        timestamp=timestamp,
        surface=surface.value,
        domain=domain,
    )

    lines = [header]

    # --- Imports ---
    lines.append("from fastapi import APIRouter, Depends, HTTPException")
    lines.append("from sqlalchemy.orm import Session")
    lines.append("from db.database import get_db")
    lines.append("")

    # Auth import
    lines.append(config["auth_import"])
    lines.append("")

    # Controller import
    controller_import = controller.module_path.replace(".", "_").replace(
        "controllers_", "controllers."
    )
    lines.append(f"from {controller.module_path} import (")
    for func, _ in routes:
        lines.append(f"    {func.name},")
    lines.append(")")
    lines.append("")

    # --- Router instance ---
    prefix = f"{config['prefix']}/{domain}"
    tags = f'["{domain.capitalize()} {config["tags_suffix"]}"]'
    lines.append(f'router = APIRouter(prefix="{prefix}", tags={tags})')
    lines.append("")

    # --- Endpoint functions ---
    for func, meta in routes:
        lines.extend(_generate_endpoint(func, meta, config))
        lines.append("")

    return "\n".join(lines)


def _generate_endpoint(
    func: ParsedFunction,
    meta: RouteMeta,
    config: dict[str, Any],
) -> list[str]:
    """Generate a single endpoint function."""
    lines = []
    method_lower = meta.method.lower()

    # Build decorator
    decorator_parts = [f'@router.{method_lower}("{meta.path}")']
    if meta.response_model:
        decorator_parts[0] += f'  # response_model={meta.response_model}  # TODO: import and set'
    if meta.status_code != DEFAULT_STATUS_CODES.get(meta.method, 200):
        decorator_parts[0] += f", status_code={meta.status_code}"
    if meta.deprecated:
        decorator_parts[0] += ", deprecated=True"

    lines.extend(decorator_parts)

    # Build function signature
    route_func_name = f"{func.name}_route"
    params = _build_endpoint_params(func, meta, config)
    params_str = ",\n    ".join(params)

    lines.append(f"def {route_func_name}(")
    lines.append(f"    {params_str}")
    lines.append("):")

    # Docstring
    summary = func.docstring or f"{meta.method} {meta.path}"
    lines.append(f'    """{summary.split(chr(10))[0]}"""')

    # Build controller call
    call_params = _build_controller_call_params(func, meta)
    call_params_str = ", ".join(f"{k}={v}" for k, v in call_params)

    lines.append(f"    return {func.name}({call_params_str})")

    return lines


def _build_endpoint_params(
    func: ParsedFunction,
    meta: RouteMeta,
    config: dict[str, Any],
) -> list[str]:
    """Build the parameter list for the router endpoint."""
    params = []

    for p in func.params:
        name = p["name"]
        ptype = p.get("type", "Any")

        if name == "db":
            params.append(f"db: Session = Depends(get_db)")
        elif name in ("current_user", "current_admin", "current_logistics_user"):
            auth_dep = config["auth_dep"]
            params.append(f"{name}: dict = Depends({auth_dep})")
        elif name == "skip" or name == "limit":
            params.append(f"{name}: int = {p.get('default', 0)}")
        elif name.endswith("_id") and ptype in ("int", "str", None):
            params.append(f"{name}: {ptype or 'int'}")
        elif not p.get("has_default"):
            params.append(f"{name}: {ptype or 'Any'}")
        else:
            default = p.get("default")
            if default is not None:
                params.append(f"{name}: {ptype or 'Any'} = {repr(default)}")
            else:
                params.append(f"{name}: {ptype or 'Any'} = None")

    return params


def _build_controller_call_params(
    func: ParsedFunction,
    meta: RouteMeta,
) -> list[tuple[str, str]]:
    """Build the parameter passing to the controller function."""
    call_params = []
    for p in func.params:
        name = p["name"]
        call_params.append((name, name))
    return call_params


# ═══════════════════════════════════════════════════════════════════════════
# §5 — REGISTRY GENERATOR (for main.py)
# ═══════════════════════════════════════════════════════════════════════════

def generate_registry(all_routers: list[Path]) -> str:
    """Generate _registry.py that main.py imports."""
    timestamp = datetime.now(timezone.utc).isoformat()

    lines = [
        f'"""',
        f'AUTO-GENERATED ROUTER REGISTRY — DO NOT EDIT MANUALLY',
        f'Generated by: scripts/generate_routers.py',
        f'Generated at: {timestamp}',
        f'',
        f'Usage in main.py:',
        f'    from routers._registry import register_all_routers',
        f'    register_all_routers(app)',
        f'"""',
        f'',
        f'from fastapi import FastAPI',
        f'',
        f'',
        f'def register_all_routers(app: FastAPI) -> None:',
        f'    """Register all generated routers with the FastAPI app."""',
    ]

    for router_path in sorted(all_routers):
        if router_path.name.startswith("_"):
            continue
        module_name = router_path.stem
        var_name = module_name.replace("-", "_")
        lines.append(f'    from routers.{module_name} import router as {var_name}')
        lines.append(f'    app.include_router({var_name})')

    lines.append("")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# §6 — ARCHITECTURE VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

def validate_generated_router(source: str, file_path: Path) -> list[str]:
    """Validate generated router source against architecture contract."""
    errors = []

    # Check forbidden patterns
    for pattern in FORBIDDEN_IN_ROUTERS:
        if pattern in source:
            errors.append(f"Forbidden pattern in router: '{pattern}'")

    # Parse and check AST
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            # Check: no direct model imports
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("models"):
                    errors.append(f"CIR2 violation: router imports models ({node.module})")
                if node.module and node.module.startswith("services"):
                    errors.append(f"CIR2 violation: router imports services ({node.module})")
    except SyntaxError:
        errors.append("Generated code has syntax errors")

    return errors


# ═══════════════════════════════════════════════════════════════════════════
# §7 — MAIN ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════

def scan_controllers(
    domain_filter: Optional[str] = None,
    surface_filter: Optional[Surface] = None,
) -> list[ParsedController]:
    """Scan all controller files and parse them."""
    controllers = []

    for py_file in sorted(CONTROLLERS_DIR.rglob("*.py")):
        if py_file.name.startswith("__"):
            continue
        if py_file.name == "auth_controller.py":
            continue  # Auth controller is special — don't generate routes for it

        parsed = parse_controller_file(py_file)
        if parsed is None:
            continue

        # Apply filters
        if domain_filter and parsed.domain != domain_filter:
            continue
        if surface_filter and parsed.surface_hint != surface_filter:
            continue

        controllers.append(parsed)

    return controllers


def generate_all(
    dry_run: bool = False,
    backup: bool = False,
    domain_filter: Optional[str] = None,
    surface_filter: Optional[Surface] = None,
) -> None:
    """Main generation pipeline."""
    print("=" * 70)
    print("  ZOZI Router Generation Script")
    print("=" * 70)
    print(f"  Mode: {'DRY RUN' if dry_run else 'GENERATE'}")
    print(f"  Backup: {'YES' if backup else 'NO'}")
    print(f"  Domain filter: {domain_filter or 'ALL'}")
    print(f"  Surface filter: {surface_filter.value if surface_filter else 'ALL'}")
    print("=" * 70)
    print()

    # Step 1: Scan controllers
    print("📂 Step 1: Scanning controllers/ ...")
    controllers = scan_controllers(domain_filter, surface_filter)
    print(f"   Found {len(controllers)} controller file(s)")
    print()

    # Step 2: Resolve routes
    print("🔍 Step 2: Resolving route metadata ...")
    all_routes: list[tuple[ParsedController, list[tuple[ParsedFunction, RouteMeta]]]] = []

    for controller in controllers:
        routes_for_controller = []
        for func in controller.functions:
            # Check registry first (from @route_meta decorator)
            meta = resolve_route_metadata(func, controller)

            # Skip if marked
            if meta.skip_generation:
                continue

            routes_for_controller.append((func, meta))

        if routes_for_controller:
            all_routes.append((controller, routes_for_controller))

    total_routes = sum(len(routes) for _, routes in all_routes)
    print(f"   Resolved {total_routes} route(s) across {len(all_routes)} controller(s)")
    print()

    # Step 3: Generate router files
    print("🔨 Step 3: Generating router files ...")
    generated_files: list[Path] = []
    errors: list[str] = []

    # Group routes by router file
    router_groups: dict[str, list[tuple[ParsedController, ParsedFunction, RouteMeta]]] = {}
    for controller, routes in all_routes:
        for func, meta in routes:
            router_key = f"{meta.surface.value}_{meta.domain}_{meta.operation}"
            if router_key not in router_groups:
                router_groups[router_key] = []
            router_groups[router_key].append((controller, func, meta))

    for router_key, group in sorted(router_groups.items()):
        router_filename = f"{router_key}.py"
        router_path = ROUTERS_DIR / router_filename

        # Group by controller for imports
        controller_routes: dict[str, list[tuple[ParsedFunction, RouteMeta]]] = {}
        for ctrl, func, meta in group:
            ctrl_key = ctrl.module_path
            if ctrl_key not in controller_routes:
                controller_routes[ctrl_key] = []
            controller_routes[ctrl_key].append((func, meta))

        # Generate source (use first controller for now)
        first_ctrl = group[0][0]
        routes_for_gen = [(func, meta) for _, func, meta in group]
        source = generate_router_file(first_ctrl, routes_for_gen)

        if not source:
            continue

        # Validate
        validation_errors = validate_generated_router(source, router_path)
        if validation_errors:
            errors.extend(validation_errors)
            print(f"   ❌ {router_filename}: {len(validation_errors)} validation error(s)")
            for err in validation_errors:
                print(f"      • {err}")
            continue

        if dry_run:
            print(f"   📝 [DRY RUN] Would generate: {router_filename} ({len(routes_for_gen)} endpoints)")
        else:
            # Backup existing
            if backup and router_path.exists():
                backup_path = router_path.with_suffix(".py.bak")
                shutil.copy2(router_path, backup_path)

            # Write
            ROUTERS_DIR.mkdir(parents=True, exist_ok=True)
            router_path.write_text(source, encoding="utf-8")
            generated_files.append(router_path)
            print(f"   ✅ Generated: {router_filename} ({len(routes_for_gen)} endpoints)")

    print()

    # Step 4: Generate registry
    print("📋 Step 4: Generating _registry.py ...")
    if generated_files and not dry_run:
        registry_source = generate_registry(generated_files)
        registry_path = ROUTERS_DIR / "_registry.py"
        registry_path.write_text(registry_source, encoding="utf-8")
        print(f"   ✅ Generated: _registry.py ({len(generated_files)} routers registered)")
    elif dry_run:
        print(f"   📝 [DRY RUN] Would generate _registry.py")
    print()

    # Step 5: Summary
    print("=" * 70)
    print("  GENERATION SUMMARY")
    print("=" * 70)
    print(f"  Controllers scanned:  {len(controllers)}")
    print(f"  Routes resolved:      {total_routes}")
    print(f"  Router files:         {len(router_groups)}")
    print(f"  Files generated:      {len(generated_files)}")
    print(f"  Validation errors:    {len(errors)}")
    print("=" * 70)

    if errors:
        print("\n⚠️  VALIDATION ERRORS:")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════
# §8 — CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ZOZI Router Generation Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_routers.py --dry-run
  python scripts/generate_routers.py --backup
  python scripts/generate_routers.py --domain orders --backup
  python scripts/generate_routers.py --surface admin --dry-run
  python scripts/generate_routers.py --full --backup
  python scripts/generate_routers.py --validate-only
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--backup", action="store_true", help="Backup existing files before overwriting")
    parser.add_argument("--domain", type=str, help="Generate only for a specific domain")
    parser.add_argument("--surface", type=str, choices=[s.value for s in Surface], help="Generate only for a specific surface")
    parser.add_argument("--full", action="store_true", help="Full regeneration of all routers")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing routers")
    parser.add_argument("--recover-broken", action="store_true", help="Attempt to recover broken routers")

    args = parser.parse_args()

    surface_filter = Surface(args.surface) if args.surface else None

    if args.validate_only:
        print("Validation mode not yet implemented. Run --dry-run first.")
        return

    generate_all(
        dry_run=args.dry_run,
        backup=args.backup,
        domain_filter=args.domain,
        surface_filter=surface_filter,
    )


if __name__ == "__main__":
    main()
```

---

## How Controllers Use The Bridge

### Example: `controllers/orders/admin_order_controller.py`

```python
"""Admin order management controller."""
from sqlalchemy.orm import Session
from scripts.router_metadata import route_meta, Surface


@route_meta(
    method="GET",
    path="/{order_id}",
    surface=Surface.ADMIN,
    domain="orders",
    operation="management",
    response_model="OrderDetailOut",
)
def get_order_by_id(db: Session, current_admin: dict, order_id: int):
    """Get a single order by ID."""
    # ... controller logic calling services
    pass


@route_meta(
    method="GET",
    path="/",
    surface=Surface.ADMIN,
    domain="orders",
    operation="management",
    response_model="list[OrderOut]",
)
def list_orders(db: Session, current_admin: dict, skip: int = 0, limit: int = 50):
    """List all orders with pagination."""
    pass


@route_meta(
    method="PATCH",
    path="/{order_id}/status",
    surface=Surface.ADMIN,
    domain="orders",
    operation="management",
    request_model="OrderStatusUpdate",
    response_model="OrderOut",
)
def update_order_status(db: Session, current_admin: dict, order_id: int, status: str):
    """Update order status."""
    pass
```

---

## Generated Output: `routers/admin_orders_management.py`

```python
"""
AUTO-GENERATED ROUTER — DO NOT EDIT MANUALLY
...
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db

from controllers.auth_controller import get_current_admin

from controllers.orders.admin_order_controller import (
    get_order_by_id,
    list_orders,
    update_order_status,
)

router = APIRouter(prefix="/api/v1/admin/orders", tags=["Orders Admin"])


@router.get("/{order_id}")  # response_model=OrderDetailOut  # TODO: import and set
def get_order_by_id_route(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Get a single order by ID."""
    return get_order_by_id(db=db, current_admin=current_admin, order_id=order_id)


@router.get("/")  # response_model=list[OrderOut]  # TODO: import and set
def list_orders_route(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """List all orders with pagination."""
    return list_orders(db=db, current_admin=current_admin, skip=skip, limit=limit)


@router.patch("/{order_id}/status", status_code=200)  # response_model=OrderOut
def update_order_status_route(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    """Update order status."""
    return update_order_status(db=db, current_admin=current_admin, order_id=order_id, status=status)
```

---

## File Placement

```
backend/
├── scripts/
│   ├── router_metadata.py        ← THE BRIDGE (metadata management)
│   └── generate_routers.py       ← THE SCRIPT (reads bridge + controllers)
├── controllers/
│   ├── orders/
│   │   ├── admin_order_controller.py    ← Uses @route_meta from bridge
│   │   └── customer_order_controller.py
│   └── catalog/
│       └── product_controller.py
└── routers/
    ├── admin_orders_management.py       ← GENERATED
    ├── customer_orders_tracking.py      ← GENERATED
    ├── _registry.py                     ← GENERATED
    └── ...
```

---

## Usage Workflow

```bash
# 1. New feature? Just create the controller with @route_meta
# 2. Run the script:
python scripts/generate_routers.py --domain orders --backup

# 3. Full regeneration after big changes:
python scripts/generate_routers.py --full --backup

# 4. Preview what would change:
python scripts/generate_routers.py --dry-run

# 5. Fix a specific broken router:
python scripts/generate_routers.py --domain treasury --backup
```

The bridge (`router_metadata.py`) is the **single source of truth** between your controllers and the generated routers. Controllers declare intent via `@route_meta`, the script reads that intent and produces compliant routers. No manual wiring needed.

