"""Regression tests for the implemented recovery write services.

Guards the remediation that replaced ``_missing_symbol`` stubs across the
logistics / employee / HR / IAM / banner / disputes / misc / permissions /
promotion / returns / supplier-badge write services and the router permission
primitives with real DB-write logic.
"""
from __future__ import annotations

import datetime
import json
import uuid
from decimal import Decimal

import pytest

from data.models import (
    Banner,
    CountryConfig,
    DynamicQRSession,
    Employee,
    EmployeeAttendance,
    EmployeeBiometric,
    EmployeeDocument,
    EmployeeRelation,
    EmployeeRiskScore,
    EmployeeWorkLog,
    GeoFenceLog,
    Notification,
    Order,
    PhysicalIDCard,
    PromotionEngineConfig,
    ReturnRequest,
    RevokedToken,
    RolePermissionSetting,
    Shipment,
    ShipmentEvent,
    ShippingCarrier,
    ShippingZone,
    SupplierBadge,
    SupplierBadgeBillingHistory,
    SupplierBadgeCatalog,
    SupplierDispute,
    SupplierNotificationPreference,
    SupplierProfile,
    User,
)

import services.logistics.logistics_write_service as logistics
import services.hr.employee_write_service as emp
import services.hr.hr_write_service as hr
import services.security.iam_write_service as iam
import services.commerce.banner_write_service as banner
import services.orders.disputes_write_service as disputes
import services.common.misc_write_service as misc
import services.security.permissions_write_service as perms
import services.commerce.promotion_engine_service as promo
import services.orders.returns_write_service as ret
import services.supplier.supplier_badge_service as badge
import routers.public_permission_primitives_access as prim


def _country(db, code="OM"):
    cc = db.query(CountryConfig).filter(CountryConfig.code == code).first()
    if cc is None:
        cc = CountryConfig(code=code, name=code, country_code=code, is_active=True)
        db.add(cc)
        db.commit()
        db.refresh(cc)
    return cc


def _user(db, role="customer", code="OM"):
    u = User(
        email=f"u{uuid.uuid4().hex[:12]}@ex.com",
        username=f"u{uuid.uuid4().hex[:12]}",
        hashed_password="x",
        role=role,
        country_code=code,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _employee(db, user=None, code="OM"):
    _country(db, code)
    if user is None:
        user = _user(db, role="employee", code=code)
    e = Employee(
        user_id=user.id,
        employee_code=f"E{uuid.uuid4().hex[:10]}",
        hire_date=datetime.date(2024, 1, 1),
        country_code=code,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


def _supplier(db, code="OM"):
    _country(db, code)
    u = _user(db, role="supplier", code=code)
    sp = SupplierProfile(user_id=u.id, business_name="Test Supplier", country_code=code)
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp


def _order(db, user, code="OM"):
    o = Order(
        user_id=user.id,
        order_number=f"ORD-{uuid.uuid4().hex[:12]}",
        subtotal_amount=Decimal("0"),
        total_amount=Decimal("0"),
        country_code=code,
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


# ── logistics ────────────────────────────────────────────────────────────────
def test_create_shipping_carrier_absorbs_extra_kwargs(db_session):
    u = _user(db_session)
    carrier = logistics.create_shipping_carrier(
        db_session,
        name="Aramex",
        code="aramex_om",
        supplier_id=u.id,
        tracking_url="https://x",  # extra, not a model column
        notes="n",                 # extra
        country_code="OM",
    )
    assert carrier.id is not None
    assert carrier.code == "aramex_om"
    reloaded = db_session.get(ShippingCarrier, carrier.id)
    assert reloaded is not None


def test_create_and_update_shipping_zone_json(db_session):
    _country(db_session, "OM")
    u = _user(db_session)
    zone = logistics.create_shipping_zone(
        db_session, name="GCC", countries=["OM", "AE"], supplier_id=u.id
    )
    zc = zone.countries
    if not isinstance(zc, list):
        zc = json.loads(zc)
    assert zc == ["OM", "AE"]
    logistics.update_shipping_zone(db_session, zone, {"name": "GCC2"})
    assert db_session.get(ShippingZone, zone.id).name == "GCC2"


def test_update_shipment_event_accepts_object(db_session):
    _country(db_session, "OM")
    u = _user(db_session)
    o = _order(db_session, u)
    ship = Shipment(order_id=o.id, supplier_id=u.id, country_code="OM")
    db_session.add(ship)
    db_session.commit()
    db_session.refresh(ship)
    ev = ShipmentEvent(shipment_id=ship.id, order_id=o.id, supplier_id=u.id, actor_user_id=u.id, event_type="pickup", country_code="OM")
    db_session.add(ev)
    db_session.commit()
    logistics.update_shipment_event(db_session, ev, {"latitude": 1.0, "longitude": 2.0})
    assert ev.latitude == 1.0


# ── employee ──────────────────────────────────────────────────────────────────
def test_employee_attendance_and_work_log(db_session):
    e = _employee(db_session)
    a = emp.create_employee_attendance(db_session, employee_id=e.id, date=datetime.date(2024, 5, 1))
    assert a.id is not None
    emp.update_employee_attendance(db_session, a, {"status": "present"})
    assert db_session.get(EmployeeAttendance, a.id).status == "present"

    w = emp.create_employee_work_log(db_session, employee_id=e.id, hours_worked=8, date=datetime.date(2024, 5, 1))
    assert w.id is not None


def test_dynamic_qr_session_and_expiry(db_session):
    _country(db_session, "OM")
    e = _employee(db_session)
    s = emp.create_dynamic_qr_session(db_session, employee_id=e.id, qr_token="tok", expires_at=datetime.datetime(2030, 1, 1))
    future = datetime.datetime(2035, 1, 1)
    emp.update_dynamic_qr_session(db_session, s, {"used_at": future})
    assert db_session.get(DynamicQRSession, s.id).used_at is not None

    res = emp.update_qr_sessions_expiry(db_session, [s], as_of=future)
    assert res["expired"] == 0  # already marked used -> not re-expired
    assert db_session.get(DynamicQRSession, s.id).expires_at == datetime.datetime(2030, 1, 1)


def test_employee_document_update_and_relation_delete(db_session):
    _country(db_session, "OM")
    e = _employee(db_session)
    doc = EmployeeDocument(employee_id=e.id, doc_type="passport", file_url="http://x", country_code="OM")
    db_session.add(doc)
    db_session.commit()
    emp.update_employee_document(db_session, doc, {"verified_at": datetime.datetime(2024, 1, 1)})
    assert db_session.get(EmployeeDocument, doc.id).verified_at is not None

    rel = EmployeeRelation(employee_id=e.id, related_person_name="Jane", relation_type="spouse", country_code="OM")
    db_session.add(rel)
    db_session.commit()
    emp.delete_employee_relation(db_session, rel, acting_user={"id": e.id}, reason="test")
    assert db_session.get(EmployeeRelation, rel.id).is_deleted is True


def test_create_revoked_token(db_session):
    u = _user(db_session)
    rt = emp.create_revoked_token(db_session, jti="jti-1", user_id=u.id, expires_at=datetime.datetime(2030, 1, 1))
    assert db_session.get(RevokedToken, rt.id) is not None


# ── hr ────────────────────────────────────────────────────────────────────────
def test_upsert_employee_risk_score(db_session):
    _country(db_session, "OM")
    e = _employee(db_session)
    r = hr.upsert_employee_risk_score(db_session, employee_id=e.id, score=85.0, factors={"metric": "metric"})
    assert r.risk_level == "low"
    # second call upserts the same (employee_id, assessment_date) row
    r2 = hr.upsert_employee_risk_score(db_session, employee_id=e.id, score=30.0, factors={"metric": "metric"})
    assert db_session.query(EmployeeRiskScore).filter(EmployeeRiskScore.employee_id == e.id).count() == 1
    assert r2.score == 30.0
    assert r2.risk_level == "high"


def test_create_employee_address_dependent(db_session):
    _country(db_session, "OM")
    e = _employee(db_session)
    a = hr.create_employee_address(db_session, employee_id=e.id, address_type="home", street="S", city="C", country_code="OM")
    assert a.id is not None
    d = hr.create_employee_dependent(db_session, employee_id=e.id, name="Kid", relation="child")
    assert d.id is not None


# ── iam ───────────────────────────────────────────────────────────────────────
def test_iam_biometric_geo_fence_card(db_session):
    _country(db_session, "OM")
    e = _employee(db_session)
    b = iam.create_employee_biometric(db_session, employee_id=e.id, biometric_type="fingerprint", fingerprint_hash="h")
    assert b.id is not None
    iam.update_employee_biometric(db_session, b, {"is_active": False})
    assert db_session.get(EmployeeBiometric, b.id).is_active is False

    g = iam.create_geo_fence_log(db_session, employee_id=e.id, latitude=1.0, longitude=2.0, is_within_fence=True)
    assert g.id is not None

    c = iam.create_physical_id_card(db_session, employee_id=e.id, card_number="C1")
    assert c.id is not None
    iam.update_physical_id_card(db_session, c, {"is_revoked": True})
    assert db_session.get(PhysicalIDCard, c.id).is_revoked is True


# ── banner ──────────────────────────────────────────────────────────────────
def test_banner_helpers(db_session):
    b = banner.add_banner_if_missing(db_session, {"title": "Hero", "country_code": "OM", "image_url": "http://x"})
    assert b.id is not None
    # not duplicated
    b2 = banner.add_banner_if_missing(db_session, {"title": "Hero", "country_code": "OM"})
    assert b2.id == b.id
    banner.bulk_add_banners(db_session, [{"title": "Sale", "country_code": "OM"}])
    banner.update_banner_image(db_session, b, "http://y")
    assert db_session.get(Banner, b.id).image_url == "http://y"


# ── disputes ──────────────────────────────────────────────────────────────────
def test_dispute_notification_and_updates(db_session):
    _country(db_session, "OM")
    sp = _supplier(db_session)
    n = disputes.create_dispute_notification(
        db_session, user_id=sp.user_id, type="dispute", title="t", message="m", link="/x", is_read=False, country_code="OM"
    )
    assert isinstance(n, Notification)
    assert n.user_id == sp.user_id

    prefs = disputes.create_supplier_notification_preference(db_session, supplier_id=sp.id, country_code="OM", in_app_enabled=True)
    assert prefs.id is not None
    disputes.update_supplier_notification_preference(db_session, prefs, {"email_enabled": False})
    assert db_session.get(SupplierNotificationPreference, prefs.id).email_enabled is False

    d = SupplierDispute(supplier_id=sp.id, title="d", description="x", status="open", country_code="OM")
    db_session.add(d)
    db_session.commit()
    disputes.update_supplier_dispute(db_session, d, {"status": "resolved"})
    assert db_session.get(SupplierDispute, d.id).status == "resolved"

    disputes.bulk_update_disputes(db_session, [d], {"priority": "high"})
    assert db_session.get(SupplierDispute, d.id).priority == "high"


# ── misc ──────────────────────────────────────────────────────────────────────
def test_reset_demo_data(db_session):
    _country(db_session, "OM")
    result = misc.reset_demo_data(db_session)
    assert "deleted" in result and "reseeded" in result
    assert result["reseeded"] == 3


# ── permissions ────────────────────────────────────────────────────────────
def test_upsert_role_permission_setting(db_session):
    r = perms.upsert_role_permission_setting(
        db_session, role="supplier", permissions_json=["view_catalog"], country_code="OM", updated_by_id=1
    )
    assert r.id is not None
    r2 = perms.upsert_role_permission_setting(
        db_session, role="supplier", permissions_json=["view_catalog", "manage_products"], country_code="OM", updated_by_id=1
    )
    assert r2.id == r.id
    assert "manage_products" in r2.permissions_json


# ── promotion ──────────────────────────────────────────────────────────────
def test_promotion_config(db_session):
    _country(db_session, "OM")
    promo.ensure_promotion_tables(db_session)
    cfg = promo.get_or_create_config(db_session)
    assert isinstance(cfg, PromotionEngineConfig)
    assert cfg.id is not None


# ── returns ──────────────────────────────────────────────────────────────────
def test_create_return_notification(db_session):
    _country(db_session, "OM")
    u = _user(db_session)
    o = _order(db_session, u)
    rr = ReturnRequest(order_id=o.id, customer_id=u.id, reason="broken", status="requested", country_code="OM")
    db_session.add(rr)
    db_session.commit()
    n = ret.create_return_notification(
        db_session, return_request=rr, user_id=u.id, type="order_update", title="Return", message="msg", link="/o"
    )
    assert isinstance(n, Notification)
    assert n.country_code == "OM"


# ── supplier badge ──────────────────────────────────────────────────────────
def test_supplier_badge_flow(db_session):
    sp = _supplier(db_session)
    cat = badge.list_supplier_badge_catalog(db_session)
    catalog = SupplierBadgeCatalog(name="Gold", badge_level="gold", price=Decimal("30"), credibility_weight=20.0, country_code="OM")
    db_session.add(catalog)
    db_session.commit()
    db_session.refresh(catalog)

    b = badge.purchase_supplier_badge(db_session, supplier_id=sp.user_id, catalog_id=catalog.id, country_code="OM")
    assert isinstance(b, SupplierBadge)
    hist = badge.list_supplier_badge_billing_history(db_session, supplier_id=sp.user_id)
    assert len(hist) == 1 and hist[0].amount == Decimal("30")

    score = badge.compute_credibility_score(db_session, supplier_id=sp.user_id)
    assert score == 20.0
    badge.admin_set_supplier_badge(db_session, supplier_id=sp.user_id, badge_name="Silver", country_code="OM")
    cycle = badge.run_badge_recalculation_cycle(db_session, country_code="OM")
    assert cycle["updated"] >= 1


# ── permission primitives ──────────────────────────────────────────────────
def test_permission_primitives(db_session):
    _country(db_session, "OM")
    assert isinstance(prim.COUNTRY_ROLE_PERMISSION_MAP, dict) and prim.COUNTRY_ROLE_PERMISSION_MAP
    assert isinstance(prim.HR_PERMISSION_MAP, dict) and prim.HR_PERMISSION_MAP
    assert isinstance(prim.MAKER_CHECKER_PERMISSIONS, (set, list)) and prim.MAKER_CHECKER_PERMISSIONS

    admin = _user(db_session, role="admin")
    perms.upsert_role_permission_setting(
        db_session, role="admin", permissions_json=["admin_access", "manage_users"], country_code="OM", updated_by_id=admin.id
    )
    eff = prim.get_effective_permissions(admin.id, "OM", db_session)
    assert "admin_access" in eff

    out = prim.request_permission_change(admin.id, admin.id, "manage_products", "grant", "OM", db_session)
    assert out["status"] in ("applied", "pending_maker_checker")
    prim.invalidate_permission_cache(admin.id, "OM")
