from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"


class SmokeFailure(RuntimeError):
    pass


@dataclass
class ApiSession:
    email: str
    token: str
    user: dict[str, Any]


class JsonHttpClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        payload: dict[str, Any] | None = None,
        expected: tuple[int, ...] = (200,),
    ) -> Any:
        url = f"{self.base_url}{path}"
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = f"Bearer {token}"

        req = request.Request(url, data=body, headers=headers, method=method.upper())
        status: int
        raw_text: str

        try:
            with request.urlopen(req, timeout=30) as response:
                status = response.getcode()
                raw_text = response.read().decode("utf-8")
        except error.HTTPError as exc:
            status = exc.code
            raw_text = exc.read().decode("utf-8")
        except error.URLError as exc:
            raise SmokeFailure(f"Request failed for {method} {path}: {exc}") from exc

        parsed: Any
        try:
            parsed = json.loads(raw_text) if raw_text else None
        except json.JSONDecodeError:
            parsed = raw_text

        if status not in expected:
            raise SmokeFailure(
                f"Unexpected response for {method} {path}: HTTP {status} body={parsed!r}"
            )
        return parsed


def upload_parcel_proof(client: JsonHttpClient, order_id: int, token: str, note: str) -> dict[str, Any]:
    boundary = f"----ZoziSmoke{int(time.time() * 1000)}"
    file_bytes = b"\xff\xd8\xff\xe0" + (b"\x00" * 256)
    body = b"".join(
        [
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"notes\"\r\n\r\n{note}\r\n".encode("utf-8"),
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"parcel-proof.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode("utf-8"),
            file_bytes,
            f"\r\n--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    req = request.Request(
        f"{client.base_url}/supplier/orders/{order_id}/parcel-proof",
        data=body,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            status = response.getcode()
            raw_text = response.read().decode("utf-8")
    except error.HTTPError as exc:
        status = exc.code
        raw_text = exc.read().decode("utf-8")
    except error.URLError as exc:
        raise SmokeFailure(f"Parcel proof upload failed for order {order_id}: {exc}") from exc

    payload = json.loads(raw_text) if raw_text else {}
    if status not in (200, 201):
        raise SmokeFailure(f"Unexpected parcel proof response: HTTP {status} body={payload!r}")
    return payload


def wait_for_health(client: JsonHttpClient, timeout_seconds: int = 45) -> None:
    deadline = time.time() + timeout_seconds
    last_error: str | None = None
    while time.time() < deadline:
        try:
            client.request("GET", "/health", expected=(200,))
            return
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            time.sleep(1)
    raise SmokeFailure(f"Backend did not become healthy in time. Last error: {last_error}")


def reset_and_seed_sqlite() -> None:
    command = [sys.executable, "db/init_db.py", "--reset", "--seed"]
    completed = subprocess.run(
        command,
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


def login(client: JsonHttpClient, email: str, password: str) -> ApiSession:
    payload = client.request(
        "POST",
        "/auth/login/json",
        payload={"email": email, "password": password},
        expected=(200,),
    )
    return ApiSession(email=email, token=payload["access_token"], user=payload["user"])


def register(client: JsonHttpClient, email: str, username: str, password: str, role: str) -> ApiSession:
    registration_payload = {
        "email": email,
        "username": username,
        "password": password,
        "role": role,
    }
    for attempt in range(2):
        try:
            payload = client.request(
                "POST",
                "/auth/register/json",
                payload=registration_payload,
                expected=(201,),
            )
            return ApiSession(email=email, token=payload["access_token"], user=payload["user"])
        except SmokeFailure as exc:
            if "HTTP 429" in str(exc) and attempt == 0:
                time.sleep(65)
                continue
            raise
    raise SmokeFailure(f"Unable to register user {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a live supplier/logistics partner/admin smoke flow against the backend API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL.")
    parser.add_argument(
        "--reset-seed",
        action="store_true",
        help="Reset and reseed the local SQLite database before running. Stop the backend first when using this on Windows/SQLite.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/live-order-tracking-smoke.json",
        help="Where to write the JSON summary.",
    )
    args = parser.parse_args()

    if args.reset_seed:
        reset_and_seed_sqlite()

    client = JsonHttpClient(args.base_url)
    wait_for_health(client)

    run_tag = str(int(time.time()))
    partner_password = "PartnerSmoke123!"

    admin = login(client, "admin@zozi.com", "admin123")
    supplier = login(client, "supplier@zozi.com", "supplier123")
    try:
        customer = login(client, "customer@zozi.com", "customer123")
    except SmokeFailure:
        customer = register(
            client,
            f"smoke.customer.{run_tag}@zozi.test",
            f"smoke_customer_{run_tag}",
            "CustomerSmoke123!",
            "customer",
        )

    primary_partner_user = register(
        client,
        f"logistics.partner.{run_tag}@zozi.test",
        f"logistics_partner_{run_tag}",
        partner_password,
        "logistics_partner",
    )
    shadow_partner_user = register(
        client,
        f"logistics.shadow.{run_tag}@zozi.test",
        f"logistics_shadow_{run_tag}",
        partner_password,
        "logistics_partner",
    )

    primary_partner = client.request(
        "POST",
        "/logistics-partners/",
        token=admin.token,
        payload={
            "name": f"Smoke Logistics {run_tag}",
            "code": f"SL{run_tag[-6:]}",
            "status": "active",
            "contact_name": "Smoke Partner",
            "contact_email": primary_partner_user.email,
            "portal_user_email": primary_partner_user.email,
            "coverage_regions": ["AE"],
            "service_types": ["last_mile"],
        },
        expected=(201,),
    )
    shadow_partner = client.request(
        "POST",
        "/logistics-partners/",
        token=admin.token,
        payload={
            "name": f"Shadow Logistics {run_tag}",
            "code": f"SH{run_tag[-6:]}",
            "status": "active",
            "contact_name": "Shadow Partner",
            "contact_email": shadow_partner_user.email,
            "portal_user_email": shadow_partner_user.email,
            "coverage_regions": ["AE"],
            "service_types": ["last_mile"],
        },
        expected=(201,),
    )

    client.request(
        "POST",
        f"/logistics-partners/review/profile/{primary_partner['id']}",
        token=admin.token,
        payload={"status": "approved", "note": "Smoke approved primary partner"},
        expected=(200,),
    )
    client.request(
        "POST",
        f"/logistics-partners/review/profile/{shadow_partner['id']}",
        token=admin.token,
        payload={"status": "approved", "note": "Smoke approved shadow partner"},
        expected=(200,),
    )

    primary_partner_login = login(client, primary_partner_user.email, partner_password)
    shadow_partner_login = login(client, shadow_partner_user.email, partner_password)

    primary_service_area = client.request(
        "POST",
        "/logistics-partners/service-areas",
        token=primary_partner_login.token,
        payload={
            "country_name": "United Arab Emirates",
            "country_code": "AE",
            "charge_amount": 12.0,
            "currency": "AED",
            "is_active": True,
        },
        expected=(200,),
    )
    client.request(
        "POST",
        f"/logistics-partners/review/service-areas/{primary_service_area['id']}",
        token=admin.token,
        payload={"status": "approved", "note": "Smoke approved UAE lane"},
        expected=(200,),
    )

    supplier_products = client.request("GET", "/supplier/products", token=supplier.token, expected=(200,))
    if supplier_products:
        product = supplier_products[0]
        product_source = "seeded"
    else:
        product = client.request(
            "POST",
            "/products/",
            token=supplier.token,
            payload={
                "name": f"Smoke Product {run_tag}",
                "description": "Auto-created by the live smoke script",
                "price": 149.0,
                "category": "General",
                "stock": 12,
                "supplier_id": supplier.user["id"],
            },
            expected=(200, 201),
        )
        product_source = "created"

    order = client.request(
        "POST",
        "/orders/",
        token=customer.token,
        payload={
            "items": [{"product_id": product["id"], "quantity": 1}],
            "shipping_address": "Smoke Street, Dubai, AE",
            "city": "Dubai",
            "country": "AE",
            "customer_phone": "+971500000777",
            "delivery_location": "25.2048,55.2708",
            "delivery_note": "Smoke test order",
            "payment_method": "cod",
        },
        expected=(201,),
    )
    order_id = order["id"]
    if order["status"] != "confirmed":
        raise SmokeFailure(f"Expected COD order to be confirmed, got {order['status']!r}")

    direct_status_rejection = client.request(
        "PUT",
        f"/supplier/orders/{order_id}/status",
        token=supplier.token,
        payload={"status": "processing"},
        expected=(409,),
    )

    pre_shipment_label = client.request(
        "GET",
        f"/supplier/orders/{order_id}/label",
        token=supplier.token,
        expected=(200,),
    )
    if pre_shipment_label.get("has_shipment") is not False:
        raise SmokeFailure("Expected pre-shipment label payload before shipment creation")

    direct_shipped_rejected = client.request(
        "PUT",
        f"/supplier/orders/{order_id}/status",
        token=supplier.token,
        payload={"status": "shipped"},
        expected=(409,),
    )
    direct_shipped_detail = str(direct_shipped_rejected.get("detail", ""))
    if "derived automatically" not in direct_shipped_detail:
        raise SmokeFailure("Direct shipped transition did not return the expected derived-status rejection")

    shipment = client.request(
        "POST",
        "/logistics/shipments",
        token=supplier.token,
        payload={
            "order_id": order_id,
            "current_hub": "Dubai Sorting Hub",
            "package_count": 1,
            "package_weight_kg": 1.2,
            "package_dimensions": "25x18x9 cm",
            "packaging_notes": "Smoke scenario parcel",
            "notes": "Supplier shipment created by smoke test",
        },
        expected=(200, 201),
    )
    shipment_id = shipment["id"]

    parcel_proof = upload_parcel_proof(
        client,
        order_id,
        supplier.token,
        "Smoke parcel prepared and ready for logistics handoff",
    )
    if parcel_proof.get("shipment_status") != "prepared":
        raise SmokeFailure(f"Parcel proof did not move the shipment to prepared: {parcel_proof!r}")

    post_shipment_label = client.request(
        "GET",
        f"/supplier/orders/{order_id}/label",
        token=supplier.token,
        expected=(200,),
    )
    if post_shipment_label.get("shipment_id") != shipment_id or post_shipment_label.get("has_shipment") is not True:
        raise SmokeFailure("Post-shipment label did not reflect the created shipment")

    claim_pickup = client.request(
        "PUT",
        f"/logistics-partners/shipments/{shipment_id}/status",
        token=primary_partner_login.token,
        payload={
            "status": "picking_up",
            "current_hub": "Dubai Sorting Hub",
            "event_type": "pickup_confirmed",
            "notes": "Smoke run partner claimed supplier pickup",
        },
        expected=(200,),
    )

    primary_partner_shipments = client.request(
        "GET",
        "/logistics-partners/shipments?page=1&page_size=20",
        token=primary_partner_login.token,
        expected=(200,),
    )
    shadow_partner_shipments = client.request(
        "GET",
        "/logistics-partners/shipments?page=1&page_size=20",
        token=shadow_partner_login.token,
        expected=(200,),
    )

    primary_ids = {item["id"] for item in primary_partner_shipments["items"]}
    shadow_ids = {item["id"] for item in shadow_partner_shipments["items"]}
    if shipment_id not in primary_ids:
        raise SmokeFailure("Assigned logistics partner cannot see the shipment")
    if shipment_id in shadow_ids:
        raise SmokeFailure("Unassigned logistics partner can see a shipment it should not access")

    handoff_update = client.request(
        "PUT",
        f"/logistics-partners/shipments/{shipment_id}/status",
        token=primary_partner_login.token,
        payload={
            "status": "shipped",
            "current_hub": "Dubai Sorting Hub",
            "event_type": "picked_from_supplier",
            "notes": "Smoke run parcel scanned at supplier handoff",
        },
        expected=(200,),
    )

    partner_status_update = client.request(
        "PUT",
        f"/logistics-partners/shipments/{shipment_id}/status",
        token=primary_partner_login.token,
        payload={
            "status": "in_transit",
            "current_hub": "Customer Route Hub",
            "event_type": "out_for_delivery",
            "notes": "Smoke run moved parcel to partner route",
        },
        expected=(200,),
    )

    customer_tracking = client.request(
        "GET",
        f"/orders/{order_id}/tracking",
        token=customer.token,
        expected=(200,),
    )
    admin_orders = client.request("GET", "/admin/orders?limit=500", token=admin.token, expected=(200,))
    admin_order = next((item for item in admin_orders if item["id"] == order_id), None)
    if not admin_order:
        raise SmokeFailure("Admin orders list does not include the smoke order")

    shipment_tracking = customer_tracking["shipments"][0]
    if shipment_tracking["assigned_partner_id"] != primary_partner["id"]:
        raise SmokeFailure("Tracking payload does not show the assigned logistics partner")
    if shipment_tracking["status"] != "in_transit":
        raise SmokeFailure("Tracking payload did not update after partner status change")

    summary = {
        "base_url": args.base_url,
        "run_tag": run_tag,
        "product": {"id": product["id"], "name": product.get("name")},
        "product_source": product_source,
        "order": {
            "id": order_id,
            "created_status": order["status"],
            "direct_status_rejection": direct_status_rejection.get("detail"),
            "direct_shipped_rejection": direct_shipped_detail,
        },
        "pre_shipment_label": {
            "has_shipment": pre_shipment_label["has_shipment"],
            "sheet_mode": pre_shipment_label["sheet_mode"],
            "scan_code": pre_shipment_label["scan_code"],
        },
        "shipment": {
            "id": shipment_id,
            "tracking_number": shipment.get("tracking_number"),
            "assigned_partner_id": shipment.get("assigned_partner_id"),
            "assigned_partner_name": shipment.get("assigned_partner_name"),
            "claim_pickup_status": claim_pickup.get("status"),
            "handoff_status": handoff_update.get("status"),
        },
        "partner_visibility": {
            "assigned_partner_visible_ids": sorted(primary_ids),
            "shadow_partner_visible_ids": sorted(shadow_ids),
        },
        "partner_status_update": partner_status_update,
        "tracking": {
            "order_status": customer_tracking["order_status"],
            "shipment_count": customer_tracking["shipment_count"],
            "primary_shipment_status": shipment_tracking["status"],
            "primary_shipment_partner": shipment_tracking.get("assigned_partner_name"),
        },
        "admin_order": {
            "id": admin_order["id"],
            "status": admin_order["status"],
            "total_amount": admin_order.get("total_amount") or admin_order.get("total"),
        },
        "created_partners": {
            "primary": {
                "id": primary_partner["id"],
                "email": primary_partner_user.email,
                "code": primary_partner["code"],
            },
            "shadow": {
                "id": shadow_partner["id"],
                "email": shadow_partner_user.email,
                "code": shadow_partner["code"],
            },
        },
        "customer_user": {
            "id": customer.user["id"],
            "email": customer.email,
        },
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(output_path)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
