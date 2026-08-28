"""Domain tests for logistics — shipments, tracking, and partner operations."""
from __future__ import annotations

import pytest


class TestLogisticsServiceImports:
    """Smoke tests: verify logistics service modules are importable."""

    def test_import_logistics_service(self):
        from domains.logistics.services import logistics as logistics_mod

        assert logistics_mod is not None

    def test_import_tracking_service(self):
        from domains.logistics.services.tracking import service as tracking_service

        assert tracking_service is not None

    def test_import_shipment_service(self):
        from domains.logistics.services.core.shipment_service import ShipmentService

        assert ShipmentService is not None

    def test_import_logistics_models(self):
        from domains.logistics.models.logistics import Shipment, LogisticsPartner

        assert Shipment is not None
        assert LogisticsPartner is not None

    def test_import_logistics_events(self):
        from domains.logistics.events import ShipmentCreatedEvent

        assert ShipmentCreatedEvent is not None

    def test_import_logistics_ports(self):
        from domains.logistics.ports import get_logistics_partner_by_id

        assert callable(get_logistics_partner_by_id)

    def test_import_logistics_features(self):
        from domains.logistics.features import LOGISTICS_FEATURES

        assert isinstance(LOGISTICS_FEATURES, (list, tuple, set))


class TestShipmentTracking:
    """Tests for shipment tracking operations."""

    def test_live_tracking_service_class(self):
        from domains.logistics.services.tracking.service import LiveTrackingService

        assert LiveTrackingService is not None
        assert hasattr(LiveTrackingService, "get_parcel_track")

    def test_shipment_model_fields(self, db_session):
        from domains.logistics.models.logistics import Shipment

        shipment = Shipment(
            tracking_number="TRACK-001",
            status="pending",
        )
        db_session.add(shipment)
        db_session.flush()

        assert shipment.id is not None
        assert shipment.tracking_number == "TRACK-001"
        assert shipment.status == "pending"

    def test_tracking_service_has_reconcile(self):
        from domains.orders.services.tracking.service import reconcile_order_status

        assert callable(reconcile_order_status)


class TestPartnerOperations:
    """Tests for logistics partner operations."""

    def test_partner_service_has_create_partner(self):
        from domains.logistics.services.partners.partner_service import _next_partner_code

        assert callable(_next_partner_code)

    def test_logistics_partner_model_fields(self, db_session):
        from domains.logistics.models.logistics import LogisticsPartner

        partner = LogisticsPartner(
            name="Test Partner",
            code="TEST-PARTNER",
            is_active=True,
        )
        db_session.add(partner)
        db_session.flush()

        assert partner.id is not None
        assert partner.name == "Test Partner"
        assert partner.code == "TEST-PARTNER"

    def test_logistics_engine_exists(self):
        from domains.logistics.services.core.logistics_engine import LogisticsEngine

        assert LogisticsEngine is not None

    def test_carrier_service_exists(self):
        from domains.logistics.services.core.carrier_service import CarrierService

        assert CarrierService is not None
