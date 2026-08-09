"""Backward-compatible re-export shim for logistics-partner write operations.

This module intentionally performs NO imports at module-load time. It used to
re-export handler functions from `controllers.logistics_controller` and
`routers.public_shipments_access`, which created import-time circular-import cycles
(`logistics_partner_controller`/`orders_controller` ->
`logistics_partner_write_service` -> `controllers.logistics_controller` -> ...).
Resolving names lazily via module-level `__getattr__` breaks those cycles: the
underlying modules are only imported on first attribute access, by which point
the importing module is fully initialised.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_shipment": ("controllers.logistics_controller", "create_shipment"),
    "update_shipment": ("routers.public_shipments_access", "update_shipment"),
    "create_logistics_partner": ("services.auth_write_service", "create_logistics_partner"),
    "delete_notification": ("services.comms.communication_write_service", "delete_notification"),
    "create_notification": ("services.comms.tickets_write_service", "create_notification"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# The following symbols were referenced but have NO definition anywhere in the
# codebase. They are stubbed to fail loudly at call time rather than break
# import of this module.
def _missing_symbol(name: str):
    def _f(*_a, **_k):
        raise NotImplementedError(
            f"'logistics_partner_write_service.{name}' is not implemented (refactor gap)"
        )
    return _f


create_city_distance_matrix = _missing_symbol("create_city_distance_matrix")
create_coding_remittance_receipt = _missing_symbol("create_coding_remittance_receipt")
create_logistics_partner_bank_account = _missing_symbol("create_logistics_partner_bank_account")
create_logistics_partner_document = _missing_symbol("create_logistics_partner_document")
create_logistics_partner_payout = _missing_symbol("create_logistics_partner_payout")
create_logistics_partner_service_area = _missing_symbol("create_logistics_partner_service_area")
create_pricing_profile = _missing_symbol("create_pricing_profile")
create_pricing_rule = _missing_symbol("create_pricing_rule")
create_settlement = _missing_symbol("create_settlement")
create_shipment_confirmation = _missing_symbol("create_shipment_confirmation")
create_shipment_event = _missing_symbol("create_shipment_event")
create_transaction_ledger_entry = _missing_symbol("create_transaction_ledger_entry")
create_vehicle_rule = _missing_symbol("create_vehicle_rule")
delete_category_pricing_rule = _missing_symbol("delete_category_pricing_rule")
delete_city_distance_matrix = _missing_symbol("delete_city_distance_matrix")
delete_logistics_partner = _missing_symbol("delete_logistics_partner")
delete_logistics_partner_bank_account = _missing_symbol("delete_logistics_partner_bank_account")
delete_logistics_partner_document = _missing_symbol("delete_logistics_partner_document")
delete_logistics_partner_payout = _missing_symbol("delete_logistics_partner_payout")
delete_logistics_partner_service_area = _missing_symbol("delete_logistics_partner_service_area")
delete_pricing_profile = _missing_symbol("delete_pricing_profile")
delete_pricing_rule = _missing_symbol("delete_pricing_rule")
delete_shipment = _missing_symbol("delete_shipment")
delete_vehicle_rule = _missing_symbol("delete_vehicle_rule")
update_city_distance_matrix = _missing_symbol("update_city_distance_matrix")
update_logistics_partner = _missing_symbol("update_logistics_partner")
update_logistics_partner_bank_account = _missing_symbol("update_logistics_partner_bank_account")
update_logistics_partner_document = _missing_symbol("update_logistics_partner_document")
update_logistics_partner_payout = _missing_symbol("update_logistics_partner_payout")
update_logistics_partner_service_area = _missing_symbol("update_logistics_partner_service_area")
update_notification = _missing_symbol("update_notification")
update_order = _missing_symbol("update_order")
update_order_logistics_allocation = _missing_symbol("update_order_logistics_allocation")
update_pricing_profile = _missing_symbol("update_pricing_profile")
update_pricing_rule = _missing_symbol("update_pricing_rule")
update_settlement = _missing_symbol("update_settlement")
update_transaction_ledger = _missing_symbol("update_transaction_ledger")
update_vehicle_rule = _missing_symbol("update_vehicle_rule")
