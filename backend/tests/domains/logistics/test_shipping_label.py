"""Tests for the shipping label service (Law 42 — Pydantic schema validation)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from domains.logistics.schemas.shipping_label_schemas import (
    ShipmentLabelData,
    ShipmentLabelDestination,
    validate_destination,
    validate_shipment_data,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_SHIPMENT = {
    "origin_country": "AE",
    "origin_city": "Dubai",
    "weight_kg": 1.0,
    "tracking_number": "TEST-001",
    "length_cm": 30.0,
    "width_cm": 20.0,
    "height_cm": 10.0,
}

_VALID_DESTINATION = {
    "country": "SA",
    "city": "Riyadh",
}


# ---------------------------------------------------------------------------
# Schema-level validation tests
# ---------------------------------------------------------------------------


class TestShipmentLabelDataSchema:
    """Pydantic schema validation for the shipment_data parameter."""

    def test_valid_shipment_data(self):
        """All required fields present and types correct — model constructs."""
        model = ShipmentLabelData(**_VALID_SHIPMENT)
        assert model.origin_country == "AE"
        assert model.weight_kg == 1.0
        assert model.tracking_number == "TEST-001"

    def test_default_dimensions_applied(self):
        """length_cm, width_cm, height_cm default to 30/20/10 when omitted."""
        minimal = {
            "origin_country": "AE",
            "origin_city": "Dubai",
            "weight_kg": 1.0,
            "tracking_number": "TEST-001",
        }
        model = ShipmentLabelData(**minimal)
        assert model.length_cm == 30.0
        assert model.width_cm == 20.0
        assert model.height_cm == 10.0

    def test_negative_weight_rejected(self):
        """weight_kg must be greater than zero."""
        with pytest.raises(ValidationError):
            ShipmentLabelData(
                origin_country="AE",
                origin_city="Dubai",
                weight_kg=-1.0,
                tracking_number="T1",
            )

    def test_missing_required_field_raises(self):
        """tracking_number is required; omitting it raises ValidationError."""
        with pytest.raises(ValidationError):
            ShipmentLabelData(
                origin_country="AE",
                origin_city="Dubai",
                weight_kg=1.0,
            )

    def test_positive_dimension_validator(self):
        """Negative dimensions are rejected by the model_validator."""
        with pytest.raises(ValidationError):
            ShipmentLabelData(
                origin_country="AE",
                origin_city="Dubai",
                weight_kg=1.0,
                tracking_number="T1",
                length_cm=-5.0,
            )


class TestShipmentLabelDestinationSchema:
    """Pydantic schema validation for the destination parameter."""

    def test_valid_destination(self):
        model = ShipmentLabelDestination(**_VALID_DESTINATION)
        assert model.country == "SA"
        assert model.city == "Riyadh"

    def test_country_must_be_two_chars(self):
        """country must be exactly 2 characters (ISO 3166-1 alpha-2, Law 20)."""
        with pytest.raises(ValidationError):
            ShipmentLabelDestination(country="SAU", city="Riyadh")

    def test_empty_country_rejected(self):
        with pytest.raises(ValidationError):
            ShipmentLabelDestination(country="", city="Riyadh")

    def test_empty_city_rejected(self):
        with pytest.raises(ValidationError):
            ShipmentLabelDestination(country="SA", city="")


# ---------------------------------------------------------------------------
# Validator function tests
# ---------------------------------------------------------------------------


class TestValidateShipmentData:
    def test_valid_dict_returns_normalized_dict(self):
        result = validate_shipment_data(_VALID_SHIPMENT)
        assert isinstance(result, dict)
        assert result["weight_kg"] == 1.0
        assert result["length_cm"] == 30.0

    def test_invalid_dict_raises_validation_error(self):
        with pytest.raises(ValidationError):
            validate_shipment_data({"weight_kg": -1.0})


class TestValidateDestination:
    def test_valid_dict_returns_normalized_dict(self):
        result = validate_destination(_VALID_DESTINATION)
        assert isinstance(result, dict)
        assert result["country"] == "SA"

    def test_invalid_country_length_raises(self):
        with pytest.raises(ValidationError):
            validate_destination({"country": "SAU", "city": "Riyadh"})


# ---------------------------------------------------------------------------
# Integration: create_shipment_label with Pydantic models (Law 42)
# ---------------------------------------------------------------------------


class TestCreateShipmentLabelValidation:
    """Law 42 — create_shipment_label accepts Pydantic schema parameters."""

    def test_accepts_pydantic_models(self):
        """Function accepts ShipmentLabelData and ShipmentLabelDestination models."""
        from domains.logistics.services.shipping_label import create_shipment_label

        shipment = ShipmentLabelData(**_VALID_SHIPMENT)
        dest = ShipmentLabelDestination(**_VALID_DESTINATION)
        result = create_shipment_label(shipment, dest)
        assert "rate" in result
        assert "qr_code" in result
        assert "barcode" in result

    def test_accepts_raw_dicts_backward_compat(self):
        """Raw dicts still accepted — no breaking change for existing callers."""
        from domains.logistics.services.shipping_label import create_shipment_label

        result = create_shipment_label(_VALID_SHIPMENT, _VALID_DESTINATION)
        assert "rate" in result
        assert "qr_code" in result
        assert "barcode" in result

    def test_invalid_weight_raises_validation_error(self):
        """Negative weight_kg raises ValidationError, not a provider call."""
        from domains.logistics.services.shipping_label import create_shipment_label

        bad = dict(_VALID_SHIPMENT, weight_kg=-5.0)
        with pytest.raises(ValidationError):
            create_shipment_label(bad, _VALID_DESTINATION)

    def test_missing_tracking_number_raises_validation_error(self):
        """Missing tracking_number raises ValidationError before provider call."""
        from domains.logistics.services.shipping_label import create_shipment_label

        bad = dict(_VALID_SHIPMENT, tracking_number="")
        with pytest.raises(ValidationError):
            create_shipment_label(bad, _VALID_DESTINATION)


class TestCreateShipmentLabelExceptionLogging:
    """AP-004 — bare except blocks must log via logger.exception before returning."""

    def test_shipping_rate_provider_exception_is_logged(self, caplog):
        """calculate_shipping_rate failure logs via logger.exception and returns error dict."""
        import logging

        from domains.logistics.services.shipping_label import create_shipment_label

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "domains.logistics.services.shipping_label.calculate_shipping_rate",
                lambda origin, destination, package: (_ for _ in ()).throw(RuntimeError("rate down")),
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_tracking_qr",
                lambda tracking_number: "ok-qr",
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_code128",
                lambda tracking_number: "ok-barcode",
            )
            with caplog.at_level(logging.ERROR):
                result = create_shipment_label(_VALID_SHIPMENT, _VALID_DESTINATION)

        assert "error" in result["rate"]
        assert result["qr_code"] == "ok-qr"
        assert result["barcode"] == "ok-barcode"
        assert "calculate_shipping_rate failed" in caplog.text

    def test_qr_provider_exception_is_logged(self, caplog):
        """generate_tracking_qr failure logs and returns None for qr_code."""
        import logging

        from domains.logistics.services.shipping_label import create_shipment_label

        call_count = 0

        def fake_rate(origin, destination, package):
            return {"carrier": "test", "cost": 5.0}

        def fake_qr(tracking_number):
            raise RuntimeError("qr service down")

        def fake_barcode(tracking_number):
            return "ok-barcode"

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "domains.logistics.services.shipping_label.calculate_shipping_rate",
                fake_rate,
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_tracking_qr",
                fake_qr,
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_code128",
                fake_barcode,
            )
            with caplog.at_level(logging.ERROR):
                result = create_shipment_label(_VALID_SHIPMENT, _VALID_DESTINATION)

        assert result["qr_code"] is None
        assert result["barcode"] == "ok-barcode"
        assert "generate_tracking_qr failed" in caplog.text

    def test_barcode_provider_exception_is_logged(self, caplog):
        """generate_code128 failure logs and returns None for barcode."""
        import logging

        from domains.logistics.services.shipping_label import create_shipment_label

        def fake_rate(origin, destination, package):
            return {"carrier": "test", "cost": 5.0}

        def fake_qr(tracking_number):
            return "ok-qr"

        def fake_barcode(tracking_number):
            raise RuntimeError("barcode service down")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "domains.logistics.services.shipping_label.calculate_shipping_rate",
                fake_rate,
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_tracking_qr",
                fake_qr,
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_code128",
                fake_barcode,
            )
            with caplog.at_level(logging.ERROR):
                result = create_shipment_label(_VALID_SHIPMENT, _VALID_DESTINATION)

        assert result["qr_code"] == "ok-qr"
        assert result["barcode"] is None
        assert "generate_code128 failed" in caplog.text

    def test_all_providers_exception_logs_all_errors(self, caplog):
        """All three providers failing logs three separate error messages."""
        import logging

        from domains.logistics.services.shipping_label import create_shipment_label

        def fake_rate(origin, destination, package):
            raise RuntimeError("rate down")

        def fake_qr(tracking_number):
            raise RuntimeError("qr down")

        def fake_barcode(tracking_number):
            raise RuntimeError("barcode down")

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "domains.logistics.services.shipping_label.calculate_shipping_rate",
                fake_rate,
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_tracking_qr",
                fake_qr,
            )
            mp.setattr(
                "domains.logistics.services.shipping_label.generate_code128",
                fake_barcode,
            )
            with caplog.at_level(logging.ERROR):
                result = create_shipment_label(_VALID_SHIPMENT, _VALID_DESTINATION)

        assert "error" in result["rate"]
        assert result["qr_code"] is None
        assert result["barcode"] is None
        assert "calculate_shipping_rate failed" in caplog.text
        assert "generate_tracking_qr failed" in caplog.text
        assert "generate_code128 failed" in caplog.text
