"""Diagnose mapper configuration failures (test-harness blocker).

The uncommitted model refactor removed ForeignKey declarations from several
child columns but only updated the child-side relationship (e.g.
``Product.supplier`` got explicit ``foreign_keys=[supplier_id]``) while the
parent-side relationships (``User.products``, ``User.addresses``, ...) still
declare a plain ``primaryjoin`` with no ``foreign_keys``.  SQLAlchemy then
cannot determine the foreign side of the join during ``configure_mappers``.

This script reports every failing relationship one at a time.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

import db.base  # noqa: E402

import data.models  # noqa: E402  (registers every model)

try:
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    print("MAPPER CONFIG OK")
except Exception as exc:
    print("MAPPER ERROR:", type(exc).__name__)
    print(str(exc)[:600])
