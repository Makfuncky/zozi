"""Domain-owned address serializer (single source of truth).

Imported by ``modules.customer.serializers`` (modules -> domains, allowed) and by
``domains.orders.services`` so the orders domain never depends on a module package.
"""
from __future__ import annotations
from typing import Any


def serialize_address(address: Any) -> dict:
    return {
        "id": address.id,
        "user_id": address.user_id,
        "label": getattr(address, "label", None),
        "street": address.address_line1,
        "address_line1": address.address_line1,
        "address_line2": address.address_line2,
        "city": address.city,
        "state": address.state,
        "postal_code": address.postal_code,
        "country": address.country,
        "is_default": address.is_default,
        "full_name": address.full_name,
        "phone": address.phone,
        "created_at": address.created_at,
    }
