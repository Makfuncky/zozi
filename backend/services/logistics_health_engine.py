"""
Logistics Partner Health Engine - Calculates performance scores for logistics partners.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import LogisticsPartnerProfile, Shipment, LogisticsPartnerPayout


class LogisticsHealthEngine:
    """Calculate logistics partner health scores based on performance metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_health_score(self, partner_id: int, country_code: str = None) -> Dict[str, Any]:
        """Calculate comprehensive health score for a logistics partner."""
        profile = self.db.query(LogisticsPartnerProfile).filter(
            LogisticsPartnerProfile.id == partner_id
        ).first()
        
        if not profile:
            return {"error": "Logistics partner not found"}
        
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        shipments = self._get_shipments(partner_id, country_code, thirty_days_ago, now)
        
        acceptance_rate = self._calculate_acceptance_rate(shipments)
        late_rate = self._calculate_late_rate(shipments)
        failed_rate = self._calculate_failed_rate(shipments)
        cod_accuracy = self._calculate_cod_accuracy(shipments)
        dispute_rate = self._calculate_dispute_rate(shipments)
        customer_rating = self._get_average_rating(profile)
        coverage_score = self._calculate_coverage_score(profile)
        capacity_score = self._calculate_capacity_score(profile)
        
        total_score = (
            acceptance_rate * 0.15 +
            (1 - late_rate) * 0.20 +
            (1 - failed_rate) * 0.15 +
            cod_accuracy * 0.15 +
            (1 - dispute_rate) * 0.10 +
            customer_rating * 0.15 +
            coverage_score * 0.05 +
            capacity_score * 0.05
        )
        
        return {
            "partner_id": partner_id,
            "trust_score": round(total_score * 100, 2),
            "metrics": {
                "acceptance_rate": round(acceptance_rate * 100, 2),
                "late_rate": round(late_rate * 100, 2),
                "failed_rate": round(failed_rate * 100, 2),
                "cod_accuracy": round(cod_accuracy * 100, 2),
                "dispute_rate": round(dispute_rate * 100, 2),
                "customer_rating": round(customer_rating * 100, 2),
                "coverage_score": round(coverage_score * 100, 2),
                "capacity_score": round(capacity_score * 100, 2),
            },
            "status": self._get_status(total_score),
            "last_calculated": now.isoformat(),
        }
    
    def _get_shipments(self, partner_id: int, country_code: Optional[str], start: datetime, end: datetime):
        query = self.db.query(Shipment).filter(
            Shipment.assigned_partner_id == partner_id,
            Shipment.created_at >= start,
            Shipment.created_at <= end,
        )
        if country_code:
            query = query.filter(Shipment.country_code == country_code)
        return query.all()
    
    def _calculate_acceptance_rate(self, shipments) -> float:
        if not shipments:
            return 0.5
        accepted = sum(1 for s in shipments if s.status != 'rejected')
        return accepted / len(shipments)
    
    def _calculate_late_rate(self, shipments) -> float:
        if not shipments:
            return 0.0
        late = sum(1 for s in shipments if hasattr(s, 'is_late') and s.is_late)
        return late / len(shipments)
    
    def _calculate_failed_rate(self, shipments) -> float:
        if not shipments:
            return 0.0
        failed = sum(1 for s in shipments if s.status == 'failed')
        return failed / len(shipments)
    
    def _calculate_cod_accuracy(self, shipments) -> float:
        cod_shipments = [s for s in shipments if hasattr(s, 'payment_method') and s.payment_method == 'cod']
        if not cod_shipments:
            return 1.0
        accurate = sum(1 for s in cod_shipments if s.status == 'delivered')
        return accurate / len(cod_shipments)
    
    def _calculate_dispute_rate(self, shipments) -> float:
        if not shipments:
            return 0.0
        from models import LogisticsFraudIndicator
        disputes = self.db.query(LogisticsFraudIndicator).filter(
            LogisticsFraudIndicator.shipment_id.in_([s.id for s in shipments])
        ).count()
        return disputes / len(shipments) if shipments else 0.0
    
    def _get_average_rating(self, profile) -> float:
        rating = getattr(profile, "average_rating", None)
        if not rating:
            return 0.5
        return float(rating) / 5.0
    
    def _calculate_coverage_score(self, profile) -> float:
        base_coverage = getattr(profile, "coverage_regions", None) or ""
        covered_cities = len(base_coverage.split(",")) if base_coverage else 0
        return min(covered_cities / 50, 1.0)
    
    def _calculate_capacity_score(self, profile) -> float:
        capacity = getattr(profile, "vehicle_capacity", None)
        if not capacity:
            return 0.5
        return min(capacity / 100, 1.0)
    
    def _get_status(self, score: float) -> str:
        if score >= 0.8:
            return "excellent"
        elif score >= 0.6:
            return "good"
        elif score >= 0.4:
            return "fair"
        return "poor"


def get_logistics_health_engine(db: Session) -> LogisticsHealthEngine:
    return LogisticsHealthEngine(db)
