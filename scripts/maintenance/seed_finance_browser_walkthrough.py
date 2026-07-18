from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Any, cast

from finance_cycle_smoke import (
    REPO_ROOT,
    SmokeFailure,
    ensure_demo_accounts,
    ensure_partner_pickup_access,
    ensure_logistics_settlements,
    force_settlements_eligible,
    get_user_id_by_email,
    load_app,
    login,
    mark_order_prepared,
    require_ok,
)
from fastapi.testclient import TestClient

from db.database import SessionLocal
from db.models import LogisticsSettlement, Order, Product, SupplierSettlement
from services.cash_management_service import create_ledger_entries_for_order
from utils.datetime_utils import utcnow as _utcnow


def _ensure_supplier_product(client: TestClient, supplier_headers: dict[str, str], run_tag: str) -> int:
    response = client.get("/supplier/products", headers=supplier_headers)
    if response.status_code == 200:
        items = response.json()
        if isinstance(items, list) and items:
            for item in items:
                product_id = item.get("id")
                if product_id:
                    _ensure_product_stock(int(product_id))
                    return int(product_id)

    supplier_id = get_user_id_by_email("supplier@zozi.com")
    created = require_ok(
        client.post(
            "/products/",
            headers=supplier_headers,
            json={
                "name": f"Finance Walkthrough Product {run_tag}",
                "description": "Browser walkthrough finance seed product",
                "price": 149.0,
                "category": "General",
                "stock": 20,
                "supplier_id": supplier_id,
                "image_url": "https://picsum.photos/seed/finance-walkthrough/600/600",
            },
        ),
        "Failed to create walkthrough product",
    )
    product_id = int(created["id"])
    _ensure_product_stock(product_id)
    return product_id


def _ensure_product_stock(product_id: int, minimum_stock: int = 20) -> None:
    session = SessionLocal()
    try:
        product = session.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise SmokeFailure(f"Walkthrough product {product_id} was not found")
        current_stock = int(getattr(product, "stock", 0) or 0)
        if current_stock < minimum_stock:
            product.stock = minimum_stock
        if hasattr(product, "is_approved"):
            product.is_approved = True
        if hasattr(product, "is_active"):
            product.is_active = True
        session.commit()
    finally:
        session.close()


def _create_order(
    client: TestClient,
    customer_headers: dict[str, str],
    *,
    product_id: int,
    payment_method: str,
    run_tag: str,
) -> int:
    payload = {
        "items": [{"product_id": product_id, "quantity": 1}],
        "shipping_address": f"Finance walkthrough {payment_method.upper()} {run_tag}, Dubai, AE",
        "city": "Dubai",
        "country": "AE",
        "customer_phone": "+971500000777",
        "delivery_location": "25.2048,55.2708",
        "delivery_note": f"Finance walkthrough {payment_method.upper()} {run_tag}",
        "payment_method": payment_method,
    }
    created = require_ok(
        client.post("/orders/", headers=customer_headers, json=payload),
        f"Failed to create {payment_method} order",
    )
    return int(created["id"])


def _force_card_order_confirmed(order_id: int, run_tag: str) -> None:
    session = SessionLocal()
    try:
        order = session.query(Order).filter(Order.id == order_id).first()
        if order is None:
            raise SmokeFailure(f"Card walkthrough order {order_id} was not found")

        order.status = "confirmed"
        order.payment_intent_id = f"pi_finance_walkthrough_{run_tag}_{order_id}"
        order.payment_gateway_code = order.payment_gateway_code or "stripe"
        order.payment_customer_total_amount = order.payment_customer_total_amount or order.total_amount
        order.paid_at = _utcnow()
        create_ledger_entries_for_order(order, session)
        session.commit()
    finally:
        session.close()


def _deliver_order(
    client: TestClient,
    supplier_headers: dict[str, str],
    partner_headers: dict[str, str],
    *,
    order_id: int,
    run_tag: str,
) -> int:
    shipment = require_ok(
        client.post(
            "/logistics/shipments",
            headers=supplier_headers,
            json={
                "order_id": order_id,
                "current_hub": f"Finance Hub {run_tag}",
                "package_count": 1,
                "package_weight_kg": 1.1,
                "package_dimensions": "25x18x9 cm",
                "packaging_notes": f"Finance walkthrough parcel {run_tag}",
                "notes": f"Finance walkthrough shipment {run_tag}",
            },
        ),
        f"Failed to create shipment for order {order_id}",
    )
    shipment_id = int(shipment["id"])

    mark_order_prepared(client, supplier_headers, order_id, f"Finance walkthrough parcel ready {run_tag}")

    require_ok(
        client.put(
            f"/logistics-partners/shipments/{shipment_id}/status",
            headers=partner_headers,
            json={"status": "picking_up", "event_type": "pickup_confirmed", "current_hub": f"Finance Hub {run_tag}"},
        ),
        f"Failed to mark shipment {shipment_id} as picking up",
    )
    require_ok(
        client.put(
            f"/logistics-partners/shipments/{shipment_id}/status",
            headers=partner_headers,
            json={"status": "shipped", "event_type": "picked_from_supplier", "current_hub": f"Finance Route {run_tag}"},
        ),
        f"Failed to mark shipment {shipment_id} as shipped",
    )
    require_ok(
        client.put(
            f"/logistics-partners/shipments/{shipment_id}/status",
            headers=partner_headers,
            json={"status": "in_transit", "event_type": "out_for_delivery", "current_hub": f"Finance Route {run_tag}"},
        ),
        f"Failed to mark shipment {shipment_id} as in transit",
    )
    require_ok(
        client.put(
            f"/logistics-partners/shipments/{shipment_id}/status",
            headers=partner_headers,
            json={
                "status": "delivered",
                "event_type": "customer_received",
                "current_hub": "Customer Address",
                "delivery_signature_name": "Finance Walkthrough Receiver",
                "delivery_signature_data_url": "data:image/svg+xml;utf8,%3Csvg%3E%3Cpath%20d%3D%27M0%200%20L2%202%27/%3E%3C/svg%3E",
            },
        ),
        f"Failed to mark shipment {shipment_id} as delivered",
    )
    return shipment_id


def _approve_bank_accounts(
    client: TestClient,
    admin_headers: dict[str, str],
    supplier_headers: dict[str, str],
    partner_headers: dict[str, str],
) -> None:
    require_ok(
        client.put(
            "/finance/admin/bank-settings",
            headers=admin_headers,
            json={
                "account_label": "Zozi Walkthrough Treasury",
                "beneficiary_name": "Zozi Walkthrough Treasury LLC",
                "bank_name": "Walkthrough Bank",
                "account_number": "000123456789",
                "iban": "OM11WALK1234567890",
                "currency": "OMR",
                "is_active": True,
                "remittance_reference_prefix": "ZWALK",
            },
        ),
        "Failed to save walkthrough treasury settings",
    )

    supplier_bank = require_ok(
        client.put(
            "/supplier/bank-account",
            headers=supplier_headers,
            json={
                "beneficiary_name": "Walkthrough Supplier Co",
                "bank_name": "Supplier Walkthrough Bank",
                "account_number": "1234567890",
                "iban": "OM91WALKSUP1234567890",
                "swift_code": "WALKSUPX",
                "currency": "OMR",
                "bank_country": "Oman",
            },
        ),
        "Failed to save supplier bank account",
    )
    require_ok(
        client.post(
            f"/admin/bank-accounts/{supplier_bank['id']}/approve?kind=supplier",
            headers=admin_headers,
            json={"note": "Approved for finance walkthrough."},
        ),
        "Failed to approve supplier bank account",
    )

    logistics_bank = require_ok(
        client.put(
            "/logistics-partners/me/bank-account",
            headers=partner_headers,
            json={
                "beneficiary_name": "Walkthrough Logistics Co",
                "bank_name": "Logistics Walkthrough Bank",
                "account_number": "9988776655",
                "iban": "OM91WALKLOG1234567890",
                "swift_code": "WALKLOGX",
                "currency": "OMR",
                "bank_country": "Oman",
            },
        ),
        "Failed to save logistics bank account",
    )
    require_ok(
        client.post(
            f"/admin/bank-accounts/{logistics_bank['id']}/approve?kind=logistics_partner",
            headers=admin_headers,
            json={"note": "Approved for finance walkthrough."},
        ),
        "Failed to approve logistics bank account",
    )


def _settlement_snapshot(order_id: int) -> dict[str, int]:
    session = SessionLocal()
    try:
        supplier_settlement = session.query(SupplierSettlement).filter(SupplierSettlement.order_id == order_id).first()
        logistics_settlement = session.query(LogisticsSettlement).filter(LogisticsSettlement.order_id == order_id).first()
        if supplier_settlement is None or logistics_settlement is None:
            raise SmokeFailure(f"Missing settlements for order {order_id}")
        return {
            "supplier_settlement_id": int(cast(Any, supplier_settlement).id),
            "logistics_settlement_id": int(cast(Any, logistics_settlement).id),
        }
    finally:
        session.close()


def _resolve_output_path(raw_path: str) -> Path:
    output_path = Path(raw_path)
    if output_path.is_absolute():
        return output_path
    return REPO_ROOT / output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed delivered card and COD orders for live browser finance walkthroughs.")
    parser.add_argument("--reset-seed", action="store_true", help="Reset and reseed the local database before creating walkthrough data.")
    parser.add_argument("--output", default="artifacts/finance_browser_walkthrough_seed.json", help="JSON summary output path.")
    args = parser.parse_args()

    ensure_demo_accounts(args.reset_seed)
    app = load_app()
    run_tag = str(int(time.time()))

    with TestClient(app) as client:
        admin_headers = login(client, "admin@zozi.com", "admin123")
        supplier_headers = login(client, "supplier@zozi.com", "supplier123")
        customer_headers = login(client, "customer@zozi.com", "customer123")
        partner_headers = login(client, "logistics@zozi.com", "logistics123")
        ensure_partner_pickup_access(
            client,
            admin_headers,
            partner_headers,
            note_prefix="Finance walkthrough",
        )

        _approve_bank_accounts(client, admin_headers, supplier_headers, partner_headers)
        product_id = _ensure_supplier_product(client, supplier_headers, run_tag)

        card_order_id = _create_order(client, customer_headers, product_id=product_id, payment_method="card", run_tag=run_tag)
        _force_card_order_confirmed(card_order_id, run_tag)
        card_shipment_id = _deliver_order(client, supplier_headers, partner_headers, order_id=card_order_id, run_tag=f"card-{run_tag}")
        ensure_logistics_settlements(card_order_id)
        force_settlements_eligible(card_order_id)
        card_settlements = _settlement_snapshot(card_order_id)

        cod_order_id = _create_order(client, customer_headers, product_id=product_id, payment_method="cod", run_tag=run_tag)
        cod_shipment_id = _deliver_order(client, supplier_headers, partner_headers, order_id=cod_order_id, run_tag=f"cod-{run_tag}")
        ensure_logistics_settlements(cod_order_id)
        force_settlements_eligible(cod_order_id)
        cod_settlements = _settlement_snapshot(cod_order_id)

        summary = {
            "run_tag": run_tag,
            "credentials": {
                "admin": {"email": "admin@zozi.com", "password": "admin123"},
                "supplier": {"email": "supplier@zozi.com", "password": "supplier123"},
                "customer": {"email": "customer@zozi.com", "password": "customer123"},
                "logistics": {"email": "logistics@zozi.com", "password": "logistics123"},
            },
            "card": {
                "order_id": card_order_id,
                "shipment_id": card_shipment_id,
                **card_settlements,
            },
            "cod": {
                "order_id": cod_order_id,
                "shipment_id": cod_shipment_id,
                **cod_settlements,
            },
        }

    output_path = _resolve_output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(output_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()