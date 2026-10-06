"""Law 21 / Law 20 / Law 23 / Law 55 compliance gate for
``backend/domains/comms/models/communication.py``.

Audit block FILE 75 (``07_tables_fields``, nature ``db``) raised 25 findings of
two shapes against this file:

* ``created_at missing server_default=func.now() (Law 21)``
* ``User-facing table missing country_code column (Law 5, 20)``

This module adjudicates the PATTERN rather than the individual line numbers the
audit emitted. ARCHITECTURE_STACK.md Law 21 reads:

    created_at/updated_at use server_default=func.now() (DB-side), not Python-side.

so the test asserts, for every ORM class declared in ``communication.py``, that
its ``created_at`` and ``updated_at`` columns carry a DB-side
``server_default=func.now()`` and do NOT carry a Python-side ``default=``.

Law 20 (``country_code`` is always ``String(2)`` ISO 3166-1 alpha-2) and Law 23
(``created_at``/``updated_at``/``country_code``/``is_deleted`` on every model)
are asserted in the same pass because the audit named them on the same classes.

Law 55 (``__table_args__ = {"schema": "comms"}``) is asserted too: ARCH §8
records that the ``communication`` schema was renamed to ``comms`` by migration
``20260822_communication_to_comms_schema``, so a model still declaring
``schema="communication"`` would be a real defect. Every table in this file must
land in ``comms``.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import String  # noqa: E402

from domains.comms.models import communication as communication_models  # noqa: E402

COMMS_SCHEMA = "comms"
AUDIT_COLUMNS = ("created_at", "updated_at", "country_code", "is_deleted")


def _declared_classes() -> list:
    """Every ORM class actually declared in communication.py.

    Filtered on ``__module__`` so imported re-exports (CountryConfig) are not
    attributed to this file, and on ``__table__`` so plain helper classes are
    skipped.
    """
    return [
        obj
        for name in dir(communication_models)
        for obj in [getattr(communication_models, name)]
        if isinstance(obj, type)
        and obj.__module__ == communication_models.__name__
        and hasattr(obj, "__table__")
    ]


def _class_names() -> list[str]:
    return sorted(c.__name__ for c in _declared_classes())


def test_file_declares_the_expected_models():
    """Guard the enumeration itself so the gates below cannot silently pass on
    an empty model list."""
    names = _class_names()
    assert len(names) == 20, f"expected 20 ORM classes, found {len(names)}: {names}"
    for expected in ("Notification", "FAQ", "ProxyChannel", "InternalEmail", "MaskedMessage"):
        assert expected in names, f"{expected} missing from communication.py: {names}"


def test_created_at_uses_server_default_not_python_default():
    """Law 21 — created_at must be populated DB-side via server_default=func.now().

    A Python-side ``default=`` is explicitly forbidden by Law 21 ("not
    Python-side"): it stamps the application host's clock, so it drifts under
    clock skew and is invisible to any writer that is not this ORM.
    """
    offenders = []
    for cls in _declared_classes():
        col = cls.__table__.c.get("created_at")
        if col is None:
            offenders.append(f"{cls.__name__}.created_at: column absent")
            continue
        if col.server_default is None:
            offenders.append(f"{cls.__name__}.created_at: server_default is None")
        elif "now" not in str(col.server_default.arg).lower():
            offenders.append(
                f"{cls.__name__}.created_at: server_default is "
                f"{col.server_default.arg!r}, expected now()"
            )
        if col.default is not None:
            offenders.append(
                f"{cls.__name__}.created_at: carries Python-side default="
                f"{col.default!r} alongside the server_default (Law 21)"
            )
    assert not offenders, (
        f"{len(offenders)} created_at columns violate Law 21. Offenders:\n  "
        + "\n  ".join(offenders)
    )


def test_updated_at_uses_server_default_not_python_default():
    """Law 21 — updated_at must be populated DB-side via server_default=func.now().

    Same rule as created_at. onupdate=func.now() is retained (it is what makes
    the UPDATE path stamp DB-side) but it does not substitute for the
    server_default on INSERT.
    """
    offenders = []
    for cls in _declared_classes():
        col = cls.__table__.c.get("updated_at")
        if col is None:
            offenders.append(f"{cls.__name__}.updated_at: column absent")
            continue
        if col.server_default is None:
            offenders.append(f"{cls.__name__}.updated_at: server_default is None")
        elif "now" not in str(col.server_default.arg).lower():
            offenders.append(
                f"{cls.__name__}.updated_at: server_default is "
                f"{col.server_default.arg!r}, expected now()"
            )
        if col.default is not None:
            offenders.append(
                f"{cls.__name__}.updated_at: carries Python-side default="
                f"{col.default!r} alongside the server_default (Law 21)"
            )
    assert not offenders, (
        f"{len(offenders)} updated_at columns violate Law 21. Offenders:\n  "
        + "\n  ".join(offenders)
    )


def test_every_model_carries_country_code_string2():
    """Law 20 + Law 23 — country_code is String(2) on every model.

    ``country_code`` reaches a model either by explicit declaration or through
    ``TenantMixin``; both satisfy the law, so the assertion is made against the
    mapped table rather than the class body.
    """
    offenders = []
    for cls in _declared_classes():
        table = cls.__table__
        col = table.c.get("country_code")
        if col is None:
            offenders.append(f"{cls.__name__} ({table.schema}.{table.name}): country_code absent")
            continue
        if not isinstance(col.type, String) or col.type.length != 2:
            offenders.append(
                f"{cls.__name__} ({table.schema}.{table.name}): country_code is "
                f"{col.type!r}, expected String(2)"
            )
    assert not offenders, (
        f"{len(offenders)} models violate Law 20. Offenders:\n  " + "\n  ".join(offenders)
    )


def test_every_model_carries_the_four_audit_columns():
    """Law 23 — created_at, updated_at, country_code, is_deleted on every model."""
    offenders = []
    for cls in _declared_classes():
        table = cls.__table__
        missing = [c for c in AUDIT_COLUMNS if c not in table.c]
        if missing:
            offenders.append(f"{cls.__name__} ({table.schema}.{table.name}): missing {missing}")
    assert not offenders, (
        f"{len(offenders)} models violate Law 23. Offenders:\n  " + "\n  ".join(offenders)
    )


def test_every_table_is_in_the_comms_schema():
    """Law 55 + Law 51 — every table declares __table_args__ {'schema': 'comms'}.

    ARCH §8: the ``communication`` schema was renamed to ``comms``. A model here
    still pointing at ``communication`` would resolve against a schema that no
    longer exists, so the schema name is asserted exactly.
    """
    offenders = []
    for cls in _declared_classes():
        table = cls.__table__
        if table.schema != COMMS_SCHEMA:
            offenders.append(f"{cls.__name__}: __tablename__ = {table.name!r}, schema = {table.schema!r}")
    assert not offenders, (
        f"{len(offenders)} models do not declare __table_args__ "
        f"{{'schema': '{COMMS_SCHEMA}'}}. Offenders:\n  " + "\n  ".join(offenders)
    )


def test_no_table_is_declared_twice_across_the_comms_model_package():
    """Law 51 — a table is owned by exactly one class in exactly one file.

    ``communication.py`` is a sibling of ``chat.py`` and
    ``communication_schema_models.py``; a duplicated ``__tablename__`` sharing
    one ``MetaData`` is a runtime ``InvalidRequestError`` at mapper
    configuration, so the whole package is checked, not just this file.
    """
    from infrastructure.database.base import Base

    # Importing the package registers every comms model on Base.metadata.
    import domains.comms.models  # noqa: F401

    owners = {}
    for full_name in Base.metadata.tables:
        schema, _, table_name = full_name.partition(".")
        if schema != COMMS_SCHEMA:
            continue
        owners.setdefault(table_name, []).append(schema)

    duplicated = {t: v for t, v in owners.items() if len(v) > 1}
    assert not duplicated, (
        f"{len(duplicated)} tables declared more than once in schema "
        f"{COMMS_SCHEMA!r} (Law 51): {duplicated}"
    )


def test_faq_created_at_is_stamped_by_the_database():
    """Targeted regression for the single REAL finding in audit block FILE 75.

    ``FAQ.created_at`` was the one audit column in this file that used a
    Python-side ``default=utcnow`` with no ``server_default``. This test asserts
    the DB is the stamper by inspecting the compiled DDL, so it fails against the
    old declaration and passes against the corrected one.
    """
    from sqlalchemy.schema import CreateTable
    from sqlalchemy.dialects import postgresql

    table = communication_models.FAQ.__table__
    ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
    created_at_line = next(
        (ln.strip() for ln in ddl.splitlines() if ln.strip().startswith("created_at")),
        None,
    )
    assert created_at_line is not None, f"created_at not rendered in DDL:\n{ddl}"
    assert "DEFAULT now()" in created_at_line, (
        "FAQ.created_at must be stamped DB-side (Law 21); compiled DDL line is "
        f"{created_at_line!r}"
    )
    assert "PRIMARY KEY" not in created_at_line, "sanity: parsed the wrong DDL line"
