"""Helpers for writing idempotent Alembic migrations.

When the baseline migration materialises the full ORM schema, every later
migration must be a no-op-safe delta rather than a re-creation. These
``safe_*`` wrappers forward to the matching ``op`` call only when the target
object is absent (or present, for drops), so the whole chain is reproducible
from a clean database while still applying genuine deltas (columns / indexes
/ constraints) on top.

Invocation style (produced by the idempotency patcher)::

    op.create_table("users", ...)   ->  safe_create_table(op, "users", ...)
    op.add_column("t", col)         ->  safe_add_column(op, "t", col)
    op.create_index("i", "t", ...)  ->  safe_create_index(op, "i", "t", ...)
"""

from sqlalchemy import inspect


def _inspector(op_obj):
    return inspect(op_obj.get_bind())


def _table_names(op_obj):
    return _inspector(op_obj).get_table_names(schema=None)


def _index_names(op_obj, table_name: str):
    try:
        return {idx["name"] for idx in _inspector(op_obj).get_indexes(table_name)}
    except Exception:
        return set()


def _column_names(op_obj, table_name: str):
    try:
        return {col["name"] for col in _inspector(op_obj).get_columns(table_name)}
    except Exception:
        return set()


def _constraint_names(op_obj, table_name: str):
    names = set()
    try:
        for fk in _inspector(op_obj).get_foreign_keys(table_name):
            names.add(fk["name"])
    except Exception:
        pass
    try:
        for ck in _inspector(op_obj).get_check_constraints(table_name or ""):
            names.add(ck["name"])
    except Exception:
        pass
    try:
        for uc in _inspector(op_obj).get_unique_constraints(table_name):
            names.add(uc["name"])
    except Exception:
        pass
    return names


def table_exists(op_obj, table_name: str, schema: str | None = None) -> bool:
    return table_name in _table_names(op_obj)


def column_exists(op_obj, table_name: str, column_name: str) -> bool:
    return column_name in _column_names(op_obj, table_name)


def index_exists(op_obj, index_name: str, table_name: str) -> bool:
    return index_name in _index_names(op_obj, table_name)


def constraint_exists(op_obj, table_name: str, constraint_name: str) -> bool:
    return constraint_name in _constraint_names(op_obj, table_name)


def safe_create_table(op_obj, table_name: str, *args, **kwargs):
    if not table_exists(op_obj, table_name, schema=kwargs.get("schema")):
        op_obj.create_table(table_name, *args, **kwargs)


def safe_drop_table(op_obj, table_name: str, **kwargs):
    if table_exists(op_obj, table_name, schema=kwargs.get("schema")):
        op_obj.drop_table(table_name, **kwargs)


def safe_create_index(op_obj, indexname, tablename, *cols, **kwargs):
    if not index_exists(op_obj, indexname, tablename):
        op_obj.create_index(indexname, tablename, *cols, **kwargs)


def safe_drop_index(op_obj, indexname, table_name, **kwargs):
    if index_exists(op_obj, indexname, table_name):
        op_obj.drop_index(indexname, table_name, **kwargs)


def safe_add_column(op_obj, tablename, column, schema=None, **kw):
    col_name = getattr(column, "name", None)
    if col_name is not None and column_exists(op_obj, tablename, col_name):
        return
    op_obj.add_column(tablename, column, schema=schema, **kw)


def safe_drop_column(op_obj, tablename, columnname, schema=None, **kw):
    if column_exists(op_obj, tablename, columnname):
        op_obj.drop_column(tablename, columnname, schema=schema, **kw)


def safe_create_foreign_key(op_obj, constraintname, sourcetable, targettable, local_cols, remote_cols, **kw):
    existing = {
        fk.get("name") for fk in _inspector(op_obj).get_foreign_keys(sourcetable)
    }
    if constraintname in existing:
        return
    op_obj.create_foreign_key(
        constraintname, sourcetable, targettable, local_cols, remote_cols, **kw
    )


def safe_drop_constraint(op_obj, constraintname, table_name, type_=None, **kw):
    if constraint_exists(op_obj, table_name, constraintname):
        op_obj.drop_constraint(constraintname, table_name, type_=type_, **kw)
