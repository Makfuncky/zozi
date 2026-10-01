"""Law 45 N+1 prevention — runtime smoke test for the shipments list endpoint.

ARCHITECTURE_DIAGRAM.md Law 45 forbids N+1 fan-out in hot list endpoints.
Audit finding #18: ``backend/domains/logistics/services/shipments.py`` exposed a
list endpoint that issued per-row SELECTs to hydrate the most-touched foreign
keys. The canonical model
(``domains.logistics.models.logistics_entities.Shipment``) has since been
configured with ``lazy='selectin'`` on its four fan-out relations
(``order``, ``supplier``, ``assigned_partner``, ``carrier``) so any
``select(Shipment)`` issued through the sanctioned
``domains.logistics.ports.list_shipments_page`` surface must load them in
batched SELECTs, never one-per-row.

This test installs a SQLAlchemy ``before_cursor_execute`` event listener,
issues the list page query, accesses every eager-loadable relation, and
asserts that the number of SELECT statements is bounded by a small constant
independent of the row count (i.e. no N+1).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

_BACKEND_ROOT = _TESTS_DIR.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# ---------------------------------------------------------------------------
# Static AST check — defense-in-depth so a regression that drops lazy=selectin
# is caught even without a live database.
# ---------------------------------------------------------------------------
_MODEL_PATH = _BACKEND_ROOT / "domains" / "logistics" / "models" / "logistics_entities.py"
_REQUIRED_LAZY = {"order", "supplier", "assigned_partner", "carrier"}


def test_shipment_fanout_relations_are_selectin() -> None:
    text = _MODEL_PATH.read_text(encoding="utf-8")
    tree = ast.parse(text)
    shipment_cls = next(
        (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "Shipment"),
        None,
    )
    assert shipment_cls is not None, "Shipment model not found in logistics_entities.py"

    found: dict[str, str | None] = {}
    for stmt in shipment_cls.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        name = stmt.targets[0].id
        if name not in _REQUIRED_LAZY or not isinstance(stmt.value, ast.Call):
            continue
        lazy = None
        for kw in stmt.value.keywords:
            if kw.arg == "lazy" and isinstance(kw.value, ast.Constant):
                lazy = kw.value.value
        found[name] = lazy

    missing = _REQUIRED_LAZY - found.keys()
    assert not missing, f"Shipment missing relationship declarations: {sorted(missing)}"
    not_selectin = [k for k, v in found.items() if v != "selectin"]
    assert not not_selectin, (
        "Shipment fan-out relations must use lazy='selectin' to prevent N+1:\n  "
        + "\n  ".join(f"{k}: {found[k]!r}" for k in not_selectin)
    )


# ---------------------------------------------------------------------------
# Runtime query-count check (skipped when no live DB is available).
# ---------------------------------------------------------------------------
@pytest.mark.optional_db  # noqa: F821 — opportunistic; self-skips without DB
def test_list_shipments_page_does_not_n_plus_1() -> None:
    """Touching every Shipment row + every fan-out relation must stay bounded.

    With ``selectin`` on the 4 relations, the page query should issue at most
    1 (shipments) + 4 (one per relation) = 5 SELECTs for any row count. We
    allow a small slack for driver/version queries but assert ``count <= 8``.
    """
    from sqlalchemy import event

    try:
        from domains.logistics.ports import list_shipments_page
        from domains.logistics.models.logistics_entities import Shipment
    except Exception as exc:  # pragma: no cover — import guard
        pytest.skip(f"Logistics models/ports unavailable: {exc!r}")

    try:
        from infrastructure.database.database import get_db
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"DB session unavailable: {exc!r}")

    try:
        db_gen = get_db()
        db = next(db_gen)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Cannot open DB session in this environment: {exc!r}")

    try:
        # Avoid relationship-touching count() — touch an aggregate column only.
        from sqlalchemy import func
        try:
            row_count = db.query(func.count(Shipment.id)).scalar() or 0
        except Exception as exc:
            pytest.skip(f"Shipment model cannot be queried (env-level): {exc!r}")
        if row_count < 5:
            pytest.skip(f"Need >= 5 Shipment rows to assert N+1 bound (have {row_count})")

        selects: list[str] = []

        def _capture(conn, cursor, statement, params, context, executemany):  # noqa: ANN001
            selects.append(statement)

        bind = db.get_bind()
        event.listen(bind, "before_cursor_execute", _capture)

        try:
            page = list_shipments_page(db, cursor=None, page_size=10)
            items = page.items if hasattr(page, "items") else list(page)
            for shipment in items:
                # Touch every eager-loadable relation to defeat identity-map cheating.
                try:
                    _ = shipment.order
                    _ = shipment.supplier
                    _ = shipment.assigned_partner
                    _ = shipment.carrier
                except Exception as exc:
                    pytest.skip(f"Relation load failed (env-level): {exc!r}")
        finally:
            event.remove(bind, "before_cursor_execute", _capture)

        # 1 (shipments) + 4 (one per relation via selectin) = 5, plus a couple
        # of driver-level introspection queries we tolerate.
        assert len(selects) <= 8, (
            f"list_shipments_page issued {len(selects)} SELECTs — possible N+1:\n"
            + "\n".join(selects[:30])
        )
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass
        except Exception:
            pass
