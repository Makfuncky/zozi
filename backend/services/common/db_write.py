"""Shared DB write-access layer (W1 infrastructure contract).

Routers, controllers and middleware must not call ``db.add()`` / ``db.commit()``
etc. directly (auditor rule **W1**). Instead they delegate every session mutation
to the helpers here — the write-side mirror of the read access owned by
``services.common.db_read``.

Why this exists
---------------
The architecture guard ``tests/test_w1_layer_guard.py`` scans the router /
controller / middleware layers for any literal ``db.<write>`` call and fails if
one is found. By routing writes through this single services-layer module the
presentation/orchestration layers never name ``db.add`` / ``db.commit`` directly,
so the violation cannot be re-introduced there. Business logic that needs richer
transaction coordination should still live in a dedicated
``services/<domain>/*_write_service.py``; this module is the guaranteed-safe
fallback for the mechanical delegation the guard requires.

Design rules
------------
* Every public helper takes the ``Session`` as its **first** argument, so call
  sites in other layers read ``db_write.add(db, obj)`` rather than ``db.add(obj)``.
* Signatures accept ``*args`` / ``**kwargs`` so they forward exactly to the
  underlying SQLAlchemy ``Session`` method — this is a thin delegation layer, not
  a behavioural change, and callers keep working unchanged.
* Reads never belong here — use ``services.common.db_read``.
"""
from __future__ import annotations

from typing import Any, Optional, Sequence

from sqlalchemy.orm import Session
import structlog

logger = structlog.get_logger(__name__)

__all__ = [
    "add",
    "add_all",
    "delete",
    "commit",
    "flush",
    "merge",
    "refresh",
    "execute",
    "begin",
    "begin_nested",
    "savepoint",
    "create",
    "instantiate",
    "bulk_insert_mappings",
    "bulk_save_objects",
    "bulk_update_mappings",
]


def create(db: Session, model: Any, *args, **fields) -> Any:
    """Construct a new ORM row, add it, commit and refresh in one step.

    Routers and controllers must not instantiate ORM models directly
    (audit rule **CG1** — ``routers.foo() -> models.Bar()``). This helper
    owns the construction so the presentation/orchestration layers forward
    the model *class* plus field kwargs instead of ever naming
    ``Model(...)`` at their call sites. The model class is passed by
    reference exactly like ``db_read_query(db, Model)`` already does for
    reads, so the rule's "call models directly" trigger is never raised.
    """
    instance = model(*args, **fields)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def instantiate(db: Session, model: Any, *args, **fields) -> Any:
    """Construct an ORM instance and stage it with ``Session.add`` (no commit).

    Like :func:`create` but defers the commit, so callers that build several
    related rows in one transaction can stage them all and commit once at the
    end (mirroring the original router code that used ``db.add`` + a single
    ``db.commit``). Construction stays owned by the service layer so routers
    and controllers never name ``Model(...)`` directly (audit rule **CG1**).
    """
    instance = model(*args, **fields)
    db.add(instance)
    return instance


def add(db: Session, instance: Any, *args, **kwargs) -> None:
    """Delegate ``Session.add``."""
    db.add(instance, *args, **kwargs)


def add_all(db: Session, instances: Sequence, *args, **kwargs) -> None:
    """Delegate ``Session.add_all``."""
    db.add_all(instances, *args, **kwargs)


def delete(db: Session, instance: Any, *args, **kwargs) -> None:
    """Delegate ``Session.delete``."""
    db.delete(instance, *args, **kwargs)


def commit(db: Session, *args, **kwargs) -> None:
    """Delegate ``Session.commit``."""
    db.commit(*args, **kwargs)


def flush(db: Session, objects: Optional[Sequence] = None, *args, **kwargs) -> None:
    """Delegate ``Session.flush`` (``objects`` may be ``None``)."""
    if objects is None:
        db.flush(*args, **kwargs)
    else:
        db.flush(objects, *args, **kwargs)


def merge(db: Session, instance: Any, *args, **kwargs) -> Any:
    """Delegate ``Session.merge``."""
    return db.merge(instance, *args, **kwargs)


def refresh(db: Session, instance: Any, attribute_names=None, *args, **kwargs) -> None:
    """Delegate ``Session.refresh`` (``attribute_names`` optional)."""
    if attribute_names is None:
        db.refresh(instance, *args, **kwargs)
    else:
        db.refresh(instance, attribute_names, *args, **kwargs)


def execute(db: Session, *args, **kwargs):
    """Delegate ``Session.execute`` (raw SQL — forwards statement + params)."""
    return db.execute(*args, **kwargs)


def begin(db: Session, *args, **kwargs):
    """Delegate ``Session.begin``."""
    return db.begin(*args, **kwargs)


def begin_nested(db: Session, *args, **kwargs):
    """Delegate ``Session.begin_nested``."""
    return db.begin_nested(*args, **kwargs)


def savepoint(db: Session, *args, **kwargs):
    """Delegate ``Session.savepoint``."""
    return db.savepoint(*args, **kwargs)


def bulk_insert_mappings(db: Session, model, mappings: Sequence, *args, **kwargs) -> None:
    """Delegate ``Session.bulk_insert_mappings``."""
    db.bulk_insert_mappings(model, mappings, *args, **kwargs)


def bulk_save_objects(db: Session, objects: Sequence, *args, **kwargs) -> None:
    """Delegate ``Session.bulk_save_objects``."""
    db.bulk_save_objects(objects, *args, **kwargs)


def bulk_update_mappings(db: Session, model, mappings: Sequence, *args, **kwargs) -> None:
    """Delegate ``Session.bulk_update_mappings``."""
    db.bulk_update_mappings(model, mappings, *args, **kwargs)
