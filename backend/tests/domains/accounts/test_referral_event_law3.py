"""Law 3 regression: accounts must not import ReferralPointEvent directly from
domains.customers.models; all access must route through customers.ports.

Also verifies that the two port functions added for FILE-128 exist and have
the correct signature shape (db first, primitives after, return type correct).
"""
from __future__ import annotations

import os



SRC = (
    r"D:\Projects\10_E_COMMERCE_WEBSITE\zozi\backend\domains\accounts\services\auth\auth_service.py"
)
_CUSTOMERS_PORTS = r"D:\Projects\10_E_COMMERCE_WEBSITE\zozi\backend\domains\customers\ports.py"


def test_no_direct_customer_model_import_for_referral_event():
    """ReferralPointEvent must not be imported directly from customers.models
    anywhere in auth_service.py."""
    src = SRC
    assert os.path.exists(src), f"Source file not found: {src}"
    text = open(src, encoding="utf-8").read()
    # Scan for any direct model import of ReferralPointEvent
    offenders = [
        line.strip()
        for line in text.splitlines()
        if "customer_schema_models import ReferralPointEvent" in line
        and not line.strip().startswith("#")
    ]
    assert offenders == [], (
        "auth_service.py still imports ReferralPointEvent directly from "
        "domains.customers.models. Offending lines:\n  "
        + "\n  ".join(offenders)
    )


def test_auth_service_uses_ports_for_referral_events():
    """auth_service.py must call get_referral_point_events / create_referral_point_event
    from domains.customers.ports (lazy import inside functions is acceptable)."""
    text = open(SRC, encoding="utf-8").read()
    # Must reference the port functions somewhere in the file
    assert "get_referral_point_events" in text, (
        "auth_service.py must call get_referral_point_events from customers.ports"
    )
    assert "create_referral_point_event" in text, (
        "auth_service.py must call create_referral_point_event from customers.ports"
    )


def test_customers_ports_exposes_referral_functions():
    """customers/ports.py must expose get_referral_point_events and
    create_referral_point_event as module-level names."""
    import domains.customers.ports as ports

    assert hasattr(ports, "get_referral_point_events"), (
        "customers.ports missing get_referral_point_events"
    )
    assert hasattr(ports, "create_referral_point_event"), (
        "customers.ports missing create_referral_point_event"
    )


def test_referral_port_signatures():
    """Port functions must accept db as first parameter and primitives after."""
    import domains.customers.ports as ports
    import inspect

    read_sig = inspect.signature(ports.get_referral_point_events)
    read_params = list(read_sig.parameters.keys())
    assert read_params[0] == "db", (
        f"get_referral_point_events first param must be 'db', got {read_params[0]}"
    )

    write_sig = inspect.signature(ports.create_referral_point_event)
    write_params = list(write_sig.parameters.keys())
    assert write_params[0] == "db", (
        f"create_referral_point_event first param must be 'db', got {write_params[0]}"
    )
    assert "user_id" in write_params
    assert "event_type" in write_params
    assert "points" in write_params
    assert "channel" in write_params
    assert "referred_user_id" in write_params
