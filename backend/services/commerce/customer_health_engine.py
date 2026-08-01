"""
Customer Health Engine - Calculates trust scores and risk metrics for customers.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from models import User, Order, ReturnRequest


class CustomerHealthEngine:
    """Calculate customer health scores based on behavior metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_health_score(self, user_id: int) -> Dict[str, Any]:
        """Calculate comprehensive health score for a customer."""
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {"error": "Customer not found"}
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        orders = self._get_orders(user_id, thirty_days_ago, now)
        returns = self._get_returns(user_id, thirty_days_ago, now)
        
        lifetime_value = self._calculate_lifetime_value(orders)
        fraud_risk = self._calculate_fraud_risk(user)
        refund_ratio = self._calculate_refund_ratio(orders, returns)
        cod_failure_rate = self._calculate_cod_failure_rate(orders)
        purchase_frequency = self._calculate_purchase_frequency(orders)
        
        total_score = (
            min(lifetime_value / 1000, 1.0) * 0.25 +
            (1 - fraud_risk) * 0.20 +
            (1 - refund_ratio) * 0.20 +
            (1 - cod_failure_rate) * 0.15 +
            min(purchase_frequency / 10, 1.0) * 0.20
        )
        
        return {
            "customer_id": user_id,
            "trust_score": round(total_score * 100, 2),
            "metrics": {
                "lifetime_value": float(lifetime_value),
                "fraud_risk": round(fraud_risk * 100, 2),
                "refund_ratio": round(refund_ratio * 100, 2),
                "cod_failure_rate": round(cod_failure_rate * 100, 2),
                "purchase_frequency": round(purchase_frequency, 2),
            },
            "status": self._get_status(total_score),
            "last_calculated": now.isoformat(),
        }
    
    def _get_orders(self, user_id: int, start: datetime, end: datetime):
        return self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.created_at >= start,
            Order.created_at <= end,
        ).all()
    
    def _get_returns(self, user_id: int, start: datetime, end: datetime):
        order_ids = [o.id for o in self._get_orders(user_id, start, end)]
        return self.db.query(ReturnRequest).filter(
            ReturnRequest.order_id.in_(order_ids)
        ).all()
    
    def _calculate_lifetime_value(self, orders) -> Decimal:
        return sum(Decimal(str(o.total_amount)) for o in orders)
    
    def _calculate_fraud_risk(self, user) -> float:
        risk = 0.0
        if user.email_verified == False:
            risk += 0.3
        if user.phone is None:
            risk += 0.2
        return min(risk, 1.0)
    
    def _calculate_refund_ratio(self, orders, returns) -> float:
        if not orders:
            return 0.0
        return len(returns) / len(orders)
    
    def _calculate_cod_failure_rate(self, orders) -> float:
        cod_orders = [o for o in orders if hasattr(o, 'payment_method') and o.payment_method == 'cod']
        if not cod_orders:
            return 0.0
        failed = sum(1 for o in cod_orders if o.status == 'failed')
        return failed / len(cod_orders)
    
    def _calculate_purchase_frequency(self, orders) -> float:
        if len(orders) < 2:
            return float(len(orders))
        sorted_orders = sorted(orders, key=lambda x: x.created_at)
        days = (sorted_orders[-1].created_at - sorted_orders[0].created_at).days
        return len(orders) / max(days, 1) * 30
    
    def _get_status(self, score: float) -> str:
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        return "at_risk"


def get_customer_health_engine(db: Session) -> CustomerHealthEngine:
    return CustomerHealthEngine(db)
