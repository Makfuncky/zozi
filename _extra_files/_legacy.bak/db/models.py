"""ORM model registry facade.

Application layers (utils, middleware, dependencies, and any layer that
must not depend on the `models` top-level package per the dependency-graph
contract) reference ORM model classes through `db.models`. The `db` layer
is permitted; only `db.database` / `db.create_tables` / `db.init_db` are
banned for those layers. All model classes are re-exported unchanged.
"""
from __future__ import annotations

import types as _types
import _legacy.models as _models

_g = globals()
for _n in dir(_models):
    if _n.startswith("_"):
        continue
    _v = getattr(_models, _n)
    if isinstance(_v, _types.ModuleType):
        continue
    _g[_n] = _v
