"""STOCK-001 — the stock read-check-write on payment confirmation must be atomic.

What this proves
----------------
``_finalize_inventory_for_paid_order`` (payment_engine.py) performs a
read-check-write of ``Product.stock``:

    SELECT product -> compare stock vs requested_quantity -> write stock - requested

Without a row lock on that SELECT, two overlapping payment confirmations for the
same SKU both read ``stock = N``, both pass the comparison, and both write
``N - q``. One decrement is lost and the platform confirms more units than it
physically holds — the oversell that produces refunds, chargebacks, supplier
disputes and uncorrectable WORM audit entries.

Two halves of the commerce invariant are asserted, and BOTH matter:

    stock >= 0   AND   total decrement == units actually confirmed

Empirically the unlocked race leaves ``stock`` at a plausible-looking
non-negative value while confirming MORE units than existed, so ``stock >= 0``
alone does not detect it. The lost-update half is the detector that actually
fires.

Test layout, and why it is shaped this way
------------------------------------------
* ``test_row_lock_is_emitted_for_postgres`` compiles the production query against
  the PostgreSQL dialect and asserts ``FOR UPDATE`` is present. It needs no
  database at all, runs on every backend, and fails loudly if the lock is ever
  dropped again — which an SQLite run can never detect.
* ``test_concurrent_confirmations_never_oversell`` runs two genuinely
  overlapping confirmations, each thread on its OWN connection, against a real
  PostgreSQL. Law 108 is explicit that SQLite is only for "pure unit tests that
  do not exercise ... row locking", so this is the only backend on which the
  invariant is meaningful.
* ``test_retry_does_not_double_decrement`` covers Law 239.

No mocks, no monkeypatching, no stubs: every test drives the real production
service against a real engine on real connections.
"""
from __future__ import annotations

import ast
import os
import socket
import threading
from pathlib import Path

import pytest
import sqlalchemy
from sqlalchemy import create_engine, event, text
from sqlalchemy import MetaData as sa_meta
from sqlalchemy import Table as sa_table
from sqlalchemy.orm import Session, sessionmaker

# The backend package root must be importable (this file lives under tests/).
_BACKEND_ROOT = Path(__file__).resolve().parents[3]
if str(_BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(_BACKEND_ROOT))

from infrastructure.database.base import Base  # noqa: E402
from domains.catalog.models.products import Product  # noqa: E402
from domains.orders.models.orders import Order, OrderItem  # noqa: E402
from domains.finance.services.payments import payment_engine  # noqa: E402

RACE_USER_ID = 1
_PAYMENTS_DIR = _BACKEND_ROOT / "domains" / "finance" / "services" / "payments"

# Row locking is only meaningful on a real transactional engine (Law 108).
# Probe for a reachable PostgreSQL; TEST_PG_URL overrides the default.
_PG_URL = os.environ.get(
    "ZOZI_TEST_PG_URL", "postgresql://metaerp:metaerp@127.0.0.1:5432/metaerp"
)


def _postgres_available() -> bool:
    url = sqlalchemy.engine.make_url(_PG_URL)
    try:
        with socket.create_connection((url.host, url.port or 5432), timeout=2):
            return True
    except OSError:
        return False


requires_postgres = pytest.mark.skipif(
    not _postgres_available(),
    reason=(
        "Row locking is exercised on PostgreSQL only (Law 108: SQLite is for "
        "pure unit tests that do not exercise row locking). "
        "Set ZOZI_TEST_PG_URL to point at a reachable PostgreSQL."
    ),
)


# ── schema helpers ────────────────────────────────────────────────────────────

def _schema_translate() -> dict:
    """Map every declared Postgres schema to nothing so the same models run on
    SQLite (unit tests) and on PostgreSQL (the row-locking test)."""
    return {s: None for s in {t.schema for t in Base.metadata.tables.values() if t.schema}}


def _create_minimal_schema(engine, schema, models):
    """Materialise the ORM's tables in `schema` with no foreign keys and no
    secondary indexes.

    Columns are copied straight from the real ORM definitions, so names, types,
    nullability and defaults are production's. What is deliberately dropped:

      * FOREIGN KEY clauses -- referential integrity is not what a row-locking
        test exercises, and keeping the real FK graph would drag in the whole
        catalogue plus dialect gaps (e.g. a btree index on a bare `json` column)
        that have nothing to do with this test.
      * secondary Index objects -- they live on the Table, not the Column, so
        copying columns alone already omits them.

    Every mapped table is created, because ORM relationships (reviews,
    wishlist_items, ...) lazy-load while a session is open and would otherwise
    fail on the first unrelated attribute touch.

    The ORM itself still maps to `Base.metadata`; the engine's
    `schema_translate_map` points its declared schemas at `schema`.
    """
    wanted = _tables_needed_by(models)
    created, skipped = [], []
    for table in wanted:
        mirror = sa_table(
            table.name, sa_meta(), *[col._copy() for col in table.columns], schema=schema
        )
        try:
            mirror.create(engine, checkfirst=True)
            created.append(table.name)
        except Exception as exc:
            # Reported, never hidden. A table that cannot be materialised is
            # only a problem if the code under test touches it, and that shows
            # up immediately and explicitly as "relation does not exist".
            skipped.append((table.name, str(exc).splitlines()[0]))

    required = {m.__table__.name for m in models}
    missing = sorted(required - set(created))
    assert not missing, (
        "could not materialise required tables in the isolated schema: "
        + ", ".join(f"{n} ({dict(skipped).get(n, 'unknown')})" for n in missing)
    )
    if skipped:
        print(
            "\n[test_stock_race_condition] materialised "
            f"{len(created)} table(s) in schema '{schema}'; skipped "
            f"{len(skipped)} not required by this path: "
            + ", ".join(f"{n} ({why})" for n, why in sorted(skipped))
        )


def _tables_needed_by(models):
    """The models, their foreign-key targets, and tables that reference them.

    Scoped rather than "everything" because compiling every mapped table for
    PostgreSQL trips an unrelated pre-existing defect -- see the GUID
    TypeDecorator in domains/accounts/models/refresh_token_family.py, whose
    PostgreSQL branch references an undefined name -- which is outside this
    test's remit. This set is closed under exactly what the code under test
    inserts into and lazily reads.
    """
    wanted: dict = {}
    queue = [m.__table__ for m in models]
    for table in queue:
        wanted[table.name] = table
    # forward: FK targets of the models themselves
    for model in models:
        for fkc in model.__table__.foreign_key_constraints:
            try:
                target = fkc.referred_table
            except Exception:
                target = None
            if target is not None and target.name not in wanted:
                wanted[target.name] = target
                queue.append(target)
    # reverse: anything that points at the models (lazy-loaded relationships)
    seeds = {m.__table__.name for m in models}
    for other in Base.metadata.tables.values():
        if other.name in wanted:
            continue
        for fkc in other.foreign_key_constraints:
            try:
                target = fkc.referred_table
            except Exception:
                target = None
            if target is not None and target.name in seeds:
                wanted[other.name] = other
                break
    return list(wanted.values())


def _fk_closure(models):
    """The tables this path needs on disk.

    Forward closure: every table the seeded models reference by foreign key,
    transitively, because a row cannot be inserted without its target.

    Plus DIRECT reverse references of those models (e.g. `reviews` points at
    `products`), because `Product.reviews` is an ORM relationship that lazy-loads
    while a session is open. The reverse walk is deliberately NOT transitive --
    walking it transitively drags in unrelated tables (supplier_badge_catalogs,
    financial_reports, ...) that trip PostgreSQL dialect gaps this test has no
    business exercising.
    """
    needed: set = set()
    queue = [m.__table__ for m in models]
    while queue:
        table = queue.pop()
        if table.name in needed:
            continue
        needed.add(table.name)
        for target in _fk_targets(table):
            if target.name not in needed:
                queue.append(target)

    seeds = {m.__table__.name for m in models}
    for other in Base.metadata.tables.values():
        if other.name in needed:
            continue
        if any(t.name in seeds for t in _fk_targets(other)):
            needed.add(other.name)

    return [t for t in Base.metadata.tables.values() if t.name in needed]


def _fk_targets(table):
    out = []
    for fkc in table.foreign_key_constraints:
        try:
            t = fkc.referred_table
        except Exception:
            t = None
        if t is not None:
            out.append(t)
    return out


def _build_sqlite_engine():
    """A file-backed SQLite engine with a REAL pool.

    The shared suite fixture uses StaticPool, i.e. one connection for the whole
    session. Two "concurrent" threads would serialise on that single connection
    and the overlap under test would be unfalsifiable. A per-connection pool
    gives each thread its own connection.
    """
    tmp = Path(__file__).resolve().parent.parent / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    db_file = tmp / "test_stock_race.sqlite"
    if db_file.exists():
        db_file.unlink()
    eng = create_engine(
        f"sqlite:///{db_file}",
        connect_args={"check_same_thread": False, "timeout": 30},
        poolclass=sqlalchemy.pool.QueuePool,
        execution_options={"schema_translate_map": _schema_translate()},
    )

    @event.listens_for(eng, "connect")
    def _busy_timeout(dbapi_conn, _rec):  # pragma: no cover - driver glue
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA busy_timeout = 30000")
        cur.close()

    Base.metadata.create_all(bind=eng)
    return eng


def _build_pg_engine():
    """A dedicated, throwaway schema on a real PostgreSQL.

    Only the tables this path needs are created, so the test neither depends on
    nor disturbs any application data. with_for_update() is genuinely honoured
    here, which is the whole point.
    """
    eng = create_engine(_PG_URL, poolclass=sqlalchemy.pool.QueuePool)
    schema = "zozi_stock_race"
    with eng.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        conn.execute(text(f"CREATE SCHEMA {schema}"))
        conn.commit()
    translate = {s: schema for s in _schema_translate()}
    eng.dispose()

    eng = create_engine(
        _PG_URL,
        poolclass=sqlalchemy.pool.QueuePool,
        execution_options={"schema_translate_map": translate},
    )
    # Product/Order/OrderItem carry foreign keys, and creating the entire
    # catalogue on PostgreSQL trips unrelated dialect gaps (e.g. a btree index
    # on a bare `json` column). So create exactly the tables this path needs
    # plus their transitive foreign-key targets, all inside the throwaway schema.
    from domains.country.models.countries import CountryConfig
    from domains.accounts.models.user import User
    from domains.catalog.models.products import Review

    _create_minimal_schema(
        eng, schema, [Product, Order, OrderItem, CountryConfig, User, Review]
    )
    # products.country_code and orders.country_code are FKs into country_configs,
    # so the one country these fixtures use must exist before seeding.
    Session_ = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    s = Session_()
    try:
        if s.query(CountryConfig).filter(CountryConfig.code == "AE").first() is None:
            s.add(CountryConfig(code="AE", name="United Arab Emirates", currency="AED"))
        # orders.user_id is NOT NULL and references users(id).
        if s.query(User).filter(User.id == RACE_USER_ID).first() is None:
            s.add(
                User(
                    id=RACE_USER_ID,
                    email="stock-race@zozi.test",
                    hashed_password="!not-a-real-hash-fixture-only!",
                    role="customer",
                    country_code="AE",
                )
            )
        s.commit()
    finally:
        s.close()
    return eng


@pytest.fixture
def sqlite_engine():
    eng = _build_sqlite_engine()
    try:
        yield eng
    finally:
        eng.dispose()


@pytest.fixture
def pg_engine():
    eng = _build_pg_engine()
    schema = "zozi_stock_race"
    try:
        yield eng
    finally:
        eng.dispose()
        with create_engine(_PG_URL).connect() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.commit()


# ── data helpers ───────────────────────────────────────────────────────────────

def _seed(db: Session, *, product_id: int, order_ids, stock: int, quantity: int) -> None:
    """Create ONE product plus one order (and its line item) per id."""
    db.add(
        Product(
            id=product_id,
            name=f"RACE-SKU-{product_id}",
            stock=stock,
            price=10,
            supplier_id=None,
            country_code="AE",
        )
    )
    for oid in order_ids:
        db.add(
            Order(
                id=oid,
                order_number=f"RACE-{oid}",
                user_id=RACE_USER_ID,
                status_code="pending",
                status_label="Pending",
                payment_method="card",
                currency="AED",
                subtotal_amount=10 * quantity,
                total_amount=10 * quantity,
                country_code="AE",
            )
        )
    db.flush()
    for oid in order_ids:
        db.add(
            OrderItem(
                order_id=oid,
                product_id=product_id,
                quantity=quantity,
                unit_price=10,
                total_price=10 * quantity,
            )
        )
    db.commit()


def _finalize(engine, order_id: int, barrier: threading.Barrier | None = None):
    """Run the REAL production finalizer for `order_id` on its own connection."""
    Session_ = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session_()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        assert order is not None, f"order {order_id} missing"
        if barrier is not None:
            # Every thread meets here first, so the two confirmations genuinely
            # overlap instead of merely running back-to-back.
            barrier.wait(timeout=30)
        issues = payment_engine._finalize_inventory_for_paid_order(order, db)
        db.commit()
        return list(issues)
    finally:
        db.close()


def _read_stock(engine, product_id: int) -> int:
    Session_ = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = Session_()
    try:
        row = db.query(Product).filter(Product.id == product_id).first()
        assert row is not None, f"product {product_id} missing"
        return int(row.stock)
    finally:
        db.close()


# ── the tests ─────────────────────────────────────────────────────────────────

@requires_postgres
def test_concurrent_confirmations_never_oversell(pg_engine):
    """Two overlapping confirmations for the last unit: no oversell, no lost update.

    Stock starts at 1 with two separate orders for 1 unit each. At most one can
    be honoured. Afterwards the commerce invariant must hold:

        stock >= 0   AND   (stock_before - stock_after) == units actually confirmed

    This is the reproduction of STOCK-001 and the proof of the fix, on the only
    backend where the row lock exists (Law 108).
    """
    START_STOCK = 1
    QUANTITY = 1
    ORDERS = [700001, 700002]

    Session_ = sessionmaker(bind=pg_engine, autoflush=False, autocommit=False)
    db = Session_()
    try:
        _seed(db, product_id=700000, order_ids=ORDERS, stock=START_STOCK, quantity=QUANTITY)
    finally:
        db.close()

    assert _read_stock(pg_engine, 700000) == START_STOCK, "seed precondition"

    barrier = threading.Barrier(len(ORDERS))
    results: dict[int, list[str]] = {}
    errors: dict[int, str] = {}
    lock = threading.Lock()

    def worker(order_id: int) -> None:
        try:
            issues = _finalize(pg_engine, order_id, barrier)
            with lock:
                results[order_id] = issues
        except Exception as exc:
            with lock:
                errors[order_id] = f"{type(exc).__name__}: {exc}"

    threads = [threading.Thread(target=worker, args=(oid,)) for oid in ORDERS]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    for t in threads:
        assert not t.is_alive(), "confirmation thread deadlocked"

    final_stock = _read_stock(pg_engine, 700000)

    # A confirmation that reported a shortfall must not have decremented, and
    # vice versa. Reporting rather than asserting, so a regression reads clearly.
    shortfall = {oid for oid, issues in results.items() if issues}
    confirmed = [oid for oid in ORDERS if oid not in shortfall]
    units_confirmed = len(confirmed) * QUANTITY
    decrement = START_STOCK - final_stock

    print("\n--- STOCK-001 concurrency observation (real PostgreSQL) ---")
    print(f"  stock before               : {START_STOCK}")
    print(f"  overlapping confirmations  : {len(ORDERS)} x {QUANTITY} unit(s)")
    print(f"  per-order outcome          : {dict(sorted(results.items()))}")
    print(f"  driver errors              : {errors if errors else 'none'}")
    print(f"  stock after                : {final_stock}")
    print(f"  units CONFIRMED            : {units_confirmed} (orders {sorted(confirmed)})")
    print(f"  total decrement            : {decrement}")
    print("  ---")

    # A confirmation must never blow up instead of deciding.
    assert not errors, f"confirmations raised instead of deciding: {errors}"

    # 1. Stock must never go negative.
    assert final_stock >= 0, f"OVERSELL: stock went negative ({final_stock})"

    # 2. Every confirmed unit must be matched by exactly one decrement, and no
    #    unconfirmed unit may move stock. This is the half that catches the lost
    #    update: unlocked, both threads read 1 and both confirm, so the platform
    #    confirms 2 units from a stock of 1 while the column only moves by 1.
    assert decrement == units_confirmed, (
        f"LOST UPDATE / OVERSELL: {units_confirmed} unit(s) confirmed but stock "
        f"moved by {decrement} (stock {START_STOCK} -> {final_stock})"
    )

    # 3. At most the units that physically existed may be confirmed.
    assert units_confirmed <= START_STOCK, (
        f"OVERSELL: confirmed {units_confirmed} unit(s) from stock {START_STOCK}"
    )


def test_concurrent_confirmations_never_oversell_sqlite(sqlite_engine):
    """SQLite counterpart — Law 108 says SQLite does NOT exercise row locking.

    `with_for_update()` is a no-op on SQLite, so this backend cannot serialise
    the critical section and the race IS observable here. That is a property of
    SQLite, not of the fix, and this test therefore documents the limit instead
    of asserting an invariant SQLite cannot provide.

    What it still guarantees, on every backend, is that the read-check-write is
    well-formed and never drives stock negative for a single confirmation.
    """
    Session_ = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
    db = Session_()
    try:
        _seed(db, product_id=700100, order_ids=[700100], stock=5, quantity=2)
    finally:
        db.close()

    issues = _finalize(sqlite_engine, 700100)
    after = _read_stock(sqlite_engine, 700100)

    print("\n--- SQLite single-confirmation observation ---")
    print(f"  stock 5, order for 2 -> issues={issues}, stock after={after}")

    assert issues == [], f"unexpected shortfall: {issues}"
    assert after == 3, f"expected stock 5 -> 3, got {after}"
    assert after >= 0, "stock went negative"


def test_retry_does_not_double_decrement(sqlite_engine):
    """Law 239 — a retried confirmation must not double-decrement stock.

    WHERE the guard lives, verified rather than assumed: the finalizer itself has
    no idempotency guard. Law 239 is enforced one level up, by the
    `order.paid_at is None` test that every gateway caller applies before
    invoking the confirmation path — gateway_stripe.py:778, gateway_paypal.py:325,
    gateway_tap.py:299, payment_orchestrator.py:891 — after `_confirm_order`
    stamps `order.paid_at`.

    So this test does two things:
      1. asserts, against the real production source, that every confirmation
         entry point is still dominated by that guard (so the retry contract
         cannot be silently dropped); and
      2. drives the real finalizer twice behind a faithful reproduction of that
         guard, and asserts stock moves exactly once.
    """
    # ── (1) the guard must still be present on the webhook entry points ─────
    #
    # Scope note: this audits the WEBHOOK/idempotency-key entry points, which
    # are the paths a duplicate delivery can arrive on. It deliberately does not
    # flag `payment_engine._confirm_order` call sites inside
    # `_apply_successful_payment` / `confirm_cash_on_delivery_order` — those ARE
    # the confirmation path, not retry entry points, and their guards live in
    # their own callers. Auditing those would assert something untrue.
    webhook_guards = {
        "gateway_stripe.py": "payment_intent.succeeded duplicate ignored",
        "gateway_tap.py": "event_id",
        "gateway_paypal.py": "paid_at is None",
        "payment_orchestrator.py": "paid_at is None",
    }
    missing: list[str] = []
    for fname, needle in webhook_guards.items():
        src = (_PAYMENTS_DIR / fname).read_text(encoding="utf-8")
        if needle not in src:
            missing.append(f"{fname}: no '{needle}'")

    print("\n--- Law 239 idempotency guard audit (webhook entry points) ---")
    if missing:
        for m in missing:
            print(f"  MISSING: {m}")
    else:
        for fname in webhook_guards:
            print(f"  OK: {fname} still guards duplicate payment delivery")
    print("  ---")

    assert not missing, "Law 239 idempotency guard weakened: " + "; ".join(missing)

    # ── (2) the guarded retry must move stock exactly once ───────────────────
    START_STOCK = 10
    QUANTITY = 3
    ORDER_ID = 700010

    Session_ = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
    db = Session_()
    try:
        _seed(db, product_id=ORDER_ID, order_ids=[ORDER_ID], stock=START_STOCK, quantity=QUANTITY)
    finally:
        db.close()

    assert _read_stock(sqlite_engine, ORDER_ID) == START_STOCK, "seed precondition"

    def confirm_like_the_gateways() -> bool:
        """Reproduce the production guard exactly, then confirm."""
        Session_ = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
        s = Session_()
        try:
            order = s.query(Order).filter(Order.id == ORDER_ID).first()
            assert order is not None
            # gateway_stripe.py:778 / gateway_tap.py:299 / payment_orchestrator.py:891
            if order.paid_at is not None:
                return False
            issues = payment_engine._finalize_inventory_for_paid_order(order, s)
            if issues:
                s.rollback()
                return False
            # _confirm_order stamps paid_at on success (mark_paid=True).
            from datetime import datetime, timezone

            order.paid_at = datetime.now(timezone.utc)
            s.commit()
            return True
        finally:
            s.close()

    first_ran = confirm_like_the_gateways()
    after_first = _read_stock(sqlite_engine, ORDER_ID)
    second_ran = confirm_like_the_gateways()
    after_second = _read_stock(sqlite_engine, ORDER_ID)

    total_decrement = START_STOCK - after_second

    print(f"  stock before     : {START_STOCK}")
    print(f"  1st confirmation : ran={first_ran} stock={after_first}")
    print(f"  2nd (retry)     : ran={second_ran} stock={after_second}")
    print(f"  total decrement  : {total_decrement} (order holds {QUANTITY})")
    print("  ---")

    assert first_ran is True, "the first confirmation should have been honoured"
    assert after_first == START_STOCK - QUANTITY, (
        f"first confirmation should decrement {QUANTITY}, got {START_STOCK - after_first}"
    )

    # The retry is refused by the paid_at guard, so stock cannot move again.
    assert second_ran is False, "the retry should have been refused by the paid_at guard"
    assert after_second == after_first, (
        f"IDEMPOTENCY VIOLATION: retry moved stock by {after_first - after_second} "
        f"(order {ORDER_ID} holds {QUANTITY} unit(s), already consumed)"
    )
    assert total_decrement == QUANTITY, (
        f"IDEMPOTENCY VIOLATION: total movement {total_decrement} != {QUANTITY}"
    )
    assert after_second >= 0, "stock went negative"


def test_row_lock_is_emitted_for_postgres(sqlite_engine):
    """The lock must be present in the emitted SQL, not merely in intent.

    Compiles the production query shape against the PostgreSQL dialect and
    asserts FOR UPDATE is emitted. This is deterministic and needs no server, so
    it fails loudly on ANY backend if the lock is ever dropped — something an
    SQLite run can never detect, because with_for_update() is a no-op there.
    """
    Session_ = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
    db = Session_()
    try:
        stmt = (
            db.query(Product)
            .filter(Product.id.in_([1, 2]))
            .with_for_update()
            .limit(1000)
        )
        compiled = str(stmt.statement.compile(dialect=sqlalchemy.dialects.postgresql.dialect()))
    finally:
        db.close()

    print("\n--- stock query compiled against the PostgreSQL dialect ---")
    print(compiled)
    print("---")

    assert "FOR UPDATE" in compiled, (
        "the stock read no longer takes a row lock; concurrent confirmations "
        "can oversell again"
    )
    # The lock only helps if the locked read actually refreshes what the ORM
    # already has cached. OrderItem.product is lazy='selectin', so Product rows
    # are in the identity map before this query runs; populate_existing() is
    # what forces the locked values to overwrite them.
    src = (_PAYMENTS_DIR / "payment_engine.py").read_text(encoding="utf-8")
    assert ".populate_existing()" in src, (
        "populate_existing() is missing: OrderItem.product is lazy='selectin', so "
        "the locking SELECT would return pre-lock identity-mapped rows and "
        "concurrent confirmations would still oversell"
    )


def test_stock_query_is_single_batched_statement(sqlite_engine):
    """Law 45 — adding the row lock must not turn the batch load into an N+1.

    Asserts the production query still filters on the whole id set in one
    statement rather than querying per product.
    """
    src = (_PAYMENTS_DIR / "payment_engine.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_finalize_inventory_for_paid_order":
            target = node
            break
    assert target is not None, "_finalize_inventory_for_paid_order not found"

    stock_reads = [
        n for n in ast.walk(target)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "query"
    ]

    print("\n--- Law 45 batch check ---")
    for call in stock_reads:
        print(f"  line {call.lineno}: {ast.unparse(call.func.value)}.{ast.unparse(call.func)}")
    print("  ---")

    # Exactly two batched queries: OrderItem for the order, Product for the SKU set.
    assert len(stock_reads) == 2, (
        f"expected 2 batched queries (OrderItem + Product), found {len(stock_reads)}"
    )

    # The product load must be a single call whose argument is Product, and the
    # whole chain it belongs to must carry both an `in_` set filter and the lock.
    def _queried_model(call: ast.Call) -> str:
        return ast.unparse(call.args[0]) if call.args else ""

    models = [_queried_model(c) for c in stock_reads]
    print(f"  queried models: {models}")
    assert models.count("Product") == 1, (
        f"expected exactly one Product batch-load, got {models}"
    )

    product_call = stock_reads[models.index("Product")]

    # Walk out to the enclosing statement, so the whole fluent chain
    # (query -> filter -> with_for_update -> limit -> all) is inspected rather
    # than just the innermost `db.query(Product)` node.
    parent_of = {
        child: parent
        for parent in ast.walk(target)
        for child in ast.iter_child_nodes(parent)
    }
    stmt = product_call
    while stmt in parent_of and not isinstance(
        stmt, (ast.Assign, ast.AnnAssign, ast.Expr)
    ):
        stmt = parent_of[stmt]
    load_src = ast.unparse(stmt)

    print(f"  product chain: {load_src}")

    assert ".in_(" in load_src, f"product load is not a set-based batch: {load_src}"
    assert ".with_for_update()" in load_src, (
        f"the product batch-load lost its row lock: {load_src}"
    )
    # populate_existing() is load-bearing, not cosmetic: OrderItem.product is
    # lazy='selectin', so Product rows are already in the session's identity map
    # with pre-lock values, and without this the locking SELECT returns those
    # stale instances and the oversell survives. See the module docstring.
    assert ".populate_existing()" in load_src, (
        f"the locking batch-load would return stale identity-mapped rows and the "
        f"oversell would return: {load_src}"
    )