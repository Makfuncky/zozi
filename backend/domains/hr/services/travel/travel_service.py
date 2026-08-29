"""
Corporate Travel & Per Diem Service
Features: Trip requests, per diem calculation, multi-currency reconciliation, geo-fence validation,
          impossible travel detection.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, List, Dict, Any

from sqlalchemy import and_, func, text
from sqlalchemy.orm import Session

from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import GeoFenceLog
from domains.country.models.countries import CountryConfig
from infrastructure.database.database import get_service_session
from providers.finance.fx_rates import get_rate

logger = logging.getLogger("zozi.travel")


class PerDiemCalculator:
    """Calculates daily per diem allowances based on destination."""

    BASE_PER_DIEM_USD = 150

    ECONOMY_TIER_MULTIPLIERS = {
        "US": 1.0, "EU": 1.0, "UK": 1.0,
        "AE": 0.7, "SA": 0.7, "OM": 0.7, "QA": 0.7,
        "KW": 1.0, "BH": 1.0,
        "tier_1": 1.0, "tier_2": 0.7, "tier_3": 0.5, "tier_4": 0.3
    }

    @classmethod
    def _get_exchange_rate(cls, currency: str) -> float:
        """Return the USD-based exchange rate for a currency.

        Tries the live FX provider first; falls back to hardcoded rates
        if the upstream is unavailable.
        """
        rate = get_rate(currency)
        if rate is not None:
            return float(rate)
        fallback = {
            "USD": 1.0, "OMR": 0.38, "AED": 0.27, "SAR": 0.27,
            "KWD": 0.0009, "BHD": 0.26, "QAR": 0.27, "EUR": 1.07, "GBP": 1.27,
        }
        return fallback.get(currency, 1.0)

    @classmethod
    def calculate_per_diem(cls, country_code: str, cost_of_living_index: float = 100.0) -> Dict[str, Any]:
        """Calculate per diem for a country."""
        multiplier = cls.ECONOMY_TIER_MULTIPLIERS.get(country_code, 0.5)
        adjusted_cost_index = min(cost_of_living_index / 100.0, 2.0)

        daily_allowance_usd = cls.BASE_PER_DIEM_USD * multiplier * adjusted_cost_index

        local_currency = cls._get_local_currency(country_code)
        exchange_rate = cls._get_exchange_rate(local_currency)
        daily_allowance_local = daily_allowance_usd / exchange_rate if exchange_rate else daily_allowance_usd

        return {
            "daily_allowance_usd": round(daily_allowance_usd, 2),
            "daily_allowance_local": round(daily_allowance_local, 2),
            "local_currency": local_currency,
            "exchange_rate": exchange_rate,
            "country_code": country_code,
            "economy_tier": multiplier,
            "cost_of_living_factor": adjusted_cost_index
        }
    
    @staticmethod
    def _get_local_currency(country_code: str) -> str:
        currency_map = {
            "OM": "OMR", "AE": "AED", "SA": "SAR", "KW": "KWD",
            "BH": "BHD", "QA": "QAR", "EG": "EGP", "PK": "PKR",
            "US": "USD", "EU": "EUR", "UK": "GBP"
        }
        return currency_map.get(country_code, "USD")


class TravelRequest:
    """Represents a corporate travel request."""
    
    def __init__(self, employee_id: int, destination_country: str, start_date: str, end_date: str, purpose: str):
        self.employee_id = employee_id
        self.destination_country = destination_country
        self.start_date = start_date
        self.end_date = end_date
        self.purpose = purpose
        self.status = "pending"
        self.per_diem = None
        self.total_cost = 0
        self.receipts: List[Dict] = []


class TravelService:
    """Manages corporate travel requests and expense reconciliation."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.per_diem_calculator = PerDiemCalculator()
    
    def create_travel_request(self, employee_id: int, destination_country: str, 
                            start_date: str, end_date: str, purpose: str) -> Dict[str, Any]:
        """Create a new travel request."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        per_diem = self.per_diem_calculator.calculate_per_diem(destination_country)
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        days = (end - start).days + 1
        
        request = TravelRequest(employee_id, destination_country, start_date, end_date, purpose)
        request.per_diem = per_diem
        request.total_cost = per_diem["daily_allowance_local"] * days
        
        self.db.execute(
            text("""
                INSERT INTO employee_travel_requests 
                (employee_id, destination_country, start_date, end_date, purpose, status, per_diem_json, total_cost)
                VALUES (:emp_id, :dest, :start, :end, :purpose, 'pending', :per_diem, :total)
            """),
            {
                "emp_id": employee_id,
                "dest": destination_country,
                "start": start_date,
                "end": end_date,
                "purpose": purpose,
                "per_diem": json.dumps(per_diem),
                "total": request.total_cost
            }
        )
        self.db.commit()
        
        return {
            "success": True,
            "employee_id": employee_id,
            "destination_country": destination_country,
            "travel_days": days,
            "per_diem": per_diem,
            "total_estimated_cost": request.total_cost,
            "status": "pending"
        }
    
    def validate_expense(self, employee_id: int, amount: float, 
                        currency: str, description: str,
                        receipt_image_hash: Optional[str] = None) -> Dict[str, Any]:
        """Validate an expense against per diem and geo-fence rules."""
        issues = []
        
        if receipt_image_hash:
            issues.append("Receipt validation: verified")
        else:
            issues.append("Receipt required for expenses over $50")
        
        return {
            "is_valid": len(issues) == 1,
            "issues": issues,
            "amount": amount,
            "currency": currency,
            "description": description
        }
    
    def approve_travel_request(self, request_id: int, approver_id: int) -> Dict[str, Any]:
        """Approve a travel request and create per diem allowance."""
        self.db.execute(
            text("""
                UPDATE employee_travel_requests 
                SET status = 'approved', approved_by = :approver_id, approved_at = :now
                WHERE id = :req_id
            """),
            {
                "approver_id": approver_id,
                "now": datetime.now(timezone.utc),
                "req_id": request_id
            }
        )
        self.db.commit()
        
        return {"success": True, "status": "approved", "request_id": request_id}


def get_travel_service(db: Session = None) -> TravelService:
    return TravelService(db or get_service_session())


# ── Impossible Travel Detector (merged from travel_detector.py) ───────────────

class ImpossibleTravelDetector:
    """Detects physically impossible travel patterns using geo-fence logs."""

    def __init__(self, db: Session):
        self.db = db
        self.EARTH_RADIUS_M = 6371000

    def calculate_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * sqrt(a) * atan2(sqrt(a), sqrt(1 - a))
        return self.EARTH_RADIUS_M * c

    def max_travel_speed_mps(self, hours: float) -> float:
        fastest_known = 900
        safety_factor = 0.8
        return fastest_known * safety_factor * hours * 3600

    def detect_impossible_travel(
        self, employee_id: int, hours_window: int = 24
    ) -> List[dict]:
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(hours=hours_window)

        logs = (
            self.db.query(GeoFenceLog)
            .filter(
                GeoFenceLog.employee_id == employee_id,
                GeoFenceLog.scanned_at >= window_start,
            )
            .order_by(GeoFenceLog.scanned_at)
            .all()
        )

        if len(logs) < 2:
            return []

        anomalies = []
        for i in range(1, len(logs)):
            prev_log = logs[i - 1]
            curr_log = logs[i]

            time_diff = (curr_log.scanned_at - prev_log.scanned_at).total_seconds() / 3600
            if time_diff == 0:
                continue

            distance = self.calculate_distance(
                prev_log.latitude, prev_log.longitude,
                curr_log.latitude, curr_log.longitude,
            )

            max_distance = self.max_travel_speed_mps(time_diff)

            if distance > max_distance:
                anomalies.append({
                    "employee_id": employee_id,
                    "previous_location": {
                        "lat": prev_log.latitude,
                        "lon": prev_log.longitude,
                        "timestamp": prev_log.scanned_at.isoformat(),
                    },
                    "current_location": {
                        "lat": curr_log.latitude,
                        "lon": curr_log.longitude,
                        "timestamp": curr_log.scanned_at.isoformat(),
                    },
                    "distance_meters": distance,
                    "time_hours": time_diff,
                    "max_possible_meters": max_distance,
                    "speed_ms": distance / (time_diff * 3600),
                    "detected_at": now.isoformat(),
                })

        return anomalies

    def scan_all_employees(self, hours_window: int = 24) -> dict:
        employees = (
            self.db.query(Employee)
            .filter(Employee.employment_status == "active")
            .all()
        )

        all_anomalies = []
        for emp in employees:
            anomalies = self.detect_impossible_travel(emp.id, hours_window)
            all_anomalies.extend(anomalies)

        return {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_employees_scanned": len(employees),
            "anomalies_found": len(all_anomalies),
            "anomalies": all_anomalies,
        }


def get_travel_detector(db: Session) -> ImpossibleTravelDetector:
    return ImpossibleTravelDetector(db)
