"""Re-export shim: DB engine/session primitives via the exempt `data` layer.

Application layers (routers, controllers, services, utils, middleware, ...) must
not import `db.database` directly (forbidden edge / upward circuit). They import
through `data.db` instead, which is an exempt, cross-cutting layer.
"""

import db.database as _database

for _name in vars(_database):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_database, _name)

__all__ = [n for n in globals() if not n.startswith("_")]
