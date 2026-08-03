"""
Payment Orchestrator Service
Dynamically enables/disables payment gateways based on country configuration.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from data.db import get_db_context
from data.models import CountryConfig, PaymentOrchestratorSync

logger = logging.getLogger(__name__)


class PaymentOrchestratorService:
    """Manages payment gateway orchestration per country."""
    
    @staticmethod
    def get_enabled_gateways(country_code: str) -> List[Dict[str, Any]]:
        """Get list of enabled payment gateways for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()
            
            if not config or not config.payment_gateways_json:
                return []
            
            try:
                gateways = json.loads(config.payment_gateways_json) if isinstance(config.payment_gateways_json, str) else config.payment_gateways_json
            except (json.JSONDecodeError, TypeError):
                return []
            
            enabled = [g for g in gateways if g.get('enabled', True)]
            return enabled
    
    @staticmethod
    def sync_gateways(country_code: str) -> Dict[str, Any]:
        """Sync gateways from CountryConfig to PaymentOrchestratorSync table."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()
            
            if not config or not config.payment_gateways_json:
                return {"synced": 0, "message": "No gateways configured"}
            
            try:
                gateways = json.loads(config.payment_gateways_json) if isinstance(config.payment_gateways_json, str) else config.payment_gateways_json
            except (json.JSONDecodeError, TypeError):
                return {"synced": 0, "message": "Invalid gateway configuration"}
            
            synced_count = 0
            for gateway in gateways:
                gateway_id = gateway.get('id') or gateway.get('gateway_id')
                if not gateway_id:
                    continue
                
                existing = db.query(PaymentOrchestratorSync).filter(
                    PaymentOrchestratorSync.country_code == country_code.upper(),
                    PaymentOrchestratorSync.gateway_id == gateway_id
                ).first()
                
                if existing:
                    existing.is_active = gateway.get('enabled', True)
                    existing.gateway_name = gateway.get('name', gateway_id)
                    existing.environment = gateway.get('environment', 'test')
                    existing.fee_percent = Decimal(str(gateway.get('fee_percent', 0))) if gateway.get('fee_percent') else None
                    existing.fee_fixed = Decimal(str(gateway.get('fee_fixed', 0))) if gateway.get('fee_fixed') else None
                    existing.supported_payment_methods = json.dumps(gateway.get('payment_methods', [])) if gateway.get('payment_methods') else None
                    existing.status = gateway.get('status', 'active')
                    existing.last_sync_at = datetime.utcnow()
                else:
                    existing = PaymentOrchestratorSync(
                        country_code=country_code.upper(),
                        gateway_id=gateway_id,
                        gateway_name=gateway.get('name', gateway_id),
                        environment=gateway.get('environment', 'test'),
                        is_active=gateway.get('enabled', True),
                        fee_percent=Decimal(str(gateway.get('fee_percent', 0))) if gateway.get('fee_percent') else None,
                        fee_fixed=Decimal(str(gateway.get('fee_fixed', 0))) if gateway.get('fee_fixed') else None,
                        supported_payment_methods=json.dumps(gateway.get('payment_methods', [])) if gateway.get('payment_methods') else None,
                        status=gateway.get('status', 'active'),
                        last_sync_at=datetime.utcnow()
                    )
                    db.add(existing)
                
                synced_count += 1
            
            db.commit()
            return {"synced": synced_count, "message": f"Synced {synced_count} gateways"}
    
    @staticmethod
    def get_gateway_fees(country_code: str, gateway_id: str) -> Dict[str, Any]:
        """Get fee structure for a specific gateway in a country."""
        with get_db_context() as db:
            sync = db.query(PaymentOrchestratorSync).filter(
                PaymentOrchestratorSync.country_code == country_code.upper(),
                PaymentOrchestratorSync.gateway_id == gateway_id
            ).first()
            
            if not sync:
                return {"fee_percent": 0, "fee_fixed": 0}
            
            return {
                "fee_percent": float(sync.fee_percent) if sync.fee_percent else 0,
                "fee_fixed": float(sync.fee_fixed) if sync.fee_fixed else 0,
            }
    
    @staticmethod
    def is_gateway_available(country_code: str, gateway_id: str) -> bool:
        """Check if a gateway is available and enabled for a country."""
        with get_db_context() as db:
            sync = db.query(PaymentOrchestratorSync).filter(
                PaymentOrchestratorSync.country_code == country_code.upper(),
                PaymentOrchestratorSync.gateway_id == gateway_id,
                PaymentOrchestratorSync.is_active == True,
                PaymentOrchestratorSync.status == 'active'
            ).first()
            
            return sync is not None


def invalidate_payment_cache(country_code: str):
    """Invalidate payment-related caches for a country."""
    PaymentOrchestratorService.get_enabled_gateways.cache_clear() if hasattr(PaymentOrchestratorService.get_enabled_gateways, 'cache_clear') else None
