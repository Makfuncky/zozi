"""Supplier order operations."""
from controllers.supplier.supplier_controller import (  # noqa: F401
    get_supplier_orders,
    update_supplier_order_status,
    get_supplier_order_detail,
    get_supplier_label_payload,
    upload_supplier_parcel_proof,
    get_supplier_shipments,
)
