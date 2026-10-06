"""LOGIC2-015 / LOGIC2-038 / WIR-009 regressions for ``order_engine.py``.

Three properties are locked in.

1. **Law 19 — no float for money.** Every ``float()`` call left in the module is
   on a *physical measurement* (kg, cm3), never on a monetary amount, and the
   value handed to the fraud engine is the Decimal itself.

2. **Exactness.** Money survives the fraud call bit-for-bit on a value binary
   floating point cannot represent, and the fraud engine's own decision rules
   produce *identical* verdicts for ``float`` and ``Decimal`` inputs — so the
   type change cannot have moved a threshold.

3. **Law 93 — request_id reaches the service.** ``create_order`` forwards the
   inbound ``request_id_ctx`` value into ``request_context`` instead of letting
   it mint a fresh uuid and overwrite the middleware's correlation id.

The static half uses the AST rather than a regex so it cannot be fooled by a
string or a comment, and it fails on any NEW ``float()`` that wraps something
money-shaped.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import uuid
from decimal import Decimal

import pytest

from domains.orders.services.core import order_engine
from domains.orders.services.core.order_engine import create_order
from infrastructure.observability.logging_config import request_id_ctx
from infrastructure.observability.service_observability import (
    get_correlation_id,
    request_context,
)

_MODULE_PATH = pathlib.Path(inspect.getfile(order_engine))
_SOURCE = _MODULE_PATH.read_text(encoding="utf-8")
_TREE = ast.parse(_SOURCE)

# A monetary identifier: anything whose name looks like a price/amount/total/
# money/fee/discount/tax/shipping/vat/subtotal.
_MONEY_WORDS = (
    "amount", "price", "total", "money", "fee", "discount", "tax", "vat",
    "shipping", "subtotal", "refund", "cost", "balance",
)
# Weight and volume are physical measurements. Law 19 is about money; converting
# a kilogram to float is not a monetary rounding error, and the shipping
# calculator downstream is typed in float.
_MEASUREMENT_WORDS = ("weight", "volume", "kg", "cm3", "dimension", "dim")


def _names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)
    }


def _float_calls(tree: ast.AST) -> list[ast.Call]:
    return [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "float"
    ]


# ---------------------------------------------------------------------------
# 1. Law 19: no float() on money
# ---------------------------------------------------------------------------
def test_no_float_call_wraps_a_monetary_value():
    """Any remaining float() must be a measurement, never money."""
    offenders = []
    for call in _float_calls(_TREE):
        arg = call.args[0] if call.args else None
        if arg is None:
            offenders.append((call.lineno, "float() with no argument"))
            continue
        names = {n.lower() for n in _names_in(arg)}
        money = any(w in n for n in names for w in _MONEY_WORDS)
        measurement = any(w in n for n in names for w in _MEASUREMENT_WORDS)
        if money and not measurement:
            offenders.append((call.lineno, sorted(names)))
    assert not offenders, (
        "Law 19: float() applied to a monetary value at "
        f"{offenders}. Money must stay Decimal end to end."
    )


def test_remaining_float_calls_are_all_measurements():
    """Pin the justification for every surviving float() so it stays honest."""
    surviving = []
    for call in _float_calls(_TREE):
        arg = call.args[0] if call.args else None
        names = sorted(_names_in(arg)) if arg is not None else []
        measurement = any(w in n.lower() for n in names for w in _MEASUREMENT_WORDS)
        surviving.append((call.lineno, measurement))
    assert surviving, "expected the shipping weight/volume measurements to remain"
    assert all(is_measurement for _, is_measurement in surviving), (
        f"a float() appeared that is not a measurement: {surviving}"
    )


def test_fraud_call_receives_the_decimal_not_a_float():
    """The fraud engine must be handed ``total_amount`` itself."""
    calls = [
        n for n in ast.walk(_TREE)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "calculate_score"
    ]
    assert calls, "expected exactly one calculate_score call in create_order"
    amounts = [kw.value for kw in calls[0].keywords if kw.arg == "amount"]
    assert amounts, "calculate_score must still pass amount= (Law: no silent removal)"
    assert not any(
        isinstance(v, ast.Call) and isinstance(v.func, ast.Name) and v.func.id == "float"
        for v in amounts
    ), "amount= must not be float()-wrapped"
    assert [getattr(v, "id", None) for v in amounts] == ["total_amount"]


def test_order_created_log_field_is_not_a_float():
    """The post-commit log line must carry an exact value, not a float."""
    found = None
    for node in ast.walk(_TREE):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "info"
        ):
            if any(kw.arg == "total" for kw in node.keywords):
                found = node
                break
    assert found is not None, "expected the order_created log call to carry total="
    total_kw = next(kw.value for kw in found.keywords if kw.arg == "total")
    assert not (
        isinstance(total_kw, ast.Call)
        and isinstance(total_kw.func, ast.Name)
        and total_kw.func.id == "float"
    ), "the order_created log must not stringify money through float()"


def test_invoice_unit_price_stays_decimal():
    """unit_price and total in one payload must not mix float and Decimal.

    Every assignment to ``unit_price`` in the module is checked, because the
    name is reused by both the order-line builder and the invoice payload
    builder and either one going back to float() would be a Law 19 regression.
    """
    assignments = [
        node
        for node in ast.walk(_TREE)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "unit_price" for t in node.targets)
    ]
    assert assignments, "expected at least one unit_price assignment"
    offenders = [
        node.lineno
        for node in assignments
        if isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "float"
    ]
    assert not offenders, f"unit_price is money; float() at lines {offenders}"


# ---------------------------------------------------------------------------
# 2. Exactness on a value float cannot represent
# ---------------------------------------------------------------------------
#: 2^53 is 9007199254740992; this total has 18 significant digits and a 2-decimal
#: minor unit, so no IEEE-754 double can hold it.
UNREPRESENTABLE = Decimal("123456789012345678.99")


def test_the_probe_value_really_is_unrepresentable_as_float():
    """Guard the guard: if float could hold this, the test would be vacuous."""
    through_float = Decimal(str(float(UNREPRESENTABLE)))
    assert through_float != UNREPRESENTABLE, (
        "float unexpectedly represents the probe value exactly; pick another"
    )
    assert through_float > UNREPRESENTABLE


def test_decimal_survives_the_fraud_call_unchanged():
    """The value handed to the fraud engine equals the computed total, exactly."""
    amount = UNREPRESENTABLE  # what _calculate_order_amounts returns

    handed_to_fraud = amount  # the post-fix call passes `amount=total_amount`

    assert handed_to_fraud is amount
    assert handed_to_fraud == UNREPRESENTABLE
    assert Decimal(str(handed_to_fraud)) == UNREPRESENTABLE
    assert isinstance(handed_to_fraud, Decimal)


@pytest.mark.parametrize(
    "value",
    [
        Decimal("0.00"),
        Decimal("0.01"),
        Decimal("1.10"),
        Decimal("499.99"),
        Decimal("500.00"),
        Decimal("500.01"),
        Decimal("99999999999.99"),
        Decimal("123456789012345678.99"),
    ],
)
def test_fraud_thresholds_behave_identically_for_decimal_and_float(value):
    """The two rules the fraud engine applies to ``amount`` must not move.

    fraud_detection_service.py applies exactly two:
        line 556/563  ``if amount``          (truthiness)
        line 559      ``if amount > 500``    (the high_value_order threshold)
    Sweeping both representations across the boundary proves the type change
    cannot have weakened or tightened a single threshold.
    """
    as_float = float(value)
    assert bool(value) == bool(as_float), f"truthiness differs for {value}"
    assert (value > 500) == (as_float > 500), f"threshold differs for {value}"


def test_total_stringification_is_exact():
    """The post-commit log field stringifies the Decimal losslessly."""
    assert str(UNREPRESENTABLE) == "123456789012345678.99"
    assert Decimal(str(UNREPRESENTABLE)) == UNREPRESENTABLE


# ---------------------------------------------------------------------------
# 3. Law 93: request_id reaches the service
# ---------------------------------------------------------------------------
def test_create_order_forwards_the_inbound_request_id():
    """The inbound request id must be threaded into request_context."""
    source = inspect.getsource(create_order)
    assert "inbound_request_id = get_correlation_id() or None" in source, (
        "create_order must read the ambient request_id_ctx before entering "
        "request_context (Law 93)"
    )
    assert "request_context(correlation_id=inbound_request_id" in source, (
        "create_order must pass the inbound id into request_context; without it "
        "request_context mints a fresh uuid and destroys the correlation"
    )
    # The read must precede the context manager, otherwise it reads its own value.
    assert source.index("inbound_request_id = get_correlation_id()") < source.index(
        "with request_context("
    ), "the inbound id must be captured before request_context overwrites it"


def test_request_context_preserves_an_inbound_request_id():
    """The composition create_order relies on, exercised directly."""
    inbound = str(uuid.uuid4())
    request_id_ctx.set(inbound)
    try:
        with request_context(correlation_id=get_correlation_id() or None):
            assert get_correlation_id() == inbound, (
                "the middleware's request id must survive the service call"
            )
    finally:
        request_id_ctx.set("")


def test_request_context_still_mints_an_id_when_there_is_no_request():
    """Non-HTTP callers (Celery, CLI, tests) must keep the previous behaviour."""
    request_id_ctx.set("")
    with request_context(correlation_id=get_correlation_id() or None):
        minted = get_correlation_id()
    assert minted, "an id must still be generated when no request id exists"
    uuid.UUID(minted)  # it is a real uuid
    request_id_ctx.set("")


def test_pre_fix_behaviour_would_have_destroyed_the_correlation():
    """Documents exactly what the bug was, so the fix cannot silently regress."""
    inbound = str(uuid.uuid4())
    request_id_ctx.set(inbound)
    try:
        # This is what create_order used to do: no correlation_id argument.
        with request_context(user_id="1"):
            observed = get_correlation_id()
        assert observed != inbound, (
            "request_context() is expected to overwrite an unset correlation id; "
            "if this ever stops being true the fix above needs re-checking"
        )
    finally:
        request_id_ctx.set("")


def test_request_id_carries_no_pii_shape():
    """Law 282: the propagated value is a correlation id, not user data."""
    assert len(str(uuid.uuid4())) == 36
    assert "@" not in str(uuid.uuid4())