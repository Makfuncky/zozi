"""Cross-Border Detection Middleware for Customer Sessions."""
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import Request, HTTPException


class CrossBorderDetectionMiddleware:
    """Detects and tracks customer sessions crossing country boundaries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_cross_border_session(
        self,
        user_id: int,
        source_country: str,
        target_country: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Optional[Dict]:
        """Detect if a user session crosses country boundaries."""
        if not source_country or not target_country:
            return None
        
        source = source_country.upper()
        target = target_country.upper()
        
        if source == target:
            return None
        
        from data.models import CountryConfig, CrossCountryCustomerSession
        
        existing = self.db.query(CrossCountryCustomerSession).filter(
            CrossCountryCustomerSession.user_id == user_id,
            CrossCountryCustomerSession.source_country_code == source,
            CrossCountryCustomerSession.target_country_code == target
        ).first()
        
        if existing:
            existing.session_count += 1
            existing.last_seen_at = datetime.now(timezone.utc)
            self.db.commit()
            return {"type": "session_update", "id": existing.id}
        
        new_session = CrossCountryCustomerSession(
            user_id=user_id,
            source_country_code=source,
            target_country_code=target,
            ip_address=ip_address,
            user_agent=user_agent,
            session_data=json.dumps({
                "first_interaction": "product_view",
                "countries_involved": [source, target]
            }) if source_country and target_country else None
        )
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return {"type": "new_session", "id": new_session.id}
    
    def get_cross_border_summary(self, country_code: str) -> Dict:
        """Get cross-border activity summary for a country."""
        from data.models import CrossCountryCustomerSession, CountryConfig
        
        country = self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()
        
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        
        sessions_to = self.db.query(CrossCountryCustomerSession).filter(
            CrossCountryCustomerSession.target_country_code == country_code.upper()
        ).all()
        
        sessions_from = self.db.query(CrossCountryCustomerSession).filter(
            CrossCountryCustomerSession.source_country_code == country_code.upper()
        ).all()
        
        return {
            "country_code": country_code.upper(),
            "incoming_sessions": len(sessions_to),
            "outgoing_sessions": len(sessions_from),
            "total_cross_border_users": len(set(s.user_id for s in sessions_to + sessions_from)),
            "conversions": sum(1 for s in sessions_to if s.conversion),
            "conversion_rate": sum(1 for s in sessions_to if s.conversion) / len(sessions_to) if sessions_to else 0
        }


class LocalizationService:
    """Handles localization and internationalization for countries."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_localized_content(self, country_code: str, locale: str = None) -> Dict:
        """Get localized content for a country."""
        from data.models import CountryConfig, CountryCommunicationTemplate
        
        country = self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()
        
        if not country:
            return {}
        
        templates = self.db.query(CountryCommunicationTemplate).filter(
            CountryCommunicationTemplate.country_code == country_code.upper()
        ).all()
        
        return {
            "country": {
                "name": country.name,
                "currency": country.currency,
                "language": country.language,
                "date_format": country.date_format,
                "measurement_system": country.measurement_system,
            },
            "templates": [
                {"key": t.template_key, "subject": t.subject, "body": t.body}
                for t in templates
            ]
        }
    
    def format_currency(self, amount: float, country_code: str) -> str:
        """Format currency for a specific country."""
        from data.models import CountryConfig
        
        country = self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()
        
        if not country:
            return f"{amount:.2f}"
        
        symbol = country.currency_symbol or country.currency
        return f"{symbol} {amount:,.2f}"
    
    def format_date(self, date, country_code: str) -> str:
        """Format date according to country's locale."""
        from data.models import CountryConfig
        
        country = self.db.query(CountryConfig).filter(
            CountryConfig.code == country_code.upper()
        ).first()
        
        if not country or not country.date_format:
            return date.isoformat() if date else ""
        
        fmt = country.date_format
        if fmt == "DD/MM/YYYY":
            return date.strftime("%d/%m/%Y") if date else ""
        elif fmt == "MM/DD/YYYY":
            return date.strftime("%m/%d/%Y") if date else ""
        elif fmt == "YYYY-MM-DD":
            return date.strftime("%Y-%m-%d") if date else ""
        
        return date.isoformat() if date else ""

