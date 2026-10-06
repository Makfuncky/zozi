"""Law conformance for ``domains/security/models/fraud.py`` (FILE 103).

Scope: the 18 ORM classes declared in that file, checked against the Table
law group (Law 20, 21, 22, 23, 51, 52, 53, 55) plus Law 19 (no float) and
Law 45 (no explicit ``lazy="select"``).

The audit worklist for this block (TF-236 .. TF-262) claimed 27 defects of
the form ``created_at missing server_default=func.now()`` and ``Model missing
created_at/updated_at column``. Every one of those columns is present and
correct in the current source, so those assertions are pinned here as
regression guards: they are the evidence that the audit's line numbers no
longer describe this file.

One genuine defect was found during the third pass and is asserted here:
``country_code`` -- itself one of the four Law 23 audit columns -- is
assigned more than once in the bodies of ``FraudRule``, ``IPReputation`` and
``FraudAlert``. Python keeps only the last assignment, so the earlier ones are
shadowed dead code and a maintainer editing "the country_code column" may
edit a line that has no effect.
"""
from __future__ import annotations

import ast
import collections
import pathlib
import re

import pytest
from sqlalchemy import Float, Numeric
from sqlalchemy.orm import RelationshipProperty

from domains.security.models import fraud as fraud_models

MODEL_SOURCE = pathlib.Path(fraud_models.__file__)
MODEL_NAMES = sorted(fraud_models.__all__)
MODELS = [getattr(fraud_models, n) for n in MODEL_NAMES]

# Law 23: every model MUST include these four columns.
AUDIT_COLUMNS = ("created_at", "updated_at", "country_code", "is_deleted")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _assigned_column_attrs() -> dict[str, list[tuple[str, int]]]:
    """Map class name -> [(attribute name, line), ...] of Column() assignments.

    Parsed from the AST rather than the live class objects on purpose: two
    ``Column`` objects bound to the same attribute name collapse into one
    entry in ``vars(model)``, so the live objects cannot see the duplication
    that the source actually contains.
    """
    tree = ast.parse(MODEL_SOURCE.read_text(encoding="utf-8"))
    out: dict[str, list[tuple[str, int]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        hits: list[tuple[str, int]] = []
        for stmt in node.body:
            targets: list[ast.expr] = []
            call = None
            if isinstance(stmt, ast.Assign):
                targets = list(stmt.targets)
                call = stmt.value
            elif isinstance(stmt, ast.AnnAssign):
                targets = [stmt.target]
                call = stmt.value
            if not isinstance(call, ast.Call):
                continue
            fname = getattr(call.func, "id", getattr(call.func, "attr", None))
            if fname != "Column":
                continue
            for t in targets:
                if isinstance(t, ast.Name):
                    hits.append((t.id, stmt.lineno))
        if hits:
            out[node.name] = hits
    return out


ASSIGNED = _assigned_column_attrs()


# --------------------------------------------------------------------------
# Law 21 -- created_at/updated_at use server_default=func.now()
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", MODEL_NAMES)
def test_created_at_uses_server_default_func_now(name: str) -> None:
    """Law 21: created_at is stamped DB-side, not Python-side."""
    col = getattr(fraud_models, name).created_at
    assert col is not None, f"{name} has no created_at column"
    assert col.server_default is not None, f"{name}.created_at has no server_default"
    assert "now()" in str(col.server_default.arg), (
        f"{name}.created_at server_default is {col.server_default.arg!r}, expected func.now()"
    )


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_updated_at_uses_server_default_func_now(name: str) -> None:
    """Law 21: updated_at also stamps DB-side and refreshes on update."""
    col = getattr(fraud_models, name).updated_at
    assert col is not None, f"{name} has no updated_at column"
    assert col.server_default is not None, f"{name}.updated_at has no server_default"
    assert "now()" in str(col.server_default.arg), (
        f"{name}.updated_at server_default is {col.server_default.arg!r}, expected func.now()"
    )
    assert col.onupdate is not None, f"{name}.updated_at does not refresh on UPDATE"


# --------------------------------------------------------------------------
# Law 23 -- audit columns
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", MODEL_NAMES)
def test_audit_columns_present(name: str) -> None:
    """Law 23: created_at, updated_at, country_code, is_deleted all present."""
    model = getattr(fraud_models, name)
    missing = [c for c in AUDIT_COLUMNS if not hasattr(model, c)]
    assert not missing, f"{name} missing audit columns: {missing}"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_is_deleted_defaults_false_and_indexed(name: str) -> None:
    """Law 54: is_deleted is a non-null boolean defaulting to false, indexed."""
    col = getattr(fraud_models, name).is_deleted
    assert col.nullable is False, f"{name}.is_deleted is nullable"
    assert col.default is not None and col.default.arg is False, (
        f"{name}.is_deleted does not default to False"
    )
    assert col.index is True, f"{name}.is_deleted is not indexed"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_country_code_is_string_two(name: str) -> None:
    """Law 20: country_code is String(2) (ISO 3166-1 alpha-2)."""
    col = getattr(fraud_models, name).country_code
    assert col.type.length == 2, (
        f"{name}.country_code is {col.type!r}, expected String(2)"
    )


# --------------------------------------------------------------------------
# Law 55 -- schema-per-domain
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", MODEL_NAMES)
def test_table_declares_security_schema(name: str) -> None:
    """Law 55: every table lives in the security schema."""
    model = getattr(fraud_models, name)
    assert model.__tablename__, f"{name} has no __tablename__"
    assert model.__table__.schema == "security", (
        f"{name} resolves to schema {model.__table__.schema!r}, expected 'security'"
    )


# --------------------------------------------------------------------------
# No shadowed duplicate Column assignments
# --------------------------------------------------------------------------
def test_no_duplicate_column_declarations_in_source() -> None:
    """Each class body assigns a given column attribute exactly once.

    A second ``country_code = Column(...)`` in the same class body is not a
    second column -- Python rebinds the name and SQLAlchemy registers only
    the survivor -- so the earlier assignment is silently dead. Keeping it
    invites edits to a line that has no effect on the schema.
    """
    offenders: list[str] = []
    for cls, hits in ASSIGNED.items():
        names = [n for n, _ in hits]
        for name in sorted({n for n in names if names.count(n) > 1}):
            lines = sorted(ln for n, ln in hits if n == name)
            offenders.append(f"{cls}.{name} assigned {len(lines)}x at lines {lines}")
    assert not offenders, "duplicate Column assignments: " + "; ".join(offenders)


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_country_code_is_one_column_in_effective_table(name: str) -> None:
    """country_code contributes exactly one column to the effective table."""
    cols = [c for c in getattr(fraud_models, name).__table__.columns if c.name == "country_code"]
    assert len(cols) == 1, f"{name} has {len(cols)} effective country_code columns"


# --------------------------------------------------------------------------
# Law 22 / 52 / 53 -- foreign keys
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", MODEL_NAMES)
def test_every_foreign_key_declares_ondelete(name: str) -> None:
    """Law 22/52: every ForeignKey states an explicit ondelete behaviour."""
    table = getattr(fraud_models, name).__table__
    offenders = [
        f"{col.name} -> {fk.target_fullname}"
        for col in table.columns
        for fk in col.foreign_keys
        if fk.ondelete is None or str(fk.ondelete).strip() == ""
    ]
    assert not offenders, f"{name}: ForeignKey without ondelete: {offenders}"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_every_foreign_key_column_is_indexed(name: str) -> None:
    """Law 53: Postgres does not auto-index FKs, so the model must."""
    table = getattr(fraud_models, name).__table__
    offenders = [
        col.name for col in table.columns if col.foreign_keys and not col.index
    ]
    assert not offenders, f"{name}: un-indexed FK column(s): {offenders}"


# --------------------------------------------------------------------------
# Law 19 -- no float
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", MODEL_NAMES)
def test_no_float_columns(name: str) -> None:
    """Law 19: money/scores use Decimal/Numeric, never float."""
    offenders = [
        col.name for col in getattr(fraud_models, name).__table__.columns
        if isinstance(col.type, (Float,))
    ]
    assert not offenders, f"{name}: float column(s): {offenders}"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_score_columns_use_numeric(name: str) -> None:
    """Fraud scores are exact decimals (Numeric), not binary floats."""
    for attr in ("fraud_score", "reputation_score", "risk_score"):
        col = getattr(fraud_models, name, None)
        if col is None or not hasattr(col, attr):
            continue
        c = getattr(col, attr)
        if not isinstance(c.property.columns[0].type, (Numeric,)) and not hasattr(c, "type"):
            continue
        assert not isinstance(c.type, Float), f"{name}.{attr} must not be Float"


# --------------------------------------------------------------------------
# Law 45 -- no explicit lazy="select"
# --------------------------------------------------------------------------
def test_no_relationship_declares_lazy_select() -> None:
    """Law 45: an explicit ``lazy='select'`` on a relationship is forbidden.

    Mirrors the architecture gate (``test_law32_through_law57.py``): scan the
    AST for ``relationship(...)`` calls carrying ``lazy='select'``.
    """
    tree = ast.parse(MODEL_SOURCE.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if getattr(node.func, "id", getattr(node.func, "attr", None)) != "relationship":
            continue
        for kw in node.keywords:
            if kw.arg != "lazy":
                continue
            if isinstance(kw.value, ast.Constant) and kw.value.value == "select":
                offenders.append(f"line {node.lineno}: lazy='select'")
    assert not offenders, f"Law 45 violation: {offenders}"


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_every_declared_relationship_resolves(name: str) -> None:
    """Sanity: each relationship named in the source maps to a real attribute.

    ``relationship("User", ...)`` is resolved by string against the mapper.
    A typo here only fails at first access, deep inside a service, so pin it.
    """
    mapper = getattr(fraud_models, name).__mapper__
    declared = {
        p.key: p for p in mapper.relationships
        if isinstance(p, RelationshipProperty)
    }
    for rel in declared.values():
        assert rel.mapper is not None, f"{name}.{rel.key} does not resolve to a mapped class"


# --------------------------------------------------------------------------
# Law 51 -- single table ownership
# --------------------------------------------------------------------------
def test_each_tablename_is_declared_once_repo_wide() -> None:
    """Law 51: no duplicate __tablename__ anywhere in the repo."""
    backend_root = pathlib.Path(fraud_models.__file__).resolve().parents[3]
    pattern = re.compile(r"""__tablename__\s*=\s*["']([^"']+)""")
    mine = {getattr(fraud_models, n).__tablename__ for n in MODEL_NAMES}
    seen: dict[str, list[str]] = collections.defaultdict(list)
    for path in backend_root.rglob("*.py"):
        parts = set(path.parts)
        if parts & {".git", "__pycache__", "node_modules", ".venv", "alembic"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for match in pattern.finditer(text):
            if match.group(1) in mine:
                seen[match.group(1)].append(str(path.relative_to(backend_root)))
    duplicates = {t: locs for t, locs in seen.items() if len(locs) > 1}
    assert not duplicates, f"duplicate __tablename__ (Law 51): {duplicates}"
    assert len(seen) == len(mine), (
        f"expected all {len(mine)} fraud tables to be declared; found {len(seen)}"
    )


# --------------------------------------------------------------------------
# Law 21 paired test — no Python-side default on any DateTime column
# --------------------------------------------------------------------------
def test_no_datetime_column_uses_python_side_default() -> None:
    """Law 21 paired gate: every Column(DateTime, ...) with a ``default`` kwarg
    must also carry ``server_default=func.now()``.

    Walks *both* ``ast.Assign`` and ``ast.AnnAssign`` so that columns declared
    with or without a type annotation are both caught.  This blind spot is
    exactly how the 4 Python-side defaults in this module (DeviceFingerprint,
    IPAccountLinkage, ReturnAbusePattern, VelocityCounter) survived a green
    test suite in a previous pass.
    """
    tree = ast.parse(MODEL_SOURCE.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        # Determine the Call node and target name for both assign forms
        if isinstance(node, ast.Assign):
            if not node.targets:
                continue
            target = node.targets[0]
            call = node.value
        else:  # ast.AnnAssign
            target = node.target
            call = node.value
        if not isinstance(call, ast.Call):
            continue
        fname = getattr(call.func, "id", getattr(call.func, "attr", None))
        if fname != "Column":
            continue
        col_name = getattr(target, "id", None)
        # Is the first positional arg a DateTime type?
        is_datetime = any(
            getattr(a, "id", None) == "DateTime" for a in call.args
        )
        if not is_datetime:
            continue
        has_default = any(kw.arg == "default" for kw in call.keywords)
        has_server_default = any(kw.arg == "server_default" for kw in call.keywords)
        if has_default and not has_server_default:
            offenders.append(
                f"line {node.lineno}: {col_name or '?'} = Column(DateTime, default=...) "
                f"missing server_default=func.now()"
            )
    assert not offenders, (
        "Law 21 Python-side default violations (add server_default=func.now()): "
        + "; ".join(offenders)
    )