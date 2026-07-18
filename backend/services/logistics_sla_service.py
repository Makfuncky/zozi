"""
Logistics SLA Service
Calculates delivery ETAs considering public holidays and working days.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from db.database import get_db_context
from models import CountryConfig

logger = logging.getLogger(__name__)


class LogisticsSLAService:
    """Manages SLA calculations with holiday awareness."""
    
    @staticmethod
    def get_public_holidays(country_code: str) -> List[Dict[str, Any]]:
        """Get public holidays for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper(),
                CountryConfig.is_active == True,
            ).first()
            
            if not config or not config.public_holidays_json:
                return []
            
            try:
                holidays = json.loads(config.public_holidays_json) if isinstance(config.public_holidays_json, str) else config.public_holidays_json
                return holidays if isinstance(holidays, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
    
    @staticmethod
    def get_working_days(country_code: str) -> List[str]:
        """Get working days for a country (default: Mon-Sat)."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper(),
                CountryConfig.is_active == True,
            ).first()
            
            if config and config.working_days_json:
                try:
                    days = json.loads(config.working_days_json) if isinstance(config.working_days_json, str) else config.working_days_json
                    return days if isinstance(days, list) else []
                except (json.JSONDecodeError, TypeError):
                    pass
            
            return ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    
    @staticmethod
    def is_holiday(date: datetime, holidays: List[Dict[str, Any]]) -> bool:
        """Check if a date is a holiday."""
        date_str = date.strftime("%Y-%m-%d")
        for holiday in holidays:
            if holiday.get("date") == date_str:
                return True
        return False
    
    @staticmethod
    def add_business_days(
        start_date: datetime,
        days: int,
        country_code: str,
        exclude_holidays: bool = True
    ) -> datetime:
        """Add business days excluding weekends and holidays."""
        holidays = LogisticsSLAService.get_public_holidays(country_code) if exclude_holidays else []
        working_days = LogisticsSLAService.get_working_days(country_code)
        
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        
        current = start_date
        added = 0
        max_iterations = days * 14
        iterations = 0
        
        while added < days and iterations < max_iterations:
            iterations += 1
            current = current + timedelta(days=1)
            day_name = day_names[current.weekday()]
            
            if day_name in working_days:
                if exclude_holidays and LogisticsSLAService.is_holiday(current, holidays):
                    continue
                added += 1
        
        return current
    
    @staticmethod
    def calculate_eta(
        order_date: datetime,
        transit_days: int,
        country_code: str,
        cutoff_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate estimated delivery date."""
        cutoff = datetime.strptime(cutoff_time, "%H:%M") if cutoff_time else datetime.strptime("17:00", "%H:%M")
        now = datetime.now()
        
        if now.time() >= cutoff.time():
            order_date = order_date + timedelta(days=1)
        
        delivery_date = LogisticsSLAService.add_business_days(
            order_date,
            transit_days,
            country_code
        )
        
        return {
            "estimated_delivery_date": delivery_date.strftime("%Y-%m-%d"),
            "transit_days": transit_days,
            "cutoff_time": cutoff_time or "17:00",
            "holidays_excluded": LogisticsSLAService.get_public_holidays(country_code)
        }


def run_treasury_sync():
    """Cron job to sync treasury settings from CountryConfig."""
    from services.treasury_service import TreasuryService
    
    with get_db_context() as db:
        countries = db.query(CountryConfig).filter(CountryConfig.is_active == True).all()
        
        for country in countries:
            settings = TreasuryService.get_payout_settings(country.code)
            logger.info(f"Treasury sync for {country.code}: hold_days={settings['settlement_hold_days']}, min_payout={settings['minimum_payout_amount']}")
