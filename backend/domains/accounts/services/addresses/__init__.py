"""accounts domain — addresses services."""
from __future__ import annotations

from domains.accounts.services.addresses.addresses_service import *

__all__: list[str] = [
    "list_addresses",
    "create_address_from_payload",
    "update_address_from_payload",
    "delete_address_by_id",
    "set_default_address_by_id",
    "list_user_addresses",
    "get_user_address",
    "unset_other_default_addresses",
    "create_address",
    "update_address",
    "delete_address",
    "set_default_address",
]
