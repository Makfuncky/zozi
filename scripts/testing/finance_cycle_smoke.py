from __future__ import annotations

import os
import argparse
import io
import importlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient

from db.database import SessionLocal
from db.models import LogisticsSettlement, Order, OrderLogisticsAllocation, Shipment, SupplierSettlement, TransactionLedger, User
from services.cash_management_service import create_settlements_on_delivery
from services import finance_transfer_service
from utils.datetime_utils import utcnow as _utcnow


class SmokeFailure(RuntimeError):
    pass


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def ensure_demo_accounts(reset_seed: bool) -> None:
    if reset_seed:
        completed = subprocess.run(
            [sys.executable, "db/init_db.py", "--reset", "--seed"],
            cwd=BACKEND_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise SmokeFailure(
                "Reset/seed failed:\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )
        return

    migrations = importlib.import_module("utils.migrations")
    seed_module = importlib.import_module("db.seed")
    migrations.upgrade_database_to_head()
    seed_module.seed_data()


def load_app() -> Any:
    module_spec = importlib.util.spec_from_file_location("zozi_backend_main", BACKEND_ROOT / "main.py")
    if module_spec is None or module_spec.loader is None:
        raise SmokeFailure("Unable to load backend main module")
    main = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(main)
    return main.app


def require_ok(response: Any, message: str) -> dict[str, Any]:
    if response.status_code not in (200, 201):
        raise SmokeFailure(f"{message}: HTTP {response.status_code} {response.text}")
    payload = response.json()
    return payload if isinstance(payload, dict) else {"items": payload}


def login(client: TestClient, username: str, password: str) -> dict[str, Any]:
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    if response.status_code != 200:
        raise SmokeFailure(f"Login failed for {username}: {response.status_code} {response.text}")
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}


def register(client: TestClient, email: str, username: str, password: str, role: str) -> dict[str, Any]:
    response = client.post(
        "/auth/register",
        json={"email": email, "username": username, "password": password, "role": role},
    )
    if response.status_code not in (200, 201):
        raise SmokeFailure(f"Register failed for {email}: {response.status_code} {response.text}")
    return login(client, email, password)


def configure_smoke_transfer_provider() -> None:
    finance_transfer_service.settings.bank_api_enabled = True
    if not finance_transfer_service.settings.bank_api_base_url.strip():
        finance_transfer_service.settings.bank_api_base_url = "https://sandbox.bank.test"
    if not finance_transfer_service.settings.bank_api_batch_path.strip():
        finance_transfer_service.settings.bank_api_batch_path = "/v1/payout-batches"
    if not finance_transfer_service.settings.bank_api_auth_token.strip():
        finance_transfer_service.settings.bank_api_auth_token = os.environ.get("BANK_API_AUTH_TOKEN", "smoke-bank-token")
    if not finance_transfer_service.settings.bank_api_source_account_id.strip():
        finance_transfer_service.settings.bank_api_source_account_id = "zozi-smoke-main"


def force_settlements_eligible(order_id: int) -> dict[str, int]:
    session = SessionLocal()
    try:
        supplier_rows = session.query(SupplierSettlement).filter(SupplierSettlement.order_id == order_id).all()
        logistics_rows = session.query(LogisticsSettlement).filter(LogisticsSettlement.order_id == order_id).all()
        if not supplier_rows:
            raise SmokeFailure(f"No supplier settlements created for order {order_id}")
        if not logistics_rows:
            raise SmokeFailure(f"No logistics settlements created for order {order_id}")

        eligible_at = _utcnow()
        for row in supplier_rows:
            row.eligible_at = eligible_at
            row.status = "eligible"
        for row in logistics_rows:
            row.eligible_at = eligible_at
            row.status = "eligible"
        session.commit()
        return {"supplier": len(supplier_rows), "logistics": len(logistics_rows)}
    finally:
        session.close()


def get_user_id_by_email(email: str) -> int:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == email).first()
        if user is None or user.id is None:
            raise SmokeFailure(f"Unable to locate user id for {email}")
        return int(user.id)
    finally:
        session.close()


def mark_order_prepared(client: TestClient, headers: dict[str, str], order_id: int, note: str) -> None:
    response = client.post(
        f"/supplier/orders/{order_id}/parcel-proof",
        data={"notes": note},
        files={"file": (f"parcel-{order_id}.jpg", io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 256), "image/jpeg")},
        headers=headers,
    )
    if response.status_code not in (200, 201):
        raise SmokeFailure(f"Failed to mark order prepared: HTTP {response.status_code} {response.text}")


def ensure_partner_pickup_access(
    client: TestClient,
    admin_headers: dict[str, str],
    partner_headers: dict[str, str],
    *,
    note_prefix: str,
) -> int:
    partner_profile = require_ok(
        client.get("/logistics-partners/profile", headers=partner_headers),
        "Failed to load logistics partner profile",
    )
    partner_id = int(partner_profile["id"])

    require_ok(
        client.post(
            f"/logistics-partners/review/profile/{partner_id}",
            headers=admin_headers,
            json={"status": "approved", "note": f"{note_prefix} approved logistics profile."},
        ),
        "Failed to approve logistics partner profile",
    )

    existing_areas_payload = require_ok(
        client.get("/logistics-partners/service-areas", headers=partner_headers),
        "Failed to load logistics partner service areas",
    )
    existing_areas = cast(list[dict[str, Any]], existing_areas_payload.get("items", []))
    approved_area = next(
        (
            area
            for area in existing_areas
            if area.get("approval_status") == "approved"
            and area.get("is_active", True)
            and str(area.get("country_code", "")).upper() == "AE"
            and str(area.get("city_name", "")).strip() == ""
        ),
        None,
    )

    if approved_area is None:
        created_area = require_ok(
            client.post(
                "/logistics-partners/service-areas",
                headers=partner_headers,
                json={
                    "country_name": "United Arab Emirates",
                    "country_code": "AE",
                    "zone_label": "Finance Smoke UAE",
                    "charge_amount": 12.0,
                    "currency": "AED",
                    "is_active": True,
                },
            ),
            "Failed to create logistics partner service area",
        )
        require_ok(
            client.post(
                f"/logistics-partners/review/service-areas/{created_area['id']}",
                headers=admin_headers,
                json={"status": "approved", "note": f"{note_prefix} approved UAE lane."},
            ),
            "Failed to approve logistics partner service area",
        )

    return partner_id


def ensure_logistics_settlements(order_id: int) -> None:
    session = SessionLocal()
    try:
        existing = session.query(LogisticsSettlement).filter(LogisticsSettlement.order_id == order_id).first()
        if existing is not None:
            return

        order = session.query(Order).filter(Order.id == order_id).first()
        shipment = session.query(Shipment).filter(Shipment.order_id == order_id).first()
        partner_id = getattr(shipment, "assigned_partner_id", None) if shipment else None
        if order is None or shipment is None or partner_id is None:
            raise SmokeFailure(f"Unable to backfill logistics settlement inputs for order {order_id}")

        for ledger in session.query(TransactionLedger).filter(TransactionLedger.order_id == order_id).all():
            if not getattr(ledger, "logistics_partner_id", None):
                ledger.logistics_partner_id = partner_id
            if not getattr(ledger, "shipment_id", None):
                ledger.shipment_id = shipment.id

        for allocation in session.query(OrderLogisticsAllocation).filter(OrderLogisticsAllocation.order_id == order_id).all():
            if not getattr(allocation, "partner_id", None):
                allocation.partner_id = partner_id
            if not getattr(allocation, "shipment_id", None):
                allocation.shipment_id = shipment.id

        create_settlements_on_delivery(order, session)
        session.commit()
    finally:
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the finance cycle smoke: order -> delivery -> settlement -> payout batch -> dispatch preview.")
    parser.add_argument("--reset-seed", action="store_true", help="Reset and reseed the local database before the smoke run.")
    parser.add_argument("--output", default="artifacts/finance_cycle_smoke.json", help="Path to write the JSON smoke summary.")
    args = parser.parse_args()

    print_section("Seed")
    ensure_demo_accounts(args.reset_seed)
    configure_smoke_transfer_provider()

    app = load_app()
    run_tag = str(int(time.time()))
    partner_password = os.environ.get("ZOZI_PARTNER_PASSWORD", "PartnerSmoke123!")
    partner_email = f"finance.partner.{run_tag}@zozi.test"
    partner_username = f"finance_partner_{run_tag}"

    with TestClient(app) as client:
        print_section("Auth")
        admin_headers = login(client, "admin@zozi.com", "admin123")
        supplier_headers = login(client, "supplier@zozi.com", "supplier123")
        try:
            customer_headers = login(client, "customer@zozi.com", "customer123")
        except SmokeFailure:
            customer_headers = register(
                client,
                f"finance.customer.{run_tag}@zozi.test",
                f"finance_customer_{run_tag}",
                "CustomerSmoke123!",
                "customer",
            )
        register(client, partner_email, partner_username, partner_password, "logistics_partner")

        print_section("Partner Setup")
        partner_payload = require_ok(
            client.post(
                "/logistics-partners/",
                headers=admin_headers,
                json={
                    "name": f"Finance Smoke Partner {run_tag}",
                    "code": f"FS{run_tag[-6:]}",
                    "status": "active",
                    "contact_name": "Finance Smoke Partner",
                    "contact_email": partner_email,
                    "portal_user_email": partner_email,
                    "coverage_regions": ["AE"],
                    "service_types": ["last_mile"],
                },
            ),
            "Failed to create logistics partner",
        )
        partner_headers = login(client, partner_email, partner_password)
        ensure_partner_pickup_access(
            client,
            admin_headers,
            partner_headers,
            note_prefix="Finance smoke",
        )

        print_section("Order")
        supplier_products = client.get("/supplier/products", headers=supplier_headers)
        if supplier_products.status_code != 200:
            raise SmokeFailure(f"Failed to load supplier products: {supplier_products.status_code} {supplier_products.text}")
        products = supplier_products.json()
        supplier_id = get_user_id_by_email("supplier@zozi.com")
        if products:
            product = products[0]
        else:
            product = require_ok(
                client.post(
                    "/products/",
                    headers=supplier_headers,
                    json={
                        "name": f"Finance Smoke Product {run_tag}",
                        "description": "Auto-created by finance cycle smoke",
                        "price": 149.0,
                        "category": "Smoke",
                        "stock": 12,
                        "supplier_id": supplier_id,
                    },
                ),
                "Failed to create supplier product",
            )

        order = require_ok(
            client.post(
                "/orders/",
                headers=customer_headers,
                json={
                    "items": [{"product_id": product["id"], "quantity": 1}],
                    "shipping_address": "Smoke Street, Dubai, AE",
                    "city": "Dubai",
                    "country": "AE",
                    "customer_phone": "+971500000888",
                    "delivery_location": "25.2048,55.2708",
                    "delivery_note": "Finance smoke order",
                    "payment_method": "cod",
                },
            ),
            "Failed to create smoke order",
        )
        order_id = cast(int, order["id"])

        shipment = require_ok(
            client.post(
                "/logistics/shipments",
                headers=supplier_headers,
                json={
                    "order_id": order_id,
                    "current_hub": "Dubai Sorting Hub",
                    "package_count": 1,
                    "package_weight_kg": 1.2,
                    "package_dimensions": "25x18x9 cm",
                    "packaging_notes": "Finance smoke parcel",
                    "notes": "Shipment created by finance cycle smoke",
                },
            ),
            "Failed to create shipment",
        )
        shipment_id = cast(int, shipment["id"])

        mark_order_prepared(client, supplier_headers, order_id, "Finance smoke parcel prepared for pickup")

        require_ok(
            client.put(
                f"/logistics-partners/shipments/{shipment_id}/status",
                headers=partner_headers,
                json={"status": "picking_up", "event_type": "pickup_confirmed", "current_hub": "Dubai Sorting Hub"},
            ),
            "Failed to claim pickup",
        )
        require_ok(
            client.put(
                f"/logistics-partners/shipments/{shipment_id}/status",
                headers=partner_headers,
                json={"status": "shipped", "event_type": "picked_from_supplier", "current_hub": "Dubai Sorting Hub"},
            ),
            "Failed to mark shipment shipped",
        )
        require_ok(
            client.put(
                f"/logistics-partners/shipments/{shipment_id}/status",
                headers=partner_headers,
                json={"status": "in_transit", "event_type": "out_for_delivery", "current_hub": "Customer Route Hub"},
            ),
            "Failed to mark shipment in transit",
        )
        delivered = require_ok(
            client.put(
                f"/logistics-partners/shipments/{shipment_id}/status",
                headers=partner_headers,
                json={
                    "status": "delivered",
                    "event_type": "customer_received",
                    "current_hub": "Customer Address",
                    "delivery_signature_name": "Finance Smoke Receiver",
                    "delivery_signature_data_url": "data:image/svg+xml;utf8,%3Csvg%3E%3Cpath%20d%3D%27M0%200%20L1%201%27/%3E%3C/svg%3E",
                },
            ),
            "Failed to mark shipment delivered",
        )

        print_section("Settlement")
        ensure_logistics_settlements(order_id)
        settlement_counts = force_settlements_eligible(order_id)
        supplier_settlements = client.get("/finance/admin/supplier-settlements?limit=200", headers=admin_headers)
        logistics_settlements = client.get("/finance/admin/logistics-settlements?limit=200", headers=admin_headers)
        if supplier_settlements.status_code != 200 or logistics_settlements.status_code != 200:
            raise SmokeFailure("Failed to load finance settlements after delivery")

        print_section("Banking Setup")
        require_ok(
            client.put(
                "/finance/admin/bank-settings",
                headers=admin_headers,
                json={
                    "account_label": "Zozi Smoke Treasury",
                    "beneficiary_name": "Zozi Smoke Treasury LLC",
                    "bank_name": "Smoke Bank",
                    "account_number": "000123456789",
                    "iban": "OM11SMOKE1234567890",
                    "currency": "OMR",
                    "is_active": True,
                    "remittance_reference_prefix": "ZSMOKE",
                },
            ),
            "Failed to save treasury bank settings",
        )

        supplier_bank = require_ok(
            client.put(
                "/supplier/bank-account",
                headers=supplier_headers,
                json={
                    "beneficiary_name": "Smoke Supplier Co",
                    "bank_name": "Supplier Smoke Bank",
                    "account_number": "1234567890",
                    "iban": "OM91SMOKESUP1234567890",
                    "swift_code": "SMOKESUPX",
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
                json={"note": "Finance smoke approved supplier bank account."},
            ),
            "Failed to approve supplier bank account",
        )

        logistics_bank = require_ok(
            client.put(
                "/logistics-partners/me/bank-account",
                headers=partner_headers,
                json={
                    "beneficiary_name": "Smoke Logistics Co",
                    "bank_name": "Logistics Smoke Bank",
                    "account_number": "9988776655",
                    "iban": "OM91SMOKELOG1234567890",
                    "swift_code": "SMOKELOGX",
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
                json={"note": "Finance smoke approved logistics bank account."},
            ),
            "Failed to approve logistics bank account",
        )

        print_section("Payout Processing")
        supplier_payouts = require_ok(
            client.post("/finance/admin/payouts/supplier/process", headers=admin_headers),
            "Failed to process supplier payouts",
        )
        logistics_payouts = require_ok(
            client.post("/finance/admin/payouts/logistics/process", headers=admin_headers),
            "Failed to process logistics payouts",
        )
        if int(supplier_payouts.get("processed", 0)) < 1:
            raise SmokeFailure("Supplier payout process returned no payouts")
        if int(logistics_payouts.get("processed", 0)) < 1:
            raise SmokeFailure("Logistics payout process returned no payouts")

        print_section("Dispatch Preview")
        provider_meta = require_ok(
            client.get("/finance/admin/transfer-providers", headers=admin_headers),
            "Failed to load transfer providers",
        )
        supplier_preview = require_ok(
            client.post(
                "/finance/admin/payouts/supplier/dispatch?provider=configured_bank_api&dry_run=true",
                headers=admin_headers,
            ),
            "Failed to preview supplier dispatch",
        )
        logistics_preview = require_ok(
            client.post(
                "/finance/admin/payouts/logistics/dispatch?provider=configured_bank_api&dry_run=true",
                headers=admin_headers,
            ),
            "Failed to preview logistics dispatch",
        )

    summary = {
        "run_tag": run_tag,
        "order_id": order_id,
        "shipment_id": shipment_id,
        "partner_id": partner_payload["id"],
        "delivery_status": delivered["status"],
        "settlements_created": settlement_counts,
        "supplier_payouts_processed": supplier_payouts["processed"],
        "logistics_payouts_processed": logistics_payouts["processed"],
        "transfer_providers": provider_meta,
        "supplier_dispatch_preview": {
            "status": supplier_preview["status"],
            "dispatchable_count": supplier_preview.get("dispatchable_count", 0),
            "skipped_count": supplier_preview.get("skipped_count", 0),
        },
        "logistics_dispatch_preview": {
            "status": logistics_preview["status"],
            "dispatchable_count": logistics_preview.get("dispatchable_count", 0),
            "skipped_count": logistics_preview.get("skipped_count", 0),
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(output_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()