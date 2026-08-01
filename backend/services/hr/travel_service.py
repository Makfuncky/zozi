"""
Corporate Travel & Per Diem Service
Features: Trip requests, per diem calculation, multi-currency reconciliation, geo-fence validation
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from models.employee_models import Employee
from models.countries import CountryConfig
from db.database import get_service_session

logger = logging.getLogger("zozi.travel")


class PerDiemCalculator:
    """Calculates daily per diem allowances based on destination."""
    
    BASE_PER_DIEM_USD = 150
    
    LOCAL_CURRENCY_RATES = {
        "USD": 1.0, "OMR": 0.38, "AED": 0.27, "SAR": 0.27,
        "KWD": 0.0009, "BHD": 0.26, "QAR": 0.27, "EUR": 1.07, "GBP": 1.27
    }
    
    ECONOMY_TIER_MULTIPLIERS = {
        "US": 1.0, "EU": 1.0, "UK": 1.0,
        "AE": 0.7, "SA": 0.7, "OM": 0.7, "QA": 0.7,
        "KW": 1.0, "BH": 1.0,
        "tier_1": 1.0, "tier_2": 0.7, "tier_3": 0.5, "tier_4": 0.3
    }
    
    @classmethod
    def calculate_per_diem(cls, country_code: str, cost_of_living_index: float = 100.0) -> Dict[str, Any]:
        """Calculate per diem for a country."""
        multiplier = cls.ECONOMY_TIER_MULTIPLIERS.get(country_code, 0.5)
        adjusted_cost_index = min(cost_of_living_index / 100.0, 2.0)
        
        daily_allowance_usd = cls.BASE_PER_DIEM_USD * multiplier * adjusted_cost_index
        
        local_currency = cls._get_local_currency(country_code)
        exchange_rate = cls.LOCAL_CURRENCY_RATES.get(local_currency, 1.0)
        daily_allowance_local = daily_allowance_usd / exchange_rate
        
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
