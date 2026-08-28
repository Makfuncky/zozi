"""Logistics domain — feature + service smoke tests.

Laws 4 (features), 2 (thin routers delegate to services), 131 (mock providers).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure tests._support is importable (pytest import machinery fix).
_TESTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))


class TestLogisticsFeatureAtoms:
    """Law 4 — every logistics feature atom is in the rbac catalog."""

    @pytest.mark.parametrize(
        "feature",
        [
            "logistics.shipping.tracking",
            "logistics.delivery.estimates",
            "logistics.shipping.manage",
            "logistics.fulfillment.manage",
            "logistics.partners.manage",
            "logistics.sla.manage",
            "logistics.profile.read",
            "logistics.profile.write",
        ],
    )
    def test_feature_in_catalog(self, feature):
        from tests._support.laws import assert_feature_in_catalog

        assert_feature_in_catalog(feature)


class TestLogisticsServiceImports:
    """Law 2 — service layer is importable (thin routers delegate here)."""

    def test_import_logistics_service(self):
        from domains.logistics.services import logistics as logistics_mod

        assert logistics_mod is not None

    def test_import_tracking_service(self):
        from domains.logistics.services.tracking import service as tracking_service

        assert tracking_service is not None

    def test_import_shipment_service(self):
        from domains.logistics.services.core.shipment_service import ShipmentService

        assert ShipmentService is not None

    def test_import_logistics_engine(self):
        from domains.logistics.services.core.logistics_engine import LogisticsEngine

        assert LogisticsEngine is not None

    def test_import_carrier_service(self):
        from domains.logistics.services.core.carrier_service import CarrierService

        assert CarrierService is not None


class TestLogisticsModelPersistence:
    """Laws 6/23 — models persist with audit columns populated."""

    def test_shipment_persists(self, db_session):
        from domains.logistics.models.logistics import Shipment

        shipment = Shipment(order_id=1, supplier_id=1)
        db_session.add(shipment)
        db_session.flush()

        assert shipment.id is not None
        assert shipment.created_at is not None
        assert shipment.updated_at is not None
        assert shipment.is_deleted is False

    def test_logistics_partner_persists(self, db_session):
        from domains.logistics.models.logistics import LogisticsPartner

        partner = LogisticsPartner(name="Test Partner", code="TEST-PARTNER-001")
        db_session.add(partner)
        db_session.flush()

        assert partner.id is not None
        assert partner.created_at is not None
        assert partner.is_deleted is False


class TestLogisticsShippingProvider:
    """Law 131 — shipping provider functions are callable without real SDKs."""

    def test_get_available_carriers(self):
        from providers.shipping.shipping_calculator import get_available_carriers

        carriers = get_available_carriers("AE")
        assert isinstance(carriers, list)
        assert len(carriers) > 0
        assert all("id" in c and "name" in c for c in carriers)

    def test_estimate_delivery_days(self):
        from providers.shipping.shipping_calculator import estimate_delivery_days

        result = estimate_delivery_days(
            origin={"country": "AE", "city": "Dubai"},
            destination={"country": "SA", "city": "Riyadh"},
            carrier="aramex",
        )
        assert "min_days" in result
        assert "max_days" in result

    def test_compare_shipping_options(self):
        from providers.shipping.shipping_calculator import compare_shipping_options

        results = compare_shipping_options(
            origin={"country": "AE", "city": "Dubai"},
            destination={"country": "SA", "city": "Riyadh"},
            package={"weight_kg": 2.0, "length_cm": 30, "width_cm": 20, "height_cm": 10},
        )
        assert isinstance(results, list)
        assert len(results) > 0
