"""
Supplier Health Engine - Calculates trust scores and health metrics for suppliers.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from data.models import SupplierProfile, Order, SupplierDispute, SupplierCountryCommission


class SupplierHealthEngine:
    """Calculate supplier health scores based on multiple metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_health_score(self, supplier_id: int, country_code: str = None) -> Dict[str, Any]:
        """Calculate comprehensive health score for a supplier."""
        profile = self.db.query(SupplierProfile).filter(
            SupplierProfile.id == supplier_id
        ).first()
        
        if not profile:
            return {"error": "Supplier not found"}
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        orders = self._get_orders(supplier_id, country_code, thirty_days_ago, now)
        disputes = self._get_disputes(supplier_id, thirty_days_ago, now)
        
        response_time_score = self._calculate_response_time_score(orders)
        cancellation_rate = self._calculate_cancellation_rate(orders)
        return_rate = self._calculate_return_rate(orders)
        customer_rating = self._get_average_rating(profile)
        late_shipment_rate = self._calculate_late_shipment_rate(orders)
        dispute_rate = self._calculate_dispute_rate(orders, disputes)
        growth_score = self._calculate_growth_score(orders)
        kyc_score = self._calculate_kyc_score(profile)
        
        total_score = (
            response_time_score * 0.15 +
            (1 - cancellation_rate) * 0.10 +
            (1 - return_rate) * 0.10 +
            customer_rating * 0.20 +
            (1 - late_shipment_rate) * 0.15 +
            (1 - dispute_rate) * 0.15 +
            growth_score * 0.10 +
            kyc_score * 0.05
        )
        
        return {
            "supplier_id": supplier_id,
            "trust_score": round(total_score * 100, 2),
            "metrics": {
                "response_time_score": round(response_time_score * 100, 2),
                "cancellation_rate": round(cancellation_rate * 100, 2),
                "return_rate": round(return_rate * 100, 2),
                "customer_rating": round(customer_rating * 100, 2),
                "late_shipment_rate": round(late_shipment_rate * 100, 2),
                "dispute_rate": round(dispute_rate * 100, 2),
                "growth_score": round(growth_score * 100, 2),
                "kyc_score": round(kyc_score * 100, 2),
            },
            "status": self._get_status(total_score),
            "last_calculated": now.isoformat(),
        }
    
    def _get_orders(self, supplier_id: int, country_code: Optional[str], start: datetime, end: datetime):
        from data.models import OrderItem
        order_ids = [
            r[0]
            for r in self.db.query(OrderItem.order_id)
            .filter(OrderItem.supplier_id == supplier_id)
            .all()
        ]
        if not order_ids:
            return []
        query = self.db.query(Order).filter(
            Order.id.in_(order_ids),
            Order.created_at >= start,
            Order.created_at <= end,
        )
        if country_code:
            query = query.filter(Order.shipping_country == country_code)
        return query.all()
    
    def _get_disputes(self, supplier_id: int, start: datetime, end: datetime):
        return self.db.query(SupplierDispute).filter(
            SupplierDispute.supplier_id == supplier_id,
            SupplierDispute.created_at >= start,
            SupplierDispute.created_at <= end,
        ).all()
    
    def _calculate_response_time_score(self, orders) -> float:
        if not orders:
            return 0.5
        response_times = []
        for o in orders:
            if o.created_at and o.updated_at:
                delta = (o.updated_at - o.created_at).total_seconds() / 3600
                response_times.append(min(delta / 24, 1))
        return sum(response_times) / len(response_times) if response_times else 0.5
    
    def _calculate_cancellation_rate(self, orders) -> float:
        if not orders:
            return 0.0
        cancelled = sum(1 for o in orders if o.status == 'cancelled')
        return cancelled / len(orders)
    
    def _calculate_return_rate(self, orders) -> float:
        if not orders:
            return 0.0
        from data.models import ReturnRequest
        returns = self.db.query(ReturnRequest).filter(
            ReturnRequest.order_id.in_([o.id for o in orders])
        ).count()
        return returns / len(orders) if orders else 0.0
    
    def _get_average_rating(self, profile) -> float:
        rating = getattr(profile, "average_rating", None)
        if not rating:
            return 0.5
        return float(rating) / 5.0
    
    def _calculate_late_shipment_rate(self, orders) -> float:
        if not orders:
            return 0.0
        late = 0
        for o in orders:
            if hasattr(o, 'logistics_status') and o.logistics_status == 'delayed':
                late += 1
        return late / len(orders)
    
    def _calculate_dispute_rate(self, orders, disputes) -> float:
        if not orders:
            return 0.0
        return len(disputes) / len(orders)
    
    def _calculate_growth_score(self, orders) -> float:
        if len(orders) < 2:
            return 0.5
        sorted_orders = sorted(orders, key=lambda x: x.created_at)
        first_half = sorted_orders[:len(sorted_orders)//2]
        second_half = sorted_orders[len(sorted_orders)//2:]
        first_revenue = sum(float(o.total_amount) for o in first_half)
        second_revenue = sum(float(o.total_amount) for o in second_half)
        growth = (second_revenue - first_revenue) / first_revenue if first_revenue > 0 else 0
        return min(max(growth, 0), 1)
    
    def _calculate_kyc_score(self, profile) -> float:
        status = getattr(profile, "verification_status", None)
        if status == 'approved':
            return 1.0
        elif status in ('pending', 'under_review', 'documents_submitted'):
            return 0.5
        return 0.0
    
    def _get_status(self, score: float) -> str:
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        return "poor"


def get_supplier_health_engine(db: Session) -> SupplierHealthEngine:
    return SupplierHealthEngine(db)
