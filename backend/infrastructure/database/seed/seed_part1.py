import json
import logging
import os
import re
import warnings
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from infrastructure.database.database import engine
from domains.governance.models.user import User
from domains.catalog.models.products import Category
from domains.catalog.models.products import Product
from domains.comms.models.marketing import EmailTemplate
from domains.comms.models.suppliers import SupplierProfile
from domains.country.models.countries import CountryConfig
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import LogisticsPartnerServiceArea
from domains.logistics.models.logistics import LogisticsPricingProfile
from domains.logistics.models.logistics import LogisticsVehicleRule
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from domains.orders.models.orders import OrderLogisticsAllocation
from domains.hr.models.employee_models import (
def _seed_password(env_key: str) -> str:
    value = os.getenv(env_key)
    if not value:
        default = "DevSeed123!"
        warnings.warn(
            f"Seed password environment variable {env_key} is not set. "
            f"Using default dev password '{default}'. "
            "Set it before running seed in production."
        )
        return default
    return value


def _ensure_demo_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    role: str,
    log_label: str,
) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            username = f"{username}_{role}"
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            role=role,
            country_code="AE",
        )
        db.add(user)
        logger.info("Seeded default %s user", log_label)
    else:
        if user.role != role:
            user.role = role
    
    existing_hash = getattr(user, "hashed_password", "") or ""
    if not existing_hash or not verify_password(password, existing_hash):
        user.hashed_password = get_password_hash(password)

    user.email_verified = True
    if hasattr(user, "is_active") and getattr(user, "is_active") is not True:
        user.is_active = True
    return user


def _to_decimal(value: Decimal | float | int | str | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _json_dumps(value: object) -> str:
    return json.dumps(value, default=float)


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "seed-item"


def _filter_model_payload(model: Any, payload: dict[str, object]) -> dict[str, object]:
    allowed_fields = set(model.__table__.columns.keys())
    return {key: value for key, value in payload.items() if key in allowed_fields}


def _prepare_database_for_seed() -> None:
    pass


def _ensure_demo_supplier_profile(
    db: Session,
    *,
    supplier_user: User,
) -> SupplierProfile:
    supplier_profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == supplier_user.id)
        .first()
    )
    if not supplier_profile:
        supplier_profile = SupplierProfile(
            user_id=supplier_user.id,
            business_name="ZOZI Supplier Demo",
            slug=DEMO_SUPPLIER_SLUG,
        )
        db.add(supplier_profile)
        logger.info("Seeded default supplier profile")

    supplier_profile.business_name = "ZOZI Supplier Demo"
    supplier_profile.slug = getattr(supplier_profile, "slug", None) or DEMO_SUPPLIER_SLUG
    supplier_profile.business_type = "retailer"
    supplier_profile.country_code = "AE"
    supplier_profile.phone_business = "+971500000000"
    supplier_profile.website = "https://supplier.zozi.local"
    supplier_profile.address = json.dumps({
        "line1": "Dubai Design District",
        "city": "Dubai",
        "country": "United Arab Emirates",
        "country_code": "AE",
    })
    supplier_profile.is_terms_accepted = True
    supplier_profile.terms_version = "v1"
    supplier_profile.verification_status = "approved"
    supplier_profile.is_active = True
    return supplier_profile


def _upsert_demo_product(db: Session, product_data: dict[str, object]) -> None:
    payload = _filter_model_payload(Product, product_data)
    payload.setdefault("slug", _slugify(str(product_data["name"])))
    payload.setdefault("country_code", "AE")

    existing = db.query(Product).filter(Product.name == product_data["name"]).first()
    if not existing:
        db.add(Product(**payload))
        return

    for field, value in payload.items():
        setattr(existing, field, value)


def _upsert_email_template(db: Session, template_data: dict[str, object]) -> None:
    payload = dict(template_data)
    if "html_content" in payload and "body_html" not in payload:
        payload["body_html"] = payload["html_content"]
    if "body_html" in payload and "html_content" not in payload:
        payload["html_content"] = payload["body_html"]
    if "text_content" in payload and "body_text" not in payload:
        payload["body_text"] = payload["text_content"]
    if "body_text" in payload and "text_content" not in payload:
        payload["text_content"] = payload["body_text"]

    filtered_payload = _filter_model_payload(EmailTemplate, payload)
    existing = db.query(EmailTemplate).filter(EmailTemplate.name == str(template_data["name"])).first()
    if not existing:
        db.add(EmailTemplate(**filtered_payload))
        logger.info("Seeded email template: %s", template_data["name"])
        return

    for field, value in filtered_payload.items():
        setattr(existing, field, value)


def _ensure_demo_service_area(
    db: Session,
    *,
    partner: LogisticsPartner,
    admin_id: int,
) -> LogisticsPartnerServiceArea:
    area = (
        db.query(LogisticsPartnerServiceArea)
        .filter(
            LogisticsPartnerServiceArea.partner_id == partner.id,
            LogisticsPartnerServiceArea.country_code == "AE",
            LogisticsPartnerServiceArea.origin_city == "Dubai",
            LogisticsPartnerServiceArea.city_name == "Dubai",
        )
        .first()
    )
    if not area:
        area = LogisticsPartnerServiceArea(
            partner_id=partner.id,
            country_code="AE",
            country_name="United Arab Emirates",
            origin_city="Dubai",
            city_name="Dubai",
        )
        db.add(area)

    area.country_name = "United Arab Emirates"
    area.origin_city = "Dubai"
    area.city_name = "Dubai"
    area.zone_label = "Dubai Demo Lane"
    area.charge_amount = Decimal("12.00")
    area.minimum_charge = Decimal("12.00")
    area.per_kg_rate = Decimal("0.60")
    area.pickup_charge = Decimal("1.50")
    area.dropoff_charge = Decimal("1.50")
    area.currency = "AED"
    area.delivery_days_min = 0
    area.delivery_days_max = 1
    area.is_active = True
    area.approval_status = "approved"
    area.review_note = "Seeded demo coverage for live pickup acceptance QA"
    area.reviewed_by = admin_id
    area.reviewed_at = _utcnow()
    return area


def _ensure_demo_pricing_profile(
    db: Session,
    *,
    partner: LogisticsPartner,
    service_area: LogisticsPartnerServiceArea,
    admin_id: int,
) -> LogisticsPricingProfile:
    profile = (
        db.query(LogisticsPricingProfile)
        .filter(
            LogisticsPricingProfile.partner_id == partner.id,
            LogisticsPricingProfile.service_area_id == service_area.id,
            LogisticsPricingProfile.profile_name == "Dubai Demo Default",
        )
        .first()
    )
    if not profile:
        profile = LogisticsPricingProfile(
            partner_id=partner.id,
            service_area_id=service_area.id,
            profile_name="Dubai Demo Default",
        )
        db.add(profile)

    profile.base_in_city_fee = Decimal("9.00")
    profile.per_kg_rate = Decimal("0.60")
    profile.minimum_charge = Decimal("12.00")
    profile.maximum_charge = Decimal("40.00")
    profile.fuel_multiplier = Decimal("1.0000")
    profile.currency = "AED"
    profile.is_active = True
    profile.approval_status = "approved"
    profile.review_note = "Seeded demo pricing for live pickup acceptance QA"
    profile.reviewed_by = admin_id
    profile.reviewed_at = _utcnow()
    return profile


def _ensure_demo_vehicle_rule(
    db: Session,
    *,
    partner: LogisticsPartner,
    service_area: LogisticsPartnerServiceArea,
    admin_id: int,
    vehicle_type: str,
    max_weight_kg: str,
    cost_multiplier: str,
    priority_rank: int,
) -> LogisticsVehicleRule:
    rule = (
        db.query(LogisticsVehicleRule)
        .filter(
            LogisticsVehicleRule.partner_id == partner.id,
            LogisticsVehicleRule.service_area_id == service_area.id,
            LogisticsVehicleRule.vehicle_type == vehicle_type,
        )
        .first()
    )
    if not rule:
        rule = LogisticsVehicleRule(
            partner_id=partner.id,
            service_area_id=service_area.id,
            vehicle_type=vehicle_type,
        )
        db.add(rule)

    rule.route_scope = "any"
    rule.max_weight_kg = Decimal(max_weight_kg)
    rule.cost_multiplier = Decimal(cost_multiplier)
    rule.priority_rank = priority_rank
    rule.is_active = True
    rule.approval_status = "approved"
    rule.review_note = "Seeded demo vehicle option"
    rule.reviewed_by = admin_id
    rule.reviewed_at = _utcnow()
    return rule


def _ensure_demo_pickup_ready_shipment(
    db: Session,
    *,
    admin_user: User,
    customer_user: User,
    supplier_user: User,
    logistics_partner: LogisticsPartner,
    service_area: LogisticsPartnerServiceArea,
) -> None:
    product = (
        db.query(Product)
        .filter(
            Product.supplier_id == supplier_user.id,
            Product.name == "Luxury Handbag",
        )
        .first()
    )
    if product is None:
        logger.warning("Skipping demo pickup-ready shipment seed because the sample supplier product is missing")
        return

    supplier_profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == supplier_user.id).first()
    supplier_city = (getattr(supplier_profile, "city", None) or "Dubai").strip() or "Dubai"
    weight_kg = 4.5
    quote = quote_shipping_for_destination(
        db,
        country="AE",
        city="Dubai",
        partner_id=logistics_partner.id,
        supplier_city=supplier_city,
        total_weight_kg=weight_kg,
        categories=[product.category] if getattr(product, "category", None) else [],
        pickup_count=1,
        dropoff_count=1,
    )
    if quote is None:
        raise RuntimeError("Unable to seed demo pickup-ready shipment because the demo logistics quote could not be resolved")

    pricing_breakdown = quote["pricing_breakdown"]
    shipping_amount = _to_decimal(pricing_breakdown.get("shipping_amount"))
    pickup_charge = _to_decimal(pricing_breakdown.get("pickup_charge"))
    dropoff_charge = _to_decimal(pricing_breakdown.get("dropoff_charge"))
    subtotal_amount = _to_decimal(getattr(product, "price", 0))
    now = _utcnow()

    shipment = db.query(Shipment).filter(Shipment.tracking_number == DEMO_PICKUP_TRACKING_NUMBER).first()
    order = db.query(Order).filter(Order.id == shipment.order_id).first() if shipment else None
    if order is None:
        order = Order(
            order_number=f"DEMO-{DEMO_PICKUP_TRACKING_NUMBER}",
            customer_id=customer_user.id,
            user_id=customer_user.id,
            status="processing",
            payment_status="pending",
            payment_method="cod",
            subtotal=subtotal_amount,
            shipping_fee=shipping_amount,
            tax_amount=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            total=subtotal_amount + shipping_amount,
            total_amount=subtotal_amount + shipping_amount,
            currency="AED",
            country_code="AE",
        )
        db.add(order)
        db.flush()

    order.order_number = order.order_number or f"DEMO-{DEMO_PICKUP_TRACKING_NUMBER}"
    order.customer_id = customer_user.id
    order.user_id = customer_user.id
    order.subtotal = subtotal_amount
    order.shipping_fee = shipping_amount
    order.tax_amount = Decimal("0.00")
    order.subtotal_amount = subtotal_amount
    order.discount_amount = Decimal("0.00")
    order.vat_amount = Decimal("0.00")
    order.shipping_amount = shipping_amount
    order.total = subtotal_amount + shipping_amount
    order.total_amount = subtotal_amount + shipping_amount
    order.payment_method = "cod"
    order.payment_status = order.payment_status or "pending"
    order.currency = "AED"
    order.status = "processing"
    order.shipping_address = "Marina Walk, Dubai, United Arab Emirates"
    order.shipping_city = "Dubai"
    order.shipping_country = "AE"
    order.shipping_postal_code = "00000"
    order.customer_phone = "+971500000222"
    order.delivery_location = "Dubai Marina"
    order.delivery_note = "Seeded demo order for logistics pickup acceptance"
    order.tracking_number = DEMO_PICKUP_TRACKING_NUMBER
    order.selected_partner_id = logistics_partner.id
    order.selected_service_area_id = service_area.id
    order.estimated_delivery_min = getattr(service_area, "delivery_days_min", None)
    order.estimated_delivery_max = getattr(service_area, "delivery_days_max", None)

    order_item = (
        db.query(OrderItem)
        .filter(
            OrderItem.order_id == order.id,
            OrderItem.product_id == product.id,
        )
        .first()
    )
    if not order_item:
        order_item = OrderItem(order_id=order.id, product_id=product.id)
        db.add(order_item)
    order_item.quantity = 1
    order_item.supplier_id = getattr(supplier_profile, "id", None)
    order_item.product_name = product.name
    order_item.product_image = getattr(product, "image_url", None)
    order_item.unit_price = subtotal_amount
    order_item.total_price = subtotal_amount
    order_item.price = subtotal_amount
    order_item.selected_size = ""
    order_item.selected_color = getattr(product, "color", None) or ""

    db.flush()

    if shipment is None:
        shipment = Shipment(order_id=order.id, supplier_id=supplier_user.id)
        db.add(shipment)
        db.flush()

    shipment.order_id = order.id
    shipment.supplier_id = supplier_user.id
    shipment.assigned_partner_id = logistics_partner.id
    shipment.carrier_name = "ZOZI Demo Courier"
    shipment.tracking_number = DEMO_PICKUP_TRACKING_NUMBER
    shipment.status = "processing"
    shipment.distribution_channel = "local_courier"
    shipment.current_hub = "Dubai Supplier Hub"
    shipment.scan_code = f"ORDER-{order.id}"
    shipment.accepted_vehicle_rule_id = None
    shipment.accepted_vehicle_type = None
    shipment.accepted_vehicle_multiplier = None
    shipment.accepted_vehicle_selected_at = None
    shipment.package_count = 1
    shipment.package_weight_kg = weight_kg
    shipment.package_dimensions = getattr(product, "dimensions", None) or "40x30x20 cm"
    shipment.packaged_at = now
    shipment.packaged_by_user_id = supplier_user.id
    shipment.packaging_notes = "Seeded demo parcel ready for live pickup acceptance"
    shipment.shipped_at = None
    shipment.estimated_delivery = None
    shipment.actual_delivery = None
    shipment.delivery_signature_name = None
    shipment.delivery_signature_data_url = None
    shipment.delivery_signature_captured_at = None
    shipment.notes = "Prepared demo shipment for logistics partner QA"

    allocation = (
        db.query(OrderLogisticsAllocation)
        .filter(
            OrderLogisticsAllocation.order_id == order.id,
            OrderLogisticsAllocation.supplier_id == supplier_user.id,
        )
        .first()
    )
    if not allocation:
        allocation = OrderLogisticsAllocation(order_id=order.id, supplier_id=supplier_user.id)
        db.add(allocation)

    allocation.shipment_id = shipment.id
    allocation.partner_id = logistics_partner.id
    allocation.service_area_id = service_area.id
    allocation.allocation_source = "seed_demo"
    allocation.partner_name_snapshot = logistics_partner.name
    allocation.partner_code_snapshot = logistics_partner.code
    allocation.service_area_label_snapshot = getattr(service_area, "zone_label", None) or "Dubai Demo Lane"
    allocation.destination_country = "AE"
    allocation.destination_city = "Dubai"
    allocation.shipping_amount = shipping_amount
    allocation.pickup_charge = pickup_charge
    allocation.dropoff_charge = dropoff_charge
    allocation.accepted_vehicle_rule_id = None
    allocation.accepted_vehicle_type = None
    allocation.accepted_vehicle_multiplier = None
    allocation.accepted_shipping_amount = None
    allocation.accepted_pickup_charge = None
    allocation.accepted_dropoff_charge = None
    allocation.estimated_delivery_min = getattr(service_area, "delivery_days_min", None)
    allocation.estimated_delivery_max = getattr(service_area, "delivery_days_max", None)
    allocation.currency = str(quote.get("currency") or "AED")
    allocation.pricing_breakdown_json = _json_dumps(pricing_breakdown)
    allocation.accepted_pricing_breakdown_json = None
    allocation.accepted_at = None

    demo_event = (
        db.query(ShipmentEvent)
        .filter(
            ShipmentEvent.shipment_id == shipment.id,
            ShipmentEvent.event_type == "supplier_prepared",
            ShipmentEvent.notes == DEMO_PICKUP_EVENT_NOTE,
        )
        .first()
    )
    if not demo_event:
        demo_event = ShipmentEvent(
            shipment_id=shipment.id,
            order_id=order.id,
            supplier_id=supplier_user.id,
            actor_user_id=supplier_user.id,
            actor_role="supplier",
            event_type="supplier_prepared",
            notes=DEMO_PICKUP_EVENT_NOTE,
        )
        db.add(demo_event)

    demo_event.order_id = order.id
    demo_event.supplier_id = supplier_user.id
    demo_event.actor_user_id = supplier_user.id
    demo_event.actor_role = "supplier"
    demo_event.status = "processing"
    demo_event.event_type = "supplier_prepared"
    demo_event.status_after = "processing"
    demo_event.distribution_channel = "local_courier"
    demo_event.location = "Dubai Supplier Hub"
    demo_event.scan_code = shipment.scan_code
    demo_event.notes = DEMO_PICKUP_EVENT_NOTE
    demo_event.created_at = now

    logistics_partner.verified_at = now
    logistics_partner.verified_by = admin_user.id

    logger.info("Seeded demo pickup-ready logistics shipment %s", DEMO_PICKUP_TRACKING_NUMBER)

