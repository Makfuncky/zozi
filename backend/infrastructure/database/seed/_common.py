"""Shared seed functions — all domain models loaded lazily (Law 1 compliant).

This module contains the canonical implementations of all seed helpers.
Domain models are resolved at call time via string-based lazy references,
so infrastructure never imports domains at module load time.
"""
from __future__ import annotations

import json
import logging
import os
import re
import secrets
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker, Session
from infrastructure.database.database import engine, _IS_SQLITE

from infrastructure.database.seed.models import get_model

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
logger = logging.getLogger(__name__)

DEMO_PICKUP_TRACKING_NUMBER = "TRACK-DEMO-PICKUP-READY-001"
DEMO_PICKUP_EVENT_NOTE = "Demo pickup-ready reset"
DEMO_SUPPLIER_SLUG = "zozi-supplier-demo"


def _utcnow():
    from infrastructure.utils.datetime_utils import utcnow
    return utcnow()


def _seed_password(env_key: str) -> str:
    value = os.getenv(env_key)
    if not value:
        generated = secrets.token_urlsafe(16)
        logger.warning(
            "Seed password environment variable %s is not set. "
            "Generated a random password: %s . "
            "Set %s to use a deterministic password.",
            env_key,
            generated,
            env_key,
        )
        return generated
    return value


def _ensure_demo_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
    role: str,
    log_label: str,
):
    from infrastructure.utils.auth import get_password_hash, verify_password
    User = get_model("User")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        existing_username = db.query(User).filter(User.email == email).first()
        if existing_username:
            email = f"{username}_{role}@example.com"
        user = User(
            email=email,
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
    """Prepare the database for bulk seed operations.

    For SQLite backends this disables foreign-key enforcement so seed data
    can be inserted in any order without triggering constraint violations.
    PostgreSQL handles this via DEFERRABLE constraints in migrations, so
    this is a no-op there.
    """
    if _IS_SQLITE:
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys=OFF"))
            logger.info("SQLite foreign keys disabled for seed")


def _ensure_demo_supplier_profile(
    db: Session,
    *,
    supplier_user,
):
    SupplierProfile = get_model("SupplierProfile")
    supplier_profile = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == supplier_user.id)
        .first()
    )
    if not supplier_profile:
        supplier_profile = SupplierProfile(
            user_id=supplier_user.id,
            business_name="ZOZI Supplier Demo",
        )
        db.add(supplier_profile)
        logger.info("Seeded default supplier profile")

    supplier_profile.business_name = "ZOZI Supplier Demo"
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
    Product = get_model("Product")
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
    EmailTemplate = get_model("EmailTemplate")
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
    partner,
    admin_id: int,
):
    LogisticsPartnerServiceArea = get_model("LogisticsPartnerServiceArea")
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
    partner,
    service_area,
    admin_id: int,
):
    LogisticsPricingProfile = get_model("LogisticsPricingProfile")
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
    partner,
    service_area,
    admin_id: int,
    vehicle_type: str,
    max_weight_kg: str,
    cost_multiplier: str,
    priority_rank: int,
):
    LogisticsVehicleRule = get_model("LogisticsVehicleRule")
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
    admin_user,
    customer_user,
    supplier_user,
    logistics_partner,
    service_area,
) -> None:
    from infrastructure.database.seed.logistics import quote_shipping_for_destination
    Product = get_model("Product")
    Shipment = get_model("Shipment")
    Order = get_model("Order")
    OrderItem = get_model("OrderItem")
    OrderLogisticsAllocation = get_model("OrderLogisticsAllocation")
    ShipmentEvent = get_model("ShipmentEvent")
    SupplierProfile = get_model("SupplierProfile")

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
            status_code="processing",
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
    order.status_code = "processing"
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


def _seed_countries(db: Session) -> None:
    logger.info("Seeding countries...")
    CountryConfig = get_model("CountryConfig")

    existing_count = db.query(CountryConfig).count()
    if existing_count > 0:
        logger.info(f"Countries already exist ({existing_count}), skipping")
        return

    demo_countries = [
        {
            "code": "AE",
            "name": "United Arab Emirates",
            "currency": "AED",
            "timezone": "Asia/Dubai",
            "currency_symbol": "د.إ",
            "phone_code": "+971",
            "language": "en",
            "is_active": True,
            "tax_type": "VAT",
            "tax_rate": Decimal("0.05"),
            "tax_name": "VAT",
            "tax_inclusive": False,
        },
        {
            "code": "SA",
            "name": "Saudi Arabia",
            "currency": "SAR",
            "timezone": "Asia/Riyadh",
            "currency_symbol": "﷼",
            "phone_code": "+966",
            "language": "ar",
            "is_active": True,
            "tax_type": "VAT",
            "tax_rate": Decimal("0.15"),
            "tax_name": "VAT",
            "tax_inclusive": False,
        },
        {
            "code": "IN",
            "name": "India",
            "currency": "INR",
            "timezone": "Asia/Kolkata",
            "currency_symbol": "₹",
            "phone_code": "+91",
            "language": "en",
            "is_active": True,
            "tax_type": "GST",
            "tax_rate": Decimal("0.18"),
            "tax_name": "GST",
            "tax_inclusive": False,
        },
    ]

    for c in demo_countries:
        country = CountryConfig(**c)
        db.add(country)
        logger.info(f"Seeded country: {c['code']} - {c['name']}")

    db.commit()


def _seed_employee_data(db: Session) -> None:
    logger.info("Seeding employee data...")

    from infrastructure.database.rls_interceptor import set_rls_context
    set_rls_context(None, is_restricted=False)

    CountryConfig = get_model("CountryConfig")
    User = get_model("User")
    Employee = get_model("Employee")
    Office = get_model("Office")
    from infrastructure.utils.auth import get_password_hash

    countries = db.query(CountryConfig).limit(1000).all()
    if not countries:
        logger.warning("No countries found, skipping employee seeding")
        return

    existing_count = db.query(Employee).count()
    if existing_count > 0:
        logger.info(f"Employees already exist ({existing_count}), skipping")
        return

    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        admin = _ensure_demo_user(
            db,
            email="admin@zozi.com",
            username="admin",
            password=_seed_password("SEED_ADMIN_PASSWORD"),
            role="admin",
            log_label="admin"
        )

    for country in countries[:3]:
        office = Office(
            name=f"{country.name} Office",
            country_code=country.code,
            city=country.name,
            latitude=25.0,
            longitude=45.0
        )
        db.add(office)

    db.commit()

    for i, country in enumerate(countries[:5]):
        office = db.query(Office).filter(Office.country_code == country.code).first()
        user = User(
            email=f"employee{i}@zozi.com",
            hashed_password=get_password_hash(_seed_password("SEED_EMPLOYEE_PASSWORD")),
            role="employee",
            full_name=f"Employee {i}",
            country_code=country.code,
        )
        db.add(user)
        db.commit()

        emp = Employee(
            user_id=user.id,
            employee_code=f"EMP{i:04d}",
            office_id=office.id if office else None,
            department="Operations",
            position="Staff",
            employment_type="full_time",
            employment_status="active",
            salary=Decimal("500.000"),
            currency="OMR",
            country_code=country.code,
            hire_date=_utcnow(),
            gender="male",
        )
        db.add(emp)

    db.commit()
    logger.info("Employee data seeded successfully")


def seed_data(session_factory: Callable[[], Session] | Session | None = None) -> None:
    _prepare_database_for_seed()
    if isinstance(session_factory, Session):
        db = session_factory
    else:
        db = (session_factory or SessionLocal)()
    try:
        _seed_countries(db)
        admin_user = _ensure_demo_user(
            db,
            email="admin@zozi.com",
            username="admin",
            password=_seed_password("SEED_ADMIN_PASSWORD"),
            role="admin",
            log_label="admin",
        )
        supplier_user = _ensure_demo_user(
            db,
            email="supplier@zozi.com",
            username="supplier",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="supplier",
        )
        customer_user = _ensure_demo_user(
            db,
            email="customer@zozi.com",
            username="customer",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="customer",
        )
        logistics_user = _ensure_demo_user(
            db,
            email="logistics@zozi.com",
            username="logistics",
            password=_seed_password("SEED_LOGISTICS_PASSWORD"),
            role="logistics_partner",
            log_label="logistics partner",
        )

        _ensure_demo_user(
            db,
            email="admin@test.com",
            username="admin_test",
            password=_seed_password("SEED_ADMIN_PASSWORD"),
            role="admin",
            log_label="test admin",
        )
        _ensure_demo_user(
            db,
            email="supplier@test.com",
            username="supplier_test",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="test supplier",
        )
        _ensure_demo_user(
            db,
            email="customer@test.com",
            username="customer_test",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="test customer",
        )

        # Extended demo users from across GCC regions
        _ensure_demo_user(
            db,
            email="fashion.supplier@zozi.com",
            username="fashion_house",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="fashion supplier",
        )
        _ensure_demo_user(
            db,
            email="home.supplier@zozi.com",
            username="home_living",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="home supplier",
        )
        _ensure_demo_user(
            db,
            email="beauty.supplier@zozi.com",
            username="beauty_parlour",
            password=_seed_password("SEED_SUPPLIER_PASSWORD"),
            role="supplier",
            log_label="beauty supplier",
        )
        _ensure_demo_user(
            db,
            email="sara@customer.com",
            username="sara_omani",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="customer (Oman)",
        )
        _ensure_demo_user(
            db,
            email="mohammed@customer.com",
            username="mohammed_ksa",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="customer (KSA)",
        )
        _ensure_demo_user(
            db,
            email="fatima@customer.com",
            username="fatima_uae",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="customer (UAE)",
        )
        _ensure_demo_user(
            db,
            email="khalid@customer.com",
            username="khalid_bahrain",
            password=_seed_password("SEED_CUSTOMER_PASSWORD"),
            role="customer",
            log_label="customer (Bahrain)",
        )
        _ensure_demo_user(
            db,
            email="fast.delivery@zozi.com",
            username="fast_delivery",
            password=_seed_password("SEED_LOGISTICS_PASSWORD"),
            role="logistics_partner",
            log_label="logistics (KSA)",
        )
        _ensure_demo_user(
            db,
            email="gulf.shipping@zozi.com",
            username="gulf_shipping",
            password=_seed_password("SEED_LOGISTICS_PASSWORD"),
            role="logistics_partner",
            log_label="logistics (Oman)",
        )

        db.flush()
        supplier_id = supplier_user.id
        admin_id = admin_user.id
        logistics_user_id = logistics_user.id

        supplier_profile = _ensure_demo_supplier_profile(
            db,
            supplier_user=supplier_user,
        )

        LogisticsPartner = get_model("LogisticsPartner")
        logistics_partner = db.query(LogisticsPartner).filter(LogisticsPartner.user_id == logistics_user_id).first()
        if not logistics_partner:
            logistics_partner = db.query(LogisticsPartner).filter(LogisticsPartner.code == "ZOZI-DEMO-LP").first()

        if not logistics_partner:
            logistics_partner = LogisticsPartner(
                name="ZOZI Logistics Demo",
                code="ZOZI-DEMO-LP",
                user_id=logistics_user_id,
            )
            db.add(logistics_partner)
            logger.info("Seeded default logistics partner profile")

        logistics_partner.name = "ZOZI Logistics Demo"
        logistics_partner.code = "ZOZI-DEMO-LP"
        logistics_partner.contact_name = "ZOZI Logistics Team"
        logistics_partner.contact_email = "logistics@zozi.com"
        logistics_partner.contact_phone = "+971500000111"
        logistics_partner.website = "https://logistics.zozi.local"
        logistics_partner.coverage_regions = json.dumps(["United Arab Emirates", "Saudi Arabia"])
        logistics_partner.service_types = json.dumps(["ground", "same_day"])
        logistics_partner.status = "active"
        logistics_partner.verification_status = "approved"
        logistics_partner.verification_note = "Seeded demo logistics partner approved for browser QA"
        logistics_partner.verified_by = admin_id
        logistics_partner.verified_at = _utcnow()
        logistics_partner.user_id = logistics_user_id

        db.flush()

        Category = get_model("Category")
        Product = get_model("Product")
        categories_data = [
            {"name": "Fashion",      "slug": "fashion",      "icon": "👗", "sort_order": 1,
             "image_url": "https://picsum.photos/seed/fashion/600/400"},
            {"name": "Accessories",  "slug": "accessories",  "icon": "💍", "sort_order": 2,
             "image_url": "https://picsum.photos/seed/accessories/600/400"},
            {"name": "Electronics",  "slug": "electronics",  "icon": "📱", "sort_order": 3,
             "image_url": "https://picsum.photos/seed/electronics/600/400"},
            {"name": "Beauty",       "slug": "beauty",       "icon": "💄", "sort_order": 4,
             "image_url": "https://picsum.photos/seed/beauty/600/400"},
            {"name": "Home & Living","slug": "home-living",  "icon": "🏠", "sort_order": 5,
             "image_url": "https://picsum.photos/seed/home/600/400"},
            {"name": "Sports",       "slug": "sports",       "icon": "⚽", "sort_order": 6,
             "image_url": "https://picsum.photos/seed/sports/600/400"},
            {"name": "Footwear",     "slug": "footwear",     "icon": "👟", "sort_order": 7,
             "image_url": "https://picsum.photos/seed/shoes/600/400"},
            {"name": "Watches",      "slug": "watches",      "icon": "⌚", "sort_order": 8,
             "image_url": "https://picsum.photos/seed/watches/600/400"},
            {"name": "General",      "slug": "general",      "icon": "📦", "sort_order": 9,
             "image_url": "https://picsum.photos/seed/general/600/400"},
            {"name": "Furniture",    "slug": "furniture",    "icon": "🛋️", "sort_order": 10,
             "image_url": "https://picsum.photos/seed/furniture/600/400"},
        ]
        for cat_data in categories_data:
            existing_cat = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing_cat:
                db.add(Category(is_active=True, **cat_data))
                logger.info("Seeded category: %s", cat_data["name"])
            else:
                for field, value in cat_data.items():
                    setattr(existing_cat, field, value)

        extended_products = [
            {"name": "Luxury Handbag", "description": "Premium leather handbag with gold accents, perfect for any occasion.",
             "price": 299.99, "compare_price": 399.99, "category": "Fashion", "brand": "Luxury Edition",
             "rating": 4.5, "stock": 15, "color": "Black", "image_url": "https://picsum.photos/seed/handbag1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_featured": True, "is_active": True},
            {"name": "Designer Watch", "description": "Elegant Swiss-movement timepiece with sapphire crystal glass.",
             "price": 499.99, "compare_price": 699.99, "category": "Watches", "brand": "Chrono Elite",
             "rating": 4.8, "stock": 8, "color": "Gold", "image_url": "https://picsum.photos/seed/watch1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_featured": True, "is_active": True, "is_hot": True},
            {"name": "Silk Scarf", "description": "100% pure silk scarf with vibrant hand-painted pattern.",
             "price": 89.99, "compare_price": 129.99, "category": "Fashion", "brand": "Silk House",
             "rating": 4.2, "stock": 25, "color": "Red", "image_url": "https://picsum.photos/seed/scarf1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Wireless Noise-Cancelling Headphones",
             "description": "Premium over-ear headphones with 40-hour battery life and active noise cancellation.",
             "price": 349.99, "compare_price": 449.99, "category": "Electronics", "brand": "SoundMax",
             "rating": 4.7, "stock": 20, "color": "Midnight Black", "image_url": "https://picsum.photos/seed/headphones1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_featured": True, "is_active": True, "is_new": True},
            {"name": "Diamond Stud Earrings",
             "description": "0.5ct genuine diamond stud earrings in 18K white gold setting.",
             "price": 899.99, "compare_price": 1199.99, "category": "Accessories", "brand": "Diamond & Co",
             "rating": 4.9, "stock": 5, "color": "White Gold", "image_url": "https://picsum.photos/seed/earrings1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_hot": True},
            {"name": "Premium Moisturizing Serum",
             "description": "Hyaluronic acid and vitamin C serum for radiant, youthful skin.",
             "price": 79.99, "compare_price": 109.99, "category": "Beauty", "brand": "GlowLab",
             "rating": 4.4, "stock": 40, "color": None, "image_url": "https://picsum.photos/seed/serum1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True},
            {"name": "Ergonomic Office Chair",
             "description": "Height-adjustable mesh office chair with lumbar support and 5-year warranty.",
             "price": 599.99, "compare_price": 799.99, "category": "Home & Living", "brand": "ErgoSeat",
             "rating": 4.6, "stock": 10, "color": "Charcoal", "image_url": "https://picsum.photos/seed/chair1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Athletic Running Shoes",
             "description": "Lightweight, responsive foam midsole running shoes for marathon training.",
             "price": 149.99, "compare_price": 199.99, "category": "Footwear", "brand": "RunFast",
             "rating": 4.5, "stock": 30, "color": "Electric Blue", "image_url": "https://picsum.photos/seed/shoes1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_featured": True},
            {"name": "Leather Bifold Wallet",
             "description": "Full-grain Italian leather wallet with RFID blocking, 8 card slots.",
             "price": 59.99, "compare_price": 89.99, "category": "Accessories", "brand": "Leather & Co",
             "rating": 4.3, "stock": 50, "color": "Brown", "image_url": "https://picsum.photos/seed/wallet1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Smart Fitness Tracker",
             "description": "24/7 heart rate monitoring, sleep tracking, GPS, and 7-day battery life.",
             "price": 199.99, "compare_price": 249.99, "category": "Electronics", "brand": "FitPulse",
             "rating": 4.4, "stock": 22, "color": "Graphite", "image_url": "https://picsum.photos/seed/tracker1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True},
            {"name": "Cashmere Pullover Sweater",
             "description": "100% pure cashmere v-neck sweater, ultra-soft and warm.",
             "price": 189.99, "compare_price": 259.99, "category": "Fashion", "brand": "Cashmere & Co",
             "rating": 4.6, "stock": 18, "color": "Camel", "image_url": "https://picsum.photos/seed/sweater1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_featured": True},
            {"name": "Rose Gold Bangle Bracelet",
             "description": "18K rose gold plated bangle with cubic zirconia accent stones.",
             "price": 119.99, "compare_price": 169.99, "category": "Accessories", "brand": "Golden Touch",
             "rating": 4.5, "stock": 12, "color": "Rose Gold", "image_url": "https://picsum.photos/seed/bracelet1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Matte Liquid Lipstick Set",
             "description": "Long-lasting 12-hour formula, set of 6 classic shades, cruelty-free.",
             "price": 44.99, "compare_price": 69.99, "category": "Beauty", "brand": "ColorPop",
             "rating": 4.3, "stock": 60, "color": "Multi", "image_url": "https://picsum.photos/seed/lipstick1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True},
            {"name": "Stainless Steel Water Bottle",
             "description": "1L triple-insulated bottle, keeps drinks cold 36h / hot 18h.",
             "price": 34.99, "compare_price": 49.99, "category": "Sports", "brand": "HydroMax",
             "rating": 4.7, "stock": 80, "color": "Midnight Blue", "image_url": "https://picsum.photos/seed/bottle1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Scented Soy Candle Set",
             "description": "Set of 3 hand-poured soy wax candles with essential oil fragrances.",
             "price": 49.99, "compare_price": 74.99, "category": "Home & Living", "brand": "ZenScents",
             "rating": 4.5, "stock": 35, "color": "Ivory", "image_url": "https://picsum.photos/seed/candle1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Leather Belt",
             "description": "Full-grain cowhide leather belt with antique brass buckle, sizes 30-44.",
             "price": 69.99, "compare_price": 99.99, "category": "Fashion", "brand": "BeltCraft",
             "rating": 4.4, "stock": 28, "color": "Dark Brown", "image_url": "https://picsum.photos/seed/belt1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Yoga Mat Premium",
             "description": "6mm thick non-slip TPE yoga mat with body alignment lines, eco-friendly.",
             "price": 59.99, "compare_price": 89.99, "category": "Sports", "brand": "ZenFlow",
             "rating": 4.6, "stock": 45, "color": "Purple", "image_url": "https://picsum.photos/seed/yogamat1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Ceramic Coffee Mug Set",
             "description": "Set of 4 handcrafted ceramic mugs, 350ml each, dishwasher-safe.",
             "price": 39.99, "compare_price": 59.99, "category": "Home & Living", "brand": "CeramicKind",
             "rating": 4.4, "stock": 55, "color": "Earth Tones", "image_url": "https://picsum.photos/seed/mug1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True},
            {"name": "Snap-Back Baseball Cap",
             "description": "100% cotton twill 6-panel cap with adjustable snap closure.",
             "price": 29.99, "compare_price": 44.99, "category": "Fashion", "brand": "CapKing",
             "rating": 4.2, "stock": 70, "color": "Black / White", "image_url": "https://picsum.photos/seed/cap1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Portable Bluetooth Speaker",
             "description": "360° surround sound, waterproof IPX7, 12-hour battery, USB-C charging.",
             "price": 129.99, "compare_price": 179.99, "category": "Electronics", "brand": "SoundWave",
             "rating": 4.5, "stock": 18, "color": "Gunmetal", "image_url": "https://picsum.photos/seed/speaker1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_hot": True},
            {"name": "Perfume Eau de Parfum",
             "description": "Floral-oriental fragrance with top notes of rose and jasmine, 100ml.",
             "price": 159.99, "compare_price": 219.99, "category": "Beauty", "brand": "Essence Royale",
             "rating": 4.7, "stock": 20, "color": None, "image_url": "https://picsum.photos/seed/perfume1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_featured": True},
            {"name": "Slim Leather Backpack",
             "description": "15in laptop compartment, water-resistant coated canvas with leather trim.",
             "price": 179.99, "compare_price": 249.99, "category": "Fashion", "brand": "Urban Carry",
             "rating": 4.5, "stock": 14, "color": "Tan", "image_url": "https://picsum.photos/seed/backpack1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True},
            {"name": "Stainless Steel Sunglasses",
             "description": "UV400 polarised lenses with lightweight stainless steel frame.",
             "price": 99.99, "compare_price": 139.99, "category": "Accessories", "brand": "OptiView",
             "rating": 4.3, "stock": 22, "color": "Gunmetal / Grey", "image_url": "https://picsum.photos/seed/glasses1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True},
            {"name": "Resistance Band Set",
             "description": "Set of 5 loop bands (10–50 lbs) with mesh carry bag, latex-free.",
             "price": 24.99, "compare_price": 39.99, "category": "Sports", "brand": "FlexBand",
             "rating": 4.6, "stock": 100, "color": "Multi", "image_url": "https://picsum.photos/seed/bands1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_new": True},
            {"name": "Chef's Knife 8-inch",
             "description": "High-carbon German steel blade with full tang handle, razor-sharp edge.",
             "price": 89.99, "compare_price": 129.99, "category": "Home & Living", "brand": "BladeChef",
             "rating": 4.8, "stock": 25, "color": "Silver", "image_url": "https://picsum.photos/seed/knife1/600/600",
             "supplier_id": supplier_id, "is_approved": True, "is_active": True, "is_hot": True},
        ]
        for product_data in extended_products:
            _upsert_demo_product(db, product_data)

        demo_service_area = _ensure_demo_service_area(db, partner=logistics_partner, admin_id=admin_id)
        db.flush()
        _ensure_demo_pricing_profile(db, partner=logistics_partner, service_area=demo_service_area, admin_id=admin_id)
        _ensure_demo_vehicle_rule(db, partner=logistics_partner, service_area=demo_service_area, admin_id=admin_id,
                                  vehicle_type="car", max_weight_kg="10.00", cost_multiplier="1.0000", priority_rank=10)
        _ensure_demo_vehicle_rule(db, partner=logistics_partner, service_area=demo_service_area, admin_id=admin_id,
                                  vehicle_type="van", max_weight_kg="25.00", cost_multiplier="1.2000", priority_rank=20)
        db.flush()
        _ensure_demo_pickup_ready_shipment(db, admin_user=admin_user, customer_user=customer_user,
                                           supplier_user=supplier_user, logistics_partner=logistics_partner,
                                           service_area=demo_service_area)

        email_templates = [
            {"name": "Welcome Series - New Customer", "subject": "Welcome to ZOZI - Your Fashion Journey Begins!",
             "html_content": "<p>Welcome! Use code <strong>WELCOME10</strong> at checkout.</p>",
             "template_type": "promotional", "variables": '["{{first_name}}"]', "created_by": admin_id},
            {"name": "Flash Sale Announcement", "subject": "⚡ FLASH SALE: Up to 50% Off!",
             "html_content": "<h3>🚨 FLASH SALE ALERT! 🚨</h3><p>Up to <strong>50% off</strong> selected items.</p>",
             "template_type": "promotional", "variables": '["{{first_name}}"]', "created_by": admin_id},
            {"name": "New Arrivals Newsletter", "subject": "New Arrivals: Fresh Fashion Just Landed!",
             "html_content": "<p>Hello {{first_name}}, check out the latest arrivals!</p>",
             "template_type": "marketing", "variables": '["{{first_name}}"]', "created_by": admin_id},
            {"name": "Abandoned Cart Recovery", "subject": "Your Cart is Waiting!",
             "html_content": "<p>Hi {{first_name}}, your cart is saved and ready for you!</p>",
             "template_type": "transactional", "variables": '["{{first_name}}"]', "created_by": admin_id},
        ]
        for template_data in email_templates:
            _upsert_email_template(db, template_data)

        # ── Country-scoped seed data (AE & SA) ────────────────────────────────
        _seed_country_scoped_data(db, admin_id=admin_id)

        # Seed treasury system (chart of accounts + buckets)
        from infrastructure.database.treasury_seeder import seed_treasury_system
        seed_treasury_system(db)

        db.commit()
        logger.info("Sample data seeded successfully")
        _seed_employee_data(db)
    except Exception:
        db.rollback()
        logger.exception("Seed failed")
        raise
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════
#  Country-scoped seed data — AE & SA
# ══════════════════════════════════════════════════════════════════════════

def _seed_country_scoped_data(db: Session, admin_id: int) -> None:
    """Seed country-specific actors, products, banners, and flash sales for AE and SA.

    This data is used to verify:
    1. Country isolation (RLS) — data scoped by country_code
    2. Admin consolidated view — admin sees all countries
    3. Per-country actors: employees, suppliers, customers, logistics
    4. Per-country products, banners, flash sales, coupons
    """
    from datetime import timedelta
    from infrastructure.database.rls_interceptor import set_rls_context
    from infrastructure.utils.auth import get_password_hash

    logger.info("Seeding country-scoped data for AE and SA...")

    # Set RLS context to unrestricted for seeding
    set_rls_context(None, is_restricted=False)

    User = get_model("User")
    Employee = get_model("Employee")
    Office = get_model("Office")
    SupplierProfile = get_model("SupplierProfile")
    LogisticsPartner = get_model("LogisticsPartner")
    Category = get_model("Category")
    Product = get_model("Product")
    Banner = get_model("Banner")
    FlashSale = get_model("FlashSale")
    FlashSaleItem = get_model("FlashSaleItem")
    Coupon = get_model("Coupon")

    now = _utcnow()

    # ── Helper: get or create user ─────────────────────────────────────────
    def _get_or_create_user(email: str, username: str, pwd: str, role: str, country: str, full_name: str) -> object:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash(pwd),
                role=role,
                full_name=full_name,
                country_code=country,
            )
            db.add(user)
            db.flush()
            logger.info(f"Created {role} user: {email} ({country})")
        return user

    # ══════════════════════════════════════════════════════════════════════
    #  UAE (AE) COUNTRY DATA
    # ══════════════════════════════════════════════════════════════════════

    # ── AE Employees ─────────────────────────────────────────────────────
    ae_employees = [
        ("ae.manager@zozi.com", "ae_manager", "Ahmed Al-Mansouri", "Operations", "Country Manager"),
        ("ae.finance@zozi.com", "ae_finance", "Fatima Al-Rashid", "Finance", "Finance Lead"),
        ("ae.support@zozi.com", "ae_support", "Khalid Hassan", "Customer Support", "Support Lead"),
    ]
    for email, uname, name, dept, pos in ae_employees:
        u = _get_or_create_user(email, uname, "employee123", "employee", "AE", name)
        if not db.query(Employee).filter(Employee.user_id == u.id).first():
            office = db.query(Office).filter(Office.country_code == "AE").first()
            db.add(Employee(
                user_id=u.id, employee_code=f"AE-{uname[:3].upper()}-{u.id:04d}",
                office_id=office.id if office else None,
                department=dept, position=pos, employment_type="full_time",
                employment_status="active", salary=Decimal("8000"), currency="AED",
                country_code="AE", hire_date=now - timedelta(days=180),
            ))

    # ── AE Suppliers ─────────────────────────────────────────────────────
    ae_suppliers = [
        ("dubai.fashion@supplier.ae", "dubai_fashion", "Dubai Fashion House", "Premium Fashion"),
        ("abudhabi.tech@supplier.ae", "abudhabi_tech", "Abu Dhabi Tech Store", "Electronics"),
    ]
    for email, uname, name, biz in ae_suppliers:
        u = _get_or_create_user(email, uname, "supplier123", "supplier", "AE", name)
        if not db.query(SupplierProfile).filter(SupplierProfile.user_id == u.id).first():
            db.add(SupplierProfile(
                user_id=u.id, business_name=biz, business_type="retailer",
                country_code="AE", website="https://supplier-ae.zozi.local",
                address=json.dumps({"city": "Dubai", "country": "UAE", "country_code": "AE"}),
                verification_status="approved",
            ))

    # ── AE Customers ─────────────────────────────────────────────────────
    ae_customers = [
        ("sara@customer.ae", "sara_uae", "Sara Al-Maktoum"),
        ("omar@customer.ae", "omar_uae", "Omar Al-Rashid"),
        ("nora@customer.ae", "nora_uae", "Nora Al-Hassan"),
    ]
    for email, uname, name in ae_customers:
        _get_or_create_user(email, uname, "customer123", "customer", "AE", name)

    # ── AE Logistics ─────────────────────────────────────────────────────
    ae_logistics = [
        ("emirates.express@zozi.ae", "emirates_express", "Emirates Express Delivery"),
        ("desert.shipping@zozi.ae", "desert_shipping", "Desert Shipping Co."),
    ]
    for email, uname, name in ae_logistics:
        u = _get_or_create_user(email, uname, "logistics123", "logistics_partner", "AE", name)
        if not db.query(LogisticsPartner).filter(LogisticsPartner.user_id == u.id).first():
            db.add(LogisticsPartner(
                name=name, code=f"AE-LOG-{u.id:04d}", user_id=u.id,
                contact_name=f"{name} Team", contact_email=email,
                contact_phone="+971500002000",
                coverage_regions=json.dumps(["Dubai", "Abu Dhabi", "Sharjah"]),
                service_types=json.dumps(["ground", "same_day", "express"]),
                status_code="active", verification_status="approved",
                verified_by=admin_id, verified_at=now, country_code="AE",
            ))

    # ══════════════════════════════════════════════════════════════════════
    #  SAUDI ARABIA (SA) COUNTRY DATA
    # ══════════════════════════════════════════════════════════════════════

    # ── SA Employees ─────────────────────────────────────────────────────
    sa_employees = [
        ("sa.manager@zozi.com", "sa_manager", "Mohammed Al-Saud", "Operations", "Country Manager"),
        ("sa.finance@zozi.com", "sa_finance", "Layla Al-Zahrani", "Finance", "Finance Lead"),
        ("sa.support@zozi.com", "sa_support", "Abdullah Al-Qahtani", "Customer Support", "Support Lead"),
    ]
    for email, uname, name, dept, pos in sa_employees:
        u = _get_or_create_user(email, uname, "employee123", "employee", "SA", name)
        if not db.query(Employee).filter(Employee.user_id == u.id).first():
            office = db.query(Office).filter(Office.country_code == "SA").first()
            db.add(Employee(
                user_id=u.id, employee_code=f"SA-{uname[:3].upper()}-{u.id:04d}",
                office_id=office.id if office else None,
                department=dept, position=pos, employment_type="full_time",
                employment_status="active", salary=Decimal("9000"), currency="SAR",
                country_code="SA", hire_date=now - timedelta(days=150),
            ))

    # ── SA Suppliers ─────────────────────────────────────────────────────
    sa_suppliers = [
        ("riyadh.fashion@supplier.sa", "riyadh_fashion", "Riyadh Fashion Boutique", "Luxury Fashion"),
        ("jeddah.tech@supplier.sa", "jeddah_tech", "Jeddah Tech World", "Electronics"),
    ]
    for email, uname, name, biz in sa_suppliers:
        u = _get_or_create_user(email, uname, "supplier123", "supplier", "SA", name)
        if not db.query(SupplierProfile).filter(SupplierProfile.user_id == u.id).first():
            db.add(SupplierProfile(
                user_id=u.id, business_name=biz, business_type="retailer",
                country_code="SA", website="https://supplier-sa.zozi.local",
                address=json.dumps({"city": "Riyadh", "country": "Saudi Arabia", "country_code": "SA"}),
                verification_status="approved",
            ))

    # ── SA Customers ─────────────────────────────────────────────────────
    sa_customers = [
        ("fahd@customer.sa", "fahd_sa", "Fahd Al-Otaibi"),
        ("reem@customer.sa", "reem_sa", "Reem Al-Dosari"),
        ("nasser@customer.sa", "nasser_sa", "Nasser Al-Shehri"),
    ]
    for email, uname, name in sa_customers:
        _get_or_create_user(email, uname, "customer123", "customer", "SA", name)

    # ── SA Logistics ─────────────────────────────────────────────────────
    sa_logistics = [
        ("saudi.post.express@zozi.sa", "saudi_post", "Saudi Post Express"),
        ("red.sea@zozi.sa", "red_sea", "Red Sea Logistics"),
    ]
    for email, uname, name in sa_logistics:
        u = _get_or_create_user(email, uname, "logistics123", "logistics_partner", "SA", name)
        if not db.query(LogisticsPartner).filter(LogisticsPartner.user_id == u.id).first():
            db.add(LogisticsPartner(
                name=name, code=f"SA-LOG-{u.id:04d}", user_id=u.id,
                contact_name=f"{name} Team", contact_email=email,
                contact_phone="+966500002000",
                coverage_regions=json.dumps(["Riyadh", "Jeddah", "Dammam"]),
                service_types=json.dumps(["ground", "express", "cold_chain"]),
                status_code="active", verification_status="approved",
                verified_by=admin_id, verified_at=now, country_code="SA",
            ))

    db.flush()

    # ══════════════════════════════════════════════════════════════════════
    #  COUNTRY-SPECIFIC PRODUCTS
    # ══════════════════════════════════════════════════════════════════════

    categories = db.query(Category).limit(10).all()
    ae_supplier_ids = [u.id for u in db.query(User).filter(User.role == "supplier", User.country_code == "AE").all()]
    sa_supplier_ids = [u.id for u in db.query(User).filter(User.role == "supplier", User.country_code == "SA").all()]

    ae_products = [
        ("Luxury Date Box (AE)", "Premium Ajwa dates in luxury packaging", Decimal("199.99"), "General", 0, "https://picsum.photos/seed/ae_dates/600/600"),
        ("Arabic Coffee Set (AE)", "Traditional Arabic coffee pot and cups", Decimal("149.99"), "Home & Living", 0, "https://picsum.photos/seed/ae_coffee/600/600"),
        ("Perfume Oud Collection (AE)", "Premium Oud perfume - 100ml", Decimal("399.99"), "Beauty", 1, "https://picsum.photos/seed/ae_oud/600/600"),
        ("Gold Plated Watch (AE)", "Luxury gold-plated wristwatch", Decimal("599.99"), "Watches", 1, "https://picsum.photos/seed/ae_watch/600/600"),
    ]
    sa_products = [
        ("Saudi Rose Water (SA)", "Pure Taif rose water - 250ml", Decimal("89.99"), "Beauty", 0, "https://picsum.photos/seed/sa_rose/600/600"),
        ("Majlis Cushion Set (SA)", "Traditional Saudi majlis cushion set", Decimal("249.99"), "Home & Living", 0, "https://picsum.photos/seed/sa_majlis/600/600"),
        ("Smart Prayer Mat (SA)", "Tech-enabled prayer mat with Qibla finder", Decimal("179.99"), "Electronics", 1, "https://picsum.photos/seed/sa_mat/600/600"),
        ("Saudi Date Chocolate (SA)", "Premium chocolate-covered dates", Decimal("129.99"), "General", 1, "https://picsum.photos/seed/sa_dates/600/600"),
    ]

    for name, desc, price, cat_name, sup_idx, img in ae_products:
        if not db.query(Product).filter(Product.name == name).first():
            cat = next((c for c in categories if c.name == cat_name), categories[0] if categories else None)
            if cat:
                sid = ae_supplier_ids[sup_idx] if sup_idx < len(ae_supplier_ids) else None
                db.add(Product(name=name, description=desc, price=price, category_id=cat.id,
                                 supplier_id=sid, image_url=img, country_code="AE",
                                 is_approved=True, is_active=True, is_featured=True))

    for name, desc, price, cat_name, sup_idx, img in sa_products:
        if not db.query(Product).filter(Product.name == name).first():
            cat = next((c for c in categories if c.name == cat_name), categories[0] if categories else None)
            if cat:
                sid = sa_supplier_ids[sup_idx] if sup_idx < len(sa_supplier_ids) else None
                db.add(Product(name=name, description=desc, price=price, category_id=cat.id,
                                 supplier_id=sid, image_url=img, country_code="SA",
                                 is_approved=True, is_active=True, is_featured=True))

    db.flush()

    # ══════════════════════════════════════════════════════════════════════
    #  COUNTRY-SPECIFIC BANNERS
    # ══════════════════════════════════════════════════════════════════════

    banners = [
        ("Ramadan Special Offers (AE)", "Up to 50% off on premium products", "AE", "hero",
         "https://picsum.photos/seed/ae_ramadan/1200/400", "/promotions/ramadan"),
        ("Free Delivery Dubai (AE)", "Same-day delivery on orders over AED 200", "AE", "promotional",
         "https://picsum.photos/seed/ae_delivery/1200/400", "/delivery"),
        ("Saudi National Day Sale (SA)", "Celebrate with up to 60% off", "SA", "hero",
         "https://picsum.photos/seed/sa_national/1200/400", "/promotions/national-day"),
        ("Riyadh Express Delivery (SA)", "Get your order in 2 hours", "SA", "promotional",
         "https://picsum.photos/seed/sa_express/1200/400", "/delivery"),
    ]
    for title, subtitle, country, btype, img, link in banners:
        if not db.query(Banner).filter(Banner.title == title).first():
            db.add(Banner(title=title, subtitle=subtitle, image_url=img, link=link,
                           banner_type=btype, country_code=country, is_active=True,
                           sort_order=10, created_by_id=admin_id,
                           starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=30)))

    db.flush()

    # ══════════════════════════════════════════════════════════════════════
    #  COUNTRY-SPECIFIC FLASH SALES
    # ══════════════════════════════════════════════════════════════════════

    ae_flash_prods = db.query(Product).filter(Product.country_code == "AE").limit(3).all()
    sa_flash_prods = db.query(Product).filter(Product.country_code == "SA").limit(3).all()

    # AE Flash Sale
    if not db.query(FlashSale).filter(FlashSale.title == "AE Flash Weekend").first():
        ae_fs = FlashSale(title="AE Flash Weekend", description="Weekend flash sale - up to 40% off",
                          starts_at=now - timedelta(hours=1), ends_at=now + timedelta(days=3),
                          discount_pct=Decimal("40"), is_active=True, country_code="AE")
        db.add(ae_fs)
        db.flush()
        for p in ae_flash_prods:
            if p.price:
                disc = (Decimal(str(p.price)) * Decimal("0.60")).quantize(Decimal("0.01"))
                db.add(FlashSaleItem(flash_sale_id=ae_fs.id, product_id=p.id,
                                     original_price=Decimal(str(p.price)), discounted_price=disc, country_code="AE"))

    # SA Flash Sale
    if not db.query(FlashSale).filter(FlashSale.title == "SA Mega Sale").first():
        sa_fs = FlashSale(title="SA Mega Sale", description="Mega sale event - up to 50% off",
                          starts_at=now - timedelta(hours=1), ends_at=now + timedelta(days=5),
                          discount_pct=Decimal("50"), is_active=True, country_code="SA")
        db.add(sa_fs)
        db.flush()
        for p in sa_flash_prods:
            if p.price:
                disc = (Decimal(str(p.price)) * Decimal("0.50")).quantize(Decimal("0.01"))
                db.add(FlashSaleItem(flash_sale_id=sa_fs.id, product_id=p.id,
                                     original_price=Decimal(str(p.price)), discounted_price=disc, country_code="SA"))

    db.flush()

    # ══════════════════════════════════════════════════════════════════════
    #  COUNTRY-SPECIFIC COUPONS
    # ══════════════════════════════════════════════════════════════════════

    coupons = [
        ("WELCOME_AE", "percentage", Decimal("15"), Decimal("100"), "AE", 100),
        ("FREESHIP_AE", "fixed", Decimal("25"), Decimal("200"), "AE", 50),
        ("WELCOME_SA", "percentage", Decimal("20"), Decimal("150"), "SA", 100),
        ("FREESHIP_SA", "fixed", Decimal("30"), Decimal("250"), "SA", 50),
    ]
    for code, dtype, dval, min_ord, country, usage in coupons:
        if not db.query(Coupon).filter(Coupon.code == code).first():
            db.add(Coupon(code=code, discount_type=dtype, discount_value=dval,
                           minimum_order=min_ord, usage_limit=usage,
                           starts_at=now - timedelta(days=1), expires_at=now + timedelta(days=60),
                           is_active=True, country_code=country))

    db.commit()
    logger.info("Country-scoped data seeded successfully")
