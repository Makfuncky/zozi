"""
Shared base for cross-border session trackers.

``get_session_country`` and ``clear_session`` are byte-identical between
``services.geography.cross_border_service.CrossBorderTracker`` and
``services.geography.cross_border_tracker.CrossBorderTracker`` and live
here so the logic is defined once. The two concrete trackers inherit
these and keep only their divergent tracking helpers.
"""
from __future__ import annotations

from typing import Optional, Dict, Any


class CrossBorderTrackerBase:
    """Tracks customers shopping in different countries."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def get_session_country(self, session_id: str) -> Optional[str]:
        """Get the current country for a session."""
        session = self._sessions.get(session_id)
        return session.get("country_code") if session else None

    def clear_session(self, session_id: str):
        """Clear a session."""
        self._sessions.pop(session_id, None)
