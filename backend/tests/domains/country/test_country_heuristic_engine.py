"""
Tests for country_heuristic_engine.py
=======================================
Tests cover: constant extraction AP-12 and gateway recommendation logic.
"""

import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "domains", "country", "services", "research"))


class TestCountryStatusPossibleConstant:
    def test_constant_defined(self):
        from country_heuristic_engine import COUNTRY_STATUS_POSSIBLE

        assert COUNTRY_STATUS_POSSIBLE is not None

    def test_constant_value(self):
        from country_heuristic_engine import COUNTRY_STATUS_POSSIBLE

        assert COUNTRY_STATUS_POSSIBLE == "possible"

    def test_constant_used_in_gateway_recommendation(self):
        from country_heuristic_engine import _suggest_gateways

        with patch("country_heuristic_engine.PaymentGatewayRegistry") as mock_registry:
            mock_registry.is_supported.return_value = False
            gateways = _suggest_gateways(
                region="europe", gdp=5000, internet=30, country_code="GB"
            )
            possible_gateways = [
                g for g in gateways if g["recommendation"] == "possible"
            ]
            assert len(possible_gateways) >= 1
            for g in possible_gateways:
                assert g["recommendation"] == "possible"
