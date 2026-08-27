from __future__ import annotations
import logging
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from domains.finance.models.finance import PayoutBatch
# TODO: Module not yet created
# from domains.finance.services.payments.base import BasePaymentGateway
# TODO: Module not yet created
# from domains.finance.services.payments.base_models import ConnectionTestResult
# TODO: Module not yet created
# from domains.finance.services.payments.base_models import PaymentResult
# TODO: Module not yet created
# from domains.finance.services.payments.base_models import RefundResult
# TODO: Module not yet created
# from domains.finance.services.payments.registry import PaymentGatewayRegistry
"""
Payout Batch Service — Smart automated payout generation.

Handles:
  - #14: Smart Payout Batch Generation (nightly cron gathers eligible settlements)
  - #15: Supplier Self-Approval (SMS/email link for supplier approval)
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, and_

from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import Vendor
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import FinanceAuditLog
from domains.finance.models.payments import LogisticsPartnerPayout
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
from domains.finance.services.finance_service import general_ledger_service as gl
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

# Payout configuration
PAYOUT_HOLDING_DAYS = 7       # Days to hold before payout eligible
MIN_PAYOUT_AMOUNT = Decimal("10.00")  # Minimum payout threshold
BATCH_LIMIT = 200             # Max items per batch


# ── #14: Smart Payout Batch Generation ─────────────────────────────────────


def generate_supplier_payout_batches(
    db: Session,
    country_code: str = None,
    holding_days: int = PAYOUT_HOLDING_DAYS,
) -> dict:
    """
    Nightly cron: Gather eligible supplier settlements and create payout batches.
    
    Logic:
    1. Find all settlements with status='pending' and age > holding_days
    2. Group by supplier
    3. Create batch items for each supplier meeting minimum threshold
    4. Generate batch header with total
    5. Return batches ready for supplier approval
    """
    cutoff_date = _utcnow() - timedelta(days=holding_days)
    
    # Find eligible settlements
    q = db.query(SupplierSettlement).filter(
        SupplierSettlement.status == "pending",
        SupplierSettlement.created_at <= cutoff_date,
    )
    if country_code:
        q = q.filter(SupplierSettlement.country_code == country_code)
    
    settlements = q.all()
    
    if not settlements:
        return {"batches_created": 0, "message": "No eligible settlements"}
    
    # Group by supplier
    supplier_settlements: dict[int, list] = {}
    for s in settlements:
        sid = s.supplier_id
        if sid not in supplier_settlements:
            supplier_settlements[sid] = []
        supplier_settlements[sid].append(s)
    
    batches_created = 0
    total_items = 0
    
    for supplier_id, supplier_s_settlements in supplier_settlements.items():
        total_amount = sum(Decimal(str(s.net_amount or 0)) for s in supplier_s_settlements)
        
        # Skip if below minimum
        if total_amount < MIN_PAYOUT_AMOUNT:
            continue
        
        # Create batch
        batch = _create_payout_batch(
            db,
            entity_type="supplier",
            entity_id=supplier_id,
            settlements=supplier_s_settlements,
            total_amount=total_amount,
            country_code=country_code,
        )
        batches_created += 1
        
        # Send approval email to supplier
        try:
            from domains.comms.services.transactional_email_service import enqueue_supplier_approval_email
            enqueue_supplier_approval_email(
                supplier_id, batch.id, batch.batch_number, float(total_amount)
            )
        except Exception as e:
            logger.warning("Failed to send approval email for batch %s: %s", batch.id, e)
        total_items += len(supplier_s_settlements)
    
    db.commit()
    
    _log_automation(db, "payout_batch_generation", len(settlements), total_items, {
        "batches_created": batches_created,
        "suppliers_processed": len(supplier_settlements),
    }, country_code)
    
    return {
        "batches_created": batches_created,
        "total_settlements": len(settlements),
        "total_items": total_items,
    }


def generate_logistics_payout_batches(
    db: Session,
    country_code: str = None,
    holding_days: int = 7,
) -> dict:
    """Generate payout batches for logistics partners (COD remittances)."""
    cutoff_date = _utcnow() - timedelta(days=holding_days)
    
    q = db.query(LogisticsPartnerPayout).filter(
        LogisticsPartnerPayout.status == "pending",
        LogisticsPartnerPayout.created_at <= cutoff_date,
    )
    if country_code:
        q = q.filter(LogisticsPartnerPayout.country_code == country_code)
    
    payouts = q.all()
    
    if not payouts:
        return {"batches_created": 0, "message": "No eligible logistics payouts"}
    
    # Group by logistics partner
    partner_payouts: dict[int, list] = {}
    for p in payouts:
        pid = p.logistics_partner_id
        if pid not in partner_payouts:
            partner_payouts[pid] = []
        partner_payouts[pid].append(p)
    
    batches_created = 0
    
    for partner_id, partner_payouts_list in partner_payouts.items():
        total_amount = sum(Decimal(str(p.net_amount or 0)) for p in partner_payouts_list)
        
        if total_amount < MIN_PAYOUT_AMOUNT:
            continue
        
        batch = _create_payout_batch(
            db,
            entity_type="logistics",
            entity_id=partner_id,
            settlements=partner_payouts_list,
            total_amount=total_amount,
            country_code=country_code,
        )
        batches_created += 1
    
    db.commit()
    
    _log_automation(db, "logistics_payout_batch", len(payouts), batches_created, {
        "batches_created": batches_created,
    }, country_code)
    
    return {"batches_created": batches_created, "total_payouts": len(payouts)}


def _create_payout_batch(
    db: Session,
    entity_type: str,
    entity_id: int,
    settlements: list,
    total_amount: Decimal,
    country_code: str = None,
) -> PayoutBatch:
    """Create a payout batch with items."""
    batch_number = f"PB-{entity_type[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
    
    batch = PayoutBatch(
        batch_number=batch_number,
        country_code=country_code,
        total_amount=total_amount,
        item_count=len(settlements),
        status="generated",
        created_by=1,  # System user
    )
    db.add(batch)
    db.flush()
    
    for settlement in settlements:
        item = PayoutBatchItem(
            batch_id=batch.id,
            entity_type=entity_type,
            entity_id=entity_id,
            amount=settlement.net_amount or Decimal("0"),
            currency=settlement.currency or "OMR",
            reference=f"Settlement #{settlement.id}",
            status="pending",
            country_code=country_code,
        )
        db.add(item)
        
        # Mark settlement as batched
        settlement.status = "batched"
        settlement.payout_id = batch.id
    
    return batch


# ── #15: Supplier Self-Approval ────────────────────────────────────────────


def get_pending_batches_for_supplier(
    db: Session,
    supplier_id: int,
) -> list[dict]:
    """Get payout batches pending supplier approval."""
    batches = db.query(PayoutBatch).filter(
        PayoutBatch.status == "generated",
        PayoutBatch.items.any(
            PayoutBatchItem.entity_type == "supplier",
            PayoutBatchItem.entity_id == supplier_id,
        ),
    ).all()
    
    return [
        {
            "batch_id": b.id,
            "batch_number": b.batch_number,
            "total_amount": float(b.total_amount or 0),
            "item_count": b.item_count,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in batches
    ]


def supplier_approve_batch(
    db: Session,
    batch_id: int,
    supplier_id: int,
    approved: bool = True,
    notes: str = None,
) -> dict:
    """
    Supplier approves or rejects a payout batch via self-service link.
    
    On approval: status -> 'supplier_approved'
    On rejection: status -> 'supplier_rejected'
    """
    batch = db.query(PayoutBatch).get(batch_id)
    if not batch:
        raise ValueError(f"Batch #{batch_id} not found")
    
    # Verify supplier has items in this batch
    has_items = db.query(PayoutBatchItem).filter(
        PayoutBatchItem.batch_id == batch_id,
        PayoutBatchItem.entity_type == "supplier",
        PayoutBatchItem.entity_id == supplier_id,
    ).first()
    
    if not has_items:
        raise ValueError(f"Supplier #{supplier_id} has no items in batch #{batch_id}")
    
    if batch.status != "generated":
        raise ValueError(f"Batch #{batch_id} is not in 'generated' status (current: {batch.status})")
    
    if approved:
        batch.status = "supplier_approved"
        batch.notes = notes or f"Approved by supplier #{supplier_id}"
    else:
        batch.status = "supplier_rejected"
        batch.notes = notes or f"Rejected by supplier #{supplier_id}"
    
    db.commit()
    
    _log_automation(db, "supplier_approval", batch_id, {
        "approved": approved,
        "supplier_id": supplier_id,
    }, batch.country_code)
    
    return {
        "batch_id": batch_id,
        "status": batch.status,
        "approved": approved,
    }


# ── Helper ─────────────────────────────────────────────────────────────────


def _log_automation(db: Session, kind: str, processed: int, changed: int,
                     detail: dict = None, country_code: str = None):
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=processed,
            records_changed=changed,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Automation log failed: %s", e)
        db.rollback()

# === MERGED from payout_engine.py ===

logger = logging.getLogger(__name__)


class PayoutEngine:
    def __init__(self, db: Session):
        self.db = db

    def _lazy_country_models(self):
        from domains.country.models.countries import CountryConfig, PayoutRuleCategory, PayoutRuleProduct
        return CountryConfig, PayoutRuleCategory, PayoutRuleProduct

    def get_payout_rate(
        self,
        country_code: str,
        supplier_id: int,
        product_id: Optional[int] = None,
        category_slug: Optional[str] = None,
    ) -> Decimal:
        country = self._get_country(country_code)
        if not country:
            logger.warning("Country %s not found", country_code)
            return Decimal("0")

        if product_id is not None:
            rate = self._get_product_payout_rate(country_code, product_id)
            if rate is not None:
                return rate

        if category_slug is not None:
            rate = self._get_category_payout_rate(country_code, category_slug)
            if rate is not None:
                return rate

        return self._get_default_payout_rate(country_code)

    def _get_country(self, country_code: str):
        CountryConfig, _, _ = self._lazy_country_models()
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper(),
            CountryConfig.is_active == True,
        ).first()

    def _get_product_payout_rate(self, country_code: str, product_id: int) -> Optional[Decimal]:
        _, _, PayoutRuleProduct = self._lazy_country_models()
        rule = (
            self.db.query(PayoutRuleProduct)
            .filter(
                PayoutRuleProduct.country_code == country_code.upper(),
                PayoutRuleProduct.product_id == product_id,
                PayoutRuleProduct.is_active == True,
            )
            .first()
        )
        if rule:
            return Decimal(str(rule.payout_rate))
        return None

    def _get_category_payout_rate(self, country_code: str, category_slug: str) -> Optional[Decimal]:
        _, PayoutRuleCategory, _ = self._lazy_country_models()
        rule = (
            self.db.query(PayoutRuleCategory)
            .filter(
                PayoutRuleCategory.country_code == country_code.upper(),
                PayoutRuleCategory.category_slug == category_slug.lower(),
                PayoutRuleCategory.is_active == True,
            )
            .first()
        )
        if rule:
            return Decimal(str(rule.payout_rate))
        return None

    def _get_default_payout_rate(self, country_code: str) -> Decimal:
        country = self._get_country(country_code)
        if country and country.payout_settings_json:
            import json
            try:
                settings = json.loads(country.payout_settings_json)
                if settings and "default_payout_rate" in settings:
                    return Decimal(str(settings["default_payout_rate"]))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        return Decimal("0.10")

    def get_minimum_payout(self, country_code: str) -> Decimal:
        country = self._get_country(country_code)
        if country and country.minimum_payout_amount:
            return Decimal(str(country.minimum_payout_amount))
        return Decimal("10.00")

    def get_payout_currency(self, country_code: str) -> str:
        country = self._get_country(country_code)
        if country and country.payout_currency:
            return country.payout_currency
        if country:
            return country.currency
        return "USD"

    def get_payout_schedule(self, country_code: str) -> dict:
        country = self._get_country(country_code)
        if country and country.payout_settings_json:
            import json
            try:
                settings = json.loads(country.payout_settings_json)
                return {
                    "schedule": settings.get("payout_schedule", "weekly"),
                    "day": settings.get("payout_day", "sunday"),
                    "batch_size": settings.get("batch_size", 50),
                }
            except (json.JSONDecodeError, TypeError):
                pass
        return {"schedule": "weekly", "day": "sunday", "batch_size": 50}

    def calculate_supplier_payout(
        self,
        country_code: str,
        supplier_id: int,
        order_amount: Decimal,
        product_id: Optional[int] = None,
        category_slug: Optional[str] = None,
    ) -> dict:
        rate = self.get_payout_rate(country_code, supplier_id, product_id, category_slug)
        minimum = self.get_minimum_payout(country_code)
        currency = self.get_payout_currency(country_code)

        payout_amount = (order_amount * rate).quantize(Decimal("0.01"))
        is_below_minimum = payout_amount < minimum

        return {
            "rate": rate,
            "payout_amount": payout_amount,
            "minimum_payout": minimum,
            "currency": currency,
            "is_below_minimum": is_below_minimum,
        }

# === MERGED from payment_engine.py ===

logger = logging.getLogger(__name__)


class PaymentEngine:
    """Orchestrates payment operations across countries and gateways.

    Usage::

        engine = PaymentEngine(db)
        result = engine.process_payment(
            country_code="SA",
            gateway_id="stripe",
            amount=199.99,
            currency="SAR",
            order_id=42,
        )
    """

    def __init__(self, db: Session):
        self.db = db

    def _lazy_country_models(self):
        from domains.country.models.countries import CountryConfig, CountryGatewayCredentials
        return CountryConfig, CountryGatewayCredentials

    def __init__(self, db: Session):
        self.db = db

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def process_payment(
        self,
        country_code: str,
        gateway_id: str,
        amount: float,
        currency: str,
        *,
        order_id: int | None = None,
        description: str = "",
        customer: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        environment: str = "test",
        **kwargs: Any,
    ) -> PaymentResult:
        country = self._get_country(country_code)
        if not country:
            return PaymentResult(
                success=False,
                error_code="country_not_found",
                error_message=f"Country '{country_code}' not configured",
            )
        if not self._gateway_enabled_for_country(country, gateway_id):
            return PaymentResult(
                success=False,
                error_code="gateway_not_enabled",
                error_message=f"Gateway '{gateway_id}' is not enabled for {country_code}",
            )
        adapter = self._get_adapter(gateway_id)
        credentials = self._load_credentials(country_code, gateway_id, environment)
        if not self._validate_adapter_creds(adapter, credentials):
            return PaymentResult(
                success=False,
                error_code="credentials_invalid",
                error_message=f"Invalid or missing credentials for {gateway_id} ({environment})",
            )
        return adapter.process_payment(
            amount=amount,
            currency=currency,
            credentials=credentials,
            order_id=order_id,
            description=description,
            customer=customer,
            metadata=metadata,
            **kwargs,
        )

    def process_refund(
        self,
        country_code: str,
        gateway_id: str,
        transaction_id: str,
        amount: float | None = None,
        *,
        environment: str = "test",
        reason: str = "",
        **kwargs: Any,
    ) -> RefundResult:
        adapter = self._get_adapter(gateway_id)
        credentials = self._load_credentials(country_code, gateway_id, environment)
        return adapter.process_refund(
            transaction_id=transaction_id,
            amount=amount,
            credentials=credentials,
            reason=reason,
            **kwargs,
        )

    def test_gateway_connection(
        self,
        country_code: str,
        gateway_id: str,
        *,
        environment: str = "test",
    ) -> ConnectionTestResult:
        adapter = self._get_adapter(gateway_id)
        credentials = self._load_credentials(country_code, gateway_id, environment)
        return adapter.test_connection(credentials)

    def get_available_gateways(self, country_code: str | None = None) -> list[dict[str, Any]]:
        gateways = []
        for gid in PaymentGatewayRegistry.list_available():
            cls = PaymentGatewayRegistry.get(gid)
            enabled = True
            if country_code:
                country = self._get_country(country_code)
                enabled = self._gateway_enabled_for_country(country, gid) if country else False
            gateways.append({
                "gateway_id": gid,
                "display_name": cls.display_name if cls else gid,
                "enabled": enabled,
            })
        return gateways

    def validate_credentials(
        self,
        gateway_id: str,
        credentials: dict[str, Any],
    ) -> bool:
        adapter_cls = PaymentGatewayRegistry.get(gateway_id)
        if not adapter_cls:
            return False
        return adapter_cls().validate_credentials(credentials)

    # ----------------------------------------------------------------
    # Internal helpers
    # ----------------------------------------------------------------

    def _get_country(self, country_code: str):
        CountryConfig, _ = self._lazy_country_models()
        return self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper(),
            CountryConfig.is_active == True,
        ).first()

    def _gateway_enabled_for_country(self, country, gateway_id: str) -> bool:
        raw = country.payment_gateways_json
        if not raw:
            return False
        try:
            gateways = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            return False
        if not isinstance(gateways, list):
            return False
        for gw in gateways:
            if isinstance(gw, dict) and str(gw.get("gateway_id", "")).lower() == gateway_id.lower():
                return bool(gw.get("enabled", False))
        return False

    def _get_adapter(self, gateway_id: str) -> BasePaymentGateway:
        cls = PaymentGatewayRegistry.get_or_raise(gateway_id)
        return cls()

    def _load_credentials(
        self,
        country_code: str,
        gateway_id: str,
        environment: str,
    ) -> dict[str, Any]:
        _, CountryGatewayCredentials = self._lazy_country_models()
        record = self.db.query(CountryGatewayCredentials).filter(
            CountryGatewayCredentials.country_code == country_code.upper(),
            CountryGatewayCredentials.gateway_id == gateway_id,
            CountryGatewayCredentials.environment == environment,
            CountryGatewayCredentials.is_active == True,
        ).first()
        if record and record.encrypted_credentials:
            try:
                import json
                return json.loads(record.encrypted_credentials)
            except (json.JSONDecodeError, TypeError):
                logger.warning("Could not decode credentials for %s/%s/%s", country_code, gateway_id, environment)
                return {}
        return {}

    def _validate_adapter_creds(self, adapter: BasePaymentGateway, credentials: dict[str, Any]) -> bool:
        return bool(credentials) and adapter.validate_credentials(credentials)

# === MERGED from payment_orchestrator.py ===

from infrastructure.utils.datetime_utils import utcnow
"""
Payment Orchestrator Service
Dynamically enables/disables payment gateways based on country configuration.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime

from infrastructure.database.database import get_db_context
from domains.country.models.countries import CountryConfig
from domains.country.models.country_control import PaymentOrchestratorSync

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
                    existing.last_sync_at = utcnow()
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
                        last_sync_at=utcnow()
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

# === MERGED from auto_payout_scheduler.py ===

"""
Auto-Payout Scheduler
=====================
Background job that checks eligible SupplierSettlements AND LogisticsSettlements
whose eligible_at has passed and creates Payout / LogisticsPartnerPayout records
with a PayoutBatch for automated disbursement.

Triggers:
  - On server startup (via main.py lifespan, behind BACKGROUND_JOBS_ENABLED=1)
  - On-demand via POST /admin/payouts/run-auto-sweep

Design:
  Supplier sweep:
    1. Query all pending SupplierSettlements where eligible_at <= now() and payout_id IS NULL
    2. For each eligible settlement → create a Payout record
    3. Group created Payouts by supplier → create PayoutBatchItem per supplier
    4. Wrap everything in a single PayoutBatch (status='draft' for admin review)
    5. Update each settlement with its payout_id
    6. Log to FinanceAutomationLog
    7. Return a summary dict

  Logistics sweep (identical pattern):
    1. Query all pending LogisticsSettlements where eligible_at <= now() and payout_id IS NULL
    2. For each eligible settlement → create a LogisticsPartnerPayout record
    3. Group by partner_id → create PayoutBatchItem per partner (entity_type="logistics")
    4. Same PayoutBatch, same FinanceAutomationLog pattern

Idempotency:
  - Each settlement is processed at most once (guarded by payout_id IS NULL)
  - The entire batch is wrapped in a DB transaction
"""


import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session

from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import SupplierSettlement
from domains.governance.models.admin import LogisticsSettlement
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payout
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from kernel.money import round_money, to_decimal

logger = logging.getLogger(__name__)

# ── Settings ────────────────────────────────────────────────────────────────

# How often the background thread runs (seconds)
SWEEP_INTERVAL_SECONDS = 3600  # 1 hour

# Default holding period (days) used when settlement.eligible_at is NULL
DEFAULT_HOLDING_DAYS = 10


# ── Core sweep logic ────────────────────────────────────────────────────────


def run_auto_payout_sweep(
    db: Session,
    *,
    force_date: datetime | None = None,
    batch_notes: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Find eligible settlements and create payouts.

    Parameters
    ----------
    db : Session
        Active database session.
    force_date : datetime, optional
        Override the eligibility check for testing (defaults to now).
    batch_notes : str, optional
        Notes attached to the PayoutBatch.
    dry_run : bool, default=False
        When True, only count eligible settlements without creating records.

    Returns
    -------
    dict
        Summary with keys:
          - processed: number of settlements processed
          - total_net_amount: sum of net amounts
          - supplier_count: unique suppliers paid
          - payout_ids: list[dict] — supplier_id, payout_id, amount
          - batch_id: PayoutBatch.id (None for dry_run)
          - status: "ok", "no_eligible_settlements", or "error"
          - error: str (only on status="error")
    """
    now = force_date or _utcnow()
    try:
        # ── 1. Find eligible settlements ────────────────────────────────────
        settlements = (
            db.query(SupplierSettlement)
            .filter(
                SupplierSettlement.status == "pending",
                SupplierSettlement.payout_id.is_(None),
                SupplierSettlement.is_deleted == False,  # noqa: E712
                # eligible_at is NULL → use the created_at + default holding period
                (
                    SupplierSettlement.eligible_at.is_(None)
                    & (SupplierSettlement.created_at <= now - timedelta(days=DEFAULT_HOLDING_DAYS))
                )
                | (SupplierSettlement.eligible_at <= now),
            )
            .order_by(SupplierSettlement.supplier_id.asc(), SupplierSettlement.id.asc())
            .all()
        )

        if not settlements:
            return {
                "processed": 0,
                "total_net_amount": 0.0,
                "supplier_count": 0,
                "payout_ids": [],
                "batch_id": None,
                "status": "no_eligible_settlements",
            }

        # ── 2. Verify supplier bank accounts exist ───────────────────────────
        supplier_ids_in_scope = {cast(int, s.supplier_id) for s in settlements}
        try:
            from domains.governance.models.admin import SupplierBankAccount

            bank_accounts = (
                db.query(SupplierBankAccount.supplier_id)
                .filter(
                    SupplierBankAccount.supplier_id.in_(supplier_ids_in_scope),
                    SupplierBankAccount.is_verified == True,  # noqa: E712
                )
                .all()
            )
            verified_supplier_ids = {row[0] for row in bank_accounts}
        except Exception:
            # If SupplierBankAccount model isn't available (no migration yet),
            # proceed without bank verification.
            logger.warning("SupplierBankAccount model not available; skipping bank verification")
            verified_supplier_ids = supplier_ids_in_scope

        # Filter out suppliers without verified bank accounts
        unverified_suppliers = supplier_ids_in_scope - verified_supplier_ids
        if unverified_suppliers:
            logger.warning(
                "Skipping %d suppliers with no verified bank account: %s",
                len(unverified_suppliers),
                sorted(unverified_suppliers),
            )
            settlements = [s for s in settlements if cast(int, s.supplier_id) in verified_supplier_ids]
            if not settlements:
                return {
                    "processed": 0,
                    "total_net_amount": 0.0,
                    "supplier_count": 0,
                    "payout_ids": [],
                    "batch_id": None,
                    "status": "no_eligible_settlements",
                    "warning": f"{len(unverified_suppliers)} supplier(s) skipped: no verified bank account",
                }

        # ── 3. Group by supplier ────────────────────────────────────────────
        supplier_groups: dict[int, list[SupplierSettlement]] = {}
        for s in settlements:
            supplier_groups.setdefault(cast(int, s.supplier_id), []).append(s)

        net_by_supplier: dict[int, Decimal] = {}
        for supplier_id, group in supplier_groups.items():
            net_by_supplier[supplier_id] = sum(
                (to_decimal(s.net_amount or 0) for s in group),
                Decimal("0"),
            )

        total_net = round_money(sum(net_by_supplier.values(), Decimal("0")))

        if dry_run:
            return {
                "processed": len(settlements),
                "total_net_amount": float(total_net),
                "supplier_count": len(supplier_groups),
                "payout_ids": [
                    {"supplier_id": sid, "amount": float(amt), "settlement_count": len(supplier_groups[sid])}
                    for sid, amt in net_by_supplier.items()
                ],
                "batch_id": None,
                "status": "ok",
            }

        # ── 3. Create Payout records (one per settlement) ───────────────────
        created_payouts: list[Payout] = []
        for settlement in settlements:
            country_code = cast(str | None, settlement.country_code) or "OM"
            settlement_currency = cast(str | None, getattr(settlement, "currency", None)) or "OMR"
            payout = Payout(
                supplier_id=cast(int, settlement.supplier_id),
                order_id=cast(int | None, settlement.order_id),
                amount=round_money(to_decimal(settlement.net_amount or 0)),
                currency=settlement_currency,
                method="bank_transfer",
                status="pending",
                country_code=country_code,
                notes=f"Auto-payout from settlement #{settlement.id}",
            )
            db.add(payout)
            db.flush()  # get payout.id

            settlement.payout_id = cast(int, payout.id)
            settlement.status = "processed"
            created_payouts.append(payout)

        # Derive batch-level country_code / currency from the most common
        # values across all settlements (avoids mixing currencies in one batch).
        settlement_countries: dict[str, int] = {}
        settlement_currencies: dict[str, int] = {}
        for s in settlements:
            cc = cast(str | None, getattr(s, "country_code", None)) or "OM"
            settlement_countries[cc] = settlement_countries.get(cc, 0) + 1
            sc = cast(str | None, getattr(s, "currency", None)) or "OMR"
            settlement_currencies[sc] = settlement_currencies.get(sc, 0) + 1
        batch_country = max(settlement_countries, key=settlement_countries.get)  # type: ignore[arg-type]
        batch_currency = max(settlement_currencies, key=settlement_currencies.get)  # type: ignore[arg-type]

        # ── 4. Create PayoutBatch ───────────────────────────────────────────
        batch_number = f"APB-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        payout_batch = PayoutBatch(
            batch_number=batch_number,
            country_code=batch_country,
            total_amount=total_net,
            item_count=len(supplier_groups),
            status="draft",
            notes=batch_notes or f"Auto-payout batch for {len(settlements)} settlements",
        )
        db.add(payout_batch)
        db.flush()

        # ── 5. Create PayoutBatchItem records (one per supplier) ────────────
        for supplier_id, amt in net_by_supplier.items():
            item = PayoutBatchItem(
                batch_id=cast(int, payout_batch.id),
                entity_type="supplier",
                entity_id=supplier_id,
                amount=round_money(amt),
                currency=batch_currency,
                reference=f"Supplier #{supplier_id} — {len(supplier_groups[supplier_id])} settlement(s)",
                status="pending",
                country_code=batch_country,
            )
            db.add(item)

        # ── 6. Log to FinanceAutomationLog ──────────────────────────────────
        log_entry = FinanceAutomationLog(
            kind="auto_payout",
            records_processed=len(settlements),
            records_changed=len(created_payouts),
            detail={
                "batch_id": cast(int, payout_batch.id),
                "batch_number": batch_number,
                "supplier_count": len(supplier_groups),
                "settlement_count": len(settlements),
                "total_net_amount": float(total_net),
                "payout_ids": [cast(int, p.id) for p in created_payouts],
                "batch_country": batch_country,
                "batch_currency": batch_currency,
            },
            country_code=batch_country,
        )
        db.add(log_entry)
        db.commit()

        # ── 7. Send payout notifications ────────────────────────────────────
        notifications: list[dict[str, Any]] = []
        try:
            from domains.comms.services.payout_notification_service import notify_suppliers_of_payout

            summary = {
                "payout_ids": [
                    {"supplier_id": sid, "amount": float(amt), "settlement_count": len(supplier_groups[sid])}
                    for sid, amt in net_by_supplier.items()
                ],
                "batch_number": batch_number,
                "status": "ok",
            }
            notifications = notify_suppliers_of_payout(db, summary)
        except Exception as notify_exc:
            logger.exception("Failed to send payout notifications: %s", notify_exc)

        logger.info(
            "Auto-payout sweep complete: %d settlements → %d payouts "
            "for %d suppliers, batch %s (total %s OMR) — %d notifications",
            len(settlements),
            len(created_payouts),
            len(supplier_groups),
            batch_number,
            float(total_net),
            len(notifications),
        )

        return {
            "processed": len(settlements),
            "total_net_amount": float(total_net),
            "supplier_count": len(supplier_groups),
            "payout_ids": [
                {
                    "supplier_id": sid,
                    "payout_id": cast(int, p.id),
                    "amount": float(to_decimal(p.amount or 0)),
                }
                for sid, group in supplier_groups.items()
                for p in created_payouts
                if cast(int, p.supplier_id) == sid
            ],
            "batch_id": cast(int, payout_batch.id),
            "batch_number": batch_number,
            "status": "ok",
            "notifications": notifications,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Auto-payout sweep failed: %s", exc)
        return {
            "processed": 0,
            "total_net_amount": 0.0,
            "supplier_count": 0,
            "payout_ids": [],
            "batch_id": None,
            "status": "error",
            "error": str(exc),
        }


# ── Logistics payout sweep ──────────────────────────────────────────────────


def run_auto_logistics_payout_sweep(
    db: Session,
    *,
    force_date: datetime | None = None,
    batch_notes: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Find eligible LogisticsSettlements and create LogisticsPartnerPayout records.

    Mirrors ``run_auto_payout_sweep`` but for logistics partners:
      - Queries ``LogisticsSettlement`` instead of ``SupplierSettlement``
      - Creates ``LogisticsPartnerPayout`` records instead of ``Payout``
      - Groups by ``partner_id`` with ``entity_type="logistics"`` in batch items

    Parameters
    ----------
    db : Session
        Active database session.
    force_date : datetime, optional
        Override the eligibility check for testing (defaults to now).
    batch_notes : str, optional
        Notes attached to the PayoutBatch.
    dry_run : bool, default=False
        When True, only count eligible settlements without creating records.

    Returns
    -------
    dict
        Summary with keys:
          - processed: number of settlements processed
          - total_amount: sum of settlement amounts
          - partner_count: unique partners paid
          - payout_ids: list[dict] — partner_id, payout_id, amount
          - batch_id: PayoutBatch.id (None for dry_run)
          - status: "ok", "no_eligible_settlements", or "error"
    """
    now = force_date or _utcnow()
    try:
        # ── 1. Find eligible logistics settlements ──────────────────────────
        settlements = (
            db.query(LogisticsSettlement)
            .filter(
                LogisticsSettlement.status == "pending",
                LogisticsSettlement.payout_id.is_(None),
                # eligible_at is NULL → use created_at + default holding period
                (
                    LogisticsSettlement.eligible_at.is_(None)
                    & (LogisticsSettlement.created_at <= now - timedelta(days=DEFAULT_HOLDING_DAYS))
                )
                | (LogisticsSettlement.eligible_at <= now),
            )
            .order_by(LogisticsSettlement.partner_id.asc(), LogisticsSettlement.id.asc())
            .all()
        )

        if not settlements:
            return {
                "processed": 0,
                "total_amount": 0.0,
                "partner_count": 0,
                "payout_ids": [],
                "batch_id": None,
                "status": "no_eligible_settlements",
            }

        # ── 2. Verify logistics partner bank accounts exist ─────────────────
        partner_ids_in_scope = {cast(int, s.partner_id) for s in settlements}
        try:
            from domains.governance.models.admin import LogisticsPartnerBankAccount

            bank_accounts = (
                db.query(LogisticsPartnerBankAccount.partner_id)
                .filter(
                    LogisticsPartnerBankAccount.partner_id.in_(partner_ids_in_scope),
                    LogisticsPartnerBankAccount.is_active == True,  # noqa: E712
                )
                .all()
            )
            verified_partner_ids = {row[0] for row in bank_accounts}
        except Exception:
            logger.warning("LogisticsPartnerBankAccount model not available; skipping bank verification")
            verified_partner_ids = partner_ids_in_scope

        # Filter out partners without active bank accounts
        unverified_partners = partner_ids_in_scope - verified_partner_ids
        if unverified_partners:
            logger.warning(
                "Skipping %d partners with no active bank account: %s",
                len(unverified_partners),
                sorted(unverified_partners),
            )
            settlements = [s for s in settlements if cast(int, s.partner_id) in verified_partner_ids]
            if not settlements:
                return {
                    "processed": 0,
                    "total_amount": 0.0,
                    "partner_count": 0,
                    "payout_ids": [],
                    "batch_id": None,
                    "status": "no_eligible_settlements",
                    "warning": f"{len(unverified_partners)} partner(s) skipped: no active bank account",
                }

        # ── 3. Group by partner ─────────────────────────────────────────────
        partner_groups: dict[int, list[LogisticsSettlement]] = {}
        for s in settlements:
            partner_groups.setdefault(cast(int, s.partner_id), []).append(s)

        amount_by_partner: dict[int, Decimal] = {}
        for partner_id, group in partner_groups.items():
            amount_by_partner[partner_id] = sum(
                (to_decimal(s.amount or 0) for s in group),
                Decimal("0"),
            )

        total_amount = round_money(sum(amount_by_partner.values(), Decimal("0")))

        if dry_run:
            return {
                "processed": len(settlements),
                "total_amount": float(total_amount),
                "partner_count": len(partner_groups),
                "payout_ids": [
                    {"partner_id": pid, "amount": float(amt), "settlement_count": len(partner_groups[pid])}
                    for pid, amt in amount_by_partner.items()
                ],
                "batch_id": None,
                "status": "ok",
            }

        # ── 4. Create LogisticsPartnerPayout records ────────────────────────
        created_payouts: list[LogisticsPartnerPayout] = []
        for settlement in settlements:
            country_code = cast(str | None, settlement.country_code) or "OM"
            settlement_currency = cast(str | None, getattr(settlement, "currency", None)) or "OMR"
            payout = LogisticsPartnerPayout(
                partner_id=cast(int, settlement.partner_id),
                amount=round_money(to_decimal(settlement.amount or 0)),
                currency=settlement_currency,
                method="bank_transfer",
                status="pending",
                country_code=country_code,
                notes=f"Auto-payout from logistics settlement #{settlement.id}",
            )
            db.add(payout)
            db.flush()

            settlement.payout_id = cast(int, payout.id)
            settlement.status = "processed"
            created_payouts.append(payout)

        # Derive batch-level country_code / currency
        batch_countries: dict[str, int] = {}
        batch_currencies: dict[str, int] = {}
        for s in settlements:
            cc = cast(str | None, getattr(s, "country_code", None)) or "OM"
            batch_countries[cc] = batch_countries.get(cc, 0) + 1
            sc = cast(str | None, getattr(s, "currency", None)) or "OMR"
            batch_currencies[sc] = batch_currencies.get(sc, 0) + 1
        batch_country = max(batch_countries, key=batch_countries.get)  # type: ignore[arg-type]
        batch_currency = max(batch_currencies, key=batch_currencies.get)  # type: ignore[arg-type]

        # ── 5. Create PayoutBatch ───────────────────────────────────────────
        batch_number = f"ALB-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        payout_batch = PayoutBatch(
            batch_number=batch_number,
            country_code=batch_country,
            total_amount=total_amount,
            item_count=len(partner_groups),
            status="draft",
            notes=batch_notes or f"Auto-logistics-payout batch for {len(settlements)} settlements",
        )
        db.add(payout_batch)
        db.flush()

        # ── 6. Create PayoutBatchItem records (one per partner) ─────────────
        for partner_id, amt in amount_by_partner.items():
            item = PayoutBatchItem(
                batch_id=cast(int, payout_batch.id),
                entity_type="logistics",
                entity_id=partner_id,
                amount=round_money(amt),
                currency=batch_currency,
                reference=f"Logistics Partner #{partner_id} — {len(partner_groups[partner_id])} settlement(s)",
                status="pending",
                country_code=batch_country,
            )
            db.add(item)

        # ── 7. Log to FinanceAutomationLog ──────────────────────────────────
        log_entry = FinanceAutomationLog(
            kind="auto_logistics_payout",
            records_processed=len(settlements),
            records_changed=len(created_payouts),
            detail={
                "batch_id": cast(int, payout_batch.id),
                "batch_number": batch_number,
                "partner_count": len(partner_groups),
                "settlement_count": len(settlements),
                "total_amount": float(total_amount),
                "payout_ids": [cast(int, p.id) for p in created_payouts],
                "batch_country": batch_country,
                "batch_currency": batch_currency,
            },
            country_code=batch_country,
        )
        db.add(log_entry)
        db.commit()

        # ── 8. Send payout notifications ────────────────────────────────────
        logistics_notifications: list[dict[str, Any]] = []
        try:
            from domains.comms.services.payout_notification_service import notify_logistics_partners_of_payout

            summary = {
                "payout_ids": [
                    {"partner_id": pid, "amount": float(amt), "settlement_count": len(partner_groups[pid])}
                    for pid, amt in amount_by_partner.items()
                ],
                "batch_number": batch_number,
                "status": "ok",
            }
            logistics_notifications = notify_logistics_partners_of_payout(db, summary)
        except Exception as notify_exc:
            logger.exception("Failed to send logistics payout notifications: %s", notify_exc)

        logger.info(
            "Auto-logistics-payout sweep complete: %d settlements → %d payouts "
            "for %d partners, batch %s (total %s OMR) — %d notifications",
            len(settlements),
            len(created_payouts),
            len(partner_groups),
            batch_number,
            float(total_amount),
            len(logistics_notifications),
        )

        return {
            "processed": len(settlements),
            "total_amount": float(total_amount),
            "partner_count": len(partner_groups),
            "payout_ids": [
                {
                    "partner_id": pid,
                    "payout_id": cast(int, p.id),
                    "amount": float(to_decimal(p.amount or 0)),
                }
                for pid, group in partner_groups.items()
                for p in created_payouts
                if cast(int, p.partner_id) == pid
            ],
            "batch_id": cast(int, payout_batch.id),
            "batch_number": batch_number,
            "status": "ok",
            "notifications": logistics_notifications,
        }

    except Exception as exc:
        db.rollback()
        logger.exception("Auto-logistics-payout sweep failed: %s", exc)
        return {
            "processed": 0,
            "total_amount": 0.0,
            "partner_count": 0,
            "payout_ids": [],
            "batch_id": None,
            "status": "error",
            "error": str(exc),
        }


# ── Background job state (exposed for admin dashboard) ───────────────────


_auto_payout_thread: threading.Thread | None = None
_stop_event = threading.Event()
_background_status: dict[str, Any] = {
    "is_running": False,
    "is_thread_alive": False,
    "last_run_at": None,
    "last_run_status": None,
    "last_error": None,
    "total_sweep_count": 0,
    "total_settlements_processed": 0,
    "last_supplier_result": None,
    "last_logistics_result": None,
    "thread_started_at": None,
    "thread_stopped_at": None,
}
_background_status_lock = threading.Lock()


def update_background_status(**kwargs: Any) -> None:
    """Thread-safe update of the shared background-status dict.

    This is a public function exposed so the admin router can update
    in-memory state after a manual trigger (POST /background-job/trigger).
    """
    with _background_status_lock:
        _background_status.update(kwargs)


def _update_background_status(**kwargs: Any) -> None:
    """Internal alias for backward compatibility."""
    update_background_status(**kwargs)
    """Thread-safe update of the shared background-status dict."""
    with _background_status_lock:
        _background_status.update(kwargs)


def get_background_job_status() -> dict[str, Any]:
    """Return a snapshot of the background job state for the admin dashboard.

    Returns a copy so callers can't mutate internal state.
    """
    with _background_status_lock:
        snapshot = dict(_background_status)
    # Live-check the thread
    snapshot["is_thread_alive"] = (
        _auto_payout_thread is not None and _auto_payout_thread.is_alive()
    )
    return snapshot


def _update_after_sweep(
    sweep_name: str,
    result: dict[str, Any],
    status: str,
) -> None:
    """Update shared state after a background sweep run.

    Uses the lock for atomic read-modify-write to avoid race conditions
    between the supplier and logistics sweeps running sequentially.
    """
    error = result.get("error") if status == "error" else None
    processed = result.get("processed", 0)

    with _background_status_lock:
        prev_total = _background_status.get("total_settlements_processed", 0)
        prev_error = _background_status.get("last_error")
        _background_status["total_settlements_processed"] = prev_total + processed

        if sweep_name == "supplier":
            _background_status["last_supplier_result"] = result
            # Always update last_run_status — if logistics runs after and fails,
            # the logistics branch below will overwrite this
            _background_status["last_run_status"] = status
            if error:
                _background_status["last_error"] = error
        elif sweep_name == "logistics":
            _background_status["last_logistics_result"] = result
            # Overwrite the top-level status so a logistics failure is visible
            _background_status["last_run_status"] = status
            if error:
                _background_status["last_error"] = error
            elif not _background_status.get("last_error"):
                # Only clear error if neither sweep failed
                _background_status["last_error"] = None

    # ── Fire-and-forget WebSocket broadcast ────────────────────────────────
    _broadcast_sweep_completed(sweep_name=sweep_name, status=status, result=result)


def _broadcast_sweep_completed(
    sweep_name: str,
    status: str,
    result: dict[str, Any],
) -> None:
    """Broadcast a sweep-completion event to the admin dashboard via WebSocket.

    Fires from sync code; silently no-ops if no event loop is running.
    """
    try:
        from infrastructure.utils.websocket_manager import broadcast_background_job_update

        broadcast_background_job_update(
            {
                "event": "sweep_completed",
                "sweep_name": sweep_name,
                "status": status,
                "processed": result.get("processed", 0),
                "batch_number": result.get("batch_number"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception:
        logger.debug("Failed to broadcast sweep completion (expected if no WS connected)")


def start_auto_payout_background_job(interval_seconds: int = SWEEP_INTERVAL_SECONDS) -> None:
    """Start a daemon thread that runs both supplier and logistics payout
    sweeps periodically.

    Call this once from the application lifespan.  The thread is a daemon so it
    will be killed when the main process exits.

    Use ``BACKGROUND_JOBS_ENABLED=1`` env var (already checked in main.py) to
    gate this behind the same flag as other background jobs.
    """
    global _auto_payout_thread
    if _auto_payout_thread is not None and _auto_payout_thread.is_alive():
        logger.warning("Auto-payout background job is already running, skipping duplicate start.")
        return

    _stop_event.clear()
    _update_background_status(
        is_running=True,
        thread_started_at=datetime.now(timezone.utc).isoformat(),
        thread_stopped_at=None,
    )

    def _loop() -> None:
        logger.info("Auto-payout background job started (interval=%ds)", interval_seconds)
        # Initial run after a short delay to let the server warm up
        _run_once_with_retry(delay_before=15)
        while not _stop_event.is_set():
            if _stop_event.wait(interval_seconds):
                break
            _run_once_with_retry()

    _auto_payout_thread = threading.Thread(target=_loop, daemon=True, name="auto-payout-sweep")
    _auto_payout_thread.start()
    logger.info("Auto-payout background job thread started.")


def stop_auto_payout_background_job() -> None:
    """Signal the background thread to stop gracefully."""
    _stop_event.set()
    _update_background_status(
        is_running=False,
        thread_stopped_at=datetime.now(timezone.utc).isoformat(),
    )
    logger.info("Auto-payout background job stop requested.")


def _run_once_with_retry(delay_before: int = 0) -> None:
    """Run both supplier and logistics sweeps inside a fresh DB session."""
    if delay_before > 0:
        time.sleep(delay_before)

    try:
        from infrastructure.database.database import SessionLocal

        # Supplier sweep
        db = SessionLocal()
        try:
            result = run_auto_payout_sweep(db)
            status = result.get("status", "error")
            if status == "no_eligible_settlements":
                logger.debug("Supplier auto-payout sweep: no eligible settlements.")
            elif status == "ok":
                logger.info(
                    "Supplier auto-payout sweep: %d settlements → %d suppliers, batch=%s total=%s",
                    result.get("processed", 0),
                    result.get("supplier_count", 0),
                    result.get("batch_number"),
                    result.get("total_net_amount"),
                )
            else:
                logger.error("Supplier auto-payout sweep error: %s", result.get("error"))
            _update_after_sweep("supplier", result, status)
        finally:
            db.close()

        # Logistics sweep
        db = SessionLocal()
        try:
            result = run_auto_logistics_payout_sweep(db)
            status = result.get("status", "error")
            if status == "no_eligible_settlements":
                logger.debug("Logistics auto-payout sweep: no eligible settlements.")
            elif status == "ok":
                logger.info(
                    "Logistics auto-payout sweep: %d settlements → %d partners, batch=%s total=%s",
                    result.get("processed", 0),
                    result.get("partner_count", 0),
                    result.get("batch_number"),
                    result.get("total_amount"),
                )
            else:
                logger.error("Logistics auto-payout sweep error: %s", result.get("error"))
            _update_after_sweep("logistics", result, status)
        finally:
            db.close()

        _update_background_status(
            last_run_at=datetime.now(timezone.utc).isoformat(),
            total_sweep_count=_background_status.get("total_sweep_count", 0) + 1,
        )

    except Exception as exc:
        logger.exception("Auto-payout sweep runner crashed: %s", exc)
        _update_background_status(
            last_run_at=datetime.now(timezone.utc).isoformat(),
            last_run_status="error",
            last_error=str(exc),
        )

# === MERGED from payments_gateway_service.py ===

"""Payments gateway service — order payment orchestration primitives.

Stub implementations: the canonical payment logic is being consolidated into the
service layer. These symbols are re-exported by
``services.finance.order_payment_functions`` and consumed across the orders and
payments controllers. They are provided here as leaf definitions so the import
graph stays acyclic and ``import main`` succeeds.
"""

from typing import Any, Optional
import structlog
logger = structlog.get_logger(__name__)


def apply_order_status_change(order: Any, new_status: str, db: Any = None, **kwargs: Any) -> Any:
    order.status = new_status
    if db is not None:
        db.commit()
        db.refresh(order)
    return order


def build_order_payment_snapshot(order: Any, db: Any = None) -> dict:
    return {
        "order_id": getattr(order, "id", None),
        "status": getattr(order, "status", None),
        "total": getattr(order, "total_amount", None),
    }


def confirm_cash_on_delivery_order(order: Any, db: Any = None) -> Any:
    return apply_order_status_change(order, "confirmed", db)


def is_checkout_payment_method_allowed(method: str, country_code: Optional[str] = None) -> bool:
    return bool(method)


def normalize_checkout_payment_method(method: str) -> str:
    return (method or "").strip().lower()


def event_publisher(event: str, **payload: Any) -> None:
    return None


def order_holds_inventory(order: Any) -> bool:
    return bool(getattr(order, "items", None))


__all__ = [
    "apply_order_status_change",
    "build_order_payment_snapshot",
    "confirm_cash_on_delivery_order",
    "is_checkout_payment_method_allowed",
    "normalize_checkout_payment_method",
    "_event_publisher",
    "_order_holds_inventory",
]

# === MERGED from admin_payouts_service.py ===

"""Auto-migrated service logic from routers/admin_payouts.py."""
# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import _update_bg_status_after_manual_trigger

from fastapi import Depends, HTTPException, Path, Query

from pydantic import BaseModel

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import PayoutCreate, PayoutOut

from domains.accounts.models.user import User
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.payments import Payout

from domains.audit.services.logs.audit_service import AuditAction, audit_log

# TODO: Module not yet created
# from domains.finance.services.auto_payout_scheduler import get_background_job_status as _get_bg_status

# TODO: Module not yet created
# from domains.finance.services.auto_payout_scheduler import run_auto_logistics_payout_sweep as _run_logistics_sweep

# TODO: Module not yet created
# from domains.finance.services.auto_payout_scheduler import run_auto_payout_sweep as _run_supplier_sweep

# TODO: Module not yet created
# from domains.finance.services.auto_payout_scheduler import start_auto_payout_background_job as _start_bg_job

# TODO: Module not yet created
# from domains.finance.services.auto_payout_scheduler import stop_auto_payout_background_job as _stop_bg_job

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.datetime_utils import utcnow

from infrastructure.utils.dependencies import require_admin

from infrastructure.database.rls_interceptor import clear_rls_context, set_rls_context

class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = "verified"















# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import create_payout






















# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import list_pending_payouts














# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import list_pending_payouts_by_country











# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import verify_payout













# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import run_auto_payout_sweep














# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import process_payout
# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import get_background_job_status_endpoint


# === auto-wiring re-exports (migration repair) ===
# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import start_background_job
# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import stop_background_job
# TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import trigger_background_job
# TODO: Module not yet created
# # TODO: Module not yet created
# from domains.governance.services.admin_treasury_status_service import trigger_background_job_kind

# === MERGED from payout_notification_service.py ===

"""
Payout Notification Service
===========================
Sends email notifications to suppliers and logistics partners when the
auto-payout sweep creates new PayoutBatch records.

Relies on ``email_service.send_email`` (Resend API if configured, else
console-log).  Falls back to the ``NotificationEngine`` in-app notification
when the email send fails or the user has no email address.

Design decisions:
  - Notifications are sent synchronously from the sweep function so the
    caller (background thread or admin endpoint) sees any failures in
    the sweep result's ``notifications`` field.
  - Only one notification per supplier/partner per batch is sent
    (aggregates all settlements for that entity).
  - If the entity has no verified email address, falls back to an in-app
    notification via NotificationEngine.
"""


import logging
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

# ── HTML email builders ────────────────────────────────────────────────────

FRONTEND_URL = "http://localhost:3000"  # overridden by settings if available


def _get_frontend_url() -> str:
    """Return the configured frontend URL or the development default."""
    try:
        from config import settings

        return getattr(settings, "frontend_url", FRONTEND_URL)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("Handled Exception in payout_notification_service.py:44")
        return FRONTEND_URL


def _build_supplier_payout_email(
    supplier_name: str,
    amount: Decimal | float,
    batch_number: str,
    supplier_id: int,
) -> str:
    """Build an HTML email body for a supplier payout notification."""
    payout_url = f"{_get_frontend_url()}/supplier/payouts"
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1a1a2e;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h1 style="font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0;">ZOZI</h1>
    <p style="font-size: 13px; color: #6b7280; margin: 4px 0 0;">Payout Notification</p>
  </div>

  <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
    <p style="font-size: 14px; color: #374151; margin: 0 0 8px;">A payout has been initiated for</p>
    <p style="font-size: 22px; font-weight: 800; color: #16a34a; margin: 0 0 4px;">
      {amount:,.2f} OMR
    </p>
    <p style="font-size: 12px; color: #6b7280; margin: 0;">Batch: {batch_number}</p>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Supplier</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #6b7280; text-align: right; border-bottom: 1px solid #e5e7eb;">
        {supplier_name}
      </td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Status</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #f59e0b; text-align: right; border-bottom: 1px solid #e5e7eb;">
        Pending Approval
      </td>
    </tr>
  </table>

  <p style="font-size: 12px; color: #6b7280; line-height: 1.5;">
    This payout is in <strong>draft</strong> status and requires admin approval
    before it is dispatched.  Payment is estimated within <strong>3–5 business days</strong>
    after approval.  You can track its status at any time from your payout dashboard.
  </p>

  <div style="text-align: center; margin: 24px 0;">
    <a href="{payout_url}"
       style="display: inline-block; background: #1a1a2e; color: #fff; text-decoration: none;
              font-size: 14px; font-weight: 600; padding: 12px 32px; border-radius: 8px;">
      View Payout Dashboard →
    </a>
  </div>

  <p style="font-size: 11px; color: #9ca3af; text-align: center; margin-top: 32px;">
    ZOZI E-Commerce Platform &middot; Automated payout notification
  </p>
</body>
</html>"""


def _build_logistics_payout_email(
    partner_name: str,
    amount: Decimal | float,
    batch_number: str,
    partner_id: int,
) -> str:
    """Build an HTML email body for a logistics partner payout notification."""
    payout_url = f"{_get_frontend_url()}/logistics-partner/payouts"
    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #1a1a2e;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h1 style="font-size: 20px; font-weight: 700; color: #1a1a2e; margin: 0;">ZOZI</h1>
    <p style="font-size: 13px; color: #6b7280; margin: 4px 0 0;">Logistics Payout Notification</p>
  </div>

  <div style="background: #eff6ff; border: 1px solid #93c5fd; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
    <p style="font-size: 14px; color: #374151; margin: 0 0 8px;">A logistics payout has been initiated for</p>
    <p style="font-size: 22px; font-weight: 800; color: #2563eb; margin: 0 0 4px;">
      {amount:,.2f} OMR
    </p>
    <p style="font-size: 12px; color: #6b7280; margin: 0;">Batch: {batch_number}</p>
  </div>

  <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Partner</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #6b7280; text-align: right; border-bottom: 1px solid #e5e7eb;">
        {partner_name}
      </td>
    </tr>
    <tr>
      <td style="padding: 8px 12px; font-size: 13px; color: #374151; border-bottom: 1px solid #e5e7eb;">
        <strong>Status</strong>
      </td>
      <td style="padding: 8px 12px; font-size: 13px; color: #f59e0b; text-align: right; border-bottom: 1px solid #e5e7eb;">
        Pending Approval
      </td>
    </tr>
  </table>

  <p style="font-size: 12px; color: #6b7280; line-height: 1.5;">
    This payout is in <strong>draft</strong> status and requires admin approval
    before it is dispatched.  You can track its status from your payout dashboard.
  </p>

  <div style="text-align: center; margin: 24px 0;">
    <a href="{payout_url}"
       style="display: inline-block; background: #1a1a2e; color: #fff; text-decoration: none;
              font-size: 14px; font-weight: 600; padding: 12px 32px; border-radius: 8px;">
      View Payout Dashboard →
    </a>
  </div>

  <p style="font-size: 11px; color: #9ca3af; text-align: center; margin-top: 32px;">
    ZOZI E-Commerce Platform &middot; Automated payout notification
  </p>
</body>
</html>"""


# ── Public API ─────────────────────────────────────────────────────────────


def notify_suppliers_of_payout(
    db: Session,
    sweep_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Send payout notification emails to all suppliers in the sweep result.

    Parameters
    ----------
    db : Session
        Active database session (used to look up user details).
    sweep_result : dict
        The return value from ``run_auto_payout_sweep()``.  Must contain
        ``payout_ids`` (list of ``{supplier_id, payout_id, amount}``),
        ``batch_number``, and ``status``.

    Returns
    -------
    list[dict]
        One entry per notification sent (or attempted), each with keys:
        ``supplier_id``, ``email``, ``status``, and optionally ``error``.
    """
    from infrastructure.utils.email_service import send_email

    notifications: list[dict[str, Any]] = []
    payout_ids = sweep_result.get("payout_ids", [])
    batch_number = sweep_result.get("batch_number", "N/A")

    if not payout_ids or sweep_result.get("status") != "ok":
        logger.debug("No supplier payouts to notify for batch %s", batch_number)
        return notifications

    # Deduplicate by supplier_id (one notification per supplier per batch)
    # N+1 removal: resolve every supplier user in a single query before the loop.
    users_by_id: dict[int, Any] = {}
    prefetch_error: Exception | None = None
    try:
        from domains.governance.models.user import User

        unique_supplier_ids = list(dict.fromkeys(
            cast(int, entry.get("supplier_id")) for entry in payout_ids
        ))
        if unique_supplier_ids:
            supplier_rows = (
                db.query(User)
                .filter(User.id.in_(unique_supplier_ids))
                .limit(SAFE_QUERY_LIMIT)
                .all()
            )
            for row in supplier_rows:
                users_by_id.setdefault(row.id, row)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:  # surfaced per-supplier below to preserve error reporting
        logger.exception("Handled Exception in payout_notification_service.py:232")
        prefetch_error = exc

    seen_suppliers: set[int] = set()
    for entry in payout_ids:
        supplier_id = cast(int, entry.get("supplier_id"))
        if supplier_id in seen_suppliers:
            continue
        seen_suppliers.add(supplier_id)

        amount = cast(float, entry.get("amount", 0))
        supplier_name = f"Supplier #{supplier_id}"
        email: str | None = None

        try:
            if prefetch_error is not None:
                raise prefetch_error

            # Look up the supplier user record for name + email
            user = users_by_id.get(supplier_id)
            if user:
                supplier_name = getattr(user, "full_name", None) or getattr(user, "username", None) or supplier_name

            email = getattr(user, "email", None) if user else None
            if not email:
                logger.warning(
                    "No email for supplier %d; sending in-app notification instead.",
                    supplier_id,
                )
                _send_in_app_notification_separate_session(
                    supplier_id,
                    title="New Payout Initiated",
                    message=f"A payout of {amount:,.2f} OMR (batch {batch_number}) has been initiated for your settlements.",
                )
                notifications.append({
                    "supplier_id": supplier_id,
                    "email": None,
                    "status": "in_app_fallback",
                })
                continue

            html = _build_supplier_payout_email(supplier_name, amount, batch_number, supplier_id)
            send_email(
                to=email,
                subject=f"ZOZI Payout — {amount:,.2f} OMR ({batch_number})",
                html=html,
            )
            notifications.append({
                "supplier_id": supplier_id,
                "email": email,
                "status": "sent",
            })
            logger.info("Payout notification sent to supplier %d <%s>", supplier_id, email)

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            logger.exception("Failed to notify supplier %d: %s", supplier_id, exc)
            notifications.append({
                "supplier_id": supplier_id,
                "email": email,
                "status": "error",
                "error": str(exc),
            })

    return notifications


def notify_logistics_partners_of_payout(
    db: Session,
    sweep_result: dict[str, Any],
) -> list[dict[str, Any]]:
    """Send payout notification emails to all logistics partners in the sweep result.

    Parameters
    ----------
    db : Session
        Active database session (used to look up partner details).
    sweep_result : dict
        The return value from ``run_auto_logistics_payout_sweep()``.

    Returns
    -------
    list[dict]
        One entry per notification sent (or attempted).
    """
    from infrastructure.utils.email_service import send_email

    notifications: list[dict[str, Any]] = []
    payout_ids = sweep_result.get("payout_ids", [])
    batch_number = sweep_result.get("batch_number", "N/A")

    if not payout_ids or sweep_result.get("status") != "ok":
        logger.debug("No logistics payouts to notify for batch %s", batch_number)
        return notifications

    # N+1 removal: resolve partners and their linked users in bulk before the loop.
    partners_by_id: dict[Any, Any] = {}
    users_by_id: dict[Any, Any] = {}
    prefetch_error: Exception | None = None
    try:
        from domains.logistics.models.logistics import LogisticsPartner
        from domains.governance.models.user import User

        unique_partner_ids = list(dict.fromkeys(
            cast(int, entry.get("partner_id")) for entry in payout_ids
        ))
        if unique_partner_ids:
            partner_rows = (
                db.query(LogisticsPartner)
                .filter(LogisticsPartner.id.in_(unique_partner_ids))
                .limit(SAFE_QUERY_LIMIT)
                .all()
            )
            for row in partner_rows:
                partners_by_id.setdefault(row.id, row)

        partner_user_ids = list(dict.fromkeys(
            uid for uid in (
                getattr(p, "user_id", None) for p in partners_by_id.values()
            ) if uid is not None
        ))
        if partner_user_ids:
            user_rows = (
                db.query(User)
                .filter(User.id.in_(partner_user_ids))
                .limit(SAFE_QUERY_LIMIT)
                .all()
            )
            for row in user_rows:
                users_by_id.setdefault(row.id, row)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:  # surfaced per-partner below to preserve error reporting
        logger.exception("Handled Exception in payout_notification_service.py:361")
        prefetch_error = exc

    seen_partners: set[int] = set()
    for entry in payout_ids:
        partner_id = cast(int, entry.get("partner_id"))
        if partner_id in seen_partners:
            continue
        seen_partners.add(partner_id)

        amount = cast(float, entry.get("amount", 0))
        partner_name = f"Partner #{partner_id}"
        email: str | None = None

        try:
            if prefetch_error is not None:
                raise prefetch_error

            # Look up the logistics partner record
            partner = partners_by_id.get(partner_id)
            if partner:
                partner_name = getattr(partner, "company_name", None) or getattr(partner, "name", None) or partner_name

            # The partner record may have an email field; also check user relation
            email = getattr(partner, "email", None)
            if not email and partner:
                user = users_by_id.get(getattr(partner, "user_id", None))
                email = getattr(user, "email", None) if user else None

            if not email:
                logger.warning(
                    "No email for logistics partner %d; sending in-app notification instead.",
                    partner_id,
                )
                _send_in_app_notification_separate_session(
                    partner_id,
                    title="New Logistics Payout Initiated",
                    message=f"A logistics payout of {amount:,.2f} OMR (batch {batch_number}) has been initiated.",
                )
                notifications.append({
                    "partner_id": partner_id,
                    "email": None,
                    "status": "in_app_fallback",
                })
                continue

            html = _build_logistics_payout_email(partner_name, amount, batch_number, partner_id)
            send_email(
                to=email,
                subject=f"ZOZI Logistics Payout — {amount:,.2f} OMR ({batch_number})",
                html=html,
            )
            notifications.append({
                "partner_id": partner_id,
                "email": email,
                "status": "sent",
            })
            logger.info("Payout notification sent to partner %d <%s>", partner_id, email)

        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
            logger.exception("Failed to notify logistics partner %d: %s", partner_id, exc)
            notifications.append({
                "partner_id": partner_id,
                "email": email,
                "status": "error",
                "error": str(exc),
            })

    return notifications


def _send_in_app_notification_separate_session(
    user_id: int,
    title: str,
    message: str,
) -> None:
    """Fallback: create an in-app notification using a SEPARATE DB session.

    Using a separate session prevents any notification write failure from
    affecting the settlement sweep's session (which has already been
    committed).  The notification is best-effort — errors are logged.
    """
    try:
        from infrastructure.database.database import SessionLocal
        from domains.comms.services.shared.notification.notification_engine import NotificationEngine
        from domains.comms.services.shared.notification.notification_engine import NotificationChannel
        from domains.comms.services.shared.notification.notification_engine import NotificationPriority

        notif_db = SessionLocal()
        try:
            engine = NotificationEngine(notif_db)
            engine.send(
                user_id=user_id,
                title=title,
                message=message,
                channel=NotificationChannel.IN_APP,
                priority=NotificationPriority.HIGH,
            )
        finally:
            notif_db.close()
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as exc:
        logger.debug("In-app notification fallback failed for user %d: %s", user_id, exc)

# === MERGED from payout_admin_service.py ===

"""Treasury payout-admin service.

Thin service layer backing the payout-admin controller. Operations are kept
deliberately small; this module exists so the routers -> controllers ->
services circuit (CIR2) is preserved for payout administration.
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.payments import Payout
import structlog
logger = structlog.get_logger(__name__)


def query_payouts_by_country(
    db: Session, country_code: str, skip: int = 0, limit: int = 20, **kwargs: Any
) -> list:
    return (
        db.query(Payout)
        .filter(Payout.country_code == country_code.upper())
        .order_by(Payout.id.desc())
        
        .limit(limit)
        .all()
    )


def query_pending_payouts(db: Session, skip: int = 0, limit: int = 20, **kwargs: Any) -> list:
    return (
        db.query(Payout)
        .filter(Payout.status == "pending")
        .order_by(Payout.id.desc())
        
        .limit(limit)
        .all()
    )


def query_pending_payouts_by_country(
    db: Session, country_code: str, skip: int = 0, limit: int = 20, **kwargs: Any
) -> list:
    return (
        db.query(Payout)
        .filter(Payout.country_code == country_code.upper(), Payout.status == "pending")
        .order_by(Payout.id.desc())
        
        .limit(limit)
        .all()
    )


def get_payout(db: Session, payout_id: int) -> Optional[Payout]:
    return db.query(Payout).filter(Payout.id == payout_id).first()


def create_payout_record(db: Session, **kwargs: Any) -> Payout:
    fields = {k: v for k, v in kwargs.items() if hasattr(Payout, k)}
    payout = Payout(**fields)
    db.add(payout)
    db.flush()
    db.commit()
    db.refresh(payout)
    return payout


def verify_payout_record(
    db: Session, payout_id: int, verified_by: Optional[int] = None, **kwargs: Any
) -> Optional[Payout]:
    payout = get_payout(db, payout_id)
    if payout is None:
        return None
    payout.status = "verified"
    db.commit()
    db.refresh(payout)
    return payout


def process_payout_record(
    db: Session, payout_id: int, processed_by: Optional[int] = None, **kwargs: Any
) -> Optional[Payout]:
    payout = get_payout(db, payout_id)
    if payout is None:
        return None
    payout.status = "processed"
    db.commit()
    db.refresh(payout)
    return payout


def query_recent_automation_logs(db: Session, limit: int = 20, **kwargs: Any) -> list:
    return db.query(FinanceAutomationLog).limit(limit).all()

# === MERGED from payout_admin_write_service.py ===

"""Admin payout write service.

Owns every DB mutation behind the country-scoped admin payout endpoints so the
router and controller layers stay write-free (W1 layer contract).

Each function takes ``db: Session`` first, performs the mutation, commits, and
raises ``HTTPException`` exactly as the original router code did.

NOTE: the ``audit_log(...)`` calls below are reproduced verbatim from the
original router endpoints (same arguments, same position *after* the commit) so
that runtime behaviour is byte-for-byte preserved by this refactor.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.payments import Payout
from domains.audit.services.logs.audit_service import AuditAction, audit_log
from infrastructure.utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)


def create_country_payout(
    db: Session,
    *,
    country_code: str,
    payload,
    admin_id,
    admin_username,
) -> Payout:
    """Create a payout for ``country_code`` and audit the action."""
    model_cols = {c.name for c in Payout.__table__.columns}
    data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
    p = Payout(**data, country_code=country_code)
    db.add(p); db.commit(); db.refresh(p)
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=p.id,
        details={"amount": str(p.amount) if p.amount else None, "method": p.method},
    )
    return p


def verify_country_payout(
    db: Session,
    *,
    country_code: str,
    payout_id: int,
    payload,
    admin_id,
    admin_username,
) -> dict:
    """Mark a payout as verified (or the status supplied on the payload)."""
    p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code).first()
    if not p:
        raise HTTPException(404, "Payout not found")
    p.status = payload.status if payload and payload.status else "verified"
    p.processed_at = utcnow()
    if payload:
        if payload.note:
            p.notes = payload.note
        if payload.bank_reference:
            p.reference = payload.bank_reference
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"status": p.status, "reference": p.reference, "notes": p.notes},
    )
    return {"verified": True, "payout_id": payout_id}


def process_country_payout(
    db: Session,
    *,
    country_code: str,
    payout_id: int,
    admin_id,
    admin_username,
) -> dict:
    """Mark a payout as paid."""
    p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code).first()
    if not p:
        raise HTTPException(404)
    p.status = "paid"; p.processed_at = utcnow()
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"status": "paid"},
    )
    return {"message": "Payout processed"}

# === MERGED from payout_read_service.py ===

"""Supplier payout read service (W1).

Owns the read behind ``supplier_payout_controller.list_supplier_payouts`` so the
controller no longer reaches into the ORM directly.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.models.suppliers import SupplierProfile
from domains.finance.models.payments import Payout
import structlog

logger = structlog.get_logger(__name__)


def list_supplier_payouts(current_user, db: Session) -> list[Payout]:
    """Return all payouts for the calling supplier's profile."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == current_user.id)
        .first()
    )
    if not supplier:
        raise HTTPException(404)
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier.id)
        .order_by(Payout.created_at.desc())
        .all()
    )

# === MERGED from payouts_service.py ===

"""Admin payout management controller."""

from typing import Any, List, Optional, cast
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from domains.comms.models.communication import Notification
from domains.finance.models.finance import TransactionLedger
from domains.finance.models.finance import SupplierSettlement
from domains.governance.models.admin import LogisticsSettlement
from domains.finance.models.payments import Payout
from domains.audit.services.logs.audit_service import audit_log, AuditAction


def list_pending_payouts(db: Session, limit: int = 200, offset: int = 0) -> list:
    payouts = (
        db.query(Payout)
        .options(joinedload(Payout.supplier))
        .filter(Payout.status.in_(["pending", "processing"]))
        .order_by(Payout.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 200))
        .all()
    )
    return [
        {
            "id": payout.id,
            "supplier_id": payout.supplier_id,
            "supplier_username": payout.supplier.username if payout.supplier else None,
            "amount": float(cast(Any, getattr(payout, "amount")) or 0),
            "status": payout.status,
            "method": payout.method,
            "reference": payout.reference_id,
            "notes": payout.notes,
            "created_at": payout.created_at,
            "processed_at": payout.processed_at,
        }
        for payout in payouts
    ]


def _refresh_order_finance_settlement_status(order_id: int, db: Session) -> None:
    entries = db.query(TransactionLedger).filter(TransactionLedger.order_id == order_id).limit(1000).all()
    if not entries:
        return

    supplier_pairs = [(entry.supplier_id, order_id) for entry in entries if entry.supplier_id]
    logistics_pairs = [
        (entry.logistics_partner_id, order_id)
        for entry in entries
        if entry.logistics_partner_id
    ]

    supplier_settlements = {
        (row.supplier_id, row.order_id): row
        for row in db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.order_id == order_id,
            SupplierSettlement.supplier_id.in_([p[0] for p in supplier_pairs]),
        )
        .all()
    }

    logistics_settlements = {
        (row.partner_id, row.order_id): row
        for row in db.query(LogisticsSettlement)
        .filter(
            LogisticsSettlement.order_id == order_id,
            LogisticsSettlement.partner_id.in_([p[0] for p in logistics_pairs]),
        )
        .all()
    }

    for entry in entries:
        if str(getattr(entry, "settlement_status", "") or "") == "refunded":
            continue

        supplier_settlement = supplier_settlements.get((entry.supplier_id, order_id))
        logistics_settlement = logistics_settlements.get((entry.logistics_partner_id, order_id)) if entry.logistics_partner_id else None

        supplier_done = bool(supplier_settlement and supplier_settlement.status == "settled")
        logistics_done = True if entry.logistics_partner_id is None else bool(
            logistics_settlement and logistics_settlement.status == "settled"
        )

        if supplier_done and logistics_done:
            entry.settlement_status = "fully_settled"
        elif supplier_done:
            entry.settlement_status = "supplier_settled"
        elif logistics_done:
            entry.settlement_status = "logistics_settled"
        else:
            entry.settlement_status = "pending"


def _sync_supplier_settlements_for_payout(
    payout_id: int,
    new_status: str,
    processed_at: datetime | None,
    db: Session,
) -> None:
    settlements = db.query(SupplierSettlement).filter(SupplierSettlement.payout_id == payout_id).all()
    if not settlements:
        return

    touched_order_ids: set[int] = set()
    now = processed_at or datetime.now(timezone.utc).replace(tzinfo=None)

    for settlement in settlements:
        touched_order_ids.add(cast(int, settlement.order_id))

        if new_status == "completed":
            settlement.status = "settled"
            settlement.settled_at = now
        elif new_status == "rejected":
            settlement.status = "eligible" if settlement.eligible_at and settlement.eligible_at <= now else "pending"
            settlement.payout_id = None
            settlement.settled_at = None
            settlement.bank_transaction_id = None
        else:
            settlement.status = "processing"
            settlement.settled_at = None

    for order_id in touched_order_ids:
        _refresh_order_finance_settlement_status(order_id, db)


def verify_payout(
    payout_id: int,
    data: dict,
    acting_user: dict,
    db: Session,
) -> dict:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    new_status = str(data.get("status", "")).strip().lower()
    if new_status not in {"processing", "completed", "rejected"}:
        raise HTTPException(status_code=422, detail="status must be one of: processing, completed, rejected")

    setattr(payout, "status", new_status)
    setattr(
        payout,
        "reference_id",
        str(data.get("reference", "")).strip()
        or cast(str | None, getattr(payout, "reference_id"))
        or build_transfer_reference(
            db,
            kind="supplier_payout",
            entity_id=int(cast(int, getattr(payout, "supplier_id"))),
            record_id=int(cast(int, getattr(payout, "id"))),
        ),
    )
    setattr(payout, "notes", str(data.get("notes", "")).strip() or cast(str | None, getattr(payout, "notes")))
    processed_at: datetime | None = None
    if new_status in {"completed", "rejected"}:
        processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        setattr(payout, "processed_at", processed_at)
    else:
        setattr(payout, "processed_at", None)

    _sync_supplier_settlements_for_payout(payout_id, new_status, processed_at, db)

    supplier_id = cast(int | None, getattr(payout, "supplier_id"))
    if supplier_id:
        message = (
            f"Your payout request #{payout.id} is now {new_status}."
            if new_status != "completed"
            else f"Your payout request #{payout.id} has been completed."
        )
        db.add(
            Notification(
                user_id=supplier_id,
                type="payout",
                title="Payout Update",
                message=message,
                link="/supplier/payouts",
            )
        )

    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="payout",
        resource_id=cast(int, getattr(payout, "id")),
        details={"status": new_status, "reference": cast(str | None, getattr(payout, "reference_id"))},
        status="success",
    )
    return {
        "id": payout.id,
        "status": payout.status,
        "reference": payout.reference_id,
        "notes": payout.notes,
        "processed_at": payout.processed_at,
    }

# === MERGED from payout_approval_read_service.py ===

"""Payout-approval read service.

Owns the read/aggregation behind the Admin Payout Approval Dashboard so the
router stays free of ``db.query`` calls. The shape returned by ``get_pending_payouts``
is identical to the former inline implementation in ``routers/public_treasury_payments.py``.
"""

from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session, joinedload

# User imported lazily to avoid circular import
_User_model = None

def _get_User():
    global _User_model
    if _User_model is None:
        from domains.governance.ports import User as _U
        _User_model = _U
    return _User_model
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.logistics.models.logistics import LogisticsPartner
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payout


def _serialize_payout(p: Payout) -> dict[str, Any]:
    return {
        "id": cast(int, p.id),
        "supplier_id": cast(int | None, p.supplier_id),
        "order_id": cast(int | None, p.order_id),
        "amount": float(cast(Decimal, p.amount or 0)),
        "currency": cast(str | None, p.currency) or "OMR",
        "method": cast(str | None, p.method) or "",
        "status": cast(str | None, p.status) or "",
        "reference": cast(str | None, p.reference),
        "notes": cast(str | None, p.notes),
        "country_code": cast(str | None, p.country_code) or "",
        "created_at": cast(Any, p.created_at).isoformat() if getattr(p, "created_at", None) else None,
        "processed_at": cast(Any, p.processed_at).isoformat() if getattr(p, "processed_at", None) else None,
    }


def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
    return {
        "id": cast(int, item.id),
        "entity_type": cast(str, item.entity_type),
        "entity_id": cast(int, item.entity_id),
        "amount": float(cast(Decimal, item.amount or 0)),
        "currency": cast(str | None, item.currency) or "OMR",
        "reference": cast(str | None, item.reference),
        "status": cast(str | None, item.status) or "",
    }


def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
    return {
        "id": cast(int, batch.id),
        "batch_number": cast(str, batch.batch_number),
        "country_code": cast(str, batch.country_code),
        "total_amount": float(cast(Decimal, batch.total_amount or 0)),
        "item_count": cast(int, batch.item_count or 0),
        "status": cast(str, batch.status),
        "notes": cast(str | None, batch.notes),
        "created_at": cast(Any, batch.created_at).isoformat() if getattr(batch, "created_at", None) else None,
        "items": [_serialize_batch_item(item) for item in (batch.items or [])],
    }


def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    if not entity_ids:
        return {}
    users = db.query(User).filter(User.id.in_(entity_ids)).all()
    return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}


def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    if not entity_ids:
        return {}
    partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
    return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}


def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
    items = list(batch.items or [])
    supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "supplier"}
    logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "logistics"}
    supplier_names = _resolve_supplier_names(supplier_ids, db)
    logistics_names = _resolve_logistics_names(logistics_ids, db)

    enriched = []
    for item in items:
        e = _serialize_batch_item(item)
        eid = cast(int, item.entity_id)
        etype = cast(str, item.entity_type)
        if etype == "supplier":
            e["entity_name"] = supplier_names.get(eid, f"Supplier #{eid}")
        elif etype == "logistics":
            e["entity_name"] = logistics_names.get(eid, f"Partner #{eid}")
        else:
            e["entity_name"] = f"#{eid}"
        enriched.append(e)
    return enriched


def _load_unbatched_payouts(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    query = db.query(Payout).filter(Payout.status.in_(["pending", "draft"]))
    total = query.count()
    payouts = query.order_by(Payout.created_at.desc()).limit(page_size).all()

    supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
    supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}

    result = []
    for payout in payouts:
        s = _serialize_payout(payout)
        sid = cast(int | None, payout.supplier_id)
        s["supplier_name"] = supplier_names.get(cast(int, sid), f"Supplier #{sid}") if sid else None
        result.append(s)
    return result, total


def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(
        PayoutBatch.status.in_(["draft", "pending"])
    )
    total = query.count()
    batches = query.order_by(PayoutBatch.created_at.desc()).limit(page_size).all()

    result = []
    for batch in batches:
        enriched_items = _enrich_batch_items(batch, db)
        s = _serialize_batch(batch)
        s["items"] = enriched_items
        result.append(s)
    return result, total


def get_pending_payouts(db: Session, page: int, page_size: int) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review."""
    batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
    unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

    logistics_payout_q = db.query(LogisticsPartnerPayout).filter(
        LogisticsPartnerPayout.status.in_(["pending", "draft"]),
    )
    logistics_payout_total = logistics_payout_q.count()
    logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).limit(page_size).all()

    logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
    logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}

    unbatched_logistics = []
    for lp in logistics_payouts:
        pid = cast(int | None, lp.partner_id)
        unbatched_logistics.append({
            "id": cast(int, lp.id),
            "partner_id": pid,
            "partner_name": logistics_names.get(cast(int, pid), f"Partner #{pid}") if pid else None,
            "amount": float(cast(Decimal, lp.amount or 0)),
            "currency": cast(str | None, lp.currency) or "OMR",
            "status": cast(str | None, lp.status) or "",
            "reference": cast(str | None, lp.reference),
            "notes": cast(str | None, lp.notes),
            "created_at": cast(Any, lp.created_at).isoformat() if getattr(lp, "created_at", None) else None,
        })

    total_amount = sum(b["total_amount"] for b in batches)
    total_items = sum(b["item_count"] for b in batches)

    return {
        "pending_batches": batches,
        "unbatched_payouts": unbatched,
        "unbatched_logistics_payouts": unbatched_logistics,
        "summary": {
            "total_batches": batch_total,
            "total_amount": round(total_amount, 2),
            "total_items": total_items,
            "pending_payouts_count": payout_total,
            "pending_logistics_payouts_count": logistics_payout_total,
        },
        "pagination": {"page": page, "page_size": page_size},
    }


def list_payouts(db: Session, country_code: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """List payouts for a country with pagination (returns ORM rows)."""
    q = db.query(Payout).filter(Payout.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def list_pending_payouts(db: Session, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """List all pending payouts (RLS-scoped by request context if set)."""
    q = db.query(Payout).filter(Payout.status == "pending")
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def list_pending_payouts_by_country(db: Session, country_code: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """List pending payouts for a specific country."""
    q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def get_payout_approval_history(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    """Recent FinanceAutomationLog entries for the auto-payout background job."""
    history = (
        db.query(FinanceAutomationLog)
        .filter(FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]))
        .order_by(FinanceAutomationLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id,
            "kind": h.kind,
            "records_processed": h.records_processed,
            "records_changed": h.records_changed,
            "detail": h.detail,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]

# === MERGED from payout_approval_service.py ===

"""Payout approval workflow service (Law 2: domain owns the transaction).

Mirrors the admin payout-approval router's mutate endpoints so the HTTP layer
stays a thin wrapper. Reads (the /pending dashboard) remain in the router as the
accepted read-layer.
"""

from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session, joinedload

from domains.finance.models.finance import PayoutBatch, PayoutBatchItem
from domains.logistics.models.logistics import LogisticsPartner
from domains.finance.models.payments import LogisticsPartnerPayout, Payout
from domains.audit.services.logs.audit_service import audit_log, AuditAction
from infrastructure.utils.datetime_utils import utcnow


def approve_payout(payout_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException_not_found("Payout not found")
    if payout.status not in ("pending", "draft"):
        raise HTTPException_conflict(f"Cannot approve payout in '{payout.status}' status.")
    payout.status = "approved"
    if notes:
        payout.notes = (payout.notes or "") + f"\nApproved: {notes}"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}


def reject_payout(payout_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException_not_found("Payout not found")
    if payout.status not in ("pending", "draft", "approved"):
        raise HTTPException_conflict(f"Cannot reject payout in '{payout.status}' status.")
    payout.status = "rejected"
    if notes:
        payout.notes = (payout.notes or "") + f"\nRejected: {notes}"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}


def _load_batch(batch_id: int, db: Session) -> PayoutBatch:
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException_not_found("Payout batch not found")
    return batch


def approve_batch(batch_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Approve a payout batch — draft → approved."""
    batch = _load_batch(batch_id, db)
    if batch.status not in ("draft", "pending"):
        raise HTTPException_conflict(
            f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved."
        )
    now = utcnow()
    batch.status = "approved"
    batch.approved_by = cast(int, admin_id)
    batch.notes = (batch.notes or "") + (
        f"\nApproved by admin #{admin_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "approved"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout_batch",
        resource_id=batch_id,
        details={"action": "approve", "batch_number": batch.batch_number},
    )
    return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}


def reject_batch(batch_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Reject a payout batch — draft → rejected."""
    batch = _load_batch(batch_id, db)
    if batch.status not in ("draft", "pending", "approved"):
        raise HTTPException_conflict(f"Cannot reject batch in '{batch.status}' status.")
    now = utcnow()
    old_status = batch.status
    batch.status = "rejected"
    batch.notes = (batch.notes or "") + (
        f"\nRejected by admin #{admin_id} at {now.isoformat()}."
        + (f" Reason: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "pending"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout_batch",
        resource_id=batch_id,
        details={"action": "reject", "batch_number": batch.batch_number, "previous_status": old_status},
    )
    return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}


def dispatch_batch(batch_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch."""
    batch = _load_batch(batch_id, db)
    if batch.status != "approved":
        raise HTTPException_conflict(
            f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched."
        )
    now = utcnow()
    batch.status = "dispatched"
    batch.dispatched_at = now
    batch.notes = (batch.notes or "") + (
        f"\nDispatched by admin #{admin_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )

    supplier_payout_ids: list[int] = []
    logistics_payout_ids: list[int] = []

    for item in batch.items or []:
        item.status = "paid"
        etype = cast(str, item.entity_type)
        eid = cast(int, item.entity_id)
        if etype == "supplier":
            supplier_payout_ids.append(eid)
        elif etype == "logistics":
            logistics_payout_ids.append(eid)

    if supplier_payout_ids:
        db.query(Payout).filter(
            Payout.supplier_id.in_(supplier_payout_ids),
            Payout.status.in_(["pending", "approved"]),
        ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

    if logistics_payout_ids:
        db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.partner_id.in_(logistics_payout_ids),
            LogisticsPartnerPayout.status.in_(["pending", "approved"]),
        ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout_batch",
        resource_id=batch_id,
        details={"action": "dispatch", "batch_number": batch.batch_number},
    )
    return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}


def HTTPException_not_found(detail: str):
    from fastapi import HTTPException
    return HTTPException(status_code=404, detail=detail)


def HTTPException_conflict(detail: str):
    from fastapi import HTTPException
    return HTTPException(status_code=409, detail=detail)

# === MERGED from payout_approval_write_service.py ===

"""Payout-approval write service (W1-exempt transaction owner).

Owns every DB mutation behind the Admin Payout Approval Dashboard so that
``routers/payout_approval.py`` and ``controllers/payout_approval_controller.py``
stay free of ``db.add`` / ``db.commit`` / ``db.delete`` / ``db.flush`` (audit
rule W1: only ``services/**`` may own DB transactions).

Behaviour is preserved exactly as it was implemented in the router:
status-transition guards (404 / 409), note-append formatting, batch-item
cascades, the dispatch fan-out to ``Payout`` / ``LogisticsPartnerPayout``, and
the returned response payloads.

NOTE — audit logging: the router previously called
``audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=..., username=...,
user_role=..., resource_type=..., resource_id=...)``. That call could never
succeed: ``AuditAction`` has no ``PAYOUT_PROCESSED`` member (AttributeError) and
``domains.audit.services.logs.audit_service.audit_log`` takes ``actor_id`` / ``entity`` / ``entity_key`` rather
than ``user_id`` / ``resource_type`` / ``resource_id``. Every write endpoint
therefore raised HTTP 500 *after* committing. The calls below preserve the
original intent while matching the real ``audit_log`` signature.
"""

from decimal import Decimal
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from domains.comms.models.suppliers import SupplierProfile
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payout
from domains.audit.services.logs.audit_service import audit_log
from infrastructure.utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)

# Action recorded on the audit trail for every payout-approval mutation.
PAYOUT_PROCESSED = "payout_processed"


# ── Internal helpers ─────────────────────────────────────────────────────────


def _audit(
    db: Session,
    *,
    actor_id: int | None,
    actor_username: str | None,
    entity: str,
    entity_key: Any,
    details: dict[str, Any],
) -> None:
    """Record a payout-approval action on the audit trail.

    ``audit_log`` swallows and logs its own exceptions, so a failure here can
    never mask the already-committed business mutation.
    """
    audit_log(
        db=db,
        actor_id=int(actor_id or 0),
        action=PAYOUT_PROCESSED,
        entity=entity,
        entity_key=str(entity_key),
        details={**details, "username": actor_username, "role": "admin"},
    )


def _get_payout_or_404(db: Session, payout_id: int) -> Payout:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    return payout


def _get_batch_or_404(db: Session, batch_id: int) -> PayoutBatch:
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Payout batch not found")
    return batch


# ── Individual payout actions ────────────────────────────────────────────────


def approve_payout(
    db: Session,
    payout_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    payout = _get_payout_or_404(db, payout_id)
    if payout.status not in ("pending", "draft"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve payout in '{payout.status}' status.",
        )
    payout.status = "approved"
    if notes:
        payout.notes = (payout.notes or "") + f"\nApproved: {notes}"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout",
        entity_key=payout_id,
        details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}


def reject_payout(
    db: Session,
    payout_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    payout = _get_payout_or_404(db, payout_id)
    if payout.status not in ("pending", "draft", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject payout in '{payout.status}' status.",
        )
    payout.status = "rejected"
    if notes:
        payout.notes = (payout.notes or "") + f"\nRejected: {notes}"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout",
        entity_key=payout_id,
        details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}


# ── Batch-level actions ──────────────────────────────────────────────────────


def approve_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Approve a payout batch — moves it from draft → approved."""
    batch = _get_batch_or_404(db, batch_id)
    if batch.status not in ("draft", "pending"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved.",
        )
    now = utcnow()
    batch.status = "approved"
    batch.approved_by = cast(int, actor_id)
    batch.notes = (batch.notes or "") + (
        f"\nApproved by admin #{actor_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "approved"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout_batch",
        entity_key=batch_id,
        details={"action": "approve", "batch_number": batch.batch_number},
    )
    return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}


def reject_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Reject a payout batch — moves it from draft → rejected."""
    batch = _get_batch_or_404(db, batch_id)
    if batch.status not in ("draft", "pending", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject batch in '{batch.status}' status.",
        )
    now = utcnow()
    old_status = batch.status
    batch.status = "rejected"
    batch.notes = (batch.notes or "") + (
        f"\nRejected by admin #{actor_id} at {now.isoformat()}."
        + (f" Reason: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "pending"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout_batch",
        entity_key=batch_id,
        details={
            "action": "reject",
            "batch_number": batch.batch_number,
            "previous_status": old_status,
        },
    )
    return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}


def dispatch_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch.

    Updates the batch status to dispatched, marks all batch items as paid,
    and updates the underlying Payout / LogisticsPartnerPayout records to paid.
    """
    batch = _get_batch_or_404(db, batch_id)
    if batch.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched.",
        )
    now = utcnow()
    batch.status = "dispatched"
    batch.dispatched_at = now
    batch.notes = (batch.notes or "") + (
        f"\nDispatched by admin #{actor_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )

    supplier_payout_ids: list[int] = []
    logistics_payout_ids: list[int] = []

    for item in batch.items or []:
        item.status = "paid"
        etype = cast(str, item.entity_type)
        eid = cast(int, item.entity_id)
        if etype == "supplier":
            supplier_payout_ids.append(eid)
        elif etype == "logistics":
            logistics_payout_ids.append(eid)

    # --- Bulk-update Payout records for suppliers in this batch ---
    # Batch items store entity_id = supplier_id (set by the auto-payout
    # scheduler).  We match by Payout.supplier_id, which is the correct
    # column.  This is safe because the status filter (pending/approved)
    # prevents touching already-paid payouts from prior batches.
    if supplier_payout_ids:
        db.query(Payout).filter(
            Payout.supplier_id.in_(supplier_payout_ids),
            Payout.status.in_(["pending", "approved"]),
        ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

    if logistics_payout_ids:
        db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.partner_id.in_(logistics_payout_ids),
            LogisticsPartnerPayout.status.in_(["pending", "approved"]),
        ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout_batch",
        entity_key=batch_id,
        details={"action": "dispatch", "batch_number": batch.batch_number},
    )
    return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}


# ── Bulk status maintenance ──────────────────────────────────────────────────


def update_payout_status_by_ids(db: Session, payout_ids: list[int], status: str) -> None:
    """Update status for specific Payout records by their primary key.

    Moved out of the router with the rest of the write path; the caller owns
    when (or whether) to commit.
    """
    if payout_ids:
        now = utcnow()
        db.query(Payout).filter(
            Payout.id.in_(payout_ids),
            Payout.status.in_(["pending", "draft", "approved"]),
        ).update({"status": status, "processed_at": now}, synchronize_session=False)


def request_supplier_payout(db: Session, current_user, payload: dict) -> dict:
    """Create a supplier-initiated payout request and commit."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, 'Supplier profile not found')
    amount = payload.get('amount')
    if not amount or float(amount) <= 0:
        raise HTTPException(400, 'A positive payout amount is required')
    payout = Payout(
        supplier_id=supplier.id,
        amount=float(amount),
        method=payload.get('method', 'bank'),
        notes=payload.get('notes', 'Supplier-initiated payout request'),
        status='pending',
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return {
        'status': 'success',
        'payout': {
            'id': payout.id,
            'amount': float(payout.amount),
            'status': payout.status,
        },
    }

# === MERGED from payout_status_service.py ===

'Treasury payout status controller.\n\nHolds the read/write logic for admin payout records (list / create / verify /\nprocess). Previously inline in ``routers.admin_treasury_status`` (CG1: ``Payout``\ninstantiation in router, W1: ``db.add``/``db.commit`` in router, DBA32: OFFSET\npagination). Routers now set RLS context, authorize, and delegate here.\n\nLists use keyset (seek) pagination via an opaque ``cursor`` (``created_at`` +\n``id``) instead of ``OFFSET``.\n'
import base64
# TODO: Module not yet created
# from domains.comms.services.utility.db_read import query as db_read_query
# TODO: Module not yet created
# from domains.comms.services.utility.db_read import execute as db_read_execute
from datetime import datetime
from typing import Optional, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from domains.finance.models.payments import Payout
from domains.audit.services.logs.audit_service import AuditAction, audit_log
# TODO: Module not yet created
# from domains.comms.services.utility.write_helpers import commit_and_refresh
# TODO: Module not yet created
# from domains.comms.services.utility.write_helpers import commit_only
from infrastructure.utils.datetime_utils import utcnow

def _encode_cursor(dt: datetime, id_: int) -> str:
    raw = f'{dt.isoformat()}|{id_}'
    return base64.urlsafe_b64encode(raw.encode()).decode()

def _decode_cursor(cursor: Optional[str]) -> Optional[Tuple[datetime, int]]:
    if not cursor:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        (iso, id_) = raw.split('|')
        return (datetime.fromisoformat(iso), int(id_))
    except Exception:
        return None

def list_payouts(country_code: str, db: Session, limit: int, cursor: Optional[str]=None) -> Tuple[list[Payout], Optional[str], bool]:
    q = db_read_query(db, Payout).filter(Payout.country_code == country_code.upper())
    cur = _decode_cursor(cursor)
    if cur:
        (cdt, cid) = cur
        q = q.filter((Payout.created_at < cdt) | (Payout.created_at == cdt) & (Payout.id < cid))
    rows = q.order_by(Payout.created_at.desc(), Payout.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    return (rows, next_cursor, has_more)

def list_pending_payouts(db: Session, limit: int, cursor: Optional[str]=None) -> Tuple[list[Payout], Optional[str], bool]:
    q = db_read_query(db, Payout).filter(Payout.status == 'pending')
    cur = _decode_cursor(cursor)
    if cur:
        (cdt, cid) = cur
        q = q.filter((Payout.created_at < cdt) | (Payout.created_at == cdt) & (Payout.id < cid))
    rows = q.order_by(Payout.created_at.desc(), Payout.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    return (rows, next_cursor, has_more)

def list_pending_payouts_by_country(country_code: str, db: Session, limit: int, cursor: Optional[str]=None) -> Tuple[list[Payout], Optional[str], bool]:
    q = db_read_query(db, Payout).filter(Payout.status == 'pending', Payout.country_code == country_code.upper())
    cur = _decode_cursor(cursor)
    if cur:
        (cdt, cid) = cur
        q = q.filter((Payout.created_at < cdt) | (Payout.created_at == cdt) & (Payout.id < cid))
    rows = q.order_by(Payout.created_at.desc(), Payout.id.desc()).limit(limit).all()
    has_more = len(rows) == limit
    next_cursor = _encode_cursor(rows[-1].created_at, rows[-1].id) if has_more else None
    return (rows, next_cursor, has_more)

def create_payout(country_code: str, payload, current_admin, db: Session) -> Payout:
    model_cols = {c.name for c in Payout.__table__.columns}
    data = {k: v for (k, v) in payload.model_dump().items() if k in model_cols}
    p = Payout(**data, country_code=country_code.upper())
    p = commit_and_refresh(db, p)
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=p.id, details={'amount': str(p.amount) if p.amount else None, 'method': p.method})
    return p

def verify_payout(country_code: str, payout_id: int, payload, current_admin, db: Session) -> dict:
    p = db_read_query(db, Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
    if not p:
        raise HTTPException(404, 'Payout not found')
    p.status = payload.status if payload and payload.status else 'verified'
    p.processed_at = utcnow()
    if payload:
        if payload.note:
            p.notes = payload.note
        if payload.bank_reference:
            p.reference = payload.bank_reference
    commit_only(db)
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': p.status, 'reference': p.reference, 'notes': p.notes})
    return {'verified': True, 'payout_id': payout_id}

def process_payout(country_code: str, payout_id: int, current_admin, db: Session) -> dict:
    p = db_read_query(db, Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
    if not p:
        raise HTTPException(404)
    p.status = 'paid'
    p.processed_at = utcnow()
    commit_only(db)
    audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': 'paid'})
    return {'message': 'Payout processed'}

# === MERGED from payout_dispatch_service.py ===

"""Payout transfer-dispatch write service.

Owns the DB write path for bulk payout transfer dispatch so the
controller/router layer stays read-only (LC1 / W1 layer contract):

* ``dispatch_transfer_batch_with_audit`` performs the writes through a
  caller-supplied session (used by the synchronous admin endpoint).
* ``run_dispatch_transfer_batch_job`` owns the session lifecycle and the
  ``commit``/``rollback`` (used by the background job enqueued from the
  controller). It is the only place here that opens a session and commits.
"""

from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

# TODO: Module not yet created
# from domains.finance.services.ledger.finance_transfer_service import execute_transfer_batch
from domains.audit.services.logs.audit_service import AuditAction, audit_log
from infrastructure.database.database import SessionLocal
import structlog
logger = structlog.get_logger(__name__)


def normalize_dispatch_kind(kind: str) -> tuple[str, str]:
    normalized_kind = kind.strip().lower()
    if normalized_kind not in {"supplier", "logistics"}:
        raise HTTPException(status_code=422, detail="kind must be 'supplier' or 'logistics'")
    export_type = "supplier-payout-transfers" if normalized_kind == "supplier" else "logistics-payout-transfers"
    return normalized_kind, export_type


def dispatch_transfer_batch_with_audit(
    kind: str,
    admin_user: dict,
    db: Session,
    *,
    provider: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    normalized_kind, export_type = normalize_dispatch_kind(kind)
    result = execute_transfer_batch(
        export_type,
        db=db,
        provider=provider,
        dry_run=dry_run,
    )
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_user.get("id"),
        username=admin_user.get("username"),
        user_role=admin_user.get("role"),
        resource_type=f"{normalized_kind}_payout_dispatch",
        details={
            "provider": result.get("provider"),
            "status": result.get("status"),
            "dry_run": dry_run,
            "dispatchable_count": result.get("dispatchable_count"),
            "skipped_count": result.get("skipped_count"),
            "batch_reference": result.get("batch_reference"),
        },
    )
    return result


def run_dispatch_transfer_batch_job(
    kind: str,
    admin_user: dict,
    *,
    provider: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Background-job entrypoint: owns the session lifecycle and commit."""
    session = SessionLocal()
    try:
        result = dispatch_transfer_batch_with_audit(
            kind,
            admin_user,
            session,
            provider=provider,
            dry_run=dry_run,
        )
        session.commit()
        return result
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("run_dispatch_transfer_batch_job_failed", error=str(e))
        session.rollback()
        raise
    finally:
        session.close()

# === MERGED from refund_posting_service.py ===

"""
Refund Posting Service — Auto journal entry creation on refund approval.

Handles:
  - #26: Auto Refund Posting + Supplier Deduction
  
Refund Journal Entries:
  - Card refund: Dr 2030 Customer Refund Reserve / Cr 1020 Gateway Clearing
  - COD refund: Dr 2030 Customer Refund Reserve / Cr 1010 Cash Operating
  - Commission reversal: Dr 4010 Commission Revenue / Cr 2030 Customer Refund Reserve
  - VAT reversal: Dr 2040 VAT Payable / Cr 2030 Customer Refund Reserve
  - Supplier deduction: Dr 2010 Supplier Payable / Cr 2030 Customer Refund Reserve
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.finance.models.finance import RefundLedger
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TransactionLedger
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import FinanceAuditLog
from domains.orders.models.orders import Order
from infrastructure.database.schemas import JournalEntryCreate, JournalLineInput
from domains.finance.services.finance_service import general_ledger_service as gl
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


# ── #26: Auto Refund Posting ───────────────────────────────────────────────


def post_refund_automatically(
    db: Session,
    refund_id: int,
    approved_by: int = None,
    country_code: str = None,
) -> dict:
    """
    Auto-post journal entries when a refund is approved.
    
    Creates reversing entries:
    1. Reverse original revenue recognition
    2. Post refund liability
    3. Deduct from supplier payable (if applicable)
    """
    refund = db.query(RefundLedger).get(refund_id)
    if not refund:
        raise ValueError(f"Refund #{refund_id} not found")
    
    if refund.status == "posted":
        return {"status": "already_posted", "refund_id": refund_id}
    
    if refund.status not in ("approved", "pending"):
        raise ValueError(f"Refund #{refund_id} cannot be posted (status: {refund.status})")
    
    order = db.query(Order).get(refund.order_id)
    if not order:
        raise ValueError(f"Order #{refund.order_id} not found for refund #{refund_id}")
    
    cc = country_code or order.country_code
    
    # Get refund amounts
    customer_refund = Decimal(str(refund.customer_refund_amount or 0))
    commission_reversal = Decimal(str(refund.commission_reversal or 0))
    vat_adjustment = Decimal(str(refund.vat_adjustment or 0))
    supplier_deduction = Decimal(str(refund.supplier_reversal or 0))
    
    lines = []
    
    # 1. Refund liability: Dr 2030 Customer Refund Reserve
    if customer_refund > 0:
        if order.payment_method == "card":
            # Card refund goes through gateway
            lines.append(JournalLineInput(
                account_code="2030",
                side="debit",
                amount=customer_refund,
                description=f"Customer refund liability - Order #{order.id}",
            ))
            lines.append(JournalLineInput(
                account_code="1020",
                side="credit",
                amount=customer_refund,
                description=f"Gateway clearing - refund to card - Order #{order.id}",
            ))
        else:
            # COD refund from cash
            lines.append(JournalLineInput(
                account_code="2030",
                side="debit",
                amount=customer_refund,
                description=f"Customer refund liability - Order #{order.id}",
            ))
            lines.append(JournalLineInput(
                account_code="1010",
                side="credit",
                amount=customer_refund,
                description=f"Cash operating - COD refund - Order #{order.id}",
            ))
    
    # 2. Commission reversal: Dr 4010 / Cr 2030
    if commission_reversal > 0:
        lines.append(JournalLineInput(
            account_code="4010",
            side="debit",
            amount=commission_reversal,
            description=f"Commission revenue reversal - Order #{order.id}",
        ))
        lines.append(JournalLineInput(
            account_code="2030",
            side="credit",
            amount=commission_reversal,
            description=f"Refund reserve from commission reversal - Order #{order.id}",
        ))
    
    # 3. VAT reversal: Dr 2040 / Cr 2030
    if vat_adjustment > 0:
        lines.append(JournalLineInput(
            account_code="2040",
            side="debit",
            amount=vat_adjustment,
            description=f"VAT payable reversal - Order #{order.id}",
        ))
        lines.append(JournalLineInput(
            account_code="2030",
            side="credit",
            amount=vat_adjustment,
            description=f"Refund reserve from VAT reversal - Order #{order.id}",
        ))
    
    # 4. Supplier deduction: Dr 2010 / Cr 2030
    if supplier_deduction > 0:
        lines.append(JournalLineInput(
            account_code="2010",
            side="debit",
            amount=supplier_deduction,
            description=f"Supplier payable deduction - Order #{order.id}",
        ))
        lines.append(JournalLineInput(
            account_code="2030",
            side="credit",
            amount=supplier_deduction,
            description=f"Refund reserve from supplier deduction - Order #{order.id}",
        ))
    
    if not lines:
        return {"status": "no_amounts", "refund_id": refund_id}
    
    # Create journal entry
    entry_data = JournalEntryCreate(
        entry_date=_utcnow(),
        reference_type="refund",
        reference_id=refund.id,
        reference_number=f"REF-{refund.id:06d}",
        description=f"Refund posted for Order #{order.id} - {order.order_number}",
        currency=refund.currency or order.currency or "OMR",
        country_code=cc,
        lines=lines,
    )
    
    result = gl.create_journal_entry(db, entry_data)
    
    # Update refund status
    refund.status = "posted"
    refund.processed_at = _utcnow()
    refund.performed_by = approved_by
    db.commit()
    
    # Create supplier deduction record if applicable
    if supplier_deduction > 0 and order.supplier_id:
        _create_supplier_deduction(db, order, supplier_deduction, refund.id, cc)
    
    _log_refund(db, "refund_posted", refund_id, {
        "order_id": order.id,
        "customer_refund": float(customer_refund),
        "commission_reversal": float(commission_reversal),
        "vat_adjustment": float(vat_adjustment),
        "supplier_deduction": float(supplier_deduction),
        "journal_entry_id": result.id,
    }, cc)
    
    return {
        "status": "posted",
        "refund_id": refund_id,
        "journal_entry_id": result.id,
        "customer_refund": float(customer_refund),
        "commission_reversal": float(commission_reversal),
        "vat_adjustment": float(vat_adjustment),
        "supplier_deduction": float(supplier_deduction),
    }


def _create_supplier_deduction(
    db: Session,
    order: Order,
    amount: Decimal,
    refund_id: int,
    country_code: str = None,
):
    """Create a negative supplier settlement for the refund deduction."""
    settlement = SupplierSettlement(
        supplier_id=order.supplier_id,
        order_id=order.id,
        gross_amount=Decimal("0"),
        commission_amount=Decimal("0"),
        net_amount=-amount,  # Negative = deduction
        status="deducted",
        currency=order.currency or "OMR",
        country_code=country_code,
    )
    db.add(settlement)
    db.flush()
    
    # Link refund to settlement
    refund = db.query(RefundLedger).get(refund_id)
    if refund:
        refund.ledger_id = settlement.id


def _log_refund(db: Session, kind: str, entity_id: int, detail: dict, country_code: str = None):
    """Log refund posting activity."""
    try:
        db.add(FinanceAutomationLog(
            kind=kind,
            records_processed=1,
            records_changed=1,
            detail={**detail, "entity_id": entity_id},
            country_code=country_code,
        ))
        db.add(FinanceAuditLog(
            action="journal_post",
            entity_type="refund",
            entity_id=entity_id,
            detail=detail,
            country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("Refund log failed: %s", e)
        db.rollback()

# === MERGED from admin_treasury_payments_service.py ===

"""
Admin Payout Approval Router
=============================
Endpoints for the Admin Payout Approval Dashboard — lists all pending payouts
and batches with supplier/logistics context, and provides an approve/reject/dispatch
workflow.

Routes (mounted at /admin/payout-approval):
  GET  /pending                       → pending payouts + batches with enrichment
  POST /payouts/{payout_id}/approve   → approve an individual (unbatched) payout
  POST /payouts/{payout_id}/reject    → reject an individual payout
  POST /batches/{batch_id}/approve    → approve a batch (draft→approved)
  POST /batches/{batch_id}/reject     → reject a batch
  POST /batches/{batch_id}/dispatch   → mark batch + its payouts as paid

Read/serialization helpers live here (routers -> models reads are permitted for
enrichment); all session writes are delegated to
``controllers.treasury.payout_approval_controller``.
"""
from decimal import Decimal
from typing import Any, cast
from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import SupplierSettlement
from domains.logistics.models.logistics import LogisticsPartner
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.models.payments import Payout
from infrastructure.utils.dependencies import require_admin
from domains.finance.ports import approve_payout
from domains.finance.ports import reject_payout
from domains.finance.ports import approve_batch
from domains.finance.ports import reject_batch
from domains.finance.ports import dispatch_batch

class ActionRequest(BaseModel):
    notes: str | None = None

def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
    return {'id': cast(int, item.id), 'entity_type': cast(str, item.entity_type), 'entity_id': cast(int, item.entity_id), 'amount': float(cast(Decimal, item.amount or 0)), 'currency': cast(str | None, item.currency) or 'OMR', 'reference': cast(str | None, item.reference), 'status': cast(str | None, item.status) or ''}

def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
    return {'id': cast(int, batch.id), 'batch_number': cast(str, batch.batch_number), 'country_code': cast(str, batch.country_code), 'total_amount': float(cast(Decimal, batch.total_amount or 0)), 'item_count': cast(int, batch.item_count or 0), 'status': cast(str, batch.status), 'notes': cast(str | None, batch.notes), 'created_at': cast(Any, batch.created_at).isoformat() if getattr(batch, 'created_at', None) else None, 'items': [_serialize_batch_item(item) for item in batch.items or []]}

def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Return paginated batches in draft/pending status with enriched items."""
    query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(PayoutBatch.status.in_(['draft', 'pending']))
    total = query.count()
    batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    result = []
    for batch in batches:
        enriched_items = _enrich_batch_items(batch, db)
        s = _serialize_batch(batch)
        s['items'] = enriched_items
        result.append(s)
    return (result, total)

def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    """Return {entity_id: display_name} for supplier IDs."""
    if not entity_ids:
        return {}
    users = db.query(User).filter(User.id.in_(entity_ids)).all()
    return {cast(int, u.id): cast(str, u.username or u.email or f'Supplier #{u.id}') for u in users}

def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    """Return {entity_id: display_name} for logistics partner IDs."""
    if not entity_ids:
        return {}
    partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
    return {cast(int, p.id): cast(str, p.name or f'Partner #{p.id}') for p in partners}

def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
    """Return batch items with resolved entity_name fields."""
    items = list(batch.items or [])
    supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == 'supplier'}
    logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == 'logistics'}
    supplier_names = _resolve_supplier_names(supplier_ids, db)
    logistics_names = _resolve_logistics_names(logistics_ids, db)
    enriched = []
    for item in items:
        e = _serialize_batch_item(item)
        eid = cast(int, item.entity_id)
        etype = cast(str, item.entity_type)
        if etype == 'supplier':
            e['entity_name'] = supplier_names.get(eid, f'Supplier #{eid}')
        elif etype == 'logistics':
            e['entity_name'] = logistics_names.get(eid, f'Partner #{eid}')
        else:
            e['entity_name'] = f'#{eid}'
        enriched.append(e)
    return enriched

def _serialize_payout(p: Payout) -> dict[str, Any]:
    return {'id': cast(int, p.id), 'supplier_id': cast(int | None, p.supplier_id), 'order_id': cast(int | None, p.order_id), 'amount': float(cast(Decimal, p.amount or 0)), 'currency': cast(str | None, p.currency) or 'OMR', 'method': cast(str | None, p.method) or '', 'status': cast(str | None, p.status) or '', 'reference': cast(str | None, p.reference), 'notes': cast(str | None, p.notes), 'country_code': cast(str | None, p.country_code) or '', 'created_at': cast(Any, p.created_at).isoformat() if getattr(p, 'created_at', None) else None, 'processed_at': cast(Any, p.processed_at).isoformat() if getattr(p, 'processed_at', None) else None}

def _load_unbatched_payouts(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Return paginated individual Payout records with supplier names."""
    query = db.query(Payout).filter(Payout.status.in_(['pending', 'draft']))
    total = query.count()
    payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
    supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}
    result = []
    for payout in payouts:
        s = _serialize_payout(payout)
        sid = cast(int | None, payout.supplier_id)
        s['supplier_name'] = supplier_names.get(cast(int, sid), f'Supplier #{sid}') if sid else None
        result.append(s)
    return (result, total)

def get_pending_payouts(page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100), current_admin: User=Depends(require_admin), db: Session=Depends(get_db)) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review.

    Pagination is applied independently to batches and unbatched payouts.
    """
    (batches, batch_total) = _load_pending_batches_with_items(db, page, page_size)
    (unbatched, payout_total) = _load_unbatched_payouts(db, page, page_size)
    logistics_payout_q = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.status.in_(['pending', 'draft']))
    logistics_payout_total = logistics_payout_q.count()
    logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
    logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}
    unbatched_logistics = []
    for lp in logistics_payouts:
        pid = cast(int | None, lp.partner_id)
        unbatched_logistics.append({'id': cast(int, lp.id), 'partner_id': pid, 'partner_name': logistics_names.get(cast(int, pid), f'Partner #{pid}') if pid else None, 'amount': float(cast(Decimal, lp.amount or 0)), 'currency': cast(str | None, lp.currency) or 'OMR', 'status': cast(str | None, lp.status) or '', 'reference': cast(str | None, lp.reference), 'notes': cast(str | None, lp.notes), 'created_at': cast(Any, lp.created_at).isoformat() if getattr(lp, 'created_at', None) else None})
    total_amount = sum((b['total_amount'] for b in batches))
    total_items = sum((b['item_count'] for b in batches))
    return {'pending_batches': batches, 'unbatched_payouts': unbatched, 'unbatched_logistics_payouts': unbatched_logistics, 'summary': {'total_batches': batch_total, 'total_amount': round(total_amount, 2), 'total_items': total_items, 'pending_payouts_count': payout_total, 'pending_logistics_payouts_count': logistics_payout_total}, 'pagination': {'page': page, 'page_size': page_size}}

# === MERGED from admin_treasury_status_service.py ===

"""Admin payouts router."""
from fastapi import Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.payments import Payout
from infrastructure.database.schemas import PayoutCreate, PayoutOut
from infrastructure.utils.dependencies import require_admin
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import set_rls_context, clear_rls_context
from infrastructure.utils.datetime_utils import utcnow
from domains.audit.services.logs.audit_service import audit_log, AuditAction
from domains.finance.ports import get_background_job_status
from domains.finance.ports import start_auto_payout_background_job
from domains.finance.ports import stop_auto_payout_background_job
from domains.finance.ports import run_auto_payout_sweep
from domains.finance.ports import run_auto_logistics_payout_sweep

class PayoutVerifyRequest(BaseModel):
    note: str | None = None
    bank_reference: str | None = None
    transfer_date: str | None = None
    status: str = 'verified'

def list_payouts(country_code: str=Path(..., description='ISO country code'), _: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}
    finally:
        clear_rls_context()

def create_payout(country_code: str=Path(..., description='ISO country code'), payload: PayoutCreate=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        model_cols = {c.name for c in Payout.__table__.columns}
        data = {k: v for (k, v) in payload.model_dump().items() if k in model_cols}
        p = Payout(**data, country_code=country_code.upper())
        db.add(p)
        db.commit()
        db.refresh(p)
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=p.id, details={'amount': str(p.amount) if p.amount else None, 'method': p.method})
        return p
    finally:
        clear_rls_context()

def list_pending_payouts(current_admin: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    """List all pending payouts (RLS-scoped if context is set)."""
    q = db.query(Payout).filter(Payout.status == 'pending')
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}

def list_pending_payouts_by_country(country_code: str=Path(..., description='ISO country code'), current_admin: User=Depends(require_admin), db: Session=Depends(get_db), page: int=Query(1, ge=1), page_size: int=Query(20, ge=1, le=100)):
    """List pending payouts for a specific country."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Payout).filter(Payout.status == 'pending', Payout.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {'data': rows, 'total': total, 'page': page, 'page_size': page_size}
    finally:
        clear_rls_context()

def verify_payout(country_code: str=Path(..., description='ISO country code'), payout_id: int=Path(...), payload: PayoutVerifyRequest=None, current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    """Verify a payout."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404, 'Payout not found')
        p.status = payload.status if payload and payload.status else 'verified'
        p.processed_at = utcnow()
        if payload:
            if payload.note:
                p.notes = payload.note
            if payload.bank_reference:
                p.reference = payload.bank_reference
        db.commit()
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': p.status, 'reference': p.reference, 'notes': p.notes})
        return {'verified': True, 'payout_id': payout_id}
    finally:
        clear_rls_context()

def process_payout(country_code: str=Path(..., description='ISO country code'), payout_id: int=Path(...), current_admin: User=Depends(require_admin), db: Session=Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == country_code.upper()).first()
        if not p:
            raise HTTPException(404)
        p.status = 'paid'
        p.processed_at = utcnow()
        db.commit()
        audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=current_admin.id, username=current_admin.username, user_role='admin', resource_type='payout', resource_id=payout_id, details={'status': 'paid'})
        return {'message': 'Payout processed'}
    finally:
        clear_rls_context()

def get_background_job_status_endpoint(db: Session=Depends(get_db), current_admin: User=Depends(require_admin)):
    """Return the current state of the auto-payout background job:
    is_running, last_run_at, last_run_status, last_error, total counts,
    and recent FinanceAutomationLog entries.
    """
    status = _get_bg_status()
    history = db.query(FinanceAutomationLog).filter(FinanceAutomationLog.kind.in_(['auto_payout', 'auto_logistics_payout'])).order_by(FinanceAutomationLog.created_at.desc()).limit(20).all()
    return {'status': status, 'history': [{'id': h.id, 'kind': h.kind, 'records_processed': h.records_processed, 'records_changed': h.records_changed, 'detail': h.detail, 'created_at': h.created_at.isoformat() if h.created_at else None} for h in history]}
