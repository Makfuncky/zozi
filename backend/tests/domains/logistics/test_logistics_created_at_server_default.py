"""Law 21 + Law 6 — ``created_at`` must carry a DB-side ``server_default=now()``.

ARCHITECTURE_STACK.md Law 21 is explicit that the timestamp default is
**DB-side**, not Python-side:

  | 21 | Code Quality | Timestamps = server_default | created_at/updated_at use
      server_default=func.now() (DB-side), not Python-side. |

Law 6 makes Alembic the single source of truth for schema, so both halves have to
hold for the eight ``logistics`` tables owned by
``domains/logistics/models/logistics_entities.py``:

  1. the ORM column declares ``server_default=func.now()``; and
  2. the Alembic chain actually realises that default on a real PostgreSQL
     database, i.e. ``alembic upgrade head`` leaves ``logistics.<table>.created_at``
     with ``DEFAULT now()``.

Historically only (1) held. The model was corrected for audit TF-218..TF-225,
but the only ``op.create_table`` for these tables
(``20260806_0003_baseline_sync_orm_tables.py``) emitted ``created_at`` with no
``server_default`` — and for ``logistics.logistics_partners`` it omitted the
column entirely — so a database built from the migration chain alone had a
nullable, default-less ``created_at``. These tests are the paired verification
for that gap.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

_BACKEND_ROOT = _TESTS_DIR.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

_MODEL_PATH = _BACKEND_ROOT / "domains" / "logistics" / "models" / "logistics_entities.py"
_VERSIONS_DIR = _BACKEND_ROOT / "alembic" / "versions"

# tablename -> owning class in logistics_entities.py
MODEL_TABLES = {
    "logistics_category_pricing_rules": "LogisticsCategoryPricingRule",
    "logistics_partner_profiles": "LogisticsPartnerProfile",
    "logistics_partner_service_areas": "LogisticsPartnerServiceArea",
    "logistics_partners": "LogisticsPartner",
    "logistics_pricing_profiles": "LogisticsPricingProfile",
    "logistics_vehicle_rules": "LogisticsVehicleRule",
    "shipment_events": "ShipmentEvent",
    "shipments": "Shipment",
}
SCHEMA = "logistics"
_COLUMN = "created_at"

# The revision that owns the DB-side default for these eight tables.
LAW21_REVISION = "20261003_0001"


# ---------------------------------------------------------------------------
# 1. ORM half (Law 21)
# ---------------------------------------------------------------------------
def test_orm_created_at_declares_server_default() -> None:
    """Law 21 (ORM half): every logistics_entities model uses server_default."""
    tree = ast.parse(_MODEL_PATH.read_text(encoding="utf-8"))

    found: dict[str, bool] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        tablename = None
        has_default = False
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign) or len(stmt.targets) != 1:
                continue
            if not isinstance(stmt.targets[0], ast.Name):
                continue
            name = stmt.targets[0].id
            if name == "__tablename__" and isinstance(stmt.value, ast.Constant):
                tablename = stmt.value.value
            elif name == "created_at" and isinstance(stmt.value, ast.Call):
                has_default = any(kw.arg == "server_default" for kw in stmt.value.keywords)
        if tablename in MODEL_TABLES:
            found[tablename] = has_default

    missing = sorted(set(MODEL_TABLES) - set(found))
    assert not missing, f"logistics_entities.py no longer declares tables: {missing}"
    without = sorted(t for t, ok in found.items() if not ok)
    assert not without, (
        "Law 21: created_at must use server_default=func.now(), not a Python-side "
        f"default. Offending logistics tables: {without}"
    )


# ---------------------------------------------------------------------------
# 2. Alembic half (Law 6 + Law 21 DB-side)
# ---------------------------------------------------------------------------
def _revision_dag() -> dict[str, tuple[list[str | None], Path]]:
    """revision -> (down_revisions, file). ``down_revision`` may be a merge tuple."""
    revs: dict[str, tuple[list[str | None], Path]] = {}
    for path in sorted(_VERSIONS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        rev: str | None = None
        downs: list[str | None] = []

        def _record(name: str, value: ast.AST | None) -> None:
            nonlocal rev
            if value is None:
                return
            if name == "revision" and isinstance(value, ast.Constant):
                rev = value.value
            elif name == "down_revision":
                if isinstance(value, ast.Constant):
                    downs.append(value.value)
                elif isinstance(value, (ast.Tuple, ast.List, ast.Set)):
                    downs.extend(
                        el.value for el in value.elts if isinstance(el, ast.Constant)
                    )

        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                _record(node.target.id, node.value)
            elif isinstance(node, ast.Assign):
                for tgt in node.targets:
                    if isinstance(tgt, ast.Name):
                        _record(tgt.id, node.value)

        if rev:
            revs[rev] = (downs, path)
    return revs


def _revision_chain() -> list[Path]:
    """Migration files in dependency order (a parent always precedes its child).

    Deterministic Kahn topological sort over the ``down_revision`` graph so the
    result is stable regardless of filename ordering, and so a merge revision
    (``down_revision`` tuple) still yields a single linear application order.
    """
    revs = _revision_dag()

    indegree: dict[str, int] = {rev: 0 for rev in revs}
    children: dict[str, list[str]] = {rev: [] for rev in revs}
    for rev, (downs, _) in revs.items():
        for down in downs:
            if down in revs:
                indegree[rev] += 1
                children[down].append(rev)

    ready = sorted(r for r, deg in indegree.items() if deg == 0)
    order: list[Path] = []
    while ready:
        rev = ready.pop(0)
        order.append(revs[rev][1])
        for child in sorted(children[rev]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
        ready.sort()

    assert len(order) == len(revs), (
        "migration graph contains a cycle or an unresolvable down_revision: "
        f"ordered {len(order)} of {len(revs)}"
    )
    return order


def _module_constants(tree: ast.Module) -> dict[str, ast.AST]:
    """module-level ``NAME = <literal>`` bindings, so migrations that hoist
    table names / column names into constants are still read correctly."""
    consts: dict[str, ast.AST] = {}
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                consts[node.target.id] = node.value
        elif isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value
    return consts


def _literal(node: ast.AST | None, consts: dict[str, ast.AST], depth: int = 0):
    """Resolve ``Name`` -> constant (or tuple of constants). None when dynamic."""
    if node is None or depth > 5:
        return None
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in consts:
        return _literal(consts[node.id], consts, depth + 1)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        values = tuple(_literal(el, consts, depth + 1) for el in node.elts)
        if all(isinstance(v, str) for v in values):
            return values
    return None


def _is_now_expression(node: ast.AST | None, consts: dict[str, ast.AST] | None = None) -> bool:
    """True for ``sa.func.now()`` / ``sa.func.current_timestamp()`` / text('now()')."""
    if node is None:
        return False
    if consts and isinstance(node, ast.Name) and node.id in consts:
        return _is_now_expression(consts[node.id], consts)
    if isinstance(node, ast.Call):
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name in {"now", "current_timestamp"}:
            return True
        if node.args:
            literal = _literal(node.args[0], consts or {})
            if isinstance(literal, str):
                upper = literal.upper()
                return "NOW()" in upper or "CURRENT_TIMESTAMP" in upper
        for kw in node.keywords:
            if kw.arg == "text" and _is_now_expression(kw.value, consts):
                return True
    return False


def _column_server_default(
    col: ast.AST, consts: dict[str, ast.AST]
) -> tuple[str | None, ast.AST | None]:
    """(column_name, server_default node) for a ``sa.Column(...)`` call."""
    if not isinstance(col, ast.Call):
        return None, None
    name = _literal(col.args[0], consts) if col.args else None
    sd = None
    for kw in col.keywords:
        if kw.arg == "server_default":
            sd = kw.value
    return (name if isinstance(name, str) else None), sd


def _resolve_table(value, consts: dict[str, ast.AST]) -> str | None:
    if isinstance(value, (ast.AST, type(None))):
        value = _literal(value, consts)
    if not isinstance(value, str):
        return None
    name = value.split(".")[-1]
    return name if name in MODEL_TABLES else None


_BATCH_TABLE_BINDING = "__a08_batch_table__"


def _collect_calls(
    node: ast.AST,
    consts: dict[str, ast.AST],
    local: dict[str, ast.AST],
    out: list[tuple[ast.Call, dict[str, ast.AST]]],
) -> None:
    """Flatten a migration body to ``(call, bindings)`` pairs.

    Two idioms are resolved so the scan does not silently miss them:

    * ``for table in TARGET_TABLES: ...`` — the loop variable is bound to each
      element of the resolved constant tuple, one pass per element;
    * ``with op.batch_alter_table(table) as batch_op:`` — the table is injected as
      ``__a08_batch_table__`` so ``batch_op.alter_column("created_at", ...)``,
      which carries no table reference of its own, still resolves.
    """
    if isinstance(node, ast.For):
        var = node.target.id if isinstance(node.target, ast.Name) else None
        values = _literal(node.iter, {**consts, **local}) if var else None
        if var and isinstance(values, tuple):
            for value in values:
                child = dict(local)
                child[var] = ast.Constant(value=value)
                for stmt in node.body + node.orelse:
                    _collect_calls(stmt, consts, child, out)
            return

    if isinstance(node, (ast.With, ast.AsyncWith)):
        child = local
        for item in node.items:
            call = item.context_expr
            if (
                isinstance(call, ast.Call)
                and getattr(call.func, "attr", None) in {"batch_alter_table", "alter_table"}
                and call.args
            ):
                tbl = _resolve_table(call.args[0], {**consts, **local})
                if tbl:
                    child = dict(local)
                    child[_BATCH_TABLE_BINDING] = ast.Constant(value=tbl)
        for stmt in node.body:
            _collect_calls(stmt, consts, child, out)
        return

    if isinstance(node, ast.Call):
        out.append((node, local))

    for child_node in ast.iter_child_nodes(node):
        _collect_calls(child_node, consts, local, out)


def _chain_created_at_defaults() -> dict[str, bool]:
    """tablename -> does the chain leave ``created_at`` with DEFAULT now()?

    Statements are applied in chain order and the last one wins, which is the
    state a database is actually left in after ``alembic upgrade head``.
    """
    state: dict[str, bool] = {}
    targets = set(MODEL_TABLES)

    for path in _revision_chain():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        consts = _module_constants(tree)

        # Only ``upgrade()`` describes the state a database is left in after
        # ``alembic upgrade head``; ``downgrade()`` intentionally walks the
        # column back and must not be read as the resulting schema.
        upgrade_fn = next(
            (
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "upgrade"
            ),
            None,
        )
        scope_nodes = (
            upgrade_fn.body
            if upgrade_fn is not None
            else [
                node
                for node in tree.body
                if not (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "downgrade"
                )
            ]
        )

        calls: list[tuple[ast.Call, dict[str, ast.AST]]] = []
        for stmt in scope_nodes:
            _collect_calls(stmt, consts, {}, calls)

        for node, local in calls:
            scope = {**consts, **local}
            attr = getattr(node.func, "attr", None)

            if attr == "create_table" and node.args:
                tbl = _resolve_table(node.args[0], scope)
                if not tbl:
                    continue
                matched = False
                for arg in node.args[1:]:
                    col_name, sd = _column_server_default(arg, scope)
                    if col_name == _COLUMN:
                        state[tbl] = _is_now_expression(sd, scope)
                        matched = True
                if not matched:
                    # table created without created_at -> no default present
                    state[tbl] = False

            elif attr == "add_column" and len(node.args) >= 2:
                tbl = _resolve_table(node.args[0], scope)
                if not tbl:
                    continue
                col_name, sd = _column_server_default(node.args[1], scope)
                if col_name == _COLUMN:
                    state[tbl] = _is_now_expression(sd, scope)

            elif attr in {"alter_column", "column"}:
                tbl = None
                col_name = None
                sd = None
                for arg in node.args:
                    value = _literal(arg, scope)
                    if value == _COLUMN:
                        col_name = value
                    else:
                        tbl = tbl or _resolve_table(arg, scope)
                for kw in node.keywords:
                    value = _literal(kw.value, scope)
                    if kw.arg in {"table_name", "table"}:
                        tbl = tbl or _resolve_table(kw.value, scope)
                    elif kw.arg == "column_name":
                        col_name = value
                    elif kw.arg == "server_default":
                        sd = kw.value
                if tbl is None:
                    bound = _literal(scope.get(_BATCH_TABLE_BINDING), scope)
                    tbl = bound if bound in MODEL_TABLES else None
                if tbl and col_name == _COLUMN:
                    # ``server_default=None`` explicitly removes the default.
                    state[tbl] = _is_now_expression(sd, scope)

            elif attr == "execute" and node.args:
                raw = _literal(node.args[0], scope)
                if not isinstance(raw, str):
                    continue
                sql = raw.upper()
                if "SET DEFAULT" not in sql or "CREATED_AT" not in sql:
                    continue
                for tbl in targets:
                    if f"{SCHEMA}.{tbl.upper()}" in sql or f'"{SCHEMA}"."{tbl.upper()}"' in sql:
                        state[tbl] = "NOW()" in sql or "CURRENT_TIMESTAMP" in sql

    return state


def test_alembic_chain_realises_created_at_server_default() -> None:
    """Law 6 + Law 21 (schema half): 'alembic upgrade head' must set DEFAULT now()."""
    state = _chain_created_at_defaults()

    unaddressed = sorted(set(MODEL_TABLES) - set(state))
    assert not unaddressed, (
        "Law 6/Law 21: no Alembic revision creates or defaults "
        f"logistics.<table>.created_at for {unaddressed}. Alembic is the schema "
        "source of truth, so the ORM's server_default=func.now() is never "
        "realised in the database built from the chain."
    )
    without = sorted(t for t, ok in state.items() if not ok)
    assert not without, (
        "Law 21 (DB-side): 'alembic upgrade head' leaves logistics.<table>.created_at "
        f"without DEFAULT now() for {without}. Add a migration that sets "
        "server_default=sa.func.now() on those columns."
    )


def test_migration_chain_is_topologically_ordered() -> None:
    """Law 6: every revision in the chain is reachable from a root, no cycles."""
    revs = _revision_dag()
    order = _revision_chain()
    assert len(order) == len(revs), (
        f"expected every one of {len(revs)} revisions to be ordered, got {len(order)}"
    )
    # The Law 21 revision that owns this file's DB-side default must be part of
    # the applied chain, not an orphan branch.
    assert LAW21_REVISION in revs, (
        f"revision {LAW21_REVISION} is missing from alembic/versions"
    )
    assert revs[LAW21_REVISION][0] and all(
        d in revs for d in revs[LAW21_REVISION][0] if d
    ), f"{LAW21_REVISION} has an unresolved down_revision"


# ---------------------------------------------------------------------------
# 3. Live catalog (Law 21 verified against the running database)
# ---------------------------------------------------------------------------
def test_live_catalog_created_at_defaults_to_now() -> None:
    """Every logistics.created_at column in the live catalog carries DEFAULT now()."""
    import sqlalchemy as sa

    from infrastructure.database.database import engine

    with engine.connect() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT table_name, column_default FROM information_schema.columns "
                "WHERE table_schema = :schema AND column_name = :col "
                "AND table_name = ANY(CAST(:names AS text[])) ORDER BY table_name"
            ),
            {"schema": SCHEMA, "col": _COLUMN, "names": sorted(MODEL_TABLES)},
        ).fetchall()

    seen = {name: default for name, default in rows}
    assert set(seen) == set(MODEL_TABLES), (
        "live catalog is missing logistics created_at columns: "
        f"{sorted(set(MODEL_TABLES) - set(seen))}"
    )
    without_default = sorted(n for n, d in seen.items() if d is None)
    assert not without_default, f"catalog default missing on: {without_default}"
    not_now = sorted(n for n, d in seen.items() if "now()" not in str(d).lower())
    assert not_now == [], f"catalog default is not now() on: {not_now}"
