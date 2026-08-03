"""
Cross-Border Session Tracker
Tracks customers shopping in different countries.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from data.db import get_db_context
from data.models import CountryConfig

logger = logging.getLogger(__name__)


class CrossBorderTracker:
    """Tracks customer cross-border shopping sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    def track_session(
        self, 
        session_id: str, 
        ip_address: str, 
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Track a customer session with country detection."""
        from services.cross_border_service import GeoDetectionService
        
        country_code = GeoDetectionService.detect_country_from_ip(ip_address)
        if not country_code:
            return None
        
        previous = self._sessions.get(session_id)
        now = datetime.utcnow()
        
        change_info = {
            "session_id": session_id,
            "previous_country": previous.get("country_code") if previous else None,
            "new_country": country_code,
            "ip_address": ip_address,
            "user_id": user_id,
            "timestamp": now.isoformat(),
            "is_new_session": previous is None,
            "crossed_border": previous is not None and previous.get("country_code") != country_code,
        }
        
        self._sessions[session_id] = {
            "country_code": country_code,
            "ip_address": ip_address,
            "user_id": user_id,
            "first_seen": previous.get("first_seen", change_info["timestamp"]) if previous else change_info["timestamp"],
            "last_seen": change_info["timestamp"],
        }
        
        return change_info
    
    def get_session_country(self, session_id: str) -> Optional[str]:
        """Get the current country for a session."""
        session = self._sessions.get(session_id)
        return session.get("country_code") if session else None
    
    def clear_session(self, session_id: str):
        """Clear a session."""
        self._sessions.pop(session_id, None)
    
    def get_cross_border_stats(self, country_code: str) -> Dict[str, Any]:
        """Get cross-border shopping statistics for a country."""
        stats = {"total_sessions": 0, "crossings": 0, "unique_users": set()}
        
        for session in self._sessions.values():
            if session.get("country_code") == country_code:
                stats["total_sessions"] += 1
                if session.get("user_id"):
                    stats["unique_users"].add(session["user_id"])
        
        return {
            "total_sessions": stats["total_sessions"],
            "unique_users": len(stats["unique_users"]),
        }


_cross_border_tracker = CrossBorderTracker()


def get_cross_border_tracker() -> CrossBorderTracker:
    return _cross_border_tracker
