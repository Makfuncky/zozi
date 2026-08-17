# ZOZI Auto-Router

Single source of truth: `backend/routers/generated/auto_router.py`.

## Policy (decided 2026-08-11)

**The auto-router is the convention for NEW controllers only.**

- Existing hand-written routers in `backend/routers/*.py` (the ~200 legacy
  routers, websockets, country control-plane, aliases, etc.) **stay as-is** and
  continue to be auto-discovered by `main._load_routers()`.
- New HTTP-facing controller functions are tagged with `@route`/`@get`/...
  decorators; the generator emits a thin delegating router next to them.
- We do **not** mechanically convert the legacy routers. The legacy routers
  follow a different pattern (routers orchestrate and *share* controller
  functions across multiple files), so a controller function can map to several
  routes — incompatible with the one-function = one-route model. Converting
  them would require per-domain refactoring, which is out of scope.

This keeps the tool safe and in our control: nothing is guessed, and untouched
code never changes.

## How it works

1. Controllers import **only** the decorators from
   `routers.generated.auto_router` (a controller never imports FastAPI):

   ```python
   from routers.generated.auto_router import get, post, put, delete, patch, route
   from db.schemas import CouponCreate

   @post("/api/v1/coupons", deps=["db", "admin"], body=CouponCreate,
         response_model=CouponOut, status_code=201, tags=["coupons"])
   def create_coupon(code, discount_type, db, current_user) -> dict:
       ...
   ```

2. The generator reads those declarations from `controllers/**` via **AST only**
   (it never imports or executes a controller, so a broken controller cannot
   crash the scan).

3. It emits a thin FastAPI router that delegates to the controller function and
   writes it into the **surface folder** `backend/routers/` named
   `{surface}_{feature}_{domain}.py` (e.g. `public_commerce_coupons.py`), carrying
   the `AUTO-GENERATED` marker. The surface comes from the route path
   (`SURFACES` in `auto_router.py`); feature/domain come from the controller
   module — readable, no `gen_` prefix.

4. `main._load_routers()` globs `backend/routers/*.py` and includes every
   `router`, so generated routers are mounted automatically — **no central
   registry**.

## Migrating an existing controller (deliberate, lossless)

Migrating a hand-written router to the auto-router is opt-in and done one
controller at a time. It is safe ONLY when the generated router is a faithful,
lossless replacement of the hand-written one. Recipe (proven on the wishlist
pilot):

1. Read the controller **and** its hand-written router. Confirm the router does
   no non-trivial work the generator can't emit: auth adaptation
   (e.g. `current_user -> user_id`), `Query(ge=…, le=…)` constraints, and
   `response_model` Pydantic classes defined *inside the router*.
2. Make the controller decorator-friendly:
   - Accept `Depends`-injected args directly (`current_user: dict`, `db`) instead
     of deriving them in the router; move any adaptation (`_user_id`) into the
     controller.
   - Define the returned `response_model` (and view models) *in the controller
     module* so the generated file can re-import them.
   - Move validation that lived in `Query(...)` constraints into the controller
     (e.g. `limit = max(1, min(200, limit))`).
   - Add `@get`/`@post`/`@put`/`@patch`/`@delete` with `deps=["db","user"]`,
     `response_model`, `status_code`, `tags`.
3. Generate the router: `python routers/generated/auto_router.py --domain <name>`
   (dry-run first to inspect).
4. **Delete** the hand-written router — otherwise the same `(METHOD, path)` is
   registered twice and FastAPI errors.
5. Validate: `python routers/generated/auto_router.py --verify`, `py_compile`
   the generated file, and boot the app / run the route's tests.

Do **not** migrate controllers that: are shared across ≥2 routers or ≥2
surfaces (one decorator set can't express both mounts), define their own
`@router.*` (invisible to the AST scan), or contain `.commit()` without first
refactoring transaction ownership out. Coupon and wishlist are the reference
pilots.

## Contract (controller function arguments)

| Controller arg | Generated role |
|---|---|
| name inside `{...}` in the path | path param |
| name in `deps=[...]` | injected `Depends(...)` |
| name in `query=[...]` | `Query(...)` |
| the `body=` model | single `Body(...)` |
| remaining args on write methods | body fields (`Body(...)`) |
| remaining args on read methods | `Query(...)` |
| `**kwargs` (rest) | passed through as `**kwargs` |

Parameter defaults from the controller are preserved in the generated wrapper
(e.g. `limit: int = Query(200)`). Supported deps: `db`, `admin`, `user`,
`optional_user`, `background_tasks`, `request`.

## Commands

Run from `backend/`:

```bash
python routers/generated/auto_router.py                  # write routers/ (surface)
python routers/generated/auto_router.py --dry-run        # print to stdout, write nothing
python routers/generated/auto_router.py --check          # validate + summary, exit 1 on fail
python routers/generated/auto_router.py --verify        # ensure committed files match controllers
python routers/generated/auto_router.py --report         # print discovered routes
python routers/generated/auto_router.py --validate       # check existing routers for forbidden patterns
python routers/generated/auto_router.py --clean          # remove orphan generated files
python routers/generated/auto_router.py --domain coupons # one module substring
python routers/generated/auto_router.py --force          # allow routes colliding with existing routers
```

- `--verify` is the CI/pre-commit gate: it fails if any generated file is
  missing, drifted, or orphaned. Re-run the generator after any controller edit.
- Generated files carry the `AUTO-GENERATED` marker and are never written over a
  hand-written router (a file without the marker is left untouched).
- Collision detection skips a route only when it collides with a *hand-written*
  router. The generator's own previously-generated output is identified by the
  `AUTO-GENERATED` marker (not a filename prefix) and is excluded, so regeneration
  is idempotent. Use `--force` to emit colliding routes anyway.

## Architecture guardrails

Generated routers must only delegate to controllers. The validator forbids:

- `db.commit` / `session.commit` / `db.flush` / `session.flush`
- `from models import` / `from services import` / `from data.models import`

## Status

- `controllers/commerce/coupons_controller.py` (5 routes),
  `controllers/commerce/wishlist_controller.py` (4 routes), and
  `controllers/commerce/reviews_controller.py` (5 routes) are the pilots,
  generating `routers/public_commerce_coupons.py`,
  `routers/public_commerce_wishlist.py`, and `routers/public_commerce_reviews.py`,
  all verified through `--verify`, `py_compile`, and generated-router import.
  - Reviews notes: routes live under `/api/v1/reviews/*` (not `/api/v1/*`) to
    avoid colliding with `wishlist_controller`'s `GET /api/v1` and the products
    router's `GET /api/v1/products/{id}`. The `PUT /api/v1/reviews/{id}` route is
    marked `skip=True` because reviews are updated via the generic
    `commerce_write_service` dispatch, not a direct PUT (the tests expect 405).
  - Hand-written `routers/customer_reviews_review.py` and
    `routers/customer_wishlist_list.py` were deleted (lossless: replaced by the
    generated routers).
- All other domains remain hand-written and are not touched by this tool.
- `scripts/maintenance/gen_routers.py` is unrelated and is not used by this tool.
