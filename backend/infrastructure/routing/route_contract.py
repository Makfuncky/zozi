"""infrastructure.routing — HTTP route-contract decorators (platform layer).

NEW_STRUCTURE.md has no top-level ``core/`` package. The route-contract
decorators (get/post/put/delete/patch/route) are technical routing primitives
with zero business logic, so they live in the platform layer under
``infrastructure/routing`` rather than in any domain or module.

Controller modules import these metadata-only decorators to declare their HTTP
contract without importing FastAPI. The implementation is defined in
``infrastructure.routing.auto_router`` and re-exported here as the single,
stable import surface for controllers.
"""
from infrastructure.routing.auto_router import *  # noqa: F401,F403
from infrastructure.routing.auto_router import (  # noqa: F401
    delete,
    get,
    patch,
    post,
    put,
    route,
)
